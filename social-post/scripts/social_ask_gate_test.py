#!/usr/bin/env python3
"""Regression lock: agents may not ask for capture time or for data already on record."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from review_outcome_intakes import review
from review_outcome_intakes_test import base, caption_event
from social_ask_gate import ASK, BLOCK_RECORDED, BLOCK_RETIRED, check, main
from social_store import write_jsonl


class AskGateTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="social-post-ask-gate-test-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def seed(self, *rows):
        write_jsonl(self.root / "data" / "outcome_intakes.jsonl", list(rows))

    def statuses(self, *items, post="example-post"):
        return {row["item"]: row["status"] for row in check(self.root, post, list(items))["items"]}

    def test_capture_time_is_blocked_in_every_spelling_even_without_records(self):
        items = ["screenshot_time", "captured_at", "capture_datetime", "hours_since_publish",
                 "maturity", "截圖時間", "幾點截圖", "狀態列時間"]
        self.assertEqual(set(self.statuses(*items).values()), {BLOCK_RETIRED})

    def test_recorded_time_caption_and_metric_are_never_asked_again(self):
        intake = base()
        intake["evidence"] = [{"path": "data/evidence/example/01.jpg", "sha256": "0" * 64}]
        self.seed(intake, caption_event())
        report = check(self.root, "example-post", ["發布時間", "全文", "views", "link_clicks"])
        statuses = {row["item"]: row["status"] for row in report["items"]}
        self.assertEqual(statuses, {"發布時間": BLOCK_RECORDED, "全文": BLOCK_RECORDED,
                                    "views": BLOCK_RECORDED, "link_clicks": ASK})
        self.assertEqual(report["decision"], "BLOCK")
        self.assertIn("data/evidence/example/01.jpg", report["evidence_to_check_first"])

    def test_truly_missing_items_may_be_asked_only_after_evidence(self):
        self.seed(base())
        report = check(self.root, "example-post", ["complete_caption_analysis", "link_clicks"])
        self.assertEqual(report["decision"], ASK)
        self.assertTrue(any("evidence" in rule for rule in report["rules"]))

    def test_review_missing_list_never_contains_capture_time(self):
        self.seed(base())
        for row in review(self.root)["post_observations"]:
            self.assertLessEqual(set(row["missing"]),
                                 {"publication_datetime", "complete_caption_analysis"})
            self.assertFalse(any(self.statuses(item).get(item) == BLOCK_RETIRED
                                 for item in row["missing"]))

    def test_cli_exit_codes(self):
        self.seed(base())
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["--root", str(self.root), "--post", "example-post", "截圖時間"]), 2)
        self.assertEqual(json.loads(output.getvalue())["decision"], "BLOCK")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "--post", "example-post", "link_clicks"]), 0)


if __name__ == "__main__":
    unittest.main()
