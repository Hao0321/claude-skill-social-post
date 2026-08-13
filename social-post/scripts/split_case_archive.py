#!/usr/bin/env python3
"""Split the legacy case_studies.md into one file per permanent Case ID."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "case_studies.md"
CASE_DIR = ROOT / "references" / "cases"
MANIFEST = CASE_DIR / "manifest.json"
HEADING = re.compile(r"^## Case (\d+):?\s*(.*)$", re.M)


def parse(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    matches = list(HEADING.finditer(text))
    if not matches:
        raise ValueError("No Case headings found")
    prefix = text[:matches[0].start()]
    cases = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        cases.append((int(match.group(1)), match.group(2).strip(), text[match.start():end].rstrip() + "\n"))
    ids = [case_id for case_id, _, _ in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate Case IDs")
    return prefix, cases


def index_text(prefix: str, cases: list[tuple[int, str, str]]) -> str:
    output = [prefix.rstrip(), "", "---", "", "## Case archive navigation", "", "每個 Case 已拆成獨立檔案；永久 ID 不變。最新結構化成效以 `../data/*.jsonl` 為準。", "", "| Case | 標題 | 檔案 |", "|---:|---|---|"]
    for case_id, title, _ in sorted(cases, reverse=True):
        safe_title = title.replace("|", "／")
        output.append(f"| {case_id} | {safe_title} | [Case {case_id}](cases/case-{case_id:02d}.md) |")
    return "\n".join(output) + "\n"


def verify(cases: list[tuple[int, str, str]]) -> None:
    missing = []
    changed = []
    for case_id, _, expected in cases:
        path = CASE_DIR / f"case-{case_id:02d}.md"
        if not path.exists():
            missing.append(str(path))
        elif path.read_text(encoding="utf-8-sig") != expected:
            changed.append(str(path))
    if missing or changed:
        raise ValueError(f"archive verification failed missing={missing} changed={changed}")


def write_manifest(cases: list[tuple[int, str, str]]) -> None:
    records = []
    for case_id, title, content in cases:
        records.append({
            "case_id": case_id,
            "title": title,
            "path": f"case-{case_id:02d}.md",
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        })
    MANIFEST.write_text(json.dumps({"schema_version": "1.0", "cases": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_manifest() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    for record in manifest["cases"]:
        path = CASE_DIR / record["path"]
        if not path.exists():
            raise ValueError(f"missing archive file: {path}")
        normalized = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if digest != record["sha256"]:
            raise ValueError(f"archive checksum mismatch: {path}")
    return len(manifest["cases"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify and MANIFEST.exists():
        count = verify_manifest()
        print(f"verified {count} cases from manifest")
        return 0
    original = SOURCE.read_text(encoding="utf-8-sig")
    prefix, cases = parse(original)
    if args.write:
        CASE_DIR.mkdir(parents=True, exist_ok=True)
        for case_id, _, content in cases:
            (CASE_DIR / f"case-{case_id:02d}.md").write_text(content, encoding="utf-8")
        verify(cases)
        write_manifest(cases)
        SOURCE.write_text(index_text(prefix, cases), encoding="utf-8")
        print(f"split {len(cases)} cases; index rewritten")
        return 0
    if args.verify:
        verify(cases)
        print(f"verified {len(cases)} cases")
        return 0
    print(f"DRY_RUN cases={len(cases)} target={CASE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
