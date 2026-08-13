#!/usr/bin/env python3
"""Split the legacy formula monolith into one routed file per formula family."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "formulas.md"
TARGET = ROOT / "references" / "formulas"
HEADING = re.compile(r"^(?P<level>##|###) (?P<label>F\d+(?: mini)?)｜(?P<title>.+)$", re.M)


def target_name(label: str) -> str:
    match = re.fullmatch(r"F(\d+)( mini)?", label)
    if not match:
        raise ValueError(f"invalid formula label: {label}")
    suffix = "-mini" if match.group(2) else ""
    return f"F{int(match.group(1)):02d}{suffix}.md"


def split() -> list[dict[str, str]]:
    text = SOURCE.read_text(encoding="utf-8-sig")
    matches = list(HEADING.finditer(text))
    if not matches:
        raise ValueError("no formula headings found")
    TARGET.mkdir(parents=True, exist_ok=True)
    records = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        label = match.group("label")
        filename = target_name(label)
        section = text[match.start():end].strip() + "\n"
        (TARGET / filename).write_text(section, encoding="utf-8")
        records.append({"id": label.replace(" ", "-"), "title": match.group("title").strip(), "path": filename})
    prelude = text[:matches[0].start()].rstrip()
    navigation = [
        "",
        "## Formula files",
        "",
        "只開任務需要的一個公式檔。共同演算法／選擇原則留在本索引；公式全文在 `formulas/`。",
        "",
        "| Formula | Title | File |",
        "|---|---|---|",
    ]
    navigation.extend(
        f"| {row['id']} | {row['title']} | [{row['path']}](formulas/{row['path']}) |"
        for row in records
    )
    SOURCE.write_text(prelude + "\n" + "\n".join(navigation) + "\n", encoding="utf-8")
    manifest = {"schema_version": "1.0", "source_of_truth": "references/formulas/FNN.md", "formulas": records}
    (TARGET / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records


def refresh_manifest() -> list[dict[str, str]]:
    records = []
    for path in sorted(TARGET.glob("F*.md")):
        heading = HEADING.search(path.read_text(encoding="utf-8-sig"))
        if not heading:
            raise ValueError(f"missing formula heading: {path}")
        records.append({"id": heading.group("label").replace(" ", "-"), "title": heading.group("title").strip(), "path": path.name})
    manifest = {"schema_version": "1.0", "source_of_truth": "references/formulas/FNN.md", "formulas": records}
    (TARGET / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-manifest", action="store_true")
    args = parser.parse_args()
    records = refresh_manifest() if args.refresh_manifest else split()
    print(f"formula archive ready: {len(records)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
