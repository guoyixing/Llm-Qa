from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.repository_config import RepositoryCredentials
from tools.sync_repositories import ProjectConfig, Status, synchronize
from tools.sync_safety import CommandSpec


URL = "https://example.invalid/team/repository.git"
CREDENTIALS = RepositoryCredentials("fixture-user", "fixture-password")


def config(local_path: Path, credentials: RepositoryCredentials | None) -> ProjectConfig:
    return ProjectConfig(
        "example-service", local_path, URL, "main",
        "PROJECT_EXAMPLE_SERVICE_REPO_URL", credentials,
    )


def command_name(spec: CommandSpec) -> str:
    return spec.arguments[0]


class SyncGitAuthenticationTests(unittest.TestCase):
    @patch("tools.sync_repositories.checked_commit", return_value="a" * 40)
    @patch("tools.sync_repositories._checked_repository")
    @patch("tools.sync_repositories.run_git", return_value="")
    @patch("tools.sync_repositories.prepare_safe_parent")
    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_clone_alone_receives_project_credentials(
        self,
        _validate_descendant: Mock,
        _prepare_parent: Mock,
        run_git_mock: Mock,
        _checked_repository: Mock,
        _checked_commit: Mock,
    ) -> None:
        # Given
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            code_root.mkdir(parents=True)
            project = config(code_root / "team" / "example-service", CREDENTIALS)

            # When
            result = synchronize(project, code_root, Path(temporary) / "hooks")

        # Then
        self.assertEqual(result["status"], Status.SUCCESS)
        self.assertEqual(result["message"], "仓库已安全克隆。")
        specs = tuple(call.args[0] for call in run_git_mock.call_args_list)
        self.assertEqual(tuple(command_name(spec) for spec in specs), ("clone",))
        self.assertIs(getattr(specs[0], "credentials", None), CREDENTIALS)
        self.assertIn("main", specs[0].arguments)
        self.assertEqual(specs[0].arguments[-1], str(project.local_path))

    @patch("tools.sync_repositories.checked_commit", return_value="a" * 40)
    @patch("tools.sync_repositories._checked_repository")
    @patch("tools.sync_repositories.run_git", return_value="")
    @patch("tools.sync_repositories.prepare_safe_parent")
    @patch("tools.sync_repositories.validate_safe_descendant")
    def test_anonymous_clone_remains_credential_free(
        self,
        _validate_descendant: Mock,
        _prepare_parent: Mock,
        run_git_mock: Mock,
        _checked_repository: Mock,
        _checked_commit: Mock,
    ) -> None:
        # Given
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            code_root.mkdir(parents=True)
            project = config(code_root / "team" / "example-service", None)

            # When
            result = synchronize(project, code_root, Path(temporary) / "hooks")

        # Then
        self.assertEqual(result["status"], Status.SUCCESS)
        spec = run_git_mock.call_args.args[0]
        self.assertEqual(command_name(spec), "clone")
        self.assertIsNone(getattr(spec, "credentials", None))

    def test_only_fetch_and_pull_receive_credentials_on_existing_repository(self) -> None:
        # Given
        captured: list[CommandSpec] = []
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            repository = code_root / "team" / "example-service"
            repository.mkdir(parents=True)
            project = config(repository, CREDENTIALS)

            def fake_git(spec: CommandSpec, _hooks: Path) -> str:
                captured.append(spec)
                arguments = spec.arguments
                if arguments == ("rev-parse", "--show-toplevel"):
                    return str(repository)
                if arguments == ("branch", "--show-current"):
                    return "main"
                if arguments[:2] == ("remote", "get-url"):
                    return URL
                if arguments == ("rev-parse", "HEAD"):
                    return "a" * 40 if sum(command_name(item) == "rev-parse" for item in captured) == 2 else "b" * 40
                if arguments[0] == "rev-list":
                    return "0 1"
                return ""

            # When
            with (
                patch("tools.sync_repositories.validate_safe_descendant"),
                patch("tools.sync_repositories.reject_unsafe_git_config"),
                patch("tools.sync_repositories.run_git", side_effect=fake_git),
            ):
                result = synchronize(project, code_root, Path(temporary) / "hooks")

        # Then
        self.assertEqual(result["status"], Status.SUCCESS)
        self.assertEqual(result["commit"], "b" * 40)
        self.assertEqual(result["message"], "仓库已仅快进同步。")
        for spec in captured:
            expected = CREDENTIALS if command_name(spec) in {"fetch", "pull"} else None
            self.assertIs(getattr(spec, "credentials", None), expected, spec.arguments)
        self.assertEqual(
            tuple(command_name(spec) for spec in captured),
            ("rev-parse", "status", "branch", "remote", "rev-parse", "fetch", "rev-list", "pull", "rev-parse"),
        )

    def test_anonymous_existing_repository_has_no_authenticated_network_specs(self) -> None:
        # Given
        captured: list[CommandSpec] = []
        with tempfile.TemporaryDirectory() as temporary:
            code_root = Path(temporary) / "data" / "code"
            repository = code_root / "team" / "example-service"
            repository.mkdir(parents=True)
            project = config(repository, None)

            def fake_git(spec: CommandSpec, _hooks: Path) -> str:
                captured.append(spec)
                arguments = spec.arguments
                if arguments == ("rev-parse", "--show-toplevel"):
                    return str(repository)
                if arguments == ("branch", "--show-current"):
                    return "main"
                if arguments[:2] == ("remote", "get-url"):
                    return URL
                if arguments == ("rev-parse", "HEAD"):
                    return "a" * 40
                if arguments[0] == "rev-list":
                    return "0 0"
                return ""

            # When
            with (
                patch("tools.sync_repositories.validate_safe_descendant"),
                patch("tools.sync_repositories.reject_unsafe_git_config"),
                patch("tools.sync_repositories.run_git", side_effect=fake_git),
            ):
                result = synchronize(project, code_root, Path(temporary) / "hooks")

        # Then
        self.assertEqual(result["status"], Status.SUCCESS)
        network_specs = tuple(spec for spec in captured if command_name(spec) in {"fetch", "pull"})
        self.assertEqual(tuple(command_name(spec) for spec in network_specs), ("fetch", "pull"))
        self.assertTrue(all(getattr(spec, "credentials", None) is None for spec in network_specs))


if __name__ == "__main__":
    unittest.main()
