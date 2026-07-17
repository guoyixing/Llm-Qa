from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import ANY, MagicMock, patch

from tools.send_mail import Report, Smtp, deliver, main
from tools.user_identity import EmailAddress, UserId


VALID_ENV = {
    "USER_1_ID": "alice",
    "USER_1_NAME": "张三",
    "USER_1_GIT_EMAIL": "alice@example.com",
    "USER_1_LEADER_EMAIL": "leader-a@example.com, leader-b@example.com",
    "DEFAULT_LEADER_EMAIL": "default-a@example.com, default-b@example.com",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "465",
    "SMTP_TIMEOUT_SECONDS": "10",
    "SMTP_USE_TLS": "false",
    "SMTP_USE_SSL": "true",
    "SMTP_FROM": "sender@example.com",
}
SEND_ARGV = (
    "--send",
    "--user",
    "alice",
    "--markdown",
    "reports/daily/2026-07-17/alice-code-review.md",
    "--html",
    "reports/daily/2026-07-17/alice-code-review.html",
)
ITEM = Report(
    user_id=UserId("alice"),
    report_date="2026-07-17",
    subject="2026-07-17 alice 代码质量审查日报",
    html="<html><body>张三（alice）</body></html>",
)
CONFIG = Smtp(
    host="smtp.example.com",
    port=465,
    timeout=10,
    username="",
    password="",
    sender=EmailAddress("sender@example.com"),
    use_ssl=True,
)
LEADERS = (
    EmailAddress("leader-a@example.com"),
    EmailAddress("leader-b@example.com"),
)


