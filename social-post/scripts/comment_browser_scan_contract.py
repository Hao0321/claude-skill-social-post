#!/usr/bin/env python3
"""Compatibility API plus scan/replay orchestration for browser contracts."""

from __future__ import annotations

from typing import Any
import re
from urllib.parse import parse_qsl, urlsplit

from comment_browser_common import (
    PLATFORM_HOSTS, _canonical_url, _require_comment_permalink_for_post,
    _require_platform_url, _require_post_url, _require_recent_observation,
    _json_digest, _require_live_receipt, _require_schema_version, _required_boolean,
    _required_string,
)
from comment_domain import normalize_comment, stable_id
from comment_scan_provenance import (
    SCAN_PROVENANCE_DIGEST_FIELD,
    build_scan_capability_binding,
    build_scan_provenance,
    normalize_scan_capability_metadata,
    normalize_scan_receipt_consumption,
    build_target_observation_provenance,
    validate_scan_provenance,
)
from social_primitives import parse_time


from comment_browser_scan_request import (
    SCAN_COMPLETION_EVENT_TYPE, TARGET_COMPLETION_EVENT_TYPE, _target_scope,
    build_browser_scan_request, normalize_browser_scan_request,
)
from comment_browser_scan_evidence import (
    _comment_scope, _normalize_scanned_comment, _normalize_thread_expansion_evidence,
    _require_complete_thread_expansion, _scope_from_scan, _verify_scan_context,
)
from comment_browser_scan_completion import (
    build_browser_scan_completion, normalize_browser_scan_completion,
)
from comment_browser_target_contract import (
    build_browser_target_completion, normalize_browser_target_completion,
    normalize_browser_target_observation,
)


def replay_browser_scan_requests(
    rows: list[dict[str, Any]], maximum_ttl_seconds: int = 600,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Validate the append-only request ledger and index it by request id."""
    requests: dict[str, dict[str, Any]] = {}
    completion_ids: set[str] = set()
    errors: list[str] = []
    for index, raw in enumerate(rows, 1):
        if isinstance(raw, dict) and raw.get("event_type") in {
            SCAN_COMPLETION_EVENT_TYPE, TARGET_COMPLETION_EVENT_TYPE,
        }:
            request_id = raw.get("scan_request_id")
            request = requests.get(request_id) if isinstance(request_id, str) else None
            if request is None:
                errors.append(
                    f"browser scan request row {index}: completion references "
                    "an unknown or not-yet-recorded scan_request_id"
                )
                continue
            if request["completion_events"]:
                errors.append(
                    f"browser scan request row {index}: one-shot scan request already completed"
                )
                continue
            try:
                completion = (
                    normalize_browser_target_completion(raw, request)
                    if raw["event_type"] == TARGET_COMPLETION_EVENT_TYPE
                    else normalize_browser_scan_completion(raw, request)
                )
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"browser scan request row {index}: {exc}")
                continue
            completion_id = completion["completion_event_id"]
            if completion_id in completion_ids:
                errors.append(
                    f"browser scan request row {index}: duplicate completion_event_id"
                )
                continue
            completion_ids.add(completion_id)
            request["completion_events"].append(completion)
            request["last_completion"] = completion
            request["execution_status"] = "completed"
            continue
        try:
            request = normalize_browser_scan_request(raw)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"browser scan request row {index}: {exc}")
            continue
        duration = (
            parse_time(request["expires_at"]) - parse_time(request["requested_at"])
        ).total_seconds()
        if duration > maximum_ttl_seconds:
            errors.append(
                f"browser scan request row {index}: ttl exceeds {maximum_ttl_seconds} seconds"
            )
            continue
        request_id = request["scan_request_id"]
        if request_id in requests:
            errors.append(f"browser scan request row {index}: duplicate scan_request_id")
            continue
        requests[request_id] = {
            **request,
            "execution_status": "pending",
            "completion_events": [],
            "last_completion": None,
        }
    return requests, errors


def normalize_browser_scan(
    raw: dict[str, Any], policy: dict[str, Any], request: dict[str, Any],
) -> dict[str, Any]:
    """Validate one authenticated live-page scan and return ingest-ready rows."""
    if not isinstance(raw, dict):
        raise ValueError("browser scan must be a JSON object")
    request = normalize_browser_scan_request(request)
    if request.get("observation_scope") == "target_comment":
        raise ValueError("target observation request cannot be consumed as a whole-post scan")
    scope = _scope_from_scan(raw, request)
    _verify_scan_context(raw, scope, request, policy)
    _require_complete_thread_expansion(
        raw.get("thread_expansion_evidence"), "live browser scan",
    )
    comments = raw.get("comments")
    if not isinstance(comments, list) or any(not isinstance(row, dict) for row in comments):
        raise ValueError("browser scan comments must be a list of objects")
    maximum = int(policy.get("maximum_comments_per_scan", 100))
    if len(comments) > maximum:
        raise ValueError(f"browser scan exceeds maximum_comments_per_scan={maximum}")
    observed_at = _required_string(raw, "observed_at")
    normalized = [
        _normalize_scanned_comment(row, scope, observed_at) for row in comments
    ]
    scan_id = stable_id(
        "browser-scan", request["scan_request_id"], scope, observed_at,
        [row["raw_fingerprint"] for row in normalized],
    )
    observed_url = _canonical_url(_required_string(raw, "observed_url"))
    provenance = build_scan_provenance(
        raw, scan_id=scan_id, scope=scope, observed_url=observed_url,
        observed_at=observed_at, comments=normalized,
    )
    if provenance is not None:
        bound_comments = []
        for row in normalized:
            rebound = normalize_comment({
                **row,
                "event_id": None,
                "scan_provenance": provenance,
                SCAN_PROVENANCE_DIGEST_FIELD: provenance["provenance_digest"],
            })
            rebound["observed_parent_post_permalink"] = row[
                "observed_parent_post_permalink"
            ]
            bound_comments.append(rebound)
        normalized = bound_comments
    result = {
        "schema_version": 1,
        "test_only": raw["test_only"],
        "scan_request_id": request["scan_request_id"],
        "scan_id": scan_id,
        "scope": scope,
        "observed_url": observed_url,
        "observed_at": observed_at,
        "comments": normalized,
    }
    if provenance is not None:
        result.update({
            "scan_provenance": provenance,
            SCAN_PROVENANCE_DIGEST_FIELD: provenance["provenance_digest"],
        })
    return result
