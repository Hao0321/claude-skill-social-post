#!/usr/bin/env python3
"""Smoke-test structured outcomes and generated archives."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_rule_registry import build
from log_outcome import prepare_records, validate_staged
from social_data import SKILL_ROOT, series_summary, validate_store
from social_store import commit_records


def main() -> int:
    result = validate_store()
    if not result["valid"]:
        raise AssertionError(result["errors"])
    if result["counts"]["posts"]:
        minimum_counts = {"posts": 4, "snapshots": 6, "experiments": 3}
        if any(result["counts"].get(key, 0) < value for key, value in minimum_counts.items()):
            raise AssertionError(f"outcome store lost records: {result['counts']}")
        rows = series_summary(SKILL_ROOT, "reborn-married-driver")
        by_episode = {row["episode"]: row for row in rows}
        if not {1, 2, 3}.issubset(by_episode):
            raise AssertionError("baseline episodes disappeared")
        expected_watch = {1: 61.1, 2: 38.9, 3: 41.1}
        if {episode: by_episode[episode]["watch_percent"] for episode in expected_watch} != expected_watch:
            raise AssertionError("baseline derived watch percentages changed")
        beyblade_rows = series_summary(SKILL_ROOT, "beyblade-battles")
        if {row["platform"] for row in beyblade_rows} != {"facebook", "youtube"}:
            raise AssertionError("cross-platform snapshots were collapsed")
        youtube = next(row for row in beyblade_rows if row["platform"] == "youtube")
        if youtube["watch_seconds"] is not None or youtube["watch_percent"] is not None:
            raise AssertionError("missing YouTube retention was converted to zero")
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
    for relative, pattern in (("references/cases/manifest.json", "case-*.md"), ("references/rules/manifest.json", "R*.md")):
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
    with tempfile.TemporaryDirectory(prefix="social-post-concurrency-") as raw:
        data_dir = Path(raw) / "data"
        published = "2026-08-13T10:00:00+08:00"

        def bundle(suffix: str) -> dict:
            post_id = f"post-{suffix}"
            return {
                "post": {
                    "post_id": post_id, "published_at": published,
                    "platforms": ["facebook"], "caption": suffix,
                },
                "snapshot": {
                    "snapshot_id": f"snapshot-{suffix}", "post_id": post_id,
                    "captured_at": "2026-08-13T11:00:00+08:00", "metrics": {},
                },
            }

        first, _, first_revision = prepare_records(bundle("first"), data_dir)
        second, _, second_revision = prepare_records(bundle("second"), data_dir)
        validate_staged(first)
        validate_staged(second)
        commit_records(first, data_dir=data_dir, expected_revision=first_revision)
        try:
            commit_records(second, data_dir=data_dir, expected_revision=second_revision)
        except RuntimeError:
            pass
        else:
            raise AssertionError("stale concurrent writer was not rejected")
    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
