#!/usr/bin/env python3
"""Explicit local governance commands; data ingestion never approves rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from social_cohorts import MEDIA_FAMILIES, channel_inventory
from social_data import feature_matrix
from social_learning import activate, learning_overview, propose, record_reference, review
from social_reference_migration import migrate_external
from social_writing_contract import bootstrap, check_draft, contract_status, writing_context
from workbench_contract import PLATFORMS, parse_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "bootstrap", "context", "check-draft", "channels",
                                           "record-reference", "migrate-external", "propose", "review", "activate"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--formula", default="")
    parser.add_argument("--format", choices=("A", "B", "C"), default="C")
    parser.add_argument("--platform", choices=PLATFORMS)
    parser.add_argument("--media-family", choices=MEDIA_FAMILIES)
    parser.add_argument("--revision")
    parser.add_argument("--proposal")
    parser.add_argument("--digest")
    parser.add_argument("--decision", choices=("approve", "reject"))
    parser.add_argument("--notes", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--owner-confirmed", action="store_true",
                        help="Only after the human reviews this exact digest; never infer from a general task")
    args = parser.parse_args()
    root = args.root.absolute()
    try:
        if args.action in {"bootstrap", "record-reference", "migrate-external", "propose", "review", "activate"} and not args.write:
            raise ValueError("explicit --write required; no automatic author-policy writes")
        if args.action in {"context", "check-draft"} and (not args.platform or not args.media_family):
            raise ValueError("exact platform and media family are required")
        if args.action == "status":
            result = {"contract": contract_status(root), **learning_overview(root)}
        elif args.action == "bootstrap":
            result = bootstrap(root)
        elif args.action == "channels":
            result = channel_inventory(feature_matrix(root), PLATFORMS)
        elif args.action == "migrate-external":
            result = migrate_external(root)
        elif args.action == "context":
            result = writing_context(root, args.formula, args.format, args.platform, args.media_family)
        elif args.action == "check-draft":
            if not args.input or not args.revision or not args.formula:
                raise ValueError("draft file, formula and bound author revision are required")
            result = check_draft(root, args.input.read_text(encoding="utf-8-sig"), args.formula,
                                 args.format, args.revision, args.platform, args.media_family)
        elif args.action in {"record-reference", "propose"}:
            if not args.input:
                raise ValueError("input JSON is required")
            raw = args.input.read_bytes()
            if len(raw) > 100000:
                raise ValueError("input exceeds bound")
            value = parse_json(raw.decode("utf-8-sig"))
            result = (record_reference(root, value) if args.action == "record-reference" else propose(root, value))
        elif args.action == "review":
            result = review(root, args.proposal, args.digest, args.decision, args.notes,
                            owner_confirmed=args.owner_confirmed)
        else:
            result = activate(root, args.proposal, args.digest, owner_confirmed=args.owner_confirmed)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 1 if result.get("structural_pass") is False else 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
