#!/usr/bin/env python3
"""Focused regression tests for outcome schema, timezone and experiment gates."""

from __future__ import annotations

import copy
import hashlib
from unittest import mock
from zoneinfo import ZoneInfoNotFoundError

from social_post_analysis import caption_counts
from social_validation import (
    materialize_corrections,
    validate_account_snapshots,
    validate_experiments,
    validate_posts,
    validate_snapshots,
)


def analyzed_post() -> dict:
    caption = "同步貼文測試！"
    digest = hashlib.sha256(caption.encode("utf-8")).hexdigest()
    media_digest = hashlib.sha256(b"same-source-media").hexdigest()
    return {
        "schema_version": "1.0",
        "post_id": "post-schema-time-test",
        "published_at": "2026-08-30T10:00:00+08:00",
        "published_at_confidence": "high",
        "timezone": "Asia/Taipei",
        "platforms": ["facebook", "instagram"],
        "caption": caption,
        "caption_confidence": "high",
        "caption_sha256": digest,
        "analysis_status": "complete",
        "analysis_version": "schema-time-test-v1",
        "analysis_eligible": True,
        "analysis_evidence": "synthetic focused regression fixture",
        "content_type": "background_text_post",
        "format_features": {
            "surface": "facebook_background_text",
            "caption_layout": "single line",
            **caption_counts(caption),
            "emoji": 0,
            "explicit_cta": 0,
            "facebook_background_style": True,
            "background_color": "black",
            "text_color": "white",
            "text_weight": "bold",
            "alignment": "center",
            "rendered_line_count_observed": 1,
        },
        "wording_features": {
            "opening": caption,
            "hook": "同步貼文測試",
            "mechanism": "focused fixture",
            "differentiator": "focused fixture",
            "proof_style": "synthetic evidence",
            "cta": "無明確 CTA",
            "keywords": ["同步貼文"],
            "named_entities": [],
            "numbers_observed": [],
            "numeric_language": [],
            "voice": ["直接"],
            "punctuation_style": ["全形驚嘆號"],
        },
        "publication_context": {
            "local_date": "2026-08-30",
            "weekday_zh_tw": "星期日",
            "local_time": "10:00",
            "daypart": "週日上午",
        },
        "platform_publications": {
            platform: {
                "published_at": f"2026-08-30T10:0{minute}:00+08:00",
                "timezone": "Asia/Taipei",
                "sync_mode": "same_copy_manual",
                "caption_sha256": digest,
                "media_sha256": media_digest,
            }
            for platform, minute in (("facebook", 0), ("instagram", 2))
        },
    }


def post_errors(post: dict) -> list[str]:
    errors: list[str] = []
    validate_posts([post], errors, [])
    return errors


def require_rejection(candidate: dict, fragment: str) -> None:
    errors = post_errors(candidate)
    if not any(fragment in error for error in errors):
        raise AssertionError(f"expected {fragment!r}, received {errors}")


def check_post_schema_and_timezone() -> None:
    source = analyzed_post()
    if errors := post_errors(source):
        raise AssertionError(f"valid post fixture failed: {errors}")

    unsupported = copy.deepcopy(source)
    unsupported["schema_version"] = "9.9"
    require_rejection(unsupported, "schema_version")

    legacy = copy.deepcopy(source)
    legacy.pop("schema_version")
    legacy.pop("timezone")
    if errors := post_errors(legacy):
        raise AssertionError(f"pre-versioned legacy post stopped validating: {errors}")

    versioned_without_zone = copy.deepcopy(source)
    versioned_without_zone.pop("timezone")
    require_rejection(versioned_without_zone, "IANA timezone name")

    invalid_zone = copy.deepcopy(source)
    invalid_zone["timezone"] = "Taipei/Not-A-Zone"
    require_rejection(invalid_zone, "recognized IANA timezone")

    misspelled_zone = copy.deepcopy(source)
    misspelled_zone["timezone"] = "Asia/Taipe"
    require_rejection(misspelled_zone, "recognized IANA timezone")

    wrong_offset = copy.deepcopy(source)
    wrong_offset["published_at"] = "2026-08-30T10:00:00+00:00"
    require_rejection(wrong_offset, "UTC offset does not match timezone")

    wrong_weekday = copy.deepcopy(source)
    wrong_weekday["publication_context"]["weekday_zh_tw"] = "星期一"
    require_rejection(wrong_weekday, "publication_context.weekday_zh_tw")

    wrong_date = copy.deepcopy(source)
    wrong_date["publication_context"]["local_date"] = "2026-08-29"
    require_rejection(wrong_date, "publication_context.local_date")

    wrong_minute = copy.deepcopy(source)
    wrong_minute["publication_context"]["local_time"] = "10:01"
    require_rejection(wrong_minute, "publication_context.local_time")


