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
from social_test_hermes_tweet_contract import main as run_hermes_tweet_contract_tests
from social_test_schema_time_validation import main as run_schema_time_tests
from social_validation import validate_posts
from sync_public import (
    candidates,
    forbidden_public_paths,
    managed_paths,
    privacy_violations,
    public_generated_cache_paths,
    public_tree_rows,
    purge_public_generated,
    safe_destination,
    write_manifest,
)


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
    if statuses.count("complete") != 7 or statuses.count("excluded_placeholder") != 1:
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


def check_private_binary_tokens(candidate: Path) -> None:
    private_config_path = SKILL_ROOT / "audit.config.json"
    if not private_config_path.exists():
        return
    private_config = json.loads(private_config_path.read_text(encoding="utf-8-sig"))
    private_tokens = private_config.get("sync", {}).get("privacy", {}).get("tokens", [])[-3:]
    if len(private_tokens) != 3:
        raise AssertionError("private 8/27 privacy fixtures are missing")
    for token_index, token in enumerate(private_tokens):
        case_variant = "".join(
            char.swapcase() if char.isascii() and char.isalpha() else char for char in token
        )
        token_variants = (
            b"\xff" + case_variant.encode("utf-8"),
            case_variant.encode("utf-16-le"),
            case_variant.encode("utf-16-be"),
            b"\xff\xfe" + case_variant.encode("utf-16-le"),
            b"\xfe\xff" + case_variant.encode("utf-16-be"),
        )
        token_config = {"sync": {"privacy": {"tokens": [token], "patterns": []}}}
        for encoding_index, payload in enumerate(token_variants):
            candidate.write_bytes(payload)
            if not privacy_violations(
                [(candidate, f"private-token-{token_index}-{encoding_index}.bin")], token_config
            ):
                raise AssertionError(
                    f"private token {token_index} encoding {encoding_index} escaped the privacy scan"
                )


def check_public_privacy_guard(candidate: Path) -> None:
    config = {"sync": {"privacy": {"tokens": ["private-account"], "patterns": []}}}
    candidate.write_text("contains private-account marker", encoding="utf-8")
    if not privacy_violations([(candidate, "candidate.md")], config):
        raise AssertionError("public sync privacy token was not blocked")
    secret_fixture = "Author" + "ization: " + "Bearer " + "private-" + "secret-value"
    candidate.write_text(secret_fixture, encoding="utf-8")
    pattern_config = {"sync": {"privacy": {"tokens": [], "patterns": [
        r"(?i)Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~-]{8,}",
    ]}}}
    if not privacy_violations([(candidate, "candidate.md")], pattern_config):
        raise AssertionError("public sync credential-shaped pattern was not blocked")
    candidate.write_bytes(
        b"\xff\x00Author" + b"ization: " + b"Bearer " + b"private-secret-value\x00"
        + "私人里程碑".encode("utf-16-le")
    )
    binary_config = {"sync": {"privacy": {
        "tokens": ["私人里程碑"], "patterns": pattern_config["sync"]["privacy"]["patterns"],
    }}}
    if len(privacy_violations([(candidate, "candidate.pyc")], binary_config)) != 2:
        raise AssertionError("public sync binary privacy scan missed a token or secret pattern")
    credential = "Author" + "ization: " + "Bearer " + "private-" + "secret-value"
    credential_variants = (
        b"\xff" + credential.encode("utf-8"), credential.encode("utf-16-le"),
        credential.encode("utf-16-be"), b"\xff\xfe" + credential.encode("utf-16-le"),
        b"\xfe\xff" + credential.encode("utf-16-be"),
    )
    for index, payload in enumerate(credential_variants):
        candidate.write_bytes(payload)
        if not privacy_violations([(candidate, f"credential-{index}.bin")], pattern_config):
            raise AssertionError(f"binary credential encoding {index} escaped the privacy scan")
    check_private_binary_tokens(candidate)


def check_public_generated_guard(root: Path) -> None:
    config = {"sync": {"purge_public_generated": ["scripts/__pycache__"]}}
    if public_generated_cache_paths(config) != {"scripts/__pycache__"}:
        raise AssertionError("public generated-cache allowlist did not normalize")
    cache_dir = root / "scripts" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "fixture.pyc").write_bytes(b"generated")
    if purge_public_generated(root, config) != ["scripts/__pycache__"] or cache_dir.exists():
        raise AssertionError("configured public generated cache was not removed")
    try:
        public_generated_cache_paths({"sync": {"purge_public_generated": ["scripts/**/__pycache__"]}})
    except ValueError:
        return
    raise AssertionError("public generated-cache allowlist accepted a glob")


def check_public_inventory_guard(root: Path, candidate: Path) -> None:
    candidate.write_text("public fixture", encoding="utf-8")
    try:
        safe_destination(root, "../escape.txt")
    except ValueError:
        pass
    else:
        raise AssertionError("public sync accepted a path outside its root")
    write_manifest(root, ["safe.md"])
    if managed_paths(root) != {"safe.md"}:
        raise AssertionError("public sync managed manifest did not round-trip")
    unmanaged = root / "unmanaged-example.md"
    unmanaged.write_text("contains private-account marker", encoding="utf-8")
    config = {"sync": {"privacy": {"tokens": ["private-account"], "patterns": []}}}
    public_rows, public_failures = public_tree_rows(root)
    if public_failures or not privacy_violations(public_rows, config):
        raise AssertionError("unmanaged public file escaped the privacy scan")
    unmanaged.unlink()
    linked = root / "linked-example.md"
    try:
        linked.symlink_to(candidate)
    except OSError:
        pass
    else:
        _public_rows, public_failures = public_tree_rows(root)
        if not public_failures:
            raise AssertionError("linked public path escaped the privacy scan")
        linked.unlink()
    (root / "safe.md").write_text("public", encoding="utf-8")
    (root / "private.jsonl").write_text('{"author":"private"}\n', encoding="utf-8")
    fixture_ignore = ["candidate.md", ".social-post-managed.json"]
    allowlist = {"sync": {"include": ["safe.md"], "ignore": [
        *fixture_ignore, "private.jsonl",
    ]}, "exclude": []}
    if [relative for _path, relative in candidates(allowlist, root)] != ["safe.md"]:
        raise AssertionError("public sync copied a file outside the closed-world allowlist")
    try:
        candidates({"sync": {"include": ["safe.md"], "ignore": fixture_ignore}, "exclude": []}, root)
    except ValueError:
        pass
    else:
        raise AssertionError("public sync silently accepted an unclassified private file")
    try:
        candidates({"sync": {"ignore": []}}, root)
    except ValueError:
        pass
    else:
        raise AssertionError("public sync accepted a missing include allowlist")
    if forbidden_public_paths({"sync": {"forbid_public": ["audit.config.json"]}}) != {
        "audit.config.json"
    }:
        raise AssertionError("public sync lost its exact private-only path contract")
    try:
        forbidden_public_paths({"sync": {"forbid_public": ["*.json"]}})
    except ValueError:
        return
    raise AssertionError("public sync accepted a destructive forbidden-path glob")


def check_public_sync_guard() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-public-guard-") as raw:
        root = Path(raw)
        candidate = root / "candidate.md"
        check_public_privacy_guard(candidate)
        check_public_generated_guard(root)
        check_public_inventory_guard(root, candidate)


def main() -> int:
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
    run_hermes_tweet_contract_tests()
    run_feature_matrix_tests()
    run_schema_time_tests()
    run_comment_self_tests()
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
