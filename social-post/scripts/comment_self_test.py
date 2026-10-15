#!/usr/bin/env python3
"""Public entry point for modular comment-operation behavioral tests."""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
from pathlib import Path

from comment_test_authorization import run_authorization_tests
from comment_capability_gate import main as run_capability_gate
from comment_capability_gate_calibration import run_capability_gate_calibration
from comment_capability_promotion_calibration import promotion_calibration_tests
from comment_test_browser_adapter import run_browser_adapter_tests
from comment_test_browser_contract import run_browser_contract_tests
from comment_test_browser_recovery import run_browser_recovery_tests
from comment_test_browser_receipt_provenance import run_browser_receipt_provenance_tests
from comment_test_browser_send_urls import run_browser_send_url_tests
from comment_test_browser_target import run_browser_target_tests
from comment_test_canary import run_canary_tests
from comment_test_cli import run_cli_tests
from comment_test_fixture_promotion_envelope import (
    run_fixture_promotion_envelope_tests,
)
from comment_test_state import run_state_tests
from comment_test_trusted_host_verifier import run_trusted_host_verifier_tests


JS_TEST_MODULES = {
    "scripts/comment_cua_runtime_test.mjs",
    "scripts/comment_cua_dispatch_test.mjs",
    "scripts/comment_chrome_actuator_fixture_test.mjs",
    "scripts/comment_chrome_actuator_guards_test.mjs",
    "scripts/comment_chrome_actuator_receipts_test.mjs",
    "scripts/comment_chrome_actuator_reinspection_test.mjs",
    "scripts/comment_chrome_actuator_reply_exhaustion_test.mjs",
    "scripts/comment_chrome_actuator_scan_test.mjs",
    "scripts/comment_chrome_actuator_send_test.mjs",
    "scripts/comment_chrome_actuator_test.mjs",
    "scripts/comment_chrome_claim_bridge_test.mjs",
    "scripts/comment_chrome_target_tab_reuse_test.mjs",
    "scripts/comment_chrome_claim_integration_test.mjs",
    "scripts/comment_chrome_facebook_reader_test.mjs",
    "scripts/comment_chrome_facebook_child_reader_test.mjs",
    "scripts/comment_chrome_fixture_contract_test.mjs",
    "scripts/comment_chrome_host_authority_test.mjs",
    "scripts/comment_chrome_instagram_selection_test.mjs",
    "scripts/comment_chrome_live_bridge_test.mjs",
    "scripts/comment_chrome_live_surface_test.mjs",
    "scripts/comment_chrome_live_surface_candidate_cases_test.mjs",
    "scripts/comment_chrome_live_surface_observation_cases_test.mjs",
    "scripts/comment_chrome_node_frame_lifecycle_test.mjs",
    "scripts/comment_chrome_node_frame_mapping_test.mjs",
    "scripts/comment_chrome_runtime_reconnect_test.mjs",
    "scripts/comment_chrome_scan_adapters_test.mjs",
    "scripts/comment_chrome_textarea_identity_test.mjs",
    "scripts/comment_chrome_threads_reader_test.mjs",
    "scripts/comment_chrome_threads_canary_surface_test.mjs",
    "scripts/comment_chrome_threads_dom_fixtures_test.mjs",
    "scripts/comment_chrome_threads_canary_reader_cases_test.mjs",
    "scripts/comment_chrome_threads_icon_identity_test.mjs",
}