def check_missing_timezone_database() -> None:
    """A Python without tz data (Windows without tzdata) still rejects, with an install hint."""
    def no_database(name: str):
        raise ZoneInfoNotFoundError(f"No time zone found with key {name}")

    with mock.patch("social_validation.ZoneInfo", side_effect=no_database),             mock.patch("social_validation.available_timezones", return_value=set()):
        errors = post_errors(analyzed_post())
    if not any("no IANA timezone database" in error and "pip install tzdata" in error
               for error in errors):
        raise AssertionError(f"expected a missing tz database rejection, received {errors}")
    if any("is not a recognized IANA timezone" in error for error in errors):
        raise AssertionError(f"missing tz database was reported as a bad name: {errors}")


def check_platform_publications() -> None:
    source = analyzed_post()

    bad_keys = copy.deepcopy(source)
    bad_keys["platform_publications"]["youtube"] = bad_keys["platform_publications"].pop("instagram")
    require_rejection(bad_keys, "keys must exactly match platforms")

    non_string_key = copy.deepcopy(source)
    non_string_key["platform_publications"][1] = non_string_key["platform_publications"].pop("instagram")
    require_rejection(non_string_key, "invalid platform keys")

    bad_zone = copy.deepcopy(source)
    bad_zone["platform_publications"]["instagram"]["timezone"] = "Invalid/Zone"
    require_rejection(bad_zone, "recognized IANA timezone")

    bad_offset = copy.deepcopy(source)
    bad_offset["platform_publications"]["instagram"]["published_at"] = (
        "2026-08-30T10:02:00+00:00"
    )
    require_rejection(bad_offset, "UTC offset does not match timezone")

    bad_digest = copy.deepcopy(source)
    bad_digest["platform_publications"]["facebook"]["media_sha256"] = "not-a-digest"
    require_rejection(bad_digest, "media_sha256 must be a lowercase SHA-256 digest")

    bad_sync_mode = copy.deepcopy(source)
    bad_sync_mode["platform_publications"]["facebook"]["sync_mode"] = "automatic"
    require_rejection(bad_sync_mode, "sync_mode must be one of")

    mismatched_same_copy = copy.deepcopy(source)
    mismatched_same_copy["platform_publications"]["instagram"]["caption_sha256"] = "a" * 64
    require_rejection(mismatched_same_copy, "must match the post caption")

    adapted = copy.deepcopy(source)
    adapted["platform_publications"]["instagram"]["sync_mode"] = "platform_adapted"
    adapted["platform_publications"]["instagram"]["caption_sha256"] = "a" * 64
    if errors := post_errors(adapted):
        raise AssertionError(f"platform-adapted caption was rejected: {errors}")


def experiment_errors(experiment: dict, post_ids: set[str]) -> list[str]:
    errors: list[str] = []
    validate_experiments([experiment], post_ids, set(), errors, [])
    return errors


def check_validated_experiment_gate() -> None:
    post_ids = {"post-a", "post-b"}
    emerging = {
        "schema_version": "1.1",
        "experiment_id": "exp-focused",
        "revision": 1,
        "post_ids": ["post-a"],
        "rule_ids": [],
        "evidence": {"status": "emerging", "independent_samples": False},
    }
    if errors := experiment_errors(emerging, post_ids):
        raise AssertionError(f"emerging evidence incorrectly hit validated gate: {errors}")

    too_few = copy.deepcopy(emerging)
    too_few["evidence"] = {"status": "validated", "independent_samples": 1}
    errors = experiment_errors(too_few, post_ids)
    if not any("at least two independent samples" in error for error in errors):
        raise AssertionError(f"validated single-sample experiment passed: {errors}")

    no_control = copy.deepcopy(emerging)
    no_control["post_ids"] = ["post-a", "post-b"]
    no_control["evidence"] = {"status": "validated", "independent_samples": 2}
    no_control["variants"] = {"treatment": "black card", "comparison": "text post"}
    errors = experiment_errors(no_control, post_ids)
    if not any("variants.control" in error for error in errors):
        raise AssertionError(f"validated experiment without control passed: {errors}")

    valid = copy.deepcopy(no_control)
    valid["variants"] = {"treatment": "black card", "control": "plain text"}
    if errors := experiment_errors(valid, post_ids):
        raise AssertionError(f"valid controlled experiment failed: {errors}")


