#!/usr/bin/env python3
"""Reply-event schema and state replay, with backward-compatible public exports."""

from __future__ import annotations

from typing import Any

from comment_authorization import (
    APPROVAL_MODES,
    AUTHORIZATION_BASES,
    GRANT_EVENT_TYPES,
    apply_grant_event,
    consume_grant_action,
    event_time_is_monotonic,
    require_non_empty_strings,
    validate_approval_shape,
    validate_bounded_approval,
    validate_grant_shape,
    validate_scope,
)
from comment_browser_provenance import (
    validate_capability_metadata_shape, validate_consumption_shape,
)
from comment_canary import CANARY_EVENT, apply_canary_lease, consume_canary_for_attempt
from comment_browser_send_contract import _browser_action_from_ledger
from comment_identity import (
    IDENTITY_CONFIDENCE,
    PLATFORMS,
    comment_fingerprint,
    normalize_comment,
    normalized_text,
    reply_hash,
    stable_id,
    validate_comment_events,
)
from comment_reply_context_validation import (
    _approval_scope,
    _comment_at,
    _validate_approval_context,
    _validate_comment_guards,
    _validate_send_comment,
    _validate_send_expiry,
)
from comment_reply_validation import (
    EVENT_TYPES,
    REPLY_EVENT_TYPES,
    RISK_LEVELS,
    validate_reply_event_shape as _validate_reply_event_shape,
)
from comment_scan_provenance import (
    ACTION_PROVENANCE_DIGEST_FIELD,
    DRAFT_PROVENANCE_DIGEST_FIELD,
    SCAN_PROVENANCE_DIGEST_FIELD,
    draft_provenance_fields,
    validate_draft_provenance_binding,
    validate_send_provenance_binding,
)
from social_primitives import parse_time


TERMINAL_STATES = {"sent_verified", "reconciled_sent", "skipped"}