def run_js_architecture_config_test() -> None:
    """Prove exact JS role patterns precede the browser production catch-all."""
    skill_root = Path(__file__).resolve().parent.parent
    config_path = skill_root / "audit.config.json"
    canonical_ledger = skill_root / ".rd" / "capability-ledger.json"
    if not config_path.exists():
        if canonical_ledger.exists():
            raise AssertionError("private canonical package is missing audit.config.json")
        print("comment JS private Cleanup config test not applicable in public projection")
        return
    config = json.loads(config_path.read_text(encoding="utf-8"))
    layers = config.get("architecture", {}).get("layers", [])
    names = [layer.get("name") for layer in layers]
    required = ("test", "e2e", "fixture", "browser-actuator", "tools")
    if any(names.count(name) != 1 for name in required):
        raise AssertionError("audit.config must define each JS architecture layer exactly once")
    browser_index = names.index("browser-actuator")
    if any(names.index(name) >= browser_index for name in ("test", "e2e", "fixture")):
        raise AssertionError("exact test/e2e/fixture layers must precede browser catch-all")
    patterns = {layer["name"]: layer.get("patterns", []) for layer in layers}
    configured_tests = {item for item in patterns["test"] if item.endswith("_test.mjs")}
    if configured_tests != JS_TEST_MODULES:
        raise AssertionError("audit.config JS test layer drifted from the exact module set")
    if any("*" in item for item in configured_tests):
        raise AssertionError("audit.config JS test roles must not use suffix/default globs")
    if patterns["e2e"] != ["scripts/comment_fixture_browser_e2e.mjs"]:
        raise AssertionError("audit.config E2E role must use the exact reviewed module")
    if patterns["fixture"] != [
        "scripts/comment_chrome_fixture_evidence_testonly.mjs",
        "scripts/comment_chrome_fixture_receipt_testonly.mjs",
        "scripts/comment_chrome_live_surface_fixture_testonly.mjs",
        "scripts/comment_chrome_node_frame_lifecycle_snapshot_testonly.mjs",
        "scripts/comment_chrome_node_frame_lifecycle_testonly.mjs",
        "scripts/comment_chrome_node_frame_mapping_fixture_testonly.mjs",
        "scripts/comment_chrome_node_frame_mapping_testonly.mjs",
        "scripts/comment_chrome_scan_fixture_testonly.mjs",
        "scripts/comment_adapter_fixtures/fixture-runtime.js",
    ]:
        raise AssertionError("audit.config fixture role must use exact reviewed modules")
    if "scripts/comment_js_architecture_*.mjs" not in patterns["tools"]:
        raise AssertionError("native JavaScript gate modules must be assigned to tools")
    print("comment JS architecture config test passed")


