from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from types import MappingProxyType
import unicodedata
import unittest
from typing import Final, Literal
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DAILY_REVIEW = ROOT / ".opencode" / "commands" / "daily-review.md"
CODE_REVIEW = ROOT / ".opencode" / "commands" / "code-review.md"
EMAIL_STYLE = ROOT / ".opencode" / "skills" / "code-review-email-style" / "SKILL.md"

IdentityMode = Literal["validate-user", "resolve-user"]
IdentityValue = str | int | None
VALIDATE_FIELDS: Final = frozenset(("status", "user_name"))
RESOLVE_FIELDS: Final = frozenset(("user_id", "user_name"))
EXPECTED_FIELDS: Final[Mapping[IdentityMode, frozenset[str]]] = MappingProxyType(
    {"validate-user": VALIDATE_FIELDS, "resolve-user": RESOLVE_FIELDS}
)
CONTRACT_SOURCES: Final = (DAILY_REVIEW, CODE_REVIEW, EMAIL_STYLE)
MACHINE_AUTHORIZATIONS: Final = (
    "NAME 可作为路径",
    "NAME 用于文件名",
    "NAME 允许作为 CLI 参数",
    "user_name 可以用作聚合键",
    "NAME 可用于收件人路由",
    "user_name 作为邮件主题",
)
LEGACY_AUTHORIZATIONS: Final = (
    'validate-user 也可接受 {"status":"VALID"}',
    'resolve-user 也可接受 {"user_id":"<user_id>"}',
)
POSITIVE_NAME_AUTHORIZATION: Final = re.compile(
    r"(?:NAME|user_name)[^。\n；不只仅]{0,24}"
    + r"(?:可(?:以)?(?:作为|用作|用于)?|允许(?:作为|用作|用于)?|作为|用作|用于)"
    + r"[^。\n；不]{0,24}(?:路径|文件名|CLI\s*参数|聚合键|收件人路由|邮件主题)"
)
LEGACY_PAYLOAD_AUTHORIZATION: Final = re.compile(
    r'(?:validate-user[^。\n；]{0,24}(?:可|允许|接受|兼容|支持)[^。\n；]{0,24}\{"status":"VALID"\}'
    + r'|resolve-user[^。\n；]{0,24}(?:可|允许|接受|兼容|支持)[^。\n；]{0,24}\{"user_id":"<user_id>"\})'
)


@dataclass(frozen=True, slots=True)
class IdentityResult:
    mode: IdentityMode
    user_id: str
    payload: Mapping[str, IdentityValue]


def identity_payloads_are_valid(results: Sequence[IdentityResult]) -> bool:
    names_by_id: dict[str, str] = {}
    for result in results:
        expected_fields = EXPECTED_FIELDS[result.mode]
        if result.payload.get("user_id", result.user_id) != result.user_id:
            return False
        if frozenset(result.payload) != expected_fields:
            return False
        user_name = result.payload["user_name"]
        if not isinstance(user_name, str):
            return False
        if (
            user_name != user_name.strip()
            or not user_name
            or len(user_name) > 128
            or any(unicodedata.category(character) == "Cc" for character in user_name)
        ):
            return False
        known_name = names_by_id.setdefault(result.user_id, user_name)
        if known_name != user_name:
            return False
    return True


