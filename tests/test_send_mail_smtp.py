import unittest

from tools.send_mail import MailError, smtp


class SendMailSmtpTests(unittest.TestCase):
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
