from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import quote

from tools.repository_config import RepositoryCredentials
from tools.sync_safety import CommandSpec, GitFailure, run_git


REAL_SUBPROCESS_RUN = subprocess.run
URL = "https://example.invalid/team/repository.git"
USERNAME = " 用户 + name@example.invalid ! "
PASSWORD = " 密碼 :/?#[]@!$&'()*+,;= é "
CREDENTIALS = RepositoryCredentials(USERNAME, PASSWORD)


def authenticated_spec(directory: Path) -> CommandSpec:
    kwargs = {"credentials": CREDENTIALS, "repository_url": URL}
    try:
        return CommandSpec(("fetch", "origin"), directory, **kwargs)
    except TypeError:
        return CommandSpec(("fetch", "origin"), directory)


def completed(returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["git"], returncode, stdout="ok\n", stderr=stderr)


class GitAskPassTests(unittest.TestCase):
    def test_command_spec_accepts_scoped_credentials_at_runtime(self) -> None:
        # Given / When / Then
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            spec = authenticated_spec(hooks)

            self.assertIs(getattr(spec, "credentials", None), CREDENTIALS)
            self.assertEqual(getattr(spec, "repository_url", None), URL)

    @patch("tools.sync_safety.subprocess.run", return_value=completed())
    def test_anonymous_command_uses_empty_askpass_without_credentials(
        self, run_mock: Mock
    ) -> None:
        # Given
        inherited = {
            "GIT_ASKPASS": "inherited-helper",
            "GIT_USERNAME": USERNAME,
            "GIT_PASSWORD": PASSWORD,
        }
        spec = CommandSpec(("status", "--porcelain=v1"), Path("repository"))

        # When
        with patch.dict(os.environ, inherited, clear=False):
            run_git(spec, Path("hooks"))

        # Then
        environment = run_mock.call_args.kwargs["env"]
        self.assertEqual(environment["GIT_ASKPASS"], "")
        self.assertNotIn("GIT_USERNAME", environment)
        self.assertNotIn("GIT_PASSWORD", environment)
        self.assertNotIn(USERNAME, environment.values())
        self.assertNotIn(PASSWORD, environment.values())

    def test_credentialed_command_uses_safe_temporary_helper(self) -> None:
        # Given
        observed_paths: list[Path] = []

        def inspect_git(_arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            environment = kwargs["env"]
            self.assertIsInstance(environment, dict)
            helper = Path(environment["GIT_ASKPASS"])
            observed_paths.append(helper)
            self.assertTrue(helper.is_absolute())
            self.assertTrue(helper.is_file())
            sources = tuple(
                path.read_text(encoding="utf-8", errors="replace")
                for path in helper.parent.iterdir()
                if path.is_file()
            )
            self.assertTrue(sources)
            self.assertNotIn(USERNAME, "".join(sources))
            self.assertNotIn(PASSWORD, "".join(sources))
            encoded_username = quote(USERNAME, safe="")
            encoded_url = URL.replace("https://", f"https://{encoded_username}@")
            prompts = {
                f"Username for '{URL}': ": USERNAME,
                f"Password for '{encoded_url}': ": PASSWORD,
            }
            for prompt, expected in prompts.items():
                answer = REAL_SUBPROCESS_RUN(
                    [str(helper), prompt], env=environment, capture_output=True,
                    text=True, encoding="utf-8", errors="replace", timeout=5,
                )
                self.assertEqual(answer.returncode, 0)
                self.assertEqual(answer.stdout.rstrip("\r\n"), expected)
            rejected = (
                f"Token for '{URL}': ",
                "Username for 'http://example.invalid/team/repository.git': ",
                f"Password for '{URL}': ",
                "Password for 'https://other.invalid/team/repository.git': ",
                "Password for 'https://wrong-user@example.invalid/team/repository.git': ",
            )
            for prompt in rejected:
                answer = REAL_SUBPROCESS_RUN(
                    [str(helper), prompt], env=environment, capture_output=True,
                    text=True, encoding="utf-8", errors="replace", timeout=5,
                )
                self.assertEqual(answer.stdout, "")
                self.assertNotEqual(answer.returncode, 0)
            return completed()

        # When
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            with patch("tools.sync_safety.subprocess.run", side_effect=inspect_git):
                run_git(authenticated_spec(hooks), hooks)

            # Then
            self.assertTrue(hooks.exists())
            self.assertEqual(len(observed_paths), 1)
            self.assertFalse(observed_paths[0].exists())

    def test_interrupted_environment_copy_removes_secret_from_run_git_frame(self) -> None:
        class InterruptingEnvironment(Mapping[str, str]):
            def __getitem__(self, key: str) -> str:
                if key == "LLM_QA_ASKPASS_USERNAME":
                    return USERNAME
                raise KeyboardInterrupt

            def __iter__(self) -> Iterator[str]:
                yield "LLM_QA_ASKPASS_USERNAME"
                yield "LLM_QA_ASKPASS_PASSWORD"

            def __len__(self) -> int:
                return 2

        @contextmanager
        def interrupting_session(*_args: object) -> Iterator[SimpleNamespace]:
            yield SimpleNamespace(
                environment=InterruptingEnvironment(),
                launcher=Path("unused-askpass"),
            )

        # Given / When
        caught: KeyboardInterrupt | None = None
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            try:
                with patch("tools.sync_safety.temporary_askpass", interrupting_session):
                    run_git(authenticated_spec(hooks), hooks)
            except KeyboardInterrupt as error:
                caught = error

            # Then
            self.assertIsNotNone(caught)
            traceback = caught.__traceback__
            while traceback is not None and traceback.tb_frame.f_code.co_name != "run_git":
                traceback = traceback.tb_next
            self.assertIsNotNone(traceback)
            environment = traceback.tb_frame.f_locals["environment"]
            self.assertNotIn(USERNAME, environment.values())

    def test_helper_is_cleaned_for_every_subprocess_outcome(self) -> None:
        outcomes = (
            (completed(), False),
            (completed(1, "authentication failed"), True),
            (subprocess.TimeoutExpired(["git"], 1), True),
            (OSError("fixture launch failure"), True),
        )
        for outcome, expect_failure in outcomes:
            with self.subTest(outcome=type(outcome).__name__, returncode=getattr(outcome, "returncode", None)):
                # Given
                observed: list[Path] = []

                def finish(_arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                    environment = kwargs["env"]
                    self.assertIsInstance(environment, dict)
                    observed.append(Path(environment["GIT_ASKPASS"]))
                    if isinstance(outcome, BaseException):
                        raise outcome
                    return outcome

                # When
                with tempfile.TemporaryDirectory() as temporary:
                    hooks = Path(temporary)
                    with patch("tools.sync_safety.subprocess.run", side_effect=finish):
                        if expect_failure:
                            with self.assertRaises(GitFailure):
                                run_git(authenticated_spec(hooks), hooks)
                        else:
                            run_git(authenticated_spec(hooks), hooks)

                    # Then
                    self.assertTrue(hooks.exists())
                    self.assertEqual(len(observed), 1)
                    self.assertFalse(observed[0].exists())

    def test_keyboard_interrupt_propagates_after_real_helper_cleanup(self) -> None:
        # Given
        observed_paths: list[Path] = []

        def interrupt_git(
            _arguments: list[str],
            *,
            env: dict[str, str],
            **_kwargs: str | Path | bool | int,
        ) -> subprocess.CompletedProcess[str]:
            observed_paths.append(Path(env["GIT_ASKPASS"]))
            raise KeyboardInterrupt

        # When
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            with patch("tools.sync_safety.subprocess.run", side_effect=interrupt_git):
                with self.assertRaises(KeyboardInterrupt):
                    run_git(authenticated_spec(hooks), hooks)

            # Then
            self.assertEqual(len(observed_paths), 1)
            self.assertFalse(observed_paths[0].exists())

    def test_each_credentialed_call_uses_a_distinct_helper(self) -> None:
        # Given
        observed: list[Path] = []

        def record(_arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            environment = kwargs["env"]
            self.assertIsInstance(environment, dict)
            observed.append(Path(environment["GIT_ASKPASS"]))
            return completed()

        # When
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            with patch("tools.sync_safety.subprocess.run", side_effect=record):
                run_git(authenticated_spec(hooks), hooks)
                run_git(authenticated_spec(hooks), hooks)

            # Then
            self.assertTrue(hooks.exists())
            self.assertEqual(len(observed), 2)
            self.assertNotEqual(observed[0], observed[1])
            self.assertTrue(all(not path.exists() for path in observed))

    def test_git_process_is_hardened_and_excludes_inherited_tracing(self) -> None:
        # Given
        inherited = {
            "GIT_TRACE": "1", "GIT_TRACE_PACKET": "1", "GIT_CURL_VERBOSE": "1",
            "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "credential.helper",
            "GIT_CONFIG_VALUE_0": "unsafe", "GIT_ASKPASS_REQUIRE": "force",
        }
        run_mock = Mock(return_value=completed())

        # When / Then
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            with patch.dict(os.environ, inherited, clear=False):
                with patch("tools.sync_safety.subprocess.run", run_mock):
                    run_git(authenticated_spec(hooks), hooks)

            arguments = run_mock.call_args.args[0]
            environment = run_mock.call_args.kwargs["env"]
            self.assertIn("credential.helper=", arguments)
            self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")
            self.assertNotIn("GIT_ASKPASS_REQUIRE", environment)
            self.assertIsNot(run_mock.call_args.kwargs.get("shell"), True)
            for key in inherited:
                self.assertNotIn(key, environment)

    def test_secrets_never_reach_argv_repr_or_failure_text(self) -> None:
        # Given
        run_mock = Mock(return_value=completed(1, f"authentication failed {USERNAME} {PASSWORD}"))

        # When / Then
        with tempfile.TemporaryDirectory() as temporary:
            hooks = Path(temporary)
            spec = authenticated_spec(hooks)
            with patch("tools.sync_safety.subprocess.run", run_mock):
                with self.assertRaises(GitFailure) as raised:
                    run_git(spec, hooks)

            arguments = run_mock.call_args.args[0]
            for secret in (USERNAME, PASSWORD):
                self.assertNotIn(secret, "\0".join(arguments))
                self.assertNotIn(secret, repr(spec))
                self.assertNotIn(secret, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
