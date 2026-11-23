#!/usr/bin/env python3
"""Observation, approval and send-context checks without reply-state mutation."""

from __future__ import annotations

from typing import Any

from comment_scan_provenance import (
    validate_draft_provenance_binding,
    validate_send_provenance_binding,
)
from social_primitives import parse_time


def _comment_at(
    observations: dict[str, list[dict[str, Any]]], comment_key: str, occurred_at: str,
) -> dict[str, Any] | None:
    moment = parse_time(occurred_at)
    eligible = [
        row for row in observations.get(comment_key, [])
        if parse_time(row["observed_at"]) <= moment
    ]
    return max(eligible, key=lambda row: parse_time(row["observed_at"])) if eligible else None


def _approval_scope(comment: dict[str, Any] | None, comment_key: str) -> dict[str, Any]:
    return {
        "platform": comment.get("platform") if comment else None,
        "account_key": comment.get("account_key") if comment else None,
        "post_key": comment.get("post_key") if comment else None,
        "comment_key": comment_key,
    }


def _validate_comment_guards(
    comment: dict[str, Any] | None, draft: dict[str, Any],
    label: str, errors: list[str],
) -> None:
    if comment is None or draft.get("comment_fingerprint") != comment.get("raw_fingerprint"):
        errors.append(f"{label} draft became stale before approval")
    if comment is None:
        return
    if not comment.get("body_complete"):
        errors.append(f"{label} cannot approve an incomplete comment body")
    if comment.get("is_own"):
        errors.append(f"{label} cannot approve a reply to own comment")
    if comment.get("has_own_reply"):
        errors.append(f"{label} cannot approve a comment that already has own reply")
    try:
        validate_draft_provenance_binding(draft, comment)
    except ValueError as exc:
        errors.append(f"{label} {exc}")


def _validate_approval_context(
    draft: dict[str, Any], row: dict[str, Any], comment: dict[str, Any] | None,
    expected: dict[str, Any], label: str, errors: list[str],
) -> None:
    if row.get("reply_hash") != draft.get("reply_hash"):
        errors.append(f"{label} approval reply_hash differs from draft")
    if row.get("scope") != expected:
        errors.append(f"{label} approval scope does not match visible comment")
    _validate_comment_guards(comment, draft, label, errors)


def _validate_send_expiry(
    row: dict[str, Any], permit: dict[str, Any], label: str, errors: list[str],
) -> None:
    try:
        if parse_time(row["occurred_at"]) > parse_time(permit.get("expires_at", "")):
            errors.append(f"{label} permit expired before send")
    except ValueError:
        pass


def _validate_send_comment(
    row: dict[str, Any], draft: dict[str, Any], comment: dict[str, Any] | None,
    label: str, errors: list[str],
) -> None:
    if comment is None or row.get("comment_fingerprint") != comment.get("raw_fingerprint"):
        errors.append(f"{label} visible comment changed before send")
    if comment is None or draft.get("comment_fingerprint") != comment.get("raw_fingerprint"):
        errors.append(f"{label} approved draft is stale")
    if comment is None:
        return
    try:
        validate_draft_provenance_binding(draft, comment)
        if row.get("browser_action_id"):
            validate_send_provenance_binding(row, draft, comment)
    except ValueError as exc:
        errors.append(f"{label} {exc}")
