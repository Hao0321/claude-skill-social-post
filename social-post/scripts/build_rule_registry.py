#!/usr/bin/env python3
"""Generate a machine-readable index from references/rules.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "rules.md"
RULE_DIR = ROOT / "references" / "rules"
METADATA = RULE_DIR / "metadata.json"
OUTPUT = ROOT / "data" / "rule_registry.json"
HEADING = re.compile(r"^## (R\d+)\s*[：:]\s*(.+)$", re.M)


def build() -> dict:
    metadata_value = json.loads(METADATA.read_text(encoding="utf-8-sig"))
    metadata_rows = metadata_value.get("rules", [])
    metadata = {row["id"]: row for row in metadata_rows}
    if len(metadata) != len(metadata_rows):
        raise ValueError("duplicate rule id in rules/metadata.json")
    split_sources = sorted(RULE_DIR.glob("R*.md")) if RULE_DIR.exists() else []
    sources = split_sources or [SOURCE]
    rules = []
    seen: dict[str, str] = {}
    for source in sources:
        text = source.read_text(encoding="utf-8-sig")
        matches = list(HEADING.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[match.end():end]
            heading = match.group(2).strip()
            rule_id = match.group(1)
            if rule_id in seen:
                raise ValueError(f"duplicate rule id {rule_id}: {seen[rule_id]} and {source}")
            seen[rule_id] = source.relative_to(ROOT).as_posix()
            if rule_id not in metadata:
                raise ValueError(f"missing canonical metadata for {rule_id}")
            rule_metadata = metadata[rule_id]
            status = rule_metadata.get("status")
            if status not in {"active", "emerging", "deprecated"}:
                raise ValueError(f"invalid status for {rule_id}: {status}")
            sample_mentions = sorted({int(value) for value in re.findall(r"n\s*=\s*(\d+)", section, re.I)})
            rules.append({
                "id": rule_id,
                "title": heading,
                "status": status,
                "source_file": source.relative_to(ROOT).as_posix(),
                "source_line": text.count("\n", 0, match.start()) + 1,
                "sample_mentions": sample_mentions,
                "experiment_ids": rule_metadata.get("experiment_ids", []),
            })
    rules.sort(key=lambda item: int(item["id"][1:]))
    extra_metadata = sorted(set(metadata) - set(seen))
    if extra_metadata:
        raise ValueError(f"metadata without rule files: {extra_metadata}")
    return {
        "schema_version": "2.0",
        "source_of_truth": {
            "prose": "references/rules/RNN.md",
            "lifecycle": "references/rules/metadata.json",
        },
        "rules": rules,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    registry = build()
    rendered = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(registry['rules'])} rules)")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
