#!/usr/bin/env python3
"""Schema and relationship validation for social-post structured outcomes."""

from __future__ import annotations

from datetime import datetime
from typing import Any


MATURITY_VALUES = {
    "early", "early_not_plateau", "developing", "near_48h_not_final", "mature", "plateau",
}
EVIDENCE_VALUES = {"hypothesis", "emerging", "validated", "deprecated"}
PLATFORM_VALUES = {"facebook", "instagram", "youtube", "threads", "x"}


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


def _validate_post(post: dict[str, Any], label: str, post_ids: set[str], errors: list[str], warnings: list[str]) -> None:
    for key in ("post_id", "published_at", "platforms", "caption"):
        if key not in post:
            errors.append(f"{label} missing {key}")
    post_id = post.get("post_id")
    if not isinstance(post_id, str) or not post_id.strip():
        errors.append(f"{label} post_id must be a non-empty string")
    elif post_id in post_ids:
        errors.append(f"{label} duplicate post_id {post_id}")
    else:
        post_ids.add(post_id)
    try:
        parse_time(post.get("published_at", ""))
    except ValueError:
        errors.append(f"{label} invalid published_at (ISO 8601 with offset required)")
    platforms = post.get("platforms")
    invalid_platforms = (
        not isinstance(platforms, list) or not platforms
        or any(not isinstance(item, str) or item not in PLATFORM_VALUES for item in platforms)
        or len(set(platforms)) != len(platforms)
    )
    if invalid_platforms:
        errors.append(f"{label} platforms must be a unique non-empty list from {sorted(PLATFORM_VALUES)}")
    duration = post.get("duration_seconds")
    if duration is not None and (
        not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0
    ):
        errors.append(f"{label} duration_seconds must be positive")
    episode = post.get("episode_number")
    if episode is not None and (not isinstance(episode, int) or isinstance(episode, bool) or episode < 1):
        errors.append(f"{label} episode_number must be a positive integer")
    if not isinstance(post.get("caption"), str):
        errors.append(f"{label} caption must be a string")
    content_type = str(post.get("content_type", "")).casefold()
    if duration is None and any(token in content_type for token in ("reel", "video", "short")):
        warnings.append(f"{label} video-like content has no duration_seconds")


def validate_posts(posts: list[dict[str, Any]], errors: list[str], warnings: list[str]) -> dict[str, dict[str, Any]]:
    post_ids: set[str] = set()
    for index, post in enumerate(posts, start=1):
        _validate_post(post, f"posts.jsonl:{index}", post_ids, errors, warnings)
    return {
        post["post_id"]: post
        for post in posts
        if isinstance(post.get("post_id"), str) and post.get("post_id")
    }


def _validate_breakdown(snapshot: dict[str, Any], post: dict[str, Any], label: str, errors: list[str], warnings: list[str]) -> None:
    metrics = snapshot.get("metrics", {})
    breakdown = snapshot.get("platform_breakdown", {})
    if not isinstance(breakdown, dict):
        errors.append(f"{label}.platform_breakdown must be an object")
        return
    expected_platforms = set(post.get("platforms", []))
    for metric in ("plays", "likes", "comments"):
        total = metrics.get(metric)
        values = breakdown.get(metric)
        if not isinstance(total, (int, float)) or isinstance(total, bool) or not isinstance(values, dict) or not values:
            continue
        numeric = {key: value for key, value in values.items() if isinstance(value, (int, float)) and not isinstance(value, bool)}
        invalid = [value for value in values.values() if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool))]
        if invalid or any(value < 0 for value in numeric.values()):
            errors.append(f"{label} {metric} platform breakdown must contain non-negative numbers")
            continue
        subtotal = sum(numeric.values())
        complete = bool(expected_platforms) and expected_platforms.issubset(numeric)
        if complete and subtotal != total:
            errors.append(f"{label} {metric} platform sum {subtotal} != total {total}")
        elif not complete and subtotal > total:
            errors.append(f"{label} partial {metric} platform sum {subtotal} exceeds total {total}")
        elif not complete and subtotal != total:
            warnings.append(f"{label} {metric} platform breakdown is partial; sum check not enforced")


