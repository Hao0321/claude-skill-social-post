#!/usr/bin/env python3
"""Exact native-comment intake and completion, never whole-thread exhaustion."""

from __future__ import annotations

from typing import Any

from comment_browser_common import (
    _canonical_url, _json_digest, _require_live_receipt,
    _require_recent_observation, _require_schema_version,
    _required_boolean, _required_string,
)
from comment_browser_scan_evidence import _normalize_scanned_comment, _scope_from_scan
from comment_browser_scan_request import (
    TARGET_COMPLETION_EVENT_TYPE, normalize_browser_scan_request,
)
from comment_domain import normalize_comment, stable_id
from comment_scan_provenance import (
    SCAN_PROVENANCE_DIGEST_FIELD, build_target_observation_provenance,
    normalize_scan_receipt_consumption, validate_scan_provenance,
)
from social_primitives import parse_time

def _target_observation_context(
    raw: dict[str, Any], policy: dict[str, Any], request: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str], str]:
    """Validate request authorization, exact scope, and observation freshness."""
    if not isinstance(raw, dict):
        raise ValueError("target observation must be a JSON object")
    request = normalize_browser_scan_request(request)
    if request.get("observation_scope") != "target_comment":
        raise ValueError("target observation requires a target-only request")
    if request.get("completion_events"):
        raise ValueError("target observation request already completed")
    expected_fields = {
        "schema_version", "test_only", "observation_scope", "scan_request_id",
        "session_id", "platform", "account_key", "post_key", "post_permalink",
        "observed_url", "observed_at", "authentication_state", "account_verified",
        "post_verified", "target_verified", "comment", "observation_evidence",
    }
    if set(raw) != expected_fields:
        raise ValueError("target observation fields differ from the target-only contract")
    _require_schema_version(raw, "target observation")
    _require_live_receipt(raw, "target observation")
    if raw.get("observation_scope") != "target_comment":
        raise ValueError("target observation scope must be target_comment")
    scope = _scope_from_scan(raw, request)
    if raw.get("authentication_state") != "authenticated":
        raise ValueError("target observation is not authenticated")
    for key in ("account_verified", "post_verified", "target_verified"):
        if not _required_boolean(raw, key):
            raise ValueError(f"target observation {key} was not verified")
    for key in ("scan_request_id", "session_id"):
        if raw.get(key) != request[key]:
            raise ValueError(f"target observation {key} differs from its request")
    if _canonical_url(_required_string(raw, "observed_url")) != request["target"]["comment_permalink"]:
        raise ValueError("target observation URL differs from its native parent")
    observed_at = _require_recent_observation(
        raw, policy, "maximum_browser_scan_age_seconds", 300, "target observation",
    )
    if not (parse_time(request["requested_at"]) <= parse_time(observed_at) <= parse_time(request["expires_at"])):
        raise ValueError("target observation is outside its request time window")
    return request, scope, observed_at


def _normalize_target_comment(
    comment: Any, request: dict[str, Any], scope: dict[str, str], observed_at: str,
) -> dict[str, Any]:
    """Require the complete requested native comment before attaching evidence."""
    comment_fields = {
        "platform_comment_id", "comment_permalink", "observed_parent_post_permalink",
        "author_key", "author_display", "body", "body_complete", "is_own",
        "has_own_reply", "language",
    }
    if not isinstance(comment, dict) or set(comment) not in (
        comment_fields, comment_fields | {"displayed_at"},
    ):
        raise ValueError("target observation requires exactly one complete comment object")
    for key, value in request["target"].items():
        if comment.get(key) != value:
            raise ValueError(f"target observation comment {key} differs from requested target")
    _required_string(comment, "author_key")
    _required_string(comment, "author_display")
    _required_string(comment, "language")
    if comment.get("body_complete") is not True:
        raise ValueError("target observation body must be complete")
    normalized = _normalize_scanned_comment(comment, scope, observed_at)
    return normalized


def _require_target_observation_evidence(
    evidence: Any, comment: dict[str, Any], request: dict[str, Any],
    scope: dict[str, str],
) -> None:
    """Bind two identical full-comment reads to source-owned UI continuity."""
    evidence_fields = {
        "schema_version", "adapter_id", "adapter_version", "document_binding",
        "stable_read_count", "first_read_digest", "second_read_digest",
    }
    if not isinstance(evidence, dict) or set(evidence) != evidence_fields:
        raise ValueError("target observation requires exact stable-read evidence fields")
    _require_schema_version(evidence, "target observation evidence")
    for key in ("adapter_id", "adapter_version"):
        _required_string(evidence, key)
    # The Chrome proxy exposes no physical document epoch. This records only
    # source-owned tab + URL + target continuity; never imply reload detection.
    document = evidence.get("document_binding")
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "kind", "tab_id", "observed_url", "target_digest",
    }:
        raise ValueError("target observation requires exact UI continuity binding fields")
    _require_schema_version(document, "target UI continuity binding")
    if document.get("kind") != "source_owned_ui_continuity":
        raise ValueError("target observation requires source-owned UI continuity only")
    _required_string(document, "tab_id")
    if document.get("observed_url") != request["target"]["comment_permalink"]:
        raise ValueError("target UI continuity URL differs from the exact native target")
    target_digest = _json_digest({
        "account_key": scope["account_key"].removeprefix("@"),
        "comment_permalink": request["target"]["comment_permalink"],
        "author_key": comment["author_key"], "body": comment["body"],
    })
    if document.get("target_digest") != target_digest:
        raise ValueError("target UI continuity digest differs from the observed full comment")
    if type(evidence.get("stable_read_count")) is not int or evidence["stable_read_count"] != 2:
        raise ValueError("target observation requires two stable reads")
    expected_digest = _json_digest(comment)
    if evidence.get("first_read_digest") != expected_digest or evidence.get("second_read_digest") != expected_digest:
        raise ValueError("target observation reads differ from the complete comment")


