"""Bounded workbench application adapter around the canonical Social Post engine."""

from __future__ import annotations

import copy
import hashlib
import json
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from log_outcome import load_store_records, prepare_records, validate_staged
from social_data import comparables_context, feature_matrix, validate_store
from social_post_analysis import caption_counts, punctuation_profile
from social_store import commit_records
from social_validation import MATURITY_VALUES
from workbench_contract import FORMATS, MODES, PLATFORMS, VERSION, build_handoff, parse_json, text_field
from workbench_formulas import formula_catalog
from workbench_store import check_data_paths, get_draft, list_drafts, safe_path, save_draft


class WorkbenchService:
    def __init__(self, root: Path):
        self.root = root.absolute()
        if not self.root.is_dir():
            raise ValueError("workspace must exist")
        check_data_paths(self.root)
        self.previews: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def catalog(self) -> dict[str, Any]:
        return {"version": VERSION, "modes": MODES, "formats": FORMATS,
                "formulas": formula_catalog(self.root),
                "platforms": PLATFORMS, "maturities": sorted(MATURITY_VALUES),
                "execution": "local_tools_and_ai_handoff",
                "live_publish": False, "live_comment_send": False}

    def task(self, payload: Any) -> dict[str, Any]:
        result = build_handoff(payload)
        identity = payload.get("formula")
        if identity and identity not in {row["id"] for row in formula_catalog(self.root)}:
            raise ValueError("selected formula is unavailable in this workspace")
        return result

    def overview(self) -> dict[str, Any]:
        check_data_paths(self.root)
        _, records = load_store_records(self.root / "data")
        matrix = feature_matrix(self.root)
        return {
            "posts": len(records["posts"]), "snapshots": len(records["snapshots"]),
            "drafts": len(list_drafts(self.root)), "eligible_rows": len(matrix),
            "voice_available": all(
                safe_path(self.root, name).exists()
                and "[待填]" not in safe_path(self.root, name).read_text(encoding="utf-8-sig")
                and "<your" not in safe_path(self.root, name).read_text(encoding="utf-8-sig").lower()
                for name in ("voice_quick.md", "style_profile.md")
            ),
            "content_types": sorted({row["content_type"] for row in matrix if row.get("content_type")}),
            "surfaces": sorted({row["layout"]["surface"] for row in matrix
                                if row.get("layout", {}).get("surface")}),
        }

    def compare(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) != {"platform", "content_type", "surface", "maturity"}:
            raise ValueError("exact cohort fields are required")
        query = {key: text_field(payload, key, 120) for key in payload}
        if query["platform"] not in PLATFORMS or query["maturity"] not in MATURITY_VALUES:
            raise ValueError("unknown comparison scope")
        if not query["content_type"] or not query["surface"]:
            raise ValueError("content type and surface are required")
        check_data_paths(self.root)
        return comparables_context(self.root, **query, limit=2)

    def analyze(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) != {"text"}:
            raise ValueError("invalid analysis request")
        text_field(payload, "text")
        text = payload["text"]
        return {"counts": caption_counts(text), "punctuation": punctuation_profile(text),
                "basis": "deterministic_text_features", "traffic_prediction": None}

    def preview(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) not in ({"bundle"}, {"bundle_json"}):
            raise ValueError("bundle is required")
        bundle = (parse_json(text_field(payload, "bundle_json", 100000))
                  if "bundle_json" in payload else payload["bundle"])
        allowed = {"post", "snapshot", "account_snapshot", "experiment", "correction"}
        if not isinstance(bundle, dict) or set(bundle) - allowed:
            raise ValueError("unknown outcome bundle field")
        if any(value is not None and not isinstance(value, dict) for value in bundle.values()):
            raise ValueError("bundle records must be objects")
        bundle = copy.deepcopy(bundle)
        check_data_paths(self.root)
        records, normalized, revision = prepare_records(bundle, self.root / "data")
        validate_staged(records)
        digest = hashlib.sha256(json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        with self.lock:
            now = time.monotonic()
            self.previews = {key: row for key, row in self.previews.items() if row["expires"] > now}
            if len(self.previews) >= 20:
                raise ValueError("preview capacity reached")
            identity = secrets.token_hex(24)
            self.previews[identity] = {
                "records": records, "revision": revision, "expires": now + 600, "digest": digest,
            }
        return {"preview_id": identity, "bundle_sha256": digest,
                "normalized": copy.deepcopy(normalized), "write_performed": False, "expires_seconds": 600}

    def commit(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) != {"preview_id"}:
            raise ValueError("only a preview id may be committed")
        identity = text_field(payload, "preview_id", 48)
        with self.lock:
            preview = self.previews.pop(identity, None)
            if preview is None or preview["expires"] <= time.monotonic():
                raise ValueError("preview expired or already consumed")
            check_data_paths(self.root)
            revision = commit_records(preview["records"], data_dir=self.root / "data",
                                      expected_revision=preview["revision"])
        if not validate_store(self.root)["valid"]:
            raise RuntimeError("post-commit validation failed")
        return {"status": "committed", "revision": revision, "bundle_sha256": preview["digest"]}

    def dispatch(self, route: str, payload: Any) -> Any:
        actions = {
            "/api/task": self.task,
            "/api/analyze": self.analyze,
            "/api/compare": self.compare,
            "/api/outcome/preview": self.preview,
            "/api/outcome/commit": self.commit,
            "/api/drafts/save": lambda row: save_draft(self.root, row),
        }
        if route not in actions:
            raise KeyError("unknown operation")
        return actions[route](payload)

    def draft(self, identity: str) -> dict[str, Any]:
        return get_draft(self.root, identity)
