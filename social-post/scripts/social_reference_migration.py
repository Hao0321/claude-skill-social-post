"""Non-destructive migration of legacy external observations, not own outcomes."""

from __future__ import annotations

import copy
from pathlib import Path

from social_governance_store import digest
from social_learning import record_reference
from social_store import load_jsonl


def migrate_external(root: Path) -> dict:
    latest = {}
    for row in load_jsonl(root / "data/experiments.jsonl"):
        if row.get("owner_scope") == "third_party_reference_not_hao_account":
            latest[row["experiment_id"]] = row
    migrated = []
    skipped = []
    for identity, row in latest.items():
        source = row.get("reference_observations")
        if not isinstance(source, dict) or not source.get("reference_id"):
            skipped.append(identity)
            continue
        captions = source.get("content_observations", {}).get("verified_captions", {})
        publication = source.get("publication_context", {})
        live = source.get("primary_page_observations", {})
        for platform in ("threads", "instagram"):
            observed = source.get(platform)
            if not isinstance(observed, dict) or not isinstance(observed.get("metrics"), dict):
                continue
            for kind in ("screenshot", "primary_page"):
                observation = observed if kind == "screenshot" else live.get(platform)
                if not isinstance(observation, dict):
                    continue
                metrics = observation.get("metrics") if kind == "screenshot" else {
                    key: value for key, value in observation.items()
                    if key in {"likes", "comments", "reposts", "shares_or_sends", "saves"}}
                reference = {
                    "reference_id": source["reference_id"] + "-" + platform + "-" + kind,
                    "content_id": source["reference_id"], "owner_scope": "external", "platform": platform,
                    "media_family": "video", "caption": captions.get(platform, {}).get("text"),
                    "caption_provenance": captions.get("source"),
                    "published_at": publication.get(platform + "_published_at"),
                    "timezone": publication.get("timezone"),
                    "captured_at": publication.get("captured_at") if kind == "screenshot" else live.get("observed_at"),
                    "capture_meaning": "unknown screenshot time" if kind == "screenshot" else live.get("observation_time_meaning"),
                    "metrics": metrics, "metric_qualifiers": observed.get("metric_qualifiers", {}) if kind == "screenshot" else {},
                    "observation": copy.deepcopy(observation),
                    "shared_context": {key: copy.deepcopy(source[key]) for key in
                                       ("identity", "account_context", "publication_context", "content_observations", "reuse_boundary") if key in source},
                    "evidence": copy.deepcopy(source.get("evidence_files", [])),
                    "legacy_provenance": {"experiment_id": identity, "revision": row.get("revision"),
                                          "reference_payload_sha256": digest(source),
                                          "legacy_events_preserved": True},
                }
                event = record_reference(root, reference)
                migrated.append({"reference_id": reference["reference_id"], "digest": event["reference_digest"]})
    return {"status": "migrated", "references": migrated, "skipped_missing_structured_evidence": skipped,
            "legacy_events_changed": False, "own_outcomes_changed": False}
