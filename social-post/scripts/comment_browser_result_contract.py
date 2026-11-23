#!/usr/bin/env python3
"""Post-submit result and reconciliation evidence classification."""

from __future__ import annotations

from typing import Any

from comment_browser_common import (
    _require_live_receipt, _require_recent_observation, _require_schema_version,
    _required_boolean, _required_string,
)
from comment_browser_send_common import (
    REINSPECTION_CONTEXT_FLAGS, RESULT_FLAGS, _find_intent,
    _require_non_negative_integer, _require_send_observed_url,
)
from social_primitives import parse_time


def _result_scope_matches(
    value: dict[str, Any], state: dict[str, Any], comment: dict[str, Any],
) -> None:
    attempt = state.get("attempt") or {}
    if value.get("action_id") != attempt.get("browser_action_id"):
        raise ValueError("browser result action_id differs from send attempt")
    if value.get("preflight_id") != attempt.get("browser_preflight_id"):
        raise ValueError("browser result preflight_id differs from send attempt")
    expected = attempt.get("scope")
    if value.get("scope") != expected:
        raise ValueError("browser result scope differs from send attempt")
    if value.get("comment_fingerprint") != comment.get("raw_fingerprint"):
        raise ValueError("browser result comment fingerprint differs from latest observation")
    if value.get("reply_hash") != state.get("draft", {}).get("reply_hash"):
        raise ValueError("browser result reply hash differs from approved draft")
    if value.get("preparation_id") != attempt.get("browser_preparation_id"):
        raise ValueError("browser result preparation_id differs from send attempt")
    if value.get("claim_id") != attempt.get("browser_submit_claim_id"):
        raise ValueError("browser result claim_id differs from send attempt")


def classify_browser_result(
    raw: dict[str, Any], latest_comments: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]], policy: dict[str, Any],
    intent_id: str, session_id: str,
) -> dict[str, Any]:
    """Convert structured post-submit browser evidence to a ledger outcome."""
    if not isinstance(raw, dict):
        raise ValueError("browser result must be a JSON object")
    _require_schema_version(raw, "browser result")
    _require_live_receipt(raw, "browser result")
    comment_key, state = _find_intent(states, intent_id)
    if state.get("status") != "send_started":
        raise ValueError(f"browser result requires send_started, found {state.get('status')}")
    attempt = state.get("attempt") or {}
    if attempt.get("session_id") != session_id:
        raise ValueError("browser result session differs from original send attempt")
    if raw.get("intent_id") != intent_id or raw.get("session_id") != session_id:
        raise ValueError("browser result identity differs from current action")
    comment = latest_comments[comment_key]
    _result_scope_matches(raw, state, comment)
    _require_send_observed_url(comment, _required_string(raw, "observed_url"))
    observed_at = _require_recent_observation(
        raw, policy, "maximum_browser_result_age_seconds", 300, "browser result",
    )
    if parse_time(observed_at) < parse_time(str(attempt.get("occurred_at", ""))):
        raise ValueError("browser result predates send_started")
    attempted = _required_boolean(raw, "submission_attempted")
    possible = _required_boolean(raw, "submission_possible")
    evidence = _required_string(raw, "evidence")
    flags = [_required_boolean(raw, key) for key in RESULT_FLAGS]
    post_submit_total_reply_count = raw.get("post_submit_total_reply_count")
    if (
        not isinstance(post_submit_total_reply_count, int)
        or isinstance(post_submit_total_reply_count, bool)
        or post_submit_total_reply_count < 0
    ):
        raise ValueError(
            "browser result post-submit total reply count must be a non-negative integer"
        )
    baseline_total_reply_count = attempt.get("browser_baseline_total_reply_count")
    if (
        not isinstance(baseline_total_reply_count, int)
        or isinstance(baseline_total_reply_count, bool)
        or baseline_total_reply_count < 0
    ):
        raise ValueError("browser send attempt has no valid baseline total reply count")
    count_supports_new_reply = (
        post_submit_total_reply_count >= baseline_total_reply_count + 1
    )
    if attempted and possible and all(flags) and count_supports_new_reply:
        return {"result": "sent", "evidence": evidence, "observed_at": observed_at}
    exact_reply_visible = flags[RESULT_FLAGS.index("exact_reply_visible")]
    own_author_verified = flags[RESULT_FLAGS.index("own_author_verified")]
    if (
        not attempted and not possible
        and not exact_reply_visible and not own_author_verified
    ):
        return {"result": "failed", "evidence": evidence, "observed_at": observed_at}
    return {
        "result": "unknown",
        "evidence": evidence,
        "observed_at": observed_at,
        "reason": "browser_result_uncertain_after_submission" if attempted else "browser_preflight_state_changed",
    }


