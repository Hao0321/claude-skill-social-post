#!/usr/bin/env python3
"""Canonical identity and observation ledger rules for visible comments."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import datetime
from typing import Any

from comment_scan_provenance import (
    SCAN_PROVENANCE_DIGEST_FIELD,
    comment_scan_provenance_digest,
    validate_scan_provenance,
)
from social_primitives import parse_time


PLATFORMS = {"facebook", "instagram", "threads"}
IDENTITY_CONFIDENCE = {"strong", "weak"}


def stable_id(prefix: str, *values: Any) -> str:
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"


def normalized_text(value: str) -> str:
    return unicodedata.normalize("NFC", value).strip()


def reply_hash(value: str) -> str:
    return hashlib.sha256(normalized_text(value).encode("utf-8")).hexdigest()


def _strict_boolean(value: Any, default: bool = False) -> Any:
    """Default missing booleans without treating truthy strings as booleans."""
    return default if value is None else value


def _normalized_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def canonical_comment_key(value: dict[str, Any]) -> str:
    platform_comment_id = _normalized_optional_string(value.get("platform_comment_id"))
    comment_permalink = _normalized_optional_string(value.get("comment_permalink"))
    if platform_comment_id:
        return (
            f"{value.get('platform')}:{value.get('account_key')}:"
            f"{value.get('post_key')}:{platform_comment_id}"
        )
    if comment_permalink:
        return stable_id("comment-permalink", comment_permalink)
    return stable_id(
        "ui-comment", value.get("platform"), value.get("account_key"), value.get("post_key"),
        value.get("parent_comment_key"), value.get("author_key"), value.get("displayed_at"),
        normalized_text(str(value.get("body", ""))),
    )


def comment_fingerprint(value: dict[str, Any]) -> str:
    fields = (
        value.get("platform"), value.get("account_key"), value.get("post_key"),
        value.get("platform_comment_id"), value.get("parent_comment_key"),
        value.get("author_key"), normalized_text(str(value.get("body", ""))),
        value.get("body_complete"), value.get("is_own"), value.get("has_own_reply"),
    )
    return stable_id("fingerprint", *fields)


def _normalized_identity(value: dict[str, Any], body: str) -> dict[str, Any]:
    platform_comment_id = _normalized_optional_string(value.get("platform_comment_id"))
    comment_permalink = _normalized_optional_string(value.get("comment_permalink"))
    return {
        "platform": str(value.get("platform", "")).lower().strip(),
        "account_key": str(value.get("account_key", "")).strip(),
        "post_key": str(value.get("post_key", "")).strip(),
        "platform_comment_id": platform_comment_id,
        "comment_permalink": comment_permalink,
        "parent_comment_key": _normalized_optional_string(value.get("parent_comment_key")),
        "author_key": _normalized_optional_string(value.get("author_key")),
        "displayed_at": value.get("displayed_at"),
        "body": body,
        "identity_confidence": "strong" if platform_comment_id or comment_permalink else "weak",
    }


def _comment_event(value: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    result = {
        "schema_version": 1,
        "event_id": value.get("event_id"),
        **identity,
        "post_permalink": str(value.get("post_permalink", "")).strip(),
        "comment_key": canonical_comment_key(identity),
        "author_display": value.get("author_display"),
        "language": value.get("language"),
        "observed_at": str(value.get("observed_at", "")).strip(),
        "body_complete": _strict_boolean(value.get("body_complete")),
        "is_own": _strict_boolean(value.get("is_own")),
        "has_own_reply": _strict_boolean(value.get("has_own_reply")),
        "source": "chrome_ui",
    }
    if value.get("scan_provenance") is not None or value.get(
        SCAN_PROVENANCE_DIGEST_FIELD
    ) is not None:
        provenance = validate_scan_provenance(value.get("scan_provenance"))
        supplied = value.get(SCAN_PROVENANCE_DIGEST_FIELD)
        if supplied != provenance["provenance_digest"]:
            raise ValueError("comment scan provenance digest differs from its envelope")
        result["scan_provenance"] = provenance
        result[SCAN_PROVENANCE_DIGEST_FIELD] = supplied
    return result


def normalize_comment(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize one visible browser observation without inventing completeness."""
    value = dict(raw)
    body = normalized_text(str(value.get("body", value.get("text", ""))))
    result = _comment_event(value, _normalized_identity(value, body))
    result["raw_fingerprint"] = value.get("raw_fingerprint") or comment_fingerprint(result)
    event_parts = [
        result["comment_key"], result["raw_fingerprint"], result["observed_at"],
    ]
    if result.get(SCAN_PROVENANCE_DIGEST_FIELD):
        event_parts.append(result[SCAN_PROVENANCE_DIGEST_FIELD])
    result["event_id"] = result["event_id"] or stable_id("comment-event", *event_parts)
    return result


