"""Publication-only timing for P0–P4, including all historical outcome records.

Screenshot/status-bar clocks are incidental source pixels, not learning inputs.
Raw archives remain intact; readers and new writers discard this retired metadata.
Operational P5 freshness, grants and deadlines are outside this data policy.
"""

from __future__ import annotations

TIME_POLICY_ID = "publication-only-v1"
RETIRED_CAPTURE_FIELDS = frozenset({
    "captured_at", "captured_at_confidence", "hours_since_publish", "maturity",
    "captured_before", "capture_context", "capture_source", "capture_datetime",
    "screenshot_time", "screenshot_datetime", "screenshot_captured_at",
    "original_screenshot_captured_at", "first_attachment_local_created_utc",
    "capture_meaning", "ingested_at", "observed_at", "observation_time_meaning",
})


def retired_capture_key(key):
    return isinstance(key, str) and any(part in RETIRED_CAPTURE_FIELDS for part in key.casefold().split("."))


def without_capture_metadata(value):
    """Project archive data without consulting, validating or guessing its clocks."""
    if isinstance(value, dict):
        return {key: without_capture_metadata(child) for key, child in value.items()
                if not retired_capture_key(key)}
    if isinstance(value, list):
        return [without_capture_metadata(child) for child in value]
    return value


def time_policy():
    return {"id": TIME_POLICY_ID, "analytic_time_field": "published_at",
            "screenshot_time_required": False, "legacy_capture_metadata": "archive_only_ignored",
            "screenshot_based_eligibility_or_ranking": False,
            "same_publication_minute_guarantees_performance": False}
