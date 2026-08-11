#!/usr/bin/env python3
"""Validate and summarize the structured social-post outcome store."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SKILL_ROOT / "data"
POSTS_FILE = DATA_DIR / "posts.jsonl"
SNAPSHOTS_FILE = DATA_DIR / "insight_snapshots.jsonl"
EXPERIMENTS_FILE = DATA_DIR / "experiments.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_no}: each JSONL row must be an object")
        records.append(value)
    return records


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed


def non_negative_numbers(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            non_negative_numbers(child, f"{path}.{key}", errors)
    elif isinstance(value, (int, float)) and value < 0:
        errors.append(f"{path} must be non-negative")


def validate_store(root: Path = SKILL_ROOT) -> dict[str, Any]:
    data = root / "data"
    posts = load_jsonl(data / "posts.jsonl")
    snapshots = load_jsonl(data / "insight_snapshots.jsonl")
    experiments = load_jsonl(data / "experiments.jsonl")
    errors: list[str] = []
    warnings: list[str] = []

    post_ids: set[str] = set()
    for index, post in enumerate(posts, start=1):
        label = f"posts.jsonl:{index}"
        for key in ("post_id", "series_id", "episode_number", "published_at", "duration_seconds", "platforms", "caption"):
            if key not in post:
                errors.append(f"{label} missing {key}")
        post_id = post.get("post_id")
        if post_id in post_ids:
            errors.append(f"{label} duplicate post_id {post_id}")
        if post_id:
            post_ids.add(post_id)
        try:
            parse_time(post.get("published_at", ""))
        except ValueError:
            errors.append(f"{label} invalid published_at (ISO 8601 with offset required)")
        if not isinstance(post.get("platforms"), list) or not post.get("platforms"):
            errors.append(f"{label} platforms must be a non-empty list")
        duration = post.get("duration_seconds")
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{label} duration_seconds must be positive")

    snapshot_ids: set[str] = set()
    latest_by_post: dict[str, dict[str, Any]] = {}
    posts_by_id = {post["post_id"]: post for post in posts if post.get("post_id")}
    for index, snapshot in enumerate(snapshots, start=1):
        label = f"insight_snapshots.jsonl:{index}"
        for key in ("snapshot_id", "post_id", "captured_at", "metrics"):
            if key not in snapshot:
                errors.append(f"{label} missing {key}")
        snapshot_id = snapshot.get("snapshot_id")
        if snapshot_id in snapshot_ids:
            errors.append(f"{label} duplicate snapshot_id {snapshot_id}")
        if snapshot_id:
            snapshot_ids.add(snapshot_id)
        post_id = snapshot.get("post_id")
        if post_id not in post_ids:
            errors.append(f"{label} references unknown post_id {post_id}")
            continue
        try:
            captured = parse_time(snapshot.get("captured_at", ""))
            published = parse_time(posts_by_id[post_id]["published_at"])
            if captured < published:
                errors.append(f"{label} captured_at is before published_at")
        except ValueError:
            errors.append(f"{label} invalid captured_at (ISO 8601 with offset required)")
            continue
        maturity = snapshot.get("maturity")
        if maturity is not None and maturity not in {"early", "developing", "mature", "plateau"}:
            errors.append(f"{label} invalid maturity {maturity}")
        hours = snapshot.get("hours_since_publish")
        if hours is not None and (not isinstance(hours, (int, float)) or hours < 0):
            errors.append(f"{label} hours_since_publish must be non-negative")
        if not isinstance(snapshot.get("metrics"), dict):
            errors.append(f"{label} metrics must be an object")
            continue
        non_negative_numbers(snapshot.get("metrics", {}), f"{label}.metrics", errors)
        rates = snapshot.get("rates_reported", {})
        if not isinstance(rates, dict):
            errors.append(f"{label}.rates_reported must be an object")
            rates = {}
        for key, value in rates.items():
            if isinstance(value, (int, float)) and not 0 <= value <= 100:
                errors.append(f"{label}.rates_reported.{key} must be 0..100")
        metrics = snapshot.get("metrics", {})
        breakdown = snapshot.get("platform_breakdown", {})
        for metric in ("plays", "likes", "comments"):
            total = metrics.get(metric)
            values = breakdown.get(metric)
            if total is not None and isinstance(values, dict) and values:
                subtotal = sum(value for value in values.values() if isinstance(value, (int, float)))
                if subtotal != total:
                    errors.append(f"{label} {metric} platform sum {subtotal} != total {total}")
        previous = latest_by_post.get(post_id)
        if previous is None or parse_time(previous["captured_at"]) < captured:
            latest_by_post[post_id] = snapshot

    experiment_ids: set[str] = set()
    for index, experiment in enumerate(experiments, start=1):
        label = f"experiments.jsonl:{index}"
        experiment_id = experiment.get("experiment_id")
        if not experiment_id:
            errors.append(f"{label} missing experiment_id")
        elif experiment_id in experiment_ids:
            errors.append(f"{label} duplicate experiment_id {experiment_id}")
        else:
            experiment_ids.add(experiment_id)
        for post_id in experiment.get("post_ids", []):
            if post_id not in post_ids:
                errors.append(f"{label} references unknown post_id {post_id}")
        status = experiment.get("evidence", {}).get("status")
        if status not in {"hypothesis", "emerging", "validated", "deprecated"}:
            errors.append(f"{label} invalid evidence status {status}")
        independent = experiment.get("independent_samples")
        if independent is not None and (not isinstance(independent, int) or independent < 0):
            errors.append(f"{label} independent_samples must be a non-negative integer")
        if status == "validated" and len(experiment.get("post_ids", [])) < 2:
            warnings.append(f"{label} validated with fewer than two posts")

    return {
        "valid": not errors,
        "counts": {"posts": len(posts), "snapshots": len(snapshots), "experiments": len(experiments)},
        "errors": errors,
        "warnings": warnings,
        "latest_snapshots": latest_by_post,
    }


def derived_row(post: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    metrics = snapshot.get("metrics", {})
    plays = metrics.get("plays") or 0
    reach = metrics.get("reached_accounts") or 0
    duration = post.get("duration_seconds") or 0
    watch = metrics.get("average_watch_seconds") or 0
    followers = metrics.get("followers") or 0
    sources = snapshot.get("traffic_sources_percent", {})
    interactions = sum(metrics.get(key) or 0 for key in ("likes", "comments", "reposts", "shares", "saves"))
    return {
        "episode": post.get("episode_number"),
        "post_id": post.get("post_id"),
        "captured_at": snapshot.get("captured_at"),
        "hours_since_publish": snapshot.get("hours_since_publish"),
        "plays": plays,
        "reach": reach,
        "watch_seconds": watch,
        "watch_percent": round(watch / duration * 100, 1) if duration else None,
        "skip_percent": snapshot.get("rates_reported", {}).get("skip_percent"),
        "plays_per_reached": round(plays / reach, 3) if reach else None,
        "followers_per_play_percent": round(followers / plays * 100, 3) if plays else None,
        "followers_per_reached_percent": round(followers / reach * 100, 3) if reach else None,
        "public_interactions_per_reached_percent": round(interactions / reach * 100, 3) if reach else None,
        "discovery_percent": round((sources.get("reels_tab") or 0) + (sources.get("explore") or 0), 1),
        "profile_source_percent": sources.get("profile"),
    }


def series_summary(root: Path, series_id: str | None = None) -> list[dict[str, Any]]:
    result = validate_store(root)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    posts = load_jsonl(root / "data" / "posts.jsonl")
    latest = result["latest_snapshots"]
    rows = []
    for post in posts:
        if series_id and post.get("series_id") != series_id:
            continue
        snapshot = latest.get(post["post_id"])
        if snapshot:
            rows.append(derived_row(post, snapshot))
    return sorted(rows, key=lambda row: (row.get("episode") or 0, row["post_id"]))


def render_table(rows: list[dict[str, Any]]) -> str:
    headers = ("EP", "plays", "reach", "watch", "skip", "discovery", "profile", "follow/view")
    output = [" | ".join(headers), " | ".join("---" for _ in headers)]
    for row in rows:
        values = (
            str(row["episode"]), str(row["plays"]), str(row["reach"]),
            f"{row['watch_seconds']}s/{row['watch_percent']}%",
            f"{row['skip_percent']}%", f"{row['discovery_percent']}%",
            f"{row['profile_source_percent']}%", f"{row['followers_per_play_percent']}%",
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
                print(f"valid={value['valid']} counts={value['counts']}")
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
