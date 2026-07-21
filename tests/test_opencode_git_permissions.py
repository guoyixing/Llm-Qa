from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Final, cast

from tests.test_opencode_permissions import _resolve_bash_action


ROOT = Path(__file__).resolve().parents[1]
GIT_PREFIX: Final[str] = (
    "git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false "
    "-c core.pager=cat -c color.ui=false -c diff.external= "
    "-c interactive.diffFilter= -c protocol.ext.allow=never"
)


class OpenCodeGitPermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
        config = cast(dict[str, object], raw)
        permissions = cast(dict[str, object], config["permission"])
        cls.bash_rules = cast(dict[str, str], permissions["bash"])
        cls.edit_rules = cast(dict[str, str], permissions["edit"])

    def test_safe_local_git_commit_workflow_is_allowed(self) -> None:
        # Given
        commands = (
            "git status",
            "git status --short",
            f"{GIT_PREFIX} diff --no-ext-diff --no-textconv --no-color HEAD",
            f"{GIT_PREFIX} log --no-show-signature --no-ext-diff "
            "--no-textconv --no-color --oneline -10",
            "git add -- opencode.json tests/test_opencode_permissions.py "
            "tests/test_opencode_git_permissions.py",
            "git commit -F OPENCODE_COMMIT_MESSAGE",
        )

        # When / Then
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(_resolve_bash_action(command, self.bash_rules), "allow")

    def test_dangerous_git_commit_variants_remain_denied(self) -> None:
        # Given
        commands = (
            'git commit -m "feat(core): 中文主题"',
            "git commit -F other-message.txt",
            "git commit -F .git/OPENCODE_COMMIT_MESSAGE",
            "git commit -F ./OPENCODE_COMMIT_MESSAGE",
            'git commit -F "OPENCODE_COMMIT_MESSAGE"',
            "git commit -F OPENCODE_COMMIT_MESSAGE --allow-empty",
            "git commit --allow-empty -F OPENCODE_COMMIT_MESSAGE",
            "git commit -F OPENCODE_COMMIT_MESSAGE --amend",
            "git commit --amend -F OPENCODE_COMMIT_MESSAGE",
            "git commit -F OPENCODE_COMMIT_MESSAGE --no-verify",
            "git commit --no-verify -F OPENCODE_COMMIT_MESSAGE",
            "git commit -F OPENCODE_COMMIT_MESSAGE -n",
            "git commit -n -F OPENCODE_COMMIT_MESSAGE",
            "git diff",
            "git diff --cached",
            "git log --oneline -10",
            "git branch --show-current",
            "git push origin main",
            "git fetch origin",
            "git pull origin main",
            "git clone https://example.invalid/repository.git",
            "git ls-remote origin",
            "git reset --hard HEAD",
            "git rebase main",
            "git checkout main",
            "git clean -fd",
            "git restore .",
            "$env:GIT_MASTER='1'; git commit -F OPENCODE_COMMIT_MESSAGE",
        )

        # When / Then
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(_resolve_bash_action(command, self.bash_rules), "deny")

    def test_safe_git_rules_precede_specific_denials(self) -> None:
        # Given
        patterns = tuple(self.bash_rules)
        git_default = patterns.index("git *")
        shell_denial = patterns.index("*;*")

        # When / Then
        for pattern in (
            "git status",
            "git status --short",
            "git add -- *",
            "git commit -F OPENCODE_COMMIT_MESSAGE",
        ):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, patterns)
                self.assertGreater(patterns.index(pattern), git_default)
                self.assertLess(patterns.index(pattern), shell_denial)
        for pattern in (
            "git commit *--amend*",
            "git commit *--no-verify*",
            "git commit *-n*",
        ):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, patterns)
                self.assertGreater(
                    patterns.index(pattern),
                    patterns.index("git commit -F OPENCODE_COMMIT_MESSAGE"),
                )
                self.assertLess(patterns.index(pattern), shell_denial)
        positive_patterns = tuple(
            pattern
            for pattern, action in self.bash_rules.items()
            if action in {"allow", "ask"}
        )
        self.assertFalse(any("GIT_MASTER" in pattern for pattern in positive_patterns))
        self.assertFalse(any("$env:" in pattern for pattern in positive_patterns))

    def test_workspace_root_commit_message_is_writable_while_git_metadata_is_protected(
        self,
    ) -> None:
        # Given
        message_path = "OPENCODE_COMMIT_MESSAGE"
        protected_paths = (
            ".git",
            ".git/config",
            ".git/hooks/pre-commit",
            ".git/HEAD",
            ".git/refs/heads/main",
            ".git/index",
            ".git/OPENCODE_COMMIT_MESSAGE",
        )

        # When / Then
        self.assertEqual(_resolve_bash_action(message_path, self.edit_rules), "allow")
        for path in protected_paths:
            with self.subTest(path=path):
                self.assertEqual(_resolve_bash_action(path, self.edit_rules), "deny")


if __name__ == "__main__":
    unittest.main()
