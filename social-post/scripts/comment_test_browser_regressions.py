#!/usr/bin/env python3
"""Regression-only tests for browser scan authorization and receipt causality."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from comment_state import validate_comment_store
from comment_store import load_comment_records
from comment_test_browser_adapter import LocalFixtureCommentAdapter
from comment_test_cli import draft_cli_fixture, prepare_cli_fixture, run_cli
from comment_test_support import POLICY
from comment_test_browser_contract_support import (
    add_scan_provenance_evidence, capture_receipt_commit, provenance_envelope,
    remember_receipt_capability, create_scan_request as create_bound_scan_request,
    scan_envelope, scan_provenance_envelope,
)
from social_primitives import parse_time


PLATFORM_URLS = {
    "facebook": "https://www.facebook.com/test/posts/post-facebook",
    "instagram": "https://www.instagram.com/p/post-instagram",
    "threads": "https://www.threads.com/@test/post/post-threads",
}
WRONG_COMMENT_URLS = {
    "facebook": "https://www.facebook.com/test/posts/other-post?comment_id=foreign",
    "instagram": "https://www.instagram.com/p/other-post/c/foreign",
    "threads": "https://www.threads.com/@test/post/other-post?reply=foreign",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def create_scan_request(
    script: Path, root: Path, adapter: LocalFixtureCommentAdapter,
    *, session_id: str = "scan-regression",
) -> dict:
    envelope = scan_envelope(adapter)
    if session_id != "scan-regression":
        # The shared fixture owns uniqueness; these tests only use the default.
        raise AssertionError("regression fixture uses one canonical scan session")
    return create_bound_scan_request(script, root, envelope)


def scan_payload(adapter: LocalFixtureCommentAdapter, request: dict) -> dict:
    comment = adapter.scan()
    observed_at = now_iso()
    page_url = request["post_permalink"]
    comment_permalink = f"{page_url}/comment/{comment['platform_comment_id']}"
    if request["platform"] == "instagram":
        comment_permalink = f"{page_url}/c/{comment['platform_comment_id']}"
    elif request["platform"] == "threads":
        author = comment.get("author_key") or comment.get("author_display") or "fixture_author"
        comment_permalink = (
            f"https://www.threads.com/@{author}/post/{comment['platform_comment_id']}"
        )
    comment.update({
        "post_permalink": page_url,
        "comment_permalink": comment_permalink,
        "observed_parent_post_permalink": page_url,
        "observed_at": observed_at,
    })
    return {
        "schema_version": 1,
        "test_only": False,
        "scan_request_id": request["scan_request_id"],
        "session_id": request["session_id"],
        "platform": request["platform"],
        "account_key": request["account_key"],
        "post_key": request["post_key"],
        "post_permalink": page_url,
        "observed_url": page_url,
        "observed_at": observed_at,
        "authentication_state": "authenticated",
        "account_verified": True,
        "post_verified": True,
        "thread_expansion_evidence": {
            "provided": True,
            "comments_expanded": True,
            "replies_expanded": True,
            "evidence": "fixture fully expanded comment and reply threads",
        },
        "comments": [comment],
    }


def submit_scan(
    script: Path, root: Path, request: dict, payload: dict, *, expected: int = 0,
) -> None:
    source = root / "regression-browser-scan.json"
    write_json(source, scan_provenance_envelope(root, request, payload))
    run_cli(
        script, root, "browser-scan", str(source),
        "--scan-request-id", request["scan_request_id"],
        "--session-id", request["session_id"], "--write", expected=expected,
    )


def approved_action(
    root: Path, platform: str,
) -> tuple[Path, LocalFixtureCommentAdapter, Path, str, dict]:
    script, _unused = prepare_cli_fixture(root, live_browser_actuation_enabled=True)
    adapter = LocalFixtureCommentAdapter(platform)
    request = create_scan_request(script, root, adapter)
    payload = add_scan_provenance_evidence(scan_payload(adapter, request))
    submit_scan(script, root, request, payload)
    comment_path = root / "data" / "comment_events.jsonl"
    comment = json.loads(comment_path.read_text(encoding="utf-8").splitlines()[0])
    reply_path, intent_id = draft_cli_fixture(script, root, comment)
    run_cli(
        script, root, "approve", "--intent-id", intent_id,
        "--approval-mode", "batch_confirm", "--session-id", "session-cli", "--write",
    )
    action = json.loads(run_cli(
        script, root, "browser-action", "--intent-id", intent_id,
        "--session-id", "session-cli",
    ).stdout)
    return script, adapter, reply_path, intent_id, action


def intent_state(root: Path, intent_id: str) -> dict:
    records = load_comment_records(root / "data")
    result = validate_comment_store(records["comments"], records["replies"], POLICY)
    if not result["valid"]:
        raise AssertionError(result["errors"])
    return next(
        state for state in result["reply_states"].values()
        if state.get("intent_id") == intent_id
    )


def begin_with_receipt(
    script: Path, root: Path, intent_id: str, receipt: dict, *, expected: int = 0,
) -> object:
    source = root / "regression-preflight.json"
    write_json(source, receipt)
    completed = run_cli(
        script, root, "browser-begin", str(source), "--intent-id", intent_id,
        "--session-id", "session-cli", "--write", expected=expected,
    )
    if expected == 0:
        lines = [
            line.removeprefix("SUBMIT_CLAIM ") for line in completed.stdout.splitlines()
            if line.startswith("SUBMIT_CLAIM ")
        ]
        if len(lines) != 1:
            raise AssertionError("regression browser-begin emitted no unique claim")
        claim = json.loads(lines[0])
        remember_receipt_capability(root, intent_id, claim["receipt_capability"])
    return completed


def shorten_permit_expiry(reply_path: Path) -> str:
    rows = [
        json.loads(line) for line in reply_path.read_text(encoding="utf-8").splitlines()
    ]
    expiry = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat(
        timespec="seconds",
    )
    approval = next(row for row in rows if row["event_type"] == "approved")
    approval["expires_at"] = expiry
    reply_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    return expiry


def check_visible_reply_cannot_be_failed() -> None:
    with tempfile.TemporaryDirectory(prefix="social-result-regression-") as raw:
        root = Path(raw)
        script, adapter, _reply_path, intent_id, action = approved_action(root, "facebook")
        adapter.fill_composer(action["reply_text"])
        begin_with_receipt(script, root, intent_id, adapter.preflight_receipt(action, now_iso()))
        current = intent_state(root, intent_id)
        adapter.hide_submit_control()
        adapter.show_own_reply(action["reply_text"])
        receipt = adapter.result_receipt(
            action, current["attempt"]["browser_preflight_id"], now_iso(),
        )
        if receipt["submission_attempted"] or receipt["submission_possible"]:
            raise AssertionError("fixture did not establish not-attempted/not-possible")
        if not receipt["exact_reply_visible"] or not receipt["own_author_verified"]:
            raise AssertionError("fixture did not expose contradictory success evidence")
        source = root / "regression-result.json"
        write_json(source, provenance_envelope(
            root, intent_id, "browser-finish", receipt,
        ))
        completed = run_cli(
            script, root, "browser-finish", str(source), "--intent-id", intent_id,
            "--session-id", "session-cli", "--write",
        )
        capture_receipt_commit(root, intent_id, completed.stdout)
        if intent_state(root, intent_id)["status"] != "needs_reconcile":
            raise AssertionError("visible own reply was incorrectly classified failed")


def check_scan_requires_stored_request() -> None:
    with tempfile.TemporaryDirectory(prefix="social-scan-binding-") as raw:
        root = Path(raw)
        script, _unused = prepare_cli_fixture(root, live_browser_actuation_enabled=True)
        adapter = LocalFixtureCommentAdapter("instagram")
        request = create_scan_request(script, root, adapter)
        payload = scan_payload(adapter, request)
        source = root / "scan-binding.json"
        write_json(source, payload)
        run_cli(script, root, "browser-scan", str(source), "--write", expected=2)
        run_cli(
            script, root, "browser-scan", str(source), "--scan-request-id", "unknown",
            "--session-id", request["session_id"], "--write", expected=2,
        )
        mismatched = dict(payload, session_id="other-session")
        write_json(source, mismatched)
        submit_scan(script, root, request, mismatched, expected=2)
        submit_scan(script, root, request, payload)
        rows = (root / "data" / "comment_events.jsonl").read_text(encoding="utf-8").splitlines()
        if len(rows) != 1:
            raise AssertionError("only the request-bound browser scan may append")


def check_wrong_post_comment_permalink_rejected() -> None:
    for platform in ("facebook", "instagram", "threads"):
        with tempfile.TemporaryDirectory(prefix=f"social-{platform}-parent-") as raw:
            root = Path(raw)
            script, _unused = prepare_cli_fixture(root, live_browser_actuation_enabled=True)
            adapter = LocalFixtureCommentAdapter(platform)
            request = create_scan_request(script, root, adapter)
            payload = scan_payload(adapter, request)
            payload["comments"][0]["comment_permalink"] = WRONG_COMMENT_URLS[platform]
            submit_scan(script, root, request, payload, expected=2)
            ledger = root / "data" / "comment_events.jsonl"
            if ledger.read_text(encoding="utf-8"):
                raise AssertionError(f"{platform} wrong-parent permalink mutated the ledger")


def check_preflight_causal_window() -> None:
    with tempfile.TemporaryDirectory(prefix="social-preflight-causal-") as raw:
        root = Path(raw)
        script, adapter, reply_path, intent_id, action = approved_action(root, "threads")
        adapter.fill_composer(action["reply_text"])
        permit = intent_state(root, intent_id)["permit"]
        before_approval = (parse_time(permit["occurred_at"]) - timedelta(seconds=1)).isoformat()
        baseline = reply_path.read_text(encoding="utf-8")
        receipt = adapter.preflight_receipt(action, before_approval)
        rejected = begin_with_receipt(script, root, intent_id, receipt, expected=2)
        if "predates approval" not in rejected.stderr:
            raise AssertionError("pre-approval receipt missed the approval causal guard")
        if reply_path.read_text(encoding="utf-8") != baseline:
            raise AssertionError("pre-approval receipt mutated the ledger")
        expiry = shorten_permit_expiry(reply_path)
        after_expiry = (parse_time(expiry) + timedelta(seconds=1)).isoformat()
        shortened = reply_path.read_text(encoding="utf-8")
        receipt = adapter.preflight_receipt(action, after_expiry)
        rejected = begin_with_receipt(script, root, intent_id, receipt, expected=2)
        if "permit expiry" not in rejected.stderr:
            raise AssertionError("post-expiry receipt missed the permit causal guard")
        if reply_path.read_text(encoding="utf-8") != shortened:
            raise AssertionError("post-expiry receipt mutated the ledger")


def run_browser_regression_tests() -> None:
    check_visible_reply_cannot_be_failed()
    check_scan_requires_stored_request()
    check_wrong_post_comment_permalink_rejected()
    check_preflight_causal_window()
