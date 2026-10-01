"""Task-shaped controls for the public contribution guard."""

from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from check_public_contribution import inspect_files, path_violation


class ContributionGuardTests(unittest.TestCase):
    def test_public_docs_and_fictional_example_are_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CONTRIBUTING.md").write_text("公開共創指南", encoding="utf-8")
            example = root / "references" / "outcome.example.json"
            example.parent.mkdir()
            example.write_text('{"fictional": true}', encoding="utf-8")
            self.assertEqual(
                inspect_files(root, ["CONTRIBUTING.md", "references/outcome.example.json"], {}),
                [],
            )

    def test_private_and_forced_ignored_paths_are_rejected(self):
        for name in (
            "social-post/style_profile.md", "social-post/data/posts.jsonl",
            "social-post/.rd/receipt.json", "social-post/drafts/draft.md",
            "screenshot.JPG", "browser/cookies.json", ".env.production",
        ):
            with self.subTest(path=name):
                self.assertIsNotNone(path_violation(name))
        self.assertIsNone(path_violation("social-post/style_profile.example.md"))
        self.assertIsNone(path_violation("social-post/data/rule_registry.json"))

    def test_credential_pattern_is_rejected_in_a_renamed_text_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "notes.md"
            sample.write_text("Authorization" + ": Bearer " + "fictional123456", encoding="utf-8")
            config = {"privacy": {"patterns": [r"Authorization\s*:\s*Bearer\s+\S{8,}"]}}
            self.assertTrue(inspect_files(root, ["notes.md"], config))

    def test_binary_content_cannot_hide_under_markdown_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.md").write_bytes(b"public\x00payload")
            self.assertTrue(inspect_files(root, ["notes.md"], {}))

    def test_actual_repository_privacy_config_rejects_credentials_and_user_paths(self):
        config_path = Path(__file__).resolve().parents[1] / "audit.config.json"
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        samples = (
            "Authorization" + ": Bearer " + "fictional123456",
            "Cookie" + ": " + "fictional-session=123456",
            "api_key" + "='fictional123456'",
            "C:" + "/Users/fictional/private",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "notes.md"
            for content in samples:
                with self.subTest(kind=content.split(":")[0]):
                    sample.write_text(content, encoding="utf-8")
                    self.assertTrue(inspect_files(root, ["notes.md"], config))

    def test_missing_traversal_and_case_collision_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.md").write_text("public", encoding="utf-8")
            for names in (["missing.md"], ["../outside.md"], ["notes.md", "NOTES.md"]):
                with self.subTest(paths=names):
                    self.assertTrue(inspect_files(root, names, {}))

    def test_link_to_other_data_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("public", encoding="utf-8")
            link = root / "linked.md"
            try:
                link.symlink_to(root / "source.md")
            except OSError:
                self.skipTest("host does not permit creating symlinks")
            self.assertTrue(inspect_files(root, ["linked.md"], {}))


if __name__ == "__main__":
    unittest.main()
