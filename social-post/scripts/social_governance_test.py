"""Native positive/negative controls for the isolated learning and author gate."""

from __future__ import annotations

import copy
import hashlib
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from social_cohorts import channel_inventory, media_family
from social_data import comparables_context, feature_matrix, validate_store
from social_data_feature_matrix_test import _post, _snapshot
from social_governance_store import digest, learning_events, private_path
from social_learning import activate, learning_overview, propose, record_reference, review
from social_reference_migration import migrate_external
from social_store import store_revision, write_jsonl
from social_writing_contract import active_contract, bootstrap, check_draft, verify_contract, writing_context
from workbench import WorkbenchHandler, WorkbenchServer
from workbench_service import WorkbenchService


def seed(root: Path) -> str:
    formulas = root / "references/formulas"
    formulas.mkdir(parents=True)
    for number in range(1, 31):
        (formulas / f"F{number:02}.md").write_text(f"# F{number}\n[Opening]\n[Mechanism]\n[One action]\n", encoding="utf-8")
    (formulas / "F06.md").write_text("# F6 | Mode B\n# F6a\nInvitation\n# F6b\n[Result]\n[Process]\n[Use]\n[One action]\n", encoding="utf-8")
    (formulas / "F15-mini.md").write_text("# F15 mini\n[Opening]\n[Mechanism]\n[One action]\n", encoding="utf-8")
    (root / "voice_quick.md").write_text("Real synthetic author voice; concise and factual.\n", encoding="utf-8")
    data = root / "data"
    data.mkdir()
    policy = {"schema_version": 1, "no_emoji": True, "plain_text": True, "formula_checks": {"F06b": {
        "paragraphs": 4, "no_links": True, "no_lists": True, "exclamations_first_only": True,
        "bare_endings_after_first": True}}}
    (data / "writing_policy.json").write_text(json.dumps(policy), encoding="utf-8")
    text = _post()
    video = copy.deepcopy(text)
    video.update(post_id="own-video", content_type="ai_short_drama", duration_seconds=30)
    video["format_features"].update(surface="reel_caption", facebook_background_style=False,
                                    video_orientation="vertical_9_16")
    write_jsonl(data / "posts.jsonl", [text, video])
    write_jsonl(data / "insight_snapshots.jsonl", [
        _snapshot("own-text-insight", "facebook", "2026-08-29T18:00:00+08:00", "developing", 100),
        _snapshot("own-video-insight", "instagram", "2026-08-29T18:00:00+08:00", "developing", 200, post_id="own-video"),
        _snapshot("combined-insight", "combined", "2026-08-29T18:00:00+08:00", "developing", 300, post_id="own-video"),
    ])
    return bootstrap(root)["revision"]


def reference(platform="instagram", family="video") -> dict:
    return {"reference_id": "external-example", "content_id": "one-content", "platform": platform,
            "media_family": family, "caption": "Exact external caption", "published_at": None,
            "captured_at": None, "metrics": {"views": None, "likes": 500},
            "metric_qualifiers": {"views": "not_reported", "likes": "exact"},
            "evidence": [{"source": "synthetic control", "capture_time_unknown": True}]}


