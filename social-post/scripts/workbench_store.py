"""Private draft storage with fixed paths, bounded reads and no overwrites."""

from __future__ import annotations

import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from social_store import DATA_FILENAMES, exclusive_store_lock
from workbench_contract import PLATFORMS, text_field

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
MAX_FILE = 256 * 1024


def linked(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
    )


def safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    if linked(root) or root.resolve() != root.absolute():
        raise ValueError("linked workspace is not supported")
    cursor = root
    for component in Path(relative).parts:
        if component in {"..", ".", ""} or Path(component).is_absolute():
            raise ValueError("unsafe workspace path")
        cursor = cursor / component
        if linked(cursor):
            raise ValueError("linked workspace member")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("workspace path escaped")
    return path


def check_data_paths(root: Path) -> None:
    for name in (*DATA_FILENAMES, ".write.lock"):
        safe_path(root, "data/" + name)
    for name in DATA_FILENAMES:
        safe_path(root, "data/" + name + ".tmp")


def read_json(root: Path, relative: str) -> Any:
    path = safe_path(root, relative)
    with path.open("rb") as stream:
        raw = stream.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise ValueError("file exceeds workbench bound")
    return json.loads(raw.decode("utf-8-sig"))


def draft_payload(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict) or set(payload) != {"id", "title", "text", "platform", "format"}:
        raise ValueError("invalid draft fields")
    row = {key: text_field(payload, key) for key in payload}
    if not UUID.fullmatch(row["id"]) or not row["title"] or not row["text"]:
        raise ValueError("draft id, title and text are required")
    if len(row["title"]) > 160 or row["platform"] not in PLATFORMS or row["format"] not in {"A", "B", "C"}:
        raise ValueError("invalid draft metadata")
    row["text"] = payload["text"]  # Preserve exact author whitespace and line breaks.
    return row


def save_draft(root: Path, payload: Any) -> dict[str, Any]:
    row = draft_payload(payload)
    relative = "drafts/workbench/" + row["id"] + ".json"
    check_data_paths(root)
    with exclusive_store_lock(safe_path(root, "data"), timeout_seconds=2):
        destination = safe_path(root, relative)
        if destination.exists():
            prior = read_json(root, relative)
            if any(prior.get(key) != value for key, value in row.items()):
                raise ValueError("draft id already has different content")
            return prior
        destination.parent.mkdir(parents=True, exist_ok=True)
        safe_path(root, relative)
        record = {"schema_version": 1, **row,
                  "saved_at": datetime.now(timezone.utc).isoformat()}
        raw = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
        with destination.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return record


def list_drafts(root: Path) -> list[dict[str, Any]]:
    folder = safe_path(root, "drafts/workbench")
    if not folder.exists():
        return []
    rows = []
    for index, path in enumerate(folder.iterdir()):
        if index >= 1000:
            raise ValueError("too many workbench drafts")
        if path.suffix != ".json" or not UUID.fullmatch(path.stem):
            continue
        row = read_json(root, "drafts/workbench/" + path.name)
        if not isinstance(row, dict) or row.get("id") != path.stem:
            raise ValueError("invalid saved draft")
        rows.append({key: row[key] for key in ("id", "title", "platform", "format", "saved_at")})
    return sorted(rows, key=lambda row: row["saved_at"], reverse=True)


def get_draft(root: Path, identity: str) -> dict[str, Any]:
    if not UUID.fullmatch(identity):
        raise ValueError("invalid draft id")
    return read_json(root, "drafts/workbench/" + identity + ".json")
