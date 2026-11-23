"""Public export privacy/ownership regression tests, separate from outcome fixtures."""

import json
import tempfile
from pathlib import Path

from social_data import SKILL_ROOT
from sync_public import (
    candidates,
    forbidden_public_paths,
    managed_paths,
    privacy_violations,
    public_generated_cache_paths,
    public_tree_rows,
    purge_public_generated,
    safe_destination,
    write_manifest,
)



def check_private_binary_tokens(candidate: Path) -> None:
    private_config_path = SKILL_ROOT / "audit.config.json"
    if not private_config_path.exists():
        return
    private_config = json.loads(private_config_path.read_text(encoding="utf-8-sig"))
    private_tokens = private_config.get("sync", {}).get("privacy", {}).get("tokens", [])[-3:]
    if len(private_tokens) != 3:
        raise AssertionError("private 8/27 privacy fixtures are missing")
    for token_index, token in enumerate(private_tokens):
        case_variant = "".join(
            char.swapcase() if char.isascii() and char.isalpha() else char for char in token
        )
        token_variants = (
            b"\xff" + case_variant.encode("utf-8"),
            case_variant.encode("utf-16-le"),
            case_variant.encode("utf-16-be"),
            b"\xff\xfe" + case_variant.encode("utf-16-le"),
            b"\xfe\xff" + case_variant.encode("utf-16-be"),
        )
        token_config = {"sync": {"privacy": {"tokens": [token], "patterns": []}}}
        for encoding_index, payload in enumerate(token_variants):
            candidate.write_bytes(payload)
            if not privacy_violations(
                [(candidate, f"private-token-{token_index}-{encoding_index}.bin")], token_config
            ):
                raise AssertionError(
                    f"private token {token_index} encoding {encoding_index} escaped the privacy scan"
                )


def check_public_privacy_guard(candidate: Path) -> None:
    config = {"sync": {"privacy": {"tokens": ["private-account"], "patterns": []}}}
    candidate.write_text("contains private-account marker", encoding="utf-8")
    if not privacy_violations([(candidate, "candidate.md")], config):
        raise AssertionError("public sync privacy token was not blocked")
    secret_fixture = "Author" + "ization: " + "Bearer " + "private-" + "secret-value"
    candidate.write_text(secret_fixture, encoding="utf-8")
    pattern_config = {"sync": {"privacy": {"tokens": [], "patterns": [
        r"(?i)Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~-]{8,}",
    ]}}}
    if not privacy_violations([(candidate, "candidate.md")], pattern_config):
        raise AssertionError("public sync credential-shaped pattern was not blocked")
    candidate.write_bytes(
        b"\xff\x00Author" + b"ization: " + b"Bearer " + b"private-secret-value\x00"
        + "私人里程碑".encode("utf-16-le")
    )
    binary_config = {"sync": {"privacy": {
        "tokens": ["私人里程碑"], "patterns": pattern_config["sync"]["privacy"]["patterns"],
    }}}
    if len(privacy_violations([(candidate, "candidate.pyc")], binary_config)) != 2:
        raise AssertionError("public sync binary privacy scan missed a token or secret pattern")
    credential = "Author" + "ization: " + "Bearer " + "private-" + "secret-value"
    credential_variants = (
        b"\xff" + credential.encode("utf-8"), credential.encode("utf-16-le"),
        credential.encode("utf-16-be"), b"\xff\xfe" + credential.encode("utf-16-le"),
        b"\xfe\xff" + credential.encode("utf-16-be"),
    )
    for index, payload in enumerate(credential_variants):
        candidate.write_bytes(payload)
        if not privacy_violations([(candidate, f"credential-{index}.bin")], pattern_config):
            raise AssertionError(f"binary credential encoding {index} escaped the privacy scan")
    check_private_binary_tokens(candidate)


def check_public_generated_guard(root: Path) -> None:
    config = {"sync": {"purge_public_generated": ["scripts/__pycache__"]}}
    if public_generated_cache_paths(config) != {"scripts/__pycache__"}:
        raise AssertionError("public generated-cache allowlist did not normalize")
    cache_dir = root / "scripts" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "fixture.pyc").write_bytes(b"generated")
    if purge_public_generated(root, config) != ["scripts/__pycache__"] or cache_dir.exists():
        raise AssertionError("configured public generated cache was not removed")
    try:
        public_generated_cache_paths({"sync": {"purge_public_generated": ["scripts/**/__pycache__"]}})
    except ValueError:
        return
    raise AssertionError("public generated-cache allowlist accepted a glob")


def check_public_inventory_guard(root: Path, candidate: Path) -> None:
    candidate.write_text("public fixture", encoding="utf-8")
    try:
        safe_destination(root, "../escape.txt")
    except ValueError:
        pass
    else:
        raise AssertionError("public sync accepted a path outside its root")
    write_manifest(root, ["safe.md"])
    if managed_paths(root) != {"safe.md"}:
        raise AssertionError("public sync managed manifest did not round-trip")
    unmanaged = root / "unmanaged-example.md"
    unmanaged.write_text("contains private-account marker", encoding="utf-8")
    config = {"sync": {"privacy": {"tokens": ["private-account"], "patterns": []}}}
    public_rows, public_failures = public_tree_rows(root)
    if public_failures or not privacy_violations(public_rows, config):
        raise AssertionError("unmanaged public file escaped the privacy scan")
    unmanaged.unlink()
    linked = root / "linked-example.md"
    try:
        linked.symlink_to(candidate)
    except OSError:
        pass
    else:
        _public_rows, public_failures = public_tree_rows(root)
        if not public_failures:
            raise AssertionError("linked public path escaped the privacy scan")
        linked.unlink()
    (root / "safe.md").write_text("public", encoding="utf-8")
    (root / "private.jsonl").write_text('{"author":"private"}\n', encoding="utf-8")
    fixture_ignore = ["candidate.md", ".social-post-managed.json"]
    allowlist = {"sync": {"include": ["safe.md"], "ignore": [
        *fixture_ignore, "private.jsonl",
    ]}, "exclude": []}
    if [relative for _path, relative in candidates(allowlist, root)] != ["safe.md"]:
        raise AssertionError("public sync copied a file outside the closed-world allowlist")
    try:
        candidates({"sync": {"include": ["safe.md"], "ignore": fixture_ignore}, "exclude": []}, root)
    except ValueError:
        pass
    else:
        raise AssertionError("public sync silently accepted an unclassified private file")
    try:
        candidates({"sync": {"ignore": []}}, root)
    except ValueError:
        pass
    else:
        raise AssertionError("public sync accepted a missing include allowlist")
    if forbidden_public_paths({"sync": {"forbid_public": ["audit.config.json"]}}) != {
        "audit.config.json"
    }:
        raise AssertionError("public sync lost its exact private-only path contract")
    try:
        forbidden_public_paths({"sync": {"forbid_public": ["*.json"]}})
    except ValueError:
        return
    raise AssertionError("public sync accepted a destructive forbidden-path glob")


def check_public_sync_guard() -> None:
    with tempfile.TemporaryDirectory(prefix="social-post-public-guard-") as raw:
        root = Path(raw)
        candidate = root / "candidate.md"
        check_public_privacy_guard(candidate)
        check_public_generated_guard(root)
        check_public_inventory_guard(root, candidate)


if __name__ == "__main__":
    check_public_sync_guard()
    print("public sync guard passed")

