from __future__ import annotations

from fnmatch import fnmatchcase
import json
import unittest
from pathlib import Path
from typing import Final, Mapping, cast


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON: Final[str] = "./.venv/Scripts/python.exe"
EXPECTED_BASH_POSITIVE_RULES: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        (
            "git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false -c core.pager=cat -c color.ui=false -c diff.external= -c interactive.diffFilter= -c protocol.ext.allow=never log --no-show-signature --no-ext-diff --no-textconv --no-color *",
            "allow",
        ),
        (
            "git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false -c core.pager=cat -c color.ui=false -c diff.external= -c interactive.diffFilter= -c protocol.ext.allow=never diff --no-ext-diff --no-textconv --no-color *",
            "allow",
        ),
        (
            "git --no-pager -c core.hooksPath=NUL -c core.fsmonitor=false -c core.pager=cat -c color.ui=false -c diff.external= -c interactive.diffFilter= -c protocol.ext.allow=never show --no-show-signature --no-ext-diff --no-textconv --no-color *",
            "allow",
        ),
        ("git status", "allow"),
        ("git status --short", "allow"),
        ("git add -- *", "allow"),
        ("git commit -F OPENCODE_COMMIT_MESSAGE", "allow"),
        ("./.venv/Scripts/python.exe -m unittest tests.test_project_registry -v", "allow"),
        ("./.venv/Scripts/python.exe -m unittest tests.test_sync_safety -v", "allow"),
        ("./.venv/Scripts/python.exe -m unittest tests.test_sync_repositories -v", "allow"),
        ("./.venv/Scripts/python.exe -m unittest tests.test_command_contracts -v", "allow"),
        ("./.venv/Scripts/python.exe -m unittest tests.test_opencode_git_permissions -v", "allow"),
        ("./.venv/Scripts/python.exe -m unittest tests.test_opencode_permissions -v", "allow"),
        ("./.venv/Scripts/python.exe -m unittest discover -s tests -p \"test_*.py\" -v", "allow"),
        (
            "./.venv/Scripts/python.exe -m compileall -q tools/project_registry.py tools/registry_yaml.py tests/test_project_registry.py",
            "allow",
        ),
        ("./.venv/Scripts/python.exe -m compileall -q tools tests", "allow"),
        ("./.venv/Scripts/python.exe tools/registry_snapshot.py", "allow"),
        ("./.venv/Scripts/python.exe tools/sync_repositories.py", "ask"),
        (
            "./.venv/Scripts/python.exe tools/sync_repositories.py --registry-sha256 *",
            "ask",
        ),
        ("./.venv/Scripts/python.exe tools/sync_repositories.py --project *", "ask"),
        ("./.venv/Scripts/python.exe tools/send_mail.py --list-users", "allow"),
        (
            "./.venv/Scripts/python.exe tools/send_mail.py --validate-user [A-Za-z0-9]",
            "allow",
        ),
        (
            "./.venv/Scripts/python.exe tools/send_mail.py --validate-user [A-Za-z0-9][A-Za-z0-9_-]*",
            "allow",
        ),
        (
            "./.venv/Scripts/python.exe tools/send_mail.py --resolve-user [A-Za-z0-9]*@[A-Za-z0-9]*.[A-Za-z0-9]*",
            "allow",
        ),
        (
            "./.venv/Scripts/python.exe tools/send_mail.py --send --user * --markdown reports/daily/**/*.md --html reports/daily/**/*.html",
            "ask",
        ),
    }
)


def _resolve_bash_action(command: str, rules: Mapping[str, str]) -> str:
    resolved_action: str | None = None
    for pattern, action in rules.items():
        if fnmatchcase(command, pattern):
            resolved_action = action
    if resolved_action is None:
        raise AssertionError(f"未命中任何 bash 规则: {command}")
    return resolved_action


class OpenCodePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
        config = cast(dict[str, object], raw)
        cls.permissions = cast(dict[str, object], config["permission"])

    def test_registry_has_exact_read_permission(self) -> None:
        read_rules = cast(dict[str, str], self.permissions["read"])
        self.assertEqual(read_rules["project-registry.yaml"], "allow")
        self.assertEqual(read_rules["opencode.json"], "allow")
        self.assertEqual(read_rules.get("tests/test_opencode_git_permissions.py"), "allow")
        self.assertNotEqual(read_rules.get("*.yaml"), "allow")
        self.assertNotEqual(read_rules.get("**/*.yaml"), "allow")

    def test_secret_read_denials_remain(self) -> None:
        read_rules = cast(dict[str, str], self.permissions["read"])
        self.assertEqual(read_rules["*.env"], "deny")
        self.assertEqual(read_rules["*.env.*"], "deny")
        self.assertEqual(read_rules["**/.env"], "deny")
        self.assertEqual(read_rules["**/.env.*"], "deny")

    def test_sync_permission_is_dynamic_but_not_broad_python(self) -> None:
        bash_rules = cast(dict[str, str], self.permissions["bash"])
        self.assertEqual(_resolve_bash_action("python tools/registry_snapshot.py", bash_rules), "deny")
        self.assertEqual(_resolve_bash_action(f"{VENV_PYTHON} tools/sync_repositories.py", bash_rules), "ask")
        self.assertEqual(_resolve_bash_action(f"{VENV_PYTHON} arbitrary.py", bash_rules), "deny")
        self.assertEqual(_resolve_bash_action(f"{VENV_PYTHON} -c pass", bash_rules), "deny")
        self.assertEqual(_resolve_bash_action(f"{VENV_PYTHON} tools/registry_snapshot.py", bash_rules), "allow")
        self.assertEqual(
            _resolve_bash_action(f"{VENV_PYTHON} -m unittest tests.test_opencode_permissions -v", bash_rules),
            "allow",
        )
        self.assertEqual(
            _resolve_bash_action(
                f"{VENV_PYTHON} tools/sync_repositories.py --registry-sha256 deadbeef",
                bash_rules,
            ),
            "ask",
        )
        self.assertEqual(
            _resolve_bash_action(
                f"{VENV_PYTHON} tools/sync_repositories.py --project api",
                bash_rules,
            ),
            "ask",
        )
        safe_send = (
            f"{VENV_PYTHON} tools/send_mail.py --send --user alice "
            "--markdown reports/daily/2026-07-16/alice-code-review.md "
            "--html reports/daily/2026-07-16/alice-code-review.html"
        )
        self.assertEqual(_resolve_bash_action(safe_send, bash_rules), "ask")
        self.assertEqual(
            _resolve_bash_action(
                f"{VENV_PYTHON} tools/send_mail.py --resolve-user alice@example.com",
                bash_rules,
            ),
            "allow",
        )
        self.assertEqual(
            _resolve_bash_action(
                f"{VENV_PYTHON} tools/send_mail.py --resolve-user alice@example.com extra",
                bash_rules,
            ),
            "deny",
        )
        self.assertEqual(
            _resolve_bash_action(
                f"{safe_send} extra",
                bash_rules,
            ),
            "deny",
        )
        for symbol, label in (
            (";", "semicolon"),
            ("&", "ampersand"),
            ("|", "pipe"),
            (">", "redirection"),
            ("<", "input-redirection"),
            ("`", "backtick"),
            ("$", "dollar"),
            ("(", "parentheses-open"),
            (")", "parentheses-close"),
            ("{", "braces-open"),
            ("}", "braces-close"),
            ("^", "caret"),
            ("%", "percent"),
            ("#", "hash"),
            (",", "comma"),
            ("\r", "cr"),
            ("\n", "lf"),
        ):
            self.assertEqual(
                _resolve_bash_action(
                    f"{VENV_PYTHON} tools/sync_repositories.py "
                    f"--registry-sha256 deadbeef{symbol}",
                    bash_rules,
                ),
                "deny",
                label,
            )
        self.assertNotIn("python tools/registry_snapshot.py", bash_rules)
        self.assertNotIn(f"& {VENV_PYTHON} tools/registry_snapshot.py", bash_rules)
        self.assertNotIn(r".\.venv\Scripts\python.exe tools/registry_snapshot.py", bash_rules)
        self.assertNotIn(
            "python tools/sync_repositories.py --project \"api\"",
            bash_rules,
        )
        bare_send_mail_denies = [
            command
            for command, action in bash_rules.items()
            if command.startswith("python tools/send_mail.py") and action == "deny"
        ]
        self.assertGreater(len(bare_send_mail_denies), 0)
        for command in bare_send_mail_denies:
            venv_command = command.replace("python", VENV_PYTHON, 1)
            self.assertEqual(bash_rules[venv_command], "deny")

    def test_bash_positive_rules_are_exactly_expected(self) -> None:
        bash_rules = cast(dict[str, str], self.permissions["bash"])
        actual_positive_rules = frozenset(
            (pattern, action)
            for pattern, action in bash_rules.items()
            if action in {"allow", "ask"}
        )
        self.assertEqual(actual_positive_rules, EXPECTED_BASH_POSITIVE_RULES)


if __name__ == "__main__":
    unittest.main()
