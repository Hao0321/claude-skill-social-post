#!/usr/bin/env python3
"""Validate and summarize the structured social-post outcome store."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from social_store import load_jsonl, store_revision
from social_cohorts import MEDIA_FAMILIES, media_family as infer_media_family, owner_scope
from social_post_analysis import HEX_256, punctuation_profile
from social_validation import (
    MATURITY_VALUES, PLATFORM_VALUES, materialize_corrections, parse_time,
    validate_account_snapshots, validate_experiments, validate_posts, validate_snapshots,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SKILL_ROOT / "data"
POSTS_FILE = DATA_DIR / "posts.jsonl"
SNAPSHOTS_FILE = DATA_DIR / "insight_snapshots.jsonl"
ACCOUNT_SNAPSHOTS_FILE = DATA_DIR / "account_snapshots.jsonl"
EXPERIMENTS_FILE = DATA_DIR / "experiments.jsonl"
CORRECTIONS_FILE = DATA_DIR / "corrections.jsonl"
RULE_REGISTRY_FILE = DATA_DIR / "rule_registry.json"

MATRIX_METRIC_KEYS = (
    "plays", "views", "reached_accounts", "viewers", "average_watch_seconds",
    "followers", "followers_gained", "subscribers_gained", "interactions", "likes",
    "comments", "reposts", "shares", "saves",
)

OUTCOME_DIRECT_SNAPSHOT_KEYS = frozenset({
    "metrics", "rates_reported", "derived_rates", "traffic_sources_percent",
    "distribution_sources_percent", "audience", "ranking", "retention",
    "captured_at_confidence", "metric_qualifiers", "metric_scope_notes",
    "platform_breakdown", "surface_observations", "alternate_ui_values",
    "benchmarks_reported", "performance_comparison_reported",
    "moderation_or_delivery_note", "moderation_or_delivery_notice", "trajectory_note",
})
SNAPSHOT_CONTROL_KEYS = frozenset({
    "schema_version", "snapshot_id", "post_id", "platform_scope", "captured_at",
    "hours_since_publish", "maturity", "aggregation_eligible", "measurement_status",
    "evidence", "evidence_sha256",
})


def _configure_cli_streams() -> None:
    """Emit deterministic UTF-8 even when Windows inherited a legacy code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


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
    corrections = load_jsonl(data / CORRECTIONS_FILE.name)
    errors: list[str] = []
    warnings: list[str] = []
    posts, snapshots, account_snapshots = materialize_corrections(
        posts, snapshots, account_snapshots, corrections, errors,
    )
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
            "corrections": len(corrections),
        },
        "errors": errors,
        "warnings": warnings,
        "posts": posts,
        "latest_snapshots": latest,
        "latest_snapshots_by_platform": latest_by_platform,
        "latest_account_snapshots": latest_accounts,
        "latest_experiments": latest_experiments,
    }


