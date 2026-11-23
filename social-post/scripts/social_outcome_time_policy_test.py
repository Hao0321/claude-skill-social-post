"""Publication-only ingestion, old-clock invariance and repeated observations."""

import copy
import tempfile
import unittest
from pathlib import Path

from log_outcome import prepare_records, validate_staged
from review_outcome_intakes import review
from review_outcome_intakes_test import base, caption_event, post
from social_data import (comparables_context, feature_matrix, observation_history,
                         validate_store, validation_json_view)
from social_learning import learning_overview, record_reference
from social_outcome_time_policy import RETIRED_CAPTURE_FIELDS
from social_store import commit_records, write_jsonl


class PublicationOnlyTimeTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="social-publication-time-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def snapshot(self, identity="observation-1", views=100, platform="facebook", **extra):
        return {"schema_version": "1.0", "snapshot_id": identity, "post_id": "example-post",
                "platform_scope": platform, "metrics": {"views": views, "comments": None}, **extra}

    def seed(self, snapshots):
        row = post("example-post", "A concrete task and benefit.")
        row["platforms"] = ["facebook", "instagram"]
        write_jsonl(self.root / "data/posts.jsonl", [row])
        write_jsonl(self.root / "data/insight_snapshots.jsonl", snapshots)

    def assert_no_capture_fields(self, value):
        if isinstance(value, dict):
            self.assertFalse(set(value) & RETIRED_CAPTURE_FIELDS)
            for child in value.values():
                self.assert_no_capture_fields(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_no_capture_fields(child)

    def test_missing_capture_accepts_preview_commit_and_reopen(self):
        bundle = {"post": post("example-post", "A concrete task and benefit."),
                  "snapshot": self.snapshot()}
        records, normalized, revision = prepare_records(bundle, self.root / "data")
        validate_staged(records)
        commit_records(records, data_dir=self.root / "data", expected_revision=revision)
        self.assertTrue(validate_store(Path(str(self.root)))["valid"])
        self.assertEqual(feature_matrix(self.root)[0]["outcome"]["metrics"]["views"], 100)
        self.assert_no_capture_fields(normalized)

    def test_all_old_clock_mutations_leave_analytics_invariant(self):
        self.seed([self.snapshot()])
        expected = feature_matrix(self.root)
        for clock in (None, "not-a-time", "1900-01-01", "2099-01-01T00:00:00+00:00", {"untrusted": True}):
            with self.subTest(clock=clock):
                self.seed([self.snapshot(captured_at=clock, captured_at_confidence="invalid",
                                         hours_since_publish=-100, maturity="untrusted",
                                         capture_context={"status_bar_time": "01:33"})])
                self.assertTrue(validate_store(self.root)["valid"])
                self.assertEqual(feature_matrix(self.root), expected)
                self.assert_no_capture_fields(validation_json_view(validate_store(self.root)))

    def test_second_input_is_latest_and_first_is_retained_without_clock(self):
        observations = [self.snapshot("first", 100, observation_label="publication day"),
                        self.snapshot("second", 350, observation_label="next day")]
        self.seed(observations)
        raw = (self.root / "data/insight_snapshots.jsonl").read_bytes()
        latest, = feature_matrix(self.root)
        self.assertEqual(latest["snapshot_id"], "second")
        history = observation_history(self.root, "example-post")
        self.assertEqual([r["snapshot_id"] for r in history["observations"]], ["first", "second"])
        self.assertEqual(history["observations"][1]["count_delta_from_previous"], {"views": 250})
        self.assertEqual(history["observations"][1]["observation_label"], "next day")
        self.assertIsNone(history["growth_rate_per_hour"])
        self.assertEqual((self.root / "data/insight_snapshots.jsonl").read_bytes(), raw)

    def test_clock_order_never_overrides_input_order_and_platforms_do_not_mix(self):
        self.seed([self.snapshot("old-input", 100, captured_at="2099-01-01T00:00:00+00:00"),
                   self.snapshot("ig-input", 900, platform="instagram"),
                   self.snapshot("new-input", 50, captured_at="1900-01-01T00:00:00+00:00")])
        result = {r["platform"]: r for r in feature_matrix(self.root)}
        self.assertEqual(result["facebook"]["snapshot_id"], "new-input")
        self.assertEqual(result["instagram"]["outcome"]["metrics"]["views"], 900)
        history = observation_history(self.root, "example-post", platform="facebook")
        self.assertEqual(history["observations"][1]["count_delta_from_previous"], {"views": -50})
        self.assert_no_capture_fields(result)

    def test_unknown_and_ineligible_observations_do_not_hide_known_outcome(self):
        self.seed([self.snapshot("known", 100), self.snapshot("unknown", None, measurement_status="awaiting_data"),
                   self.snapshot("excluded", 999, aggregation_eligible=False)])
        self.assertEqual(feature_matrix(self.root)[0]["snapshot_id"], "known")
        history = observation_history(self.root, "example-post")
        self.assertEqual(len(history["observations"]), 3)
        self.assertFalse(history["observations"][1]["outcome_eligible"])
        self.assertEqual(history["observations"][2]["count_delta_from_previous"], {})

    def test_publication_identity_and_numeric_validation_are_not_relaxed(self):
        self.seed([self.snapshot()])
        for key, value in (("published_at", "bad"), ("caption_sha256", "0" * 64)):
            row = post("example-post", "A concrete task and benefit.")
            row[key] = value
            write_jsonl(self.root / "data/posts.jsonl", [row])
            self.assertFalse(validate_store(self.root)["valid"])
        self.seed([self.snapshot(views=-1)])
        self.assertFalse(validate_store(self.root)["valid"])
        self.seed([self.snapshot(), self.snapshot()])
        self.assertFalse(validate_store(self.root)["valid"])

    def test_comparison_and_account_need_no_screenshot_or_maturity(self):
        self.seed([self.snapshot()])
        result = comparables_context(self.root, platform="facebook", content_type="photo_post", surface="facebook_photo")
        self.assertTrue(result["comparison_policy"]["outcome_comparison_allowed"])
        self.assertFalse(result["comparison_policy"]["timing"]["causal_claim_allowed"])
        self.assert_no_capture_fields(result)
        write_jsonl(self.root / "data/account_snapshots.jsonl", [{
            "schema_version": "1.0", "account_snapshot_id": "window", "platform": "facebook",
            "window_days": 30, "metrics": {"views": 1500}}])
        self.assertTrue(validate_store(self.root)["valid"])

    def test_prior_intake_capture_and_external_clock_are_not_requirements(self):
        original = base()
        original["snapshot_observation"]["captured_at"] = "not-a-clock"
        write_jsonl(self.root / "data/outcome_intakes.jsonl", [original, caption_event()])
        row, = review(self.root)["post_observations"]
        self.assertEqual(row["missing"], [])
        self.assert_no_capture_fields(row)
        reference = {"reference_id": "external", "content_id": "external-post", "platform": "threads",
                     "media_family": "text_image", "caption": None, "published_at": None,
                     "metrics": {"likes": 10}, "metric_qualifiers": {}, "evidence": [{"kind": "fictional"}]}
        record_reference(self.root, reference)
        self.assertEqual(len(learning_overview(self.root)["external_references"]), 1)
        self.assert_no_capture_fields(learning_overview(self.root))


if __name__ == "__main__":
    unittest.main()
