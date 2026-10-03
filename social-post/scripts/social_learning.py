"""Separate external observations and digest-bound, owner-reviewed proposals."""

from __future__ import annotations

import copy
import hashlib
import secrets
from pathlib import Path
from typing import Any

from social_cohorts import MEDIA_FAMILIES
from social_governance_store import (append_event_locked, digest, governance_lock,
                                     learning_events, write_document)
from social_primitives import PLATFORM_VALUES, parse_time
from social_writing_contract import (POINTER, POLICY, active_contract, effective_sources,
                                     policy_valid, save_version_locked, verify_contract)


def valid_scope(scope: Any) -> None:
    if not isinstance(scope, dict) or set(scope) != {"platform", "media_family"}:
        raise ValueError("exact platform/media scope is required")
    if scope["platform"] not in PLATFORM_VALUES - {"combined"} or scope["media_family"] not in MEDIA_FAMILIES:
        raise ValueError("unknown learning scope")


def record_reference(root: Path, reference: dict[str, Any]) -> dict[str, Any]:
    """Unknown publication dates and metrics are allowed; no fake own-post ID."""
    required = {"reference_id", "content_id", "platform", "media_family", "caption", "published_at",
                "captured_at", "metrics", "metric_qualifiers", "evidence"}
    if not isinstance(reference, dict) or not required <= set(reference):
        raise ValueError("incomplete external observation")
    valid_scope({key: reference[key] for key in ("platform", "media_family")})
    if reference.get("owner_scope", "external") != "external" or "post_id" in reference:
        raise ValueError("external observations cannot masquerade as own posts")
    if not all(isinstance(reference[key], str) and reference[key] for key in ("reference_id", "content_id")):
        raise ValueError("external identities are required")
    if reference["caption"] is not None and not isinstance(reference["caption"], str):
        raise ValueError("caption must be exact text or unknown")
    for field in ("published_at", "captured_at"):
        if reference[field] is not None:
            parse_time(reference[field])
    if not isinstance(reference["metrics"], dict) or not isinstance(reference["metric_qualifiers"], dict):
        raise ValueError("metrics and qualifiers must be separate objects")
    if not isinstance(reference["evidence"], list) or not reference["evidence"]:
        raise ValueError("external observation needs provenance")
    event = {"schema_version": 1, "kind": "external_reference", "owner_scope": "external",
             "reference": copy.deepcopy(reference), "reference_digest": digest(reference)}
    with governance_lock(root):
        prior = [row for row in learning_events(root) if row.get("kind") == "external_reference"
                 and row["reference"]["reference_id"] == reference["reference_id"]]
        if prior:
            if prior[-1] != event:
                raise ValueError("external observation already exists; append a new observation ID")
            return event
        append_event_locked(root, event)
    return event


def _evidence_scope(root: Path, identities: list[str], scope: dict[str, str]) -> list[dict[str, Any]]:
    """External evidence can motivate a candidate, never prove own validation."""
    from social_data import feature_matrix

    available = {}
    for row in feature_matrix(root):
        if row["owner_scope"] == "own":
            available[row["snapshot_id"]] = {"platform": row["platform"], "media_family": row["media_family"],
                                             "owner_scope": "own", "post_id": row["post_id"]}
    for row in learning_events(root):
        if row.get("kind") == "external_reference":
            ref = row["reference"]
            available[ref["reference_id"]] = {"platform": ref["platform"], "media_family": ref["media_family"],
                                               "owner_scope": "external", "content_id": ref["content_id"]}
    if not identities or len(identities) != len(set(identities)):
        raise ValueError("distinct recorded evidence IDs are required")
    result = []
    for identity in identities:
        if identity not in available or any(available[identity][key] != scope[key] for key in scope):
            raise ValueError("evidence is missing or crosses platform/media boundaries")
        result.append({"id": identity, **available[identity]})
    return result


