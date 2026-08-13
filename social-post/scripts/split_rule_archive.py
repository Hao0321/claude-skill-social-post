#!/usr/bin/env python3
"""Split references/rules.md into one file per permanent R ID."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "rules.md"
RULE_DIR = ROOT / "references" / "rules"
MANIFEST = RULE_DIR / "manifest.json"
HEADING = re.compile(r"^## (R\d+)：\s*(.*)$", re.M)


def parse(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    matches = list(HEADING.finditer(text))
    if not matches:
        raise ValueError("No R headings found")
    prefix = text[:matches[0].start()]
    rules = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        rule_id = int(match.group(1)[1:])
        rules.append((rule_id, match.group(2).strip(), text[match.start():end].rstrip() + "\n"))
    ids = [rule_id for rule_id, _, _ in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate R IDs")
    return prefix, rules


def index_text(prefix: str, rules: list[tuple[int, str, str]]) -> str:
    output = [prefix.rstrip(), "", "---", "", "## R1-R42 navigation", "", "每條永久規則已拆成獨立檔案。只讀任務相關的 R，避免一次載入整本規則庫。", "", "| R | 標題 | 狀態 | 檔案 |", "|---:|---|---|---|"]
    for rule_id, title, _ in sorted(rules):
        if "廢除" in title or "撤回" in title:
            status = "deprecated"
        elif "🧪" in title or "emerging" in title.casefold():
            status = "emerging"
        else:
            status = "active"
        safe_title = title.replace("|", "／")
        output.append(f"| R{rule_id} | {safe_title} | {status} | [R{rule_id}](rules/R{rule_id:02d}.md) |")
    return "\n".join(output) + "\n"


def normalized_hash(content: str) -> str:
    return hashlib.sha256(content.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def verify_rules(rules: list[tuple[int, str, str]]) -> None:
    for rule_id, _, expected in rules:
        path = RULE_DIR / f"R{rule_id:02d}.md"
        if not path.exists():
            raise ValueError(f"missing rule file: {path}")
        actual = path.read_text(encoding="utf-8-sig")
        if normalized_hash(actual) != normalized_hash(expected):
            raise ValueError(f"rule content mismatch: {path}")


def write_manifest(rules: list[tuple[int, str, str]]) -> None:
    records = [{
        "rule_id": f"R{rule_id}",
        "title": title,
        "path": f"R{rule_id:02d}.md",
        "sha256": normalized_hash(content),
    } for rule_id, title, content in rules]
    MANIFEST.write_text(json.dumps({"schema_version": "1.0", "rules": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def current_rules() -> list[tuple[int, str, str]]:
    rules = []
    for path in sorted(RULE_DIR.glob("R*.md")):
        text = path.read_text(encoding="utf-8-sig")
        match = HEADING.search(text)
        if not match:
            raise ValueError(f"missing R heading: {path}")
        rules.append((int(match.group(1)[1:]), match.group(2).strip(), text.replace("\r\n", "\n")))
    if not rules:
        raise ValueError("No split rule files found")
    return rules


def verify_manifest() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    for record in manifest["rules"]:
        path = RULE_DIR / record["path"]
        if not path.exists():
            raise ValueError(f"missing rule file: {path}")
        if normalized_hash(path.read_text(encoding="utf-8-sig")) != record["sha256"]:
            raise ValueError(f"rule checksum mismatch: {path}")
    return len(manifest["rules"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--refresh-manifest", action="store_true")
    args = parser.parse_args()
    if args.refresh_manifest:
        rules = current_rules()
        write_manifest(rules)
        print(f"refreshed manifest for {len(rules)} rules")
        return 0
    if args.verify and MANIFEST.exists():
        count = verify_manifest()
        print(f"verified {count} rules from manifest")
        return 0
    prefix, rules = parse(SOURCE.read_text(encoding="utf-8-sig"))
    if args.write:
        RULE_DIR.mkdir(parents=True, exist_ok=True)
        for rule_id, _, content in rules:
            (RULE_DIR / f"R{rule_id:02d}.md").write_text(content, encoding="utf-8")
        verify_rules(rules)
        write_manifest(rules)
        SOURCE.write_text(index_text(prefix, rules), encoding="utf-8")
        print(f"split {len(rules)} rules; index rewritten")
        return 0
    print(f"DRY_RUN rules={len(rules)} target={RULE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