class ReviewIdentityContractTests(unittest.TestCase):
    def review_surfaces(self) -> tuple[str, str, str]:
        return (
            DAILY_REVIEW.read_text(encoding="utf-8"),
            CODE_REVIEW.read_text(encoding="utf-8"),
            EMAIL_STYLE.read_text(encoding="utf-8"),
        )

    def assert_safe_display_name_contract(self, contract: str) -> None:
        required_clauses = (
            "`USER_<n>_NAME`",
            "去除首尾空白后必须非空",
            "最多 128 个 Unicode 码点",
            "Unicode `Cc` 类控制字符",
            "允许重名",
            "保留其他 Unicode 字符",
            '`list-users` 只返回 `{"user_ids":[...]}`',
            '`validate-user` 对有效规范用户 ID 只返回 `{"status":"VALID","user_name":"<NAME>"}`',
            '`resolve-user` 只在 Git Author Email 唯一匹配时返回 `{"user_id":"<user_id>","user_name":"<NAME>"}`',
            "路径、文件名、CLI 参数、聚合键、收件人路由和邮件主题只使用规范用户 ID",
            "`<张&三>` 必须按不可信文本转义为 `&lt;张&amp;三&gt;（alice）`",
            "不得改变同步、SMTP 或投递语义",
        )
        payloads = (
            '{"user_ids":[...]}',
            '{"status":"VALID","user_name":"<NAME>"}',
            '{"user_id":"<user_id>","user_name":"<NAME>"}',
        )
        for clause in required_clauses:
            self.assertIn(clause, contract)
        for payload in payloads:
            self.assertEqual(contract.count(payload), 1)
        self.assertNotRegex(
            contract,
            r'(?:validate-user[^\n]*\{"status":"VALID"\}|resolve-user[^\n]*\{"user_id":"<user_id>"\})',
        )
        self.assertNotRegex(
            contract,
            r"NAME[^\n。；]{0,20}(?:可|允许|用于)[^\n。；]{0,20}(?:路径|CLI|聚合|收件人路由|邮件主题)",
        )

    def assert_no_contradictory_identity_authorization(self, contract: str) -> None:
        self.assertNotRegex(contract, POSITIVE_NAME_AUTHORIZATION)
        self.assertNotRegex(contract, LEGACY_PAYLOAD_AUTHORIZATION)

    def test_authoritative_contract_defines_safe_display_name_boundaries(self) -> None:
        # Given: the authoritative contract and contradictory in-memory variants.
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        mutations = (
            contract.replace(',"user_name":"<NAME>"', "", 1),
            contract + '\n{"status":"VALID","user_name":"<NAME>"}\n',
            contract + '\nvalidate-user 也可以只返回 {"status":"VALID"}\n',
            contract + '\nresolve-user 也可以只返回 {"user_id":"<user_id>"}\n',
            *(
                contract + f"\nNAME 可用于{boundary}\n"
                for boundary in ("路径", "CLI", "聚合", "收件人路由", "邮件主题")
            ),
        )

        # When/Then: the valid contract passes and every conflicting variant fails.
        self.assert_safe_display_name_contract(contract)
        for mutation in mutations:
            with self.subTest(mutation=mutation[-40:]):
                with self.assertRaises(AssertionError):
                    self.assert_safe_display_name_contract(mutation)

    def test_review_commands_require_exact_display_name_payloads(self) -> None:
        # Given: valid identity responses, malformed variants, and all review surfaces.
        valid = (
            IdentityResult(
                "validate-user",
                "alice",
                {"status": "VALID", "user_name": "张三"},
            ),
            IdentityResult(
                "resolve-user",
                "alice",
                {"user_id": "alice", "user_name": "张三"},
            ),
        )
        invalid = (
            valid + (IdentityResult("resolve-user", "bob", {"user_id": "bob"}),),
            valid
            + (
                IdentityResult(
                    "resolve-user",
                    "bob",
                    {"user_id": "bob", "user_name": "李四", "extra": "forbidden"},
                ),
            ),
            valid
            + (
                IdentityResult(
                    "resolve-user",
                    "bob",
                    {"user_id": "bob", "user_name": 7},
                ),
            ),
            valid
            + (
                IdentityResult(
                    "resolve-user",
                    "bob",
                    {"user_id": "bob", "user_name": "李\x00四"},
                ),
            ),
            valid
            + (
                IdentityResult(
                    "resolve-user",
                    "alice",
                    {"user_id": "alice", "user_name": "李四"},
                ),
            ),
        )

        # When: the fixture validator parses responses and the contracts are loaded.
        valid_result = identity_payloads_are_valid(valid)
        invalid_results = tuple(identity_payloads_are_valid(case) for case in invalid)
        daily, manual, skill = self.review_surfaces()

        # Then: fixtures enforce the schema and every surface states the same boundary.
        self.assertTrue(valid_result)
        self.assertEqual(invalid_results, (False, False, False, False, False))
        command_clauses = (
            '`list-users` 成功结果必须恰好包含 `{"user_ids":[...]}`',
            '`validate-user` 成功结果必须恰好包含字符串字段 `status`、`user_name`',
            '`resolve-user` 成功结果必须恰好包含字符串字段 `user_id`、`user_name`',
            "缺失、多余、类型无效或姓名无效的成功字段必须拒绝",
            "同一规范用户 ID 对应不一致的 `user_name` 必须拒绝",
        )
        for command in (daily, manual):
            for clause in command_clauses:
                self.assertIn(clause, command)
        self.assertIn("调用方必须提供已校验的规范 `user_id` 与 `user_name`", skill)
        for contract in (daily, manual, skill):
            self.assert_no_contradictory_identity_authorization(contract)

    def test_display_name_never_replaces_machine_user_id(self) -> None:
        # Given: both review commands and the HTML presentation contract.
        daily, manual, skill = self.review_surfaces()

        # When: identity display, machine-key, and output-gate clauses are inspected.
        identity_clause = "用户身份只以转义后的纯文本 `姓名（user_id）` 显示"
        id_only_clause = "聚合键、报告路径、CLI 参数和投递路由只使用规范用户 ID"
        escaped_example = "`&lt;张&amp;三&gt;（alice）`"

        # Then: names are display-only, escaped, and cannot alter workflow semantics.
        for command in (daily, manual):
            self.assertIn(identity_clause, command)
            self.assertIn(id_only_clause, command)
            self.assertIn(escaped_example, command)
        self.assertIn("手动流程不生成 HTML 或发送邮件", manual)
        self.assertIn("Markdown 成功后显式加载 `code-review-email-style`", daily)
        self.assertIn("--send --user <id> --markdown <path> --html <path>", daily)
        self.assertIn(identity_clause, skill)
        self.assertIn("`<张&三>（alice）` 是不可信纯文本", skill)
        self.assertIn(escaped_example, skill)
        self.assertIn("绝不能作为 HTML 标记", skill)
        for contract in (daily, manual, skill):
            self.assert_no_contradictory_identity_authorization(contract)

    def test_review_surfaces_reject_contradictory_identity_authorization(self) -> None:
        # Given: every source paired with machine-boundary and legacy authorizations.
        mutations = tuple(
            (source, f"\n{authorization}。\n")
            for source in CONTRACT_SOURCES
            for authorization in MACHINE_AUTHORIZATIONS
        ) + tuple(
            (source, f"\n{authorization}。\n")
            for source in CONTRACT_SOURCES
            for authorization in LEGACY_AUTHORIZATIONS
        )
        original_read_text = Path.read_text

        # When/Then: both real tests reject each patched source contradiction.
        self.assertEqual(len(mutations), 24)
        for source, mutation in mutations:
            def mutated_read_text(path: Path, encoding: str | None = None) -> str:
                content = original_read_text(path, encoding=encoding)
                return content + mutation if path == source else content

            with self.subTest(source=source.name, mutation=mutation.strip()):
                with patch.object(Path, "read_text", autospec=True, side_effect=mutated_read_text):
                    with self.assertRaises(AssertionError):
                        self.test_review_commands_require_exact_display_name_payloads()
                    with self.assertRaises(AssertionError):
                        self.test_display_name_never_replaces_machine_user_id()


if __name__ == "__main__":
    _ = unittest.main()