def _run_marked_chrome_test(node: str, name: str, marker: str, missing_message: str) -> None:
    completed = subprocess.run(
        [node, str(Path(__file__).with_name(name))],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    if marker not in completed.stdout.splitlines():
        raise AssertionError(missing_message)
    print(completed.stdout, end="", flush=True)


def run_chrome_actuator_tests() -> None:
    """Run JavaScript actuator and durable-claim contracts when Node is available."""
    node = shutil.which("node")
    if not node:
        print("comment Chrome actuator test skipped: node is unavailable")
        return
    for name in (
        "comment_chrome_claim_bridge_test.mjs",
        "comment_chrome_claim_integration_test.mjs",
        "comment_chrome_host_authority_test.mjs",
        "comment_chrome_live_bridge_test.mjs",
        "comment_chrome_live_surface_test.mjs",
        "comment_chrome_scan_adapters_test.mjs",
        "comment_chrome_actuator_test.mjs",
    ):
        subprocess.run([node, str(Path(__file__).with_name(name))], check=True)
    for name, marker, missing_message in (
        (
            "comment_cua_runtime_test.mjs",
            "comment CUA runtime ownership tests passed",
            "CUA runtime ownership child success marker is missing",
        ),
        (
            "comment_cua_dispatch_test.mjs",
            "PASS CUA durable dispatch orchestration "
            "(isolated; no browser or canonical ledger)",
            "CUA durable dispatch child success marker is missing",
        ),
        (
            "comment_chrome_runtime_reconnect_test.mjs",
            "PASS source-owned Chrome explicit disconnect reconnection tests (mocked; no browser)",
            "Chrome reconnect child success marker is missing",
        ),
        (
            "comment_chrome_target_tab_reuse_test.mjs",
            "PASS source-owned exact target intake tab reuse tests (mocked; no browser)",
            "Target intake tab reuse child success marker is missing",
        ),
        (
            "comment_chrome_facebook_reader_test.mjs",
            "PASS Facebook native reader DOM, identity and URL drift tests "
            "(anonymous; no browser submission)",
            "Facebook reader child success marker is missing",
        ),
        (
            "comment_chrome_facebook_child_reader_test.mjs",
            "PASS Facebook native child reader DOM and source continuity tests "
            "(anonymous; no browser or submission)",
            "Facebook child reader success marker is missing",
        ),
        (
            "comment_chrome_instagram_selection_test.mjs",
            "PASS IG CUA native selection and integrated single dispatch "
            "(anonymous DOM; simulated I/O only)",
            "Instagram semantic selection child success marker is missing",
        ),
        (
            "comment_chrome_threads_reader_test.mjs",
            "PASS Threads native reader DOM, identity and URL drift tests "
            "(anonymous; no browser submission)",
            "Threads reader child success marker is missing",
        ),
        (
            "comment_chrome_threads_icon_identity_test.mjs",
            "PASS Threads reply icon stable-node identity tests (anonymous; no browser)",
            "Threads icon identity child success marker is missing",
        ),
        (
            "comment_chrome_threads_canary_surface_test.mjs",
            "PASS Threads source-selected empty preparation and native DOM readers "
            "(anonymous; no browser submission)",
            "Threads canary surface child success marker is missing",
        ),
    ):
        _run_marked_chrome_test(node, name, marker, missing_message)
    fixture_runner = Path(__file__).with_name("comment_fixture_browser_e2e.mjs")
    subprocess.run([
        node, "--input-type=module", "--eval",
        f"delete globalThis.process; await import({json.dumps(fixture_runner.as_uri())});",
    ], check=True)


def run_js_architecture_gate() -> None:
    """Calibrate and run the product-native closed-world JavaScript graph gate."""
    node = shutil.which("node")
    if not node:
        raise AssertionError("comment JS architecture gate NOT_CHECKED: node is unavailable")
    scripts_root = Path(__file__).resolve().parent
    skill_root = scripts_root.parent
    gate = scripts_root / "comment_js_architecture_gate.mjs"

    def invoke(arguments: list[str], marker: str) -> dict:
        completed = subprocess.run(
            [node, str(gate), *arguments],
            cwd=skill_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"{marker}: child exit {completed.returncode}; stdout={completed.stdout!r}; "
                f"stderr={completed.stderr!r}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise AssertionError(f"{marker}: child stdout was not exactly one JSON document") from error
        if payload.get("status") != "PASS" or payload.get("marker") != marker:
            raise AssertionError(f"{marker}: success marker or PASS status is missing")
        return payload

    self_test_marker = "comment JS architecture gate self-test passed"
    self_test = invoke(["--self-test"], self_test_marker)
    if self_test.get("self_test", {}).get("passed") is not True:
        raise AssertionError("comment JS architecture gate self-test did not calibrate fixtures")
    print(self_test_marker)

    receipt_relative = Path(".rd") / "receipts" / "js-architecture-gate.json"
    actual_marker = "comment JS architecture gate passed"
    actual = invoke(["--output", receipt_relative.as_posix()], actual_marker)
    receipt_path = skill_root / receipt_relative
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt != actual:
        raise AssertionError("comment JS architecture gate receipt differs from child stdout")
    sidecar_path = receipt_path.with_name(f"{receipt_path.name}.sha256")
    expected_sidecar = (
        f"{hashlib.sha256(receipt_path.read_bytes()).hexdigest()}  {receipt_path.name}\n"
    )
    if sidecar_path.read_text(encoding="utf-8") != expected_sidecar:
        raise AssertionError("comment JS architecture gate SHA-256 sidecar is missing or invalid")
    print(actual_marker)


def _run_step(label: str, test):
    """Run one suite with visible progress so a long subprocess batch is diagnosable."""
    print(f"comment self-test START {label}", flush=True)
    result = test()
    print(f"comment self-test PASS {label}", flush=True)
    return result


def run_comment_self_tests() -> None:
    """Run the complete comment-operation test suite."""
    _run_step("state", run_state_tests)
    _run_step("authorization", run_authorization_tests)
    _run_step("cli", run_cli_tests)
    _run_step("browser-adapter", run_browser_adapter_tests)
    _run_step("browser-contract", run_browser_contract_tests)
    _run_step("browser-send-urls", run_browser_send_url_tests)
    _run_step("browser-target", run_browser_target_tests)
    _run_step("single-action-canary", run_canary_tests)
    _run_step("browser-receipt-provenance", run_browser_receipt_provenance_tests)
    _run_step("browser-recovery", run_browser_recovery_tests)
    _run_step("js-architecture-config", run_js_architecture_config_test)
    _run_step("js-architecture-gate", run_js_architecture_gate)
    _run_step("chrome-actuator", run_chrome_actuator_tests)
    skill_root = Path(__file__).resolve().parent.parent
    ledger_path = skill_root / ".rd" / "capability-ledger.json"
    package_path = skill_root / ".rd" / "package.json"
    if ledger_path.is_file() and package_path.is_file():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        package = json.loads(package_path.read_text(encoding="utf-8"))
        _run_step(
            "fixture-promotion-envelope",
            lambda: run_fixture_promotion_envelope_tests(
                skill_root, package["version"], ledger["sourceRevisionBasis"]
            ),
        )
        _run_step(
            "capability-promotion-calibration",
            lambda: promotion_calibration_tests(
                skill_root, package["version"], ledger["sourceRevisionBasis"]
            ),
        )
        _run_step(
            "trusted-host-verifier",
            lambda: run_trusted_host_verifier_tests(
                skill_root, package["version"], ledger["sourceRevisionBasis"]
            ),
        )
    else:
        print("comment promotion calibration not applicable in public projection")
        print("trusted host verifier test not applicable in public projection")
    _run_step("capability-gate-calibration", run_capability_gate_calibration)
    if _run_step("capability-gate", run_capability_gate) != 0:
        raise AssertionError("comment capability gate failed")


def main() -> int:
    run_comment_self_tests()
    print("comment self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