def validation_json_view(result: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe validation report without changing internal tuple-key indexes."""
    value = dict(result)
    by_platform = result.get("latest_snapshots_by_platform", {})
    if isinstance(by_platform, dict):
        value["latest_snapshots_by_platform"] = [
            {
                "post_id": post_id,
                "platform_scope": platform,
                "snapshot": snapshot,
            }
            for (post_id, platform), snapshot in sorted(by_platform.items())
        ]
    latest_accounts = result.get("latest_account_snapshots", {})
    if isinstance(latest_accounts, dict):
        value["latest_account_snapshots"] = [
            {
                "platform": platform,
                "window_days": window_days,
                "measurement_surface": measurement_surface,
                "snapshot": snapshot,
            }
            for (platform, window_days, measurement_surface), snapshot in sorted(
                latest_accounts.items(),
                key=lambda item: (
                    item[0][0], item[0][1], item[0][2] or "",
                    item[1].get("captured_at") or "",
                    item[1].get("account_snapshot_id") or "",
                ),
            )
        ]
    return value


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
        "plays_qualifier": snapshot.get("metric_qualifiers", {}).get("plays", "exact") if plays is not None else None,
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


def _materialized_snapshots(root: Path) -> list[dict[str, Any]]:
    """Load corrected snapshots without changing the validator's latest indexes."""
    data = root / "data"
    errors: list[str] = []
    _posts, snapshots, _accounts = materialize_corrections(
        load_jsonl(data / POSTS_FILE.name),
        load_jsonl(data / SNAPSHOTS_FILE.name),
        load_jsonl(data / ACCOUNT_SNAPSHOTS_FILE.name),
        load_jsonl(data / CORRECTIONS_FILE.name),
        errors,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return snapshots


def _materialized_account_snapshots(root: Path) -> list[dict[str, Any]]:
    """Load every corrected account snapshot, not only the latest index entries."""
    data = root / "data"
    errors: list[str] = []
    _posts, _snapshots, accounts = materialize_corrections(
        load_jsonl(data / POSTS_FILE.name),
        load_jsonl(data / SNAPSHOTS_FILE.name),
        load_jsonl(data / ACCOUNT_SNAPSHOTS_FILE.name),
        load_jsonl(data / CORRECTIONS_FILE.name),
        errors,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return accounts


def _looks_like_file_evidence(value: str) -> bool:
    """Distinguish persisted file references from a plain-language evidence note."""
    normalized = value.replace("\\", "/")
    return Path(normalized).suffix.casefold() in {
        ".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic",
        ".mp4", ".mov", ".pdf", ".json", ".csv", ".tsv",
    }


def _provenance_record(
    record: dict[str, Any], *, record_type: str, record_id_key: str,
) -> dict[str, Any]:
    """Audit one private evidence manifest without returning paths, captions, or digests."""
    evidence = record.get("evidence")
    hashes = record.get("evidence_sha256")
    evidence_shape_valid = (
        isinstance(evidence, list)
        and bool(evidence)
        and all(isinstance(item, str) and bool(item.strip()) for item in evidence)
        and len(evidence) == len(set(evidence))
    )
    references = evidence if isinstance(evidence, list) else []
    file_references = [
        item for item in references
        if isinstance(item, str) and _looks_like_file_evidence(item)
    ]
    manifest_required = bool(file_references)
    manifest_complete = (
        isinstance(hashes, dict)
        and set(hashes) == set(references)
        and all(
            isinstance(path, str)
            and isinstance(digest, str)
            and HEX_256.fullmatch(digest)
            for path, digest in hashes.items()
        )
    )
    source_files_available = 0
    source_files_verified = 0
    source_file_digest_mismatches = 0
    if isinstance(hashes, dict):
        for source in file_references:
            path = Path(source)
            if not path.is_file():
                continue
            source_files_available += 1
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            if hashes.get(source) == observed:
                source_files_verified += 1
            else:
                source_file_digest_mismatches += 1
    complete = (
        evidence_shape_valid
        and (not manifest_required or manifest_complete)
        and source_file_digest_mismatches == 0
    )
    return {
        "record_type": record_type,
        "record_id": record.get(record_id_key),
        "evidence_reference_count": len(references),
        "file_evidence_reference_count": len(file_references),
        "digest_entry_count": len(hashes) if isinstance(hashes, dict) else 0,
        "manifest_required": manifest_required,
        "manifest_complete": manifest_complete if manifest_required else None,
        "source_files_available": source_files_available,
        "source_files_verified": source_files_verified,
        "source_file_digest_mismatches": source_file_digest_mismatches,
        "complete": complete,
    }


def provenance_coverage_report(
    insight_snapshots: list[dict[str, Any]],
    account_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check every materialized outcome record while keeping private provenance private."""
    records = [
        _provenance_record(
            snapshot, record_type="insight_snapshot", record_id_key="snapshot_id",
        )
        for snapshot in insight_snapshots
    ] + [
        _provenance_record(
            snapshot, record_type="account_snapshot", record_id_key="account_snapshot_id",
        )
        for snapshot in account_snapshots
    ]
    complete_count = sum(record["complete"] for record in records)
    return {
        "complete": complete_count == len(records),
        "checked_record_count": len(records),
        "complete_record_count": complete_count,
        "insight_snapshot_count": len(insight_snapshots),
        "account_snapshot_count": len(account_snapshots),
        "evidence_reference_count": sum(
            record["evidence_reference_count"] for record in records
        ),
        "file_evidence_reference_count": sum(
            record["file_evidence_reference_count"] for record in records
        ),
        "digest_entry_count": sum(record["digest_entry_count"] for record in records),
        "source_files_available": sum(record["source_files_available"] for record in records),
        "source_files_verified": sum(record["source_files_verified"] for record in records),
        "source_file_digest_mismatches": sum(
            record["source_file_digest_mismatches"] for record in records
        ),
        "records": records,
    }


def _has_aggregation_measurement(snapshot: dict[str, Any]) -> bool:
    metrics = snapshot.get("metrics")
    return (
        snapshot.get("aggregation_eligible") is not False
        and snapshot.get("measurement_status") != "awaiting_data"
        and isinstance(metrics, dict)
        and any(value is not None for value in metrics.values())
    )


def latest_aggregation_snapshots(
    snapshots: list[dict[str, Any]],
    *,
    platform: str | None = None,
    maturity: str | None = None,
    captured_before: str | None = None,
    group_by_maturity: bool = True,
) -> dict[tuple[str, ...], dict[str, Any]]:
    """Select the deterministic latest eligible snapshot in each comparison cohort.

    Matrix cohorts are post + exact platform scope + maturity.  Eligibility is applied
    before latest selection, so a newer awaiting/ineligible row cannot hide the latest
    usable observation.  ``captured_before`` is inclusive and requires an ISO timestamp
    with a UTC offset.
    """
    cutoff = parse_time(captured_before) if captured_before is not None else None
    latest: dict[tuple[str, ...], dict[str, Any]] = {}
    latest_order: dict[tuple[str, ...], tuple[Any, str]] = {}
    for snapshot in snapshots:
        scope = snapshot.get("platform_scope") or "combined"
        snapshot_maturity = snapshot.get("maturity")
        if platform is not None and scope != platform:
            continue
        if maturity is not None and snapshot_maturity != maturity:
            continue
        if not _has_aggregation_measurement(snapshot):
            continue
        captured = parse_time(snapshot.get("captured_at", ""))
        if cutoff is not None and captured > cutoff:
            continue
        post_id = snapshot.get("post_id")
        if not isinstance(post_id, str):
            continue
        key = (post_id, scope, str(snapshot_maturity or "unspecified")) if group_by_maturity else (
            post_id, scope,
        )
        order = (captured, str(snapshot.get("snapshot_id") or ""))
        if key not in latest_order or latest_order[key] < order:
            latest[key] = snapshot
            latest_order[key] = order
    return latest


def _selected(mapping: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    source = mapping if isinstance(mapping, dict) else {}
    return {key: source.get(key) for key in keys}


def _prompt_safe_metadata(value: Any) -> Any:
    """Keep measurement facts while removing local evidence-path provenance."""
    if isinstance(value, dict):
        return {
            key: _prompt_safe_metadata(child)
            for key, child in value.items()
            if key.casefold() not in {
                "evidence", "evidence_path", "evidence_sha256", "source_path",
                "attachment_path", "file_path",
            }
        }
    if isinstance(value, list):
        return [_prompt_safe_metadata(child) for child in value]
    if isinstance(value, str):
        normalized = value.casefold().replace("\\", "/")
        attachment_segment = "-".join(("codex", "remote", "attachments"))
        windows_user_root = "/".join(("c:", "users")) + "/"
        if attachment_segment in normalized or normalized.startswith(windows_user_root):
            return "[private source omitted]"
    return value


def _extended_analytics(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Preserve every non-control analytics subtree not already modeled directly."""
    excluded = OUTCOME_DIRECT_SNAPSHOT_KEYS | SNAPSHOT_CONTROL_KEYS
    return _prompt_safe_metadata({
        key: snapshot[key] for key in sorted(snapshot) if key not in excluded
    })


def _outcome_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    metrics = snapshot.get("metrics", {})
    return {
        "primary_metrics": {
            key: metrics[key] for key in MATRIX_METRIC_KEYS
            if isinstance(metrics, dict) and key in metrics and metrics[key] is not None
        },
        "metrics": metrics,
        "rates_reported": snapshot.get("rates_reported", {}),
        "derived_rates": snapshot.get("derived_rates", {}),
        "traffic_sources_percent": snapshot.get("traffic_sources_percent", {}),
        "distribution_sources_percent": snapshot.get("distribution_sources_percent", {}),
        "audience": snapshot.get("audience", {}),
        "ranking": snapshot.get("ranking"),
        "retention": snapshot.get("retention", {}),
        "extended_analytics": _extended_analytics(snapshot),
        "measurement_context": _prompt_safe_metadata(
            _selected(snapshot, (
                "captured_at_confidence", "metric_qualifiers", "metric_scope_notes",
                "platform_breakdown", "surface_observations", "alternate_ui_values",
                "benchmarks_reported", "performance_comparison_reported",
                "moderation_or_delivery_note", "moderation_or_delivery_notice",
                "trajectory_note",
            ))
        ),
    }


def _feature_matrix_row(post: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    formatting = post.get("format_features", {})
    wording = post.get("wording_features", {})
    publication = post.get("publication_context", {})
    return {
        "post_id": post["post_id"], "series_id": post.get("series_id"),
        "episode": post.get("episode_number"), "content_type": post.get("content_type"),
        "media_family": infer_media_family(post), "owner_scope": owner_scope(post),
        "caption": post.get("caption"),
        "caption_sha256": post.get("caption_sha256"),
        "analysis_version": post.get("analysis_version"),
        "platform": snapshot.get("platform_scope") or "combined",
        "maturity": snapshot.get("maturity"), "snapshot_id": snapshot.get("snapshot_id"),
        "captured_at": snapshot.get("captured_at"),
        "hours_since_publish": snapshot.get("hours_since_publish"),
        "caption_length": _selected(formatting, (
            "characters_including_spaces", "characters_excluding_whitespace",
            "content_characters_excluding_whitespace_and_punctuation", "spaces",
            "paragraph_count", "explicit_line_breaks", "separator_blocks", "links",
            "hashtags", "emoji",
        )),
        "punctuation_counts": _selected(formatting, (
            "full_width_commas", "enumeration_commas", "full_width_periods",
            "full_width_question_marks", "full_width_exclamation_marks",
            "corner_quote_marks", "book_title_marks",
        )),
        "punctuation_profile": punctuation_profile(str(post.get("caption") or "")),
        "layout": _selected(formatting, (
            "surface", "caption_layout", "video_orientation", "facebook_background_style",
            "background_color", "text_color", "text_weight", "alignment",
            "rendered_line_count_observed",
        )),
        "wording": _selected(wording, (
            "opening", "hook", "mechanism", "differentiator", "proof_style", "keywords",
            "named_entities", "numbers_observed", "numeric_language", "voice",
            "punctuation_style", "cta",
        )),
        "publication": {
            "published_at": post.get("published_at"),
            **_selected(publication, ("local_date", "weekday_zh_tw", "local_time", "daypart")),
        },
        "outcome": _outcome_payload(snapshot),
    }


def feature_matrix(
    root: Path,
    *,
    series_id: str | None = None,
    platform: str | None = None,
    maturity: str | None = None,
    captured_before: str | None = None,
    media_family: str | None = None,
) -> list[dict[str, Any]]:
    """Join stable post features to latest same-platform/maturity outcomes."""
    if media_family is not None and media_family not in MEDIA_FAMILIES:
        raise ValueError("unknown media family")
    result = validate_store(root)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    posts = {
        post["post_id"]: post for post in result["posts"]
        if post.get("analysis_status") == "complete"
        and post.get("analysis_eligible") is True
        and owner_scope(post) == "own"
        and (media_family is None or infer_media_family(post) == media_family)
        and (series_id is None or post.get("series_id") == series_id)
    }
    latest = latest_aggregation_snapshots(
        _materialized_snapshots(root),
        platform=platform,
        maturity=maturity,
        captured_before=captured_before,
        group_by_maturity=True,
    )
    rows: list[dict[str, Any]] = []
    for snapshot in latest.values():
        post = posts.get(snapshot.get("post_id"))
        if post is None:
            continue
        rows.append(_feature_matrix_row(post, snapshot))
    return sorted(rows, key=lambda row: (
        row["publication"].get("published_at") or "",
        row["post_id"], row["platform"], row.get("maturity") or "", row["captured_at"],
    ))


def _latest_post_platform_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse maturity variants without ever mixing platform scopes."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    latest_order: dict[tuple[str, str], tuple[Any, str]] = {}
    for row in rows:
        key = (row["post_id"], row["platform"])
        order = (parse_time(row["captured_at"]), str(row.get("snapshot_id") or ""))
        if key not in latest_order or latest_order[key] < order:
            latest[key] = row
            latest_order[key] = order
    return list(latest.values())


def _primary_outcome_marker(row: dict[str, Any]) -> dict[str, Any] | None:
    primary = row.get("outcome", {}).get("primary_metrics", {})
    if not isinstance(primary, dict):
        return None
    for metric in MATRIX_METRIC_KEYS:
        value = primary.get(metric)
        if value is not None:
            return {"metric": metric, "value": value}
    return None


def _same_minute_outcome_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose counterexamples; never turn publication time into a causal rank."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        local_time = row.get("publication", {}).get("local_time")
        marker = _primary_outcome_marker(row)
        if isinstance(local_time, str) and marker is not None:
            grouped.setdefault(local_time, []).append({
                "post_id": row["post_id"],
                "platform": row["platform"],
                **marker,
            })
    conflicts: list[dict[str, Any]] = []
    for local_time, observations in sorted(grouped.items()):
        post_ids = {observation["post_id"] for observation in observations}
        outcomes = {
            (observation["metric"], json.dumps(observation["value"], sort_keys=True))
            for observation in observations
        }
        if len(post_ids) >= 2 and len(outcomes) >= 2:
            conflicts.append({
                "local_time": local_time,
                "observations": sorted(
                    observations,
                    key=lambda value: (value["post_id"], value["platform"], value["metric"]),
                ),
            })
    return conflicts


def comparables_context(
    root: Path,
    *,
    series_id: str | None = None,
    platform: str | None = None,
    content_type: str | None = None,
    surface: str | None = None,
    maturity: str | None = None,
    captured_before: str | None = None,
    media_family: str | None = None,
    limit: int = 2,
) -> dict[str, Any]:
    """Return a compact, score-free generation context from the feature matrix."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    rows = feature_matrix(
        root,
        series_id=series_id,
        platform=platform,
        maturity=maturity,
        captured_before=captured_before,
        media_family=media_family,
    )
    rows = [row for row in rows if row["media_family"] in MEDIA_FAMILIES
            and row["platform"] != "combined" and row["owner_scope"] == "own"]
    if content_type is not None:
        rows = [row for row in rows if row.get("content_type") == content_type]
    if surface is not None:
        rows = [row for row in rows if row.get("layout", {}).get("surface") == surface]
    comparable_rows = _latest_post_platform_rows(rows) if maturity is None else list(rows)
    comparable_rows.sort(key=lambda row: (
        row.get("publication", {}).get("published_at") or "",
        row.get("captured_at") or "",
        row["post_id"], row["platform"], row.get("maturity") or "",
    ), reverse=True)
    selected = comparable_rows[:limit]
    exact_cohort = all(
        value is not None for value in (platform, maturity, content_type, surface)
    )
    exact_cohort = exact_cohort and platform != "combined" and len({row["media_family"] for row in rows}) <= 1
    return {
        "query": {
            "series_id": series_id,
            "platform": platform,
            "content_type": content_type,
            "media_family": media_family,
            "surface": surface,
            "maturity": maturity,
            "captured_before": captured_before,
            "limit": limit,
        },
        "comparison_policy": {
            "owner_scope": "own", "media_family_isolation": True,
            "cross_channel_fallback": False,
            "cohort": (
                "same_platform_maturity_content_type_and_surface"
                if exact_cohort else "incomplete_filter_set"
            ),
            "cohort_is_exact": exact_cohort,
            "outcome_comparison_allowed": exact_cohort,
            "selection": {
                "strategy": "most_recent_publication",
                "tie_breakers": [
                    "captured_at_desc", "post_id_desc", "platform_desc", "maturity_desc",
                ],
                "performance_ranked": False,
            },
            "timing": {
                "role": "candidate_variable_only",
                "causal_claim_allowed": False,
                "recommended_time": None,
                "causal_weight": None,
                "same_minute_outcome_conflicts": _same_minute_outcome_conflicts(comparable_rows),
            },
        },
        "available_count": len(comparable_rows),
        "returned_count": len(selected),
        "comparables": selected,
    }


def _coverage_expectations(post: dict[str, Any]) -> dict[str, Any]:
    formatting = post.get("format_features", {})
    publication = post.get("publication_context", {})
    return {
        "publication": {
            "published_at": post.get("published_at"),
            **_selected(publication, ("local_date", "weekday_zh_tw", "local_time", "daypart")),
        },
        "length": _selected(formatting, (
            "characters_including_spaces", "characters_excluding_whitespace",
            "content_characters_excluding_whitespace_and_punctuation", "spaces",
            "paragraph_count", "explicit_line_breaks", "separator_blocks", "links",
            "hashtags", "emoji",
        )),
        "layout": _selected(formatting, (
            "surface", "caption_layout", "video_orientation", "facebook_background_style",
            "background_color", "text_color", "text_weight", "alignment",
            "rendered_line_count_observed",
        )),
        "punctuation_counts": _selected(formatting, (
            "full_width_commas", "enumeration_commas", "full_width_periods",
            "full_width_question_marks", "full_width_exclamation_marks",
            "corner_quote_marks", "book_title_marks",
        )),
        "punctuation_profile": punctuation_profile(str(post.get("caption") or "")),
    }


def _coverage_dimensions(
    post: dict[str, Any], rows: list[dict[str, Any]], expected: dict[str, Any],
    snapshots_by_id: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    wording = post.get("wording_features", {})
    present = bool(rows)
    dimensions = {
        "caption": present and all(row.get("caption") == post.get("caption") for row in rows),
        "length": present and all(row.get("caption_length") == expected["length"] for row in rows),
        "layout": present and all(row.get("layout") == expected["layout"] for row in rows),
        "keywords": present and all(
            row.get("wording", {}).get("keywords") == wording.get("keywords") for row in rows
        ),
        "voice": present and all(
            row.get("wording", {}).get("voice") == wording.get("voice") for row in rows
        ),
        "punctuation": present and all(
            row.get("wording", {}).get("punctuation_style") == wording.get("punctuation_style")
            and row.get("punctuation_counts") == expected["punctuation_counts"]
            and row.get("punctuation_profile") == expected["punctuation_profile"]
            for row in rows
        ),
        "publication": present and all(
            row.get("publication") == expected["publication"] for row in rows
        ),
        "outcomes": present and all(
            isinstance(snapshots_by_id.get(row.get("snapshot_id")), dict)
            and row.get("outcome") == _outcome_payload(snapshots_by_id[row["snapshot_id"]])
            and bool(row.get("outcome", {}).get("primary_metrics"))
            for row in rows
        ),
    }
    extended_pairs = []
    for row in rows:
        source = snapshots_by_id.get(row.get("snapshot_id"), {})
        source_extended = _extended_analytics(source) if isinstance(source, dict) else {}
        row_extended = row.get("outcome", {}).get("extended_analytics", {})
        extended_pairs.append((source_extended, row_extended))
    extended_keys = sorted({key for source, _ in extended_pairs for key in source})
    for key in extended_keys:
        dimensions[f"outcome:{key}"] = present and all(
            (key in source_extended) == (key in row_extended)
            and (
                key not in source_extended
                or row_extended.get(key) == source_extended[key]
            )
            for source_extended, row_extended in extended_pairs
        )
    return dimensions


def _coverage_row(
    post: dict[str, Any], rows: list[dict[str, Any]],
    snapshots_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dimensions = _coverage_dimensions(
        post, rows, _coverage_expectations(post), snapshots_by_id,
    )
    missing = [key for key, present in dimensions.items() if not present]
    return {
        "post_id": post["post_id"],
        "caption_sha256": post.get("caption_sha256"),
        "analysis_version": post.get("analysis_version"),
        "snapshot_count": len(rows),
        "platform_maturities": sorted({
            f"{row['platform']}:{row.get('maturity') or 'unspecified'}" for row in rows
        }),
        "extended_analytics_keys_by_snapshot": {
            row["snapshot_id"]: sorted(
                row.get("outcome", {}).get("extended_analytics", {}).keys()
            ) for row in rows
        },
        "applicable_outcome_subtrees": sorted(
            key.removeprefix("outcome:")
            for key in dimensions
            if key.startswith("outcome:")
        ),
        "dimensions": dimensions,
        "missing": missing,
        "complete": not missing,
    }


def feature_coverage_report(root: Path) -> dict[str, Any]:
    """Prove feature and evidence preservation without exposing captions or source paths."""
    result = validate_store(root)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    eligible_posts = sorted((
        post for post in result["posts"]
        if post.get("analysis_status") == "complete" and post.get("analysis_eligible") is True
    ), key=lambda value: value["post_id"])
    materialized_snapshots = _materialized_snapshots(root)
    materialized_accounts = _materialized_account_snapshots(root)
    snapshots_by_id = {
        snapshot["snapshot_id"]: snapshot for snapshot in materialized_snapshots
        if isinstance(snapshot.get("snapshot_id"), str)
    }
    rows_by_post: dict[str, list[dict[str, Any]]] = {}
    for row in feature_matrix(root):
        rows_by_post.setdefault(row["post_id"], []).append(row)
    coverage_rows = [
        _coverage_row(post, rows_by_post.get(post["post_id"], []), snapshots_by_id)
        for post in eligible_posts
    ]
    covered = sum(row["complete"] for row in coverage_rows)
    feature_complete = covered == len(coverage_rows)
    provenance = provenance_coverage_report(
        materialized_snapshots, materialized_accounts,
    )
    return {
        "coverage_complete": feature_complete and provenance["complete"],
        "feature_coverage_complete": feature_complete,
        "provenance_complete": provenance["complete"],
        "eligible_post_count": len(coverage_rows),
        "covered_post_count": covered,
        "posts": coverage_rows,
        "provenance": provenance,
    }


def series_summary(root: Path, series_id: str | None = None) -> list[dict[str, Any]]:
    result = validate_store(root)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    posts = result["posts"]
    latest = latest_aggregation_snapshots(
        _materialized_snapshots(root), group_by_maturity=False,
    )
    rows = []
    for post in posts:
        if post.get("analysis_status") != "complete" or post.get("analysis_eligible") is not True:
            continue
        if series_id and post.get("series_id") != series_id:
            continue
        for (post_id, _platform), snapshot in latest.items():
            if post_id != post["post_id"]:
                continue
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
        plays = "—" if row["plays"] is None else str(row["plays"])
        if row.get("plays_qualifier") not in (None, "exact"):
            plays = f"{plays} ({row['plays_qualifier']})"
        values = (
            str(row["episode"]), str(row["platform"]), plays, audience, watch,
            percent(row["skip_percent"]), percent(row["discovery_percent"]),
            percent(row["profile_source_percent"]), percent(row["followers_per_play_percent"]),
        )
        output.append(" | ".join(values))
    return "\n".join(output)


def render_feature_matrix(rows: list[dict[str, Any]]) -> str:
    headers = (
        "date", "time", "weekday", "platform", "maturity", "post_id", "chars", "layout",
        "keywords", "voice", "punctuation", "CTA", "outcome", "snapshot",
    )
    output = [" | ".join(headers), " | ".join("---" for _ in headers)]

    def cell(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, list):
            value = "；".join(str(item) for item in value)
        return str(value).replace("|", "\\|").replace("\n", " ")

    for row in rows:
        publication = row["publication"]
        length = row["caption_length"]
        wording = row["wording"]
        layout = row["layout"]
        metric_text = "; ".join(
            f"{key}={value}" for key, value in row["outcome"]["primary_metrics"].items()
        ) or "—"
        values = (
            publication.get("local_date"), publication.get("local_time"),
            publication.get("weekday_zh_tw"), row["platform"], row.get("maturity"),
            row["post_id"], length.get("characters_including_spaces"),
            layout.get("caption_layout"), wording.get("keywords"), wording.get("voice"),
            (
                f"{cell(wording.get('punctuation_style'))}; "
                f"profile={cell(row.get('punctuation_profile'))}"
            ),
            wording.get("cta"), metric_text,
            row.get("snapshot_id"),
        )
        output.append(" | ".join(cell(value) for value in values))
    return "\n".join(output)


def render_comparables_context(context: dict[str, Any]) -> str:
    query = context["query"]
    timing = context["comparison_policy"]["timing"]
    output = [
        (
            f"comparables={context['returned_count']}/{context['available_count']} "
            f"platform={query.get('platform') or 'any'} "
            f"maturity={query.get('maturity') or 'latest-per-post'} "
            f"content_type={query.get('content_type') or 'any'} "
            f"surface={query.get('surface') or 'any'}"
        ),
        (
            "timing=candidate_variable_only; causal_claim_allowed=false; "
            "recommended_time=none; causal_weight=none"
        ),
        (
            "selection=most_recent_publication; performance_ranked=false; "
            f"outcome_comparison_allowed={str(context['comparison_policy']['outcome_comparison_allowed']).lower()}"
        ),
    ]
    conflicts = timing.get("same_minute_outcome_conflicts", [])
    if conflicts:
        output.append(
            "same-minute counterexamples="
            + ", ".join(str(conflict["local_time"]) for conflict in conflicts)
        )
    for index, row in enumerate(context["comparables"], start=1):
        publication = row["publication"]
        output.extend([
            "",
            f"[{index}] {row['post_id']} ({row['platform']} / {row.get('maturity') or 'unspecified'})",
            (
                "published="
                f"{publication.get('local_date')} {publication.get('weekday_zh_tw')} "
                f"{publication.get('local_time')} {publication.get('daypart')}"
            ),
            "length=" + json.dumps(row["caption_length"], ensure_ascii=False, sort_keys=True),
            "layout=" + json.dumps(row["layout"], ensure_ascii=False, sort_keys=True),
            "wording=" + json.dumps(row["wording"], ensure_ascii=False, sort_keys=True),
            "punctuation=" + json.dumps(
                {
                    "counts": row["punctuation_counts"],
                    "profile": row["punctuation_profile"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            "outcome=" + json.dumps(row["outcome"], ensure_ascii=False, sort_keys=True),
            "caption:",
            str(row.get("caption") or ""),
        ])
    return "\n".join(output)


def render_feature_coverage(report: dict[str, Any]) -> str:
    output = [
        (
            f"coverage_complete={str(report['coverage_complete']).lower()} "
            f"features={report['covered_post_count']}/{report['eligible_post_count']} "
            f"provenance={report['provenance']['complete_record_count']}/"
            f"{report['provenance']['checked_record_count']}"
        )
    ]
    for row in report["posts"]:
        status = "PASS" if row["complete"] else "FAIL"
        missing = ",".join(row["missing"]) if row["missing"] else "none"
        output.append(
            f"{status} {row['post_id']} snapshots={row['snapshot_count']} missing={missing}"
        )
    for row in report["provenance"]["records"]:
        status = "PASS" if row["complete"] else "FAIL"
        output.append(
            f"{status} provenance {row['record_type']} {row['record_id']} "
            f"evidence={row['evidence_reference_count']} digests={row['digest_entry_count']}"
        )
    return "\n".join(output)


def main() -> int:
    _configure_cli_streams()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("validate", "summary", "matrix", "comparables", "context", "coverage"),
    )
    parser.add_argument("--root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--series")
    parser.add_argument("--platform", choices=("combined", *sorted(PLATFORM_VALUES)))
    parser.add_argument("--content-type")
    parser.add_argument("--media-family", choices=MEDIA_FAMILIES)
    parser.add_argument("--surface")
    parser.add_argument("--maturity", choices=sorted(MATURITY_VALUES))
    parser.add_argument("--captured-before")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            value = validate_store(args.root)
            if args.format == "json":
                print(json.dumps(
                    validation_json_view(value), ensure_ascii=False, indent=2, default=str,
                ))
            else:
                print(f"valid={value['valid']} revision={value['revision'][:12]} counts={value['counts']}")
                for error in value["errors"]:
                    print(f"FAIL {error}")
                for warning in value["warnings"]:
                    print(f"WARN {warning}")
            return 0 if value["valid"] else 1
        if args.command == "summary":
            rows = series_summary(args.root, args.series)
            print(json.dumps(rows, ensure_ascii=False, indent=2) if args.format == "json" else render_table(rows))
            return 0
        if args.command == "coverage":
            report = feature_coverage_report(args.root)
            print(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
                if args.format == "json" else render_feature_coverage(report)
            )
            return 0 if report["coverage_complete"] else 1
        if args.command in ("comparables", "context"):
            context = comparables_context(
                args.root,
                series_id=args.series,
                platform=args.platform,
                content_type=args.content_type,
                surface=args.surface,
                maturity=args.maturity,
                captured_before=args.captured_before,
                limit=args.limit,
                media_family=args.media_family,
            )
            print(
                json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True)
                if args.format == "json" else render_comparables_context(context)
            )
            return 0
        rows = feature_matrix(
            args.root,
            series_id=args.series,
            platform=args.platform,
            maturity=args.maturity,
            captured_before=args.captured_before,
            media_family=args.media_family,
        )
        print(
            json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True)
            if args.format == "json" else render_feature_matrix(rows)
        )
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"social data error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