def check_every_ledger_has_a_schema_gate() -> None:
    source = analyzed_post()
    post_validation_errors: list[str] = []
    posts_by_id = validate_posts([source], post_validation_errors, [])
    if post_validation_errors:
        raise AssertionError(f"post fixture failed before ledger checks: {post_validation_errors}")

    snapshot_errors: list[str] = []
    validate_snapshots(
        [{
            "schema_version": "9.9",
            "snapshot_id": "snapshot-schema-gate",
            "post_id": source["post_id"],
            "captured_at": "2026-08-30T11:00:00+08:00",
            "metrics": {},
        }],
        posts_by_id,
        snapshot_errors,
        [],
    )
    if not any("schema_version" in error for error in snapshot_errors):
        raise AssertionError(f"snapshot unsupported schema passed: {snapshot_errors}")

    account_errors: list[str] = []
    validate_account_snapshots(
        [{
            "schema_version": "9.9",
            "account_snapshot_id": "account-schema-gate",
            "platform": "facebook",
            "captured_at": "2026-08-30T11:00:00+08:00",
            "window_days": 30,
            "metrics": {},
        }],
        account_errors,
        [],
    )
    if not any("schema_version" in error for error in account_errors):
        raise AssertionError(f"account snapshot unsupported schema passed: {account_errors}")

    experiment = {
        "schema_version": "9.9",
        "experiment_id": "experiment-schema-gate",
        "revision": 1,
        "post_ids": [source["post_id"]],
        "rule_ids": [],
        "evidence": {"status": "emerging"},
    }
    errors = experiment_errors(experiment, {source["post_id"]})
    if not any("schema_version" in error for error in errors):
        raise AssertionError(f"experiment unsupported schema passed: {errors}")

    correction_errors: list[str] = []
    materialize_corrections(
        [source],
        [],
        [],
        [{
            "schema_version": "9.9",
            "correction_id": "correction-schema-gate",
            "recorded_at": "2026-08-30T11:00:00+08:00",
            "target_type": "post",
            "target_id": source["post_id"],
            "changes": {"caption_confidence": "medium"},
        }],
        correction_errors,
    )
    if not any("schema_version" in error for error in correction_errors):
        raise AssertionError(f"correction unsupported schema passed: {correction_errors}")


def _check_post_snapshot_evidence_manifest() -> None:
    source = analyzed_post()
    post_validation_errors: list[str] = []
    posts_by_id = validate_posts([source], post_validation_errors, [])
    if post_validation_errors:
        raise AssertionError(f"post fixture failed before evidence checks: {post_validation_errors}")

    snapshot = {
        "schema_version": "1.0",
        "snapshot_id": "snapshot-evidence-manifest",
        "post_id": source["post_id"],
        "captured_at": "2026-08-30T11:00:00+08:00",
        "metrics": {"views": 1},
        "evidence": ["private-attachment.jpg"],
        "evidence_sha256": {
            "private-attachment.jpg": hashlib.sha256(b"private-attachment").hexdigest(),
        },
    }

    def snapshot_errors(candidate: dict) -> list[str]:
        errors: list[str] = []
        validate_snapshots([candidate], posts_by_id, errors, [])
        return errors

    if errors := snapshot_errors(snapshot):
        raise AssertionError(f"valid evidence manifest failed: {errors}")
    missing_digest = copy.deepcopy(snapshot)
    missing_digest["evidence_sha256"] = {}
    if not any("exactly match" in error for error in snapshot_errors(missing_digest)):
        raise AssertionError("missing evidence digest passed")
    extra_digest = copy.deepcopy(snapshot)
    extra_digest["evidence_sha256"]["other.jpg"] = "a" * 64
    if not any("exactly match" in error for error in snapshot_errors(extra_digest)):
        raise AssertionError("extra evidence digest passed")
    invalid_digest = copy.deepcopy(snapshot)
    invalid_digest["evidence_sha256"]["private-attachment.jpg"] = "not-a-digest"
    if not any("map evidence paths" in error for error in snapshot_errors(invalid_digest)):
        raise AssertionError("invalid evidence digest passed")
    duplicate_path = copy.deepcopy(snapshot)
    duplicate_path["evidence"].append("private-attachment.jpg")
    if not any("must be unique" in error for error in snapshot_errors(duplicate_path)):
        raise AssertionError("duplicate evidence path passed")


