#!/usr/bin/env python3
"""One-shot bearer capabilities for live browser result receipts.

The nonce is returned only to the shell-free Node bridge.  Canonical ledgers retain
only a salted/domain-separated hash, an authoritative binding digest, expiry, and
the digest of the receipt consumed by the capability.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets
from typing import Any

from comment_browser_common import _json_digest
from social_primitives import parse_time


PROVENANCE_VERSION = 1
OPERATIONS = {"browser-finish", "browser-reconcile"}
CAPABILITY_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
NONCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _operation_prefix(operation: str) -> str:
    if operation == "browser-finish":
        return "browser_finish"
    if operation == "browser-reconcile":
        return "browser_reconcile"
    raise ValueError(f"unsupported browser receipt operation {operation}")


def build_receipt_binding(operation: str, attempt: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the capability scope solely from authoritative send_started data."""
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported browser receipt operation {operation}")
    required = {
        "action_id": attempt.get("browser_action_id"),
        "intent_id": attempt.get("intent_id"),
        "authorized_session_id": attempt.get("session_id"),
        "permit_id": attempt.get("permit_id"),
        "reply_hash": attempt.get("reply_hash"),
        "claim_id": attempt.get("browser_submit_claim_id"),
        "preflight_id": attempt.get("browser_preflight_id"),
        "preparation_id": attempt.get("browser_preparation_id"),
        "scope": attempt.get("scope"),
    }
    for key, value in required.items():
        if key == "scope":
            if not isinstance(value, dict) or not value:
                raise ValueError("browser receipt capability has no authoritative scope")
        elif not isinstance(value, str) or not value:
            raise ValueError(f"browser receipt capability has no authoritative {key}")
    return {
        "provenance_version": PROVENANCE_VERSION,
        "operation": operation,
        **required,
    }


def build_reconcile_receipt_binding(
    attempt: dict[str, Any], authorized_session_id: str,
) -> dict[str, Any]:
    """Bind a reconcile bearer to one existing send attempt and one fresh session."""
    if not isinstance(authorized_session_id, str) or not authorized_session_id.strip():
        raise ValueError("browser-reconcile requires an authorized current session")
    return {
        **build_receipt_binding("browser-reconcile", attempt),
        "authorized_reconcile_session_id": authorized_session_id.strip(),
    }