class SendMailMultipleRecipientsTests(unittest.TestCase):
    def invoke(
        self,
        values: dict[str, str],
        argv: tuple[str, ...] = SEND_ARGV,
    ) -> tuple[int, str]:
        output = StringIO()
        with (
            patch("sys.argv", ["send_mail.py", *argv]),
            patch("tools.send_mail.env", return_value=values),
            redirect_stdout(output),
        ):
            exit_code = main()
        return exit_code, output.getvalue().strip()

    def test_send_mode_uses_all_default_leaders_when_user_has_none(self) -> None:
        # Given
        values = dict(VALID_ENV)
        values["USER_1_LEADER_EMAIL"] = ""

        # When
        with (
            patch("tools.send_mail.report", return_value=ITEM),
            patch("tools.send_mail.deliver", return_value="ACCEPTED") as delivery,
        ):
            exit_code, _ = self.invoke(values)

        # Then
        self.assertEqual(exit_code, 0)
        delivery.assert_called_once_with(
            ANY,
            (
                EmailAddress("default-a@example.com"),
                EmailAddress("default-b@example.com"),
            ),
            ITEM,
        )

    def test_other_users_invalid_leaders_do_not_block_selected_user(self) -> None:
        # Given
        values = dict(VALID_ENV)
        values.update(
            {
                "USER_2_ID": "bob",
                "USER_2_NAME": "李四",
                "USER_2_GIT_EMAIL": "bob@example.com",
                "USER_2_LEADER_EMAIL": "bad@example.com,,other@example.com",
            },
        )

        # When
        with (
            patch("tools.send_mail.report", return_value=ITEM),
            patch("tools.send_mail.deliver", return_value="ACCEPTED") as delivery,
        ):
            exit_code, _ = self.invoke(values)

        # Then
        self.assertEqual(exit_code, 0)
        delivery.assert_called_once_with(ANY, LEADERS, ITEM)

    def test_selected_user_receives_only_their_dedicated_leaders(self) -> None:
        # Given
        values = dict(VALID_ENV)
        values.update(
            {
                "USER_2_ID": "bob",
                "USER_2_NAME": "李四",
                "USER_2_GIT_EMAIL": "bob@example.com",
                "USER_2_LEADER_EMAIL": "bob-leader@example.com",
            },
        )
        bob_item = Report(
            user_id=UserId("bob"),
            report_date="2026-07-17",
            subject="2026-07-17 bob 代码质量审查日报",
            html="<html><body>李四（bob）</body></html>",
        )
        bob_argv = tuple(value.replace("alice", "bob") for value in SEND_ARGV)

        # When
        with (
            patch("tools.send_mail.report", return_value=bob_item),
            patch("tools.send_mail.deliver", return_value="ACCEPTED") as delivery,
        ):
            exit_code, _ = self.invoke(values, bob_argv)

        # Then
        self.assertEqual(exit_code, 0)
        delivery.assert_called_once_with(
            ANY,
            (EmailAddress("bob-leader@example.com"),),
            bob_item,
        )

    def test_invalid_default_leaders_do_not_affect_dedicated_leaders(self) -> None:
        # Given
        values = dict(VALID_ENV)
        values["DEFAULT_LEADER_EMAIL"] = (
            "default@example.com,DEFAULT@example.com"
        )

        # When
        with (
            patch("tools.send_mail.report", return_value=ITEM),
            patch("tools.send_mail.deliver", return_value="ACCEPTED") as delivery,
        ):
            exit_code, _ = self.invoke(values)

        # Then
        self.assertEqual(exit_code, 0)
        delivery.assert_called_once_with(ANY, LEADERS, ITEM)

    def test_send_mode_rejects_duplicate_default_leaders_before_delivery(self) -> None:
        # Given
        values = dict(VALID_ENV)
        values["USER_1_LEADER_EMAIL"] = ""
        values["DEFAULT_LEADER_EMAIL"] = (
            "default@example.com,DEFAULT@example.com"
        )

        # When
        with (
            patch("tools.send_mail.report", return_value=ITEM),
            patch("tools.send_mail.deliver") as delivery,
        ):
            exit_code, output = self.invoke(values)

        # Then
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            output,
            '{"status":"投递前失败：邮件地址配置重复",'
            '"error_code":"邮箱配置错误"}',
        )
        self.assertNotIn("default@example.com", output.casefold())
        delivery.assert_not_called()

    def test_deliver_sends_one_message_to_all_leaders(self) -> None:
        # Given
        connection = MagicMock()
        client = connection.__enter__.return_value
        client.send_message.return_value = {}

        # When
        with patch("tools.send_mail.smtplib.SMTP_SSL", return_value=connection):
            status = deliver(CONFIG, LEADERS, ITEM)

        # Then
        self.assertEqual(status, "ACCEPTED")
        message = client.send_message.call_args.args[0]
        self.assertEqual(
            str(message["To"]),
            "leader-a@example.com, leader-b@example.com",
        )

    def test_deliver_reports_partial_when_only_one_leader_is_refused(self) -> None:
        # Given
        connection = MagicMock()
        connection.__enter__.return_value.send_message.return_value = {
            "leader-b@example.com": (550, b"rejected"),
        }

        # When
        with patch("tools.send_mail.smtplib.SMTP_SSL", return_value=connection):
            status = deliver(CONFIG, LEADERS, ITEM)

        # Then
        self.assertEqual(status, "PARTIAL")

    def test_deliver_reports_unknown_when_one_leader_has_temporary_failure(self) -> None:
        # Given
        connection = MagicMock()
        connection.__enter__.return_value.send_message.return_value = {
            "leader-b@example.com": (450, b"try later"),
        }

        # When
        with patch("tools.send_mail.smtplib.SMTP_SSL", return_value=connection):
            status = deliver(CONFIG, LEADERS, ITEM)

        # Then
        self.assertEqual(status, "UNKNOWN")

    def test_deliver_reports_rejected_when_all_leaders_are_refused(self) -> None:
        # Given
        connection = MagicMock()
        connection.__enter__.return_value.send_message.return_value = {
            "leader-a@example.com": (550, b"rejected"),
            "leader-b@example.com": (550, b"rejected"),
        }

        # When
        with patch("tools.send_mail.smtplib.SMTP_SSL", return_value=connection):
            status = deliver(CONFIG, LEADERS, ITEM)

        # Then
        self.assertEqual(status, "REJECTED")

    def test_send_mode_reports_partial_acceptance_without_success(self) -> None:
        # Given / When
        with (
            patch("tools.send_mail.report", return_value=ITEM),
            patch("tools.send_mail.deliver", return_value="PARTIAL"),
        ):
            exit_code, output = self.invoke(VALID_ENV)

        # Then
        self.assertEqual(exit_code, 4)
        self.assertEqual(
            output,
            '{"status":"邮件仅被部分收件服务器接受","error_code":"部分接受",'
            '"user_id":"alice","report_date":"2026-07-17",'
            '"delivery_status":"PARTIAL"}',
        )


if __name__ == "__main__":
    _ = unittest.main()