def proposal_payload() -> dict:
    return {"title": "Scoped candidate", "target": "references/formulas/F21.md",
            "replacement_text": "# F21\n[Opening]\n[Concrete mechanism]\n[One action]\n",
            "scope": {"platform": "instagram", "media_family": "video"},
            "evidence_ids": ["external-example"], "reason": "Test hypothesis, not causal validation."}


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="social-governance-")
        self.root = Path(self.temp.name)
        self.revision = seed(self.root)
        self.own_revision = store_revision(self.root / "data")

    def tearDown(self):
        self.temp.cleanup()

    def candidate(self):
        record_reference(self.root, reference())
        return propose(self.root, proposal_payload())

    def approve(self, event):
        return review(self.root, event["proposal"]["proposal_id"], event["proposal_digest"], "approve",
                      "Reviewed full before/after and single external sample limitations.", owner_confirmed=True)

    def activate(self, event):
        return activate(self.root, event["proposal"]["proposal_id"], event["proposal_digest"], owner_confirmed=True)

    def test_ten_independent_channels_and_no_combined_platform_ranking(self):
        rows = feature_matrix(self.root)
        report = channel_inventory(rows, ("facebook", "instagram", "youtube", "threads", "x"))
        self.assertEqual(len(report["channels"]), 10)
        self.assertEqual(report["quarantined_rows"], 1)
        self.assertEqual(sum(row["post_count"] for row in report["channels"]), 2)
        self.assertFalse(report["cross_channel_ranking"])

    def test_cross_media_and_platform_queries_never_fall_back(self):
        for platform, family in (("facebook", "video"), ("instagram", "text_image")):
            result = comparables_context(self.root, platform=platform, media_family=family,
                                        content_type="ai_short_drama", surface="reel_caption", maturity="developing")
            self.assertEqual(result["comparables"], [])
        rows = feature_matrix(self.root, platform="instagram", media_family="video")
        self.assertEqual([row["post_id"] for row in rows], ["own-video"])

    def test_unknown_conflicting_media_and_external_own_import_rejected(self):
        self.assertEqual(media_family({"content_type": "unknown"}), "unknown")
        self.assertEqual(media_family({"content_type": "video", "media_family": "text_image"}), "unknown")
        for changes in ({"media_family": "video"}, {"media_family": "bad"}, {"owner_scope": "external"}):
            post = _post()
            post.update(changes)
            write_jsonl(self.root / "data/posts.jsonl", [post])
            self.assertFalse(validate_store(self.root)["valid"])

    def test_external_ingestion_keeps_unknown_time_and_never_changes_own_or_contract(self):
        record_reference(self.root, reference())
        record_reference(self.root, reference())
        result = learning_overview(self.root)
        self.assertEqual(len(result["external_references"]), 1)
        self.assertIsNone(result["external_references"][0]["published_at"])
        self.assertEqual(store_revision(self.root / "data"), self.own_revision)
        self.assertEqual(verify_contract(self.root)["revision"], self.revision)
        self.assertEqual(len(feature_matrix(self.root, platform="instagram")), 1)

    def test_external_identity_and_observation_overwrite_rejected(self):
        record_reference(self.root, reference())
        for candidate in ({**reference(), "post_id": "fake-own"}, {**reference(), "metrics": {"likes": 501}},
                          {**reference(), "media_family": "combined"}):
            with self.assertRaises(ValueError):
                record_reference(self.root, candidate)

    def test_all_installed_formula_sources_are_locked_and_read_in_full(self):
        _, document = active_contract(self.root)
        self.assertEqual(len([name for name in document["sources"] if "/F" in name]), 31)
        for number in range(1, 31):
            identity = "F06b" if number == 6 else f"F{number:02}"
            context = writing_context(self.root, identity, "B" if number == 6 else "C", "instagram", "video")
            self.assertEqual(context["formula_source"], document["sources"]["references/formulas/" + f"F{number:02}.md"]["text"])
        self.assertEqual(bootstrap(self.root)["revision"], self.revision)
        self.assertEqual(len(list((self.root / "data/author_contracts").iterdir())), 1)

    def test_direct_source_drift_blocks_context_bootstrap_and_handoff(self):
        (self.root / "references/formulas/F21.md").write_text("Unreviewed edit", encoding="utf-8")
        for action in (lambda: verify_contract(self.root), lambda: bootstrap(self.root),
                       lambda: writing_context(self.root, "F21", "C"),
                       lambda: WorkbenchService(self.root).task({"mode": "P2", "platform": "instagram",
                           "media_family": "video", "format": "C", "formula": "F21", "topic": "One real fact"})):
            with self.assertRaises(ValueError):
                action()

    def test_ambiguous_and_undocumented_f_variants_rejected(self):
        for identity in ("F06", "F06d", "../F06"):
            with self.assertRaises(ValueError):
                writing_context(self.root, identity, "B")
        with self.assertRaises(ValueError):
            writing_context(self.root, "F06b", "C")

    def test_unreviewed_new_rule_source_does_not_bypass_frozen_inventory(self):
        rules = self.root / "references/rules"
        rules.mkdir()
        (rules / "R99.md").write_text("Unapproved rule", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_contract(self.root)

    def test_f6b_native_structure_positive_and_negative_controls(self):
        text = "我做了一個工具！！\n\n花兩天完成測試\n\n說一句話就能啟動\n\n想試用的留言"
        check = lambda value: check_draft(self.root, value, "F06b", "B", self.revision, "facebook", "text_image")
        self.assertTrue(check(text)["structural_pass"])
        self.assertFalse(check(text)["delivery_ready"])
        variants = [text.rsplit("\n\n", 1)[0], text + "\n\n多一段", text + "。",
                    text.replace("測試", "測試！"), text + " https://example.org", text + "\U0001f600",
                    text.replace("花兩天", "1. 花兩天"), text.replace("完成測試", "**完成測試**")]
        for value in variants:
            self.assertFalse(check(value)["structural_pass"], value)

    def test_candidate_keeps_active_contract_unchanged_and_is_not_validation(self):
        event = self.candidate()
        self.assertEqual(verify_contract(self.root)["revision"], self.revision)
        self.assertEqual(event["proposal"]["evidence_claim"], "candidate_not_validated_rule")
        self.assertEqual(learning_overview(self.root)["proposals"][0]["state"], "pending")
        self.assertEqual(store_revision(self.root / "data"), self.own_revision)

    def test_bad_target_cross_scope_evidence_and_policy_weakening_rejected(self):
        record_reference(self.root, reference())
        policy = json.loads((self.root / "data/writing_policy.json").read_text())
        policy["no_emoji"] = False
        for changes in ({"target": "../secret"}, {"scope": {"platform": "facebook", "media_family": "video"}},
                        {"evidence_ids": ["missing"]}, {"evidence_ids": ["external-example", "external-example"]},
                        {"target": "data/writing_policy.json", "replacement_text": json.dumps(policy)}):
            with self.assertRaises(ValueError):
                propose(self.root, {**proposal_payload(), **changes})

    def test_no_owner_approval_wrong_digest_and_no_review_activation_rejected(self):
        event = self.candidate()
        identity = event["proposal"]["proposal_id"]
        with self.assertRaises(ValueError):
            review(self.root, identity, event["proposal_digest"], "approve", "No actual owner approval")
        with self.assertRaises(ValueError):
            review(self.root, identity, "0" * 64, "approve", "Wrong digest", owner_confirmed=True)
        with self.assertRaises(ValueError):
            self.activate(event)
        self.approve(event)
        self.assertEqual(verify_contract(self.root)["revision"], self.revision)
        with self.assertRaises(ValueError):
            activate(self.root, identity, event["proposal_digest"])

    def test_latest_rejection_revokes_prior_approval(self):
        event = self.candidate()
        self.approve(event)
        review(self.root, event["proposal"]["proposal_id"], event["proposal_digest"], "reject",
               "New evidence does not support adoption.", owner_confirmed=True)
        with self.assertRaises(ValueError):
            self.activate(event)

    def test_activation_is_scoped_retains_original_and_parent_and_blocks_replay(self):
        event = self.candidate()
        original = (self.root / event["proposal"]["target"]).read_bytes()
        self.approve(event)
        result = self.activate(event)
        self.assertEqual(result["previous_revision"], self.revision)
        self.assertEqual((self.root / event["proposal"]["target"]).read_bytes(), original)
        matching = writing_context(self.root, "F21", "C", "instagram", "video")
        self.assertEqual(matching["formula_source"], event["proposal"]["replacement_text"])
        for platform, family in (("facebook", "video"), ("instagram", "text_image")):
            self.assertEqual(writing_context(self.root, "F21", "C", platform, family)["formula_source"], original.decode())
        self.assertEqual(len(list((self.root / "data/author_contracts").iterdir())), 2)
        self.assertEqual(learning_overview(self.root)["proposals"][0]["state"], "activated")
        with self.assertRaises(ValueError):
            self.activate(event)
        with self.assertRaises(ValueError):
            check_draft(self.root, "Old draft", "F21", "C", self.revision)

    def test_concurrent_candidates_must_rebase_and_review_again(self):
        first = self.candidate()
        second = propose(self.root, proposal_payload())
        self.approve(first)
        self.approve(second)
        self.activate(first)
        with self.assertRaises(ValueError):
            self.activate(second)

    def test_edited_proposal_cannot_reuse_a_review_digest(self):
        event = self.candidate()
        self.approve(event)
        rows = learning_events(self.root)
        rows[1]["proposal"]["replacement_text"] += "Hidden change"
        write_jsonl(self.root / "data/learning_events.jsonl", rows)
        with self.assertRaises(ValueError):
            self.activate(event)

    def test_context_and_http_preserve_bound_contract_and_explicit_owner_steps(self):
        service = WorkbenchService(self.root)
        task = service.task({"mode": "P2", "platform": "instagram", "media_family": "video",
                             "format": "C", "formula": "F21", "topic": "A genuine observation"})
        self.assertEqual(task["writing_contract"]["revision"], self.revision)
        server = WorkbenchServer(self.root, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        headers = {"Content-Type": "application/json", "Origin": server.origin,
                   "Cookie": "sp_session=" + server.session, "X-Social-Post-CSRF": server.csrf}
        try:
            self.candidate()
            event = learning_overview(self.root)["proposals"][0]
            body = {"proposal_id": event["proposal"]["proposal_id"], "proposal_digest": event["proposal_digest"],
                    "decision": "approve", "notes": "Full synthetic owner review"}
            connection.request("POST", "/api/governance/review", json.dumps(body), {**headers, "X-Social-Post-CSRF": "wrong"})
            response = connection.getresponse(); response.read()
            self.assertEqual(response.status, 403)
            connection.request("POST", "/api/governance/review", json.dumps(body), headers)
            response = connection.getresponse(); response.read()
            self.assertEqual(response.status, 200)
            self.assertEqual(verify_contract(self.root)["revision"], self.revision)
            connection.request("POST", "/api/governance/activate", json.dumps({key: body[key] for key in
                               ("proposal_id", "proposal_digest")}), headers)
            response = connection.getresponse(); response.read()
            self.assertEqual(response.status, 200)
            self.assertNotEqual(verify_contract(self.root)["revision"], self.revision)
        finally:
            connection.close(); server.shutdown(); thread.join(5); server.server_close()


def run_governance_tests() -> None:
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(GovernanceTests))
    if not result.wasSuccessful():
        raise AssertionError("governance native controls failed")
    print("SOCIAL_GOVERNANCE_TESTS_PASS count=" + str(result.testsRun))


if __name__ == "__main__":
    run_governance_tests()