def _account_evidence_manifest_fixture() -> dict:
    return {
        "schema_version": "1.0",
        "account_snapshot_id": "account-evidence-manifest",
        "platform": "instagram",
        "captured_at": "2026-08-30T11:00:00+08:00",
        "window_days": 30,
        "measurement_surface": "account_overview",
        "metrics": {"views": 1},
        "evidence": ["private-account-attachment.jpg"],
        "evidence_sha256": {
            "private-account-attachment.jpg": hashlib.sha256(
                b"private-account-attachment"
            ).hexdigest(),
        },
    }


def _check_account_evidence_manifest(account: dict) -> None:
    def account_errors(candidate: dict) -> list[str]:
        errors: list[str] = []
        validate_account_snapshots([candidate], errors, [])
        return errors

    if errors := account_errors(account):
        raise AssertionError(f"valid account evidence manifest failed: {errors}")
    missing_account_digest = copy.deepcopy(account)
    missing_account_digest["evidence_sha256"] = {}
    if not any(
        "exactly match" in error for error in account_errors(missing_account_digest)
    ):
        raise AssertionError("account snapshot missing evidence digest passed")
    invalid_account_digest = copy.deepcopy(account)
    invalid_account_digest["evidence_sha256"]["private-account-attachment.jpg"] = "bad"
    if not any(
        "map evidence paths" in error for error in account_errors(invalid_account_digest)
    ):
        raise AssertionError("account snapshot invalid evidence digest passed")


def _check_account_evidence_manifest_correction(account: dict) -> None:
    legacy_account = copy.deepcopy(account)
    legacy_account["evidence"] = ["C:/private/account.jpg"]
    legacy_account["evidence_sha256"] = {"account.jpg": "a" * 64}
    correction_errors: list[str] = []
    _posts, _snapshots, corrected_accounts = materialize_corrections(
        [],
        [],
        [legacy_account],
        [{
            "schema_version": "1.0",
            "correction_id": "normalize-account-evidence-map",
            "recorded_at": "2026-08-30T12:00:00+08:00",
            "target_type": "account_snapshot",
            "target_id": legacy_account["account_snapshot_id"],
            "changes": {
                "evidence_sha256": {"C:/private/account.jpg": "b" * 64},
            },
        }],
        correction_errors,
    )
    if correction_errors:
        raise AssertionError(f"account evidence correction failed: {correction_errors}")
    if corrected_accounts[0]["evidence_sha256"] != {
        "C:/private/account.jpg": "b" * 64,
    }:
        raise AssertionError("evidence manifest correction merged obsolete path keys")


def check_snapshot_evidence_manifest() -> None:
    _check_post_snapshot_evidence_manifest()
    account = _account_evidence_manifest_fixture()
    _check_account_evidence_manifest(account)
    _check_account_evidence_manifest_correction(account)


def check_account_latest_surface_index() -> None:
    def account(snapshot_id: str, surface: str, views: int) -> dict:
        return {
            "schema_version": "1.0",
            "account_snapshot_id": snapshot_id,
            "platform": "instagram",
            "captured_at": "2026-08-30T11:00:00+08:00",
            "window_days": 30,
            "measurement_surface": surface,
            "metrics": {"views": views},
        }

    errors: list[str] = []
    latest = validate_account_snapshots([
        account("account-overview", "account_overview", 1),
        account("account-ranking-a", "reel_rankings", 2),
        account("account-ranking-z", "reel_rankings", 3),
    ], errors, [])
    if errors:
        raise AssertionError(f"account latest surface fixture failed: {errors}")
    if set(latest) != {
        ("instagram", 30, "account_overview"),
        ("instagram", 30, "reel_rankings"),
    }:
        raise AssertionError(f"account measurement surfaces were collapsed: {latest}")
    if latest[("instagram", 30, "reel_rankings")]["account_snapshot_id"] != (
        "account-ranking-z"
    ):
        raise AssertionError("equal-time account snapshots lack a deterministic ID tie-break")


def main() -> int:
    check_post_schema_and_timezone()
    check_missing_timezone_database()
    check_platform_publications()
    check_validated_experiment_gate()
    check_every_ledger_has_a_schema_gate()
    check_snapshot_evidence_manifest()
    check_account_latest_surface_index()
    print("PASS social schema/time validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
