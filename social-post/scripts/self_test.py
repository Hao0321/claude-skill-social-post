#!/usr/bin/env python3
"""Smoke-test structured outcomes and generated archives."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from build_rule_registry import build
from comment_self_test import run_comment_self_tests
from log_outcome import prepare_records, validate_staged
from social_data import SKILL_ROOT, series_summary, validate_store, validation_json_view
from social_data_feature_matrix_test import main as run_feature_matrix_tests
from social_post_analysis import caption_counts
from social_store import commit_records
from social_test_schema_time_validation import main as run_schema_time_tests
from social_governance_test import run_governance_tests
from social_validation import validate_posts
from social_public_sync_test import check_public_sync_guard

def check_private_baseline(result: dict) -> None:
    if not result["counts"]["posts"]:
        return
    minimum_counts = {"posts": 4, "snapshots": 6, "experiments": 3}
    if any(result["counts"].get(key, 0) < value for key, value in minimum_counts.items()):
        raise AssertionError(f"outcome store lost records: {result['counts']}")
    rows = series_summary(SKILL_ROOT, "reborn-married-driver")
    by_episode = {row["episode"]: row for row in rows if row["platform"] == "combined"}
    if not {1, 2, 3}.issubset(by_episode):
        raise AssertionError("baseline episodes disappeared")
    if 4 in by_episode:
        raise AssertionError("excluded placeholder entered series pattern learning")
    expected_watch = {1: 61.1, 2: 38.9, 3: 41.1}
    observed = {episode: by_episode[episode]["watch_percent"] for episode in expected_watch}
    if observed != expected_watch:
        raise AssertionError("baseline derived watch percentages changed")
    beyblade_rows = series_summary(SKILL_ROOT, "beyblade-battles")
    if {row["platform"] for row in beyblade_rows} != {"facebook", "instagram", "youtube"}:
        raise AssertionError("cross-platform snapshots were collapsed")
    youtube = next(row for row in beyblade_rows if row["platform"] == "youtube")
    if youtube["watch_seconds"] is not None or youtube["watch_percent"] is not None:
        raise AssertionError("missing YouTube retention was converted to zero")
    if result["counts"].get("account_snapshots", 0) < 1:
        raise AssertionError("account-level Instagram history disappeared")
    statuses = [post.get("analysis_status") for post in result["posts"]]
    if statuses.count("complete") < 7 or statuses.count("excluded_placeholder") < 1:
        raise AssertionError(f"private post analysis coverage drifted: {statuses}")
    if any(
        post.get("analysis_eligible") is not False
        for post in result["posts"] if post.get("analysis_status") == "excluded_placeholder"
    ):
        raise AssertionError("placeholder post became eligible for pattern learning")


def check_post_analysis_contract(result: dict) -> None:
    if not result["posts"]:
        return
    source = copy.deepcopy(next(
        post for post in result["posts"] if post.get("analysis_status") == "complete"
    ))
    errors: list[str] = []
    validate_posts([source], errors, [])
    if errors:
        raise AssertionError(f"positive post-analysis fixture failed: {errors}")

    def rejected(candidate: dict, label: str) -> None:
        fixture_errors: list[str] = []
        validate_posts([candidate], fixture_errors, [])
        if not fixture_errors:
            raise AssertionError(f"post-analysis negative fixture was accepted: {label}")

    caption_drift = copy.deepcopy(source)
    caption_drift["caption"] += "！"
    rejected(caption_drift, "caption changed without hash/features")
    count_drift = copy.deepcopy(source)
    count_drift["format_features"]["characters_including_spaces"] += 1
    rejected(count_drift, "caption character count drift")
    weekday_drift = copy.deepcopy(source)
    weekday_drift["publication_context"]["weekday_zh_tw"] = "星期一"
    rejected(weekday_drift, "publication weekday drift")
    bool_count = copy.deepcopy(source)
    bool_count["format_features"]["hashtags"] = False
    rejected(bool_count, "boolean caption count")
    pending_version = copy.deepcopy(source)
    pending_version["analysis_version"] = "pending"
    rejected(pending_version, "complete analysis with pending version")
    missing_evidence = copy.deepcopy(source)
    missing_evidence["analysis_evidence"] = ""
    rejected(missing_evidence, "analyzed post without evidence")
    eligible_placeholder = copy.deepcopy(source)
    eligible_placeholder.update({
        "analysis_status": "excluded_placeholder",
        "analysis_eligible": True,
        "analysis_exclusion_reason": "fixture",
    })
    rejected(eligible_placeholder, "eligible placeholder")


def check_registry_backlinks(result: dict) -> None:
    registry = build()
    rule_files = list((SKILL_ROOT / "references" / "rules").glob("R*.md"))
    if len(registry["rules"]) != len(rule_files):
        raise AssertionError("rule registry count differs from rule files")
    registry_by_id = {row["id"]: row for row in registry["rules"]}
    latest_experiments = result["latest_experiments"]
    if (SKILL_ROOT / "data" / "experiments.jsonl").exists():
        for rule_id, rule in registry_by_id.items():
            for experiment_id in rule.get("experiment_ids", []):
                experiment = latest_experiments.get(experiment_id)
                if experiment is None or rule_id not in experiment.get("rule_ids", []):
                    raise AssertionError(f"broken rule/experiment backlink: {rule_id} <-> {experiment_id}")
    for experiment_id, experiment in latest_experiments.items():
        for rule_id in experiment.get("rule_ids", []):
            if experiment_id not in registry_by_id[rule_id].get("experiment_ids", []):
                raise AssertionError(f"broken experiment/rule backlink: {experiment_id} <-> {rule_id}")


def check_archive_manifests() -> None:
    pairs = (("references/cases/manifest.json", "case-*.md"), ("references/rules/manifest.json", "R*.md"))
    for relative, pattern in pairs:
        manifest_path = SKILL_ROOT / relative
        if not manifest_path.exists():
            continue
        value = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        key = "cases" if "cases" in value else "rules"
        expected = len(list((SKILL_ROOT / Path(relative).parent).glob(pattern)))
        if len(value[key]) != expected:
            raise AssertionError(f"{relative} expected {expected}, found {len(value[key])}")
        for record in value[key]:
            if not (SKILL_ROOT / Path(relative).parent / record["path"]).exists():
                raise AssertionError(f"missing archived file: {record['path']}")


def sample_bundle(suffix: str, *, complete_analysis: bool = False) -> dict:
    post_id = f"post-{suffix}"
    post = {"post_id": post_id, "published_at": "2026-08-13T10:00:00+08:00",
            "platforms": ["facebook"], "caption": suffix}
    if complete_analysis:
        post.update({
            "published_at_confidence": "high",
            "caption_confidence": "high",
            "analysis_status": "complete",
            "analysis_version": "self-test-v1",
            "analysis_eligible": True,
            "analysis_evidence": "synthetic_self_test_fixture",
            "caption_sha256": hashlib.sha256(suffix.encode("utf-8")).hexdigest(),
            "format_features": {
                "surface": "self_test",
                "caption_layout": "single line",
                **caption_counts(suffix),
                "emoji": 0,
                "explicit_cta": 0,
            },
            "wording_features": {
                "opening": suffix,
                "hook": "fixture hook",
                "mechanism": "fixture mechanism",
                "differentiator": "fixture differentiator",
                "proof_style": "fixture proof",
                "cta": "no call to action",
                "keywords": ["fixture"],
                "named_entities": [],
                "numbers_observed": [],
                "numeric_language": [],
                "voice": ["fixture"],
                "punctuation_style": ["fixture"],
            },
            "publication_context": {
                "local_date": "2026-08-13",
                "weekday_zh_tw": "星期四",
                "local_time": "10:00",
                "daypart": "self_test",
            },
        })
    return {
        "post": post,
        "snapshot": {"snapshot_id": f"snapshot-{suffix}", "post_id": post_id,
                     "captured_at": "2026-08-13T11:00:00+08:00", "metrics": {}},
    }


def check_concurrent_writer() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-concurrency-") as raw:
        data_dir = Path(raw) / "data"
        first, _, first_revision = prepare_records(sample_bundle("first"), data_dir)
        second, _, second_revision = prepare_records(sample_bundle("second"), data_dir)
        validate_staged(first)
        validate_staged(second)
        commit_records(first, data_dir=data_dir, expected_revision=first_revision)
        try:
            commit_records(second, data_dir=data_dir, expected_revision=second_revision)
        except RuntimeError:
            return
        raise AssertionError("stale concurrent writer was not rejected")


def check_account_snapshot() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-account-") as raw:
        data_dir = Path(raw) / "data"
        bundle = {"account_snapshot": {
            "account_snapshot_id": "ig-account-30d-test", "platform": "instagram",
            "captured_at": "2026-08-13T17:03:00+08:00", "window_days": 30,
            "metrics": {"reel_views": 100, "net_followers": 2},
        }}
        staged, _, revision = prepare_records(bundle, data_dir)
        validate_staged(staged)
        commit_records(staged, data_dir=data_dir, expected_revision=revision)


def check_append_only_corrections() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-correction-") as raw:
        root = Path(raw)
        data_dir = root / "data"
        bundle = sample_bundle("corrected")
        bundle["post"]["content_type"] = "short_video"
        bundle["snapshot"]["metrics"] = {"plays": 1200}
        bundle["correction"] = {
            "correction_id": "correction-duration-and-precision",
            "target_type": "post",
            "target_id": "post-corrected",
            "recorded_at": "2026-08-13T12:00:00+08:00",
            "changes": {"duration_seconds": 30},
            "reason": "duration confirmed from source media",
        }
        staged, _, revision = prepare_records(bundle, data_dir)
        validate_staged(staged)
        commit_records(staged, data_dir=data_dir, expected_revision=revision)
        result = validate_store(root)
        if result["posts"][0].get("duration_seconds") != 30:
            raise AssertionError("post correction was not materialized")
        raw_post = json.loads((data_dir / "posts.jsonl").read_text(encoding="utf-8"))
        if "duration_seconds" in raw_post:
            raise AssertionError("correction mutated the original post event")

        invalid = {"correction": {
            "correction_id": "correction-illegal-identity",
            "target_type": "post",
            "target_id": "post-corrected",
            "recorded_at": "2026-08-13T13:00:00+08:00",
            "changes": {"post_id": "different"},
            "reason": "negative control",
        }}
        rejected, _, _ = prepare_records(invalid, data_dir)
        try:
            validate_staged(rejected)
        except ValueError:
            pass
        else:
            raise AssertionError("identity-changing correction was accepted")


def check_metric_qualifiers() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-qualifier-") as raw:
        root = Path(raw)
        data_dir = root / "data"
        bundle = sample_bundle("rounded", complete_analysis=True)
        bundle["snapshot"]["metrics"] = {"plays": 86000}
        bundle["snapshot"]["metric_qualifiers"] = {"plays": "rounded"}
        staged, _, revision = prepare_records(bundle, data_dir)
        validate_staged(staged)
        commit_records(staged, data_dir=data_dir, expected_revision=revision)
        rows = series_summary(root)
        if rows[0].get("plays_qualifier") != "rounded":
            raise AssertionError("metric precision qualifier disappeared from summary")

        dotted = sample_bundle("dotted-qualifier", complete_analysis=True)
        dotted["snapshot"]["metrics"] = {"plays": 100}
        dotted["snapshot"]["benchmarks_reported"] = {"views_more_than_usual_approx": 80}
        dotted["snapshot"]["metric_qualifiers"] = {
            "benchmarks_reported.views_more_than_usual_approx": "rounded"
        }
        staged, _, _ = prepare_records(dotted, data_dir)
        validate_staged(staged)

        invalid = sample_bundle("missing-dotted-qualifier", complete_analysis=True)
        invalid["snapshot"]["metrics"] = {"plays": 100}
        invalid["snapshot"]["metric_qualifiers"] = {
            "benchmarks_reported.not_present": "rounded"
        }
        rejected, _, _ = prepare_records(invalid, data_dir)
        try:
            validate_staged(rejected)
        except ValueError:
            pass
        else:
            raise AssertionError("missing dotted-path metric qualifier was accepted")


def check_aggregation_exclusion() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-aggregation-") as raw:
        root = Path(raw)
        data_dir = root / "data"
        bundle = sample_bundle("awaiting-data", complete_analysis=True)
        bundle["snapshot"]["metrics"] = {"plays": 100}
        bundle["snapshot"]["aggregation_eligible"] = False
        staged, _, revision = prepare_records(bundle, data_dir)
        validate_staged(staged)
        commit_records(staged, data_dir=data_dir, expected_revision=revision)
        if series_summary(root):
            raise AssertionError("aggregation_eligible=false snapshot entered series summary")




def main() -> int:
    import sys
    from social_snapshot_test import run_self_test as run_snapshot_tests
    run_snapshot_tests(sys.modules[__name__])
    result = validate_store()
    if not result["valid"]:
        raise AssertionError(result["errors"])
    json.dumps(validation_json_view(result), ensure_ascii=False)
    check_private_baseline(result)
    check_post_analysis_contract(result)
    check_registry_backlinks(result)
    check_archive_manifests()
    check_concurrent_writer()
    check_account_snapshot()
    check_append_only_corrections()
    check_metric_qualifiers()
    check_aggregation_exclusion()
    check_public_sync_guard()
    run_feature_matrix_tests()
    run_schema_time_tests()
    run_governance_tests()
    run_intake_review_tests()
    run_comment_self_tests()
    print("self-test passed")
    return 0


def run_intake_review_tests() -> None:
    import unittest
    import review_outcome_intakes_test
    import social_intake_analysis_test
    import social_outcome_time_policy_test
    import social_ask_gate_test

    suite = unittest.defaultTestLoader.loadTestsFromModule(review_outcome_intakes_test)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(social_ask_gate_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(social_intake_analysis_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(social_outcome_time_policy_test))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise AssertionError("outcome intake review tests failed")


if __name__ == "__main__":
    raise SystemExit(main())
