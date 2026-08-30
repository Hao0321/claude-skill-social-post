#!/usr/bin/env python3
"""Check the public Hermes Tweet documentation contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parent
REFERENCE = "references/hermes-tweet.md"
TEST_SCRIPT = "scripts/social_test_hermes_tweet_contract.py"


def require(path: Path, snippets: tuple[str, ...]) -> str:
    text = path.read_text(encoding="utf-8")
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")
    return text


def check_examples(reference: str) -> None:
    blocks = re.findall(r"```json\n(.*?)\n```", reference, re.DOTALL)
    if len(blocks) != 4:
        raise AssertionError(f"expected 4 Hermes JSON examples, found {len(blocks)}")
    explore_read, read, explore_action, action = (json.loads(block) for block in blocks)
    if explore_read.get("method") != "GET" or not explore_read.get("query"):
        raise AssertionError("read discovery example lost its bounded catalog query")
    if not read.get("path", "").startswith("/api/v1/") or read.get("query", {}).get("limit") != 25:
        raise AssertionError("read example lost its catalog path or result limit")
    if explore_action.get("include_actions") is not True:
        raise AssertionError("action discovery example does not request action routes")
    required = {"path", "method", "body", "reason"}
    if required - action.keys() or action.get("method") != "POST":
        raise AssertionError("action example lost its explicit operation contract")


def main() -> int:
    reference = require(
        ROOT / REFERENCE,
        (
            "tweet_explore",
            "tweet_read",
            "tweet_action",
            "HERMES_TWEET_ENABLE_ACTIONS=true",
            "不要建立直接 HTTP fallback",
            "每次都需要精確核准",
        ),
    )
    check_examples(reference)
    require(ROOT / "SKILL.md", (REFERENCE, "tweet_action"))
    require(ROOT / "references" / "generate_and_publish.md", ("hermes-tweet.md", "endpoint"))
    require(ROOT / "references" / "x.md", ("hermes-tweet.md", "tweet_explore"))
    require(REPOSITORY_ROOT / "docs" / "setup.md", ("Xquik-dev/hermes-tweet", "tweet_action"))
    require(REPOSITORY_ROOT / "README.md", ("Hermes Tweet", "Xquik-dev/hermes-tweet"))
    manifest = json.loads((ROOT / ".social-post-managed.json").read_text(encoding="utf-8"))
    managed = set(manifest.get("managed_paths", []))
    if not {REFERENCE, TEST_SCRIPT} <= managed:
        raise AssertionError(
            "Hermes reference or contract test is absent from the managed manifest"
        )
    print("Hermes Tweet contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
