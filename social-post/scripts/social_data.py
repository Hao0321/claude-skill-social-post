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
MATURITY_VALUES = {
    "early", "early_not_plateau", "developing", "near_48h_not_final", "mature", "plateau",
}
EVIDENCE_VALUES = {"hypothesis", "emerging", "validated", "deprecated"}


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
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed


def non_negative_numbers(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            non_negative_numbers(child, f"{path}.{key}", errors)
    elif value is None:
        return
    elif not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{path} must be a number or null")
    elif value < 0:
        errors.append(f"{path} must be non-negative")


def validate_percent_mapping(value: Any, path: str, errors: list[str]) -> list[float]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return []
    values: list[float] = []
    for key, child in value.items():
        if child is None:
            continue
        if not isinstance(child, (int, float)) or isinstance(child, bool) or not 0 <= child <= 100:
            errors.append(f"{path}.{key} must be a number from 0..100")
        else:
            values.append(float(child))
    return values


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
        for key in ("post_id", "published_at", "platforms", "caption"):
            if key not in post:
                errors.append(f"{label} missing {key}")
        post_id = post.get("post_id")
        if not isinstance(post_id, str) or not post_id.strip():
            errors.append(f"{label} post_id must be a non-empty string")
        else:
            if post_id in post_ids:
                errors.append(f"{label} duplicate post_id {post_id}")
            post_ids.add(post_id)
        try:
            parse_time(post.get("published_at", ""))
        except ValueError:
            errors.append(f"{label} invalid published_at (ISO 8601 with offset required)")
        platforms = post.get("platforms")
        if (
            not isinstance(platforms, list) or not platforms
            or any(not isinstance(item, str) or not item.strip() for item in platforms)
            or len(set(platforms)) != len(platforms)
        ):
            errors.append(f"{label} platforms must be a non-empty list")
        duration = post.get("duration_seconds")
        if duration is not None and (
            not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0
        ):
            errors.append(f"{label} duration_seconds must be positive")
        episode = post.get("episode_number")
        if episode is not None and (not isinstance(episode, int) or isinstance(episode, bool) or episode < 1):
            errors.append(f"{label} episode_number must be a positive integer")
        series = post.get("series_id")
        if series is not None and (not isinstance(series, str) or not series.strip()):
            errors.append(f"{label} series_id must be a non-empty string")
        if not isinstance(post.get("caption"), str):
            errors.append(f"{label} caption must be a string")
        content_type = str(post.get("content_type", "")).casefold()
        if duration is None and any(token in content_type for token in ("reel", "video", "short")):
            warnings.append(f"{label} video-like content has no duration_seconds")

    snapshot_ids: set[str] = set()
    latest_by_post: dict[str, dict[str, Any]] = {}
    posts_by_id = {
        post["post_id"]: post
        for post in posts
        if isinstance(post.get("post_id"), str) and post.get("post_id")
    }
    for index, snapshot in enumerate(snapshots, start=1):
        label = f"insight_snapshots.jsonl:{index}"
        for key in ("snapshot_id", "post_id", "captured_at", "metrics"):
            if key not in snapshot:
                errors.append(f"{label} missing {key}")
        snapshot_id = snapshot.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id.strip():
            errors.append(f"{label} snapshot_id must be a non-empty string")
        else:
            if snapshot_id in snapshot_ids:
                errors.append(f"{label} duplicate snapshot_id {snapshot_id}")
            snapshot_ids.add(snapshot_id)
        post_id = snapshot.get("post_id")
        if not isinstance(post_id, str) or not post_id.strip():
            errors.append(f"{label} post_id must be a non-empty string")
            continue
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
        if maturity is not None and maturity not in MATURITY_VALUES:
            errors.append(f"{label} invalid maturity {maturity}")
        confidence = snapshot.get("captured_at_confidence")
        if confidence is not None and confidence not in {"low", "medium", "high"}:
            errors.append(f"{label} invalid captured_at_confidence {confidence}")
        hours = snapshot.get("hours_since_publish")
        if hours is not None and (
            not isinstance(hours, (int, float)) or isinstance(hours, bool) or hours < 0
        ):
            errors.append(f"{label} hours_since_publish must be non-negative")
        elif hours is not None:
            actual_hours = (captured - published).total_seconds() / 3600
            if abs(float(hours) - actual_hours) > 1:
                warnings.append(f"{label} hours_since_publish differs from timestamps by more than 1 hour")
        if not isinstance(snapshot.get("metrics"), dict):
            errors.append(f"{label} metrics must be an object")
            continue
        non_negative_numbers(snapshot.get("metrics", {}), f"{label}.metrics", errors)
        rates = snapshot.get("rates_reported", {})
        validate_percent_mapping(rates, f"{label}.rates_reported", errors)
        metrics = snapshot.get("metrics", {})
        breakdown = snapshot.get("platform_breakdown", {})
        if not isinstance(breakdown, dict):
            errors.append(f"{label}.platform_breakdown must be an object")
            breakdown = {}
        expected_platforms = set(posts_by_id[post_id].get("platforms", []))
        for metric in ("plays", "likes", "comments"):
            total = metrics.get(metric)
            values = breakdown.get(metric)
            total_is_number = isinstance(total, (int, float)) and not isinstance(total, bool)
            if total is not None and not total_is_number:
                continue
            if total_is_number and isinstance(values, dict) and values:
                numeric_values = {
                    key: value for key, value in values.items()
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                }
                invalid_values = [
                    value for value in values.values()
                    if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool))
                ]
                if invalid_values or any(value < 0 for value in numeric_values.values()):
                    errors.append(f"{label} {metric} platform breakdown must contain non-negative numbers")
                    continue
                subtotal = sum(numeric_values.values())
                complete = expected_platforms and expected_platforms.issubset(numeric_values)
                if complete and subtotal != total:
                    errors.append(f"{label} {metric} platform sum {subtotal} != total {total}")
                elif not complete and subtotal > total:
                    errors.append(f"{label} partial {metric} platform sum {subtotal} exceeds total {total}")
                elif not complete and subtotal != total:
                    warnings.append(f"{label} {metric} platform breakdown is partial; sum check not enforced")
        traffic_values = validate_percent_mapping(
            snapshot.get("traffic_sources_percent", {}), f"{label}.traffic_sources_percent", errors,
        )
        if traffic_values and sum(traffic_values) > 101:
            warnings.append(f"{label} traffic source percentages sum above 101%")
        audience = snapshot.get("audience", {})
        if audience:
            if not isinstance(audience, dict):
                errors.append(f"{label}.audience must be an object")
            else:
                follower_values = validate_percent_mapping(
                    {key: audience[key] for key in ("followers_percent", "non_followers_percent") if key in audience},
                    f"{label}.audience.followership", errors,
                )
                if len(follower_values) == 2 and abs(sum(follower_values) - 100) > 1.5:
                    warnings.append(f"{label} follower audience percentages do not sum near 100%")
                for group in ("gender_percent", "age_percent"):
                    if group in audience:
                        group_values = validate_percent_mapping(audience[group], f"{label}.audience.{group}", errors)
                        if group_values and abs(sum(group_values) - 100) > 1.5:
                            warnings.append(f"{label} {group} does not sum near 100%")
                if "top_countries_percent" in audience:
                    validate_percent_mapping(
                        audience["top_countries_percent"], f"{label}.audience.top_countries_percent", errors,
                    )
        previous = latest_by_post.get(post_id)
        if previous is None or parse_time(previous["captured_at"]) < captured:
            latest_by_post[post_id] = snapshot

    experiment_ids: set[str] = set()
    for index, experiment in enumerate(experiments, start=1):
        label = f"experiments.jsonl:{index}"
        experiment_id = experiment.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id.strip():
            errors.append(f"{label} experiment_id must be a non-empty string")
        elif experiment_id in experiment_ids:
            errors.append(f"{label} duplicate experiment_id {experiment_id}")
        else:
            experiment_ids.add(experiment_id)
        experiment_posts = experiment.get("post_ids", [])
        if not isinstance(experiment_posts, list) or not experiment_posts:
            errors.append(f"{label} post_ids must be a non-empty list")
            experiment_posts = []
        for post_id in experiment_posts:
            if not isinstance(post_id, str) or not post_id.strip():
                errors.append(f"{label} post_ids must contain non-empty strings")
            elif post_id not in post_ids:
                errors.append(f"{label} references unknown post_id {post_id}")
        evidence = experiment.get("evidence", {})
        if not isinstance(evidence, dict):
            errors.append(f"{label} evidence must be an object")
            evidence = {}
        status = evidence.get("status")
        if status not in EVIDENCE_VALUES:
            errors.append(f"{label} invalid evidence status {status}")
        independent = experiment.get("independent_samples", evidence.get("independent_samples"))
        if independent is not None and not isinstance(independent, (bool, int)):
            errors.append(f"{label} independent_samples must be a boolean or non-negative integer")
        elif isinstance(independent, int) and not isinstance(independent, bool) and independent < 0:
            errors.append(f"{label} independent_samples must be non-negative")
        elif isinstance(independent, int) and not isinstance(independent, bool) and independent > len(experiment_posts):
            errors.append(f"{label} independent_samples exceeds post count")
        independent_enough = (
            isinstance(independent, int) and not isinstance(independent, bool) and independent >= 2
        )
        if status == "validated" and not independent_enough:
            warnings.append(f"{label} validated with fewer than two independent samples")

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
    if not isinstance(sources, dict):
        sources = {}
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
    return sorted(rows, key=lambda row: (row.get("episode") is None, row.get("episode") or 0, row["post_id"]))


def render_table(rows: list[dict[str, Any]]) -> str:
    headers = ("EP", "plays", "reach", "watch", "skip", "discovery", "profile", "follow/view")
    output = [" | ".join(headers), " | ".join("---" for _ in headers)]
    def percent(value: Any) -> str:
        return "—" if value is None else f"{value}%"
    for row in rows:
        values = (
            str(row["episode"]), str(row["plays"]), str(row["reach"]),
            f"{row['watch_seconds']}s/{percent(row['watch_percent'])}",
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
