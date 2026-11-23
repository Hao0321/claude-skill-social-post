"""Positive/negative/restart replay for private partial-content learning."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from review_outcome_intakes import collect_events, read_inputs, review
from review_outcome_intakes_test import pending_thread
from social_data import feature_matrix
from social_intake_analysis import record_analysis
from social_store import write_jsonl


class IntakeAnalysisTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="social-post-analysis-test-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        original, confirmed = pending_thread()
        image = self.root / "data/evidence/example/01.jpg"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"fictional-evidence-fixture-not-an-image")
        self.evidence = {"path": "data/evidence/example/01.jpg",
                         "sha256": hashlib.sha256(image.read_bytes()).hexdigest()}
        original["evidence"] = [self.evidence]
        for row in (original, confirmed):
            row["post_candidate"]["caption_transcription_notes"] = {"visible_following_phrases": ["Free"]}
        self.original, self.confirmed = original, confirmed
        self.seed(original, confirmed)
        self.payload = {"analysis_id": "fictional-analysis-v1", "source_intake_id": original["intake_id"],
                        "post_id": "example-post", "snapshot_id": "example-snapshot", "platform": "threads",
                        "media_family": "text_image", "caption_sha256": original["post_candidate"]["caption_sha256"],
                        "content_scope": "visible_first_post", "recorded_at": "2025-02-04T10:00:00+00:00",
                        "phrases": [{"text": "Prototype", "role": "use_case", "interpretation": "Example use.",
                                     "basis": "caption_exact"},
                                    {"text": "Free", "role": "cost_benefit", "interpretation": "Author claim only.",
                                     "basis": "visible_transcription"}],
                        "evidence": [self.evidence], "structure": ["Short opening; continuation unavailable."],
                        "hypotheses": ["A concrete benefit could help readers decide relevance."],
                        "confounds": ["No control; capture time missing."],
                        "next_test": ["Same platform and maturity; vary one element."],
                        "candidates": [{"candidate_id": "fictional-benefit", "statement": "Try a specific benefit.",
                                        "exclusions": "Not an active formula or causal claim.", "next_test": "Paired replay."}]}

    def seed(self, *rows):
        write_jsonl(self.root / "data/outcome_intakes.jsonl", list(rows))

    def record(self, value=None, write=True):
        path = self.root / "analysis.json"
        path.write_text(json.dumps(self.payload if value is None else value), encoding="utf-8")
        return record_analysis(self.root, path, lambda: collect_events(read_inputs(self.root)[0])[0], write=write)

    def test_dry_run_append_restart_and_idempotence(self):
        original = (self.root / "data/outcome_intakes.jsonl").read_bytes()
        self.assertEqual(self.record(write=False)["status"], "dry_run")
        self.assertFalse((self.root / "data/learning_events.jsonl").exists())
        self.assertEqual(self.record()["status"], "appended")
        ledger = (self.root / "data/learning_events.jsonl").read_bytes()
        self.assertEqual(self.record()["status"], "already_recorded")
        self.assertEqual((self.root / "data/learning_events.jsonl").read_bytes(), ledger)
        self.assertNotIn("content_analyses", review(self.root)["post_observations"][0])
        row, = review(Path(str(self.root)), include_analysis=True)["post_observations"]
        analysis, = row["content_analyses"]
        self.assertEqual(analysis["phrases"][1]["text"], "Free")
        self.assertFalse(analysis["aggregation_eligible"])
        self.assertFalse(row["caption_analysis_complete"])
        self.assertNotIn("capture_datetime", row["missing"])
        self.assertEqual(feature_matrix(self.root), [])
        self.assertEqual((self.root / "data/outcome_intakes.jsonl").read_bytes(), original)

    def test_negative_controls(self):
        for key, value in (("post_id", "other"), ("snapshot_id", "other"), ("platform", "facebook"),
                           ("media_family", "video"), ("caption_sha256", "0" * 64),
                           ("source_intake_id", "missing"), ("content_scope", "complete_caption")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.record({**self.payload, key: value})
        for phrase in ({"text": "Unknown", "role": "topic", "interpretation": "No evidence.", "basis": "caption_exact"},
                       {"text": "Free", "role": "cost_benefit", "interpretation": "Wrong hash scope.", "basis": "caption_exact"},
                       {"text": "Unknown", "role": "topic", "interpretation": "Guessed from UI.", "basis": "visible_transcription"}):
            with self.assertRaises(ValueError):
                self.record({**self.payload, "phrases": [phrase]})
        with self.assertRaises(ValueError):
            self.record({**self.payload, "evidence": [{**self.evidence, "path": "../outside.jpg"}]})
        self.record()
        with self.assertRaises(ValueError):
            self.record({**self.payload, "structure": ["Changed same ID."]})

    def test_tampered_source_and_event_are_not_silent(self):
        self.record()
        (self.root / self.evidence["path"]).write_bytes(b"changed-evidence")
        with self.assertRaises(ValueError):
            review(self.root, include_analysis=True)
        # Basic review does not consume the private annotations.
        self.assertEqual(review(self.root)["unique_post_count"], 1)
        path = self.root / "data/learning_events.jsonl"
        row = json.loads(path.read_text(encoding="utf-8"))
        row["analysis_digest"] = "0" * 64
        write_jsonl(path, [row])
        with self.assertRaises(ValueError):
            review(self.root, include_analysis=True)

    def test_new_revision_replaces_effective_text_but_preserves_history(self):
        self.record()
        revision = {**self.payload, "analysis_id": "fictional-analysis-v2",
                    "supersedes_analysis_id": self.payload["analysis_id"],
                    "confounds": ["Current interpretation; source and claims remain bounded."]}
        self.assertEqual(self.record(revision)["status"], "appended")
        row, = review(self.root, include_analysis=True)["post_observations"]
        self.assertEqual([a["analysis_id"] for a in row["content_analyses"]], ["fictional-analysis-v2"])
        raw = (self.root / "data/learning_events.jsonl").read_bytes()
        self.assertIn(b"fictional-analysis-v1", raw)
        self.assertEqual(self.record(revision)["status"], "already_recorded")
        self.assertEqual((self.root / "data/learning_events.jsonl").read_bytes(), raw)
        with self.assertRaises(ValueError):
            self.record({**revision, "analysis_id": "branch-from-superseded-parent"})

    def test_revision_requires_an_existing_parent_with_same_scope(self):
        with self.assertRaises(ValueError):
            self.record({**self.payload, "supersedes_analysis_id": "missing"})


if __name__ == "__main__":
    unittest.main()
