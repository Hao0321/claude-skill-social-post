#!/usr/bin/env python3
"""Exact-action, short-lived canary authorization; never capability promotion."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import re
import secrets
from typing import Any

from comment_browser_common import DIGEST_PATTERN, _json_digest
from social_primitives import parse_time


CANARY_EVENT = "browser_canary_lease_issued"
CANARY_ATTEMPT_FIELDS = ("browser_canary_lease_id", "browser_canary_lease_digest")
CANARY_AUTHORIZATION_BASIS = "current_session_user_instruction"
_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_FILES = tuple(sorted((
    "references/comment-policy.json",
    "scripts/comment_assistant.py", "scripts/comment_authorization.py",
    "scripts/comment_browser_cli.py", "scripts/comment_browser_common.py", "scripts/comment_browser_contract.py",
    "scripts/comment_browser_provenance.py", "scripts/comment_browser_send_contract.py",
    "scripts/comment_browser_send_common.py", "scripts/comment_browser_action_contract.py",
    "scripts/comment_browser_preflight_contract.py", "scripts/comment_browser_result_contract.py",
    "scripts/comment_browser_scan_contract.py", "scripts/comment_browser_target_cli.py",
    "scripts/comment_browser_scan_request.py", "scripts/comment_browser_scan_evidence.py",
    "scripts/comment_browser_scan_completion.py", "scripts/comment_browser_target_contract.py",
    "scripts/comment_canary.py", "scripts/comment_canary_cli.py", "scripts/comment_cli_support.py",
    "scripts/comment_domain.py", "scripts/comment_identity.py", "scripts/comment_reply_context_validation.py",
    "scripts/comment_policy.py", "scripts/comment_reply_validation.py",
    "scripts/comment_scan_provenance.py", "scripts/comment_state.py", "scripts/comment_store.py",
    "scripts/social_store.py", "scripts/social_validation.py",
    "scripts/comment_chrome_actuator.mjs", "scripts/comment_chrome_claim_bridge.mjs",
    "scripts/comment_cua_runtime.mjs",
    "scripts/comment_chrome_common.mjs", "scripts/comment_chrome_live_surface.mjs",
    "scripts/comment_chrome_live_common.mjs", "scripts/comment_chrome_facebook_surface.mjs",
    "scripts/comment_chrome_facebook_reader.mjs", "scripts/comment_chrome_threads_surface.mjs",
    "scripts/comment_chrome_facebook_child_reader.mjs",
    "scripts/comment_chrome_threads_reader.mjs",
    "scripts/comment_chrome_threads_canary_surface.mjs", "scripts/comment_chrome_threads_modal_reader.mjs",
    "scripts/comment_chrome_threads_result_reader.mjs",
    "scripts/comment_chrome_instagram_surface.mjs", "scripts/comment_chrome_instagram_reader.mjs",
    "scripts/comment_chrome_instagram_selection.mjs",
    "scripts/comment_chrome_runtime_authority.mjs", "scripts/comment_chrome_send_support.mjs",
    "scripts/comment_chrome_runtime_document.mjs", "scripts/comment_chrome_node_identity.mjs",
    "scripts/comment_chrome_send.mjs", "scripts/comment_chrome_reply_exhaustion.mjs",
)))
_LEASE_KEYS = {
    "schema_version", "lease_id", "lease_digest", "intent_id", "session_id",
    "action_id", "action_digest", "permit_id", "scope", "reply_hash",
    "comment_fingerprint", "post_permalink", "issued_at", "expires_at",
    "maximum_actions", "authorization_basis", "source_digest",
}


def canary_source_digest() -> str:
    """Hash source-owned execution inputs, never a caller-selected source tree."""
    def snapshot() -> list[dict[str, Any]]:
        rows = []
        for relative in _SOURCE_FILES:
            source = _SOURCE_ROOT / relative
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"canary source is missing or indirect: {relative}")
            data = source.read_bytes()
            rows.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        return rows
    first = snapshot()
    if first != snapshot():
        raise ValueError("canary execution source changed during authorization check")
    return _json_digest(first)


def _lease_digest(lease: dict[str, Any]) -> str:
    return _json_digest({key: value for key, value in lease.items() if key != "lease_digest"})


def validate_canary_lease_shape(lease: Any) -> None:
    if not isinstance(lease, dict) or set(lease) != _LEASE_KEYS:
        raise ValueError("canary lease must contain the exact versioned authorization fields")
    if type(lease["schema_version"]) is not int or lease["schema_version"] != 1:
        raise ValueError("canary lease schema_version must be integer 1")
    if type(lease["maximum_actions"]) is not int or lease["maximum_actions"] != 1:
        raise ValueError("canary lease maximum_actions must be integer 1")
    if lease["authorization_basis"] != CANARY_AUTHORIZATION_BASIS:
        raise ValueError("canary lease requires explicit current-session user authorization")
    if not isinstance(lease["lease_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", lease["lease_id"]):
        raise ValueError("canary lease ID must be a random 128-bit identifier")
    for key in ("lease_digest", "action_digest", "reply_hash", "source_digest"):
        if not isinstance(lease[key], str) or not DIGEST_PATTERN.fullmatch(lease[key]):
            raise ValueError(f"canary lease {key} must be a SHA-256 digest")
    for key in ("intent_id", "session_id", "action_id", "permit_id", "comment_fingerprint", "post_permalink"):
        if not isinstance(lease[key], str) or not lease[key].strip():
            raise ValueError(f"canary lease {key} must be a nonempty string")
    scope = lease["scope"]
    if not isinstance(scope, dict) or set(scope) != {"platform", "account_key", "post_key", "comment_key"}:
        raise ValueError("canary lease requires an exact comment scope")
    if scope["platform"] not in {"facebook", "instagram", "threads"} or any(
        not isinstance(value, str) or not value.strip() for value in scope.values()
    ):
        raise ValueError("canary lease scope is invalid")
    issued, expires = parse_time(lease["issued_at"]), parse_time(lease["expires_at"])
    if not 0 < (expires - issued).total_seconds() <= 300:
        raise ValueError("canary lease must last at most 300 seconds")
    if lease["lease_digest"] != _lease_digest(lease):
        raise ValueError("canary lease digest does not bind its authorization")


def validate_canary_action_binding(lease: dict[str, Any], action: dict[str, Any]) -> None:
    validate_canary_lease_shape(lease)
    for key in ("intent_id", "session_id", "action_id", "permit_id", "scope", "reply_hash", "comment_fingerprint", "post_permalink"):
        if lease[key] != action.get(key):
            raise ValueError(f"canary lease {key} differs from the canonical action")
    if lease["action_digest"] != _json_digest(action):
        raise ValueError("canary lease action_digest differs from the canonical action")
    if parse_time(lease["expires_at"]) > parse_time(action["expires_at"]):
        raise ValueError("canary lease outlives its one-shot permit")


def issue_canary_lease(action: dict[str, Any], authorization_basis: str, ttl_seconds: int,
                       *, now: datetime | None = None) -> dict[str, Any]:
    if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 300:
        raise ValueError("canary ttl-seconds must be an integer from 1 to 300")
    if authorization_basis != CANARY_AUTHORIZATION_BASIS:
        raise ValueError("canary issuance requires explicit current-session user authorization")
    # Canonical reply events use second precision; mixed precision would make
    # an immediate same-second send_started appear older than lease issuance.
    issued = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    expires = min(issued + timedelta(seconds=ttl_seconds), parse_time(action["expires_at"]))
    if expires <= issued:
        raise ValueError("canary cannot use an expired approval permit")
    lease = {
        "schema_version": 1, "lease_id": secrets.token_hex(16),
        **{key: action[key] for key in ("intent_id", "session_id", "action_id", "permit_id", "scope", "reply_hash", "comment_fingerprint", "post_permalink")},
        "action_digest": _json_digest(action), "source_digest": canary_source_digest(),
        "issued_at": issued.isoformat(), "expires_at": expires.isoformat(),
        "maximum_actions": 1, "authorization_basis": authorization_basis,
    }
    lease["lease_digest"] = _lease_digest(lease)
    validate_canary_action_binding(lease, action)
    return lease


def apply_canary_lease(current: dict[str, Any], row: dict[str, Any], action: dict[str, Any]) -> None:
    lease = row["canary_lease"]
    validate_canary_action_binding(lease, action)
    if current.get("status") != "approved":
        raise ValueError("canary lease requires an already-approved canonical intent")
    permit = current.get("permit") or {}
    if permit.get("session_id") != lease["session_id"] or parse_time(lease["issued_at"]) < parse_time(permit["occurred_at"]):
        raise ValueError("canary lease does not follow its current-session approval")
    if any(row.get(key) != lease[key] for key in ("intent_id", "session_id")):
        raise ValueError("canary event identity differs from its lease")
    if row.get("comment_key") != lease["scope"]["comment_key"] or row["occurred_at"] != lease["issued_at"]:
        raise ValueError("canary event scope or issuance time differs from its lease")
    old = current.get("canary_lease")
    if old and not old["consumed"] and parse_time(old["lease"]["expires_at"]) > parse_time(lease["issued_at"]):
        raise ValueError("an unexpired canary lease already exists for this intent")
    current.update(canary_lease={"lease": lease, "consumed": False}, last_event=row)


def consume_canary_for_attempt(current: dict[str, Any], attempt: dict[str, Any]) -> None:
    if not any(key in attempt for key in CANARY_ATTEMPT_FIELDS):
        return
    entry = current.get("canary_lease")
    if not entry or entry["consumed"]:
        raise ValueError("canary send has no unused canonical lease")
    lease = entry["lease"]
    _require_attempt_binding(lease, attempt)
    if not parse_time(lease["issued_at"]) <= parse_time(attempt["occurred_at"]) < parse_time(lease["expires_at"]):
        raise ValueError("canary lease expired before durable claim")
    entry["consumed"] = True


def _require_attempt_binding(lease: dict[str, Any], attempt: dict[str, Any]) -> None:
    if attempt.get("browser_canary_lease_id") != lease["lease_id"] or attempt.get("browser_canary_lease_digest") != lease["lease_digest"]:
        raise ValueError("canary send does not bind the canonical lease")
    for action_key, attempt_key in (("action_id", "browser_action_id"), ("action_digest", "browser_action_digest"),
                                   ("intent_id", "intent_id"), ("session_id", "session_id"), ("permit_id", "permit_id"),
                                   ("reply_hash", "reply_hash"), ("scope", "scope"), ("comment_fingerprint", "comment_fingerprint")):
        if attempt.get(attempt_key) != lease[action_key]:
            raise ValueError(f"canary send {attempt_key} differs from its lease")
    if not isinstance(attempt.get("browser_submit_claim_id"), str) or not attempt["browser_submit_claim_id"]:
        raise ValueError("canary send requires a durable browser submit claim")


def require_canary_lease(state: dict[str, Any], lease_id: str, intent_id: str, session_id: str,
                         *, action: dict[str, Any] | None = None, claim_id: str | None = None,
                         now: datetime | None = None) -> dict[str, Any]:
    entry = state.get("canary_lease")
    if not entry or entry["lease"]["lease_id"] != lease_id:
        raise ValueError("canary lease was not issued for the canonical intent")
    lease = entry["lease"]
    if lease["intent_id"] != intent_id or lease["session_id"] != session_id:
        raise ValueError("canary lease intent or current session differs")
    moment = now or datetime.now(timezone.utc)
    if not parse_time(lease["issued_at"]) <= moment < parse_time(lease["expires_at"]):
        raise ValueError("canary lease is expired or not yet active")
    if lease["source_digest"] != canary_source_digest():
        raise ValueError("canary execution source changed after authorization")
    if claim_id is None:
        if state.get("status") != "approved" or entry["consumed"] or action is None:
            raise ValueError("canary requires its approved action and unused lease")
        validate_canary_action_binding(lease, action)
    else:
        attempt = state.get("attempt") or {}
        if state.get("status") != "send_started" or not entry["consumed"] or attempt.get("browser_submit_claim_id") != claim_id:
            raise ValueError("canary dispatch requires its exact consumed durable claim")
        _require_attempt_binding(lease, attempt)
    return lease


def canary_settlement_allowed(state: dict[str, Any]) -> bool:
    """Expiry/source drift cannot strand bookkeeping for an existing attempt."""
    entry = state.get("canary_lease")
    if state.get("status") not in {"send_started", "needs_reconcile"} or not entry or not entry["consumed"]:
        return False
    try:
        _require_attempt_binding(entry["lease"], state.get("attempt") or {})
    except ValueError:
        return False
    return True
