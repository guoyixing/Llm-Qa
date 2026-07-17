from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from tools.git_askpass import RepositoryOriginError, repository_origin
from tools.repository_config import RepositoryCredentials
from tools.sync_safety import CommandSpec, CommandSpecCredentialPairingError, run_git


REAL_SUBPROCESS_RUN = subprocess.run
HTTPS_URL = "https://example.invalid/team/repository.git"
HTTP_URL = "http://example.invalid/team/repository.git"
USERNAME = " 用户 + name@example.invalid ! "
PASSWORD = " 密碼 :/?#[]@!$&'()*+,;= é "
CREDENTIALS = RepositoryCredentials(USERNAME, PASSWORD)


def authenticated_spec(directory: Path, url: str) -> CommandSpec:
    return CommandSpec(
        ("fetch", "origin"),
        directory,
        credentials=CREDENTIALS,
        repository_url=url,
    )


def completed() -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["git"], 0, stdout="ok\n", stderr="")


class GitHttpCredentialTests(unittest.TestCase):
    def test_invalid_repository_origin_raises_typed_error(self) -> None:
        # Given
        invalid_url = "https://example.invalid:invalid/repository.git"

        # When
        with self.assertRaises(RepositoryOriginError) as raised:
            _ = repository_origin(invalid_url)

        # Then
        self.assertEqual(str(raised.exception), "HTTP/HTTPS 仓库地址无效。")

    def test_invalid_command_spec_credential_pairing_raises_typed_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for label, credentials, repository_url in (
                ("credentials only", CREDENTIALS, None),
                ("URL only", None, HTTPS_URL),
            ):
                with self.subTest(label=label):
                    # Given
                    directory = Path(temporary)

                    # When
                    with self.assertRaises(CommandSpecCredentialPairingError) as raised:
                        _ = CommandSpec(
                            ("fetch", "origin"),
                            directory,
                            credentials=credentials,
                            repository_url=repository_url,
                        )

                    # Then
                    self.assertEqual(str(raised.exception), "Git 认证配置必须成对提供。")

    def test_helper_accepts_exact_scheme_host_and_effective_port(self) -> None:
        encoded_username = quote(USERNAME, safe="")
        accepted_origins = (
            ("HTTP implicit default", HTTP_URL, "http://EXAMPLE.INVALID:80/other/path.git"),
            ("HTTP explicit default", "http://example.invalid:80/repository.git", "http://example.invalid/other/path.git"),
            ("HTTPS implicit default", HTTPS_URL, "https://EXAMPLE.INVALID:443/other/path.git"),
            ("HTTPS explicit default", "https://example.invalid:443/repository.git", "https://example.invalid/other/path.git"),
            ("HTTP non-default", "http://example.invalid:8080/repository.git", "http://example.invalid:8080/other/path.git"),
            ("HTTPS non-default", "https://example.invalid:8443/repository.git", "https://example.invalid:8443/other/path.git"),
            ("HTTP explicit zero", "http://example.invalid:0/repository.git", "http://example.invalid:0/other/path.git"),
            ("IPv6 implicit default", "https://[2001:DB8::1]/team/repository.git", "https://[2001:db8::1]/different/path.git"),
            ("IPv6 non-default", "https://[2001:DB8::1]:8443/team/repository.git", "https://[2001:db8::1]:8443/different/path.git"),
            ("IPv6 explicit zero", "https://[2001:DB8::1]:0/team/repository.git", "https://[2001:db8::1]:0/different/path.git"),
        )
        for label, repository_url, prompt_url in accepted_origins:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                # Given
                hooks = Path(temporary)

                def inspect_git(
                    _arguments: list[str],
                    *,
                    env: dict[str, str],
                    **_kwargs: str | Path | bool | int,
                ) -> subprocess.CompletedProcess[str]:
                    helper = Path(env["GIT_ASKPASS"])
                    password_url = prompt_url.replace(
                        "://", f"://{encoded_username}@", 1
                    )
                    prompts = (
                        (f"Username for '{prompt_url}': ", USERNAME),
                        (f"Password for '{password_url}': ", PASSWORD),
                    )
                    for prompt, expected in prompts:
                        answer = REAL_SUBPROCESS_RUN(
                            [str(helper), prompt], env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=5,
                        )
                        self.assertEqual(answer.returncode, 0)
                        self.assertEqual(answer.stdout.rstrip("\r\n"), expected)
                    return completed()

                # When
                with patch("tools.sync_safety.subprocess.run", side_effect=inspect_git):
                    _ = run_git(authenticated_spec(hooks, repository_url), hooks)

    def test_helper_rejects_mismatched_origins_and_malformed_prompts(self) -> None:
        cases = (
            (
                "malformed and mismatched HTTPS prompts",
                HTTPS_URL,
                (
                    "Username for 'https://other.invalid/repository.git': ",
                    "Username for 'https://example.invalid:444/repository.git': ",
                    "Token for 'https://example.invalid/repository.git': ",
                    "Password for 'https://example.invalid/repository.git': ",
                    "Password for 'https://wrong-user@example.invalid/repository.git': ",
                    "Password for 'https://%ZZ@example.invalid/repository.git': ",
                    "Username for 'https://example.invalid/repository.git?ref=main': ",
                    "Username for 'https://example.invalid/repository.git#fragment': ",
                    "Username for 'https://example.invalid/with space.git': ",
                    "Username for 'https://example.invalid/control\x1f.git': ",
                ),
            ),
            (
                "HTTPS to HTTP with equal numeric port",
                "https://example.invalid:80/repository.git",
                ("Username for 'http://example.invalid:80/repository.git': ",),
            ),
            (
                "HTTP to HTTPS with equal numeric port",
                "http://example.invalid:443/repository.git",
                ("Username for 'https://example.invalid:443/repository.git': ",),
            ),
            (
                "explicit zero is not the default",
                "https://example.invalid:0/repository.git",
                ("Username for 'https://example.invalid/repository.git': ",),
            ),
            (
                "IPv6 host mismatch",
                "https://[2001:db8::1]/team/repository.git",
                ("Username for 'https://[2001:db8::2]/different/path.git': ",),
            ),
            (
                "IPv6 port mismatch",
                "https://[2001:db8::1]:8443/team/repository.git",
                ("Username for 'https://[2001:db8::1]:9443/different/path.git': ",),
            ),
        )
        for label, repository_url, rejected_prompts in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                # Given
                hooks = Path(temporary)

                def inspect_git(
                    _arguments: list[str],
                    *,
                    env: dict[str, str],
                    **_kwargs: str | Path | bool | int,
                ) -> subprocess.CompletedProcess[str]:
                    helper = Path(env["GIT_ASKPASS"])
                    for prompt in rejected_prompts:
                        answer = REAL_SUBPROCESS_RUN(
                            [str(helper), prompt], env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=5,
                        )
                        self.assertNotEqual(answer.returncode, 0)
                        self.assertEqual(answer.stdout, "")
                    return completed()

                # When
                with patch("tools.sync_safety.subprocess.run", side_effect=inspect_git):
                    _ = run_git(authenticated_spec(hooks, repository_url), hooks)

    def test_redirects_are_disabled_only_for_credentialed_http(self) -> None:
        cases = (
            ("credentialed HTTP", authenticated_spec, HTTP_URL, True),
            ("credentialed HTTPS", authenticated_spec, HTTPS_URL, False),
            ("anonymous HTTP", None, HTTP_URL, False),
        )
        for label, factory, url, redirects_disabled in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                # Given
                hooks = Path(temporary)
                spec = (
                    CommandSpec(("fetch", url), hooks)
                    if factory is None
                    else factory(hooks, url)
                )
                observed_arguments: list[tuple[str, ...]] = []

                def record_git(
                    arguments: list[str],
                    **_kwargs: str | Path | bool | int | dict[str, str],
                ) -> subprocess.CompletedProcess[str]:
                    observed_arguments.append(tuple(arguments))
                    return completed()

                # When
                with patch("tools.sync_safety.subprocess.run", side_effect=record_git):
                    _ = run_git(spec, hooks)

                # Then
                self.assertEqual(len(observed_arguments), 1)
                arguments = observed_arguments[0]
                self.assertEqual(
                    "http.followRedirects=false" in arguments,
                    redirects_disabled,
                )


if __name__ == "__main__":
    _ = unittest.main()