def propose(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"title", "target", "replacement_text", "scope", "evidence_ids", "reason"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("invalid proposal fields")
    valid_scope(payload["scope"])
    if any(not isinstance(payload[key], str) or not payload[key].strip() for key in
           ("title", "target", "replacement_text", "reason")) or len(payload["replacement_text"]) > 65536:
        raise ValueError("proposal text is required and bounded")
    if not isinstance(payload["evidence_ids"], list) or any(not isinstance(value, str) for value in payload["evidence_ids"]):
        raise ValueError("evidence IDs must be a list")
    with governance_lock(root):
        verified = verify_contract(root)
        revision, document = active_contract(root)
        sources = effective_sources(document, payload["scope"]["platform"], payload["scope"]["media_family"])
        if payload["target"] not in sources:
            raise ValueError("proposal target is not a frozen author source")
        evidence = _evidence_scope(root, payload["evidence_ids"], payload["scope"])
        if payload["target"] == POLICY:
            import json
            policy_valid(json.loads(payload["replacement_text"]))
        proposal = {"proposal_id": secrets.token_hex(16), **copy.deepcopy(payload),
                    "base_revision": revision, "base_source_sha256": sources[payload["target"]]["effective_sha256"],
                    "base_text": sources[payload["target"]]["text"],
                    "evidence": evidence, "evidence_claim": "candidate_not_validated_rule"}
        event = {"schema_version": 1, "kind": "proposal", "proposal": proposal,
                 "proposal_digest": digest(proposal), "author_revision_unchanged": verified["revision"]}
        append_event_locked(root, event)
        return event


def proposal_by_id(root: Path, identity: str) -> dict[str, Any]:
    matches = [row for row in learning_events(root) if row.get("kind") == "proposal"
               and row["proposal"]["proposal_id"] == identity]
    if len(matches) != 1 or digest(matches[0]["proposal"]) != matches[0]["proposal_digest"]:
        raise ValueError("proposal missing or failed integrity verification")
    return matches[0]


def review(root: Path, identity: str, expected_digest: str, decision: str, notes: str,
           *, owner_confirmed: bool = False) -> dict[str, Any]:
    if not owner_confirmed:
        raise ValueError("owner must explicitly approve or reject the exact displayed proposal")
    if decision not in {"approve", "reject"} or not isinstance(notes, str) or not notes.strip() or len(notes) > 4000:
        raise ValueError("a review decision and substantive notes are required")
    with governance_lock(root):
        event = proposal_by_id(root, identity)
        if event["proposal_digest"] != expected_digest or verify_contract(root)["revision"] != event["proposal"]["base_revision"]:
            raise ValueError("proposal digest or base revision changed; review again")
        row = {"schema_version": 1, "kind": "review", "proposal_id": identity,
               "proposal_digest": expected_digest, "decision": decision, "notes": notes,
               "review_id": secrets.token_hex(16), "authority": "explicit_local_owner_action"}
        append_event_locked(root, row)
        return row


def activate(root: Path, identity: str, expected_digest: str, *, owner_confirmed: bool = False) -> dict[str, Any]:
    if not owner_confirmed:
        raise ValueError("activation requires a separate explicit owner action")
    with governance_lock(root):
        event = proposal_by_id(root, identity)
        proposal = event["proposal"]
        revision, document = active_contract(root)
        verify_contract(root)
        if expected_digest != event["proposal_digest"] or revision != proposal["base_revision"]:
            raise ValueError("stale or replayed proposal; rebase and review again")
        reviews = [row for row in learning_events(root) if row.get("kind") == "review"
                   and row["proposal_id"] == identity]
        if not reviews or reviews[-1]["decision"] != "approve" or reviews[-1]["proposal_digest"] != expected_digest:
            raise ValueError("exact proposal has no current owner approval")
        scope = proposal["scope"]
        source = effective_sources(document, scope["platform"], scope["media_family"])[proposal["target"]]
        if source["effective_sha256"] != proposal["base_source_sha256"]:
            raise ValueError("proposal target changed")
        updated = copy.deepcopy(document)
        updated["parent_revision"] = revision
        updated["proposal_digest"] = expected_digest
        updated["approval"] = reviews[-1]
        overrides = [row for row in updated["overrides"]
                     if (row["target"], row["scope"]) != (proposal["target"], scope)]
        overrides.append({"target": proposal["target"], "scope": scope,
                          "text": proposal["replacement_text"], "text_digest": digest(proposal["replacement_text"]),
                          "proposal_digest": expected_digest})
        updated["overrides"] = overrides
        next_revision = save_version_locked(root, updated)
        # Immutable content and embedded approval precede the single atomic pointer switch.
        write_document(root, POINTER, {"schema_version": 1, "revision": next_revision})
        return {"status": "activated", "revision": next_revision, "previous_revision": revision,
                "scope": scope, "proposal_digest": expected_digest}


def learning_overview(root: Path) -> dict[str, Any]:
    rows = learning_events(root)
    revisions = []
    try:
        current, document = active_contract(root)
        while current:
            revisions.append(document.get("proposal_digest"))
            current = document.get("parent_revision")
            if not current:
                break
            from social_governance_store import read_document
            document = read_document(root, "data/author_contracts/" + current + ".json")
            if digest(document) != current or len(revisions) > 1000:
                raise ValueError("invalid contract ancestry")
    except FileNotFoundError:
        if any(row.get("kind") == "proposal" for row in rows):
            raise ValueError("author contract missing for existing proposals")
    candidates = []
    for event in rows:
        if event.get("kind") != "proposal":
            continue
        proposal = event["proposal"]
        reviews = [row for row in rows if row.get("kind") == "review"
                   and row["proposal_id"] == proposal["proposal_id"]]
        state = "activated" if event["proposal_digest"] in revisions else (reviews[-1]["decision"] if reviews else "pending")
        candidates.append({**event, "state": state})
    references = [row["reference"] for row in rows if row.get("kind") == "external_reference"]
    return {"external_references": references, "proposals": candidates, "automatic_update": False}
