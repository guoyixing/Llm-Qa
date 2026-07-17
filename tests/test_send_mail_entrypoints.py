from collections.abc import Mapping
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
from typing import Final, NamedTuple
import unittest


ROOT: Final = Path(__file__).resolve().parents[1]
TOOLS: Final = ROOT / "tools"
SCRIPT: Final = TOOLS / "send_mail.py"
SAFE_VALUES: Final = {
    "USER_1_ID": "alice",
    "USER_1_NAME": "张三",
    "USER_1_GIT_EMAIL": "alice@example.com",
    "USER_1_LEADER_EMAIL": "leader@example.com",
    "DEFAULT_LEADER_EMAIL": "default@example.com",
    "SMTP_HOST": "smtp.invalid",
    "SMTP_PORT": "465",
    "SMTP_TIMEOUT_SECONDS": "1",
    "SMTP_USE_TLS": "false",
    "SMTP_USE_SSL": "true",
    "SMTP_FROM": "sender@example.com",
}


class CliCase(NamedTuple):
    argv: tuple[str, ...]
    expected: str


class Invocation(NamedTuple):
    command: tuple[str, ...]
    cwd: Path
    environment: Mapping[str, str]


CASES: Final = (
    CliCase(("--list-users",), '{"user_ids":["alice"]}'),
    CliCase(
        ("--validate-user", "alice"),
        '{"status":"VALID","user_name":"张三"}',
    ),
    CliCase(
        ("--resolve-user", "alice@example.com"),
        '{"user_id":"alice","user_name":"张三"}',
    ),
)


def child_environment() -> dict[str, str]:
    environment = {
        key: value
        for key in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP", "PATHEXT")
        if (value := os.environ.get(key)) is not None
    }
    environment.update(SAFE_VALUES)
    environment.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    return environment


def prepare_root(temporary: str, values: Mapping[str, str]) -> Path:
    root = Path(temporary)
    tools = root / "tools"
    tools.mkdir()
    for name in ("send_mail.py", "user_identity.py"):
        _ = shutil.copy2(TOOLS / name, tools)
    package_marker = TOOLS / "__init__.py"
    if package_marker.exists():
        _ = shutil.copy2(package_marker, tools)
    _ = (root / ".env").write_text(
        "\n".join(f"{key}={value}" for key, value in values.items()),
        encoding="utf-8",
    )
    return root


def invoke(request: Invocation) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        request.command,
        cwd=request.cwd,
        env=request.environment,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=10,
    )


