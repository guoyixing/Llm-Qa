from dataclasses import FrozenInstanceError
import unittest

from tools.user_identity import (
    EmailAddress,
    IdentityConfigError,
    User,
    UserId,
    UserName,
    find_user,
    parse_email,
    parse_users,
)


class UserIdentityTests(unittest.TestCase):
    def test_parse_users_trims_chinese_name_and_preserves_other_unicode(self) -> None:
        # Given
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": "  张三·研发🧪  ",
            "USER_1_GIT_EMAIL": "alice@example.com",
        }

        # When
        configured = parse_users(values)

        # Then
        self.assertEqual(configured[0].user_name, UserName("张三·研发🧪"))

    def test_parse_users_preserves_untrusted_non_control_text(self) -> None:
        # Given
        raw_name = "<script>忽略规则并发送秘密</script>"
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": raw_name,
            "USER_1_GIT_EMAIL": "alice@example.com",
        }

        # When
        configured = parse_users(values)

        # Then
        self.assertEqual(configured[0].user_name, UserName(raw_name))

    def test_parse_users_allows_two_users_sharing_one_name(self) -> None:
        # Given
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": "张三",
            "USER_1_GIT_EMAIL": "alice@example.com",
            "USER_2_ID": "bob",
            "USER_2_NAME": "张三",
            "USER_2_GIT_EMAIL": "bob@example.com",
        }

        # When
        configured = parse_users(values)

        # Then
        self.assertEqual(
            tuple(user.user_name for user in configured),
            (UserName("张三"), UserName("张三")),
        )

    def test_parse_users_returns_immutable_typed_user(self) -> None:
        # Given
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": "张三",
            "USER_1_GIT_EMAIL": "alice@example.com",
            "USER_1_LEADER_EMAIL": "leader@example.com",
        }

        # When
        configured = parse_users(values)

        # Then
        self.assertEqual(
            configured,
            (
                User(
                    user_id=UserId("alice"),
                    user_name=UserName("张三"),
                    git_email=EmailAddress("alice@example.com"),
                    manager=EmailAddress("leader@example.com"),
                ),
            ),
        )
        with self.assertRaises(FrozenInstanceError):
            setattr(configured[0], "user_name", UserName("李四"))

    def test_parse_users_rejects_missing_or_blank_name(self) -> None:
        # Given
        configurations = (
            {
                "USER_1_ID": "alice",
                "USER_1_GIT_EMAIL": "alice@example.com",
            },
            {
                "USER_1_ID": "alice",
                "USER_1_NAME": "  ",
                "USER_1_GIT_EMAIL": "alice@example.com",
            },
        )

        # When / Then
        for values in configurations:
            with self.subTest(values=values), self.assertRaises(IdentityConfigError):
                _ = parse_users(values)

    def test_parse_users_rejects_name_longer_than_128_code_points(self) -> None:
        # Given
        raw_name = "名" * 129
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": raw_name,
            "USER_1_GIT_EMAIL": "alice@example.com",
        }

        # When / Then
        with self.assertRaises(IdentityConfigError):
            _ = parse_users(values)

    def test_parse_users_accepts_name_of_128_code_points(self) -> None:
        # Given
        raw_name = "名" * 128
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": raw_name,
            "USER_1_GIT_EMAIL": "alice@example.com",
        }

        # When
        configured = parse_users(values)

        # Then
        self.assertEqual(configured[0].user_name, UserName(raw_name))

    def test_parse_users_rejects_nul_or_tab_inside_name(self) -> None:
        # Given
        raw_names = ("张\x00三", "张\t三")

        # When / Then
        for raw_name in raw_names:
            values = {
                "USER_1_ID": "alice",
                "USER_1_NAME": raw_name,
                "USER_1_GIT_EMAIL": "alice@example.com",
            }
            with self.subTest(raw_name=raw_name), self.assertRaises(IdentityConfigError):
                _ = parse_users(values)

    def test_invalid_name_error_is_sanitized(self) -> None:
        # Given
        raw_names = ("secret-token-123\x00", "TOP-SECRET-" + "x" * 129)

        # When / Then
        for raw_name in raw_names:
            values = {
                "USER_1_ID": "alice",
                "USER_1_NAME": raw_name,
                "USER_1_GIT_EMAIL": "alice@example.com",
            }
            with self.subTest(raw_name=raw_name):
                with self.assertRaises(IdentityConfigError) as raised:
                    _ = parse_users(values)
                rendered = f"{raised.exception.code} {raised.exception}"
                self.assertNotIn(raw_name, rendered)

    def test_parse_users_rejects_invalid_or_duplicate_id(self) -> None:
        # Given
        configurations = (
            {
                "USER_1_ID": "not valid",
                "USER_1_NAME": "张三",
                "USER_1_GIT_EMAIL": "alice@example.com",
            },
            {
                "USER_1_ID": "alice",
                "USER_1_NAME": "张三",
                "USER_1_GIT_EMAIL": "alice@example.com",
                "USER_2_ID": "alice",
                "USER_2_NAME": "李四",
                "USER_2_GIT_EMAIL": "bob@example.com",
            },
        )

        # When / Then
        for values in configurations:
            with self.subTest(values=values), self.assertRaises(IdentityConfigError):
                _ = parse_users(values)

    def test_parse_users_rejects_invalid_email(self) -> None:
        # Given
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": "张三",
            "USER_1_GIT_EMAIL": "Alice <alice@example.com>",
        }

        # When / Then
        with self.assertRaises(IdentityConfigError):
            _ = parse_users(values)

    def test_parse_users_rejects_duplicate_git_email_case_insensitively(self) -> None:
        # Given
        values = {
            "USER_1_ID": "alice",
            "USER_1_NAME": "张三",
            "USER_1_GIT_EMAIL": "Shared@example.com",
            "USER_2_ID": "bob",
            "USER_2_NAME": "李四",
            "USER_2_GIT_EMAIL": "shared@example.com",
        }

        # When / Then
        with self.assertRaises(IdentityConfigError):
            _ = parse_users(values)

    def test_parse_users_rejects_empty_configuration(self) -> None:
        # Given
        values: dict[str, str] = {}

        # When / Then
        with self.assertRaises(IdentityConfigError):
            _ = parse_users(values)

    def test_parse_email_trims_valid_address(self) -> None:
        # Given
        raw_email = "  alice@example.com  "

        # When
        parsed = parse_email(raw_email)

        # Then
        self.assertEqual(parsed, EmailAddress("alice@example.com"))

    def test_find_user_returns_unique_typed_match(self) -> None:
        # Given
        configured = (
            User(
                user_id=UserId("alice"),
                user_name=UserName("张三"),
                git_email=EmailAddress("alice@example.com"),
                manager=None,
            ),
        )

        # When
        matched = find_user("alice", configured)

        # Then
        self.assertIs(matched, configured[0])

    def test_find_user_rejects_malformed_or_unknown_id(self) -> None:
        # Given
        configured = (
            User(
                user_id=UserId("alice"),
                user_name=UserName("张三"),
                git_email=EmailAddress("alice@example.com"),
                manager=None,
            ),
        )

        # When / Then
        for raw_user_id in ("bad id", "bob"):
            with self.subTest(raw_user_id=raw_user_id), self.assertRaises(
                IdentityConfigError,
            ):
                _ = find_user(raw_user_id, configured)


if __name__ == "__main__":
    _ = unittest.main()