def _secret_hash(binding_digest: str, nonce: str) -> str:
    material = (
        f"social-post-browser-receipt-capability-v{PROVENANCE_VERSION}\0"
        f"{binding_digest}\0{nonce}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def issue_receipt_capability(
    operation: str, binding: dict[str, Any], issued_at: str, ttl_seconds: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (bearer, ledger metadata); never place bearer nonce in metadata."""
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported browser receipt operation {operation}")
    if ttl_seconds < 1:
        raise ValueError("browser receipt capability TTL must be positive")
    issued = parse_time(issued_at).astimezone(timezone.utc)
    expires_at = (issued + timedelta(seconds=ttl_seconds)).isoformat()
    binding_digest = _json_digest(binding)
    nonce = secrets.token_urlsafe(32)
    capability_id = secrets.token_hex(16)
    bearer = {
        "schema_version": PROVENANCE_VERSION,
        "operation": operation,
        "capability_id": capability_id,
        "nonce": nonce,
    }
    prefix = _operation_prefix(operation)
    metadata = {
        f"{prefix}_capability_version": PROVENANCE_VERSION,
        f"{prefix}_capability_id": capability_id,
        f"{prefix}_capability_hash": _secret_hash(binding_digest, nonce),
        f"{prefix}_capability_binding_digest": binding_digest,
        f"{prefix}_capability_issued_at": issued.isoformat(),
        f"{prefix}_capability_expires_at": expires_at,
    }
    return bearer, metadata


def issue_reconcile_receipt_capability(
    attempt: dict[str, Any], authorized_session_id: str,
    issued_at: str, ttl_seconds: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Issue a reconcile-only bearer whose session binding is ledger-visible."""
    session_id = authorized_session_id.strip()
    bearer, metadata = issue_receipt_capability(
        "browser-reconcile",
        build_reconcile_receipt_binding(attempt, session_id),
        issued_at,
        ttl_seconds,
    )
    metadata["browser_reconcile_authorized_session_id"] = session_id
    return bearer, metadata


def reconcile_receipt_binding_from_issuer(
    attempt: dict[str, Any], issuer: dict[str, Any], requested_session_id: str,
) -> dict[str, Any]:
    """Rebuild a reconcile binding from the authoritative capability issuer."""
    authorized = issuer.get("browser_reconcile_authorized_session_id")
    if authorized is None:
        # Backward compatibility for ledgers created before session-bound reconcile
        # capabilities existed. New issuances always take the branch below.
        return build_receipt_binding("browser-reconcile", attempt)
    if not isinstance(authorized, str) or not authorized:
        raise ValueError("browser-reconcile authorized session metadata is invalid")
    if requested_session_id != authorized:
        raise ValueError("browser-reconcile session differs from its issued capability")
    return build_reconcile_receipt_binding(attempt, authorized)


def _required_capability_metadata(
    issuer: dict[str, Any], operation: str,
) -> tuple[str, str, str, str]:
    prefix = _operation_prefix(operation)
    if issuer.get(f"{prefix}_capability_version") != PROVENANCE_VERSION:
        raise ValueError(f"{operation} has no versioned receipt capability")
    capability_id = issuer.get(f"{prefix}_capability_id")
    secret_hash = issuer.get(f"{prefix}_capability_hash")
    binding_digest = issuer.get(f"{prefix}_capability_binding_digest")
    expires_at = issuer.get(f"{prefix}_capability_expires_at")
    if not isinstance(capability_id, str) or not CAPABILITY_ID_PATTERN.fullmatch(capability_id):
        raise ValueError(f"{operation} capability id is invalid")
    if not isinstance(secret_hash, str) or not DIGEST_PATTERN.fullmatch(secret_hash):
        raise ValueError(f"{operation} capability hash is invalid")
    if not isinstance(binding_digest, str) or not DIGEST_PATTERN.fullmatch(binding_digest):
        raise ValueError(f"{operation} capability binding digest is invalid")
    if not isinstance(expires_at, str):
        raise ValueError(f"{operation} capability expiry is invalid")
    return capability_id, secret_hash, binding_digest, expires_at


def consume_receipt_envelope(
    envelope: Any, operation: str, binding: dict[str, Any], issuer: dict[str, Any],
    *, now: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate a one-shot provenance envelope without mutating any ledger state."""
    if not isinstance(envelope, dict):
        raise ValueError(f"{operation} input must be a provenance envelope object")
    if set(envelope) != {"provenance", "receipt"}:
        raise ValueError(f"{operation} requires exactly provenance and receipt fields")
    provenance = envelope.get("provenance")
    receipt = envelope.get("receipt")
    if not isinstance(provenance, dict):
        raise ValueError(f"{operation} provenance must be an object")
    if not isinstance(receipt, dict):
        raise ValueError(f"{operation} receipt must be an object")
    if provenance.get("schema_version") != PROVENANCE_VERSION:
        raise ValueError(f"{operation} provenance schema_version must be integer 1")
    if provenance.get("operation") != operation:
        raise ValueError(f"{operation} provenance operation differs from the command")
    capability_id = provenance.get("capability_id")
    nonce = provenance.get("nonce")
    if not isinstance(capability_id, str) or not CAPABILITY_ID_PATTERN.fullmatch(capability_id):
        raise ValueError(f"{operation} provenance capability_id is invalid")
    if not isinstance(nonce, str) or not NONCE_PATTERN.fullmatch(nonce):
        raise ValueError(f"{operation} provenance nonce is invalid")
    expected_id, expected_hash, expected_binding_digest, expires_at = (
        _required_capability_metadata(issuer, operation)
    )
    binding_digest = _json_digest(binding)
    if not hmac.compare_digest(binding_digest, expected_binding_digest):
        raise ValueError(f"{operation} capability binding differs from the send attempt")
    if not hmac.compare_digest(capability_id, expected_id):
        raise ValueError(f"{operation} capability id was not issued for this attempt")
    candidate_hash = _secret_hash(binding_digest, nonce)
    if not hmac.compare_digest(candidate_hash, expected_hash):
        raise ValueError(f"{operation} capability nonce is invalid")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if current >= parse_time(expires_at).astimezone(timezone.utc):
        raise ValueError(f"{operation} receipt capability expired")
    receipt_digest = _json_digest(receipt)
    consumed = {
        "browser_receipt_provenance_version": PROVENANCE_VERSION,
        "browser_receipt_operation": operation,
        "browser_receipt_capability_id": capability_id,
        "browser_receipt_binding_digest": binding_digest,
        "browser_receipt_digest": receipt_digest,
    }
    return receipt, consumed


def validate_capability_metadata_shape(
    row: dict[str, Any], operation: str, label: str, errors: list[str],
) -> None:
    """Ledger schema validation for issued capability metadata (never a nonce)."""
    prefix = _operation_prefix(operation)
    if row.get(f"{prefix}_capability_version") != PROVENANCE_VERSION:
        errors.append(f"{label} {operation} capability version must be 1")
    patterns = {
        f"{prefix}_capability_id": CAPABILITY_ID_PATTERN,
        f"{prefix}_capability_hash": DIGEST_PATTERN,
        f"{prefix}_capability_binding_digest": DIGEST_PATTERN,
    }
    for key, pattern in patterns.items():
        value = row.get(key)
        if not isinstance(value, str) or not pattern.fullmatch(value):
            errors.append(f"{label} {key} is invalid")
    for key in (f"{prefix}_capability_issued_at", f"{prefix}_capability_expires_at"):
        try:
            parse_time(str(row.get(key, "")))
        except ValueError:
            errors.append(f"{label} {key} must be ISO 8601 with UTC offset")
    if operation == "browser-reconcile":
        authorized = row.get("browser_reconcile_authorized_session_id")
        if authorized is not None and (
            not isinstance(authorized, str) or not authorized.strip()
        ):
            errors.append(
                f"{label} browser_reconcile_authorized_session_id must be non-empty"
            )


def validate_consumption_shape(
    row: dict[str, Any], operation: str, label: str, errors: list[str],
) -> None:
    if row.get("browser_receipt_provenance_version") != PROVENANCE_VERSION:
        errors.append(f"{label} browser receipt provenance version must be 1")
    if row.get("browser_receipt_operation") != operation:
        errors.append(f"{label} browser receipt operation must be {operation}")
    patterns = {
        "browser_receipt_capability_id": CAPABILITY_ID_PATTERN,
        "browser_receipt_binding_digest": DIGEST_PATTERN,
        "browser_receipt_digest": DIGEST_PATTERN,
    }
    for key, pattern in patterns.items():
        value = row.get(key)
        if not isinstance(value, str) or not pattern.fullmatch(value):
            errors.append(f"{label} {key} is invalid")
