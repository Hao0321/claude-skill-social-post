"""Versioned private author contracts and deterministic draft checks.

Hashes enforce integrity, not semantic quality. Host review is always required.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from social_governance_store import digest, governance_lock, private_path, read_document, write_document

POINTER = "data/author_contract.json"
POLICY = "data/writing_policy.json"
FORMULA = re.compile(r"^F(?:0[1-9]|[12][0-9]|30)(?:[a-d]|-mini)?$")
SOURCE_NAMES = ("voice_quick.md", "style_profile.md", "references/formulas.md", "references/rules.md", POLICY)
CHECK_KEYS = {"paragraphs", "no_links", "no_lists", "exclamations_first_only", "bare_endings_after_first"}


def formula_path(identity: str) -> str:
    if not FORMULA.fullmatch(identity):
        raise ValueError("unknown formula identity")
    base = identity if identity.endswith("-mini") else identity[:3]
    return "references/formulas/" + base + ".md"


def policy_valid(policy: Any) -> None:
    if not isinstance(policy, dict) or set(policy) != {"schema_version", "no_emoji", "plain_text", "formula_checks"}:
        raise ValueError("invalid writing policy fields")
    if policy["schema_version"] != 1 or policy["no_emoji"] is not True or policy["plain_text"] is not True:
        raise ValueError("baseline no-emoji/plain-text policy cannot be silently weakened")
    if not isinstance(policy["formula_checks"], dict):
        raise ValueError("formula checks must be an object")
    for identity, checks in policy["formula_checks"].items():
        formula_path(identity)
        if not isinstance(checks, dict) or set(checks) - CHECK_KEYS:
            raise ValueError("unsupported formula constraint")
        for key, value in checks.items():
            if key == "paragraphs":
                if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 50:
                    raise ValueError("paragraph constraint exceeds bound")
            elif not isinstance(value, bool):
                raise ValueError("formula switch must be boolean")


def _version_path(revision: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise ValueError("invalid author revision")
    return "data/author_contracts/" + revision + ".json"


def _policy(sources: dict[str, Any]) -> dict[str, Any]:
    if POLICY not in sources:
        return {"schema_version": 1, "no_emoji": True, "plain_text": True, "formula_checks": {}}
    policy = json.loads(sources[POLICY]["text"])
    policy_valid(policy)
    return policy


def save_version_locked(root: Path, document: dict[str, Any]) -> str:
    revision = digest(document)
    write_document(root, _version_path(revision), document, immutable=True)
    return revision


def source_names(root: Path) -> set[str]:
    names = {name for name in SOURCE_NAMES if private_path(root, name).is_file()}
    for folder, pattern in (("references/formulas", "F*.md"), ("references/rules", "R[0-9]*.md")):
        directory = private_path(root, folder)
        if directory.exists():
            names.update(path.relative_to(root).as_posix() for path in directory.glob(pattern))
    return names


def bootstrap(root: Path) -> dict[str, Any]:
    """One-time explicit setup; never recapture drift as a new baseline."""
    with governance_lock(root):
        if private_path(root, POINTER).exists():
            return verify_contract(root)
        names = source_names(root)
        if not names or "voice_quick.md" not in names:
            raise ValueError("real author voice is required before locking")
        sources = {}
        for name in sorted(names):
            raw = private_path(root, name).read_bytes()
            if len(raw) > 256 * 1024:
                raise ValueError("author source exceeds bound")
            source = raw.decode("utf-8-sig")
            if name == "voice_quick.md" and ("[待填]" in source or "<your" in source.lower()):
                raise ValueError("placeholder voice cannot be locked as a learned author")
            sources[name] = {"disk_sha256": hashlib.sha256(raw).hexdigest(), "text": source,
                             "effective_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest()}
        _policy(sources)
        document = {"schema_version": 1, "parent_revision": None, "proposal_digest": None,
                    "sources": sources, "overrides": []}
        revision = save_version_locked(root, document)
        write_document(root, POINTER, {"schema_version": 1, "revision": revision})
        return verify_contract(root)


def active_contract(root: Path) -> tuple[str, dict[str, Any]]:
    pointer = read_document(root, POINTER)
    if set(pointer) != {"schema_version", "revision"} or pointer["schema_version"] != 1:
        raise ValueError("invalid author contract pointer")
    revision = pointer["revision"]
    document = read_document(root, _version_path(revision))
    if digest(document) != revision or document.get("schema_version") != 1:
        raise ValueError("author contract version failed integrity verification")
    if not isinstance(document.get("sources"), dict):
        raise ValueError("invalid author source map")
    return revision, document


def verify_contract(root: Path) -> dict[str, Any]:
    revision, document = active_contract(root)
    if source_names(root) != set(document["sources"]):
        raise ValueError("unreviewed author-source inventory change")
    for name, source in document["sources"].items():
        raw = private_path(root, name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["disk_sha256"]:
            raise ValueError("unreviewed author-source drift: " + name)
        if hashlib.sha256(source["text"].encode("utf-8")).hexdigest() != source["effective_sha256"]:
            raise ValueError("effective author source failed integrity verification")
    for override in document.get("overrides", []):
        if override["target"] not in document["sources"] or digest(override["text"]) != override["text_digest"]:
            raise ValueError("reviewed override failed integrity verification")
        if override["target"] == POLICY:
            policy_valid(json.loads(override["text"]))
    _policy(document["sources"])
    return {"status": "locked", "revision": revision, "sources": len(document["sources"]),
            "parent_revision": document["parent_revision"], "automatic_update": False}


def contract_status(root: Path) -> dict[str, Any]:
    if not private_path(root, POINTER).exists():
        return {"status": "unconfigured", "automatic_update": False}
    return verify_contract(root)


def effective_sources(document: dict[str, Any], platform: str | None, family: str | None) -> dict[str, Any]:
    sources = {name: dict(source) for name, source in document["sources"].items()}
    for override in document.get("overrides", []):
        if override["scope"] != {"platform": platform, "media_family": family}:
            continue
        source = sources[override["target"]]
        source["text"] = override["text"]
        source["effective_sha256"] = hashlib.sha256(override["text"].encode("utf-8")).hexdigest()
        source["reviewed_override"] = True
    return sources


def writing_context(root: Path, formula: str, writing_format: str,
                    platform: str | None = None, family: str | None = None) -> dict[str, Any]:
    verified = verify_contract(root)
    _, document = active_contract(root)
    sources = effective_sources(document, platform, family)
    name = formula_path(formula) if formula else None
    if name and name not in sources:
        raise ValueError("selected formula was not locked")
    if formula == "F06":
        raise ValueError("F06 has distinct variants; explicitly choose F06a or F06b")
    if formula and formula[-1] in "abcd" and not re.search(
        rf"\bF0?{int(formula[1:3])}{formula[-1]}\b", sources[name]["text"], re.I
    ):
        raise ValueError("selected formula variant is not documented")
    if writing_format not in {"A", "B", "C"}:
        raise ValueError("explicit writing format is required")
    if name:
        declared = re.findall(r"(?im)^#{1,6}[^\n]*\bMode\s+([ABC])\b", sources[name]["text"])
        if len(set(declared)) == 1 and writing_format != declared[0].upper():
            raise ValueError("selected F requires Mode " + declared[0].upper() + "; choose a compatible formula or format")
    return {**verified, "formula": formula, "format": writing_format,
            "scope": {"platform": platform, "media_family": family},
            "policy": _policy(sources), "voice": sources["voice_quick.md"]["text"],
            "formula_source": sources[name]["text"] if name else None,
            "formula_sha256": sources[name]["effective_sha256"] if name else None,
            "reviewed_overrides": {path: source["text"] for path, source in sources.items()
                                   if source.get("reviewed_override")},
            "semantic_review_required": True,
            "strategy_numbers_are_unverified_unless_backed_by_current_evidence": True}


def contains_emoji(text: str) -> bool:
    return any(0x1F000 <= ord(char) <= 0x1FAFF or 0x2600 <= ord(char) <= 0x27BF
               or char in "\ufe0f\u20e3" for char in text)


def check_draft(root: Path, text: str, formula: str, writing_format: str,
                expected_revision: str, platform: str | None = None, family: str | None = None) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip() or len(text) > 24000:
        raise ValueError("draft must be nonempty bounded text")
    context = writing_context(root, formula, writing_format, platform, family)
    if context["revision"] != expected_revision:
        raise ValueError("draft uses a stale author contract")
    failures = []
    paragraphs = re.split(r"\n\s*\n", text.strip())
    policy = context["policy"]
    checks = policy["formula_checks"].get(formula, {})
    if policy["no_emoji"] and contains_emoji(text):
        failures.append("emoji_not_allowed")
    if policy["plain_text"] and re.search(r"(?m)^\s{0,3}#{1,6}\s|\*\*|```|\[[^\]]+\]\(https?://", text):
        failures.append("plain_text_required")
    if "paragraphs" in checks and len(paragraphs) != checks["paragraphs"]:
        failures.append("wrong_paragraph_count")
    if checks.get("no_links") and re.search(r"https?://|www\.", text, re.I):
        failures.append("links_not_allowed")
    if checks.get("no_lists") and re.search(r"(?m)^\s*(?:[-*•]|\d+[.)、])\s*\S", text):
        failures.append("lists_not_allowed")
    if checks.get("exclamations_first_only") and any(re.search(r"[!！]", part) for part in paragraphs[1:]):
        failures.append("exclamations_after_first")
    if checks.get("bare_endings_after_first") and any(
        unicodedata.category(part.rstrip()[-1]).startswith(("P", "S")) for part in paragraphs[1:]
    ):
        failures.append("punctuated_ending_after_first")
    return {"revision": context["revision"], "formula": formula, "format": writing_format,
            "draft_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "structural_pass": not failures, "failures": failures,
            "paragraphs": len(paragraphs), "semantic_review_required": True,
            "delivery_ready": False,
            "note": "Host must additionally review the complete effective formula, ordered intent, author voice and factual sources."}
