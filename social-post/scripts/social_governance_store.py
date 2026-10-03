"""Private governance IO; fixed paths, immutable versions and one writer lock."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

from social_store import exclusive_store_lock, load_jsonl

MAX_DOCUMENT = 2 * 1024 * 1024


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def private_path(root: Path, relative: str) -> Path:
    root = root.absolute()
    if root.resolve() != root:
        raise ValueError("linked governance root")
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in {"..", "."} for part in parts):
        raise ValueError("unsafe governance path")
    cursor = root
    for part in parts:
        cursor = cursor / part
        if cursor.exists() or cursor.is_symlink():
            info = cursor.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
                raise ValueError("linked governance member")
    if not cursor.resolve().is_relative_to(root):
        raise ValueError("governance path escaped")
    return cursor


def read_document(root: Path, relative: str) -> dict[str, Any]:
    path = private_path(root, relative)
    raw = path.read_bytes()
    if len(raw) > MAX_DOCUMENT:
        raise ValueError("governance document exceeds bound")
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("governance document must be an object")
    return value


def write_document(root: Path, relative: str, value: dict[str, Any], *, immutable: bool = False) -> None:
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if len(raw) > MAX_DOCUMENT:
        raise ValueError("governance document exceeds bound")
    path = private_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    private_path(root, relative)
    if immutable:
        if path.exists():
            if read_document(root, relative) != value:
                raise ValueError("immutable governance version collision")
            return
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return
    temporary = private_path(root, relative + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def learning_events(root: Path) -> list[dict[str, Any]]:
    path = private_path(root, "data/learning_events.jsonl")
    if path.exists() and path.stat().st_size > 16 * MAX_DOCUMENT:
        raise ValueError("learning ledger exceeds bound; archive with provenance before continuing")
    return load_jsonl(path)


def append_event_locked(root: Path, event: dict[str, Any]) -> None:
    """Caller holds the canonical writer lock. No mutation of old events."""
    path = private_path(root, "data/learning_events.jsonl")
    raw = (json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    if len(raw) > MAX_DOCUMENT:
        raise ValueError("learning event exceeds bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def governance_lock(root: Path):
    private_path(root, "data/.write.lock")
    return exclusive_store_lock(private_path(root, "data"), timeout_seconds=2)
