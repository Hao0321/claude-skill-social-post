#!/usr/bin/env python3
"""Offline-verifiable scan provenance and browser-action digest chaining.

This contract deliberately proves only receipt continuity.  It never asserts a
trusted Chrome host, full lifecycle node mapping, or production capability.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import re
import secrets
from typing import Any

from comment_browser_common import DIGEST_PATTERN, _json_digest
from social_primitives import parse_time


SCAN_PROVENANCE_SCHEMA_VERSION = 1
SCAN_PROVENANCE_DIGEST_FIELD = "scan_provenance_digest"
DRAFT_PROVENANCE_DIGEST_FIELD = "draft_provenance_digest"
ACTION_PROVENANCE_DIGEST_FIELD = "action_provenance_digest"
SCAN_CAPABILITY_OPERATION = "browser-scan"
SCAN_CAPABILITY_VERSION = 1
SCAN_CAPABILITY_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
SCAN_CAPABILITY_NONCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


def build_scan_capability_binding(request: dict[str, Any]) -> dict[str, Any]:
    """Bind one browser scan bearer to one stored request and exact scope."""
    scope = {
        key: _required_string(request, key, "browser scan request")
        for key in ("platform", "account_key", "post_key", "post_permalink")
    }
    binding = {
        "provenance_version": SCAN_CAPABILITY_VERSION,
        "operation": SCAN_CAPABILITY_OPERATION,
        "scan_request_id": _required_string(
            request, "scan_request_id", "browser scan request",
        ),
        "authorized_session_id": _required_string(
            request, "session_id", "browser scan request",
        ),
        "requested_at": _required_string(
            request, "requested_at", "browser scan request",
        ),
        "request_expires_at": _required_string(
            request, "expires_at", "browser scan request",
        ),
        "scope": scope,
    }
    if request.get("observation_scope") == "target_comment":
        binding["observation_scope"] = "target_comment"
        binding["target"] = request["target"]
    return binding


def _scan_secret_hash(capability_id: str, binding_digest: str, nonce: str) -> str:
    """Hash a bearer with its random capability id as a public per-issue salt."""
    material = (
        f"social-post-browser-scan-capability-v{SCAN_CAPABILITY_VERSION}\0"
        f"{capability_id}\0{binding_digest}\0{nonce}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def issue_scan_receipt_capability(
    request: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a one-shot bearer plus nonce-free request-ledger metadata."""
    binding = build_scan_capability_binding(request)
    issued_at = parse_time(binding["requested_at"]).astimezone(timezone.utc)
    expires_at = parse_time(binding["request_expires_at"]).astimezone(timezone.utc)
    if expires_at <= issued_at:
        raise ValueError("browser scan capability expiry must follow issuance")
    binding_digest = _json_digest(binding)
    capability_id = secrets.token_hex(16)
    nonce = secrets.token_urlsafe(32)
    bearer = {
        "schema_version": SCAN_CAPABILITY_VERSION,
        "operation": SCAN_CAPABILITY_OPERATION,
        "capability_id": capability_id,
        "nonce": nonce,
    }
    metadata = {
        "browser_scan_capability_version": SCAN_CAPABILITY_VERSION,
        "browser_scan_capability_id": capability_id,
        "browser_scan_capability_hash": _scan_secret_hash(
            capability_id, binding_digest, nonce,
        ),
        "browser_scan_capability_binding_digest": binding_digest,
        "browser_scan_capability_issued_at": issued_at.isoformat(),
        "browser_scan_capability_expires_at": expires_at.isoformat(),
    }
    return bearer, metadata


