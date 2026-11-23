#!/usr/bin/env python3
"""Isolated canary authorization tests: no Chrome and no active ledger writes."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from comment_browser_common import _json_digest
from comment_browser_send_contract import CANARY_COMPOSER_FIELDS, validate_browser_preflight
from comment_canary import canary_settlement_allowed, require_canary_lease
from comment_state import validate_comment_store
from comment_store import load_comment_records
from comment_test_browser_adapter import LocalFixtureCommentAdapter
from comment_test_browser_contract_support import (
    PREPARATION_CORE_KEYS, SESSION_ID, bound_preflight_for, capture_receipt_commit,
    ingest_browser_scan, intent_state, reinspection_for,
    scan_envelope, write_json,
)
from comment_test_cli import draft_cli_fixture, ingest_cli_fixture, prepare_cli_fixture, run_cli
from comment_test_support import POLICY
from social_primitives import parse_time


@contextmanager
def fixture(platform: str = "facebook", *, mention: bool = False):
    with tempfile.TemporaryDirectory(prefix="social-canary-only-test-") as raw:
        root = Path(raw)
        script, _unused = prepare_cli_fixture(root, live_browser_actuation_enabled=True)
        adapter = LocalFixtureCommentAdapter(platform)
        scan = scan_envelope(adapter)
        if platform == "instagram":
            scan["comments"][0]["author_key"] = "fixture_reader"
        comment = ingest_browser_scan(script, root, scan)
        reply = "@fixture_reader Thanks for reading!" if mention else "Thanks for reading!"
        run_cli(script, root, "draft", "--comment-key", comment["comment_key"], "--session-id", SESSION_ID,
                "--text", reply, "--classification", "positive_reaction", "--risk", "low",
                "--confidence", "0.99", "--language", "en", "--write")
        reply_path = root / "data/reply_events.jsonl"
        intent = json.loads(reply_path.read_text(encoding="utf-8").splitlines()[0])["intent_id"]
        run_cli(script, root, "approve", "--intent-id", intent, "--session-id", SESSION_ID,
                "--approval-mode", "batch_confirm", "--write")
        action = json.loads(run_cli(script, root, "browser-action", "--intent-id", intent, "--session-id", SESSION_ID).stdout)
        # Only this temporary fixture policy is changed; production stays off.
        policy_path = root / "references/comment-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["live_browser_actuation_enabled"] = False
        write_json(policy_path, policy)
        yield root, script, comment, intent, action


def issue(root: Path, script: Path, intent: str, *extra: str, expected: int = 0):
    result = run_cli(script, root, "browser-canary-lease", "--intent-id", intent,
                     "--session-id", SESSION_ID, "--authorization-basis", "current_session_user_instruction",
                     *extra, expected=expected)
    lines = [line.removeprefix("CANARY_LEASE ") for line in result.stdout.splitlines() if line.startswith("CANARY_LEASE ")]
    return json.loads(lines[0]) if lines else None


def begin(root: Path, script: Path, action: dict, lease: dict, *, receipt: dict | None = None,
          write: bool = True, expected: int = 0):
    source = root / "canary-preflight.json"
    write_json(source, receipt or bound_preflight_for(action))
    result = run_cli(script, root, "browser-begin", str(source), "--intent-id", action["intent_id"],
                     "--session-id", SESSION_ID, "--canary-lease-id", lease["lease_id"],
                     *(("--write",) if write else ()), expected=expected)
    claims = [line.removeprefix("SUBMIT_CLAIM ") for line in result.stdout.splitlines() if line.startswith("SUBMIT_CLAIM ")]
    return json.loads(claims[0]) if claims else None


def native_preflight(action: dict) -> dict:
    raw = bound_preflight_for(action)
    raw["observed_url"] = action["comment_anchor"]["comment_permalink"]
    prefix = f"@{action['author_key']} "
    evidence = {
        "schema_version": 1, "action_digest": _json_digest(action), "observed_url": raw["observed_url"],
        "comment_key": action["scope"]["comment_key"], "platform_comment_id": action["comment_anchor"]["platform_comment_id"],
        "author_key": action["author_key"],
        "document_binding": {
            "schema_version": 1, "kind": "source_owned_ui_continuity", "tab_id": "fixture-tab-1",
            "observed_url": raw["observed_url"],
            "target_digest": _json_digest({
                "account_key": action["scope"]["account_key"].removeprefix("@"),
                "comment_permalink": action["comment_anchor"]["comment_permalink"],
                "author_key": action["author_key"], "body": action["expected_body"],
            }),
        },
        "trigger_locator_digest": _json_digest({
            "platform_comment_id": action["comment_anchor"]["platform_comment_id"],
            "comment_permalink": action["comment_anchor"]["comment_permalink"],
            "author_key": action["author_key"], "expected_body": action["expected_body"], "role": "button", "name": "回覆",
        }),
        "composer_node_id": "fixture-node-1", "initial_text": prefix,
    }
    raw.update(composer_empty_before_fill=False, composer_initial_state="native_target_mention",
               composer_initial_text=prefix, selected_parent_evidence=evidence,
               selected_parent_evidence_digest=_json_digest(evidence))
    return rebind(raw)


def rebind(raw: dict) -> dict:
    raw["preparation_id"] = _json_digest({key: raw[key] for key in (*PREPARATION_CORE_KEYS, *CANARY_COMPOSER_FIELDS) if key in raw})
    return raw


def semantic_native_preflight(action: dict) -> dict:
    raw = native_preflight(action)
    evidence = raw["selected_parent_evidence"]
    del evidence["composer_node_id"]
    evidence.update(schema_version=2, selection_kind="source_clicked_instagram_native_reply",
                    composer_scope="unique_native_post_form", stable_reads=2)
    raw["selected_parent_evidence_digest"] = _json_digest(evidence)
    return rebind(raw)


class CanaryLeaseTests(unittest.TestCase):
    def test_legacy_raw_observation_cannot_issue_canary(self):
        with tempfile.TemporaryDirectory(prefix="social-canary-legacy-") as raw:
            root = Path(raw)
            script, source = prepare_cli_fixture(root)
            comment = ingest_cli_fixture(script, root, source)
            _path, intent = draft_cli_fixture(script, root, comment)
            run_cli(script, root, "approve", "--intent-id", intent, "--session-id", SESSION_ID,
                    "--approval-mode", "batch_confirm", "--write")
            before = (root / "data/reply_events.jsonl").read_bytes()
            issue(root, script, intent, "--write", expected=2)
            self.assertEqual((root / "data/reply_events.jsonl").read_bytes(), before)

    def test_dry_run_and_normal_send_remain_hard_off(self):
        with fixture() as (root, script, _comment, intent, action):
            ledger = root / "data/reply_events.jsonl"
            before = ledger.read_bytes()
            self.assertIsNone(issue(root, script, intent))
            self.assertEqual(ledger.read_bytes(), before)
            for ttl in ("0", "301", "-1"):
                issue(root, script, intent, "--ttl-seconds", ttl, "--write", expected=2)
            self.assertEqual(ledger.read_bytes(), before)
            lease = issue(root, script, intent, "--write")
            self.assertEqual(lease["maximum_actions"], 1)
            self.assertLessEqual(parse_time(lease["expires_at"]), parse_time(action["expires_at"]))
            issue(root, script, intent, "--write", expected=2)
            source = root / "normal.json"
            write_json(source, bound_preflight_for(action))
            rejected = run_cli(script, root, "browser-begin", str(source), "--intent-id", intent,
                               "--session-id", SESSION_ID, "--write", expected=2)
            self.assertIn("disabled by policy", rejected.stderr)

    def test_claim_is_one_shot_and_check_binds_exact_session_action_and_claim(self):
        with fixture() as (root, script, _comment, intent, action):
            lease = issue(root, script, intent, "--write")
            checked = run_cli(script, root, "browser-action", "--intent-id", intent, "--session-id", SESSION_ID,
                              "--canary-lease-id", lease["lease_id"])
            self.assertEqual(json.loads(checked.stdout), action)
            begin(root, script, action, lease, write=False)
            self.assertFalse(intent_state(root, intent)["canary_lease"]["consumed"])
            claim = begin(root, script, action, lease)
            self.assertTrue(intent_state(root, intent)["canary_lease"]["consumed"])
            check = ("browser-canary-check", "--intent-id", intent, "--session-id", SESSION_ID,
                     "--canary-lease-id", lease["lease_id"])
            result = run_cli(script, root, *check, "--claim-id", claim["claim_id"])
            self.assertEqual(json.loads(result.stdout)["decision"], "CANARY_CLAIMED")
            run_cli(script, root, *check, expected=2)
            run_cli(script, root, *check, "--claim-id", "wrong", expected=2)
            before = (root / "data/reply_events.jsonl").read_bytes()
            begin(root, script, action, lease, expected=2)
            self.assertEqual((root / "data/reply_events.jsonl").read_bytes(), before)

    def test_expiry_source_and_wrong_binding_fail_closed(self):
        with fixture() as (root, script, _comment, intent, action):
            lease = issue(root, script, intent, "--write")
            state = intent_state(root, intent)
            for moment in (parse_time(lease["expires_at"]), parse_time(lease["issued_at"]) - timedelta(seconds=1)):
                with self.assertRaises(ValueError):
                    require_canary_lease(state, lease["lease_id"], intent, SESSION_ID, action=action, now=moment)
            with patch("comment_canary.canary_source_digest", return_value="0" * 64), self.assertRaisesRegex(ValueError, "source changed"):
                require_canary_lease(state, lease["lease_id"], intent, SESSION_ID, action=action)
            for lease_id, session, candidate in (("0" * 32, SESSION_ID, action), (lease["lease_id"], "other-session", action),
                                                  (lease["lease_id"], SESSION_ID, dict(action, reply_text="Changed"))):
                with self.assertRaises(ValueError):
                    require_canary_lease(state, lease_id, intent, session, action=candidate)

    def test_competing_claim_processes_commit_only_one_attempt(self):
        with fixture() as (root, script, _comment, intent, action):
            lease = issue(root, script, intent, "--write")
            source = root / "race-preflight.json"
            write_json(source, bound_preflight_for(action))
            argv = [sys.executable, str(script), "browser-begin", str(source), "--intent-id", intent,
                    "--session-id", SESSION_ID, "--canary-lease-id", lease["lease_id"], "--root", str(root), "--write"]
            children = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         text=True, encoding="utf-8", shell=False) for _ in range(2)]
            outputs = [child.communicate(timeout=20) for child in children]
            self.assertEqual(sorted(child.returncode for child in children), [0, 2])
            self.assertEqual(sum(stdout.count("SUBMIT_CLAIM ") for stdout, _stderr in outputs), 1)
            records = load_comment_records(root / "data")
            self.assertEqual(sum(row["event_type"] == "send_started" for row in records["replies"]), 1)

    def test_replay_rejects_duplicate_tampered_or_unissued_lease(self):
        with fixture() as (root, script, _comment, intent, action):
            lease = issue(root, script, intent, "--write")
            begin(root, script, action, lease)
            records = load_comment_records(root / "data")
            cases = []
            duplicate = deepcopy(records["replies"])
            duplicate.insert(-1, dict(duplicate[-2], audit_id="different-audit"))
            cases.append(duplicate)
            for key, value in (("browser_canary_lease_id", "0" * 32), ("browser_canary_lease_digest", "0" * 64)):
                changed = deepcopy(records["replies"])
                changed[-1][key] = value
                cases.append(changed)
            cases.append([row for row in records["replies"] if row["event_type"] != "browser_canary_lease_issued"])
            forged = deepcopy(records["replies"])
            forged[-2]["canary_lease"]["session_id"] = "other-session"
            forged[-2]["canary_lease"]["lease_digest"] = _json_digest({key: value for key, value in forged[-2]["canary_lease"].items() if key != "lease_digest"})
            cases.append(forged)
            for rows in cases:
                self.assertFalse(validate_comment_store(records["comments"], rows, POLICY)["valid"])

    def test_finish_and_reconcile_stay_available_only_for_claimed_canary(self):
        with fixture() as (root, script, _comment, intent, action):
            lease = issue(root, script, intent, "--write")
            claim = begin(root, script, action, lease)
            state = intent_state(root, intent)
            with self.assertRaises(ValueError):
                require_canary_lease(state, lease["lease_id"], intent, SESSION_ID, claim_id=claim["claim_id"], now=parse_time(lease["expires_at"]))
            with patch("comment_canary.canary_source_digest", side_effect=AssertionError("settlement must not read new source")):
                self.assertTrue(canary_settlement_allowed(state))
            recovery = run_cli(script, root, "browser-recovery-action", "--intent-id", intent,
                               "--session-id", "fixture-recovery-session")
            recovery_attempt = json.loads(recovery.stdout)["attempt"]
            self.assertEqual(recovery_attempt["canary_lease_id"], lease["lease_id"])
            self.assertEqual(recovery_attempt["canary_lease_digest"], lease["lease_digest"])
            receipt = {
                **reinspection_for(action, state["attempt"], found=False),
                "submission_attempted": True, "submission_possible": True,
                "post_submit_total_reply_count": 0,
            }
            source = root / "finish.json"
            write_json(source, {"provenance": claim["receipt_capability"], "receipt": receipt})
            finished = run_cli(script, root, "browser-finish", str(source), "--intent-id", intent, "--session-id", SESSION_ID, "--write")
            commit = capture_receipt_commit(root, intent, finished.stdout)
            self.assertEqual(intent_state(root, intent)["status"], "needs_reconcile")
            write_json(source, {"provenance": commit["next_capability"], "receipt": reinspection_for(action, state["attempt"], found=False)})
            run_cli(script, root, "browser-reconcile", str(source), "--intent-id", intent, "--session-id", SESSION_ID, "--write")
            self.assertEqual(intent_state(root, intent)["status"], "reconciled_not_sent")
            run_cli(script, root, "browser-action", "--intent-id", intent, "--session-id", SESSION_ID, "--canary-lease-id", lease["lease_id"], expected=2)

    def test_native_mention_requires_canary_exact_parent_evidence_and_bound_preparation(self):
        with fixture("instagram", mention=True) as (root, script, comment, intent, action):
            lease = issue(root, script, intent, "--write")
            state = intent_state(root, intent)
            receipt = native_preflight(action)
            def validate(raw, lease_id=lease["lease_id"]):
                return validate_browser_preflight(raw, {comment["comment_key"]: comment}, {comment["comment_key"]: state}, POLICY, intent, SESSION_ID, canary_lease_id=lease_id)
            validate(receipt)
            with self.assertRaises(ValueError):
                validate(receipt, None)
            bare = bound_preflight_for(action)
            bare["composer_empty_before_fill"] = False
            with self.assertRaises(ValueError):
                validate(bare)
            for changes in ({"composer_initial_text": "@other "}, {"composer_empty_before_fill": True},
                            {"selected_parent_evidence_digest": "0" * 64}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    validate(rebind({**receipt, **changes}))
            for field, value in (("author_key", "other"), ("platform_comment_id", "other"), ("document_epoch", 123456789),
                                 ("composer_node_id", ""), ("trigger_locator_digest", "0" * 64)):
                bad = deepcopy(receipt)
                bad["selected_parent_evidence"][field] = value
                bad["selected_parent_evidence_digest"] = _json_digest(bad["selected_parent_evidence"])
                with self.subTest(field=field), self.assertRaises(ValueError):
                    validate(rebind(bad))
            for field, value in (("schema_version", True), ("kind", "physical_document_epoch"), ("tab_id", ""),
                                 ("observed_url", action["post_permalink"]), ("target_digest", "0" * 64)):
                bad = deepcopy(receipt)
                bad["selected_parent_evidence"]["document_binding"][field] = value
                bad["selected_parent_evidence_digest"] = _json_digest(bad["selected_parent_evidence"])
                with self.subTest(binding_field=field), self.assertRaises(ValueError):
                    validate(rebind(bad))
            begin(root, script, action, lease, receipt=receipt)
            attempt = intent_state(root, intent)["attempt"]
            self.assertEqual(attempt["browser_composer_initial_text"], "@fixture_reader ")

    def test_native_mention_cannot_change_an_approved_reply_without_prefix(self):
        with fixture("instagram") as (root, script, _comment, _intent, action):
            lease = issue(root, script, action["intent_id"], "--write")
            begin(root, script, action, lease, receipt=native_preflight(action), expected=2)

    def test_semantic_native_mention_preserves_legacy_and_rejects_false_selection(self):
        with fixture("instagram", mention=True) as (root, script, comment, intent, action):
            lease = issue(root, script, intent, "--write")
            state = intent_state(root, intent)
            def validate(raw, lease_id=lease["lease_id"]):
                return validate_browser_preflight(raw, {comment["comment_key"]: comment},
                    {comment["comment_key"]: state}, POLICY, intent, SESSION_ID, canary_lease_id=lease_id)
            # The same canonical action, lease and evaluator accept both the
            # unchanged historical v1 and the explicitly semantic v2 contract.
            validate(native_preflight(action))
            receipt = semantic_native_preflight(action)
            validated = validate(receipt)
            self.assertEqual(validated["selected_parent_evidence"]["schema_version"], 2)
            self.assertNotIn("composer_node_id", validated["selected_parent_evidence"])
            before = (root / "data/reply_events.jsonl").read_bytes()
            with self.assertRaises(ValueError):
                validate(receipt, None)
            for field, value in (
                ("schema_version", True), ("schema_version", 1), ("schema_version", 3),
                ("selection_kind", "mention_prefill_only"),
                ("selection_kind", "source_clicked_threads_native_reply"),
                ("composer_scope", "any_visible_editor"), ("stable_reads", 0),
                ("stable_reads", 1), ("stable_reads", True), ("stable_reads", "2"),
                ("composer_node_id", "invented-node"), ("document_epoch", "invented-epoch"),
                ("author_key", "another_reader"), ("platform_comment_id", "another_parent"),
                ("comment_key", "another_comment"), ("action_digest", "0" * 64),
                ("observed_url", action["post_permalink"]), ("initial_text", "@another_reader "),
                ("trigger_locator_digest", "0" * 64),
            ):
                bad = deepcopy(receipt)
                bad["selected_parent_evidence"][field] = value
                bad["selected_parent_evidence_digest"] = _json_digest(bad["selected_parent_evidence"])
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate(rebind(bad))
            for field in ("selection_kind", "composer_scope", "stable_reads"):
                bad = deepcopy(receipt)
                del bad["selected_parent_evidence"][field]
                bad["selected_parent_evidence_digest"] = _json_digest(bad["selected_parent_evidence"])
                with self.subTest(missing=field), self.assertRaises(ValueError):
                    validate(rebind(bad))
            for field, value in (("kind", "physical_document_epoch"), ("tab_id", ""),
                                 ("target_digest", "0" * 64), ("observed_url", action["post_permalink"])):
                bad = deepcopy(receipt)
                bad["selected_parent_evidence"]["document_binding"][field] = value
                bad["selected_parent_evidence_digest"] = _json_digest(bad["selected_parent_evidence"])
                with self.subTest(binding_field=field), self.assertRaises(ValueError):
                    validate(rebind(bad))
            for changes in ({"composer_initial_text": "@another_reader "},
                            {"composer_empty_before_fill": True},
                            {"selected_parent_evidence_digest": "0" * 64}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    validate(rebind({**receipt, **changes}))
            stale_digest = deepcopy(receipt)
            stale_digest["selected_parent_evidence"]["document_binding"]["tab_id"] = "different-tab"
            stale_digest["selected_parent_evidence_digest"] = _json_digest(stale_digest["selected_parent_evidence"])
            with self.assertRaisesRegex(ValueError, "preparation_id integrity"):
                validate(stale_digest)
            self.assertEqual((root / "data/reply_events.jsonl").read_bytes(), before)
            # Exercise the real isolated CLI claim after all negatives; the
            # persisted attempt keeps v2 rather than inventing a legacy node ID.
            begin(root, script, action, lease, receipt=receipt)
            attempt = intent_state(root, intent)["attempt"]
            self.assertEqual(attempt["browser_selected_parent_evidence"]["schema_version"], 2)
            self.assertNotIn("composer_node_id", attempt["browser_selected_parent_evidence"])


def run_canary_tests() -> None:
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CanaryLeaseTests))
    if not result.wasSuccessful():
        raise AssertionError("canary lease tests failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
