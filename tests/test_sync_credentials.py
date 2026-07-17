from __future__ import annotations

import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

from tools.project_registry import Project
from tools.repository_config import ProtectedConfigError, parse_dotenv
from tools.sync_repositories import ProjectConfig, ResultJson, load_config


URL_KEY = "PROJECT_EXAMPLE_SERVICE_REPO_URL"
USERNAME_KEY = "PROJECT_EXAMPLE_SERVICE_REPO_USERNAME"
PASSWORD_KEY = "PROJECT_EXAMPLE_SERVICE_REPO_PASSWORD"
HTTPS_URL = "https://example.invalid/repository.git"
HTTP_URL = "http://example.invalid/repository.git"
INVALID_CREDENTIAL_MESSAGE = "注册仓库 HTTP/HTTPS 凭据配置无效。"


def project() -> Project:
    return Project(
        project_id="example-service",
        name="示例服务",
        code_dir=PurePosixPath("data/code/team/example-service"),
        standards_dir=PurePosixPath("standards/projects/example-service"),
        default_branch="main",
        repository_url_config_key=URL_KEY,
        enabled=True,
    )


def load_fixture(
    values: dict[str, tuple[str, ...]], projects: tuple[Project, ...]
) -> tuple[tuple[ProjectConfig, ...], tuple[ResultJson, ...]]:
    with (
        patch("tools.sync_repositories.parse_dotenv", return_value=values),
        patch("tools.sync_repositories.validate_safe_descendant"),
        patch("tools.sync_repositories.validate_root"),
    ):
        return load_config(Path("fixture.env"), projects)


