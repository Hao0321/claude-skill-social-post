"""Read one coherent outcome revision without writing locks, files or caches."""
from __future__ import annotations
import hashlib
import json
import stat
import time
import threading
from contextlib import contextmanager
from pathlib import Path

DATA_FILENAMES = ("posts.jsonl", "insight_snapshots.jsonl", "account_snapshots.jsonl",
                  "experiments.jsonl", "corrections.jsonl")
_OWNERS = threading.local()


@contextmanager
def _lock_owner_scope(data_dir: Path):
    """Called only by the store after acquiring its physical writer lock."""
    owners = getattr(_OWNERS, "paths", None)
    if owners is None:
        owners = _OWNERS.paths = set()
    key = data_dir.resolve()
    owners.add(key)
    try:
        yield
    finally:
        owners.remove(key)


def parse_jsonl(data: bytes, name: str) -> list[dict]:
    records = []
    # JSON Lines uses physical LF separators; U+2028/U+2029 inside captions are data.
    for line_no, raw in enumerate(data.decode("utf-8-sig").split("\n"), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{name}:{line_no}: each JSONL row must be an object")
        records.append(value)
    return records


def file_identity(path: Path) -> tuple | None:
    try:
        item = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(item.st_mode) or getattr(item, "st_file_attributes", 0) & 0x400:
        raise ValueError("outcome ledger must be a regular, non-linked file")
    return (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)


def revision_from_bytes(payloads: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in DATA_FILENAMES:
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(payloads[name])
        digest.update(b"\0")
    return digest.hexdigest()


def read_store_snapshot(data_dir: Path, *, timeout_seconds: float = 10.0) -> tuple[str, dict]:
    """Retry changed inputs; never stamp mixed rows with a later revision."""
    deadline = time.monotonic() + timeout_seconds
    lock = data_dir / ".write.lock"
    owned = data_dir.resolve() in getattr(_OWNERS, "paths", set())
    while True:
        if owned or not lock.exists():
            before = {name: file_identity(data_dir / name) for name in DATA_FILENAMES}
            try:
                payloads = {name: (data_dir / name).read_bytes() if before[name] is not None else b""
                            for name in DATA_FILENAMES}
            except FileNotFoundError:
                payloads = None  # An atomic writer changed membership while reading.
            after = {name: file_identity(data_dir / name) for name in DATA_FILENAMES}
            if payloads is not None and before == after and (owned or not lock.exists()):
                return revision_from_bytes(payloads), {
                    name: parse_jsonl(data, name) for name, data in payloads.items()}
        if time.monotonic() >= deadline:
            raise TimeoutError("outcome store is changing; retry from a fresh snapshot")
        time.sleep(0.01)
