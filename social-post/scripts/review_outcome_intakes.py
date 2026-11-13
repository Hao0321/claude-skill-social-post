#!/usr/bin/env python3
"""Read-only P3 evidence queue; never a source for the performance matrix."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

from social_data import SKILL_ROOT, _validated_store
from social_primitives import PLATFORM_VALUES, parse_time
from social_snapshot import file_identity, parse_jsonl
from social_validation import MEASUREMENT_QUALIFIERS, validate_posts


POST = "owner_post_outcome_intake"
ACCOUNT = "owner_account_outcome_intake"
CAPTION = "author_full_caption_confirmation"
METRICS = ("views", "viewers", "interactions", "clicks", "link_clicks", "reactions",
           "likes", "comments", "shares", "saves", "followers_gained")


def identifier(row, key):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"invalid {key}")
    return value


def index(rows, key):
    result = {}
    for row in rows:
        value = identifier(row, key)
        if value in result:
            raise ValueError(f"duplicate {key}: {value}")
        result[value] = row
    return result


def read_inputs(root):
    path = root / "data" / "outcome_intakes.jsonl"
    before = file_identity(path)
    raw = path.read_bytes() if before is not None else b""
    result, snapshots, accounts = _validated_store(root)
    if before != file_identity(path):
        raise ValueError("intake ledger changed during review; retry")
    if not result["valid"]:
        raise ValueError("canonical outcome store is invalid; run social_data.py validate")
    return parse_jsonl(raw, path.name), snapshots, accounts, result["revision"]


def caption_candidate(row):
    post = row.get("post_candidate")
    if not isinstance(post, dict):
        raise ValueError("post intake requires a post_candidate object")
    errors = []
    validate_posts([post], errors, [])
    if errors:
        raise ValueError(f"{row['intake_id']}: {'; '.join(errors)}")
    return post


def timestamp(row, minimum=None):
    value = row.get("captured_at")
    if value is not None:
        captured = parse_time(value)
        if minimum is not None and captured < parse_time(minimum):
            raise ValueError("intake captured_at is before published_at")
    return value


def recorded_time(value):
    # PowerShell's round-trip timestamp can contain seven fractional digits.
    # Compare at Python's microsecond precision, but keep the ledger value verbatim.
    if isinstance(value, str):
        value = re.sub(r"(\.\d{6})\d+(?=Z$|[+-]\d{2}:\d{2}$)", r"\1", value)
    return parse_time(value)


def metric_view(record, group=None):
    metrics = record.get("metrics", {})
    qualifiers = record.get("metric_qualifiers", {})
    selected = qualifiers if group is None else group[0]
    prefix = "" if group is None else group[1]
    if not isinstance(metrics, dict) or not isinstance(selected, dict):
        raise ValueError("intake metrics and qualifiers must be objects")
    result = {}
    for key in METRICS:
        value = metrics.get(key)
        if value is None:
            continue
        if (type(value) not in (int, float) or value < 0
                or (isinstance(value, float) and not math.isfinite(value))):
            raise ValueError(f"invalid intake metric: {key}")
        qualifier = selected.get(prefix + key)
        if qualifier is not None and qualifier not in MEASUREMENT_QUALIFIERS:
            raise ValueError(f"invalid intake metric qualifier: {key}")
        result[key] = {"value": value, "qualifier": qualifier}
    return result


def observed_metrics(snapshot):
    references = {}
    for key in ("meta_overview_observation", "instagram_reference"):
        ref = snapshot.get(key)
        if isinstance(ref, dict):
            references[key] = metric_view(ref, (
                snapshot.get("metric_qualifiers", {}), f"{key}.metrics.",
            ))
    return {"platform_metrics": metric_view(snapshot), "reference_metrics": references}


def complete_caption(post):
    return (post.get("caption_is_complete") is not False
            and post.get("analysis_status") == "complete" and post.get("analysis_eligible") is True)


def apply_supplement(entries, event):
    parent = identifier(event, "parent_intake_id")
    entry = entries.get(parent)
    if entry is None or event.get("snapshot_source_intake_id") != parent:
        raise ValueError("caption supplement must reference an exact post intake")
    post = caption_candidate(event)
    prior = entry["post"]
    for key in ("post_id", "platforms", "published_at", "content_type", "media_family"):
        if post.get(key) != prior.get(key):
            raise ValueError(f"caption supplement conflicts with parent {key}")
    if (event.get("post_id") != prior["post_id"]
            or event.get("snapshot_id") != entry["snapshot"]["snapshot_id"]
            or event.get("platform") != entry["snapshot"]["platform_scope"]):
        raise ValueError("caption supplement conflicts with parent observation")
    if (not complete_caption(post) or not post["caption"].startswith(prior["caption"])
            or (complete_caption(prior) and post["caption_sha256"] != prior["caption_sha256"])):
        raise ValueError("caption supplement is incomplete or conflicts with observed text")
    recorded = event.get("recorded_at")
    if recorded_time(recorded) < recorded_time(entry["recorded"]):
        raise ValueError("caption supplement precedes its base or previous supplement")
    entry.update(post=post, recorded=recorded)
    entry["supplements"].append(event["intake_id"])


def post_summary(intake_id, entry, registered):
    post, snapshot = entry["post"], entry["snapshot"]
    scope = snapshot["platform_scope"]
    canonical = registered.get(snapshot["snapshot_id"])
    if canonical and (canonical["post_id"] != post["post_id"]
                      or (canonical.get("platform_scope") or "combined") != scope):
        raise ValueError("canonical snapshot conflicts with intake identity")
    observed = timestamp(snapshot, post["published_at"])
    captured = canonical["captured_at"] if canonical else observed
    missing = []
    if captured is None:
        missing.append("capture_datetime")
    if not complete_caption(post):
        missing.append("complete_caption_analysis")
    return {
        "intake_id": intake_id, "post_id": post["post_id"], "snapshot_id": snapshot["snapshot_id"],
        "platform": scope, "published_at": post["published_at"],
        "recorded_at": entry["recorded"], "captured_at": captured,
        "capture_source": "canonical" if canonical else "intake" if observed else None,
        "canonical_registered": canonical is not None, "missing": missing,
        "caption_analysis_complete": complete_caption(post),
        "supplement_intake_ids": entry["supplements"], **observed_metrics(snapshot),
    }


def account_summary(event, registered):
    account = event.get("account_snapshot_candidate")
    if not isinstance(account, dict):
        raise ValueError("account intake requires an account_snapshot_candidate object")
    identity = identifier(account, "account_snapshot_id")
    platform, days = account.get("platform"), account.get("window_days")
    if (platform not in PLATFORM_VALUES or platform != event.get("platform")
            or type(days) is not int or days <= 0 or account.get("post_id") is not None):
        raise ValueError("invalid account observation scope")
    canonical = registered.get(identity)
    if canonical and (canonical["platform"] != platform or canonical["window_days"] != days):
        raise ValueError("canonical account snapshot conflicts with intake identity")
    observed = timestamp(account)
    captured = canonical["captured_at"] if canonical else observed
    recorded = event.get("recorded_at")
    recorded_time(recorded)
    return {
        "intake_id": event["intake_id"], "account_snapshot_id": identity,
        "platform": platform, "window_days": days,
        "recorded_at": recorded, "captured_at": captured,
        "capture_source": "canonical" if canonical else "intake" if observed else None,
        "canonical_registered": canonical is not None,
        "missing": [] if captured else ["capture_datetime"], "account_metrics": metric_view(account),
    }


def collect_events(events):
    posts, accounts, reference_ids, snapshot_ids = {}, [], [], set()
    for identity, event in index(events, "intake_id").items():
        kind = event.get("event_type")
        if kind in (POST, ACCOUNT, CAPTION) and event.get("owner_scope") != "own":
            raise ValueError("reviewable intake must be marked own")
        if kind == POST:
            post = caption_candidate(event)
            snapshot = event.get("snapshot_observation")
            if not isinstance(snapshot, dict):
                raise ValueError("post intake requires a snapshot_observation object")
            scope = snapshot.get("platform_scope")
            if (snapshot.get("post_id") != post["post_id"] or scope != event.get("platform")
                    or scope not in post["platforms"]):
                raise ValueError("post intake identity or platform mismatch")
            snapshot_id = identifier(snapshot, "snapshot_id")
            if snapshot_id in snapshot_ids:
                raise ValueError(f"duplicate intake snapshot_id: {snapshot_id}")
            snapshot_ids.add(snapshot_id)
            recorded = event.get("recorded_at")
            recorded_time(recorded)
            posts[identity] = {"post": post, "snapshot": snapshot, "supplements": [],
                               "recorded": recorded}
        elif kind == ACCOUNT:
            accounts.append(event)
        elif kind == CAPTION:
            apply_supplement(posts, event)
        else:
            reference_ids.append(identity)
    return posts, accounts, reference_ids


def review(root=SKILL_ROOT, *, since=None):
    events, snapshots, accounts, revision = read_inputs(root)
    posts, account_events, references = collect_events(events)
    snapshot_index = index(snapshots, "snapshot_id")
    account_index = index(accounts, "account_snapshot_id")
    post_rows = [post_summary(key, value, snapshot_index) for key, value in posts.items()]
    account_rows = [account_summary(event, account_index) for event in account_events]
    index(account_rows, "account_snapshot_id")
    post_rows = filtered(post_rows, since)
    account_rows = filtered(account_rows, since)
    return {
        "schema_version": 1, "reference_only": True, "canonical_revision": revision,
        "since_intake_date": since.isoformat() if since else None,
        "unique_post_count": len({row["post_id"] for row in post_rows}),
        "post_observations": post_rows, "account_observations": account_rows,
        "other_history_ids_unfiltered": references,
    }


def filtered(rows, since):
    recent = [row for row in rows if since is None or recorded_time(row["recorded_at"]).date() >= since]
    return sorted(recent, key=lambda row: (recorded_time(row["recorded_at"]), row["intake_id"]),
                  reverse=True)


def render(report):
    posts, accounts = report["post_observations"], report["account_observations"]
    lines = [f"intake review (read-only): {report['unique_post_count']} posts, "
             f"{len(posts)} post observations, {len(accounts)} account observations"]
    for row in posts + accounts:
        kind = "account" if "account_snapshot_id" in row else "post"
        status = "registered" if row["canonical_registered"] else "not registered"
        missing = ", ".join(row["missing"]) or "none listed (native validation still required)"
        lines.append(f"{kind} {row['intake_id']} [{row['platform']}; {status}] missing: {missing}")
    lines.append("Not a performance comparison. Use --format json for scoped observations.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--since", type=date.fromisoformat, help="minimum local intake event date (YYYY-MM-DD)")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    args = parser.parse_args()
    try:
        value = review(args.root, since=args.since)
        print(json.dumps(value, ensure_ascii=False, indent=2) if args.format == "json" else render(value))
        return 0
    except (OSError, ValueError, TypeError, AttributeError, KeyError, TimeoutError) as exc:
        print(f"outcome intake review error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
