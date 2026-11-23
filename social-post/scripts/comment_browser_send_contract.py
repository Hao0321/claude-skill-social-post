#!/usr/bin/env python3
"""Compatibility exports for modular browser send and recovery contracts."""

from __future__ import annotations

import re
from typing import Any

from comment_browser_common import (
    _json_digest, _require_comment_permalink_for_post, _require_live_receipt,
    _require_platform_url, _require_post_url, _require_recent_observation,
    _require_schema_version, _required_digest,
    _required_boolean, _required_string,
    parse_time,
)
from comment_identity import stable_id
from comment_canary import CANARY_ATTEMPT_FIELDS, canary_settlement_allowed, require_canary_lease
from comment_scan_provenance import (
    ACTION_PROVENANCE_DIGEST_FIELD,
    DRAFT_PROVENANCE_DIGEST_FIELD,
    SCAN_PROVENANCE_DIGEST_FIELD,
    browser_action_provenance_fields,
)

from comment_browser_action_contract import (
    _browser_action_from_ledger, build_browser_action, build_browser_recovery_action,
)
from comment_browser_preflight_contract import (
    _require_action_binding, _require_canary_native_mention,
    _require_preparation_binding, validate_browser_preflight,
)
from comment_browser_result_contract import (
    _require_reinspection_evidence_flags, _result_scope_matches,
    classify_browser_reinspection, classify_browser_result,
)
from comment_browser_send_common import (
    CANARY_COMPOSER_FIELDS, PREFLIGHT_FLAGS, REINSPECTION_CONTEXT_FLAGS, RESULT_FLAGS,
    _find_intent, _require_no_scope_reconciliation, _require_non_negative_integer,
    _require_send_observed_url, _scope_key,
)
