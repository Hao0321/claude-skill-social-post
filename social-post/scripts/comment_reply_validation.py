#!/usr/bin/env python3
"""Schema validation for normalized reply-ledger events."""

from __future__ import annotations

from typing import Any

from comment_authorization import (
    GRANT_EVENT_TYPES,
    require_non_empty_strings,
    validate_approval_shape,
    validate_grant_shape,
    validate_scope,
)
from comment_browser_provenance import (
    validate_capability_metadata_shape,
    validate_consumption_shape,
)
from comment_browser_common import DIGEST_PATTERN
from comment_canary import CANARY_ATTEMPT_FIELDS, CANARY_EVENT, validate_canary_lease_shape
from comment_identity import reply_hash
from comment_scan_provenance import (
    ACTION_PROVENANCE_DIGEST_FIELD,
    DRAFT_PROVENANCE_DIGEST_FIELD,
    SCAN_PROVENANCE_DIGEST_FIELD,
)
from social_primitives import parse_time


RISK_LEVELS = {"low", "medium", "high"}
REPLY_EVENT_TYPES = {
    "drafted", "approved", "send_started", "sent_verified", "needs_reconcile",
    "reconciled_sent", "reconciled_not_sent", "browser_reinspection_observed",
    "reconcile_recovery_issued", "failed", "deferred", "skipped", "revoked", CANARY_EVENT,
}
EVENT_TYPES = REPLY_EVENT_TYPES | GRANT_EVENT_TYPES


