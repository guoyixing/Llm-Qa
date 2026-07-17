from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import ANY, patch

from tools.send_mail import Report, main, report
from tools.user_identity import EmailAddress, UserId


VALID_ENV = {
    "USER_1_ID": "alice",
    "USER_1_NAME": "张三",
    "USER_1_GIT_EMAIL": "alice@example.com",
    "USER_1_LEADER_EMAIL": "leader@example.com",
    "DEFAULT_LEADER_EMAIL": "default@example.com",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "465",
    "SMTP_TIMEOUT_SECONDS": "10",
    "SMTP_USE_TLS": "false",
    "SMTP_USE_SSL": "true",
    "SMTP_FROM": "sender@example.com",
}
ROOT = Path(__file__).resolve().parents[1]


class SendMailIdentityTests(unittest.TestCase):
    def invoke(self, argv: list[str], values: dict[str, str]) -> tuple[int, str]:
        output = StringIO()
        with (
            patch("sys.argv", ["send_mail.py", *argv]),
            patch("tools.send_mail.env", return_value=values),
            redirect_stdout(output),
        ):
            exit_code = main()
        return exit_code, output.getvalue().strip()

    def test_identity_modes_return_exact_display_name_payloads(self) -> None:
        # Given
        cases = (
            (["--list-users"], '{"user_ids":["alice"]}'),
            (
                ["--validate-user", "alice"],
                '{"status":"VALID","user_name":"张三"}',
            ),
            (
                ["--resolve-user", "alice@example.com"],
                '{"user_id":"alice","user_name":"张三"}',
            ),
        )

        # When / Then
        for argv, expected in cases:
            with self.subTest(argv=argv):
                exit_code, output = self.invoke(argv, VALID_ENV)
                self.assertEqual(exit_code, 0)
                self.assertEqual(output, expected)

    def test_direct_script_identity_modes_return_authorized_json(self) -> None:
        # Given
        cases = (
            (["--list-users"], '{"user_ids":["alice"]}'),
            (
                ["--validate-user", "alice"],
                '{"status":"VALID","user_name":"张三"}',
            ),
            (
                ["--resolve-user", "alice@example.com"],
                '{"user_id":"alice","user_name":"张三"}',
            ),
        )
        safe_values = dict(VALID_ENV)
        safe_values["SMTP_HOST"] = "smtp.invalid"
        child_env = {
            key: value
            for key in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP", "PATHEXT")
            if (value := os.environ.get(key)) is not None
        }
        child_env.update(safe_values)
        child_env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})

        with TemporaryDirectory() as temporary:
            synthetic_root = Path(temporary)
            synthetic_tools = synthetic_root / "tools"
            synthetic_tools.mkdir()
            _ = shutil.copy2(ROOT / "tools" / "__init__.py", synthetic_tools)
            _ = shutil.copy2(ROOT / "tools" / "send_mail.py", synthetic_tools)
            _ = shutil.copy2(ROOT / "tools" / "user_identity.py", synthetic_tools)
            _ = (synthetic_root / ".env").write_text(
                "\n".join(f"{key}={value}" for key, value in safe_values.items()),
                encoding="utf-8",
            )

            # When / Then
            for argv, expected in cases:
                with self.subTest(argv=argv):
                    completed = subprocess.run(
                        [sys.executable, "tools/send_mail.py", *argv],
                        cwd=synthetic_root,
                        env=child_env,
                        capture_output=True,
                        encoding="utf-8",
                        check=False,
                        timeout=10,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(completed.stdout.strip(), expected)
                    self.assertEqual(completed.stderr, "")

    def test_invalid_name_globally_closes_all_identity_modes(self) -> None:
        # Given
        invalid_names = (None, "  ", "TOP-SECRET-" + "名" * 129, "secret\x00name")
        expected_by_mode = {
            "--list-users": '{"status":"用户姓名配置无效","error_code":"用户配置错误"}',
            "--validate-user": '{"status":"身份校验失败","error_code":"用户配置错误"}',
            "--resolve-user": '{"status":"身份解析失败","error_code":"身份解析失败"}',
        }

        # When / Then
        for raw_name in invalid_names:
            values = dict(VALID_ENV)
            if raw_name is None:
                del values["USER_1_NAME"]
            else:
                values["USER_1_NAME"] = raw_name
            for mode, expected in expected_by_mode.items():
                argument = "alice@example.com" if mode == "--resolve-user" else "alice"
                argv = [mode] if mode == "--list-users" else [mode, argument]
                with self.subTest(raw_name=raw_name, mode=mode):
                    exit_code, output = self.invoke(argv, values)
                    self.assertEqual(exit_code, 2)
                    self.assertEqual(output, expected)
                    if raw_name:
                        self.assertNotIn(raw_name, output)

    def test_unknown_identity_and_duplicate_email_fail_safely(self) -> None:
        # Given
        duplicate = dict(VALID_ENV)
        duplicate.update(
            {
                "USER_2_ID": "bob",
                "USER_2_NAME": "李四",
                "USER_2_GIT_EMAIL": "ALICE@example.com",
            },
        )
        cases = (
            (
                ["--validate-user", "bob"],
                VALID_ENV,
                3,
                '{"status":"INVALID","error_code":"用户不存在"}',
            ),
            (
                ["--resolve-user", "bob@example.com"],
                VALID_ENV,
                3,
                '{"status":"身份解析失败","error_code":"身份无法唯一解析"}',
            ),
            (
                ["--list-users"],
                duplicate,
                2,
                '{"status":"Git 作者邮箱无效或重复","error_code":"用户配置错误"}',
            ),
        )

        # When / Then
        for argv, values, expected_code, expected_output in cases:
            with self.subTest(argv=argv):
                exit_code, output = self.invoke(argv, values)
                self.assertEqual(exit_code, expected_code)
                self.assertEqual(output, expected_output)
                self.assertNotIn("alice@example.com", output.casefold())

    def test_malformed_email_and_id_outputs_are_sanitized(self) -> None:
        # Given
        invalid_email = dict(VALID_ENV)
        invalid_email["USER_1_GIT_EMAIL"] = "SECRET <alice@example.com>"
        cases = (
            (["--list-users"], invalid_email, "SECRET <alice@example.com>"),
            (["--validate-user", "secret bad id"], VALID_ENV, "secret bad id"),
            (["--resolve-user", "secret;@example.com"], VALID_ENV, "secret;@example.com"),
        )

        # When / Then
        for argv, values, secret in cases:
            with self.subTest(argv=argv):
                exit_code, output = self.invoke(argv, values)
                self.assertNotEqual(exit_code, 0)
                self.assertNotIn(secret, output)

    def test_identity_modes_never_invoke_delivery(self) -> None:
        # Given
        modes = (
            ["--list-users"],
            ["--validate-user", "alice"],
            ["--resolve-user", "alice@example.com"],
        )

        # When
        with patch("tools.send_mail.deliver") as delivery:
            results = tuple(self.invoke(argv, VALID_ENV) for argv in modes)

        # Then
        self.assertTrue(all(exit_code == 0 for exit_code, _ in results))
        delivery.assert_not_called()

    def test_report_paths_and_subject_remain_ascii_id_based(self) -> None:
        # Given
        with TemporaryDirectory() as temporary:
            daily = Path(temporary) / "daily"
            day = daily / "2026-07-17"
            day.mkdir(parents=True)
            markdown = day / "alice-code-review.md"
            html = day / "alice-code-review.html"
            _ = markdown.write_text("# 日报\n", encoding="utf-8")
            _ = html.write_text(
                "<html><body>张三（alice）</body></html>",
                encoding="utf-8",
            )

            # When
            with patch("tools.send_mail.DAILY_DIR", daily):
                item = report("alice", markdown, html)

        # Then
        self.assertEqual(item.user_id, "alice")
        self.assertEqual(item.subject, "2026-07-17 alice 代码质量审查日报")
        self.assertNotIn("张三", item.subject)

    def test_send_mode_keeps_id_argv_and_manager_routing(self) -> None:
        # Given
        item = Report(
            user_id=UserId("alice"),
            report_date="2026-07-17",
            subject="2026-07-17 alice 代码质量审查日报",
            html="<html><body>张三（alice）</body></html>",
        )
        argv = [
            "--send",
            "--user",
            "alice",
            "--markdown",
            "reports/daily/2026-07-17/alice-code-review.md",
            "--html",
            "reports/daily/2026-07-17/alice-code-review.html",
        ]

        # When
        with (
            patch("tools.send_mail.report", return_value=item) as build_report,
            patch("tools.send_mail.deliver", return_value="ACCEPTED") as delivery,
        ):
            exit_code, output = self.invoke(argv, VALID_ENV)

        # Then
        self.assertEqual(exit_code, 0)
        self.assertIn('"user_id":"alice"', output)
        build_report.assert_called_once_with(
            "alice",
            Path("reports/daily/2026-07-17/alice-code-review.md"),
            Path("reports/daily/2026-07-17/alice-code-review.html"),
        )
        delivery.assert_called_once_with(ANY, EmailAddress("leader@example.com"), item)


if __name__ == "__main__":
    _ = unittest.main()
