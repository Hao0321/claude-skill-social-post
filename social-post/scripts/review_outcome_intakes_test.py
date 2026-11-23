#!/usr/bin/env python3
"""Regression checks for the P3 intake queue with fictional observations."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest.mock import patch

from review_outcome_intakes import main, review
from social_data import feature_matrix
from social_post_analysis import caption_counts
from social_store import write_jsonl


def post(post_id, caption, complete=True):
    return {
        "schema_version": "1.0", "post_id": post_id, "published_at": "2025-02-03T10:00:00+00:00",
        "published_at_confidence": "high", "timezone": "UTC", "caption": caption,
        "caption_confidence": "high", "caption_is_complete": complete,
        "caption_sha256": hashlib.sha256(caption.encode()).hexdigest(),
        "platforms": ["facebook"], "media_family": "text_image", "content_type": "photo_post",
        "analysis_status": "complete" if complete else "pending",
        "analysis_version": "fixture-v1" if complete else "pending", "analysis_eligible": complete,
        "analysis_evidence": "Fictional example.",
        "format_features": {"surface": "facebook_photo", "caption_layout": "single paragraph",
                            "emoji": 0, "explicit_cta": 0, **caption_counts(caption)},
        "wording_features": {"opening": caption, "hook": "example", "mechanism": "example",
                             "differentiator": "example", "proof_style": "none", "cta": "none",
                             "keywords": ["example"], "voice": ["plain"],
                             "punctuation_style": ["plain"], "named_entities": [],
                             "numbers_observed": [], "numeric_language": []},
        "publication_context": {"local_date": "2025-02-03", "weekday_zh_tw": "星期一",
                                "local_time": "10:00", "daypart": "morning"},
    }


def event(kind, intake_id, time="2025-02-03T18:00:00.1234567+00:00"):
    return {"event_type": kind, "intake_id": intake_id, "recorded_at": time,
            "platform": "facebook", "owner_scope": "own"}


def base(post_id="example-post", snap_id="example-snapshot", intake_id="example-intake"):
    return {
        **event("owner_post_outcome_intake", intake_id),
        "post_candidate": post(post_id, "Prototype", False),
        "snapshot_observation": {
            "snapshot_id": snap_id, "post_id": post_id, "platform_scope": "facebook",
            "captured_at": None, "metrics": {"views": 2000, "comments": 0, "link_clicks": None},
            "metric_qualifiers": {"views": "rounded", "meta_overview_observation.metrics.views": "exact"},
            "meta_overview_observation": {"metrics": {"views": 2081, "followers_gained": 0}},
            "instagram_reference": {"metrics": {"views": 35, "comments": None}},
        },
    }


def caption_event():
    return {
        **event("author_full_caption_confirmation", "example-caption", "2025-02-05T10:00:00+00:00"),
        "parent_intake_id": "example-intake", "snapshot_source_intake_id": "example-intake",
        "post_id": "example-post", "snapshot_id": "example-snapshot",
        "post_candidate": post("example-post", "Prototype ready for feedback."),
    }


def account_event():
    return {
        **event("owner_account_outcome_intake", "account-intake", "2025-02-05T11:00:00+00:00"),
        "account_snapshot_candidate": {"account_snapshot_id": "account-example", "platform": "facebook",
                                       "window_days": 30, "captured_at": None,
                                       "metrics": {"views": 12000, "followers_gained": 31}},
    }


class ReviewIntakesTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="social-post-intake-test-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.data = self.root / "data"

    def seed(self, *rows):
        write_jsonl(self.data / "outcome_intakes.jsonl", list(rows))

    def test_empty_install_is_read_only(self):
        self.assertEqual(review(self.root)["unique_post_count"], 0)
        self.assertFalse(self.data.exists())

    def test_linked_caption_and_platform_boundaries(self):
        self.seed(base(), caption_event(), account_event(), {"intake_id": "historical-note"})
        before = (self.data / "outcome_intakes.jsonl").read_bytes()
        result = review(self.root, since=date(2025, 2, 5))
        self.assertEqual(result["unique_post_count"], 1)
        row, = result["post_observations"]
        self.assertEqual(row["supplement_intake_ids"], ["example-caption"])
        self.assertTrue(row["caption_analysis_complete"])
        self.assertEqual(row["missing"], [])
        self.assertFalse(row["canonical_registered"])
        self.assertEqual(row["platform_metrics"]["views"], {"value": 2000, "qualifier": "rounded"})
        self.assertEqual(row["platform_metrics"]["comments"]["value"], 0)
        self.assertNotIn("link_clicks", row["platform_metrics"])
        self.assertEqual(row["reference_metrics"]["meta_overview_observation"]["views"]["value"], 2081)
        self.assertEqual(row["reference_metrics"]["instagram_reference"]["views"]["value"], 35)
        self.assertEqual(result["account_observations"][0]["account_metrics"]["followers_gained"]["value"], 31)
        self.assertEqual(result["other_history_ids_unfiltered"], ["historical-note"])
        self.assertNotIn("Prototype", json.dumps(result))
        self.assertEqual(feature_matrix(self.root), [])
        self.assertEqual((self.data / "outcome_intakes.jsonl").read_bytes(), before)

    def test_canonical_match_requires_the_exact_snapshot(self):
        other = base("example-post", "other-snapshot", "other-intake")
        self.seed(base(), caption_event(), other)
        write_jsonl(self.data / "posts.jsonl", [caption_event()["post_candidate"]])
        canonical = {**other["snapshot_observation"], "captured_at": "2025-02-05T10:00:00+00:00",
                     "maturity": "developing"}
        write_jsonl(self.data / "insight_snapshots.jsonl", [canonical])
        result = review(self.root)
        self.assertEqual(result["unique_post_count"], 1)
        lookup = {r["intake_id"]: r for r in result["post_observations"]}
        self.assertFalse(lookup["example-intake"]["canonical_registered"])
        self.assertTrue(lookup["other-intake"]["canonical_registered"])
        self.assertNotIn("captured_at", lookup["other-intake"])
        self.assertEqual(len(feature_matrix(self.root)), 1)

    def test_identity_conflicts_reject_but_legacy_screenshot_clocks_are_ignored(self):
        for key in ("parent_intake_id", "snapshot_source_intake_id", "post_id", "snapshot_id", "platform"):
            with self.subTest(key=key):
                bad = {**caption_event(), key: "mismatch"}
                self.seed(base(), bad)
                with self.assertRaises(ValueError):
                    review(self.root)
        for clock in ("2025-02-03T18:00:00", "2025-02-03T09:59:00+00:00"):
            with self.subTest(clock=clock):
                bad = base()
                bad["snapshot_observation"]["captured_at"] = clock
                self.seed(bad)
                self.assertEqual(review(self.root)["unique_post_count"], 1)

    def test_rejects_duplicate_and_conflicting_caption(self):
        wrong = deepcopy(caption_event())
        wrong["post_candidate"] = post("example-post", "Unrelated caption")
        for rows in ((base(), base(intake_id="distinct-intake")), (base(), wrong), (base(), base())):
            self.seed(*rows)
            with self.assertRaises(ValueError):
                review(self.root)

    def test_cli_json_and_legacy_fractional_clock(self):
        self.seed(base())
        arguments = ["review_outcome_intakes.py", "--root", str(self.root),
                     "--since", "2025-02-03", "--format", "json"]
        output = io.StringIO()
        with patch.object(sys, "argv", arguments), redirect_stdout(output):
            self.assertEqual(main(), 0)
        row, = json.loads(output.getvalue())["post_observations"]
        self.assertEqual(row["recorded_at"], "2025-02-03T18:00:00.1234567+00:00")
        self.assertEqual(row["missing"], ["complete_caption_analysis"])

    def test_undated_thread_then_time_confirmation_keeps_native_fields(self):
        original, supplement = pending_thread()
        self.seed(original)
        row, = review(self.root)["post_observations"]
        self.assertIsNone(row["published_at"])
        self.assertIn("publication_datetime", row["missing"])
        self.seed(original, supplement)
        before = (self.data / "outcome_intakes.jsonl").read_bytes()
        row, = review(self.root)["post_observations"]
        self.assertEqual(row["published_at"], supplement["post_candidate"]["published_at"])
        self.assertEqual(row["published_at_precision"], {"kind": "approximate_minute"})
        self.assertEqual(row["missing"], ["complete_caption_analysis"])
        self.assertEqual(row["platform_metrics"]["replies"]["value"], 7)
        self.assertEqual(row["platform_metrics"]["reposts"]["value"], 8)
        self.assertEqual(row["platform_metrics"]["profile_views"]["value"], 9)
        self.assertEqual(row["platform_metrics"]["future_metric"]["value"], 12)
        self.assertIn("quotes", row["unknown_platform_metrics"])
        self.assertEqual(row["platform_analytics"]["rates_reported"], {"reply_rate_percent": 0})
        self.assertIsNone(row["platform_analytics"]["audience"]["non_followers_percent"])
        self.assertNotIn("captured_at", row)
        self.assertEqual(feature_matrix(self.root), [])
        self.assertEqual((self.data / "outcome_intakes.jsonl").read_bytes(), before)

    def test_time_supplement_cannot_change_content_identity_or_metrics(self):
        for field, value in (("caption", "different"), ("analysis_eligible", True),
                             ("platforms", ["facebook"]), ("post_id", "wrong")):
            with self.subTest(field=field):
                original, supplement = pending_thread()
                supplement["post_candidate"][field] = value
                self.seed(original, supplement)
                with self.assertRaises(ValueError):
                    review(self.root)
        original, supplement = pending_thread()
        supplement["snapshot_observation"] = original["snapshot_observation"]
        self.seed(original, supplement)
        with self.assertRaises(ValueError):
            review(self.root)

    def test_pending_hash_and_unknown_metric_fail_closed(self):
        for key, value in (("caption_sha256", "0" * 64), ("analysis_eligible", True)):
            original, _ = pending_thread()
            original["post_candidate"][key] = value
            self.seed(original)
            with self.assertRaises(ValueError):
                review(self.root)
        for value in (True, -1, float("inf"), "twelve"):
            original, _ = pending_thread()
            original["snapshot_observation"]["metrics"]["new_metric"] = value
            self.seed(original)
            with self.assertRaises(ValueError):
                review(self.root)

    def test_compact_governance_status_omits_reference_bodies(self):
        import social_governance

        output = io.StringIO()
        with patch.object(sys, "argv", ["social_governance.py", "status", "--compact"]), \
                patch.object(social_governance, "contract_status", return_value={"status": "locked"}), \
                patch.object(social_governance, "learning_overview", return_value={
                    "external_references": [{"caption": "private unrelated reference"}],
                    "proposals": [], "automatic_update": False}), redirect_stdout(output):
            self.assertEqual(social_governance.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["external_reference_count"], 1)
        self.assertEqual(result["contract"], {"status": "locked"})
        self.assertNotIn("private unrelated reference", output.getvalue())


def pending_thread():
    original = base()
    original["event_type"] = "owner_post_outcome_intake_pending_publication_time"
    original["platform"] = "threads"
    original["post_candidate"].update(platforms=["threads"], published_at=None, timezone=None,
                                       content_type="text_post")
    original["snapshot_observation"].update(platform_scope="threads", metrics={
        "views": 1000, "replies": 7, "reposts": 8, "shares": 6,
        "profile_views": 9, "future_metric": 12, "quotes": None},
        rates_reported={"reply_rate_percent": 0}, audience={"non_followers_percent": None})
    confirmed = deepcopy(original["post_candidate"])
    confirmed.update(published_at="2025-02-03T10:00:00+00:00", timezone="UTC",
                     published_at_precision={"kind": "approximate_minute"})
    supplement = {**event("author_publication_time_confirmation", "time-supplement"),
                  "platform": "threads", "parent_intake_id": original["intake_id"],
                  "snapshot_source_intake_id": original["intake_id"], "post_id": "example-post",
                  "snapshot_id": "example-snapshot", "post_candidate": confirmed}
    return original, supplement


if __name__ == "__main__":
    unittest.main()
