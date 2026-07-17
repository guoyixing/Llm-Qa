import unittest

from tools.user_identity import EmailAddress, IdentityConfigError, parse_email


class UserEmailParsingTests(unittest.TestCase):
    def test_parse_email_trims_valid_horizontal_whitespace(self) -> None:
        # Given
        raw_email = "  alice@example.com  "

        # When
        parsed = parse_email(raw_email)

        # Then
        self.assertEqual(parsed, EmailAddress("alice@example.com"))

    def test_parse_email_rejects_crlf_anywhere(self) -> None:
        # Given
        invalid_addresses = (
            "\r\nalice@example.com",
            "alice@example.com\r\n",
            "alice\r\n@example.com",
        )

        # When / Then
        for raw_email in invalid_addresses:
            with self.subTest(raw_email=raw_email), self.assertRaises(
                IdentityConfigError,
            ):
                _ = parse_email(raw_email)

    def test_parse_email_rejects_display_name(self) -> None:
        # Given
        raw_email = "Alice <alice@example.com>"

        # When / Then
        with self.assertRaises(IdentityConfigError):
            _ = parse_email(raw_email)

    def test_parse_email_rejects_other_control_characters(self) -> None:
        # Given
        invalid_addresses = ("\talice@example.com", "alice\x00@example.com")

        # When / Then
        for raw_email in invalid_addresses:
            with self.subTest(raw_email=raw_email), self.assertRaises(
                IdentityConfigError,
            ):
                _ = parse_email(raw_email)


if __name__ == "__main__":
    _ = unittest.main()
