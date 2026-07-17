from __future__ import annotations

from io import BytesIO, StringIO, TextIOWrapper
import json
import unittest
from pathlib import Path
from typing import Callable, Final, Literal, NamedTuple, TypeAlias
from unittest.mock import patch

from tools.registry_snapshot import main as snapshot_main
from tools.send_mail import main as send_mail_main
from tools.sync_repositories import main as sync_main


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON: Final[str] = "./.venv/Scripts/python.exe"
COMMANDS = (
    ROOT / ".opencode" / "commands" / "sync-repositories.md",
    ROOT / ".opencode" / "commands" / "daily-review.md",
    ROOT / ".opencode" / "commands" / "code-review.md",
)
TOOLS = (
    ROOT / "tools" / "send_mail.py",
    ROOT / "tools" / "sync_repositories.py",
)
RESULT_FIELDS = (
    "project_id",
    "status",
    "local_path",
    "default_branch",
    "repository_url_config_key",
    "commit",
    "message",
)


def invoke_snapshot_argument_error() -> int:
    with patch(
        "tools.registry_snapshot.load_project_registry",
        side_effect=AssertionError("参数错误不得读取注册表"),
    ):
        return snapshot_main(("unexpected",))


def invoke_sync_argument_error() -> int:
    with (
        patch("sys.argv", ["sync_repositories.py", "--unexpected"]),
        patch(
            "tools.sync_repositories.load_project_registry",
            side_effect=AssertionError("参数错误不得读取注册表"),
        ),
        patch(
            "tools.sync_repositories.load_config",
            side_effect=AssertionError("参数错误不得读取 .env"),
        ),
        patch(
            "tools.sync_repositories.run_git",
            side_effect=AssertionError("参数错误不得运行 Git"),
        ),
        patch(
            "tools.sync_repositories.synchronize",
            side_effect=AssertionError("参数错误不得同步仓库"),
        ),
    ):
        return sync_main()


def invoke_send_mail_argument_error() -> int:
    with (
        patch("sys.argv", ["send_mail.py", "--unexpected"]),
        patch(
            "tools.send_mail.env",
            side_effect=AssertionError("参数错误不得读取 .env"),
        ),
        patch(
            "tools.send_mail.report",
            side_effect=AssertionError("参数错误不得检查报告"),
        ),
        patch(
            "tools.send_mail.deliver",
            side_effect=AssertionError("参数错误不得访问网络或发送邮件"),
        ),
    ):
        return send_mail_main()


JsonShape = Literal["object", "array"]
JsonValue: TypeAlias = bool | int | float | str | None | list["JsonValue"] | dict[str, "JsonValue"]


class CliCase(NamedTuple):
    name: str
    invoke: Callable[[], int]
    exit_code: int
    shape: JsonShape
    expected: JsonValue
    chinese: str


CLI_CASES: Final[tuple[CliCase, ...]] = (
    CliCase(
        "snapshot",
        invoke_snapshot_argument_error,
        2,
        "object",
        {"error": "项目注册表加载失败"},
        "项目注册表加载失败",
    ),
    CliCase(
        "sync",
        invoke_sync_argument_error,
        3,
        "array",
        [
            {
                "project_id": "*",
                "status": "failed",
                "local_path": "",
                "default_branch": "",
                "repository_url_config_key": "",
                "commit": "",
                "message": "全局注册表或同步配置无效。",
            }
        ],
        "全局注册表或同步配置无效。",
    ),
    CliCase(
        "send-mail",
        invoke_send_mail_argument_error,
        2,
        "object",
        {"status": "命令行参数无效", "error_code": "参数错误"},
        "命令行参数无效",
    ),
)


