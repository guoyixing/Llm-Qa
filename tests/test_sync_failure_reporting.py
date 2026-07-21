from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.sync_models import ProjectConfig, Status
from tools.sync_repositories import synchronize
from tools.sync_safety import CommandSpec, GitFailure, SafetyError


def project_config(code_root: Path, *, existing: bool = True) -> ProjectConfig:
    local_path = code_root / "example-service"
    if existing:
        local_path.mkdir(parents=True)
    else:
        code_root.mkdir(parents=True)
    return ProjectConfig(
        "example-service",
        local_path,
        "https://example.invalid/repository.git",
        "main",
        "PROJECT_EXAMPLE_SERVICE_REPO_URL",
    )


class SyncFailureReportingTests(unittest.TestCase):
    def test_git_command_failures_report_each_stage(self) -> None:
        scenarios = (
            ("clone", False, "Git clone 失败"),
            ("status", True, "工作区状态检查失败"),
            ("branch", True, "当前分支检查失败"),
            ("remote", True, "origin 绑定检查失败"),
            ("fetch", True, "Git fetch 失败"),
            ("rev-list", True, "快进条件检查失败"),
            ("pull", True, "Git pull 失败"),
        )
        secret_text = "unexpected credential detail"
        for failing_command, existing, expected_stage in scenarios:
            with self.subTest(command=failing_command):
                with tempfile.TemporaryDirectory() as temporary:
                    code_root = Path(temporary) / "data" / "code"
                    config = project_config(code_root, existing=existing)

                    def run_git_result(spec: CommandSpec, _hooks: Path) -> str:
                        command = spec.arguments[0]
                        if command == failing_command:
                            raise GitFailure(secret_text)
                        return {
                            "clone": "",
                            "status": "",
                            "branch": "main",
                            "remote": config.url,
                            "fetch": "",
                            "rev-list": "0 1",
                            "pull": "",
                        }[command]

                    with (
                        patch("tools.sync_repositories.validate_safe_descendant"),
                        patch("tools.sync_repositories.prepare_safe_parent"),
                        patch("tools.sync_repositories._checked_repository"),
                        patch("tools.sync_repositories.checked_commit", return_value="a" * 40),
                        patch("tools.sync_repositories.run_git", side_effect=run_git_result),
                    ):
                        result = synchronize(config, code_root, Path(temporary) / "hooks")

                self.assertEqual(
                    result["message"],
                    f"{expected_stage}：Git 操作失败。",
                )
                self.assertNotIn(secret_text, result["message"])

    def test_repository_validation_reports_clone_and_existing_stages(self) -> None:
        secret_text = "unexpected repository detail"
        for existing, expected_stage in (
            (False, "克隆仓库校验失败"),
            (True, "本地仓库校验失败"),
        ):
            with self.subTest(existing=existing):
                with tempfile.TemporaryDirectory() as temporary:
                    code_root = Path(temporary) / "data" / "code"
                    config = project_config(code_root, existing=existing)
                    with (
                        patch("tools.sync_repositories.validate_safe_descendant"),
                        patch("tools.sync_repositories.prepare_safe_parent"),
                        patch("tools.sync_repositories.run_git", return_value=""),
                        patch(
                            "tools.sync_repositories._checked_repository",
                            side_effect=GitFailure(secret_text),
                        ),
                    ):
                        result = synchronize(config, code_root, Path(temporary) / "hooks")

                self.assertEqual(
                    result["message"],
                    f"{expected_stage}：Git 操作失败。",
                )
                self.assertNotIn(secret_text, result["message"])

    def test_commit_confirmation_reports_clone_pre_and_post_stages(self) -> None:
        secret_text = "unexpected commit detail"
        scenarios = (
            (False, (GitFailure(secret_text),), "克隆提交确认失败"),
            (True, (GitFailure(secret_text),), "同步前提交确认失败"),
            (True, ("a" * 40, GitFailure(secret_text)), "同步后提交确认失败"),
        )
        for existing, commit_results, expected_stage in scenarios:
            with self.subTest(existing=existing, stage=expected_stage):
                with tempfile.TemporaryDirectory() as temporary:
                    code_root = Path(temporary) / "data" / "code"
                    config = project_config(code_root, existing=existing)

                    def run_git_result(spec: CommandSpec, _hooks: Path) -> str:
                        return {
                            "clone": "",
                            "status": "",
                            "branch": "main",
                            "remote": config.url,
                            "fetch": "",
                            "rev-list": "0 1",
                            "pull": "",
                        }[spec.arguments[0]]

                    with (
                        patch("tools.sync_repositories.validate_safe_descendant"),
                        patch("tools.sync_repositories.prepare_safe_parent"),
                        patch("tools.sync_repositories._checked_repository"),
                        patch(
                            "tools.sync_repositories.checked_commit",
                            side_effect=commit_results,
                        ),
                        patch("tools.sync_repositories.run_git", side_effect=run_git_result),
                    ):
                        result = synchronize(config, code_root, Path(temporary) / "hooks")

                self.assertEqual(
                    result["message"],
                    f"{expected_stage}：Git 操作失败。",
                )
                self.assertNotIn(secret_text, result["message"])

    @patch("tools.sync_repositories.prepare_safe_parent")
    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_directory_preparation_reports_fixed_safety_category(
        self,
        _validate_descendant: Mock,
        prepare_mock: Mock,
    ) -> None:
        secret_text = "unexpected directory detail"
        prepare_mock.side_effect = SafetyError(secret_text)
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            config = project_config(code_root, existing=False)

            result = synchronize(config, code_root, Path(temporary) / "hooks")

        self.assertEqual(
            result["message"],
            "本地仓库目录准备失败：同步安全检查未通过。",
        )
        self.assertNotIn(secret_text, result["message"])

    @patch("tools.sync_repositories.checked_commit", return_value="a" * 40)
    @patch("tools.sync_repositories._checked_repository")
    @patch("tools.sync_repositories.run_git")
    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_unknown_git_failure_text_is_not_reported(
        self,
        _validate_descendant: Mock,
        run_git_mock: Mock,
        _checked_repository: Mock,
        _checked_commit: Mock,
    ) -> None:
        secret_text = "unexpected credential detail"
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            config = project_config(code_root)
            run_git_mock.side_effect = (
                "",
                "main",
                config.url,
                GitFailure(secret_text),
            )

            result = synchronize(config, code_root, Path(temporary) / "hooks")

        self.assertEqual(result["status"], Status.FAILED)
        self.assertEqual(result["message"], "Git fetch 失败：Git 操作失败。")
        self.assertNotIn(secret_text, result["message"])

    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_safety_error_text_is_not_reported(self, validate_mock: Mock) -> None:
        secret_text = "unsafe path detail"
        validate_mock.side_effect = SafetyError(secret_text)
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            config = ProjectConfig(
                "example-service",
                code_root / "example-service",
                "https://example.invalid/repository.git",
                "main",
                "PROJECT_EXAMPLE_SERVICE_REPO_URL",
            )

            result = synchronize(config, code_root, Path(temporary) / "hooks")

        self.assertEqual(result["message"], "同步路径校验失败：同步安全检查未通过。")
        self.assertNotIn(secret_text, result["message"])

    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_os_error_text_is_not_reported(self, validate_mock: Mock) -> None:
        secret_text = "private filesystem detail"
        validate_mock.side_effect = OSError(secret_text)
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            config = ProjectConfig(
                "example-service",
                code_root / "example-service",
                "https://example.invalid/repository.git",
                "main",
                "PROJECT_EXAMPLE_SERVICE_REPO_URL",
            )

            result = synchronize(config, code_root, Path(temporary) / "hooks")

        self.assertEqual(result["message"], "同步路径校验失败。")
        self.assertNotIn(secret_text, result["message"])


if __name__ == "__main__":
    unittest.main()
