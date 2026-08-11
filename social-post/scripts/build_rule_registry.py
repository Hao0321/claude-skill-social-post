#!/usr/bin/env python3
"""Generate a machine-readable index from references/rules.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "rules.md"
RULE_DIR = ROOT / "references" / "rules"
OUTPUT = ROOT / "data" / "rule_registry.json"
HEADING = re.compile(r"^## (R\d+)\s*[：:]\s*(.+)$", re.M)


def build() -> dict:
    sources = sorted(RULE_DIR.glob("R*.md")) if RULE_DIR.exists() else [SOURCE]
    rules = []
    for source in sources:
        text = source.read_text(encoding="utf-8-sig")
        matches = list(HEADING.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[match.end():end]
            heading = match.group(2).strip()
            if "廢除" in heading or "撤回" in heading:
                status = "deprecated"
            elif "🧪" in heading or "emerging" in heading.casefold():
                status = "emerging"
            else:
                status = "active"
            sample_mentions = sorted({int(value) for value in re.findall(r"n\s*=\s*(\d+)", section, re.I)})
            rules.append({
                "id": match.group(1),
                "title": heading,
                "status": status,
                "source_file": source.relative_to(ROOT).as_posix(),
                "source_line": text.count("\n", 0, match.start()) + 1,
                "sample_mentions": sample_mentions,
            })
    rules.sort(key=lambda item: int(item["id"][1:]))
    source_of_truth = "references/rules/RNN.md" if RULE_DIR.exists() else "references/rules.md"
    return {"schema_version": "1.0", "source_of_truth": source_of_truth, "rules": rules}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    registry = build()
    rendered = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(registry['rules'])} rules)")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
