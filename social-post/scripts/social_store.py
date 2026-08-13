#!/usr/bin/env python3
"""JSONL persistence with optimistic revisions and a cross-platform lock."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


DATA_FILENAMES = ("posts.jsonl", "insight_snapshots.jsonl", "experiments.jsonl")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_no}: each JSONL row must be an object")
        records.append(value)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    )
    path.write_text(content, encoding="utf-8")


def store_revision(data_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in DATA_FILENAMES:
        path = data_dir / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        if path.exists():
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@contextmanager
def exclusive_store_lock(data_dir: Path, timeout_seconds: float = 10.0) -> Iterator[None]:
    """Serialize writers using atomic directory creation (works on Windows/POSIX)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_dir = data_dir / ".write.lock"
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            os.mkdir(lock_dir)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for outcome store lock: {lock_dir}")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            os.rmdir(lock_dir)
        except FileNotFoundError:
            pass


def commit_records(
    records: dict[Path, list[dict[str, Any]]],
    *,
    data_dir: Path,
    expected_revision: str,
) -> str:
    """Commit a staged store or reject a stale read-modify-write transaction."""
    with exclusive_store_lock(data_dir):
        current_revision = store_revision(data_dir)
        if current_revision != expected_revision:
            raise RuntimeError(
                "outcome store changed after validation; reload the bundle and retry "
                f"(expected {expected_revision[:12]}, found {current_revision[:12]})"
            )
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
                    temporary = destination.with_suffix(destination.suffix + ".tmp")
                    shutil.copyfile(staged, temporary)
                    temporary.replace(destination)
            except OSError:
                for destination, original in originals.items():
                    if original is None:
                        destination.unlink(missing_ok=True)
                    else:
                        destination.write_bytes(original)
                raise
        return store_revision(data_dir)
