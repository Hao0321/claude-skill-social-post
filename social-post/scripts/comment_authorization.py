#!/usr/bin/env python3
"""Session grants, one-shot permits, and shared authorization validators."""

from __future__ import annotations

from typing import Any

from comment_identity import PLATFORMS
from social_primitives import parse_time


APPROVAL_MODES = {"batch_confirm", "bounded_auto"}
AUTHORIZATION_BASES = {
    "batch_confirm_user_confirmation", "current_session_user_instruction",
}
GRANT_EVENT_TYPES = {"session_granted", "session_revoked"}


def validate_scope(
    scope: Any, label: str, errors: list[str], *, include_comment: bool,
) -> None:
    expected_keys = {"platform", "account_key", "post_key"}
    if include_comment:
        expected_keys.add("comment_key")
    if not isinstance(scope, dict):
        errors.append(f"{label} scope must be an object")
        return
    if set(scope) != expected_keys:
        errors.append(f"{label} scope must contain exactly {sorted(expected_keys)}")
    if scope.get("platform") not in PLATFORMS:
        errors.append(f"{label} scope platform must be one of {sorted(PLATFORMS)}")
    for key in expected_keys - {"platform"}:
        if not isinstance(scope.get(key), str) or not scope.get(key).strip():
            errors.append(f"{label} scope {key} must be a non-empty string")


def require_non_empty_strings(
    row: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str],
) -> None:
    for key in keys:
        if not isinstance(row.get(key), str) or not row.get(key).strip():
            errors.append(f"{label} {key} must be a non-empty string")


def validate_expiry(row: dict[str, Any], label: str, errors: list[str]) -> None:
    try:
        expires = parse_time(row.get("expires_at", ""))
        if expires <= parse_time(row.get("occurred_at", "")):
            errors.append(f"{label} expires_at must be after occurred_at")
    except ValueError:
        errors.append(f"{label} expires_at must be ISO 8601 with UTC offset")


def event_time_is_monotonic(
    current: dict[str, Any], row: dict[str, Any], label: str, errors: list[str],
) -> bool:
    previous = current.get("last_event") or current.get("event")
    if not isinstance(previous, dict):
        return True
    try:
        if parse_time(row["occurred_at"]) < parse_time(previous["occurred_at"]):
            errors.append(f"{label} event time is out of order (moves backwards)")
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def validate_grant_shape(
    row: dict[str, Any], event_type: str, label: str, errors: list[str],
) -> None:
    if event_type == "session_revoked":
        require_non_empty_strings(
            row, ("grant_id", "session_id", "reason_code"), label, errors,
        )
        return
    required = (
        "grant_id", "session_id", "scope", "expires_at", "maximum_actions",
        "authorization_basis",
    )
    for key in required:
        if key not in row:
            errors.append(f"{label} session_granted event missing {key}")
    require_non_empty_strings(row, ("grant_id", "session_id"), label, errors)
    validate_scope(row.get("scope"), label, errors, include_comment=False)
    if row.get("authorization_basis") != "current_session_user_instruction":
        errors.append(
            f"{label} session grant authorization_basis must be "
            "current_session_user_instruction"
        )
    maximum = row.get("maximum_actions")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1:
        errors.append(f"{label} maximum_actions must be a positive integer")
    validate_expiry(row, label, errors)


def validate_approval_shape(
    row: dict[str, Any], label: str, errors: list[str],
) -> None:
    required = (
        "permit_id", "session_id", "expires_at", "reply_hash", "scope",
        "approval_mode", "authorization_basis",
    )
    for key in required:
        if key not in row:
            errors.append(f"{label} approved event missing {key}")
    require_non_empty_strings(row, ("permit_id", "session_id"), label, errors)
    validate_scope(row.get("scope"), label, errors, include_comment=True)
    mode = row.get("approval_mode")
    if mode not in APPROVAL_MODES:
        errors.append(f"{label} approval_mode must be one of {sorted(APPROVAL_MODES)}")
    expected_basis = {
        "batch_confirm": "batch_confirm_user_confirmation",
        "bounded_auto": "current_session_user_instruction",
    }.get(mode)
    if row.get("authorization_basis") != expected_basis:
        errors.append(f"{label} authorization_basis does not match approval_mode")
    _validate_approval_grant_reference(row, mode, label, errors)
    validate_expiry(row, label, errors)
    if row.get("one_shot") is not True:
        errors.append(f"{label} approved permit must be one_shot")


