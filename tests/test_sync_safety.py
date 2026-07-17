from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tools.sync_safety import (
    SafetyError,
    prepare_safe_parent,
    url_identity,
    validate_safe_descendant,
)


class SyncPathSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "data" / "code"
        self.root.mkdir(parents=True)

    def test_accepts_existing_nested_directory(self) -> None:
        candidate = self.root / "team" / "service"
        candidate.mkdir(parents=True)
        self.assertEqual(
            validate_safe_descendant(self.root, candidate, allow_missing=False),
            candidate,
        )

    def test_accepts_missing_nested_target(self) -> None:
        candidate = self.root / "team" / "service"
        self.assertEqual(
            validate_safe_descendant(self.root, candidate, allow_missing=True),
            candidate,
        )

    def test_rejects_root_and_outside_path(self) -> None:
        with self.assertRaises(SafetyError):
            validate_safe_descendant(self.root, self.root, allow_missing=True)
        with self.assertRaises(SafetyError):
            validate_safe_descendant(
                self.root,
                self.root.parent / "outside",
                allow_missing=True,
            )

    def test_rejects_non_directory_ancestor(self) -> None:
        blocking_file = self.root / "team"
        blocking_file.write_text("not a directory", encoding="utf-8")
        with self.assertRaises(SafetyError):
            validate_safe_descendant(
                self.root,
                blocking_file / "service",
                allow_missing=True,
            )

    def test_prepare_parent_creates_only_missing_parents(self) -> None:
        candidate = self.root / "team" / "service"
        self.assertEqual(prepare_safe_parent(self.root, candidate), candidate)
        self.assertTrue(candidate.parent.is_dir())
        self.assertFalse(candidate.exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "平台不支持符号链接")
    def test_rejects_symlink_ancestor_when_available(self) -> None:
        real = self.root / "real"
        real.mkdir()
        link = self.root / "link"
        try:
            os.symlink(real, link, target_is_directory=True)
        except OSError:
            self.skipTest("当前环境不允许创建符号链接")
        with self.assertRaises(SafetyError):
            validate_safe_descendant(
                self.root,
                link / "service",
                allow_missing=True,
            )

    def test_scp_identity_includes_validated_username(self) -> None:
        self.assertNotEqual(
            url_identity("git@example.invalid:team/repository.git"),
            url_identity("deploy@example.invalid:team/repository.git"),
        )

    def test_scp_identity_rejects_option_shaped_username(self) -> None:
        with self.assertRaises(SafetyError):
            url_identity("-oProxyCommand=bad@example.invalid:team/repository.git")

    def test_url_identity_preserves_ipv6_authority_brackets(self) -> None:
        # Given
        repository_url = "https://[2001:DB8::1]:8443/team/repository.git"

        # When
        identity = url_identity(repository_url)

        # Then
        self.assertEqual(
            identity,
            "https://[2001:db8::1]:8443/team/repository",
        )

    def test_url_identity_rejects_whitespace_and_controls(self) -> None:
        for value in (
            "https://example.invalid/team/repository git",
            "https://example.invalid/team/repository\n",
        ):
            with self.subTest(value=value):
                with self.assertRaises(SafetyError):
                    url_identity(value)


if __name__ == "__main__":
    unittest.main()
