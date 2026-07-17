from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import ssl
import unittest
from unittest.mock import MagicMock, patch

from tools.send_mail import MailError, Report, Smtp, deliver, send_mode, smtp
from tools.user_identity import EmailAddress, UserId


VALID_VALUES = {
    "SMTP_HOST": "smtp.invalid",
    "SMTP_PORT": "465",
    "SMTP_TIMEOUT_SECONDS": "20",
    "SMTP_USE_TLS": "false",
    "SMTP_USE_SSL": "true",
    "SMTP_FROM": "sender@example.com",
}
ITEM = Report(
    user_id=UserId("alice"),
    report_date="2026-07-17",
    subject="2026-07-17 alice 代码质量审查日报",
    html="<html><body>张三（alice）</body></html>",
)
TARGETS = (EmailAddress("leader@example.com"),)
CONFIG = Smtp(
    host="smtp.invalid",
    port=465,
    timeout=20,
    username="",
    password="",
    sender=EmailAddress("sender@example.com"),
    use_ssl=True,
)


class SendMailSmtpTests(unittest.TestCase):
    def test_smtp_defaults_to_certificate_verification(self) -> None:
        # Given / When
        config = smtp(VALID_VALUES)

        # Then
        self.assertTrue(config.verify_certificate)

    def test_smtp_parses_explicit_certificate_verification_values(self) -> None:
        # Given / When / Then
        for raw, expected in (("true", True), ("false", False)):
            with self.subTest(raw=raw):
                values = dict(VALID_VALUES)
                values["SMTP_VERIFY_CERTIFICATE"] = raw
                self.assertEqual(smtp(values).verify_certificate, expected)

    def test_smtp_rejects_invalid_certificate_verification_values(self) -> None:
        # Given / When / Then
        for raw in ("", "TRUE", "False", "1", "yes"):
            with self.subTest(raw=raw):
                values = dict(VALID_VALUES)
                values["SMTP_VERIFY_CERTIFICATE"] = raw
                with self.assertRaises(MailError) as raised:
                    _ = smtp(values)
                self.assertEqual(raised.exception.code, "SMTP配置错误")
                self.assertEqual(
                    raised.exception.message,
                    "SMTP_VERIFY_CERTIFICATE 仅接受 true 或 false",
                )

    def test_deliver_keeps_certificate_verification_enabled_by_default(self) -> None:
        # Given
        connection = MagicMock()
        connection.__enter__.return_value.send_message.return_value = {}

        # When
        with patch(
            "tools.send_mail.smtplib.SMTP_SSL",
            return_value=connection,
        ) as smtp_ssl:
            status = deliver(CONFIG, TARGETS, ITEM)

        # Then
        self.assertEqual(status, "ACCEPTED")
        context = smtp_ssl.call_args.kwargs["context"]
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_deliver_keeps_certificate_verification_for_starttls_by_default(self) -> None:
        # Given
        connection = MagicMock()
        client = connection.__enter__.return_value
        client.send_message.return_value = {}
        config = CONFIG._replace(port=587, use_ssl=False)

        # When
        with patch("tools.send_mail.smtplib.SMTP", return_value=connection):
            status = deliver(config, TARGETS, ITEM)

        # Then
        self.assertEqual(status, "ACCEPTED")
        context = client.starttls.call_args.kwargs["context"]
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_deliver_uses_cert_none_context_when_explicitly_disabled(self) -> None:
        # Given
        connection = MagicMock()
        connection.__enter__.return_value.send_message.return_value = {}
        config = Smtp(
            host="smtp.invalid",
            port=465,
            timeout=20,
            username="",
            password="",
            sender=EmailAddress("sender@example.com"),
            use_ssl=True,
            verify_certificate=False,
        )

        # When
        with patch(
            "tools.send_mail.smtplib.SMTP_SSL",
            return_value=connection,
        ) as smtp_ssl:
            status = deliver(config, TARGETS, ITEM)

        # Then
        self.assertEqual(status, "ACCEPTED")
        context = smtp_ssl.call_args.kwargs["context"]
        self.assertFalse(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)

    def test_deliver_uses_cert_none_context_for_starttls(self) -> None:
        # Given
        connection = MagicMock()
        client = connection.__enter__.return_value
        client.send_message.return_value = {}
        config = Smtp(
            host="smtp.invalid",
            port=587,
            timeout=20,
            username="",
            password="",
            sender=EmailAddress("sender@example.com"),
            use_ssl=False,
            verify_certificate=False,
        )

        # When
        with patch("tools.send_mail.smtplib.SMTP", return_value=connection):
            status = deliver(config, TARGETS, ITEM)

        # Then
        self.assertEqual(status, "ACCEPTED")
        context = client.starttls.call_args.kwargs["context"]
        self.assertFalse(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)

    def test_send_mode_rejects_invalid_certificate_setting_before_delivery(self) -> None:
        # Given
        values = dict(VALID_VALUES)
        values.update(
            {
                "SMTP_VERIFY_CERTIFICATE": "TRUE",
                "USER_1_ID": "alice",
                "USER_1_NAME": "张三",
                "USER_1_GIT_EMAIL": "alice@example.com",
                "USER_1_LEADER_EMAIL": "leader@example.com",
            },
        )
        args = (
            "send",
            "alice",
            Path("reports/daily/2026-07-17/alice-code-review.md"),
            Path("reports/daily/2026-07-17/alice-code-review.html"),
        )
        output = StringIO()

        # When
        with (
            patch("tools.send_mail.report", return_value=ITEM),
            patch("tools.send_mail.env", return_value=values),
            patch("tools.send_mail.deliver") as delivery,
            redirect_stdout(output),
        ):
            exit_code = send_mode(args)

        # Then
        self.assertEqual(exit_code, 2)
        self.assertIn("SMTP_VERIFY_CERTIFICATE 仅接受 true 或 false", output.getvalue())
        delivery.assert_not_called()

    def test_port_465_rejects_starttls_mode(self) -> None:
        # Given
        values = {
            "SMTP_HOST": "smtp.invalid",
            "SMTP_PORT": "465",
            "SMTP_TIMEOUT_SECONDS": "20",
            "SMTP_USE_TLS": "true",
            "SMTP_USE_SSL": "false",
            "SMTP_FROM": "sender@example.com",
        }

        # When
        with self.assertRaises(MailError) as raised:
            _ = smtp(values)

        # Then
        self.assertEqual(raised.exception.code, "SMTP配置错误")
        self.assertEqual(
            raised.exception.message,
            "SMTP 465 端口必须使用 SSL 隐式 TLS",
        )


if __name__ == "__main__":
    _ = unittest.main()