def _validate_audience(snapshot: dict[str, Any], label: str, errors: list[str], warnings: list[str]) -> None:
    audience = snapshot.get("audience", {})
    if not audience:
        return
    if not isinstance(audience, dict):
        errors.append(f"{label}.audience must be an object")
        return
    followership = {
        key: audience[key] for key in ("followers_percent", "non_followers_percent") if key in audience
    }
    follower_values = validate_percent_mapping(followership, f"{label}.audience.followership", errors)
    if len(follower_values) == 2 and abs(sum(follower_values) - 100) > 1.5:
        warnings.append(f"{label} follower audience percentages do not sum near 100%")
    for group in ("gender_percent", "age_percent"):
        if group not in audience:
            continue
        values = validate_percent_mapping(audience[group], f"{label}.audience.{group}", errors)
        if values and abs(sum(values) - 100) > 1.5:
            warnings.append(f"{label} {group} does not sum near 100%")
    if "top_countries_percent" in audience:
        validate_percent_mapping(
            audience["top_countries_percent"], f"{label}.audience.top_countries_percent", errors,
        )


def _validate_snapshot(
    snapshot: dict[str, Any],
    label: str,
    posts_by_id: dict[str, dict[str, Any]],
    snapshot_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> tuple[str, datetime] | None:
    for key in ("snapshot_id", "post_id", "captured_at", "metrics"):
        if key not in snapshot:
            errors.append(f"{label} missing {key}")
    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        errors.append(f"{label} snapshot_id must be a non-empty string")
    elif snapshot_id in snapshot_ids:
        errors.append(f"{label} duplicate snapshot_id {snapshot_id}")
    else:
        snapshot_ids.add(snapshot_id)
    post_id = snapshot.get("post_id")
    if not isinstance(post_id, str) or not post_id.strip() or post_id not in posts_by_id:
        errors.append(f"{label} references unknown post_id {post_id}")
        return None
    try:
        captured = parse_time(snapshot.get("captured_at", ""))
        published = parse_time(posts_by_id[post_id]["published_at"])
    except ValueError:
        errors.append(f"{label} invalid captured_at (ISO 8601 with offset required)")
        return None
    if captured < published:
        errors.append(f"{label} captured_at is before published_at")
    hours = snapshot.get("hours_since_publish")
    if hours is not None and (not isinstance(hours, (int, float)) or isinstance(hours, bool) or hours < 0):
        errors.append(f"{label} hours_since_publish must be non-negative")
    elif hours is not None and abs(float(hours) - (captured - published).total_seconds() / 3600) > 1:
        warnings.append(f"{label} hours_since_publish differs from timestamps by more than 1 hour")
    if snapshot.get("maturity") is not None and snapshot.get("maturity") not in MATURITY_VALUES:
        errors.append(f"{label} invalid maturity {snapshot.get('maturity')}")
    if snapshot.get("captured_at_confidence") not in (None, "low", "medium", "high"):
        errors.append(f"{label} invalid captured_at_confidence {snapshot.get('captured_at_confidence')}")
    scope = snapshot.get("platform_scope") or "combined"
    if scope != "combined" and scope not in posts_by_id[post_id].get("platforms", []):
        errors.append(f"{label} platform_scope {scope} is not in the post platforms")
    metrics = snapshot.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{label} metrics must be an object")
        return post_id, captured
    non_negative_numbers(metrics, f"{label}.metrics", errors)
    validate_percent_mapping(snapshot.get("rates_reported", {}), f"{label}.rates_reported", errors)
    _validate_breakdown(snapshot, posts_by_id[post_id], label, errors, warnings)
    sources = validate_percent_mapping(snapshot.get("traffic_sources_percent", {}), f"{label}.traffic_sources_percent", errors)
    if sources and sum(sources) > 101:
        warnings.append(f"{label} traffic source percentages sum above 101%")
    _validate_audience(snapshot, label, errors, warnings)
    return post_id, captured


def validate_snapshots(
    snapshots: list[dict[str, Any]],
    posts_by_id: dict[str, dict[str, Any]],
    errors: list[str],
    warnings: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    snapshot_ids: set[str] = set()
    latest_by_post: dict[str, dict[str, Any]] = {}
    latest_by_platform: dict[tuple[str, str], dict[str, Any]] = {}
    for index, snapshot in enumerate(snapshots, start=1):
        identity = _validate_snapshot(
            snapshot, f"insight_snapshots.jsonl:{index}", posts_by_id, snapshot_ids, errors, warnings,
        )
        if identity is None:
            continue
        post_id, captured = identity
        previous = latest_by_post.get(post_id)
        if previous is None or parse_time(previous["captured_at"]) < captured:
            latest_by_post[post_id] = snapshot
        key = (post_id, snapshot.get("platform_scope") or "combined")
        previous_platform = latest_by_platform.get(key)
        if previous_platform is None or parse_time(previous_platform["captured_at"]) < captured:
            latest_by_platform[key] = snapshot
    return latest_by_post, latest_by_platform


def _validate_experiment_row(
    experiment: dict[str, Any],
    label: str,
    post_ids: set[str],
    known_rule_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> tuple[str, int] | None:
    experiment_id = experiment.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        errors.append(f"{label} experiment_id must be a non-empty string")
        return None
    revision = experiment.get("revision", 1)
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        errors.append(f"{label} revision must be a positive integer")
        return None
    supersedes = experiment.get("supersedes_revision")
    if revision > 1 and supersedes != revision - 1:
        errors.append(f"{label} supersedes_revision must equal {revision - 1}")
    experiment_posts = experiment.get("post_ids", [])
    if not isinstance(experiment_posts, list) or not experiment_posts:
        errors.append(f"{label} post_ids must be a non-empty list")
        experiment_posts = []
    for post_id in experiment_posts:
        if not isinstance(post_id, str) or not post_id.strip() or post_id not in post_ids:
            errors.append(f"{label} references unknown post_id {post_id}")
    rule_ids = experiment.get("rule_ids", [])
    if not isinstance(rule_ids, list) or any(not isinstance(rule_id, str) for rule_id in rule_ids):
        errors.append(f"{label} rule_ids must be a list of strings")
    elif known_rule_ids:
        for rule_id in rule_ids:
            if rule_id not in known_rule_ids:
                errors.append(f"{label} references unknown rule_id {rule_id}")
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
    if status == "validated" and not (
        isinstance(independent, int) and not isinstance(independent, bool) and independent >= 2
    ):
        warnings.append(f"{label} validated with fewer than two independent samples")
    return experiment_id, revision


def validate_experiments(
    experiments: list[dict[str, Any]],
    post_ids: set[str],
    known_rule_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> dict[str, dict[str, Any]]:
    revisions: dict[str, set[int]] = {}
    latest: dict[str, dict[str, Any]] = {}
    for index, experiment in enumerate(experiments, start=1):
        identity = _validate_experiment_row(
            experiment, f"experiments.jsonl:{index}", post_ids, known_rule_ids, errors, warnings,
        )
        if identity is None:
            continue
        experiment_id, revision = identity
        seen = revisions.setdefault(experiment_id, set())
        if revision in seen:
            errors.append(f"experiments.jsonl:{index} duplicate experiment revision {experiment_id}@{revision}")
        seen.add(revision)
        if experiment_id not in latest or latest[experiment_id].get("revision", 1) < revision:
            latest[experiment_id] = experiment
    for experiment_id, values in revisions.items():
        expected = set(range(1, max(values) + 1))
        if values != expected:
            errors.append(f"experiment {experiment_id} revisions must be contiguous from 1")
    return latest
