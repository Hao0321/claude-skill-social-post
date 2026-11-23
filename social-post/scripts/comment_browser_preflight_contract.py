#!/usr/bin/env python3
"""Browser preflight approval, preparation, and native-canary evidence validation."""

from __future__ import annotations

import re
from typing import Any

from comment_browser_action_contract import build_browser_action
from comment_browser_common import (
    _json_digest, _require_live_receipt, _require_recent_observation,
    _require_schema_version, _required_boolean, _required_digest, _required_string,
)
from comment_browser_send_common import (
    CANARY_COMPOSER_FIELDS, PREFLIGHT_FLAGS, _find_intent,
    _require_no_scope_reconciliation, _require_send_observed_url,
)
from comment_canary import require_canary_lease
from comment_identity import stable_id
from comment_scan_provenance import (
    ACTION_PROVENANCE_DIGEST_FIELD, DRAFT_PROVENANCE_DIGEST_FIELD,
    SCAN_PROVENANCE_DIGEST_FIELD,
)
from social_primitives import parse_time


def _require_action_binding(
    raw: dict[str, Any], state: dict[str, Any], comment: dict[str, Any],
    intent_id: str, session_id: str,
) -> None:
    permit = state.get("permit") or {}
    expected_action_id = stable_id("browser-action", permit.get("permit_id"), intent_id)
    if raw.get("action_id") != expected_action_id:
        raise ValueError("browser preflight action_id differs from approved action")
    if raw.get("intent_id") != intent_id or raw.get("session_id") != session_id:
        raise ValueError("browser preflight identity differs from current action")
    if raw.get("permit_id") != permit.get("permit_id"):
        raise ValueError("browser preflight permit differs from approval")
    if raw.get("scope") != permit.get("scope"):
        raise ValueError("browser preflight scope differs from approval")
    if raw.get("comment_fingerprint") != comment.get("raw_fingerprint"):
        raise ValueError("browser preflight comment fingerprint differs from observation")
    if raw.get("reply_hash") != state.get("draft", {}).get("reply_hash"):
        raise ValueError("browser preflight reply hash differs from approved draft")


def _require_preparation_binding(
    raw: dict[str, Any], expected_action: dict[str, Any],
) -> dict[str, Any]:
    action_digest = _required_digest(raw, "action_digest")
    if action_digest != _json_digest(expected_action):
        raise ValueError("browser preflight action_digest differs from approved action")
    plan_digest = _required_digest(raw, "plan_digest")
    exact_count = raw.get("baseline_exact_reply_count")
    total_count = raw.get("baseline_total_reply_count")
    if not isinstance(exact_count, int) or isinstance(exact_count, bool) or exact_count != 0:
        raise ValueError("browser preflight requires a zero exact-own reply baseline")
    if not isinstance(total_count, int) or isinstance(total_count, bool) or total_count < 0:
        raise ValueError("browser preflight baseline_total_reply_count must be non-negative")
    core = {
        "action_digest": action_digest,
        "plan_digest": plan_digest,
        "observed_url": _required_string(raw, "observed_url"),
        "observed_at": _required_string(raw, "observed_at"),
        "baseline_exact_reply_count": exact_count,
        "baseline_total_reply_count": total_count,
        "test_only": False,
    }
    if any(key in raw for key in CANARY_COMPOSER_FIELDS):
        if not all(key in raw for key in CANARY_COMPOSER_FIELDS):
            raise ValueError("canary composer evidence must include every versioned field")
        core.update({key: raw[key] for key in CANARY_COMPOSER_FIELDS})
    preparation_id = _required_digest(raw, "preparation_id")
    if preparation_id != _json_digest(core):
        raise ValueError("browser preflight preparation_id integrity check failed")
    return {
        "action_digest": action_digest,
        "plan_digest": plan_digest,
        "preparation_id": preparation_id,
        "baseline_exact_reply_count": exact_count,
        "baseline_total_reply_count": total_count,
        **{key: raw[key] for key in CANARY_COMPOSER_FIELDS if key in raw},
    }