class SyncCredentialTests(unittest.TestCase):
    def test_real_dotenv_rejects_parser_sensitive_credential_controls(self) -> None:
        parser_sensitive_values = {
            "NEL": "fixture\u0085user",
            "vertical tab": "fixture\x0buser",
            "form feed": "fixture\x0cuser",
            "file separator": "fixture\x1cuser",
            "group separator": "fixture\x1duser",
            "record separator": "fixture\x1euser",
            "trailing tab": "fixture-user\t",
        }
        for label, username in parser_sensitive_values.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                # Given
                env_path = Path(temporary) / ".env"
                env_path.write_text(
                    f"{URL_KEY}={HTTPS_URL}\n{USERNAME_KEY}={username}\n"
                    f"{PASSWORD_KEY}=fixture-password\n",
                    encoding="utf-8",
                )

                # When
                with (
                    patch("tools.sync_repositories.validate_safe_descendant"),
                    patch("tools.sync_repositories.validate_root"),
                ):
                    configured, failures = load_config(env_path, (project(),))

                # Then
                self.assertEqual(configured, ())
                self.assertEqual(len(failures), 1)
                self.assertEqual(failures[0]["message"], INVALID_CREDENTIAL_MESSAGE)

    def test_invalid_utf8_protected_config_has_no_exception_cause(self) -> None:
        # Given
        invalid_source = b"\xff"
        with tempfile.TemporaryDirectory() as temporary:
            env_path = Path(temporary) / ".env"
            env_path.write_bytes(invalid_source)

            # When
            with self.assertRaises(ProtectedConfigError) as raised:
                parse_dotenv(env_path, frozenset({URL_KEY}))

        # Then
        root = raised.exception
        pending: list[BaseException] = [root]
        seen: set[int] = set()
        exposing_source: list[BaseException] = []
        while pending:
            current = pending.pop()
            if id(current) in seen:
                continue
            seen.add(id(current))
            if getattr(current, "object", None) == invalid_source or invalid_source in current.args:
                exposing_source.append(current)
            pending.extend(
                linked for linked in (current.__cause__, current.__context__)
                if linked is not None
            )
        self.assertEqual(
            (root.__cause__, root.__context__, tuple(exposing_source)),
            (None, None, ()),
        )

    def test_load_config_requests_only_selected_project_repository_keys(self) -> None:
        # Given
        parse_mock = Mock(return_value={URL_KEY: (HTTPS_URL,)})
        with tempfile.TemporaryDirectory() as temporary:
            env_path = Path(temporary) / ".env"

            # When
            with (
                patch("tools.sync_repositories.parse_dotenv", parse_mock),
                patch("tools.sync_repositories.validate_safe_descendant"),
                patch("tools.sync_repositories.validate_root"),
            ):
                configured, failures = load_config(env_path, (project(),))

        # Then
        self.assertEqual(len(configured), 1)
        self.assertEqual(failures, ())
        parse_mock.assert_called_once_with(
            env_path, frozenset({URL_KEY, USERNAME_KEY, PASSWORD_KEY})
        )

    def test_absent_https_credentials_keep_project_anonymous(self) -> None:
        # Given
        values = {URL_KEY: (HTTPS_URL,)}

        # When
        configured, failures = load_fixture(values, (project(),))

        # Then
        self.assertEqual(failures, ())
        self.assertEqual(len(configured), 1)
        self.assertIsNone(getattr(configured[0], "credentials", "missing"))

    def test_http_and_https_credentials_are_retained_exactly(self) -> None:
        username = " 用户 + name@example.invalid ! "
        password = " 密碼 :/?#[]@!$&'()*+,;= é "
        for scheme, url in (("HTTP", HTTP_URL), ("HTTPS", HTTPS_URL)):
            with self.subTest(scheme=scheme):
                # Given
                values = {
                    URL_KEY: (url,),
                    USERNAME_KEY: (username,),
                    PASSWORD_KEY: (password,),
                }

                # When
                configured, failures = load_fixture(values, (project(),))

                # Then
                self.assertEqual(failures, ())
                self.assertEqual(len(configured), 1)
                credentials = getattr(configured[0], "credentials", None)
                if credentials is None:
                    self.fail(f"{scheme} 仓库凭据未保留。")
                self.assertEqual(credentials.username, username)
                self.assertEqual(credentials.password, password)

    def test_invalid_http_and_https_credentials_fail_only_that_project(self) -> None:
        invalid_cases = {
            "only username": {USERNAME_KEY: ("fixture-user",)},
            "only password": {PASSWORD_KEY: ("fixture-password",)},
            "duplicate username": {
                USERNAME_KEY: ("fixture-user", "other-user"),
                PASSWORD_KEY: ("fixture-password",),
            },
            "duplicate password": {
                USERNAME_KEY: ("fixture-user",),
                PASSWORD_KEY: ("fixture-password", "other-password"),
            },
            "empty username": {USERNAME_KEY: ("",), PASSWORD_KEY: ("fixture-password",)},
            "empty password": {USERNAME_KEY: ("fixture-user",), PASSWORD_KEY: ("",)},
            "username too long": {
                USERNAME_KEY: ("u" * 1025,),
                PASSWORD_KEY: ("fixture-password",),
            },
            "password too long": {
                USERNAME_KEY: ("fixture-user",),
                PASSWORD_KEY: ("p" * 1025,),
            },
        }
        control_characters = (
            ("NUL", "\x00"), ("tab", "\t"), ("CR", "\r"), ("LF", "\n"),
            ("unit separator", "\x1f"), ("DEL", "\x7f"), ("NEL", "\u0085"),
        )
        for label, control in control_characters:
            invalid_cases[f"username {label}"] = {
                USERNAME_KEY: (f"fixture{control}user",), PASSWORD_KEY: ("fixture-password",),
            }
            invalid_cases[f"password {label}"] = {
                USERNAME_KEY: ("fixture-user",), PASSWORD_KEY: (f"fixture{control}password",),
            }

        for scheme, url in (("http", HTTP_URL), ("https", HTTPS_URL)):
            for label, credentials in invalid_cases.items():
                with self.subTest(scheme=scheme, label=label):
                    # Given
                    values = {URL_KEY: (url,), **credentials}

                    # When
                    configured, failures = load_fixture(values, (project(),))

                    # Then
                    self.assertEqual(configured, ())
                    self.assertEqual(len(failures), 1)
                    self.assertEqual(failures[0]["project_id"], "example-service")
                    self.assertEqual(failures[0]["message"], INVALID_CREDENTIAL_MESSAGE)

    def test_credentials_reject_non_http_repository_urls(self) -> None:
        non_http_urls = {
            "ssh": "ssh://example.invalid/repository.git",
            "git": "git://example.invalid/repository.git",
            "scp": "git@example.invalid:team/repository.git",
        }
        for label, url in non_http_urls.items():
            with self.subTest(label=label):
                # Given
                values = {
                    URL_KEY: (url,), USERNAME_KEY: ("fixture-user",),
                    PASSWORD_KEY: ("fixture-password",),
                }

                # When
                configured, failures = load_fixture(values, (project(),))

                # Then
                self.assertEqual(configured, ())
                self.assertEqual(len(failures), 1)
                self.assertEqual(failures[0]["message"], INVALID_CREDENTIAL_MESSAGE)

    def test_credentials_allow_1024_unicode_code_points(self) -> None:
        # Given
        username = "用" * 1024
        password = "密" * 1024
        values = {
            URL_KEY: (HTTPS_URL,),
            USERNAME_KEY: (username,),
            PASSWORD_KEY: (password,),
        }

        # When
        configured, failures = load_fixture(values, (project(),))

        # Then
        self.assertEqual(failures, ())
        self.assertEqual(len(configured), 1)
        credentials = getattr(configured[0], "credentials", None)
        if credentials is None:
            self.fail("HTTPS 仓库凭据未保留。")
        self.assertEqual(credentials.username, username)
        self.assertEqual(credentials.password, password)

    def test_invalid_credentials_do_not_block_unrelated_valid_project(self) -> None:
        # Given
        unrelated = Project(
            project_id="unrelated-service",
            name="无关服务",
            code_dir=PurePosixPath("data/code/team/unrelated-service"),
            standards_dir=PurePosixPath("standards/projects/unrelated-service"),
            default_branch="main",
            repository_url_config_key="PROJECT_UNRELATED_SERVICE_REPO_URL",
            enabled=True,
        )
        values = {
            URL_KEY: (HTTPS_URL,),
            USERNAME_KEY: ("fixture-user",),
            "PROJECT_UNRELATED_SERVICE_REPO_URL": (
                "https://unrelated.invalid/repository.git",
            ),
        }

        # When
        configured, failures = load_fixture(values, (project(), unrelated))

        # Then
        self.assertEqual(tuple(item.project_id for item in configured), ("unrelated-service",))
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["project_id"], "example-service")
        self.assertEqual(failures[0]["message"], INVALID_CREDENTIAL_MESSAGE)

    def test_project_config_representation_hides_repository_secrets(self) -> None:
        # Given
        url = "https://example.invalid/private-repository.git"
        username = "fixture-visible-user"
        password = "fixture-visible-password"
        values = {
            URL_KEY: (url,),
            USERNAME_KEY: (username,),
            PASSWORD_KEY: (password,),
        }

        # When
        configured, failures = load_fixture(values, (project(),))

        # Then
        self.assertEqual(failures, ())
        self.assertEqual(len(configured), 1)
        credentials = getattr(configured[0], "credentials", None)
        self.assertIsNotNone(credentials)
        project_representation = repr(configured[0])
        credential_representation = repr(credentials)
        for secret in (url, username, password):
            self.assertNotIn(secret, project_representation)
            self.assertNotIn(secret, credential_representation)


if __name__ == "__main__":
    unittest.main()
