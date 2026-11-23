#!/usr/bin/env python3
"""Focused regression tests for the deterministic feature comparison matrix."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from social_data import (
    _coverage_dimensions, _coverage_expectations, _materialized_snapshots,
    comparables_context, feature_coverage_report, feature_matrix,
    latest_aggregation_snapshots, provenance_coverage_report,
    render_comparables_context, series_summary, observation_history,
)
from social_post_analysis import caption_counts
from social_store import write_jsonl


SCRIPT = Path(__file__).with_name("social_data.py")


def _post() -> dict:
    caption = "測試 AI 版型！"
    return {
        "schema_version": "1.0",
        "post_id": "post-feature-matrix",
        "series_id": "feature-matrix-fixture",
        "episode_number": 1,
        "published_at": "2026-08-29T10:00:00+08:00",
        "published_at_confidence": "high",
        "timezone": "Asia/Taipei",
        "platforms": ["facebook", "instagram"],
        "content_type": "background_text_post",
        "caption": caption,
        "caption_confidence": "high",
        "analysis_status": "complete",
        "analysis_version": "feature-matrix-test-v1",
        "analysis_eligible": True,
        "analysis_evidence": "synthetic focused test",
        "caption_sha256": hashlib.sha256(caption.encode("utf-8")).hexdigest(),
        "format_features": {
            "surface": "facebook_background_text",
            "caption_layout": "single paragraph rendered as a centered 2-line card",
            **caption_counts(caption),
            "emoji": 0,
            "explicit_cta": 1,
            "facebook_background_style": True,
            "background_color": "black",
            "text_color": "white",
            "text_weight": "bold",
            "alignment": "center",
            "rendered_line_count_observed": 2,
        },
        "wording_features": {
            "opening": "測試",
            "hook": "AI 版型",
            "mechanism": "黑底白字",
            "differentiator": "短句",
            "proof_style": "synthetic",
            "keywords": ["AI", "版型", "ムービー"],
            "named_entities": ["AI"],
            "numbers_observed": [],
            "numeric_language": [],
            "voice": ["直接", "高能量"],
            "punctuation_style": ["單驚嘆號收尾"],
            "cta": "測試 CTA",
        },
        "publication_context": {
            "local_date": "2026-08-29",
            "weekday_zh_tw": "星期六",
            "local_time": "10:00",
            "daypart": "週末上午",
        },
    }


def _snapshot(
    snapshot_id: str,
    platform: str,
    captured_at: str,
    maturity: str,
    viewers: int,
    *,
    post_id: str = "post-feature-matrix",
    aggregation_eligible: bool | None = None,
    measurement_status: str | None = None,
) -> dict:
    evidence_path = f"C:/fixture/{snapshot_id}.jpg"
    row = {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "post_id": post_id,
        "platform_scope": platform,
        "captured_at": captured_at,
        "captured_at_confidence": "high",
        "maturity": maturity,
        "metrics": {"viewers": viewers, "comments": viewers // 10},
        "evidence": [evidence_path],
        "evidence_sha256": {
            evidence_path: hashlib.sha256(snapshot_id.encode("utf-8")).hexdigest(),
        },
        "metric_scope_notes": {"viewers": "synthetic exact fixture"},
        "platform_breakdown": {"viewers": {platform: viewers}},
        "surface_observations": [{
            "surface": "fixture_card",
            "reported_value": viewers,
            "evidence": "/".join((
                "C:", "Users", "Fixture", ".codex",
                "-".join(("codex", "remote", "attachments")), "private.jpg",
            )),
        }],
        "alternate_ui_values": {},
        "youtube_search_terms_percent": {"戰鬥陀螺": 44.9},
        "real_time_48h_source_counts": {"youtube_search": 3535},
        "external_sources_percent_visible_subset": {"naver.line": 33.3},
        "recommended_content_reference": {"reference_title": 50.0},
        "monetization": {"estimated_revenue_usd": 9.66},
        "content_packaging_analysis": {
            "title": "正版 VS 盜版",
            "pattern": "身分反差＋可視化勝負問題",
            "evidence_path": "/".join(("C:", "Users", "Fixture", "private.jpg")),
        },
    }
    if aggregation_eligible is not None:
        row["aggregation_eligible"] = aggregation_eligible
    if measurement_status is not None:
        row["measurement_status"] = measurement_status
    return row


def _account_snapshot(snapshot_id: str, surface: str, views: int) -> dict:
    evidence_path = f"C:/fixture/{snapshot_id}.jpg"
    return {
        "schema_version": "1.0",
        "account_snapshot_id": snapshot_id,
        "platform": "instagram",
        "captured_at": "2026-08-29T16:00:00+08:00",
        "window_days": 30,
        "measurement_surface": surface,
        "metrics": {"views": views},
        "evidence": [evidence_path],
        "evidence_sha256": {
            evidence_path: hashlib.sha256(snapshot_id.encode("utf-8")).hexdigest(),
        },
    }


def _fixture(root: Path) -> None:
    data = root / "data"
    write_jsonl(data / "posts.jsonl", [_post()])
    write_jsonl(data / "insight_snapshots.jsonl", [
        _snapshot(
            "snapshot-fb-developing-old", "facebook",
            "2026-08-29T12:00:00+08:00", "developing", 10,
        ),
        _snapshot(
            "snapshot-fb-developing-new", "facebook",
            "2026-08-29T12:30:00+08:00", "developing", 20,
        ),
        _snapshot(
            "snapshot-fb-developing-ineligible", "facebook",
            "2026-08-29T13:00:00+08:00", "developing", 999,
            aggregation_eligible=False,
        ),
        _snapshot(
            "snapshot-fb-mature", "facebook",
            "2026-08-29T14:00:00+08:00", "mature", 30,
        ),
        _snapshot(
            "snapshot-ig-developing", "instagram",
            "2026-08-29T12:15:00+08:00", "developing", 40,
        ),
        _snapshot(
            "snapshot-ig-awaiting", "instagram",
            "2026-08-29T15:00:00+08:00", "developing", 999,
            measurement_status="awaiting_data",
        ),
    ])
    write_jsonl(data / "account_snapshots.jsonl", [
        _account_snapshot("account-overview", "account_overview", 100),
        _account_snapshot("account-rankings", "reel_rankings", 200),
    ])


def _assert_matrix_caption_and_layout(facebook: dict) -> None:
    if facebook["caption"] != "測試 AI 版型！":
        raise AssertionError("exact caption was not joined")
    if facebook["caption_sha256"] != hashlib.sha256("測試 AI 版型！".encode("utf-8")).hexdigest():
        raise AssertionError("caption digest was not joined")
    if facebook["analysis_version"] != "feature-matrix-test-v1":
        raise AssertionError("analysis version was not joined")
    if facebook["caption_length"]["characters_including_spaces"] != len("測試 AI 版型！"):
        raise AssertionError("caption length was not joined")
    if facebook["caption_length"]["spaces"] != 2 or facebook["caption_length"]["links"] != 0:
        raise AssertionError("complete deterministic caption length profile was not joined")
    expected_layout = {
        "surface": "facebook_background_text",
        "caption_layout": "single paragraph rendered as a centered 2-line card",
        "video_orientation": None,
        "facebook_background_style": True,
        "background_color": "black",
        "text_color": "white",
        "text_weight": "bold",
        "alignment": "center",
        "rendered_line_count_observed": 2,
    }
    if facebook["layout"] != expected_layout:
        raise AssertionError(f"full black-card layout was not joined: {facebook['layout']}")
    if facebook["wording"]["keywords"] != ["AI", "版型", "ムービー"]:
        raise AssertionError("keywords were not joined")
    if facebook["wording"]["voice"] != ["直接", "高能量"]:
        raise AssertionError("voice was not joined")
    if facebook["wording"]["punctuation_style"] != ["單驚嘆號收尾"]:
        raise AssertionError("punctuation was not joined")
    if facebook["punctuation_profile"] != {
        "total": 1,
        "unique_marks": 1,
        "histogram": {"！": 1},
        "repeated_runs": [],
    }:
        raise AssertionError("complete Unicode punctuation profile was not joined")
    if facebook["wording"]["cta"] != "測試 CTA":
        raise AssertionError("CTA was not joined")
    expected_publication = {
        "published_at": "2026-08-29T10:00:00+08:00",
        "local_date": "2026-08-29",
        "weekday_zh_tw": "星期六",
        "local_time": "10:00",
        "daypart": "週末上午",
    }
    if facebook["publication"] != expected_publication:
        raise AssertionError(f"full publication context was not joined: {facebook['publication']}")


def _assert_matrix_outcome(facebook: dict) -> None:
    if facebook["outcome"]["metrics"]["viewers"] != 30:
        raise AssertionError("latest eligible outcome was not joined")
    if facebook["outcome"]["extended_analytics"] != {
        "content_packaging_analysis": {
            "pattern": "身分反差＋可視化勝負問題", "title": "正版 VS 盜版",
        },
        "external_sources_percent_visible_subset": {"naver.line": 33.3},
        "monetization": {"estimated_revenue_usd": 9.66},
        "real_time_48h_source_counts": {"youtube_search": 3535},
        "recommended_content_reference": {"reference_title": 50.0},
        "youtube_search_terms_percent": {"戰鬥陀螺": 44.9},
    }:
        raise AssertionError("extended analytics subtrees were not joined or sanitized")
    measurement = facebook["outcome"]["measurement_context"]
    if "captured_at_confidence" in measurement:
        raise AssertionError("retired capture confidence leaked into writing features")
    if measurement["metric_scope_notes"] != {"viewers": "synthetic exact fixture"}:
        raise AssertionError("metric scope notes were not joined")
    if measurement["platform_breakdown"] != {"viewers": {"facebook": 30}}:
        raise AssertionError("platform outcome breakdown was not joined")
    if measurement["surface_observations"] != [{
        "surface": "fixture_card", "reported_value": 30,
    }]:
        raise AssertionError("surface observation values were lost or private evidence leaked")


def _assert_matrix_contract(root: Path) -> None:
    rows = feature_matrix(root)
    observed = {row["platform"]: row["snapshot_id"] for row in rows}
    expected = {"facebook": "snapshot-fb-mature", "instagram": "snapshot-ig-developing"}
    if observed != expected:
        raise AssertionError(f"same-platform last eligible input selection drifted: {observed}")
    facebook = next(row for row in rows if row["platform"] == "facebook")
    _assert_matrix_caption_and_layout(facebook)
    _assert_matrix_outcome(facebook)


def _assert_comparables_contract(root: Path) -> None:
    context = comparables_context(
        root,
        platform="facebook",
        content_type="background_text_post",
        surface="facebook_background_text",
        limit=1,
    )
    if context["returned_count"] != 1 or context["available_count"] != 1:
        raise AssertionError(f"comparables filters returned the wrong cohort: {context}")
    row = context["comparables"][0]
    if row["caption"] != "測試 AI 版型！":
        raise AssertionError("comparables context omitted the exact caption")
    if row["layout"]["caption_layout"] != "single paragraph rendered as a centered 2-line card":
        raise AssertionError("comparables context omitted the caption layout")
    if row["layout"]["background_color"] != "black" or row["layout"]["text_color"] != "white":
        raise AssertionError("comparables context omitted black-card colors")
    if row["wording"]["keywords"] != ["AI", "版型", "ムービー"]:
        raise AssertionError("comparables context omitted multilingual keywords")
    if row["wording"]["voice"] != ["直接", "高能量"]:
        raise AssertionError("comparables context omitted tone")
    if row["wording"]["punctuation_style"] != ["單驚嘆號收尾"]:
        raise AssertionError("comparables context omitted punctuation style")
    if row["publication"]["local_date"] != "2026-08-29" or row["publication"]["daypart"] != "週末上午":
        raise AssertionError("comparables context omitted date/daypart")
    if row["outcome"]["metrics"]["viewers"] != 30:
        raise AssertionError("comparables context omitted outcomes")
    if row["outcome"]["extended_analytics"]["youtube_search_terms_percent"] != {
        "戰鬥陀螺": 44.9,
    }:
        raise AssertionError("comparables context omitted YouTube search terms")
    if "evidence" in json.dumps(context, ensure_ascii=False):
        raise AssertionError("comparables context leaked raw evidence paths")
    if context["comparison_policy"]["cohort_is_exact"] is not True:
        raise AssertionError("exact platform/maturity cohort was not identified")
    if context["comparison_policy"]["outcome_comparison_allowed"] is not True:
        raise AssertionError("fully filtered cohort did not permit outcome comparison")
    if context["comparison_policy"]["selection"] != {
        "strategy": "most_recent_publication",
        "tie_breakers": [
            "post_id_desc", "platform_desc",
        ],
        "performance_ranked": False,
    }:
        raise AssertionError("comparables selection policy is not deterministic and score-free")
    if "length=" not in render_comparables_context(context):
        raise AssertionError("human comparables context omitted exact caption length")
    incomplete = comparables_context(root, platform="facebook", limit=1)
    if incomplete["comparison_policy"]["cohort_is_exact"] is not False:
        raise AssertionError("heterogeneous content/surface query was marked exact")
    if incomplete["comparison_policy"]["outcome_comparison_allowed"] is not False:
        raise AssertionError("incompletely filtered query permitted outcome comparison")
    if comparables_context(
        root,
        platform="facebook",
        content_type="background_text_post",
        surface="reel_caption",
        limit=1,
    )["returned_count"] != 0:
        raise AssertionError("surface filter was not exact")
    try:
        comparables_context(root, limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("non-positive comparables limit was accepted")


def _assert_filters_and_summary(root: Path) -> None:
    filtered = feature_matrix(root, platform="facebook")
    if [row["snapshot_id"] for row in filtered] != ["snapshot-fb-mature"]:
        raise AssertionError("platform/maturity filters are not exact")
    history = observation_history(root, "post-feature-matrix", platform="facebook")
    if [row["snapshot_id"] for row in history["observations"]] != [
        "snapshot-fb-developing-old", "snapshot-fb-developing-new",
        "snapshot-fb-developing-ineligible", "snapshot-fb-mature",
    ]:
        raise AssertionError("clock retirement discarded original observation history")
    if history["growth_rate_per_hour"] is not None:
        raise AssertionError("history invented an hourly growth rate")
    summary = {(row["platform"], row["audience_count"]) for row in series_summary(root)}
    if summary != {("facebook", 30), ("instagram", 40)}:
        raise AssertionError(f"ineligible latest snapshot hid eligible summary data: {summary}")


def _assert_coverage_report(root: Path) -> None:
    report = feature_coverage_report(root)
    if report["coverage_complete"] is not True:
        raise AssertionError(f"complete fixture failed coverage audit: {report}")
    if report["eligible_post_count"] != 1 or report["covered_post_count"] != 1:
        raise AssertionError(f"coverage counts drifted: {report}")
    provenance = report["provenance"]
    if report["provenance_complete"] is not True or provenance["complete"] is not True:
        raise AssertionError(f"complete evidence manifests failed provenance audit: {provenance}")
    if (
        provenance["checked_record_count"] != 8
        or provenance["insight_snapshot_count"] != 6
        or provenance["account_snapshot_count"] != 2
        or provenance["complete_record_count"] != 8
    ):
        raise AssertionError(f"provenance coverage did not check every ledger row: {provenance}")
    serialized_report = json.dumps(report, ensure_ascii=False)
    if "C:/fixture/" in serialized_report or "測試 AI 版型！" in serialized_report:
        raise AssertionError("coverage report leaked a caption or private evidence path")
    row = report["posts"][0]
    if not all(row["dimensions"].values()) or row["missing"]:
        raise AssertionError(f"eligible post lost a feature dimension: {row}")
    if row["caption_sha256"] != hashlib.sha256("測試 AI 版型！".encode("utf-8")).hexdigest():
        raise AssertionError("coverage report did not bind the exact caption digest")
    expected_extended = {
        "content_packaging_analysis", "external_sources_percent_visible_subset",
        "monetization", "real_time_48h_source_counts", "recommended_content_reference",
        "youtube_search_terms_percent",
    }
    observed_extended = set(next(iter(row["extended_analytics_keys_by_snapshot"].values())))
    if observed_extended != expected_extended:
        raise AssertionError(f"coverage did not enumerate every extended subtree: {row}")
    expected_dimensions = {f"outcome:{key}" for key in expected_extended}
    if set(row["dimensions"]) < expected_dimensions or not all(
        row["dimensions"][key] for key in expected_dimensions
    ):
        raise AssertionError(f"coverage did not gate every extended subtree: {row}")
    if set(row["applicable_outcome_subtrees"]) != expected_extended:
        raise AssertionError(f"applicable outcome subtree inventory drifted: {row}")

    mutated_rows = deepcopy(feature_matrix(root))
    mutated_row = next(
        item for item in mutated_rows
        if item["platform"] == "facebook"
    )
    del mutated_row["outcome"]["extended_analytics"]["monetization"]
    snapshots_by_id = {
        snapshot["snapshot_id"]: snapshot for snapshot in _materialized_snapshots(root)
    }
    dimensions = _coverage_dimensions(
        _post(), mutated_rows, _coverage_expectations(_post()), snapshots_by_id,
    )
    if dimensions["outcome:monetization"] is not False:
        raise AssertionError("coverage failed to detect a dropped monetization subtree")
    for key in expected_dimensions - {"outcome:monetization"}:
        if dimensions[key] is not True:
            raise AssertionError(f"unrelated extended subtree failed after mutation: {key}")

    incomplete_snapshots = deepcopy(_materialized_snapshots(root))
    incomplete_snapshots[0].pop("evidence_sha256")
    incomplete_provenance = provenance_coverage_report(
        incomplete_snapshots,
        [
            _account_snapshot("account-overview", "account_overview", 100),
            _account_snapshot("account-rankings", "reel_rankings", 200),
        ],
    )
    if incomplete_provenance["complete"] is not False:
        raise AssertionError("provenance coverage accepted a missing insight digest manifest")


def _assert_deterministic_cli(root: Path) -> None:
    matrix_command = [
        sys.executable, "-B", str(SCRIPT), "matrix",
        "--root", str(root), "--format", "json",
    ]
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "cp950"

    def invoke(command: list[str]) -> str:
        completed = subprocess.run(command, check=False, capture_output=True, env=environment)
        if completed.returncode != 0:
            raise AssertionError(
                "matrix CLI failed under a legacy Windows code page: "
                + completed.stderr.decode("utf-8", errors="replace")
            )
        return completed.stdout.decode("utf-8")

    first = invoke(matrix_command)
    second = invoke(matrix_command)
    if first != second:
        raise AssertionError("matrix JSON output is not deterministic")
    if len(json.loads(first)) != 2:
        raise AssertionError("matrix CLI returned the wrong cohort count")
    context_command = [
        sys.executable, "-B", str(SCRIPT), "comparables",
        "--root", str(root),
        "--platform", "facebook",
        "--content-type", "background_text_post",
        "--surface", "facebook_background_text",
        "--limit", "1",
        "--format", "json",
    ]
    context = json.loads(invoke(context_command))
    if context["comparables"][0]["caption"] != "測試 AI 版型！":
        raise AssertionError("comparables CLI did not emit the exact caption")
    coverage_command = [
        sys.executable, "-B", str(SCRIPT), "coverage",
        "--root", str(root), "--format", "json",
    ]
    coverage = json.loads(invoke(coverage_command))
    if coverage["coverage_complete"] is not True:
        raise AssertionError("coverage CLI did not prove complete feature preservation")


def _timing_fixture(root: Path) -> None:
    strong = _post()
    weak = deepcopy(strong)
    weak_caption = "同分鐘，低成效！"
    weak["post_id"] = "post-feature-matrix-same-minute-low"
    weak["published_at"] = "2026-08-22T10:00:00+08:00"
    weak["caption"] = weak_caption
    weak["caption_sha256"] = hashlib.sha256(weak_caption.encode("utf-8")).hexdigest()
    weak["format_features"].update(caption_counts(weak_caption))
    weak["wording_features"].update({
        "opening": "同分鐘",
        "hook": "低成效",
        "keywords": ["同分鐘", "低成效"],
        "voice": ["直接"],
        "punctuation_style": ["單驚嘆號收尾"],
        "cta": "無",
    })
    weak["publication_context"].update({
        "local_date": "2026-08-22",
        "weekday_zh_tw": "星期六",
        "local_time": "10:00",
        "daypart": "週末上午",
    })
    data = root / "data"
    write_jsonl(data / "posts.jsonl", [strong, weak])
    write_jsonl(data / "insight_snapshots.jsonl", [
        _snapshot(
            "snapshot-same-minute-high", "facebook",
            "2026-08-29T12:00:00+08:00", "developing", 200,
        ),
        _snapshot(
            "snapshot-same-minute-low", "facebook",
            "2026-08-22T12:00:00+08:00", "developing", 2,
            post_id="post-feature-matrix-same-minute-low",
        ),
    ])


def _assert_timing_stays_noncausal(root: Path) -> None:
    context = comparables_context(
        root,
        platform="facebook",
        content_type="background_text_post",
        surface="facebook_background_text",
        limit=2,
    )
    timing = context["comparison_policy"]["timing"]
    if timing != {
        "role": "candidate_variable_only",
        "causal_claim_allowed": False,
        "recommended_time": None,
        "causal_weight": None,
        "same_minute_outcome_conflicts": [{
            "local_time": "10:00",
            "observations": [
                {
                    "post_id": "post-feature-matrix",
                    "platform": "facebook",
                    "metric": "viewers",
                    "value": 200,
                },
                {
                    "post_id": "post-feature-matrix-same-minute-low",
                    "platform": "facebook",
                    "metric": "viewers",
                    "value": 2,
                },
            ],
        }],
    }:
        raise AssertionError(f"same-minute counterexample became causal timing advice: {timing}")
    forbidden = {"score", "virality_score", "universal_virality_score"}

    def has_forbidden_key(value: object) -> bool:
        if isinstance(value, dict):
            return any(key in forbidden or has_forbidden_key(child) for key, child in value.items())
        if isinstance(value, list):
            return any(has_forbidden_key(child) for child in value)
        return False

    if has_forbidden_key(context):
        raise AssertionError("comparables context introduced a universal score")


def _assert_tie_breaker() -> None:
    snapshots = [
        _snapshot("snapshot-a", "facebook", "2026-08-29T12:00:00+08:00", "developing", 1),
        _snapshot("snapshot-z", "facebook", "2026-08-29T12:00:00+08:00", "developing", 2),
    ]
    selected = latest_aggregation_snapshots(snapshots)
    if next(iter(selected.values()))["snapshot_id"] != "snapshot-z":
        raise AssertionError("equal-time latest selection is not deterministically ID-tiebroken")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="social-feature-matrix-") as raw:
        root = Path(raw)
        _fixture(root)
        _assert_matrix_contract(root)
        _assert_comparables_contract(root)
        _assert_filters_and_summary(root)
        _assert_coverage_report(root)
        _assert_deterministic_cli(root)
    with tempfile.TemporaryDirectory(prefix="social-timing-negative-") as raw:
        root = Path(raw)
        _timing_fixture(root)
        _assert_timing_stays_noncausal(root)
    _assert_tie_breaker()
    print("social data feature matrix tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
