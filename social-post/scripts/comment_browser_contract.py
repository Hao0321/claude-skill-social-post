#!/usr/bin/env python3
"""Compatibility facade for the modular browser comment contracts."""

from __future__ import annotations

from comment_browser_common import (
    PLATFORM_HOSTS, _canonical_url, _require_comment_permalink_for_post,
    _require_platform_url, _require_post_url, _require_recent_observation,
    _require_schema_version, _required_boolean, _required_string,
)
from comment_browser_scan_contract import (
    SCAN_COMPLETION_EVENT_TYPE, _comment_scope, _normalize_scanned_comment,
    _normalize_thread_expansion_evidence, _scope_from_scan, _verify_scan_context,
    build_browser_scan_completion, build_browser_scan_request,
    normalize_browser_scan, normalize_browser_scan_completion,
    normalize_browser_scan_request, replay_browser_scan_requests,
)
from comment_browser_send_contract import (
    PREFLIGHT_FLAGS, REINSPECTION_CONTEXT_FLAGS, RESULT_FLAGS, _find_intent,
    _require_action_binding, _require_no_scope_reconciliation,
    _result_scope_matches, _scope_key, build_browser_action,
    classify_browser_reinspection, classify_browser_result,
    validate_browser_preflight,
)
from comment_domain import reply_hash, stable_id
from social_primitives import parse_time


__all__ = [
    "PLATFORM_HOSTS",
    "SCAN_COMPLETION_EVENT_TYPE",
    "RESULT_FLAGS",
    "REINSPECTION_CONTEXT_FLAGS",
    "PREFLIGHT_FLAGS",
    "normalize_browser_scan_request",
    "build_browser_scan_request",
    "replay_browser_scan_requests",
    "normalize_browser_scan_completion",
    "build_browser_scan_completion",
    "normalize_browser_scan",
    "build_browser_action",
    "validate_browser_preflight",
    "classify_browser_result",
    "classify_browser_reinspection",
    "reply_hash",
    "stable_id",
    "parse_time",
]
