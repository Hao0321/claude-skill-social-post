#!/usr/bin/env python3
"""Dependency-free smoke test for the public outcome engine."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_rule_registry import build
from log_outcome import commit_records, prepare_records, validate_staged
from social_data import series_summary, validate_store


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="social-post-selftest-") as temp_name:
        root = Path(temp_name)
        post = {
            "post_id": "demo-ep01",
            "series_id": "demo",
            "episode_number": 1,
            "published_at": "2026-08-11T10:00:00+08:00",
            "duration_seconds": 90,
            "platforms": ["instagram"],
            "caption": "demo",
        }
        first = {
            "snapshot_id": "demo-ep01-1h",
            "post_id": "demo-ep01",
            "captured_at": "2026-08-11T11:00:00+08:00",
            "hours_since_publish": 1,
            "maturity": "early",
            "metrics": {"plays": 100, "reached_accounts": 80, "average_watch_seconds": 36, "likes": 5},
            "rates_reported": {"skip_percent": 40},
        }
        latest = {
            "snapshot_id": "demo-ep01-24h",
            "post_id": "demo-ep01",
            "captured_at": "2026-08-12T10:00:00+08:00",
            "hours_since_publish": 24,
            "maturity": "developing",
            "metrics": {"plays": 200, "reached_accounts": 120, "average_watch_seconds": 45, "likes": 10},
            "rates_reported": {"skip_percent": 35},
        }
        standalone = {
            "post_id": "standalone-post",
            "published_at": "2026-08-11T12:00:00+08:00",
            "platforms": ["instagram", "facebook"],
            "caption": "standalone text post",
            "content_type": "image_post",
        }
        standalone_snapshot = {
            "snapshot_id": "standalone-post-24h",
            "post_id": "standalone-post",
            "captured_at": "2026-08-12T12:00:00+08:00",
            "hours_since_publish": 24,
            "maturity": "developing",
            "metrics": {"plays": 10, "likes": 2},
            "platform_breakdown": {"plays": {"instagram": 8}},
        }
        experiment = {
            "experiment_id": "demo-test",
            "post_ids": ["demo-ep01"],
            "independent_samples": 1,
            "evidence": {"status": "hypothesis"},
        }
        write_jsonl(root / "data" / "posts.jsonl", [post, standalone])
        write_jsonl(root / "data" / "insight_snapshots.jsonl", [first, latest, standalone_snapshot])
        write_jsonl(root / "data" / "experiments.jsonl", [experiment])

        result = validate_store(root)
        if not result["valid"]:
            raise AssertionError(result["errors"])
        if result["counts"] != {"posts": 2, "snapshots": 3, "experiments": 1}:
            raise AssertionError(f"unexpected counts: {result['counts']}")
        if not any("platform breakdown is partial" in warning for warning in result["warnings"]):
            raise AssertionError(f"partial platform warning missing: {result['warnings']}")
        rows = series_summary(root, "demo")
        if len(rows) != 1 or rows[0]["plays"] != 200 or rows[0]["watch_percent"] != 50.0:
            raise AssertionError(f"latest snapshot or derived metrics failed: {rows}")

    with tempfile.TemporaryDirectory(prefix="social-post-write-test-") as temp_name:
        root = Path(temp_name)
        data_dir = root / "data"
        bundle = {
            "post": post,
            "snapshot": first,
            "experiment": experiment,
        }
        records, _ = prepare_records(bundle, data_dir)
        validate_staged(records)
        commit_records(records, data_dir)
        appended = dict(latest)
        records, _ = prepare_records({"snapshot": appended}, data_dir)
        validate_staged(records)
        commit_records(records, data_dir)
        committed = validate_store(root)
        if not committed["valid"] or committed["counts"] != {"posts": 1, "snapshots": 2, "experiments": 1}:
            raise AssertionError(f"transactional append failed: {committed}")

    with tempfile.TemporaryDirectory(prefix="social-post-invalid-test-") as temp_name:
        root = Path(temp_name)
        write_jsonl(root / "data" / "posts.jsonl", [{
            "post_id": [], "published_at": None, "platforms": ["instagram", "instagram"], "caption": 123,
        }])
        write_jsonl(root / "data" / "insight_snapshots.jsonl", [{
            "snapshot_id": [], "post_id": [], "captured_at": None, "metrics": {"plays": "many"},
        }])
        write_jsonl(root / "data" / "experiments.jsonl", [{
            "experiment_id": [], "post_ids": [{}], "evidence": {"status": "validated"},
            "independent_samples": "unknown",
        }])
        invalid = validate_store(root)
        if invalid["valid"] or len(invalid["errors"]) < 6:
            raise AssertionError(f"invalid store did not produce structured errors: {invalid}")

    registry = build()
    if not registry["rules"]:
        raise AssertionError("public rule library produced an empty registry")
    print(f"self-test passed; indexed {len(registry['rules'])} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
