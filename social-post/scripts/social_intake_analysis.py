"""Hash-bound private annotations of complete or explicitly partial intake content.

These records describe words and propose tests. They never promote an outcome,
change a writing contract, or enter the performance matrix.
"""

from __future__ import annotations

import copy
import hashlib
import json

from social_governance_store import (MAX_DOCUMENT, append_event_locked, digest,
                                     governance_lock, learning_events, private_path)
from social_post_analysis import caption_counts, punctuation_profile
from social_primitives import parse_time
from social_outcome_time_policy import time_policy
from social_snapshot import file_identity

KIND = "intake_content_analysis"
ROLES = {"topic", "use_case", "brand", "cost_benefit", "rights_claim", "launch_hook",
         "proof", "differentiator", "cta", "audience", "boundary", "time_claim"}
FIELDS = {"analysis_id", "source_intake_id", "post_id", "snapshot_id", "platform",
          "media_family", "caption_sha256", "content_scope", "recorded_at", "phrases",
          "evidence", "structure", "hypotheses", "confounds", "next_test", "candidates"}


def strings(values, label, *, required=True):
    if (not isinstance(values, list) or (required and not values)
            or any(not isinstance(item, str) or not item.strip() for item in values)):
        raise ValueError(f"{label} requires a string list")


def verified_evidence(root, rows, available):
    if not isinstance(rows, list) or not rows:
        raise ValueError("analysis needs original evidence bindings")
    known = {item.get("path"): item.get("sha256") or item.get("file_sha256") for item in available}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            raise ValueError("invalid analysis evidence binding")
        relative, expected = row["path"], row["sha256"]
        if (not isinstance(relative, str) or not relative.startswith("data/evidence/")
                or relative in seen or expected is None or known.get(relative) != expected):
            raise ValueError("analysis evidence is not part of the source intake")
        seen.add(relative)
        path = private_path(root, relative)
        before = file_identity(path)
        if before is None or hashlib.sha256(path.read_bytes()).hexdigest() != expected or before != file_identity(path):
            raise ValueError("analysis evidence bytes changed")


def validate_analysis(root, value, entries):
    if not isinstance(value, dict) or not FIELDS <= set(value) or set(value) - FIELDS - {"supersedes_analysis_id"}:
        raise ValueError("invalid intake analysis fields")
    if "supersedes_analysis_id" in value and (not isinstance(value["supersedes_analysis_id"], str)
                                               or not value["supersedes_analysis_id"].strip()):
        raise ValueError("invalid superseded analysis identity")
    for key in ("analysis_id", "source_intake_id", "post_id", "snapshot_id"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"invalid analysis {key}")
    entry = entries.get(value["source_intake_id"])
    if entry is None:
        raise ValueError("analysis source intake is missing")
    post, snapshot = entry["post"], entry["snapshot"]
    expected = {"post_id": post["post_id"], "snapshot_id": snapshot["snapshot_id"],
                "platform": snapshot["platform_scope"], "media_family": post["media_family"],
                "caption_sha256": post["caption_sha256"]}
    if any(value[key] != item for key, item in expected.items()):
        raise ValueError("analysis source identity, scope or caption changed")
    parse_time(value["recorded_at"])
    scope = value["content_scope"]
    if scope not in {"complete_caption", "visible_first_post"}:
        raise ValueError("unknown analysis content scope")
    if scope == "complete_caption" and (post.get("caption_is_complete") is False
                                        or post.get("analysis_status") != "complete"):
        raise ValueError("partial content cannot be declared complete")
    if scope == "visible_first_post" and post.get("caption_is_complete") is not False:
        raise ValueError("visible-first-post annotation requires explicit incomplete content")
    verified_evidence(root, value["evidence"], entry["evidence"])
    phrases = value["phrases"]
    if not isinstance(phrases, list) or not phrases:
        raise ValueError("analysis needs phrase roles")
    following = post.get("caption_transcription_notes", {}).get("visible_following_phrases", [])
    for phrase in phrases:
        if (not isinstance(phrase, dict) or set(phrase) != {"text", "role", "interpretation", "basis"}
                or phrase["role"] not in ROLES or not isinstance(phrase["text"], str)
                or not phrase["text"].strip() or not isinstance(phrase["interpretation"], str)
                or not phrase["interpretation"].strip()):
            raise ValueError("invalid phrase role")
        if phrase["basis"] == "caption_exact":
            if phrase["text"] not in post["caption"]:
                raise ValueError("phrase is absent from hash-bound caption")
        elif phrase["basis"] == "visible_transcription":
            if scope != "visible_first_post" or phrase["text"] not in following:
                raise ValueError("phrase is not an explicitly observed transcription")
        else:
            raise ValueError("unknown phrase evidence basis")
    for key in ("structure", "hypotheses", "confounds", "next_test"):
        strings(value[key], key)
    if not isinstance(value["candidates"], list):
        raise ValueError("candidates must be a list")
    for candidate in value["candidates"]:
        if (not isinstance(candidate, dict)
                or set(candidate) != {"candidate_id", "statement", "exclusions", "next_test"}
                or any(not isinstance(item, str) or not item.strip() for item in candidate.values())):
            raise ValueError("invalid hypothesis candidate")
    return entry


