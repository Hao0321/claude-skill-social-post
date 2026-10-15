#!/usr/bin/env python3
"""Validate an outcome bundle; write only after an explicit --write."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from social_data import (
    ACCOUNT_SNAPSHOTS_FILE, CORRECTIONS_FILE, DATA_DIR, EXPERIMENTS_FILE, POSTS_FILE,
    SNAPSHOTS_FILE, validate_store,
)
from social_store import commit_records, load_jsonl, read_store_snapshot, store_revision, write_jsonl


def load_store_records(data_dir: Path) -> tuple[dict[str, Path], dict[str, list[dict[str, Any]]]]:
    paths, records, _revision = _load_store_state(data_dir)
    return paths, records


def _load_store_state(data_dir: Path) -> tuple[dict, dict, str]:
    paths = {
        "posts": data_dir / POSTS_FILE.name,
        "snapshots": data_dir / SNAPSHOTS_FILE.name,
        "account_snapshots": data_dir / ACCOUNT_SNAPSHOTS_FILE.name,
        "experiments": data_dir / EXPERIMENTS_FILE.name,
        "corrections": data_dir / CORRECTIONS_FILE.name,
    }
    revision, snapshot = read_store_snapshot(data_dir)
    return paths, {name: snapshot[path.name] for name, path in paths.items()}, revision


def append_snapshot(
    post: dict[str, Any] | None,
    snapshot: dict[str, Any] | None,
    records: dict[str, list[dict[str, Any]]],
) -> None:
    if snapshot is None:
        if post is not None:
            raise ValueError("post cannot be supplied without a snapshot")
        return
    post_id = snapshot.get("post_id")
    posts_by_id = {row.get("post_id"): row for row in records["posts"]}
    existing_post = posts_by_id.get(post_id)
    if existing_post is None:
        if post is None:
            raise ValueError("new post_id requires both post and snapshot")
        if post.get("post_id") != post_id:
            raise ValueError("snapshot.post_id must match post.post_id")
        records["posts"].append(post)
    elif post is not None and post != existing_post:
        raise ValueError(
            f"post_id already exists with different data: {post_id}; "
            "omit post when appending a snapshot"
        )
    snapshot_id = snapshot.get("snapshot_id")
    if snapshot_id in {row.get("snapshot_id") for row in records["snapshots"]}:
        raise ValueError(f"duplicate snapshot_id: {snapshot_id}")
    records["snapshots"].append(snapshot)


def append_unique(
    row: dict[str, Any] | None,
    records: list[dict[str, Any]],
    identity: str,
) -> None:
    if row is None:
        return
    value = row.get(identity)
    if value in {existing.get(identity) for existing in records}:
        raise ValueError(f"duplicate {identity}: {value}")
    records.append(row)


def append_experiment(
    experiment: dict[str, Any] | None,
    records: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not experiment:
        return experiment
    normalized = dict(experiment)
    experiment_id = normalized.get("experiment_id")
    prior = [row for row in records if row.get("experiment_id") == experiment_id]
    if prior:
        next_revision = max(int(row.get("revision", 1)) for row in prior) + 1
        normalized.setdefault("revision", next_revision)
        normalized.setdefault("supersedes_revision", next_revision - 1)
    else:
        normalized.setdefault("revision", 1)
    records.append(normalized)
    return normalized


def prepare_records(
    bundle: dict[str, Any], data_dir: Path = DATA_DIR,
) -> tuple[dict[Path, list[dict[str, Any]]], dict[str, Any], str]:
    post = bundle.get("post")
    if isinstance(post, dict):
        post = copy.deepcopy(post)
        post.setdefault("analysis_status", "pending")
        post.setdefault("analysis_version", "pending")
        post.setdefault("analysis_eligible", False)
        caption = post.get("caption")
        if isinstance(caption, str):
            post.setdefault("caption_sha256", hashlib.sha256(caption.encode("utf-8")).hexdigest())
    snapshot = bundle.get("snapshot")
    account_snapshot = bundle.get("account_snapshot")
    experiment = bundle.get("experiment")
    correction = bundle.get("correction")
    if snapshot is None and account_snapshot is None and experiment is None and correction is None:
        raise ValueError(
            "bundle requires a post snapshot, account snapshot, experiment, correction, or a combination"
        )

    paths, records, base_revision = _load_store_state(data_dir)
    append_snapshot(post, snapshot, records)
    append_unique(account_snapshot, records["account_snapshots"], "account_snapshot_id")
    experiment = append_experiment(experiment, records["experiments"])
    append_unique(correction, records["corrections"], "correction_id")

    normalized: dict[str, Any] = {}
    if snapshot is not None:
        normalized["snapshot"] = snapshot
    if account_snapshot is not None:
        normalized["account_snapshot"] = account_snapshot
    if post is not None:
        normalized["post"] = post
    if experiment is not None:
        normalized["experiment"] = experiment
    if correction is not None:
        normalized["correction"] = correction
    return {paths[name]: rows for name, rows in records.items()}, normalized, base_revision


def validate_staged(records: dict[Path, list[dict[str, Any]]]) -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-") as temp_name:
        root = Path(temp_name)
        staged_data = root / "data"
        for destination, rows in records.items():
            write_jsonl(staged_data / destination.name, rows)
        result = validate_store(root)
        if not result["valid"]:
            raise ValueError("bundle would make store invalid: " + "; ".join(result["errors"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, help="JSON object with snapshot, optional post, and optional experiment")
    parser.add_argument("--write", action="store_true", help="Write after validation. Default is dry-run.")
    args = parser.parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8-sig"))
        if not isinstance(bundle, dict):
            raise ValueError("bundle must be a JSON object")
        records, normalized, base_revision = prepare_records(bundle)
        validate_staged(records)
        print(json.dumps({"base_revision": base_revision, **normalized}, ensure_ascii=False, indent=2))
        if not args.write:
            print("DRY_RUN valid bundle; add --write to commit")
            return 0
        new_revision = commit_records(
            records, data_dir=DATA_DIR, expected_revision=base_revision,
        )
        result = validate_store()
        if not result["valid"]:
            raise ValueError("store invalid after commit: " + "; ".join(result["errors"]))
        print(f"WRITE_OK revision={new_revision}")
        return 0
    except (OSError, KeyError, RuntimeError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        print(f"log outcome error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
