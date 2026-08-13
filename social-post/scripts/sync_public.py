#!/usr/bin/env python3
"""Copy the configured public allowlist without deleting public-only examples."""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "audit.config.json"


def public_root(config: dict) -> Path:
    value = config.get("sync", {}).get("public_root")
    if not value:
        raise ValueError("sync.public_root is not configured")
    result = Path(value).expanduser()
    return result if result.is_absolute() else (ROOT / result).resolve()


def ignored(relative: str, patterns: list[str]) -> bool:
    normalized = relative.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def candidates(config: dict) -> list[tuple[Path, str]]:
    excluded = config.get("exclude", [])
    sync_ignored = config.get("sync", {}).get("ignore", [])
    rows = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if ignored(relative, excluded) or ignored(relative, sync_ignored):
            continue
        rows.append((path, relative))
    return sorted(rows, key=lambda row: row[1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Copy files. Default is dry-run.")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    destination_root = public_root(config)
    rows = candidates(config)
    changed = []
    for source, relative in rows:
        destination = destination_root / relative
        if destination.exists() and destination.read_bytes() == source.read_bytes():
            continue
        changed.append(relative)
        if args.write:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    mode = "WRITE" if args.write else "DRY_RUN"
    print(f"{mode} public_root={destination_root} changed={len(changed)}")
    for relative in changed:
        print(relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