def normalize_browser_target_observation(
    raw: dict[str, Any], policy: dict[str, Any], request: dict[str, Any],
) -> dict[str, Any]:
    """Normalize one native comment without representing a complete post/thread."""
    request, scope, observed_at = _target_observation_context(raw, policy, request)
    comment = raw.get("comment")
    normalized = _normalize_target_comment(comment, request, scope, observed_at)
    _require_target_observation_evidence(
        raw.get("observation_evidence"), comment, request, scope,
    )
    scan_id = stable_id(
        "browser-target-observation", request["scan_request_id"], scope,
        request["target"], observed_at, normalized["raw_fingerprint"],
    )
    provenance = build_target_observation_provenance(
        raw, scan_id=scan_id, scope=scope, target=request["target"], comment=normalized,
    )
    bound = normalize_comment({
        **normalized, "event_id": None, "scan_provenance": provenance,
        SCAN_PROVENANCE_DIGEST_FIELD: provenance["provenance_digest"],
    })
    bound["observed_parent_post_permalink"] = normalized["observed_parent_post_permalink"]
    return {
        "schema_version": 1, "test_only": False, "observation_scope": "target_comment",
        "scan_request_id": request["scan_request_id"], "scan_id": scan_id,
        "scope": scope, "target": request["target"], "observed_at": observed_at,
        "comment": bound, "scan_provenance": provenance,
        SCAN_PROVENANCE_DIGEST_FIELD: provenance["provenance_digest"],
    }


def normalize_browser_target_completion(
    raw: dict[str, Any], request: dict[str, Any],
) -> dict[str, Any]:
    """Validate durable one-target completion, never a zero-result/exhaustion claim."""
    if not isinstance(raw, dict):
        raise ValueError("target observation completion must be an object")
    _require_schema_version(raw, "target observation completion")
    clean = normalize_browser_scan_request(request)
    if clean.get("observation_scope") != "target_comment":
        raise ValueError("target completion requires a target-only request")
    if raw.get("event_type") != TARGET_COMPLETION_EVENT_TYPE:
        raise ValueError("target observation completion event_type is invalid")
    for key in ("scan_request_id", "session_id", "observation_scope", "target"):
        if raw.get(key) != clean.get(key):
            raise ValueError(f"target completion {key} differs from its request")
    scope = {key: clean[key] for key in ("platform", "account_key", "post_key", "post_permalink")}
    if raw.get("scope") != scope:
        raise ValueError("target completion scope differs from request")
    if raw.get("test_only") is not False or type(raw.get("comment_count")) is not int or raw["comment_count"] != 1:
        raise ValueError("target completion must record exactly one live comment")
    for key in ("whole_post_complete", "reply_thread_complete"):
        if raw.get(key) is not False:
            raise ValueError(f"target completion cannot claim {key}")
    if any(key in raw for key in ("zero_result", "thread_expansion_evidence")):
        raise ValueError("target completion cannot claim zero result or scan exhaustion")
    observed_at = _required_string(raw, "observed_at")
    if not (parse_time(clean["requested_at"]) <= parse_time(observed_at) <= parse_time(clean["expires_at"])):
        raise ValueError("target completion is outside request time window")
    provenance = validate_scan_provenance(raw.get("scan_provenance"))
    if provenance.get("observation_scope") != "target_comment":
        raise ValueError("target completion requires target-only provenance")
    for key in ("scan_request_id", "scan_id", "scope", "target", "observed_at"):
        if provenance.get(key) != raw.get(key):
            raise ValueError(f"target completion provenance {key} differs")
    if raw.get(SCAN_PROVENANCE_DIGEST_FIELD) != provenance["provenance_digest"]:
        raise ValueError("target completion provenance digest differs")
    consumption = normalize_scan_receipt_consumption(raw, clean, required=True)
    if consumption["browser_scan_receipt_digest"] != provenance["scan_receipt_digest"]:
        raise ValueError("target completion receipt digest differs from provenance")
    immutable = {
        "schema_version": 1, "event_type": TARGET_COMPLETION_EVENT_TYPE,
        "scan_request_id": clean["scan_request_id"], "session_id": clean["session_id"],
        "observation_scope": "target_comment", "target": clean["target"],
        "scope": scope, "observed_at": observed_at, "comment_count": 1,
        "test_only": False, "whole_post_complete": False, "reply_thread_complete": False,
        "scan_id": _required_string(raw, "scan_id"), "scan_provenance": provenance,
        SCAN_PROVENANCE_DIGEST_FIELD: provenance["provenance_digest"], **consumption,
    }
    expected_id = stable_id("browser-target-observation-completion", immutable)
    if raw.get("completion_event_id") not in (None, expected_id):
        raise ValueError("target completion id differs from immutable fields")
    return {**immutable, "completion_event_id": expected_id}


def build_browser_target_completion(
    observation: dict[str, Any], request: dict[str, Any], consumption: dict[str, Any],
) -> dict[str, Any]:
    return normalize_browser_target_completion({
        **{key: observation[key] for key in (
            "scan_request_id", "scan_id", "observation_scope", "target", "scope",
            "observed_at", "scan_provenance", SCAN_PROVENANCE_DIGEST_FIELD,
        )},
        "schema_version": 1, "event_type": TARGET_COMPLETION_EVENT_TYPE,
        "session_id": request["session_id"], "test_only": False,
        "comment_count": 1, "whole_post_complete": False, "reply_thread_complete": False,
        **consumption,
    }, request)
