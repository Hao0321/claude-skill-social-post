#!/usr/bin/env python3
"""Immutable browser scan requests and exact native-target scope."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from comment_browser_common import (
    PLATFORM_HOSTS, _json_digest, _require_comment_permalink_for_post,
    _require_platform_url, _require_schema_version, _required_string,
)
from comment_domain import stable_id
from comment_scan_provenance import (
    build_scan_capability_binding, normalize_scan_capability_metadata,
)
from social_primitives import parse_time


SCAN_COMPLETION_EVENT_TYPE = "browser_scan_completed"
TARGET_COMPLETION_EVENT_TYPE = "browser_target_observation_completed"

def _target_scope(raw: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    """Keep exact-comment coverage separate from exhaustive post scans."""
    observation_scope = raw.get("observation_scope")
    if observation_scope is None:
        if raw.get("target") is not None:
            raise ValueError("target requires explicit target_comment observation scope")
        return {}
    if observation_scope != "target_comment":
        raise ValueError("unsupported browser observation_scope")
    target = raw.get("target")
    if not isinstance(target, dict) or set(target) != {
        "platform_comment_id", "comment_permalink",
    }:
        raise ValueError("target observation requires exactly a native id and permalink")
    comment_id = _required_string(target, "platform_comment_id")
    permalink = _require_comment_permalink_for_post(
        scope["platform"], _required_string(target, "comment_permalink"),
        scope["post_permalink"], comment_id,
    )
    parsed = urlsplit(permalink)
    if scope["platform"] == "instagram":
        # A child /r/R URL must never be mistaken for the requested parent.
        if not re.fullmatch(r"/p/[A-Za-z0-9_-]+/c/[0-9]+", parsed.path):
            raise ValueError("target Instagram observation requires a native parent comment URL")
        if parsed.path.split("/")[2] != scope["post_key"]:
            raise ValueError("target Instagram post_key differs from native shortcode")
    elif scope["platform"] == "facebook":
        ids = [v for k, v in parse_qsl(parsed.query) if k == "comment_id"]
        if ids != [comment_id] or any(
            k in {"reply_comment_id", "reply_id"} for k, _ in parse_qsl(parsed.query)
        ):
            raise ValueError("target Facebook observation requires one exact comment_id")
    elif scope["platform"] == "threads":
        # The shared URL guard binds the distinct, query-free native target ID;
        # this request must also name the exact root post, not a second target.
        root_id = urlsplit(scope["post_permalink"]).path.rsplit("/", 1)[-1]
        if root_id != scope["post_key"]:
            raise ValueError("target Threads post_key differs from native root post ID")
    else:
        raise ValueError("target observation intake does not support this platform")
    return {
        "observation_scope": "target_comment",
        "target": {"platform_comment_id": comment_id, "comment_permalink": permalink},
    }


def normalize_browser_scan_request(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate one user-created, append-only target request."""
    if not isinstance(raw, dict):
        raise ValueError("browser scan request must be a JSON object")
    _require_schema_version(raw, "browser scan request")
    platform = _required_string(raw, "platform").lower()
    if platform not in PLATFORM_HOSTS:
        raise ValueError(f"unsupported browser platform {platform}")
    scope = {
        "platform": platform,
        "account_key": _required_string(raw, "account_key"),
        "post_key": _required_string(raw, "post_key"),
        "post_permalink": _require_platform_url(
            platform, _required_string(raw, "post_permalink"), "post_permalink",
        ),
    }
    target_scope = _target_scope(raw, scope)
    requested_at = _required_string(raw, "requested_at")
    expires_at = _required_string(raw, "expires_at")
    if parse_time(expires_at) <= parse_time(requested_at):
        raise ValueError("browser scan request expires_at must follow requested_at")
    session_id = _required_string(raw, "session_id")
    expected_id = stable_id(
        "browser-scan-request", session_id, {**scope, **target_scope}, requested_at, expires_at,
    )
    if raw.get("scan_request_id") != expected_id:
        raise ValueError("browser scan request id does not match its immutable fields")
    if raw.get("authorization_basis") != "current_session_user_instruction":
        raise ValueError("browser scan request lacks current-session authorization basis")
    capability_metadata = normalize_scan_capability_metadata(raw)
    result = {
        "schema_version": 1, "scan_request_id": expected_id,
        "session_id": session_id, "requested_at": requested_at,
        "expires_at": expires_at, "authorization_basis": raw["authorization_basis"],
        **scope, **target_scope, **capability_metadata,
    }
    if capability_metadata and _json_digest(build_scan_capability_binding(result)) != (
        capability_metadata["browser_scan_capability_binding_digest"]
    ):
        raise ValueError("browser scan capability binding differs from request fields")
    return result


def build_browser_scan_request(
    *, platform: str, account_key: str, post_key: str, post_permalink: str,
    session_id: str, requested_at: str, expires_at: str,
    observation_scope: str | None = None, target: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create a target request before Chrome is allowed to report a scan."""
    provisional = {
        "schema_version": 1, "platform": platform, "account_key": account_key,
        "post_key": post_key, "post_permalink": post_permalink,
        "session_id": session_id, "requested_at": requested_at,
        "expires_at": expires_at,
        "authorization_basis": "current_session_user_instruction",
    }
    if observation_scope is not None or target is not None:
        provisional.update(observation_scope=observation_scope, target=target)
    normalized_platform = _required_string(provisional, "platform").lower()
    if normalized_platform not in PLATFORM_HOSTS:
        raise ValueError(f"unsupported browser platform {normalized_platform}")
    normalized_scope = {
        "platform": normalized_platform,
        "account_key": _required_string(provisional, "account_key"),
        "post_key": _required_string(provisional, "post_key"),
        "post_permalink": _require_platform_url(
            normalized_platform, _required_string(provisional, "post_permalink"),
            "post_permalink",
        ),
    }
    normalized_session = _required_string(provisional, "session_id")
    normalized_requested_at = _required_string(provisional, "requested_at")
    normalized_expires_at = _required_string(provisional, "expires_at")
    target_scope = _target_scope(provisional, normalized_scope)
    provisional["scan_request_id"] = stable_id(
        "browser-scan-request", normalized_session, {**normalized_scope, **target_scope},
        normalized_requested_at, normalized_expires_at,
    )
    return normalize_browser_scan_request(provisional)
