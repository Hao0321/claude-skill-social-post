#!/usr/bin/env python3
"""Gate every request to the author: search records and evidence first, never ask twice.

Binding for every agent that runs this Skill (Claude, Codex, ChatGPT or any other).
Before asking the author for any post data, run:

    python -B scripts/social_ask_gate.py --post <post_id> <item> [<item> ...]

Exit 2 (BLOCK) means the item must not be requested: it is a retired screenshot /
capture time, or the records already hold it. Exit 0 (ASK_AFTER_EVIDENCE_CHECK)
means the item is truly absent from the records; read every listed evidence file
first, and if the request is still needed, name the files you checked and the
exact field that is missing. Read-only: it never writes data.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from review_outcome_intakes import collect_events, read_inputs
from social_data import SKILL_ROOT, _configure_cli_streams, _validated_store
from social_outcome_time_policy import retired_capture_key


BLOCK_RETIRED = "BLOCK_RETIRED"
BLOCK_RECORDED = "BLOCK_ALREADY_RECORDED"
ASK = "ASK_AFTER_EVIDENCE_CHECK"
PUBLICATION = "publication_datetime"
CAPTION = "complete_caption_analysis"
RETIRED_WORDS = re.compile(
    r"screenshot|screen[_ -]?shot|capture|captured|status[_ ]?bar|maturity|hours[_ ]?since|"
    r"截圖|截屏|擷取|狀態列|成熟度|幾點截",
    re.IGNORECASE,
)
ALIASES = {
    "published_at": PUBLICATION, "publication_time": PUBLICATION, "publish_time": PUBLICATION,
    "發布時間": PUBLICATION, "發文時間": PUBLICATION, "發佈時間": PUBLICATION,
    "caption": CAPTION, "full_caption": CAPTION, "complete_caption": CAPTION,
    "全文": CAPTION, "文案": CAPTION, "完整文案": CAPTION, "續文": CAPTION,
}
RULES = [
    "Never request or derive a screenshot / capture time; only publication date, weekday, timezone and minute matter.",
    "Never ask the author to resend data already in data/*.jsonl or data/evidence; transcription errors are fixed with a correction bundle.",
    "Before asking, read every evidence file listed here; when asking, name the files checked and the exact missing field.",
    "A missing public continuation is read from the author's profile after the author signs in, not requested again.",
]


def normalize(item: str) -> str:
    value = item.strip()
    return ALIASES.get(value, ALIASES.get(value.lower(), value))


def is_retired(item: str) -> bool:
    return retired_capture_key(item) or bool(RETIRED_WORDS.search(item))


def evidence_paths(value, found: set[str]) -> set[str]:
    """Collect every data/evidence path mentioned anywhere in a record."""
    if isinstance(value, dict):
        for child in value.values():
            evidence_paths(child, found)
    elif isinstance(value, list):
        for child in value:
            evidence_paths(child, found)
    elif isinstance(value, str) and value.replace("\\", "/").startswith("data/evidence/"):
        found.add(value.replace("\\", "/"))
    return found


def lookup(values: list[dict], dotted: str):
    """Return (value, source) for the first non-null dotted path, newest observation first."""
    for row in reversed(values):
        source = row.get("snapshot_id")
        for container in (row.get("metrics", {}), row):
            current = container
            for part in dotted.split("."):
                current = current.get(part) if isinstance(current, dict) else None
            if current is not None and not isinstance(current, (dict, list)):
                return current, source
    return None, None


def records_for(root: Path, post_id: str) -> dict:
    events, _snapshots, _accounts, _revision = read_inputs(root)
    store, snapshots, _ = _validated_store(root)
    intakes = [entry for entry in collect_events(events)[0].values()
               if entry["post"].get("post_id") == post_id]
    canonical = [row for row in store["posts"] if row.get("post_id") == post_id]
    # lookup() reads newest-first, so corrected canonical snapshots go last and win
    # over raw intake candidates that may still hold a mis-transcribed value.
    observations = ([entry["snapshot"] for entry in intakes]
                    + [row for row in snapshots if row.get("post_id") == post_id])
    found: set[str] = set()
    for row in canonical + observations:
        evidence_paths(row, found)
    for entry in intakes:
        evidence_paths(entry["evidence"], found)
    return {"posts": canonical + [entry["post"] for entry in intakes],
            "observations": observations, "evidence": sorted(found)}


def decide(item: str, records: dict) -> dict:
    name = normalize(item)
    if is_retired(name) or is_retired(item):
        return {"item": item, "status": BLOCK_RETIRED,
                "reason": "publication-only time policy: screenshot / capture time is never requested"}
    posts = records["posts"]
    if name == PUBLICATION:
        value = next((row["published_at"] for row in posts if row.get("published_at")), None)
    elif name == CAPTION:
        value = next((row["caption"] for row in posts
                      if row.get("caption_is_complete") is True and row.get("caption")), None)
    else:
        value, source = lookup(records["observations"], name)
        if value is None:
            value, source = lookup(posts, name)
        if value is not None:
            return {"item": item, "status": BLOCK_RECORDED, "recorded_value": value,
                    "source": source, "reason": "already recorded; never ask again"}
    if value is not None:
        return {"item": item, "status": BLOCK_RECORDED, "recorded_value": value,
                "reason": "already recorded; never ask again"}
    return {"item": item, "status": ASK,
            "reason": "not in the records; read the evidence files first, ask only if they do not show it"}


def check(root: Path, post_id: str, items: list[str]) -> dict:
    if not post_id.strip() or not items:
        raise ValueError("--post and at least one item are required")
    records = records_for(root, post_id)
    decisions = [decide(item, records) for item in items]
    blocked = any(row["status"] != ASK for row in decisions)
    evidence = records["evidence"]
    if not records["posts"]:
        folder = root / "data" / "evidence"
        evidence = sorted(f"data/evidence/{path.name}/" for path in folder.iterdir()
                          if path.is_dir()) if folder.is_dir() else []
    return {"post_id": post_id, "decision": "BLOCK" if blocked else ASK,
            "record_found": bool(records["posts"]), "items": decisions,
            "evidence_to_check_first": evidence, "rules": RULES}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--post", required=True, help="post_id the request is about")
    parser.add_argument("items", nargs="+", help="fields you want to ask the author for")
    args = parser.parse_args(argv)
    _configure_cli_streams()
    try:
        report = check(args.root, args.post, args.items)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ask gate error (do not ask; fix the store first): {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["decision"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
