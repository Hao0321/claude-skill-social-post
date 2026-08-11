#!/usr/bin/env python3
"""Validate an outcome bundle; write only after an explicit --write."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from social_data import DATA_DIR, EXPERIMENTS_FILE, POSTS_FILE, SNAPSHOTS_FILE, load_jsonl, validate_store


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records)
    path.write_text(content, encoding="utf-8")


def prepare_records(
    bundle: dict[str, Any], data_dir: Path = DATA_DIR,
) -> tuple[dict[Path, list[dict[str, Any]]], dict[str, Any]]:
    post = bundle.get("post")
    snapshot = bundle["snapshot"]
    experiment = bundle.get("experiment")

    posts_file = data_dir / POSTS_FILE.name
    snapshots_file = data_dir / SNAPSHOTS_FILE.name
    experiments_file = data_dir / EXPERIMENTS_FILE.name
    posts = load_jsonl(posts_file)
    snapshots = load_jsonl(snapshots_file)
    experiments = load_jsonl(experiments_file)
    posts_by_id = {row.get("post_id"): row for row in posts}
    snapshot_ids = {row.get("snapshot_id") for row in snapshots}
    experiment_ids = {row.get("experiment_id") for row in experiments}

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

    if experiment:
        experiment_id = experiment.get("experiment_id")
        if experiment_id in experiment_ids:
            raise ValueError(f"duplicate experiment_id: {experiment_id}")
        experiments.append(experiment)

    normalized = {"snapshot": snapshot}
    if post is not None:
        normalized["post"] = post
    if experiment is not None:
        normalized["experiment"] = experiment
    return {
        posts_file: posts,
        snapshots_file: snapshots,
        experiments_file: experiments,
    }, normalized


def validate_staged(records: dict[Path, list[dict[str, Any]]]) -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-") as temp_name:
        root = Path(temp_name)
        staged_data = root / "data"
        for destination, rows in records.items():
            write_jsonl(staged_data / destination.name, rows)
        result = validate_store(root)
        if not result["valid"]:
            raise ValueError("bundle would make store invalid: " + "; ".join(result["errors"]))


def commit_records(records: dict[Path, list[dict[str, Any]]], data_dir: Path = DATA_DIR) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    originals = {path: path.read_bytes() if path.exists() else None for path in records}
    with tempfile.TemporaryDirectory(prefix="social-post-commit-", dir=data_dir.parent) as temp_name:
        staging = Path(temp_name)
        staged_paths: dict[Path, Path] = {}
        for destination, rows in records.items():
            staged = staging / destination.name
            write_jsonl(staged, rows)
            staged_paths[destination] = staged
        try:
            for destination, staged in staged_paths.items():
                shutil.copyfile(staged, destination.with_suffix(destination.suffix + ".tmp"))
                destination.with_suffix(destination.suffix + ".tmp").replace(destination)
        except OSError:
            for destination, original in originals.items():
                if original is None:
                    if destination.exists():
                        destination.unlink()
                else:
                    destination.write_bytes(original)
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, help="JSON object with snapshot, optional post, and optional experiment")
    parser.add_argument("--write", action="store_true", help="Write after validation. Default is dry-run.")
    args = parser.parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8-sig"))
        if not isinstance(bundle, dict):
            raise ValueError("bundle must be a JSON object")
        records, normalized = prepare_records(bundle)
        validate_staged(records)
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
        if not args.write:
            print("DRY_RUN valid bundle; add --write to commit")
            return 0
        commit_records(records)
        result = validate_store()
        if not result["valid"]:
            raise ValueError("store invalid after commit: " + "; ".join(result["errors"]))
        print("WRITE_OK")
        return 0
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"log outcome error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