def _require_reinspection_evidence_flags(
    raw: dict[str, Any],
) -> tuple[bool, bool, bool]:
    for key in REINSPECTION_CONTEXT_FLAGS:
        if not _required_boolean(raw, key):
            raise ValueError(f"browser reinspection {key} was not verified")
    return tuple(
        _required_boolean(raw, key)
        for key in ("exact_reply_visible", "own_author_verified", "absence_verified")
    )


def _classify_reinspection_reply_evidence(
    raw: dict[str, Any], attempt: dict[str, Any], observed_at: str,
) -> dict[str, Any]:
    exact, own, absent = _require_reinspection_evidence_flags(raw)
    own_author_reply_count = _require_non_negative_integer(
        raw.get("own_author_reply_count"),
        "browser reinspection own_author_reply_count must be a non-negative integer",
    )
    reinspection_total_reply_count = _require_non_negative_integer(
        raw.get("reinspection_total_reply_count"),
        "browser reinspection total reply count must be a non-negative integer",
    )
    baseline_total_reply_count = _require_non_negative_integer(
        attempt.get("browser_baseline_total_reply_count"),
        "browser send attempt has no valid baseline total reply count",
    )
    if own_author_reply_count > reinspection_total_reply_count:
        raise ValueError(
            "browser reinspection own-author reply count exceeds total reply count"
        )
    if exact != own:
        raise ValueError(
            "browser reinspection exact reply and own-author verification must agree"
        )
    if exact and own_author_reply_count < 1:
        raise ValueError(
            "browser reinspection exact own reply requires a positive own-author reply count"
        )
    count_at_or_above_baseline = (
        reinspection_total_reply_count >= baseline_total_reply_count
    )
    count_supports_new_reply = (
        reinspection_total_reply_count >= baseline_total_reply_count + 1
    )
    verified_absence = (
        count_at_or_above_baseline
        and own_author_reply_count == 0 and not exact and not own
    )
    if absent != verified_absence:
        raise ValueError(
            "browser reinspection absence_verified conflicts with own-account reply evidence"
        )
    evidence = _required_string(raw, "evidence")
    base = {"evidence": evidence, "observed_at": observed_at}
    if exact and own and count_supports_new_reply:
        return {**base, "result": "sent"}
    if verified_absence:
        return {**base, "result": "not-sent"}
    return {**base, "result": "unknown", "reason": "browser_reinspection_uncertain"}


def classify_browser_reinspection(
    raw: dict[str, Any], latest_comments: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]], policy: dict[str, Any],
    intent_id: str, session_id: str,
) -> dict[str, Any]:
    """Classify a fresh reinspection without allowing an uncertain duplicate send."""
    if not isinstance(raw, dict):
        raise ValueError("browser reinspection must be a JSON object")
    _require_schema_version(raw, "browser reinspection")
    _require_live_receipt(raw, "browser reinspection")
    comment_key, state = _find_intent(states, intent_id)
    if state.get("status") != "needs_reconcile":
        raise ValueError(
            f"browser reinspection requires needs_reconcile, found {state.get('status')}"
        )
    attempt = state.get("attempt") or {}
    if raw.get("intent_id") != intent_id or raw.get("session_id") != session_id:
        raise ValueError("browser reinspection identity differs from current action")
    if raw.get("attempt_session_id") != attempt.get("session_id"):
        raise ValueError("browser reinspection attempt_session_id differs from send attempt")
    comment = latest_comments[comment_key]
    _result_scope_matches(raw, state, comment)
    _require_send_observed_url(comment, _required_string(raw, "observed_url"))
    observed_at = _require_recent_observation(
        raw, policy, "maximum_browser_result_age_seconds", 300,
        "browser reinspection",
    )
    if parse_time(observed_at) < parse_time(str(attempt.get("occurred_at", ""))):
        raise ValueError("browser reinspection predates send_started")
    return _classify_reinspection_reply_evidence(raw, attempt, observed_at)
