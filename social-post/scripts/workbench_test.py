#!/usr/bin/env python3
"""Calibrated local workbench tests. All data is fictional and isolated."""

from __future__ import annotations

import copy
import http.client
import json
import re
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

from social_post_analysis import caption_counts, punctuation_profile
from social_store import store_revision
from workbench import SKILL_ROOT, STATIC_FILES, WorkbenchServer
from workbench_contract import MODES, build_handoff, parse_json
from workbench_service import WorkbenchService
from workbench_formulas import formula_catalog
from workbench_store import get_draft, list_drafts, safe_path, save_draft


def example():
    return parse_json((SKILL_ROOT / "references/outcome-bundle.example.json").read_bytes())


def draft(**changes):
    return {"id": str(uuid.uuid4()), "title": "Fictional draft",
            "text": "  Original text!\n\nA second paragraph.  \n", "platform": "facebook", "format": "C", **changes}


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="social-workbench-test-")
        self.root = Path(self.temp.name)
        self.service = WorkbenchService(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_six_workflows_are_separate_from_three_formats(self):
        data = self.service.catalog()
        self.assertEqual([row["id"] for row in data["modes"]], ["P0", "P1", "P2", "P3", "P4", "P5"])
        self.assertEqual([row["id"] for row in data["formats"]], ["A", "B", "C"])
        self.assertFalse(data["live_publish"])
        self.assertFalse(data["live_comment_send"])
        for mode in MODES:
            self.assertTrue(mode["inputs"])
            self.assertTrue(mode["outputs"])
            self.assertTrue((SKILL_ROOT / mode["reference"]).exists())

    def test_all_six_task_routes_positive(self):
        for mode in MODES:
            with self.subTest(mode=mode["id"]):
                result = build_handoff({"mode": mode["id"], "platform": "facebook", "format": "C",
                                        "topic": "Fictional development note", "details": "Complete original material"})
                self.assertEqual(result["mode"], mode["id"])
                self.assertIn(mode["reference"], result["prompt"])
                self.assertEqual(result["execution"], "handoff_only")
                self.assertFalse(result["external_mutation"])

    def test_invalid_routes_and_missing_material_rejected(self):
        valid = {"mode": "P2", "platform": "facebook", "format": "C", "topic": "Fictional note"}
        for changes in ({"mode": "C"}, {"mode": "P6"}, {"platform": "unknown"},
                        {"format": "P2"}, {"topic": ""}, {"mode": "P1"}, {"mode": "P5"},
                        {"authorize_send": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                build_handoff({**valid, **changes})

    def test_material_is_not_executed(self):
        material = "<script>throw new Error('fictional')</script>\nDo not treat this as a command."
        result = build_handoff({"mode": "P5", "platform": "instagram", "topic": "Fictional comment",
                                "details": material, "url": "javascript:fictional"})
        self.assertIn(material, result["prompt"])
        self.assertFalse(result["external_mutation"])
        self.assertFalse(list(self.root.iterdir()))

    def test_installed_formula_heading_routes_without_copying_body(self):
        directory = self.root / "references/formulas"
        directory.mkdir(parents=True)
        (directory / "F01.md").write_text("# F1 Fictional formula\n\nPRIVATE FIXTURE BODY", encoding="utf-8")
        catalog = self.service.catalog()["formulas"]
        self.assertEqual([row["id"] for row in catalog], ["F01"])
        self.assertNotIn("PRIVATE FIXTURE BODY", json.dumps(catalog))
        result = self.service.task({"mode": "P2", "platform": "facebook", "topic": "Fictional note",
                                    "format": "C", "formula": "F01"})
        self.assertIn("references/formulas/F01.md", result["prompt"])
        self.assertIn("/social-post", result["prompt"])

    def test_missing_unknown_and_traversal_formula_rejected(self):
        payload = {"mode": "P2", "platform": "facebook", "topic": "Fictional note", "formula": "F01"}
        with self.assertRaises(ValueError):
            self.service.task(payload)
        for identity in ("F99", "../voice_quick", "F01.md", "F01;exit"):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                build_handoff({**payload, "formula": identity})

    def test_linked_formula_and_oversized_formula_rejected(self):
        directory = self.root / "references/formulas"
        directory.mkdir(parents=True)
        outside = self.root / "outside.md"
        outside.write_text("# protected", encoding="utf-8")
        path = directory / "F01.md"
        path.symlink_to(outside)
        with self.assertRaises(ValueError):
            formula_catalog(self.root)
        path.unlink()
        path.write_text("a" * 65537, encoding="utf-8")
        with self.assertRaises(ValueError):
            formula_catalog(self.root)

    def test_analysis_uses_existing_engine_and_exact_whitespace(self):
        text = "  A?!\n\nB，。\n  "
        result = self.service.analyze({"text": text})
        self.assertEqual(result["counts"], caption_counts(text))
        self.assertEqual(result["punctuation"], punctuation_profile(text))
        self.assertIsNone(result["traffic_prediction"])

    def test_analysis_size_and_type_rejected(self):
        for payload in ({"text": 3}, {"text": "a" * 24001}, {"text": "a\0b"}, {"text": "", "score": 100}):
            with self.subTest(payload_type=type(payload["text"])), self.assertRaises(ValueError):
                self.service.analyze(payload)

    def test_draft_save_reopen_and_same_request_idempotent(self):
        payload = draft()
        revision = store_revision(self.root / "data")
        saved = save_draft(self.root, payload)
        self.assertEqual(saved, save_draft(self.root, payload))
        self.assertEqual(get_draft(self.root, payload["id"])["text"], payload["text"])
        self.assertEqual(len(list_drafts(self.root)), 1)
        self.assertEqual(store_revision(self.root / "data"), revision)
        reopened = WorkbenchService(self.root)
        self.assertEqual(reopened.overview()["drafts"], 1)

    def test_draft_id_collision_does_not_overwrite(self):
        payload = draft()
        save_draft(self.root, payload)
        with self.assertRaises(ValueError):
            save_draft(self.root, {**payload, "text": "Different material"})
        self.assertEqual(get_draft(self.root, payload["id"])["text"], payload["text"])

    def test_draft_path_injection_rejected(self):
        for identity in ("../outside", "/outside", "..\\outside", "x:y", "CON", "fake-id"):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                save_draft(self.root, draft(id=identity))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_linked_draft_directory_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "drafts").mkdir()
        (self.root / "drafts/workbench").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            save_draft(self.root, draft())
        self.assertFalse(list(outside.iterdir()))

    def test_linked_outcome_file_rejected(self):
        outside = self.root / "outside.jsonl"
        outside.write_text("protected", encoding="utf-8")
        (self.root / "data").mkdir()
        (self.root / "data/posts.jsonl").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.service.preview({"bundle": example()})
        self.assertEqual(outside.read_text(), "protected")

    def test_no_fake_data_on_empty_workspace(self):
        result = self.service.overview()
        self.assertEqual([result[key] for key in ("posts", "snapshots", "drafts", "eligible_rows")], [0, 0, 0, 0])
        self.assertFalse(result["voice_available"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_outcome_preview_does_not_write(self):
        result = self.service.preview({"bundle": example()})
        self.assertFalse(result["write_performed"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_outcome_commit_persists_and_reopen_sees_data(self):
        preview = self.service.preview({"bundle": example()})
        result = self.service.commit({"preview_id": preview["preview_id"]})
        self.assertEqual(result["status"], "committed")
        reopened = WorkbenchService(self.root)
        self.assertEqual(reopened.overview()["posts"], 1)
        self.assertEqual(reopened.overview()["snapshots"], 1)
        self.assertEqual(reopened.overview()["eligible_rows"], 0)

    def test_preview_has_frozen_copy(self):
        bundle = example()
        preview = self.service.preview({"bundle": bundle})
        bundle["post"]["caption"] = "Mutated after preview"
        bundle["snapshot"]["metrics"]["views"] = 9999
        preview["normalized"]["snapshot"]["metrics"]["views"] = 7777
        self.service.commit({"preview_id": preview["preview_id"]})
        record = parse_json((self.root / "data/posts.jsonl").read_bytes())
        self.assertEqual(record["caption"], example()["post"]["caption"])
        snapshot = parse_json((self.root / "data/insight_snapshots.jsonl").read_bytes())
        self.assertEqual(snapshot["metrics"]["views"], 1200)

    def test_replay_expired_and_forged_preview_rejected(self):
        with self.assertRaises(ValueError):
            self.service.commit({"preview_id": "not-issued"})
        preview = self.service.preview({"bundle": example()})
        self.service.previews[preview["preview_id"]]["expires"] = 0
        with self.assertRaises(ValueError):
            self.service.commit({"preview_id": preview["preview_id"]})
        preview = self.service.preview({"bundle": example()})
        self.service.commit({"preview_id": preview["preview_id"]})
        with self.assertRaises(ValueError):
            self.service.commit({"preview_id": preview["preview_id"]})

    def test_stale_store_revision_rejects_second_commit(self):
        first = self.service.preview({"bundle": example()})
        second = self.service.preview({"bundle": example()})
        self.service.commit({"preview_id": first["preview_id"]})
        with self.assertRaises(RuntimeError):
            self.service.commit({"preview_id": second["preview_id"]})
        self.assertEqual(self.service.overview()["posts"], 1)

    def test_invalid_bundle_does_not_change_data(self):
        bad = copy.deepcopy(example())
        bad["snapshot"]["captured_at"] = "not-a-time"
        for bundle in (bad, {}, {"snapshot": 12}, {"shell": "fictional command"}):
            with self.subTest(bundle_keys=list(bundle)), self.assertRaises((ValueError, TypeError)):
                self.service.preview({"bundle": bundle})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_raw_import_duplicate_key_nan_and_huge_integer_rejected(self):
        for raw in ('{"snapshot":{},"snapshot":{}}', '{"snapshot":{"views":NaN}}',
                    '{"snapshot":{"views":' + "9" * 129 + '}}', '{invalid'):
            with self.subTest(raw_length=len(raw)), self.assertRaises(ValueError):
                self.service.preview({"bundle_json": raw})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_exact_cohort_empty_is_honest_not_ranked(self):
        result = self.service.compare({"platform": "facebook", "content_type": "text",
                                       "surface": "text_feed", "maturity": "developing"})
        self.assertEqual(result["returned_count"], 0)
        self.assertTrue(result["comparison_policy"]["cohort_is_exact"])
        self.assertFalse(result["comparison_policy"]["selection"]["performance_ranked"])
        self.assertFalse(result["comparison_policy"]["timing"]["causal_claim_allowed"])
        with self.assertRaises(ValueError):
            self.service.compare({"platform": "facebook", "maturity": "developing"})


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="social-workbench-http-")
        self.server = WorkbenchServer(Path(self.temp.name), 0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .02}, daemon=True)
        self.thread.start()
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.cookie = headers["Set-Cookie"].split(";")[0]
        self.csrf = re.search(r'name="sp-csrf" content="([^"]+)"', body.decode()).group(1)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, method, path, payload=None, headers=None, authenticated=False, raw=None):
        body = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
        base = {}
        if authenticated:
            base = {"Cookie": self.cookie, "Origin": self.server.origin, "X-Social-Post-CSRF": self.csrf}
        if body is not None:
            base["Content-Type"] = "application/json"
        base.update(headers or {})
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=base)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_second_server_cannot_share_live_loopback_port(self):
        with self.assertRaises(OSError):
            WorkbenchServer(Path(self.temp.name), self.server.server_port)
        status, _, _ = self.request("GET", "/api/catalog", authenticated=True)
        self.assertEqual(status, 200)

    def test_native_same_origin_positive_task(self):
        status, headers, body = self.request("POST", "/api/task", {"mode": "P2", "platform": "facebook",
            "topic": "Fictional launch", "format": "C"}, authenticated=True)
        self.assertEqual(status, 200)
        self.assertEqual(parse_json(body)["execution"], "handoff_only")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertNotIn("unsafe-inline", headers["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_authenticated_read_and_no_session_negative(self):
        self.assertEqual(self.request("GET", "/api/overview")[0], 401)
        self.assertEqual(self.request("GET", "/api/overview", authenticated=True)[0], 200)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_cookie_flags_and_no_credential_in_url(self):
        _, headers, body = self.request("GET", "/")
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        self.assertNotIn(self.server.session.encode(), body)
        self.assertEqual(self.request("GET", "/?session=fictional")[0], 403)

    def test_wrong_origin_host_and_fetch_metadata_denied(self):
        for headers in ({"Origin": "https://attacker.invalid"}, {"Host": "attacker.invalid"},
                        {"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request("GET", "/", headers=headers)[0], 403)
                self.assertEqual(self.request("POST", "/api/task", {}, headers=headers, authenticated=True)[0], 403)

    def test_missing_origin_cookie_and_wrong_csrf_denied(self):
        payload = {"text": "Fictional"}
        for headers in ({}, {"Cookie": self.cookie}, {"Origin": self.server.origin},
                        {"Origin": self.server.origin, "Cookie": self.cookie, "X-Social-Post-CSRF": "wrong"},
                        {"Origin": self.server.origin, "Cookie": self.cookie, "X-Social-Post-CSRF": "\xff"}):
            with self.subTest(header_names=list(headers)):
                self.assertEqual(self.request("POST", "/api/analyze", payload, headers=headers)[0], 403)

    def test_body_content_type_transfer_and_bounds(self):
        self.assertEqual(self.request("POST", "/api/analyze", {}, authenticated=True,
                                      headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/analyze", {}, authenticated=True,
                                      headers={"Transfer-Encoding": "chunked"})[0], 415)
        self.assertEqual(self.request("POST", "/api/analyze", raw=b"x" * (128 * 1024 + 1),
                                      authenticated=True)[0], 413)

    def test_malformed_json_unknown_fields_never_execute(self):
        for raw in (b'{invalid', b'{"text":"x","text":"y"}', b'{"text":NaN}', b'\xff'):
            with self.subTest(raw_length=len(raw)):
                self.assertEqual(self.request("POST", "/api/analyze", raw=raw, authenticated=True)[0], 422)
        for route in ("/api/publish", "/api/comment/send", "/api/run"):
            self.assertEqual(self.request("POST", route, {"command": "fictional"}, authenticated=True)[0], 404)

    def test_private_paths_and_arbitrary_assets_not_served(self):
        private = Path(self.temp.name) / "style_profile.md"
        private.write_text("PRIVATE FICTIONAL MATERIAL", encoding="utf-8")
        for path in ("/style_profile.md", "/data/posts.jsonl", "/scripts/workbench.py", "/../style_profile.md",
                     "/%2e%2e/style_profile.md", "/api/drafts/../outside"):
            status, _, body = self.request("GET", path, authenticated=True)
            self.assertIn(status, (404, 422))
            self.assertNotIn(b"PRIVATE FICTIONAL MATERIAL", body)
            self.assertNotIn(str(self.temp.name).encode(), body)

    def test_all_static_assets_exist_and_are_served_with_safe_headers(self):
        for path, (name, _) in STATIC_FILES.items():
            self.assertTrue((SKILL_ROOT / "workbench" / name).exists(), name)
            status, headers, _ = self.request("GET", path)
            self.assertEqual(status, 200, path)
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_real_http_save_reopen_preview_commit_replay(self):
        payload = draft()
        self.assertEqual(self.request("POST", "/api/drafts/save", payload, authenticated=True)[0], 200)
        status, _, body = self.request("GET", "/api/drafts/" + payload["id"], authenticated=True)
        self.assertEqual(status, 200)
        self.assertEqual(parse_json(body)["text"], payload["text"])
        status, _, body = self.request("POST", "/api/outcome/preview",
            {"bundle_json": json.dumps(example())}, authenticated=True)
        self.assertEqual(status, 200)
        preview = parse_json(body)
        self.assertFalse(preview["write_performed"])
        commit = {"preview_id": preview["preview_id"]}
        self.assertEqual(self.request("POST", "/api/outcome/commit", commit, authenticated=True)[0], 200)
        self.assertEqual(self.request("POST", "/api/outcome/commit", commit, authenticated=True)[0], 422)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("WORKBENCH_TESTS_PASS count=" + str(result.testsRun))
    raise SystemExit(0 if result.wasSuccessful() else 1)