def _require_canary_native_mention(
    raw: dict[str, Any], action: dict[str, Any], state: dict[str, Any], lease_id: str | None,
) -> None:
    if not lease_id or action["scope"]["platform"] != "instagram":
        raise ValueError("nonempty native composer requires an authorized Instagram canary")
    require_canary_lease(state, lease_id, action["intent_id"], action["session_id"], action=action)
    author = action.get("author_key")
    if not isinstance(author, str) or not re.fullmatch(r"[A-Za-z0-9._]+", author):
        raise ValueError("native mention requires an exact Instagram author handle")
    prefix = f"@{author} "
    if raw.get("composer_initial_state") != "native_target_mention" or raw.get("composer_initial_text") != prefix:
        raise ValueError("native composer initial text differs from the approved target mention")
    if not action["reply_text"].startswith(prefix) or len(action["reply_text"]) <= len(prefix):
        raise ValueError("approved Instagram reply must preserve the exact native target mention")
    evidence = raw.get("selected_parent_evidence")
    keys = {"schema_version", "action_digest", "observed_url", "comment_key", "platform_comment_id",
            "author_key", "document_binding", "trigger_locator_digest", "initial_text"}
    version = evidence.get("schema_version") if isinstance(evidence, dict) else None
    if type(version) is not int or version not in (1, 2):
        raise ValueError("native selected-parent evidence has an invalid schema")
    keys.update({"composer_node_id"} if version == 1 else {
        "selection_kind", "composer_scope", "stable_reads",
    })
    if set(evidence) != keys:
        raise ValueError("native selected-parent evidence has an invalid schema")
    expected = {
        "action_digest": _json_digest(action), "observed_url": raw["observed_url"],
        "comment_key": action["scope"]["comment_key"],
        "platform_comment_id": action["comment_anchor"]["platform_comment_id"],
        "author_key": author, "initial_text": prefix,
        "trigger_locator_digest": _json_digest({
            "platform_comment_id": action["comment_anchor"]["platform_comment_id"],
            "comment_permalink": action["comment_anchor"]["comment_permalink"],
            "author_key": author, "expected_body": action["expected_body"],
            "role": "button", "name": "回覆",
        }),
    }
    if not expected["platform_comment_id"] or any(evidence.get(key) != value for key, value in expected.items()):
        raise ValueError("native selected-parent evidence differs from the canonical action")
    binding = evidence["document_binding"]
    binding_keys = {"schema_version", "kind", "tab_id", "observed_url", "target_digest"}
    if not isinstance(binding, dict) or set(binding) != binding_keys or type(binding.get("schema_version")) is not int or binding["schema_version"] != 1:
        raise ValueError("native selected-parent document binding has an invalid schema")
    target_digest = _json_digest({
        "account_key": action["scope"]["account_key"].removeprefix("@"),
        "comment_permalink": action["comment_anchor"]["comment_permalink"],
        "author_key": action["author_key"], "body": action["expected_body"],
    })
    if (binding["kind"] != "source_owned_ui_continuity"
            or binding["observed_url"] != action["comment_anchor"]["comment_permalink"]
            or binding["observed_url"] != raw["observed_url"]
            or _required_digest(binding, "target_digest") != target_digest):
        raise ValueError("native selected-parent document binding differs from the canonical target")
    _required_string(binding, "tab_id")
    if version == 1:
        _required_string(evidence, "composer_node_id")
    elif (evidence["selection_kind"] != "source_clicked_instagram_native_reply"
          or evidence["composer_scope"] != "unique_native_post_form"
          or type(evidence["stable_reads"]) is not int or evidence["stable_reads"] != 2):
        # CUA cannot claim a persistent DOM node. This version records the
        # source-selected, twice-read semantic form contract instead. It still
        # requires the same canonical lease/action/parent/mention/digest above;
        # schema acceptance alone is not browser provenance or send authority.
        raise ValueError("native semantic selection evidence is not source-selected and stable")
    if _required_digest(raw, "selected_parent_evidence_digest") != _json_digest(evidence):
        raise ValueError("native selected-parent evidence digest differs")


def validate_browser_preflight(
    raw: dict[str, Any], latest_comments: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]], policy: dict[str, Any],
    intent_id: str, session_id: str,
    *, canary_lease_id: str | None = None,
) -> dict[str, Any]:
    """Validate a fresh, read-only Chrome preflight before send_started."""
    if not isinstance(raw, dict):
        raise ValueError("browser preflight must be a JSON object")
    _require_schema_version(raw, "browser preflight")
    _require_live_receipt(raw, "browser preflight")
    comment_key, state = _find_intent(states, intent_id)
    if state.get("status") != "approved":
        raise ValueError(f"browser preflight requires approved status, found {state.get('status')}")
    permit = state.get("permit") or {}
    if permit.get("session_id") != session_id:
        raise ValueError("browser preflight session differs from approval")
    _require_no_scope_reconciliation(states, state, intent_id, session_id)
    comment = latest_comments[comment_key]
    _require_action_binding(raw, state, comment, intent_id, session_id)
    expected_action = build_browser_action(latest_comments, states, intent_id, session_id)
    _require_send_observed_url(comment, _required_string(raw, "observed_url"))
    observed_at = _require_recent_observation(
        raw, policy, "maximum_browser_preflight_age_seconds", 60, "browser preflight",
    )
    observed = parse_time(observed_at)
    if observed < parse_time(_required_string(permit, "occurred_at")):
        raise ValueError("browser preflight predates approval")
    if observed > parse_time(_required_string(permit, "expires_at")):
        raise ValueError("browser preflight occurred after permit expiry")
    preparation = _require_preparation_binding(raw, expected_action)
    for key in PREFLIGHT_FLAGS:
        if key == "composer_empty_before_fill" and _required_boolean(raw, key) is False:
            _require_canary_native_mention(raw, expected_action, state, canary_lease_id)
            continue
        if not _required_boolean(raw, key):
            raise ValueError(f"browser preflight {key} was not verified")
    if raw["composer_empty_before_fill"] and any(key in raw for key in CANARY_COMPOSER_FIELDS):
        raise ValueError("empty composer cannot claim native nonempty mention evidence")
    evidence = _required_string(raw, "evidence")
    preflight_id = stable_id(
        "browser-preflight", intent_id, preparation["preparation_id"], observed_at, evidence,
    )
    return {
        "preflight_id": preflight_id,
        "action_id": raw["action_id"],
        "observed_at": observed_at,
        "evidence": evidence,
        "comment_key": comment_key,
        "comment": comment,
        "state": state,
        **preparation,
        SCAN_PROVENANCE_DIGEST_FIELD: expected_action[SCAN_PROVENANCE_DIGEST_FIELD],
        DRAFT_PROVENANCE_DIGEST_FIELD: expected_action[DRAFT_PROVENANCE_DIGEST_FIELD],
        ACTION_PROVENANCE_DIGEST_FIELD: expected_action[ACTION_PROVENANCE_DIGEST_FIELD],
    }
