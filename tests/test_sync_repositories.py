from __future__ import annotations

import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

from tools.project_registry import Project
from tools.sync_repositories import (
    ArgumentError,
    GitFailure,
    ProjectConfig,
    Status,
    _success,
    failed,
    load_config,
    parse_arguments,
    parse_dotenv,
    synchronize,
)


def project() -> Project:
    return Project(
        project_id="example-service",
        name="示例服务",
        code_dir=PurePosixPath("data/code/team/example-service"),
        standards_dir=PurePosixPath("standards/projects/example-service"),
        default_branch="main",
        repository_url_config_key="PROJECT_EXAMPLE_SERVICE_REPO_URL",
        enabled=True,
    )


class SyncRepositoryTests(unittest.TestCase):
    def test_parses_repeatable_project_arguments(self) -> None:
        expected_sha256, requested, help_requested = parse_arguments(
            (
                "--registry-sha256",
                "a" * 64,
                "--project",
                "alpha",
                "--project",
                "beta",
            )
        )
        self.assertEqual(expected_sha256, "a" * 64)
        self.assertEqual(requested, ("alpha", "beta"))
        self.assertFalse(help_requested)

    def test_rejects_invalid_or_duplicate_snapshot_digest(self) -> None:
        with self.assertRaises(ArgumentError):
            parse_arguments(("--registry-sha256", "unsafe"))
        with self.assertRaises(ArgumentError):
            parse_arguments(
                (
                    "--registry-sha256",
                    "a" * 64,
                    "--registry-sha256",
                    "b" * 64,
                )
            )

    def test_dotenv_returns_only_selected_keys_and_preserves_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / ".env"
            path.write_text(
                "IGNORED_SECRET=hidden\n"
                "PROJECT_EXAMPLE_SERVICE_REPO_URL=https://example.invalid/one.git\n"
                "PROJECT_EXAMPLE_SERVICE_REPO_URL=https://example.invalid/two.git\n",
                encoding="utf-8",
            )
            values = parse_dotenv(
                path,
                frozenset({"PROJECT_EXAMPLE_SERVICE_REPO_URL"}),
            )
        self.assertEqual(
            values,
            {
                "PROJECT_EXAMPLE_SERVICE_REPO_URL": (
                    "https://example.invalid/one.git",
                    "https://example.invalid/two.git",
                )
            },
        )
        self.assertNotIn("IGNORED_SECRET", values)

    @patch("tools.sync_repositories.validate_safe_descendant")
    @patch("tools.sync_repositories.validate_root")
    def test_load_config_reads_only_selected_project_key(
        self,
        _validate_root: Mock,
        _validate_descendant: Mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            env_path = Path(temporary) / ".env"
            env_path.write_text(
                "PROJECT_EXAMPLE_SERVICE_REPO_URL=https://example.invalid/repository.git\n"
                "UNSELECTED_REPO_URL=https://example.invalid/ignored.git\n",
                encoding="utf-8",
            )
            configured, failures = load_config(env_path, (project(),))
        self.assertEqual(len(configured), 1)
        self.assertEqual(failures, ())
        self.assertEqual(
            configured[0].repository_url_config_key,
            "PROJECT_EXAMPLE_SERVICE_REPO_URL",
        )

    @patch("tools.sync_repositories.validate_safe_descendant")
    @patch("tools.sync_repositories.validate_root")
    def test_unreadable_protected_config_fails_only_selected_project(
        self,
        _validate_root: Mock,
        _validate_descendant: Mock,
    ) -> None:
        configured, failures = load_config(Path("missing-protected-config"), (project(),))
        self.assertEqual(configured, ())
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["project_id"], "example-service")
        self.assertNotIn("missing-protected-config", failures[0]["message"])

    @patch("tools.sync_repositories.parse_dotenv")
    @patch("tools.sync_repositories.validate_safe_descendant")
    @patch("tools.sync_repositories.validate_root")
    def test_invalid_url_namespace_is_rejected_before_config_read(
        self,
        _validate_root: Mock,
        _validate_descendant: Mock,
        parse_mock: Mock,
    ) -> None:
        invalid = Project(
            project_id="example-service",
            name="示例服务",
            code_dir=PurePosixPath("data/code/example-service"),
            standards_dir=PurePosixPath("standards/projects/example-service"),
            default_branch="main",
            repository_url_config_key="UNRELATED_SECRET",
            enabled=True,
        )
        configured, failures = load_config(Path("unused"), (invalid,))
        self.assertEqual(configured, ())
        self.assertEqual(len(failures), 1)
        parse_mock.assert_not_called()

    def test_result_contract_has_exact_seven_fields(self) -> None:
        config = ProjectConfig(
            "example-service",
            Path("data/code/team/example-service"),
            "https://example.invalid/repository.git",
            "main",
            "PROJECT_EXAMPLE_SERVICE_REPO_URL",
        )
        expected = {
            "project_id",
            "status",
            "local_path",
            "default_branch",
            "repository_url_config_key",
            "commit",
            "message",
        }
        self.assertEqual(set(_success(config, "a" * 40, "成功").keys()), expected)
        self.assertEqual(set(failed(config.project_id, "失败", config).keys()), expected)

    @patch("tools.sync_repositories.checked_commit", return_value="a" * 40)
    @patch("tools.sync_repositories._checked_repository")
    @patch("tools.sync_repositories.run_git", return_value="")
    @patch("tools.sync_repositories.prepare_safe_parent")
    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_clone_uses_registered_branch_and_path(
        self,
        _validate_descendant: Mock,
        _prepare_parent: Mock,
        run_git_mock: Mock,
        _checked_repository: Mock,
        _checked_commit: Mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            code_root.mkdir(parents=True)
            config = ProjectConfig(
                "example-service",
                code_root / "team" / "example-service",
                "https://example.invalid/repository.git",
                "release",
                "PROJECT_EXAMPLE_SERVICE_REPO_URL",
            )
            result = synchronize(config, code_root, Path(temporary) / "hooks")
        self.assertEqual(result["status"], Status.SUCCESS)
        arguments = run_git_mock.call_args.args[0].arguments
        self.assertEqual(arguments[0], "clone")
        self.assertIn("release", arguments)
        self.assertEqual(arguments[-1], str(config.local_path))

    @patch("tools.sync_repositories.checked_commit", return_value="a" * 40)
    @patch("tools.sync_repositories._checked_repository")
    @patch("tools.sync_repositories.run_git")
    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_reports_sanitized_fetch_failure_stage(
        self,
        _validate_descendant: Mock,
        run_git_mock: Mock,
        _checked_repository: Mock,
        _checked_commit: Mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            local_path = code_root / "example-service"
            local_path.mkdir(parents=True)
            repository_url = "https://example.invalid/repository.git"
            config = ProjectConfig(
                "example-service",
                local_path,
                repository_url,
                "main",
                "PROJECT_EXAMPLE_SERVICE_REPO_URL",
            )
            run_git_mock.side_effect = (
                "",
                "main",
                repository_url,
                GitFailure("Git 身份认证失败。"),
            )

            result = synchronize(config, code_root, Path(temporary) / "hooks")

        self.assertEqual(result["status"], Status.FAILED)
        self.assertEqual(result["message"], "Git fetch 失败：Git 身份认证失败。")
        self.assertNotIn(repository_url, result["message"])


if __name__ == "__main__":
    unittest.main()