class CommandContractTests(unittest.TestCase):
    def assert_json_output(self, rendered: str, case: CliCase) -> None:
        expected = json.dumps(case.expected, ensure_ascii=False, separators=(",", ":"))
        self.assertEqual(rendered.strip(), expected)
        self.assertEqual(rendered.lstrip().startswith("{"), case.shape == "object")
        self.assertIn(case.chinese, rendered)
        self.assertNotIn(r"\u", rendered)

    def test_cli_argument_errors_support_string_io(self) -> None:
        for case in CLI_CASES:
            with self.subTest(cli=case.name):
                output = StringIO()

                with patch("sys.stdout", output):
                    exit_code = case.invoke()

                self.assertEqual(exit_code, case.exit_code)
                self.assert_json_output(output.getvalue(), case)

    def test_cli_argument_errors_reconfigure_non_utf8_streams(self) -> None:
        for case in CLI_CASES:
            with self.subTest(cli=case.name):
                raw = BytesIO()
                output = TextIOWrapper(raw, encoding="cp1252", newline="\n")
                try:
                    with patch("sys.stdout", output):
                        exit_code = case.invoke()
                    output.flush()
                    rendered = raw.getvalue().decode("utf-8")
                finally:
                    try:
                        _ = output.detach()
                    except ValueError:
                        raw.close()

                self.assertEqual(exit_code, case.exit_code)
                self.assert_json_output(rendered, case)

    def test_all_commands_use_root_registry_without_fixed_projects(self) -> None:
        for path in COMMANDS:
            content = path.read_text(encoding="utf-8")
            self.assertIn("project-registry.yaml", content, path.name)
            self.assertIn(VENV_PYTHON, content, path.name)
            self.assertNotIn("`python tools/", content, path.name)
            self.assertNotIn("Activate.ps1", content, path.name)
            self.assertNotIn(f'"{VENV_PYTHON}"', content, path.name)
            self.assertNotIn(f"& {VENV_PYTHON}", content, path.name)
            self.assertNotIn(r".\.venv\Scripts\python.exe", content, path.name)
            self.assertNotIn("project=api", content, path.name)
            self.assertNotIn("project=web", content, path.name)
            self.assertNotIn("project=jobs", content, path.name)
            self.assertNotIn("data/code/api", content, path.name)
            self.assertNotIn("data/code/web", content, path.name)
            self.assertNotIn("data/code/jobs", content, path.name)

    def test_sync_commands_define_all_result_fields(self) -> None:
        for name in ("sync-repositories.md", "daily-review.md"):
            content = (ROOT / ".opencode" / "commands" / name).read_text(
                encoding="utf-8"
            )
            for field in RESULT_FIELDS:
                self.assertIn(f"`{field}`", content, name)
            self.assertIn("success", content, name)
            self.assertIn("failed", content, name)

    def test_daily_review_requires_one_bound_sync_invocation(self) -> None:
        content = (ROOT / ".opencode" / "commands" / "daily-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("只调用一次", content)
        self.assertIn(f"{VENV_PYTHON} tools/registry_snapshot.py", content)
        self.assertIn("--registry-sha256", content)
        self.assertIn("同一注册表快照", content)
        self.assertIn("额外", content)

    def test_manual_review_forbids_synchronization(self) -> None:
        content = (ROOT / ".opencode" / "commands" / "code-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不得调用同步脚本或同步命令", content)
        self.assertIn("不得声称工作区已同步或是远端最新", content)

    def test_tool_help_text_uses_canonical_python_prefix(self) -> None:
        for path in TOOLS:
            content = path.read_text(encoding="utf-8")
            self.assertIn(VENV_PYTHON, content, path.name)
            self.assertNotIn("python tools/", content, path.name)
            self.assertNotIn("Activate.ps1", content, path.name)
            self.assertNotIn(f'"{VENV_PYTHON}"', content, path.name)
            self.assertNotIn(f"& {VENV_PYTHON}", content, path.name)
            self.assertNotIn(r".\.venv\Scripts\python.exe", content, path.name)


if __name__ == "__main__":
    _ = unittest.main()
