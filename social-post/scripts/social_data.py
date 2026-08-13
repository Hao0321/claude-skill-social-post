#!/usr/bin/env python3
"""Validate and summarize the structured social-post outcome store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from social_store import load_jsonl, store_revision
from social_validation import (
    validate_account_snapshots, validate_experiments, validate_posts, validate_snapshots,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SKILL_ROOT / "data"
POSTS_FILE = DATA_DIR / "posts.jsonl"
SNAPSHOTS_FILE = DATA_DIR / "insight_snapshots.jsonl"
ACCOUNT_SNAPSHOTS_FILE = DATA_DIR / "account_snapshots.jsonl"
EXPERIMENTS_FILE = DATA_DIR / "experiments.jsonl"
RULE_REGISTRY_FILE = DATA_DIR / "rule_registry.json"


def _known_rule_ids(root: Path) -> set[str]:
    path = root / "data" / RULE_REGISTRY_FILE.name
    if not path.exists():
        return set()
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or not isinstance(value.get("rules"), list):
        raise ValueError("rule_registry.json must contain a rules list")
    return {
        row["id"] for row in value["rules"]
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def validate_store(root: Path = SKILL_ROOT) -> dict[str, Any]:
    """Validate all ledgers and return current materialized views."""
    data = root / "data"
    posts = load_jsonl(data / POSTS_FILE.name)
    snapshots = load_jsonl(data / SNAPSHOTS_FILE.name)
    account_snapshots = load_jsonl(data / ACCOUNT_SNAPSHOTS_FILE.name)
    experiments = load_jsonl(data / EXPERIMENTS_FILE.name)
    errors: list[str] = []
    warnings: list[str] = []
    posts_by_id = validate_posts(posts, errors, warnings)
    latest, latest_by_platform = validate_snapshots(
        snapshots, posts_by_id, errors, warnings,
    )
    latest_accounts = validate_account_snapshots(account_snapshots, errors, warnings)
    latest_experiments = validate_experiments(
        experiments, set(posts_by_id), _known_rule_ids(root), errors, warnings,
    )
    return {
        "valid": not errors,
        "revision": store_revision(data),
        "counts": {
            "posts": len(posts),
            "snapshots": len(snapshots),
            "account_snapshots": len(account_snapshots),
            "experiment_events": len(experiments),
            "experiments": len(latest_experiments),
        },
        "errors": errors,
        "warnings": warnings,
        "latest_snapshots": latest,
        "latest_snapshots_by_platform": latest_by_platform,
        "latest_account_snapshots": latest_accounts,
        "latest_experiments": latest_experiments,
    }


def derived_row(post: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    metrics = snapshot.get("metrics", {})
    plays = metrics.get("plays")
    reach = metrics.get("reached_accounts")
    viewers = metrics.get("viewers")
    audience_count = reach if reach is not None else viewers
    audience_type = "reached_accounts" if reach is not None else ("viewers" if viewers is not None else None)
    duration = post.get("duration_seconds")
    watch = metrics.get("average_watch_seconds")
    audience_gained = metrics.get("followers")
    if audience_gained is None:
        audience_gained = metrics.get("subscribers_gained")
    sources = snapshot.get("traffic_sources_percent", {})
    if not isinstance(sources, dict):
        sources = {}
    interactions = metrics.get("interactions")
    if interactions is None:
        values = [metrics.get(key) for key in ("likes", "comments", "reposts", "shares", "saves")]
        numeric = [value for value in values if isinstance(value, (int, float))]
        interactions = sum(numeric) if numeric else None
    discovery = [sources.get("shorts_feed")] if snapshot.get("platform_scope") == "youtube" else [sources.get("reels_tab"), sources.get("explore")]
    numeric_discovery = [value for value in discovery if isinstance(value, (int, float))]
    return {
        "episode": post.get("episode_number"),
        "post_id": post.get("post_id"),
        "platform": snapshot.get("platform_scope") or "combined",
        "captured_at": snapshot.get("captured_at"),
        "hours_since_publish": snapshot.get("hours_since_publish"),
        "plays": plays,
        "reach": reach,
        "audience_count": audience_count,
        "audience_count_type": audience_type,
        "watch_seconds": watch,
        "watch_percent": round(watch / duration * 100, 1) if watch is not None and duration else None,
        "skip_percent": snapshot.get("rates_reported", {}).get("skip_percent"),
        "plays_per_reached": round(plays / reach, 3) if plays is not None and reach else None,
        "plays_per_audience": round(plays / audience_count, 3) if plays is not None and audience_count else None,
        "followers_per_play_percent": round(audience_gained / plays * 100, 3) if audience_gained is not None and plays else None,
        "followers_per_reached_percent": round(audience_gained / reach * 100, 3) if audience_gained is not None and reach else None,
        "public_interactions_per_reached_percent": round(interactions / reach * 100, 3) if interactions is not None and reach else None,
        "public_interactions_per_audience_percent": round(interactions / audience_count * 100, 3) if interactions is not None and audience_count else None,
        "discovery_percent": round(sum(numeric_discovery), 1) if numeric_discovery else None,
        "profile_source_percent": sources.get("profile"),
    }


def series_summary(root: Path, series_id: str | None = None) -> list[dict[str, Any]]:
    result = validate_store(root)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    posts = load_jsonl(root / "data" / POSTS_FILE.name)
    latest = result["latest_snapshots_by_platform"]
    rows = []
    for post in posts:
        if series_id and post.get("series_id") != series_id:
            continue
        for (post_id, _platform), snapshot in latest.items():
            if post_id != post["post_id"]:
                continue
            if any(value is not None for value in snapshot.get("metrics", {}).values()):
                rows.append(derived_row(post, snapshot))
    return sorted(rows, key=lambda row: (
        row.get("episode") is None, row.get("episode") or 0, row["post_id"], row["platform"],
    ))


def render_table(rows: list[dict[str, Any]]) -> str:
    headers = ("EP", "platform", "plays", "audience", "watch", "skip", "discovery", "profile", "follow/view")
    output = [" | ".join(headers), " | ".join("---" for _ in headers)]

    def percent(value: Any) -> str:
        return "—" if value is None else f"{value}%"

    for row in rows:
        watch = "—" if row["watch_seconds"] is None else f"{row['watch_seconds']}s/{percent(row['watch_percent'])}"
        audience = "—" if row["audience_count"] is None else f"{row['audience_count']} ({row['audience_count_type']})"
        values = (
            str(row["episode"]), str(row["platform"]), str(row["plays"]), audience, watch,
            percent(row["skip_percent"]), percent(row["discovery_percent"]),
            percent(row["profile_source_percent"]), percent(row["followers_per_play_percent"]),
        )
        output.append(" | ".join(values))
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate", "summary"))
    parser.add_argument("--root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--series")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            value = validate_store(args.root)
            if args.format == "json":
                print(json.dumps(value, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"valid={value['valid']} revision={value['revision'][:12]} counts={value['counts']}")
                for error in value["errors"]:
                    print(f"FAIL {error}")
                for warning in value["warnings"]:
                    print(f"WARN {warning}")
            return 0 if value["valid"] else 1
        rows = series_summary(args.root, args.series)
        print(json.dumps(rows, ensure_ascii=False, indent=2) if args.format == "json" else render_table(rows))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"social data error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