def _validate_approval_grant_reference(
    row: dict[str, Any], mode: Any, label: str, errors: list[str],
) -> None:
    grant_id = row.get("grant_id")
    if mode == "bounded_auto":
        if not isinstance(grant_id, str) or not grant_id.strip():
            errors.append(f"{label} bounded_auto approval requires grant_id")
    elif grant_id not in (None, ""):
        errors.append(f"{label} batch_confirm approval must not reference grant_id")


def apply_grant_event(
    grants: dict[str, dict[str, Any]], row: dict[str, Any], label: str,
    errors: list[str], maximum_actions_limit: int | None,
) -> None:
    grant_id = row.get("grant_id")
    if not isinstance(grant_id, str) or not grant_id.strip():
        return
    if row.get("event_type") == "session_granted":
        _grant_session(grants, grant_id, row, label, errors, maximum_actions_limit)
        return
    _revoke_session(grants, grant_id, row, label, errors)


def _grant_session(
    grants: dict[str, dict[str, Any]], grant_id: str, row: dict[str, Any],
    label: str, errors: list[str], maximum_actions_limit: int | None,
) -> None:
    if grant_id in grants:
        errors.append(f"{label} duplicate grant_id {grant_id}")
        return
    maximum = row.get("maximum_actions")
    if isinstance(maximum_actions_limit, int) and isinstance(maximum, int):
        if maximum > maximum_actions_limit:
            errors.append(f"{label} maximum_actions exceeds policy limit")
            return
    grants[grant_id] = {
        "status": "active", "event": row, "session_id": row.get("session_id"),
        "scope": row.get("scope"), "expires_at": row.get("expires_at"),
        "maximum_actions": maximum, "used_actions": 0,
        "authorization_basis": row.get("authorization_basis"), "last_event": row,
    }


def _revoke_session(
    grants: dict[str, dict[str, Any]], grant_id: str, row: dict[str, Any],
    label: str, errors: list[str],
) -> None:
    grant = grants.get(grant_id)
    if grant is None:
        errors.append(f"{label} revokes unknown grant_id {grant_id}")
        return
    if not event_time_is_monotonic(grant, row, label, errors):
        return
    if grant.get("status") != "active":
        errors.append(f"{label} grant_id {grant_id} is already revoked")
        return
    if row.get("session_id") != grant.get("session_id"):
        errors.append(f"{label} revoked grant session_id does not match grant")
        return
    grant.update(status="revoked", event=row, last_event=row)


def validate_bounded_approval(
    row: dict[str, Any], expected_scope: dict[str, Any],
    grants: dict[str, dict[str, Any]], label: str, errors: list[str],
) -> dict[str, Any] | None:
    grant_id = row.get("grant_id")
    grant = grants.get(grant_id) if isinstance(grant_id, str) else None
    if grant is None:
        errors.append(f"{label} bounded_auto approval references unknown grant_id")
        return None
    grant_scope = {key: expected_scope[key] for key in ("platform", "account_key", "post_key")}
    if grant.get("status") != "active":
        errors.append(f"{label} bounded_auto grant is not active")
    if row.get("session_id") != grant.get("session_id"):
        errors.append(f"{label} bounded_auto grant session_id does not match approval")
    if grant.get("scope") != grant_scope:
        errors.append(f"{label} bounded_auto grant scope does not match approval")
    _validate_grant_window(row, grant, label, errors)
    maximum = grant.get("maximum_actions")
    used = grant.get("used_actions")
    if isinstance(maximum, int) and not isinstance(maximum, bool):
        if isinstance(used, int) and used >= maximum:
            errors.append(f"{label} bounded_auto grant action cap exceeded")
    return grant


def _validate_grant_window(
    row: dict[str, Any], grant: dict[str, Any], label: str, errors: list[str],
) -> None:
    try:
        approval_time = parse_time(row["occurred_at"])
        grant_expires = parse_time(grant.get("expires_at", ""))
        permit_expires = parse_time(row.get("expires_at", ""))
        grant_started = parse_time((grant.get("event") or {}).get("occurred_at", ""))
    except ValueError:
        return
    if approval_time < grant_started:
        errors.append(f"{label} bounded_auto approval predates its grant")
    if approval_time > grant_expires:
        errors.append(f"{label} bounded_auto grant expired before approval")
    if permit_expires > grant_expires:
        errors.append(f"{label} bounded_auto permit outlives its grant")


def consume_grant_action(grant: dict[str, Any]) -> None:
    grant["used_actions"] = int(grant.get("used_actions")) + 1
