#!/usr/bin/env python3
"""Shared validation helpers for browser scan and send contracts."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from social_primitives import parse_time


PLATFORM_HOSTS = {
    "facebook": {"facebook.com", "www.facebook.com", "m.facebook.com"},
    "instagram": {"instagram.com", "www.instagram.com"},
    "threads": {"threads.com", "www.threads.com", "threads.net", "www.threads.net"},
}
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _required_string(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"browser payload {key} must be a non-empty string")
    return result.strip()


def _required_boolean(value: dict[str, Any], key: str) -> bool:
    result = value.get(key)
    if not isinstance(result, bool):
        raise ValueError(f"browser payload {key} must be boolean")
    return result


def _required_digest(value: dict[str, Any], key: str) -> str:
    result = _required_string(value, key)
    if not DIGEST_PATTERN.fullmatch(result):
        raise ValueError(f"browser payload {key} must be a lowercase SHA-256 digest")
    return result


def _json_digest(value: Any) -> str:
    """Match the actuator's recursively key-sorted JSON SHA-256 digest."""
    payload = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_schema_version(value: dict[str, Any], label: str) -> None:
    version = value.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        raise ValueError(f"{label} schema_version must be integer 1")


def _require_live_receipt(value: dict[str, Any], label: str) -> None:
    test_only = value.get("test_only")
    if not isinstance(test_only, bool):
        raise ValueError(f"{label} test_only must be explicit boolean")
    if test_only:
        raise ValueError(f"{label} test-only evidence cannot enter the live ledger")