def _validate_scan_provenance_shape(
    row: dict[str, Any], label: str, errors: list[str],
) -> None:
    if row.get("scan_provenance") is None and row.get(
        SCAN_PROVENANCE_DIGEST_FIELD
    ) is None:
        return
    try:
        digest = comment_scan_provenance_digest(row)
    except ValueError as exc:
        errors.append(f"{label} {exc}")
        return
    provenance = row["scan_provenance"]
    expected_scope = {
        key: row.get(key)
        for key in ("platform", "account_key", "post_key", "post_permalink")
    }
    if provenance.get("scope") != expected_scope:
        errors.append(f"{label} scan provenance scope differs from comment")
    if provenance.get("observed_at") != row.get("observed_at"):
        errors.append(f"{label} scan provenance observed_at differs from comment")
    expected_event_id = stable_id(
        "comment-event", row.get("comment_key"), row.get("raw_fingerprint"),
        row.get("observed_at"), digest,
    )
    if row.get("event_id") != expected_event_id:
        errors.append(f"{label} event_id does not bind its scan provenance")


def _validate_identity(row: dict[str, Any], label: str, errors: list[str]) -> None:
    anchored = bool(
        _normalized_optional_string(row.get("platform_comment_id"))
        or _normalized_optional_string(row.get("comment_permalink"))
    )
    expected_confidence = "strong" if anchored else "weak"
    if row.get("identity_confidence") not in IDENTITY_CONFIDENCE:
        errors.append(f"{label} identity_confidence must be strong or weak")
    if row.get("identity_confidence") != expected_confidence:
        errors.append(
            f"{label} identity_confidence must be derived from platform_comment_id "
            "or comment_permalink"
        )
    if row.get("comment_key") != canonical_comment_key(row):
        errors.append(f"{label} comment_key does not match its canonical identity anchor")


def _validate_comment_shape(row: dict[str, Any], label: str, errors: list[str]) -> None:
    required = (
        "event_id", "platform", "account_key", "post_key", "post_permalink", "comment_key",
        "body", "observed_at", "identity_confidence", "body_complete", "is_own",
        "has_own_reply", "raw_fingerprint", "source",
    )
    for key in required:
        if key not in row:
            errors.append(f"{label} missing {key}")
    if row.get("platform") not in PLATFORMS:
        errors.append(f"{label} platform must be one of {sorted(PLATFORMS)}")
    string_keys = ("account_key", "post_key", "post_permalink", "comment_key", "body", "raw_fingerprint")
    for key in string_keys:
        if not isinstance(row.get(key), str) or not row.get(key).strip():
            errors.append(f"{label} {key} must be a non-empty string")
    if isinstance(row.get("post_permalink"), str) and not row["post_permalink"].startswith("https://"):
        errors.append(f"{label} post_permalink must use https")
    permalink = row.get("comment_permalink")
    if permalink is not None and (not isinstance(permalink, str) or not permalink.startswith("https://")):
        errors.append(f"{label} comment_permalink must use https when supplied")
    for key in ("body_complete", "is_own", "has_own_reply"):
        if not isinstance(row.get(key), bool):
            errors.append(f"{label} {key} must be boolean")
    if row.get("source") != "chrome_ui":
        errors.append(f"{label} source must be chrome_ui")
    _validate_identity(row, label, errors)
    _validate_scan_provenance_shape(row, label, errors)


def _record_event_id(
    row: dict[str, Any], label: str, seen_events: set[str], errors: list[str],
) -> None:
    event_id = row.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        errors.append(f"{label} event_id must be a non-empty string")
    elif event_id in seen_events:
        errors.append(f"{label} duplicate event_id {event_id}")
    else:
        seen_events.add(event_id)


def _record_latest(
    row: dict[str, Any], observed: datetime, latest: dict[str, dict[str, Any]],
    latest_time: dict[str, datetime], label: str, errors: list[str],
) -> None:
    comment_key = row.get("comment_key")
    if not isinstance(comment_key, str) or not comment_key:
        return
    previous_time = latest_time.get(comment_key)
    if previous_time is None or observed > previous_time:
        latest[comment_key] = row
        latest_time[comment_key] = observed
    elif observed == previous_time:
        previous = latest[comment_key]
        if (
            previous.get("raw_fingerprint") != row.get("raw_fingerprint")
            or previous.get(SCAN_PROVENANCE_DIGEST_FIELD)
            != row.get(SCAN_PROVENANCE_DIGEST_FIELD)
        ):
            errors.append(f"{label} conflicting observations share the same timestamp")


def validate_comment_events(
    rows: list[dict[str, Any]], errors: list[str], warnings: list[str],
) -> dict[str, dict[str, Any]]:
    seen_events: set[str] = set()
    latest: dict[str, dict[str, Any]] = {}
    latest_time: dict[str, datetime] = {}
    for index, row in enumerate(rows, start=1):
        label = f"comment_events.jsonl:{index}"
        _validate_comment_shape(row, label, errors)
        _record_event_id(row, label, seen_events, errors)
        try:
            observed = parse_time(row.get("observed_at", ""))
        except ValueError:
            errors.append(f"{label} observed_at must be ISO 8601 with UTC offset")
            continue
        comment_key = row.get("comment_key")
        if not isinstance(comment_key, str) or not comment_key:
            continue
        _record_latest(row, observed, latest, latest_time, label, errors)
        if row.get("identity_confidence") == "weak":
            warnings.append(f"{label} has weak identity and cannot use bounded auto-send")
    return latest