def _validate_draft_shape(row: dict[str, Any], label: str, errors: list[str]) -> None:
    required = (
        "reply_text", "reply_hash", "classification", "risk", "confidence",
        "comment_fingerprint", "language", "policy_version",
    )
    for key in required:
        if key not in row:
            errors.append(f"{label} drafted event missing {key}")
    text = row.get("reply_text")
    if not isinstance(text, str) or not text:
        errors.append(f"{label} reply_text must be non-empty")
    elif "\n" in text or "\r" in text:
        errors.append(f"{label} reply_text must be a single line")
    elif row.get("reply_hash") != reply_hash(text):
        errors.append(f"{label} reply_hash does not match reply_text")
    if row.get("risk") not in RISK_LEVELS:
        errors.append(f"{label} risk must be one of {sorted(RISK_LEVELS)}")
    confidence = row.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        errors.append(f"{label} confidence must be from 0..1")
    elif not 0 <= confidence <= 1:
        errors.append(f"{label} confidence must be from 0..1")
    if not isinstance(row.get("language"), str) or not row.get("language", "").strip():
        errors.append(f"{label} language must be a non-empty string")
    version = row.get("policy_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append(f"{label} policy_version must be a positive integer")
    provenance = (
        row.get(SCAN_PROVENANCE_DIGEST_FIELD),
        row.get(DRAFT_PROVENANCE_DIGEST_FIELD),
    )
    if any(value is not None for value in provenance):
        if not all(
            isinstance(value, str) and DIGEST_PATTERN.fullmatch(value)
            for value in provenance
        ):
            errors.append(f"{label} drafted provenance digests must be complete SHA-256 values")


def _validate_other_outcome(
    row: dict[str, Any], event_type: str, label: str, errors: list[str],
) -> None:
    if event_type == "failed":
        require_non_empty_strings(row, ("session_id",), label, errors)
        if row.get("submission_possible") is not False:
            errors.append(f"{label} failed is allowed only when submission_possible is false")
        if row.get("browser_receipt_id"):
            validate_consumption_shape(row, "browser-finish", label, errors)
    elif event_type == "needs_reconcile":
        require_non_empty_strings(row, ("session_id", "reason_code"), label, errors)
        if row.get("browser_receipt_id"):
            validate_consumption_shape(row, "browser-finish", label, errors)
            validate_capability_metadata_shape(row, "browser-reconcile", label, errors)
    elif event_type in {"deferred", "skipped", "revoked"}:
        require_non_empty_strings(row, ("reason_code",), label, errors)


def _validate_outcome_shape(
    row: dict[str, Any], event_type: str, label: str, errors: list[str],
) -> None:
    if event_type == "send_started":
        required = ("permit_id", "session_id", "reply_hash", "comment_fingerprint", "scope")
        for key in required:
            if key not in row:
                errors.append(f"{label} send_started event missing {key}")
        validate_scope(row.get("scope"), label, errors, include_comment=True)
        browser_binding = (
            "browser_action_id", "browser_preflight_id", "browser_preparation_id",
            "browser_action_digest", "browser_plan_digest", "browser_submit_claim_id",
        )
        if any(row.get(key) for key in browser_binding):
            require_non_empty_strings(row, browser_binding, label, errors)
            provenance_binding = (
                SCAN_PROVENANCE_DIGEST_FIELD,
                DRAFT_PROVENANCE_DIGEST_FIELD,
                ACTION_PROVENANCE_DIGEST_FIELD,
            )
            require_non_empty_strings(row, provenance_binding, label, errors)
            for key in provenance_binding:
                value = row.get(key)
                if not isinstance(value, str) or not DIGEST_PATTERN.fullmatch(value):
                    errors.append(f"{label} {key} must be a lowercase SHA-256 digest")
            baseline_total = row.get("browser_baseline_total_reply_count")
            if (
                not isinstance(baseline_total, int)
                or isinstance(baseline_total, bool)
                or baseline_total < 0
            ):
                errors.append(
                    f"{label} browser_baseline_total_reply_count must be a non-negative integer"
                )
            validate_capability_metadata_shape(row, "browser-finish", label, errors)
        elif any(row.get(key) for key in (
            SCAN_PROVENANCE_DIGEST_FIELD,
            DRAFT_PROVENANCE_DIGEST_FIELD,
            ACTION_PROVENANCE_DIGEST_FIELD,
        )):
            errors.append(f"{label} browser provenance cannot exist without a browser action")
    elif event_type == "sent_verified":
        require_non_empty_strings(row, ("session_id", "browser_evidence"), label, errors)
        if row.get("browser_receipt_id"):
            validate_consumption_shape(row, "browser-finish", label, errors)
    elif event_type in {"reconciled_sent", "reconciled_not_sent"}:
        require_non_empty_strings(
            row, ("session_id", "attempt_session_id", "browser_evidence"), label, errors,
        )
        if row.get("reconciliation_basis") != "browser_reinspection":
            errors.append(f"{label} reconciliation_basis must be browser_reinspection")
        if row.get("browser_receipt_id"):
            validate_consumption_shape(row, "browser-reconcile", label, errors)
    elif event_type == "browser_reinspection_observed":
        require_non_empty_strings(
            row,
            ("session_id", "attempt_session_id", "browser_evidence", "reason_code"),
            label, errors,
        )
        if row.get("reconciliation_basis") != "browser_reinspection":
            errors.append(f"{label} reinspection basis must be browser_reinspection")
        validate_consumption_shape(row, "browser-reconcile", label, errors)
        validate_capability_metadata_shape(row, "browser-reconcile", label, errors)
    elif event_type == "reconcile_recovery_issued":
        require_non_empty_strings(
            row, ("session_id", "attempt_session_id", "reason_code"), label, errors,
        )
        if row.get("reconciliation_basis") != "browser_recovery":
            errors.append(f"{label} recovery basis must be browser_recovery")
        if row.get("reason_code") not in {
            "browser_process_restarted", "receipt_capability_expired",
        }:
            errors.append(f"{label} recovery reason_code is invalid")
        validate_capability_metadata_shape(row, "browser-reconcile", label, errors)
        if row.get("browser_reconcile_authorized_session_id") != row.get("session_id"):
            errors.append(f"{label} recovery capability is not bound to its session")
    else:
        _validate_other_outcome(row, event_type, label, errors)


def validate_reply_event_shape(
    row: dict[str, Any], label: str, errors: list[str],
) -> None:
    event_type = row.get("event_type")
    if any(key in row for key in CANARY_ATTEMPT_FIELDS):
        if event_type != "send_started" or not all(row.get(key) for key in CANARY_ATTEMPT_FIELDS):
            errors.append(f"{label} canary consumption belongs only to a complete send_started binding")
    if "canary_lease" in row and event_type != CANARY_EVENT:
        errors.append(f"{label} canary lease belongs only to its authorization event")
    require_non_empty_strings(row, ("audit_id", "event_type", "occurred_at"), label, errors)
    if event_type not in GRANT_EVENT_TYPES:
        require_non_empty_strings(row, ("intent_id", "comment_key"), label, errors)
    if event_type not in EVENT_TYPES:
        errors.append(f"{label} invalid event_type {event_type}")
    try:
        parse_time(row.get("occurred_at", ""))
    except ValueError:
        errors.append(f"{label} occurred_at must be ISO 8601 with UTC offset")
    if event_type in GRANT_EVENT_TYPES:
        validate_grant_shape(row, str(event_type), label, errors)
    elif event_type == "drafted":
        _validate_draft_shape(row, label, errors)
    elif event_type == CANARY_EVENT:
        require_non_empty_strings(row, ("session_id",), label, errors)
        try:
            validate_canary_lease_shape(row.get("canary_lease"))
        except (ValueError, TypeError) as exc:
            errors.append(f"{label} {exc}")
    elif event_type == "approved":
        validate_approval_shape(row, label, errors)
    else:
        _validate_outcome_shape(row, str(event_type), label, errors)