def _canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("browser payload URLs must use https")
    if parsed.username or parsed.password:
        raise ValueError("browser payload URLs cannot contain credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("browser payload URL port is invalid") from exc
    if port not in (None, 443):
        raise ValueError("browser payload URLs cannot use non-default ports")
    hostname = parsed.hostname.lower()
    return urlunsplit((
        parsed.scheme, hostname, parsed.path.rstrip("/") or "/",
        parsed.query, "",
    ))


def _require_platform_url(platform: str, value: str, label: str) -> str:
    canonical = _canonical_url(value)
    hostname = (urlsplit(canonical).hostname or "").lower()
    if hostname not in PLATFORM_HOSTS[platform]:
        raise ValueError(f"{label} host does not match {platform}")
    return canonical


def _instagram_url_identity(value: str, *, allow_comment: bool = False) -> dict[str, str | None]:
    canonical = _require_platform_url("instagram", value, "Instagram URL")
    parsed = urlsplit(canonical)
    post = re.fullmatch(
        r"/(?:([A-Za-z0-9._]+)/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", parsed.path,
    )
    comment = re.fullmatch(
        r"/p/([A-Za-z0-9_-]+)/c/([A-Za-z0-9_-]+)", parsed.path,
    ) if allow_comment else None
    if (not post or post[1] in {".", "..", "p", "reel", "reels", "tv", "c"}) and not comment:
        raise ValueError("Instagram URL is not a supported post or native comment permalink")
    keys: set[str] = set()
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = key.lower()
        if normalized in keys or re.fullmatch(
            r"(?:id|comment_?id|reply_?id|media_?id|shortcode)", normalized,
        ):
            raise ValueError("Instagram URL query contains duplicate or ambiguous identifiers")
        keys.add(normalized)
    return {
        "url": canonical, "hostname": parsed.hostname, "query": parsed.query,
        "shortcode": comment[1] if comment else post[2],
        "comment_id": comment[2] if comment else None,
    }


def _require_post_url(
    platform: str, observed: str, expected: str, label: str,
) -> str:
    current = _require_platform_url(platform, observed, label)
    target = _require_platform_url(platform, expected, "post_permalink")
    current_parts = urlsplit(current)
    target_parts = urlsplit(target)
    if current_parts.hostname != target_parts.hostname:
        raise ValueError(f"{label} host differs from approved post_permalink")
    if platform == "instagram":
        current_identity = _instagram_url_identity(observed)
        target_identity = _instagram_url_identity(expected)
        if current_identity["shortcode"] != target_identity["shortcode"]:
            raise ValueError(f"{label} shortcode differs from approved post_permalink")
        if current_identity["query"] != target_identity["query"]:
            raise ValueError(f"{label} query differs from approved post_permalink")
        return current
    if platform == "threads":
        _threads_native_post_id(current_parts.path, current_parts.query, label)
        _threads_native_post_id(target_parts.path, target_parts.query, "post_permalink")
    if current_parts.path != target_parts.path:
        raise ValueError(f"{label} path differs from approved post_permalink")
    expected_query = Counter(parse_qsl(target_parts.query, keep_blank_values=True))
    current_query = Counter(parse_qsl(current_parts.query, keep_blank_values=True))
    if any(current_query[pair] < count for pair, count in expected_query.items()):
        raise ValueError(f"{label} query differs from approved post_permalink")
    return current


def _threads_native_post_id(path: str, query: str, label: str) -> str:
    """Require one query-free native Threads post identity, never a child path."""
    match = re.fullmatch(r"/@[A-Za-z0-9._-]+/post/([A-Za-z0-9_-]+)", path)
    if not match:
        raise ValueError(f"Threads {label} is not a stable native post")
    if query:
        raise ValueError(f"Threads {label} cannot contain a query")
    return match[1]


def _require_comment_permalink_for_post(
    platform: str, observed: str, expected_post: str,
    platform_comment_id: str | None = None,
) -> str:
    """Accept a stable platform comment anchor bound to the approved parent.

    Threads models every reply as its own ``/@author/post/{id}`` permalink, so
    its comment path cannot be nested under the root post path.  Parentage is
    independently and strictly proven by ``observed_parent_post_permalink`` in
    the scan contract; here we validate the Threads reply identity shape and
    trusted host instead of applying the FB nesting rule. Instagram native
    comment anchors may use /p/ while the parent uses /reel/ or /reels/; the
    exact shortcode, host, query and (when present) ledger comment ID remain bound.
    """
    comment = _require_platform_url(platform, observed, "comment_permalink")
    post = _require_platform_url(platform, expected_post, "post_permalink")
    comment_parts = urlsplit(comment)
    post_parts = urlsplit(post)
    if comment_parts.hostname != post_parts.hostname:
        raise ValueError("comment_permalink host differs from approved post")
    if platform == "instagram":
        anchor = _instagram_url_identity(observed, allow_comment=True)
        parent = _instagram_url_identity(expected_post)
        if not anchor["comment_id"]:
            raise ValueError("Instagram comment_permalink requires a native comment ID")
        if anchor["shortcode"] != parent["shortcode"]:
            raise ValueError("Instagram comment_permalink shortcode differs from approved post")
        if anchor["query"] != parent["query"]:
            raise ValueError("Instagram comment_permalink does not retain approved post query")
        if platform_comment_id is not None and anchor["comment_id"] != platform_comment_id:
            raise ValueError("Instagram comment_permalink ID differs from platform_comment_id")
        return comment
    if platform == "threads":
        comment_id = _threads_native_post_id(
            comment_parts.path, comment_parts.query, "comment_permalink",
        )
        post_id = _threads_native_post_id(
            post_parts.path, post_parts.query, "post_permalink",
        )
        if comment_id == post_id:
            raise ValueError("Threads root post cannot be its own comment")
        if comment_id != platform_comment_id:
            raise ValueError("Threads comment_permalink ID differs from platform_comment_id")
        return comment
    post_path = post_parts.path.rstrip("/") or "/"
    if not (
        comment_parts.path == post_path
        or comment_parts.path.startswith(post_path + "/")
    ):
        raise ValueError("comment_permalink does not belong to approved post path")
    expected_query = Counter(parse_qsl(post_parts.query, keep_blank_values=True))
    comment_query = Counter(parse_qsl(comment_parts.query, keep_blank_values=True))
    if any(comment_query[pair] < count for pair, count in expected_query.items()):
        raise ValueError("comment_permalink does not retain approved post query")
    return comment


def _require_recent_observation(
    raw: dict[str, Any], policy: dict[str, Any], policy_key: str,
    default_seconds: int, label: str,
) -> str:
    observed_at = _required_string(raw, "observed_at")
    observed = parse_time(observed_at)
    now = datetime.now(timezone.utc)
    age = (now - observed.astimezone(timezone.utc)).total_seconds()
    maximum = int(policy.get(policy_key, default_seconds))
    if age < -5 or age > maximum:
        raise ValueError(f"{label} must be no older than {maximum} seconds")
    return observed_at
