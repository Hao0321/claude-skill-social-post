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
        self.assertEqual(row["missing"], ["capture_datetime"])
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
        self.assertEqual(lookup["other-intake"]["capture_source"], "canonical")
        self.assertEqual(lookup["other-intake"]["captured_at"], canonical["captured_at"])
        self.assertEqual(len(feature_matrix(self.root)), 1)

    def test_rejects_identity_conflicts_and_bad_clock(self):
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
                with self.assertRaises(ValueError):
                    review(self.root)

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
        self.assertEqual(row["missing"], ["capture_datetime", "complete_caption_analysis"])


if __name__ == "__main__":
    unittest.main()
