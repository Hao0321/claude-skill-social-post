#!/usr/bin/env python3
"""Whole-post scan completion and provenance binding; no target-only promotion."""

from __future__ import annotations

from typing import Any

from comment_browser_common import (
    _require_schema_version, _required_boolean, _required_string,
)
from comment_browser_scan_evidence import _require_complete_thread_expansion
from comment_browser_scan_request import (
    SCAN_COMPLETION_EVENT_TYPE, normalize_browser_scan_request,
)
from comment_domain import stable_id
from comment_scan_provenance import (
    SCAN_PROVENANCE_DIGEST_FIELD, normalize_scan_capability_metadata,
    normalize_scan_receipt_consumption, validate_scan_provenance,
)
from social_primitives import parse_time

def _scan_completion_provenance(
    raw: dict[str, Any], clean_request: dict[str, Any],
    expected_scope: dict[str, Any], observed_at: str,
) -> dict[str, Any]:
    """Keep optional provenance tied to the same request, scope, time, and scan."""
    raw_provenance = raw.get("scan_provenance")
    raw_provenance_digest = raw.get(SCAN_PROVENANCE_DIGEST_FIELD)
    if raw_provenance is not None or raw_provenance_digest is not None:
        provenance = validate_scan_provenance(raw_provenance)
        if raw_provenance_digest != provenance["provenance_digest"]:
            raise ValueError("browser scan completion provenance digest differs")
        if provenance.get("scan_request_id") != clean_request["scan_request_id"]:
            raise ValueError("browser scan completion provenance request differs")
        if provenance.get("scope") != expected_scope:
            raise ValueError("browser scan completion provenance scope differs")
        if provenance.get("observed_at") != observed_at:
            raise ValueError("browser scan completion provenance time differs")
        scan_id = _required_string(raw, "scan_id")
        if provenance.get("scan_id") != scan_id:
            raise ValueError("browser scan completion provenance scan_id differs")
        return {
            "scan_id": scan_id,
            "scan_provenance": provenance,
            SCAN_PROVENANCE_DIGEST_FIELD: raw_provenance_digest,
        }
    return {}


def normalize_browser_scan_completion(
    raw: dict[str, Any], request: dict[str, Any],
) -> dict[str, Any]:
    """Validate one append-only record proving that a scan request executed."""
    if not isinstance(raw, dict):
        raise ValueError("browser scan completion must be a JSON object")
    _require_schema_version(raw, "browser scan completion")
    if raw.get("event_type") != SCAN_COMPLETION_EVENT_TYPE:
        raise ValueError("browser scan completion has the wrong event_type")
    clean_request = normalize_browser_scan_request(request)
    if clean_request.get("observation_scope") == "target_comment":
        raise ValueError("target observation cannot receive whole-post scan completion")
    if raw.get("scan_request_id") != clean_request["scan_request_id"]:
        raise ValueError("browser scan completion differs from its scan request")
    if raw.get("session_id") != clean_request["session_id"]:
        raise ValueError("browser scan completion session differs from its scan request")
    expected_scope = {
        key: clean_request[key]
        for key in ("platform", "account_key", "post_key", "post_permalink")
    }
    if raw.get("scope") != expected_scope:
        raise ValueError("browser scan completion scope differs from its scan request")
    observed_at = _required_string(raw, "observed_at")
    observed = parse_time(observed_at)
    if observed < parse_time(clean_request["requested_at"]):
        raise ValueError("browser scan completion predates its scan request")
    if observed > parse_time(clean_request["expires_at"]):
        raise ValueError("browser scan completion follows scan request expiry")
    comment_count = raw.get("comment_count")
    if not isinstance(comment_count, int) or isinstance(comment_count, bool) or comment_count < 0:
        raise ValueError("browser scan completion comment_count must be a non-negative integer")
    zero_result = _required_boolean(raw, "zero_result")
    if zero_result != (comment_count == 0):
        raise ValueError("browser scan completion zero_result disagrees with comment_count")
    expansion = _require_complete_thread_expansion(
        raw.get("thread_expansion_evidence"), "browser scan completion",
    )
    test_only = raw.get("test_only")
    if not isinstance(test_only, bool):
        raise ValueError("browser scan completion test_only must be explicit boolean")
    consumption = normalize_scan_receipt_consumption(
        raw, clean_request,
        required=(test_only is False and bool(normalize_scan_capability_metadata(clean_request))),
    )
    immutable = {
        "schema_version": 1,
        "event_type": SCAN_COMPLETION_EVENT_TYPE,
        "scan_request_id": clean_request["scan_request_id"],
        "session_id": clean_request["session_id"],
        "scope": expected_scope,
        "observed_at": observed_at,
        "comment_count": comment_count,
        "zero_result": zero_result,
        "test_only": test_only,
        "thread_expansion_evidence": expansion,
        **consumption,
    }
    immutable.update(_scan_completion_provenance(
        raw, clean_request, expected_scope, observed_at,
    ))
    expected_id = stable_id("browser-scan-completion", immutable)
    supplied_id = raw.get("completion_event_id")
    if supplied_id not in (None, expected_id):
        raise ValueError("browser scan completion id does not match its immutable fields")
    return {**immutable, "completion_event_id": expected_id}


def build_browser_scan_completion(
    scan: dict[str, Any], request: dict[str, Any], raw_evidence: Any,
    receipt_consumption: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the durable completion event for an accepted browser scan."""
    provisional = {
        "schema_version": 1,
        "event_type": SCAN_COMPLETION_EVENT_TYPE,
        "scan_request_id": scan["scan_request_id"],
        "session_id": request["session_id"],
        "scope": scan["scope"],
        "observed_at": scan["observed_at"],
        "comment_count": len(scan["comments"]),
        "zero_result": not scan["comments"],
        "test_only": scan["test_only"],
        "thread_expansion_evidence": raw_evidence,
        **(receipt_consumption or {}),
    }
    if scan.get("scan_provenance") is not None:
        provisional.update({
            "scan_id": scan["scan_id"],
            "scan_provenance": scan["scan_provenance"],
            SCAN_PROVENANCE_DIGEST_FIELD: scan[SCAN_PROVENANCE_DIGEST_FIELD],
        })
    return normalize_browser_scan_completion(provisional, request)
