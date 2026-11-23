#!/usr/bin/env python3
"""Shared scan scope, complete-expansion, and visible-comment validation."""

from __future__ import annotations

from typing import Any

from comment_browser_common import (
    PLATFORM_HOSTS, _require_comment_permalink_for_post, _require_live_receipt,
    _require_platform_url, _require_post_url, _require_recent_observation,
    _require_schema_version, _required_boolean, _required_string,
)
from comment_domain import normalize_comment
from social_primitives import parse_time

def _normalize_thread_expansion_evidence(raw: Any) -> dict[str, Any]:
    """Keep an explicit, honest record of what the actuator expanded."""
    if raw is None:
        return {
            "provided": False,
            "comments_expanded": False,
            "replies_expanded": False,
            "evidence": "thread expansion evidence was not supplied by the browser adapter",
        }
    if not isinstance(raw, dict):
        raise ValueError("thread_expansion_evidence must be an object")
    provided = _required_boolean(raw, "provided")
    comments_expanded = _required_boolean(raw, "comments_expanded")
    replies_expanded = _required_boolean(raw, "replies_expanded")
    evidence = _required_string(raw, "evidence")
    if not provided and (comments_expanded or replies_expanded):
        raise ValueError(
            "thread_expansion_evidence cannot claim expansion when provided is false"
        )
    return {
        "provided": provided,
        "comments_expanded": comments_expanded,
        "replies_expanded": replies_expanded,
        "evidence": evidence,
    }


def _require_complete_thread_expansion(raw: Any, label: str) -> dict[str, Any]:
    """Reject live scan evidence unless comments and replies were both exhausted."""
    expansion = _normalize_thread_expansion_evidence(raw)
    if not (
        expansion["provided"]
        and expansion["comments_expanded"]
        and expansion["replies_expanded"]
    ):
        raise ValueError(
            f"{label} requires verified complete comment and reply expansion"
        )
    return expansion


def _scope_from_scan(
    value: dict[str, Any], request: dict[str, Any],
) -> dict[str, str]:
    platform = _required_string(value, "platform").lower()
    if platform not in PLATFORM_HOSTS:
        raise ValueError(f"unsupported browser platform {platform}")
    expected = {
        key: str(request[key])
        for key in ("platform", "account_key", "post_key", "post_permalink")
    }
    supplied = {
        "platform": platform,
        "account_key": _required_string(value, "account_key"),
        "post_key": _required_string(value, "post_key"),
        "post_permalink": _require_platform_url(
            platform, _required_string(value, "post_permalink"), "post_permalink",
        ),
    }
    if supplied != expected:
        raise ValueError("browser scan scope differs from the stored scan request")
    return expected


def _verify_scan_context(
    value: dict[str, Any], scope: dict[str, str], request: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    _require_schema_version(value, "browser scan")
    _require_live_receipt(value, "browser scan")
    if value.get("authentication_state") != "authenticated":
        raise ValueError("browser scan is not authenticated")
    if not _required_boolean(value, "account_verified"):
        raise ValueError("browser scan account was not verified")
    if not _required_boolean(value, "post_verified"):
        raise ValueError("browser scan post was not verified")
    if value.get("scan_request_id") != request.get("scan_request_id"):
        raise ValueError("browser scan is not bound to the stored scan request")
    if value.get("session_id") != request.get("session_id"):
        raise ValueError("browser scan session differs from the stored scan request")
    observed_url = _required_string(value, "observed_url")
    _require_post_url(
        scope["platform"], observed_url, scope["post_permalink"], "observed_url",
    )
    observed_at = _require_recent_observation(
        value, policy, "maximum_browser_scan_age_seconds", 300, "browser scan",
    )
    observed = parse_time(observed_at)
    if observed < parse_time(request["requested_at"]):
        raise ValueError("browser scan predates its stored scan request")
    if observed > parse_time(request["expires_at"]):
        raise ValueError("browser scan request expired before observation")


def _comment_scope(raw: dict[str, Any], scope: dict[str, str]) -> dict[str, Any]:
    result = dict(raw)
    for key in ("platform", "account_key", "post_key", "post_permalink"):
        supplied = result.get(key)
        if supplied not in (None, "", scope[key]):
            raise ValueError(f"browser comment {key} differs from scan scope")
        result[key] = scope[key]
    return result


def _normalize_scanned_comment(
    raw: dict[str, Any], scope: dict[str, str], observed_at: str,
) -> dict[str, Any]:
    value = _comment_scope(raw, scope)
    supplied_at = value.get("observed_at")
    if supplied_at not in (None, "", observed_at):
        raise ValueError("browser comment observed_at differs from scan envelope")
    value["observed_at"] = observed_at
    value.setdefault("language", "und")
    for key in ("body_complete", "is_own", "has_own_reply"):
        _required_boolean(value, key)
    body = _required_string(value, "body")
    value["body"] = body
    comment_permalink = value.get("comment_permalink")
    if comment_permalink:
        value["comment_permalink"] = _require_comment_permalink_for_post(
            scope["platform"], str(comment_permalink), scope["post_permalink"],
            value.get("platform_comment_id"),
        )
    parent = _required_string(value, "observed_parent_post_permalink")
    parent = _require_post_url(
        scope["platform"], parent, scope["post_permalink"],
        "observed_parent_post_permalink",
    )
    value["observed_parent_post_permalink"] = parent
    normalized = normalize_comment(value)
    normalized["observed_parent_post_permalink"] = parent
    return normalized
