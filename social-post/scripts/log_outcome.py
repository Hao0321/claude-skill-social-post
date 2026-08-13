#!/usr/bin/env python3
"""Validate an outcome bundle; write only after an explicit --write."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from social_data import (
    ACCOUNT_SNAPSHOTS_FILE, DATA_DIR, EXPERIMENTS_FILE, POSTS_FILE, SNAPSHOTS_FILE,
    validate_store,
)
from social_store import commit_records, load_jsonl, store_revision, write_jsonl


def prepare_records(
    bundle: dict[str, Any], data_dir: Path = DATA_DIR,
) -> tuple[dict[Path, list[dict[str, Any]]], dict[str, Any], str]:
    base_revision = store_revision(data_dir)
    post = bundle.get("post")
    snapshot = bundle.get("snapshot")
    account_snapshot = bundle.get("account_snapshot")
    experiment = bundle.get("experiment")
    if snapshot is None and account_snapshot is None and experiment is None:
        raise ValueError("bundle requires a post snapshot, account snapshot, experiment, or a combination")

    posts_file = data_dir / POSTS_FILE.name
    snapshots_file = data_dir / SNAPSHOTS_FILE.name
    account_snapshots_file = data_dir / ACCOUNT_SNAPSHOTS_FILE.name
    experiments_file = data_dir / EXPERIMENTS_FILE.name
    posts = load_jsonl(posts_file)
    snapshots = load_jsonl(snapshots_file)
    account_snapshots = load_jsonl(account_snapshots_file)
    experiments = load_jsonl(experiments_file)
    posts_by_id = {row.get("post_id"): row for row in posts}
    snapshot_ids = {row.get("snapshot_id") for row in snapshots}

    if snapshot is not None:
        post_id = snapshot.get("post_id")
        existing_post = posts_by_id.get(post_id)
        if existing_post is None:
            if post is None:
                raise ValueError("new post_id requires both post and snapshot")
            if post.get("post_id") != post_id:
                raise ValueError("snapshot.post_id must match post.post_id")
            posts.append(post)
        elif post is not None and post != existing_post:
            raise ValueError(f"post_id already exists with different data: {post_id}; omit post when appending a snapshot")

        snapshot_id = snapshot.get("snapshot_id")
        if snapshot_id in snapshot_ids:
            raise ValueError(f"duplicate snapshot_id: {snapshot_id}")
        snapshots.append(snapshot)
    elif post is not None:
        raise ValueError("post cannot be supplied without a snapshot")

    if account_snapshot is not None:
        account_snapshot_id = account_snapshot.get("account_snapshot_id")
        known_ids = {row.get("account_snapshot_id") for row in account_snapshots}
        if account_snapshot_id in known_ids:
            raise ValueError(f"duplicate account_snapshot_id: {account_snapshot_id}")
        account_snapshots.append(account_snapshot)

    if experiment:
        experiment_id = experiment.get("experiment_id")
        prior = [row for row in experiments if row.get("experiment_id") == experiment_id]
        experiment = dict(experiment)
        if prior:
            next_revision = max(int(row.get("revision", 1)) for row in prior) + 1
            experiment.setdefault("revision", next_revision)
            experiment.setdefault("supersedes_revision", next_revision - 1)
        else:
            experiment.setdefault("revision", 1)
        experiments.append(experiment)

    normalized: dict[str, Any] = {}
    if snapshot is not None:
        normalized["snapshot"] = snapshot
    if account_snapshot is not None:
        normalized["account_snapshot"] = account_snapshot
    if post is not None:
        normalized["post"] = post
    if experiment is not None:
        normalized["experiment"] = experiment
    return {
        posts_file: posts,
        snapshots_file: snapshots,
        account_snapshots_file: account_snapshots,
        experiments_file: experiments,
    }, normalized, base_revision


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