def normalize_scan_capability_metadata(
    raw: dict[str, Any], *, required: bool = False,
) -> dict[str, Any]:
    """Validate persisted scan authority metadata without ever accepting a nonce."""
    keys = (
        "browser_scan_capability_version",
        "browser_scan_capability_id",
        "browser_scan_capability_hash",
        "browser_scan_capability_binding_digest",
        "browser_scan_capability_issued_at",
        "browser_scan_capability_expires_at",
    )
    present = [key for key in keys if raw.get(key) is not None]
    if not present:
        if required:
            raise ValueError("browser-scan has no versioned receipt capability")
        return {}
    if len(present) != len(keys):
        raise ValueError("browser scan capability metadata is incomplete")
    if raw.get("browser_scan_capability_version") != SCAN_CAPABILITY_VERSION:
        raise ValueError("browser scan capability version must be integer 1")
    capability_id = raw.get("browser_scan_capability_id")
    if not isinstance(capability_id, str) or not SCAN_CAPABILITY_ID_PATTERN.fullmatch(
        capability_id
    ):
        raise ValueError("browser scan capability id is invalid")
    for key in (
        "browser_scan_capability_hash",
        "browser_scan_capability_binding_digest",
    ):
        value = raw.get(key)
        if not isinstance(value, str) or not DIGEST_PATTERN.fullmatch(value):
            raise ValueError(f"{key} is invalid")
    issued_at = str(raw.get("browser_scan_capability_issued_at") or "")
    expires_at = str(raw.get("browser_scan_capability_expires_at") or "")
    if parse_time(expires_at) <= parse_time(issued_at):
        raise ValueError("browser scan capability expiry must follow issuance")
    return {key: raw[key] for key in keys}


def _require_scan_receipt_binding(
    receipt: dict[str, Any], request: dict[str, Any],
) -> None:
    expected_scope = {
        key: request[key]
        for key in ("platform", "account_key", "post_key", "post_permalink")
    }
    supplied_scope = {
        key: receipt.get(key)
        for key in ("platform", "account_key", "post_key", "post_permalink")
    }
    if receipt.get("scan_request_id") != request.get("scan_request_id"):
        raise ValueError("browser-scan receipt differs from its stored scan request")
    if receipt.get("session_id") != request.get("session_id"):
        raise ValueError("browser-scan receipt session differs from its stored scan request")
    if supplied_scope != expected_scope:
        raise ValueError("browser-scan receipt scope differs from its stored scan request")
    if request.get("observation_scope") == "target_comment":
        if receipt.get("observation_scope") != "target_comment":
            raise ValueError("target observation receipt cannot become a whole-post scan")
        comment = receipt.get("comment")
        if not isinstance(comment, dict) or any(
            comment.get(key) != value for key, value in request["target"].items()
        ):
            raise ValueError("target observation receipt differs from its exact target")
    elif receipt.get("observation_scope") == "target_comment":
        raise ValueError("whole-post scan capability cannot authorize a target observation")