def analysis_projection(value, entry):
    post = entry["post"]
    return {**copy.deepcopy(value), "evidence_state": "hypothesis", "reference_only": True,
            "time_policy": time_policy(),
            "aggregation_eligible": False, "author_contract_changed": False,
            "counts_scope": "complete_caption" if value["content_scope"] == "complete_caption" else "hash_bound_prefix_only_not_complete_thread",
            "bound_caption_counts": caption_counts(post["caption"]),
            "bound_punctuation_profile": punctuation_profile(post["caption"]),
            "post_wording_features": copy.deepcopy(post.get("wording_features")),
            "publication_context": copy.deepcopy(post.get("publication_context"))}


def analysis_events(root):
    path = private_path(root, "data/learning_events.jsonl")
    before = file_identity(path)
    events = [row for row in learning_events(root) if row.get("kind") == KIND]
    if before != file_identity(path):
        raise ValueError("analysis ledger changed during review; retry")
    seen = set()
    for row in events:
        if (row.get("schema_version") != 1 or row.get("analysis_digest") != digest(row.get("analysis"))
                or not isinstance(row.get("analysis"), dict)):
            raise ValueError("analysis event digest or schema is invalid")
        identity = row["analysis"]["analysis_id"]
        if identity in seen:
            raise ValueError("duplicate analysis ID")
        seen.add(identity)
    return events


def check_supersession(value, active):
    parent = value.get("supersedes_analysis_id")
    if parent is None:
        return
    prior = active.get(parent)
    if prior is None:
        raise ValueError("superseded analysis must be an existing active revision")
    keys = ("source_intake_id", "post_id", "snapshot_id", "platform", "media_family")
    if any(value[key] != prior["analysis"][key] for key in keys):
        raise ValueError("analysis revision cannot change its source or platform scope")


def active_analysis_events(root):
    active = {}
    for event in analysis_events(root):
        value = event["analysis"]
        check_supersession(value, active)
        parent = value.get("supersedes_analysis_id")
        if parent is not None:
            del active[parent]
        active[value["analysis_id"]] = event
    return active


def analyses_for_entries(root, entries):
    result = {}
    for event in active_analysis_events(root).values():
        value = event["analysis"]
        entry = validate_analysis(root, value, entries)
        result.setdefault(value["source_intake_id"], []).append(analysis_projection(value, entry))
    return result


def record_analysis(root, path, entry_loader, *, write=False):
    raw = path.read_bytes()
    if len(raw) > MAX_DOCUMENT:
        raise ValueError("analysis document exceeds bound")
    value = json.loads(raw.decode("utf-8-sig"))
    with governance_lock(root):
        intake_path = private_path(root, "data/outcome_intakes.jsonl")
        before = file_identity(intake_path)
        entries = entry_loader()
        entry = validate_analysis(root, value, entries)
        prior = [row for row in analysis_events(root)
                 if row["analysis"]["analysis_id"] == value["analysis_id"]]
        event = {"schema_version": 1, "kind": KIND, "analysis": value, "analysis_digest": digest(value)}
        if prior and prior[0] != event:
            raise ValueError("analysis ID already exists; use a new revision ID")
        if not prior:
            check_supersession(value, active_analysis_events(root))
        if before != file_identity(intake_path):
            raise ValueError("intake changed during analysis; retry")
        if write and not prior:
            append_event_locked(root, event)
    return {"valid": True, "status": "already_recorded" if prior else "appended" if write else "dry_run",
            "analysis_id": value["analysis_id"], "analysis_digest": event["analysis_digest"],
            "content_scope": value["content_scope"], "reference_only": True,
            "aggregation_eligible": False, "post_analysis_status": entry["post"]["analysis_status"]}
