from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tools.sync_safety import (
    SafetyError,
    prepare_safe_parent,
    reject_unsafe_git_config,
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


class GitMetadataSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.code_root = Path(self.temporary.name).resolve() / "data" / "code"
        self.code_root.mkdir(parents=True)

    def write_common_config(self, common_dir: Path, *, bare: bool = False) -> None:
        (common_dir / "config").write_text(
            "[core]\n"
            "\trepositoryformatversion = 0\n"
            f"\tbare = {'true' if bare else 'false'}\n"
            "[remote \"origin\"]\n"
            "\turl = https://example.invalid/team/repository.git\n"
            "\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
            "[branch \"main\"]\n"
            "\tremote = origin\n"
            "\tmerge = refs/heads/main\n",
            encoding="utf-8",
        )

    def append_common_config(self, common_dir: Path, content: str) -> None:
        with (common_dir / "config").open("a", encoding="utf-8") as config:
            config.write(content)

    def create_linked_worktree(
        self,
        common_dir: Path | None = None,
        admin_name: str = "linked",
    ) -> tuple[Path, Path, Path]:
        common_dir = common_dir or self.code_root / "primary" / ".git"
        common_dir.mkdir(parents=True)
        self.write_common_config(common_dir)

        worktree = self.code_root / "linked"
        worktree.mkdir()
        marker = worktree / ".git"
        admin_dir = common_dir / "worktrees" / admin_name
        admin_dir.mkdir(parents=True)
        marker.write_text(f"gitdir: {admin_dir}\n", encoding="utf-8")
        (admin_dir / "commondir").write_text("../..\n", encoding="utf-8")
        (admin_dir / "gitdir").write_text(f"{marker}\n", encoding="utf-8")
        return worktree, common_dir, admin_dir

    def test_accepts_standalone_repository_metadata(self) -> None:
        repository = self.code_root / "standalone"
        common_dir = repository / ".git"
        common_dir.mkdir(parents=True)
        self.write_common_config(common_dir)

        reject_unsafe_git_config(repository, self.code_root)

    def test_preserves_single_argument_standalone_validation(self) -> None:
        repository = self.code_root / "standalone"
        common_dir = repository / ".git"
        common_dir.mkdir(parents=True)
        self.write_common_config(common_dir)

        reject_unsafe_git_config(repository)

    def test_accepts_linked_worktree_metadata_inside_code_root(self) -> None:
        worktree, _, _ = self.create_linked_worktree()

        reject_unsafe_git_config(worktree, self.code_root)

    def test_accepts_linked_worktree_with_generated_admin_id(self) -> None:
        worktree, _, _ = self.create_linked_worktree(admin_name="linked1")

        reject_unsafe_git_config(worktree, self.code_root)

    def test_accepts_linked_worktree_backed_by_bare_repository(self) -> None:
        common_dir = self.code_root / "primary.git"
        worktree, _, _ = self.create_linked_worktree(common_dir=common_dir)
        self.write_common_config(common_dir, bare=True)

        reject_unsafe_git_config(worktree, self.code_root)

    def test_accepts_push_auto_setup_remote_for_standalone_repository(self) -> None:
        repository = self.code_root / "standalone"
        common_dir = repository / ".git"
        common_dir.mkdir(parents=True)
        self.write_common_config(common_dir)
        self.append_common_config(common_dir, "[push]\n\tautoSetupRemote = true\n")

        reject_unsafe_git_config(repository, self.code_root)

    def test_accepts_push_auto_setup_remote_from_linked_common_config(self) -> None:
        worktree, common_dir, _ = self.create_linked_worktree()
        self.append_common_config(common_dir, "[push]\n\tautoSetupRemote = true\n")

        reject_unsafe_git_config(worktree, self.code_root)

    def test_rejects_other_push_option(self) -> None:
        repository = self.code_root / "standalone"
        common_dir = repository / ".git"
        common_dir.mkdir(parents=True)
        self.write_common_config(common_dir)
        self.append_common_config(common_dir, "[push]\n\tdefault = simple\n")

        with self.assertRaises(SafetyError):
            reject_unsafe_git_config(repository, self.code_root)

    def test_rejects_mixed_push_options_from_linked_common_config(self) -> None:
        worktree, common_dir, _ = self.create_linked_worktree()
        self.append_common_config(
            common_dir,
            "[push]\n\tautoSetupRemote = true\n\tdefault = simple\n",
        )

        with self.assertRaises(SafetyError):
            reject_unsafe_git_config(worktree, self.code_root)

    def test_rejects_linked_worktree_admin_directory_outside_code_root(self) -> None:
        worktree = self.code_root / "linked"
        worktree.mkdir()
        outside = Path(self.temporary.name).resolve() / "outside" / "worktrees" / "linked"
        outside.mkdir(parents=True)
        (worktree / ".git").write_text(f"gitdir: {outside}\n", encoding="utf-8")

        with self.assertRaises(SafetyError):
            reject_unsafe_git_config(worktree, self.code_root)

    def test_rejects_linked_worktree_common_directory_outside_code_root(self) -> None:
        worktree, _, admin_dir = self.create_linked_worktree()
        outside = Path(self.temporary.name).resolve() / "outside.git"
        outside.mkdir()
        self.write_common_config(outside)
        (admin_dir / "commondir").write_text(f"{outside}\n", encoding="utf-8")

        with self.assertRaises(SafetyError):
            reject_unsafe_git_config(worktree, self.code_root)

    def test_rejects_linked_worktree_with_mismatched_back_pointer(self) -> None:
        worktree, _, admin_dir = self.create_linked_worktree()
        (admin_dir / "gitdir").write_text(
            f"{self.code_root / 'different' / '.git'}\n",
            encoding="utf-8",
        )

        with self.assertRaises(SafetyError):
            reject_unsafe_git_config(worktree, self.code_root)

    def test_rejects_linked_worktree_specific_config(self) -> None:
        worktree, _, admin_dir = self.create_linked_worktree()
        (admin_dir / "config.worktree").write_text(
            "[core]\n\tbare = false\n",
            encoding="utf-8",
        )

        with self.assertRaises(SafetyError):
            reject_unsafe_git_config(worktree, self.code_root)


if __name__ == "__main__":
    unittest.main()