def consume_scan_receipt_envelope(
    envelope: Any, request: dict[str, Any], *, now: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate one short-lived scan bearer and return nonce-free consumption data."""
    if not isinstance(envelope, dict) or set(envelope) != {"provenance", "receipt"}:
        raise ValueError("browser-scan requires exactly provenance and receipt fields")
    provenance = envelope.get("provenance")
    receipt = envelope.get("receipt")
    if not isinstance(provenance, dict) or not isinstance(receipt, dict):
        raise ValueError("browser-scan provenance and receipt must be objects")
    if provenance.get("schema_version") != SCAN_CAPABILITY_VERSION:
        raise ValueError("browser-scan provenance schema_version must be integer 1")
    if provenance.get("operation") != SCAN_CAPABILITY_OPERATION:
        raise ValueError("browser-scan provenance operation differs from the command")
    capability_id = provenance.get("capability_id")
    nonce = provenance.get("nonce")
    if not isinstance(capability_id, str) or not SCAN_CAPABILITY_ID_PATTERN.fullmatch(
        capability_id
    ):
        raise ValueError("browser-scan provenance capability_id is invalid")
    if not isinstance(nonce, str) or not SCAN_CAPABILITY_NONCE_PATTERN.fullmatch(nonce):
        raise ValueError("browser-scan provenance nonce is invalid")
    metadata = normalize_scan_capability_metadata(request, required=True)
    _require_scan_receipt_binding(receipt, request)
    binding_digest = _json_digest(build_scan_capability_binding(request))
    if not hmac.compare_digest(
        binding_digest, metadata["browser_scan_capability_binding_digest"],
    ):
        raise ValueError("browser-scan capability binding differs from its stored request")
    if not hmac.compare_digest(
        capability_id, metadata["browser_scan_capability_id"],
    ):
        raise ValueError("browser-scan capability id was not issued for this request")
    candidate_hash = _scan_secret_hash(capability_id, binding_digest, nonce)
    if not hmac.compare_digest(
        candidate_hash, metadata["browser_scan_capability_hash"],
    ):
        raise ValueError("browser-scan capability nonce is invalid")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    capability_expiry = parse_time(
        metadata["browser_scan_capability_expires_at"]
    ).astimezone(timezone.utc)
    request_expiry = parse_time(str(request["expires_at"])).astimezone(timezone.utc)
    if current >= min(capability_expiry, request_expiry):
        raise ValueError("browser-scan receipt capability expired")
    return receipt, {
        "browser_scan_receipt_provenance_version": SCAN_CAPABILITY_VERSION,
        "browser_scan_receipt_operation": SCAN_CAPABILITY_OPERATION,
        "browser_scan_receipt_capability_id": capability_id,
        "browser_scan_receipt_binding_digest": binding_digest,
        "browser_scan_receipt_digest": _json_digest(receipt),
    }


def normalize_scan_receipt_consumption(
    raw: dict[str, Any], request: dict[str, Any], *, required: bool = False,
) -> dict[str, Any]:
    """Validate the nonce-free one-shot receipt evidence stored on completion."""
    keys = (
        "browser_scan_receipt_provenance_version",
        "browser_scan_receipt_operation",
        "browser_scan_receipt_capability_id",
        "browser_scan_receipt_binding_digest",
        "browser_scan_receipt_digest",
    )
    present = [key for key in keys if raw.get(key) is not None]
    if not present:
        if required:
            raise ValueError("live browser scan completion lacks one-shot receipt authority")
        return {}
    if len(present) != len(keys):
        raise ValueError("browser scan receipt consumption metadata is incomplete")
    if raw.get("browser_scan_receipt_provenance_version") != SCAN_CAPABILITY_VERSION:
        raise ValueError("browser scan receipt provenance version must be integer 1")
    if raw.get("browser_scan_receipt_operation") != SCAN_CAPABILITY_OPERATION:
        raise ValueError("browser scan receipt operation must be browser-scan")
    metadata = normalize_scan_capability_metadata(request, required=True)
    if raw.get("browser_scan_receipt_capability_id") != metadata[
        "browser_scan_capability_id"
    ]:
        raise ValueError("browser scan completion capability differs from its request")
    binding_digest = raw.get("browser_scan_receipt_binding_digest")
    if binding_digest != metadata["browser_scan_capability_binding_digest"]:
        raise ValueError("browser scan completion binding differs from its request")
    receipt_digest = raw.get("browser_scan_receipt_digest")
    if not isinstance(receipt_digest, str) or not DIGEST_PATTERN.fullmatch(receipt_digest):
        raise ValueError("browser scan completion receipt digest is invalid")
    return {key: raw[key] for key in keys}


def _required_string(value: dict[str, Any], key: str, label: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"{label} {key} must be a non-empty string")
    return result.strip()


def _required_digest(value: dict[str, Any], key: str, label: str) -> str:
    result = _required_string(value, key, label)
    if not DIGEST_PATTERN.fullmatch(result):
        raise ValueError(f"{label} {key} must be a lowercase SHA-256 digest")
    return result


def _required_count(value: dict[str, Any], key: str, label: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise ValueError(f"{label} {key} must be a non-negative integer")
    return result


def _verify_attestation_id(
    value: dict[str, Any], id_key: str, label: str,
) -> str:
    supplied = _required_digest(value, id_key, label)
    core = {key: item for key, item in value.items() if key != id_key}
    if supplied != _json_digest(core):
        raise ValueError(f"{label} {id_key} integrity check failed")
    return _json_digest(value)


def _receipt_digest(raw: dict[str, Any]) -> str:
    """Hash the receipt without accepting a caller-authored self digest."""
    core = {
        key: item for key, item in raw.items()
        if key not in {
            "scan_receipt_digest", "scan_provenance", SCAN_PROVENANCE_DIGEST_FIELD,
        }
    }
    digest = _json_digest(core)
    supplied = raw.get("scan_receipt_digest")
    if supplied is not None and supplied != digest:
        raise ValueError("browser scan scan_receipt_digest integrity check failed")
    return digest


def _evidence_pair(
    raw: dict[str, Any], scope: dict[str, str], comment_count: int,
) -> dict[str, Any] | None:
    expansion = raw.get("thread_expansion_evidence")
    expansion_attestation = (
        expansion.get("adapter_attestation") if isinstance(expansion, dict) else None
    )
    mapping = raw.get("stable_node_frame_mapping_evidence")
    if expansion_attestation is None and mapping is None:
        return None
    if not isinstance(expansion_attestation, dict) or not isinstance(mapping, dict):
        raise ValueError(
            "browser scan provenance requires both expansion and node/frame mapping evidence"
        )
    for label, evidence in (
        ("browser scan expansion attestation", expansion_attestation),
        ("browser scan node/frame mapping", mapping),
    ):
        version = evidence.get("schema_version")
        if not isinstance(version, int) or isinstance(version, bool) or version != 1:
            raise ValueError(f"{label} schema_version must be integer 1")
        if evidence.get("platform") != scope["platform"]:
            raise ValueError(f"{label} platform differs from scan scope")
        if not isinstance(evidence.get("test_only"), bool):
            raise ValueError(f"{label} test_only must be explicit boolean")
        if evidence["test_only"] != raw.get("test_only"):
            raise ValueError(f"{label} test_only differs from its scan receipt")

    adapter_id = _required_string(
        expansion_attestation, "adapter_id", "browser scan expansion attestation",
    )
    adapter_version = _required_string(
        expansion_attestation, "adapter_version", "browser scan expansion attestation",
    )
    if mapping.get("adapter_id") != adapter_id or mapping.get("adapter_version") != adapter_version:
        raise ValueError("browser scan mapping adapter differs from expansion attestation")
    if expansion_attestation.get("terminal_evidence") is not True:
        raise ValueError("browser scan expansion attestation is not terminal")
    if _required_count(
        expansion_attestation, "terminal_discovered_count",
        "browser scan expansion attestation",
    ) != comment_count:
        raise ValueError("browser scan exhaustion count differs from normalized comments")
    if _required_count(mapping, "row_count", "browser scan node/frame mapping") != comment_count:
        raise ValueError("browser scan mapping row count differs from normalized comments")
    if mapping.get("full_lifecycle_bound") is not False:
        raise ValueError(
            "scan provenance v1 accepts final-scan mapping only and cannot assert full lifecycle"
        )
    coverage = _required_string(mapping, "coverage", "browser scan node/frame mapping")
    reply_exhaustion_digest = _required_digest(
        mapping, "reply_exhaustion_sha256", "browser scan node/frame mapping",
    )
    exhaustion_digest = _verify_attestation_id(
        expansion_attestation, "attestation_id", "browser scan expansion attestation",
    )
    mapping_digest = _verify_attestation_id(
        mapping, "mapping_attestation_id", "browser scan node/frame mapping",
    )
    return {
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "mapping_coverage": coverage,
        "mapping_digest": mapping_digest,
        "exhaustion_digest": exhaustion_digest,
        "reply_exhaustion_digest": reply_exhaustion_digest,
    }


def build_scan_provenance(
    raw_receipt: dict[str, Any], *, scan_id: str, scope: dict[str, str],
    observed_url: str, observed_at: str, comments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return a provenance envelope only when the complete evidence pair exists."""
    evidence = _evidence_pair(raw_receipt, scope, len(comments))
    if evidence is None:
        return None
    fingerprints = [
        _required_string(row, "raw_fingerprint", "normalized browser comment")
        for row in comments
    ]
    core = {
        "schema_version": SCAN_PROVENANCE_SCHEMA_VERSION,
        "evidence_scope": "scan_receipt_continuity_only",
        "capability_promotion_eligible": False,
        "full_lifecycle_bound": False,
        "test_only": raw_receipt["test_only"],
        "scan_request_id": _required_string(
            raw_receipt, "scan_request_id", "browser scan receipt",
        ),
        "scan_id": scan_id,
        "scan_receipt_digest": _receipt_digest(raw_receipt),
        "scope": dict(scope),
        "observed_url": observed_url,
        "observed_at": observed_at,
        "comment_fingerprints_digest": _json_digest(fingerprints),
        **evidence,
    }
    return {**core, "provenance_digest": _json_digest(core)}


def build_target_observation_provenance(
    raw: dict[str, Any], *, scan_id: str, scope: dict[str, str],
    target: dict[str, str], comment: dict[str, Any],
) -> dict[str, Any]:
    """Bind exactly one visible parent; never mint exhaustion or send authority."""
    evidence = raw["observation_evidence"]
    core = {
        "schema_version": 1,
        "evidence_scope": "target_comment_receipt_continuity_only",
        "observation_scope": "target_comment",
        "whole_post_complete": False,
        "reply_thread_complete": False,
        "capability_promotion_eligible": False,
        "full_lifecycle_bound": False,
        "test_only": False,
        "scan_request_id": raw["scan_request_id"],
        "scan_id": scan_id,
        "scan_receipt_digest": _json_digest(raw),
        "scope": dict(scope),
        "target": dict(target),
        "observed_url": target["comment_permalink"],
        "observed_at": raw["observed_at"],
        "comment_fingerprints_digest": _json_digest([comment["raw_fingerprint"]]),
        "adapter_id": evidence["adapter_id"],
        "adapter_version": evidence["adapter_version"],
        "target_observation_digest": _json_digest(evidence),
        "own_reply_absence_proven": False,
    }
    return {**core, "provenance_digest": _json_digest(core)}


def validate_scan_provenance(value: Any) -> dict[str, Any]:
    """Validate a durable provenance envelope without granting any capability."""
    if not isinstance(value, dict):
        raise ValueError("scan_provenance must be an object")
    version = value.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        raise ValueError("scan_provenance schema_version must be integer 1")
    target_only = value.get("evidence_scope") == "target_comment_receipt_continuity_only"
    if value.get("evidence_scope") not in {
        "scan_receipt_continuity_only", "target_comment_receipt_continuity_only",
    }:
        raise ValueError("scan_provenance evidence_scope is invalid")
    if value.get("capability_promotion_eligible") is not False:
        raise ValueError("scan_provenance cannot claim capability promotion eligibility")
    if value.get("full_lifecycle_bound") is not False:
        raise ValueError("scan_provenance cannot claim full lifecycle mapping")
    if not isinstance(value.get("test_only"), bool):
        raise ValueError("scan_provenance test_only must be explicit boolean")
    strings = [
        "scan_request_id", "scan_id", "observed_url", "observed_at",
        "adapter_id", "adapter_version",
    ]
    digests = ["scan_receipt_digest", "comment_fingerprints_digest", "provenance_digest"]
    if target_only:
        if value.get("observation_scope") != "target_comment":
            raise ValueError("target provenance observation_scope is invalid")
        for key in ("whole_post_complete", "reply_thread_complete", "own_reply_absence_proven"):
            if value.get(key) is not False:
                raise ValueError(f"target provenance cannot claim {key}")
        if any(key in value for key in ("exhaustion_digest", "reply_exhaustion_digest", "mapping_digest")):
            raise ValueError("target provenance cannot contain whole-scan exhaustion or mapping")
        target = value.get("target")
        if not isinstance(target, dict) or set(target) != {"platform_comment_id", "comment_permalink"}:
            raise ValueError("target provenance requires exact native target")
        for key in target:
            _required_string(target, key, "target provenance")
        if value["observed_url"] != target["comment_permalink"]:
            raise ValueError("target provenance observed URL differs from target")
        digests.append("target_observation_digest")
    else:
        if "observation_scope" in value or "target" in value:
            raise ValueError("whole-scan provenance cannot be relabeled target-only")
        strings.append("mapping_coverage")
        digests.extend(("mapping_digest", "exhaustion_digest", "reply_exhaustion_digest"))
    for key in strings:
        _required_string(value, key, "scan_provenance")
    for key in digests:
        _required_digest(value, key, "scan_provenance")
    scope = value.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("scan_provenance scope must be an object")
    for key in ("platform", "account_key", "post_key", "post_permalink"):
        _required_string(scope, key, "scan_provenance scope")
    supplied = value["provenance_digest"]
    core = {key: item for key, item in value.items() if key != "provenance_digest"}
    if supplied != _json_digest(core):
        raise ValueError("scan_provenance digest integrity check failed")
    return json.loads(json.dumps(value, ensure_ascii=False))


def comment_scan_provenance_digest(comment: dict[str, Any]) -> str | None:
    provenance = comment.get("scan_provenance")
    supplied = comment.get(SCAN_PROVENANCE_DIGEST_FIELD)
    if provenance is None and supplied is None:
        return None
    clean = validate_scan_provenance(provenance)
    expected = clean["provenance_digest"]
    if supplied != expected:
        raise ValueError("comment scan provenance digest differs from its envelope")
    if clean.get("observation_scope") == "target_comment":
        if clean["target"] != {
            "platform_comment_id": comment.get("platform_comment_id"),
            "comment_permalink": comment.get("comment_permalink"),
        }:
            raise ValueError("target provenance differs from comment identity")
        if clean["comment_fingerprints_digest"] != _json_digest([comment.get("raw_fingerprint")]):
            raise ValueError("target provenance differs from comment fingerprint")
    return expected


def draft_provenance_digest(
    *, scan_provenance_digest: str, intent_id: str, comment_key: str,
    comment_fingerprint: str, reply_hash: str,
) -> str:
    core = {
        "schema_version": 1,
        "stage": "draft",
        "scan_provenance_digest": scan_provenance_digest,
        "intent_id": intent_id,
        "comment_key": comment_key,
        "comment_fingerprint": comment_fingerprint,
        "reply_hash": reply_hash,
    }
    return _json_digest(core)


def draft_provenance_fields(
    comment: dict[str, Any], *, intent_id: str, comment_key: str,
    comment_fingerprint: str, reply_hash: str,
) -> dict[str, str]:
    scan_digest = comment_scan_provenance_digest(comment)
    if scan_digest is None:
        return {}
    return {
        SCAN_PROVENANCE_DIGEST_FIELD: scan_digest,
        DRAFT_PROVENANCE_DIGEST_FIELD: draft_provenance_digest(
            scan_provenance_digest=scan_digest, intent_id=intent_id,
            comment_key=comment_key, comment_fingerprint=comment_fingerprint,
            reply_hash=reply_hash,
        ),
    }


def validate_draft_provenance_binding(
    draft: dict[str, Any], comment: dict[str, Any],
) -> dict[str, str]:
    expected = draft_provenance_fields(
        comment, intent_id=_required_string(draft, "intent_id", "draft provenance"),
        comment_key=_required_string(draft, "comment_key", "draft provenance"),
        comment_fingerprint=_required_string(
            draft, "comment_fingerprint", "draft provenance",
        ),
        reply_hash=_required_string(draft, "reply_hash", "draft provenance"),
    )
    supplied = {
        key: draft.get(key)
        for key in (SCAN_PROVENANCE_DIGEST_FIELD, DRAFT_PROVENANCE_DIGEST_FIELD)
        if draft.get(key) is not None
    }
    if not expected:
        if supplied:
            raise ValueError("legacy comment cannot acquire browser scan provenance in a draft")
        return {}
    if supplied != expected:
        raise ValueError("draft scan provenance is missing, stale, or drifted")
    return expected


def action_provenance_digest(action: dict[str, Any]) -> str:
    core = {
        "schema_version": 1,
        "stage": "browser_action",
        "scan_provenance_digest": action.get(SCAN_PROVENANCE_DIGEST_FIELD),
        "draft_provenance_digest": action.get(DRAFT_PROVENANCE_DIGEST_FIELD),
        "action_id": action.get("action_id") or action.get("browser_action_id"),
        "intent_id": action.get("intent_id"),
        "session_id": action.get("session_id"),
        "permit_id": action.get("permit_id"),
        "scope": action.get("scope"),
        "comment_fingerprint": action.get("comment_fingerprint"),
        "reply_hash": action.get("reply_hash"),
    }
    return _json_digest(core)


def browser_action_provenance_fields(
    action: dict[str, Any], draft: dict[str, Any], comment: dict[str, Any],
) -> dict[str, str]:
    draft_fields = validate_draft_provenance_binding(draft, comment)
    if not draft_fields:
        raise ValueError(
            "browser-action requires a provenance-bound browser scan observation"
        )
    bound = {**action, **draft_fields}
    return {**draft_fields, ACTION_PROVENANCE_DIGEST_FIELD: action_provenance_digest(bound)}


def validate_send_provenance_binding(
    row: dict[str, Any], draft: dict[str, Any], comment: dict[str, Any],
) -> None:
    expected = browser_action_provenance_fields(row, draft, comment)
    supplied = {
        key: row.get(key)
        for key in (
            SCAN_PROVENANCE_DIGEST_FIELD,
            DRAFT_PROVENANCE_DIGEST_FIELD,
            ACTION_PROVENANCE_DIGEST_FIELD,
        )
    }
    if supplied != expected:
        raise ValueError("send_started browser provenance chain is missing or drifted")
