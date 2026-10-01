#!/usr/bin/env python3
"""Reject private artifacts and common credential patterns in public contributions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "social-post" / "scripts"))
from sync_public import privacy_violations  # noqa: E402

PRIVATE_NAMES = {
    "style_profile.md", "content_plan.md", "_scraped_posts_draft.md",
    ".env", "cookies.txt", "cookies.json", "login data",
}
PRIVATE_DIRS = {
    ".rd", "drafts", "private", "screenshots", "attachments", "user data",
}
PRIVATE_EXTENSIONS = {
    ".jsonl", ".har", ".trace", ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".mp4", ".mov", ".mp3", ".wav", ".zip", ".7z", ".exe", ".dll", ".pdf",
}


def path_violation(relative: str) -> str | None:
    path = PurePosixPath(relative.lower().replace("\\", "/"))
    if path.name in PRIVATE_NAMES or any(part in PRIVATE_DIRS for part in path.parts[:-1]):
        return "private local file or directory"
    if path.suffix in PRIVATE_EXTENSIONS:
        return "private ledger, trace, media or binary artifact"
    if path.name.startswith(".env."):
        return "environment configuration"
    if "data" in path.parts and path.name != "rule_registry.json":
        return "data store; put fictional examples in references instead"
    return None


def inspect_files(root: Path, relatives: list[str], config: dict) -> list[str]:
    failures: list[str] = []
    rows: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for relative in relatives:
        key = relative.casefold()
        if key in seen:
            failures.append(f"{relative}: duplicate or case-colliding path")
            continue
        seen.add(key)
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            failures.append(f"{relative}: path outside repository")
            continue
        source = root.joinpath(*pure.parts)
        if any(
            entry.is_symlink() or getattr(entry, "is_junction", lambda: False)()
            for entry in [source, *source.parents]
            if entry != root and root in entry.parents
        ):
            failures.append(f"{relative}: linked path")
            continue
        reason = path_violation(relative)
        if reason:
            failures.append(f"{relative}: {reason}")
            continue
        if not source.is_file():
            failures.append(f"{relative}: missing file")
            continue
        try:
            raw = source.read_bytes()
            raw.decode("utf-8-sig")
        except UnicodeError:
            failures.append(f"{relative}: non-UTF-8 artifact")
            continue
        if b"\x00" in raw:
            failures.append(f"{relative}: binary artifact")
            continue
        rows.append((source, relative))
    # Reuse the exporter detector; keep privacy semantics in one place.
    failures.extend(privacy_violations(rows, config))
    return sorted(set(failures))


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    )
    relatives = sorted(set(result.stdout.decode("utf-8").rstrip("\0").split("\0")))
    config = json.loads((ROOT / "audit.config.json").read_text(encoding="utf-8-sig"))
    failures = inspect_files(ROOT, relatives, config)
    if failures:
        print(f"BLOCK public contribution: {len(failures)} finding(s)")
        for failure in failures:
            print(failure)
        return 1
    print(f"public contribution guard passed: {len(relatives)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