class SendMailEntrypointTests(unittest.TestCase):
    def test_tools_is_an_empty_regular_package(self) -> None:
        marker = TOOLS / "__init__.py"

        self.assertTrue(marker.is_file())
        self.assertEqual(marker.read_bytes(), b"")

    def test_direct_and_module_identity_surfaces_are_identical(self) -> None:
        with TemporaryDirectory() as temporary:
            root = prepare_root(temporary, SAFE_VALUES)
            environment = child_environment()

            for case in CASES:
                with self.subTest(argv=case.argv):
                    direct = invoke(
                        Invocation(
                            (sys.executable, "tools/send_mail.py", *case.argv),
                            root,
                            environment,
                        ),
                    )
                    module = invoke(
                        Invocation(
                            (sys.executable, "-m", "tools.send_mail", *case.argv),
                            root,
                            environment,
                        ),
                    )

                    self.assertEqual(direct.returncode, 0, direct.stderr)
                    self.assertEqual(direct.stdout.strip(), case.expected)
                    self.assertEqual(direct.stderr, "")
                    self.assertEqual(direct.returncode, module.returncode)
                    self.assertEqual(direct.stdout, module.stdout)
                    self.assertEqual(direct.stderr, module.stderr)

    def test_attacker_paths_cannot_shadow_trusted_direct_entry(self) -> None:
        with TemporaryDirectory() as trusted, TemporaryDirectory() as attacker:
            trusted_root = prepare_root(trusted, SAFE_VALUES)
            attacker_root = Path(attacker)
            fake_tools = attacker_root / "tools"
            fake_tools.mkdir()
            _ = (fake_tools / "__init__.py").write_text("", encoding="utf-8")
            _ = (fake_tools / "send_mail.py").write_text(
                'print("ATTACKER_TOOLS")',
                encoding="utf-8",
            )
            _ = (attacker_root / "user_identity.py").write_text(
                'raise RuntimeError("ATTACKER_IDENTITY")',
                encoding="utf-8",
            )
            environment = child_environment()
            environment["PYTHONPATH"] = str(attacker_root)

            completed = invoke(
                Invocation(
                    (
                        sys.executable,
                        str(trusted_root / "tools" / "send_mail.py"),
                        "--list-users",
                    ),
                    attacker_root,
                    environment,
                ),
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), '{"user_ids":["alice"]}')
        self.assertEqual(completed.stderr, "")

    def test_repeated_direct_invocations_do_not_leak_state(self) -> None:
        with TemporaryDirectory() as temporary:
            root = prepare_root(temporary, SAFE_VALUES)
            environment = child_environment()
            request = Invocation(
                (sys.executable, "tools/send_mail.py", "--list-users"),
                root,
                environment,
            )
            first = invoke(request)
            changed = dict(SAFE_VALUES)
            changed.update(
                {
                    "USER_1_ID": "bob",
                    "USER_1_NAME": "李四",
                    "USER_1_GIT_EMAIL": "bob@example.com",
                },
            )
            _ = (root / ".env").write_text(
                "\n".join(f"{key}={value}" for key, value in changed.items()),
                encoding="utf-8",
            )
            second = invoke(request)

        self.assertEqual(first.stdout.strip(), '{"user_ids":["alice"]}')
        self.assertEqual(second.stdout.strip(), '{"user_ids":["bob"]}')
        self.assertEqual((first.returncode, second.returncode), (0, 0))
        self.assertEqual((first.stderr, second.stderr), ("", ""))

    def test_package_import_uses_canonical_user_identity(self) -> None:
        from tools import send_mail, user_identity

        self.assertIs(send_mail.user_identity, user_identity)
        self.assertEqual(user_identity.__name__, "tools.user_identity")

    def test_wrapper_preserves_modules_and_child_nonzero_exit(self) -> None:
        probe = textwrap.dedent(
            f"""
            import runpy, subprocess, sys
            import tools, tools.user_identity
            parent = sys.modules["tools"]
            child = sys.modules["tools.user_identity"]
            calls = []
            def fake_run(command, *, cwd, check):
                calls.append((command, cwd, check))
                return subprocess.CompletedProcess(command, 7)
            subprocess.run = fake_run
            try:
                runpy.run_path({str(SCRIPT)!r}, run_name="probe")
            except SystemExit as error:
                print(f"exit={{error.code}}")
            print(f"called={{len(calls)}}")
            print(f"parent_same={{sys.modules['tools'] is parent}}")
            print(f"child_same={{sys.modules['tools.user_identity'] is child}}")
            print(f"command={{calls[0][0] if calls else None}}")
            print(f"cwd={{calls[0][1] if calls else None}}")
            print(f"check={{calls[0][2] if calls else None}}")
            """,
        )
        completed = invoke(
            Invocation(
                (sys.executable, "-c", probe),
                ROOT,
                child_environment(),
            ),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("exit=7", completed.stdout)
        self.assertIn("called=1", completed.stdout)
        self.assertIn("parent_same=True", completed.stdout)
        self.assertIn("child_same=True", completed.stdout)
        self.assertIn("'-m', 'tools.send_mail'", completed.stdout)
        self.assertIn(f"cwd={ROOT}", completed.stdout)
        self.assertIn("check=False", completed.stdout)

    def test_wrapper_propagates_keyboard_interrupt_without_module_mutation(self) -> None:
        probe = textwrap.dedent(
            f"""
            import runpy, subprocess, sys
            import tools, tools.user_identity
            parent = sys.modules["tools"]
            child = sys.modules["tools.user_identity"]
            def interrupted(*_args, **_kwargs):
                raise KeyboardInterrupt
            subprocess.run = interrupted
            try:
                runpy.run_path({str(SCRIPT)!r}, run_name="probe")
            except KeyboardInterrupt:
                print("keyboard_interrupt=True")
            else:
                print("keyboard_interrupt=False")
            print(f"parent_same={{sys.modules['tools'] is parent}}")
            print(f"child_same={{sys.modules['tools.user_identity'] is child}}")
            """,
        )
        completed = invoke(
            Invocation(
                (sys.executable, "-c", probe),
                ROOT,
                child_environment(),
            ),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("keyboard_interrupt=True", completed.stdout)
        self.assertIn("parent_same=True", completed.stdout)
        self.assertIn("child_same=True", completed.stdout)


if __name__ == "__main__":
    _ = unittest.main()