def normalize_reply_event(
    raw: dict[str, Any], latest_comments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    value = dict(raw)
    event_type = str(value.get("event_type", "")).strip()
    occurred_at = str(value.get("occurred_at", "")).strip()
    comment_key = str(value.get("comment_key", "")).strip()
    result = dict(value)
    result.update({
        "schema_version": 1, "event_type": event_type,
        "occurred_at": occurred_at, "comment_key": comment_key,
    })
    if event_type == "session_granted":
        _normalize_grant_event(result, value, occurred_at)
    elif event_type == "drafted":
        _normalize_draft_event(result, value, latest_comments.get(comment_key, {}))
    result["audit_id"] = value.get("audit_id") or stable_id(
        "reply-audit", event_type, result.get("intent_id"), comment_key, occurred_at,
        result.get("reply_hash"), result.get("permit_id"), result.get("grant_id"),
        result.get("browser_receipt_capability_id"),
        result.get("browser_reconcile_capability_id"),
        result.get(SCAN_PROVENANCE_DIGEST_FIELD),
        result.get(DRAFT_PROVENANCE_DIGEST_FIELD),
        result.get(ACTION_PROVENANCE_DIGEST_FIELD),
        *((result.get("canary_lease", {}).get("lease_id"),) if event_type == CANARY_EVENT else ()),
    )
    return result


def _normalize_grant_event(
    result: dict[str, Any], value: dict[str, Any], occurred_at: str,
) -> None:
    scope = value.get("scope") if isinstance(value.get("scope"), dict) else {}
    result["scope"] = {
        "platform": str(scope.get("platform", "")).lower().strip(),
        "account_key": str(scope.get("account_key", "")).strip(),
        "post_key": str(scope.get("post_key", "")).strip(),
    }
    result["grant_id"] = value.get("grant_id") or stable_id(
        "session-grant", value.get("session_id"), result["scope"], occurred_at,
    )


def _normalize_draft_event(
    result: dict[str, Any], value: dict[str, Any], comment: dict[str, Any],
) -> None:
    text = normalized_text(str(value.get("reply_text", "")))
    result["reply_text"] = text
    result["reply_hash"] = value.get("reply_hash") or reply_hash(text)
    result["comment_fingerprint"] = (
        value.get("comment_fingerprint") or comment.get("raw_fingerprint")
    )
    result["intent_id"] = value.get("intent_id") or stable_id(
        "reply-intent", result["comment_key"], result["occurred_at"], result["reply_hash"],
    )
    result.setdefault("policy_version", 1)
    if comment:
        expected = draft_provenance_fields(
            comment, intent_id=result["intent_id"], comment_key=result["comment_key"],
            comment_fingerprint=result["comment_fingerprint"],
            reply_hash=result["reply_hash"],
        )
        for key, expected_value in expected.items():
            result[key] = value.get(key, expected_value)


def _apply_approval(
    current: dict[str, Any], row: dict[str, Any], comment_key: str,
    observations: dict[str, list[dict[str, Any]]],
    grants: dict[str, dict[str, Any]], label: str, errors: list[str],
) -> None:
    initial_error_count = len(errors)
    status = current.get("status")
    if status not in {"drafted", "failed", "reconciled_not_sent", "revoked", "deferred"}:
        errors.append(f"{label} cannot approve from {status}")
        return
    draft = current["draft"]
    comment = _comment_at(observations, comment_key, row["occurred_at"])
    expected = _approval_scope(comment, comment_key)
    _validate_approval_context(draft, row, comment, expected, label, errors)
    grant = None
    if row.get("approval_mode") == "bounded_auto":
        grant = validate_bounded_approval(row, expected, grants, label, errors)
    if grant is not None and len(errors) == initial_error_count:
        consume_grant_action(grant)
    current.update(status="approved", permit=row, last_event=row)


def _apply_send_started(
    current: dict[str, Any], row: dict[str, Any], comment_key: str,
    observations: dict[str, list[dict[str, Any]]], label: str, errors: list[str],
) -> None:
    status = current.get("status")
    if status != "approved":
        errors.append(f"{label} cannot start send from {status}")
        return
    permit = current.get("permit") or {}
    draft = current["draft"]
    if row.get("permit_id") != permit.get("permit_id"):
        errors.append(f"{label} permit_id does not match approval")
    if row.get("session_id") != permit.get("session_id"):
        errors.append(f"{label} session_id does not match approval")
    if row.get("reply_hash") != draft.get("reply_hash"):
        errors.append(f"{label} send hash differs from approved draft")
    _validate_send_expiry(row, permit, label, errors)
    comment = _comment_at(observations, comment_key, row["occurred_at"])
    _validate_send_comment(row, draft, comment, label, errors)
    if row.get("scope") != permit.get("scope"):
        errors.append(f"{label} send scope differs from approval")
    try:
        consume_canary_for_attempt(current, row)
    except ValueError as exc:
        errors.append(f"{label} {exc}")
    current.update(
        status="send_started", last_event=row, attempt=row, permit=None,
        reconcile_capability=None,
    )


def _apply_finish(
    current: dict[str, Any], row: dict[str, Any], event_type: str,
    label: str, errors: list[str],
) -> None:
    status = current.get("status")
    if status != "send_started":
        errors.append(f"{label} cannot record {event_type} from {status}")
    elif row.get("session_id") != (current.get("attempt") or {}).get("session_id"):
        errors.append(f"{label} finish session_id does not match send attempt")
    else:
        current.update(
            status=event_type, last_event=row, permit=None,
            reconcile_capability=row if event_type == "needs_reconcile" else None,
        )


def _apply_reconciliation(
    current: dict[str, Any], row: dict[str, Any], event_type: str,
    label: str, errors: list[str],
) -> None:
    status = current.get("status")
    if status != "needs_reconcile":
        errors.append(f"{label} cannot record {event_type} from {status}")
    elif row.get("attempt_session_id") != (current.get("attempt") or {}).get("session_id"):
        errors.append(f"{label} attempt_session_id does not match send attempt")
    elif row.get("reconciliation_basis") != "browser_reinspection":
        errors.append(f"{label} reconciliation requires browser_reinspection")
    else:
        current.update(
            status=event_type, last_event=row, permit=None,
            reconcile_capability=None,
        )


def _apply_reinspection_observed(
    current: dict[str, Any], row: dict[str, Any], label: str, errors: list[str],
) -> None:
    if current.get("status") != "needs_reconcile":
        errors.append(
            f"{label} cannot record browser_reinspection_observed "
            f"from {current.get('status')}"
        )
    elif row.get("attempt_session_id") != (current.get("attempt") or {}).get("session_id"):
        errors.append(f"{label} reinspection attempt session differs from send attempt")
    else:
        current.update(
            status="needs_reconcile", last_event=row, reconcile_capability=row,
        )


def _apply_reconcile_recovery(
    current: dict[str, Any], row: dict[str, Any], label: str, errors: list[str],
) -> None:
    """Move an authoritative uncertain attempt onto a fresh reconcile-only bearer."""
    status = current.get("status")
    if status not in {"send_started", "needs_reconcile"}:
        errors.append(f"{label} cannot recover reconcile authority from {status}")
        return
    attempt = current.get("attempt") or {}
    attempt_session_id = attempt.get("session_id")
    if row.get("attempt_session_id") != attempt_session_id:
        errors.append(f"{label} recovery attempt session differs from send attempt")
    current_issuer = (
        current.get("reconcile_capability") if status == "needs_reconcile" else attempt
    ) or {}
    previous_session = current_issuer.get(
        "browser_reconcile_authorized_session_id"
    )
    recovery_session = row.get("session_id")
    if recovery_session in {attempt_session_id, previous_session}:
        errors.append(f"{label} recovery requires a fresh current session")
    if row.get("browser_reconcile_authorized_session_id") != recovery_session:
        errors.append(f"{label} recovery capability session binding differs")
    if row.get("reason_code") == "receipt_capability_expired":
        expiry_key = (
            "browser_reconcile_capability_expires_at"
            if status == "needs_reconcile"
            else "browser_finish_capability_expires_at"
        )
        try:
            if parse_time(str(current_issuer.get(expiry_key, ""))) > parse_time(
                str(row.get("occurred_at", ""))
            ):
                errors.append(f"{label} recovery capability has not expired")
        except ValueError:
            errors.append(f"{label} recovery has no authoritative capability expiry")
    if errors and any(error.startswith(label) for error in errors):
        return
    current.update(
        status="needs_reconcile", last_event=row, permit=None,
        reconcile_capability=row,
    )


def _apply_disposition(
    current: dict[str, Any], row: dict[str, Any], event_type: str,
    label: str, errors: list[str],
) -> None:
    status = current.get("status")
    allowed = {"drafted", "failed", "reconciled_not_sent", "revoked", "deferred"}
    if status not in allowed:
        errors.append(f"{label} cannot record {event_type} from {status}")
    else:
        current.update(status=event_type, last_event=row)


def _apply_reply_transition(
    current: dict[str, Any], row: dict[str, Any], comment_key: str,
    observations: dict[str, list[dict[str, Any]]], grants: dict[str, dict[str, Any]],
    label: str, errors: list[str], warnings: list[str],
) -> None:
    event_type = row.get("event_type")
    if event_type == CANARY_EVENT:
        try:
            comment = _comment_at(observations, comment_key, row["occurred_at"])
            if comment is None:
                raise ValueError("canary lease has no canonical comment observation")
            action = _browser_action_from_ledger(comment, current, row["intent_id"], row["session_id"])
            apply_canary_lease(current, row, action)
        except ValueError as exc:
            errors.append(f"{label} {exc}")
    elif event_type == "approved":
        _apply_approval(current, row, comment_key, observations, grants, label, errors)
    elif event_type == "send_started":
        _apply_send_started(current, row, comment_key, observations, label, errors)
    elif event_type in {"sent_verified", "needs_reconcile", "failed"}:
        _apply_finish(current, row, str(event_type), label, errors)
    elif event_type in {"reconciled_sent", "reconciled_not_sent"}:
        _apply_reconciliation(current, row, str(event_type), label, errors)
    elif event_type == "browser_reinspection_observed":
        _apply_reinspection_observed(current, row, label, errors)
    elif event_type == "reconcile_recovery_issued":
        _apply_reconcile_recovery(current, row, label, errors)
    elif event_type in {"deferred", "skipped"}:
        _apply_disposition(current, row, str(event_type), label, errors)
    elif event_type == "revoked":
        if current.get("status") != "approved":
            errors.append(f"{label} cannot revoke from {current.get('status')}")
        else:
            current.update(status="revoked", last_event=row, permit=None)
    else:
        warnings.append(f"{label} was not applied because its event type is invalid")


def _observations_by_comment(
    comment_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    observations: dict[str, list[dict[str, Any]]] = {}
    for comment in comment_rows:
        observations.setdefault(str(comment.get("comment_key")), []).append(comment)
    return observations


def _record_audit_id(
    row: dict[str, Any], label: str, seen: set[str], errors: list[str],
) -> None:
    audit_id = row.get("audit_id")
    if isinstance(audit_id, str):
        if audit_id in seen:
            errors.append(f"{label} duplicate audit_id {audit_id}")
        seen.add(audit_id)


def _permit_is_new(
    row: dict[str, Any], label: str, seen: set[str], errors: list[str],
) -> bool:
    permit_id = row.get("permit_id")
    if permit_id in seen:
        errors.append(f"{label} duplicate permit_id {permit_id}")
        return False
    seen.add(str(permit_id))
    return True


def _intent_is_valid(
    intent_id: Any, comment_key: Any, intents: dict[str, str],
    label: str, errors: list[str],
) -> bool:
    if isinstance(intent_id, str) and intent_id in intents:
        if intents[intent_id] != comment_key:
            errors.append(f"{label} intent_id is reused across comments")
            return False
    if isinstance(intent_id, str):
        intents[intent_id] = str(comment_key)
    return True


def _apply_draft(
    states: dict[str, dict[str, Any]], comment_key: str,
    intent_id: Any, row: dict[str, Any], label: str, errors: list[str],
) -> None:
    current = states.get(comment_key)
    if current:
        blocked = TERMINAL_STATES | {"approved", "send_started", "needs_reconcile"}
        if current.get("status") in blocked:
            errors.append(f"{label} cannot draft from {current.get('status')}")
            return
        if not event_time_is_monotonic(current, row, label, errors):
            return
    states[comment_key] = {
        "status": "drafted", "intent_id": intent_id, "draft": row,
        "last_event": row, "permit": None, "attempt": None,
        "reconcile_capability": None,
        "canary_lease": None,
    }


def _apply_reply_row(
    row: dict[str, Any], label: str, observations: dict[str, list[dict[str, Any]]],
    states: dict[str, dict[str, Any]], grants: dict[str, dict[str, Any]],
    intents: dict[str, str], errors: list[str], warnings: list[str],
) -> None:
    comment_key = row.get("comment_key")
    intent_id = row.get("intent_id")
    if comment_key not in observations:
        errors.append(f"{label} references unknown comment_key {comment_key}")
        return
    if not _intent_is_valid(intent_id, comment_key, intents, label, errors):
        return
    key = str(comment_key)
    if row.get("event_type") == "drafted":
        _apply_draft(states, key, intent_id, row, label, errors)
        return
    current = states.get(key)
    if current is None or current.get("intent_id") != intent_id:
        errors.append(f"{label} has no matching active draft")
        return
    if not event_time_is_monotonic(current, row, label, errors):
        return
    _apply_reply_transition(
        current, row, key, observations, grants, label, errors, warnings,
    )


def replay_reply_events(
    reply_rows: list[dict[str, Any]], comment_rows: list[dict[str, Any]],
    errors: list[str], warnings: list[str], maximum_actions_limit: int | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    seen_audits: set[str] = set()
    seen_permits: set[str] = set()
    seen_canary_leases: set[str] = set()
    observations = _observations_by_comment(comment_rows)
    states: dict[str, dict[str, Any]] = {}
    grants: dict[str, dict[str, Any]] = {}
    intents: dict[str, str] = {}
    for index, row in enumerate(reply_rows, start=1):
        label = f"reply_events.jsonl:{index}"
        errors_before_shape = len(errors)
        _validate_reply_event_shape(row, label, errors)
        shape_invalid = len(errors) > errors_before_shape
        _record_audit_id(row, label, seen_audits, errors)
        if shape_invalid:
            continue
        if row.get("event_type") == CANARY_EVENT:
            lease_id = row["canary_lease"]["lease_id"]
            if lease_id in seen_canary_leases:
                errors.append(f"{label} duplicate canary lease ID")
                continue
            seen_canary_leases.add(lease_id)
        if row.get("event_type") in GRANT_EVENT_TYPES:
            apply_grant_event(grants, row, label, errors, maximum_actions_limit)
            continue
        if row.get("event_type") == "approved":
            if not _permit_is_new(row, label, seen_permits, errors):
                continue
        _apply_reply_row(
            row, label, observations, states, grants, intents, errors, warnings,
        )
    return states, grants
