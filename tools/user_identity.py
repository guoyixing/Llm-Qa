from collections.abc import Mapping
from dataclasses import dataclass
from email.utils import parseaddr
import re
import unicodedata
from typing import Final, NewType, override

UserId = NewType("UserId", str)
UserName = NewType("UserName", str)
EmailAddress = NewType("EmailAddress", str)

USER_ID_PATTERN: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
USER_INDEX_PATTERN: Final = re.compile(r"USER_(\d+)_ID")
USER_PATTERN: Final = USER_ID_PATTERN
USER_KEY: Final = USER_INDEX_PATTERN
MAX_USER_NAME_CODE_POINTS: Final = 128


@dataclass(frozen=True, slots=True)
class IdentityConfigError(Exception):
    code: str
    message: str
    exit_code: int = 2

    @override
    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class User:
    user_id: UserId
    user_name: UserName
    git_email: EmailAddress


def parse_email(raw: str) -> EmailAddress:
    if any(unicodedata.category(character) == "Cc" for character in raw):
        raise IdentityConfigError("邮箱配置错误", "邮件地址配置无效")
    value = raw.strip()
    display, address = parseaddr(value)
    is_valid = (
        bool(address)
        and not display
        and address == value
        and "@" in address
    )
    if not is_valid:
        raise IdentityConfigError("邮箱配置错误", "邮件地址配置无效")
    return EmailAddress(address)


def parse_emails(raw: str) -> tuple[EmailAddress, ...]:
    parts = raw.split(",")
    if any(not part.strip() for part in parts):
        raise IdentityConfigError("邮箱配置错误", "邮件地址列表包含空项")
    addresses = tuple(parse_email(part) for part in parts)
    normalized = tuple(address.casefold() for address in addresses)
    if len(set(normalized)) != len(normalized):
        raise IdentityConfigError("邮箱配置错误", "邮件地址配置重复")
    return addresses


def parse_leaders(values: Mapping[str, str], user_id: UserId) -> tuple[EmailAddress, ...]:
    indexes = tuple(
        match.group(1)
        for key, value in values.items()
        if (match := USER_INDEX_PATTERN.fullmatch(key)) and value.strip() == str(user_id)
    )
    if USER_ID_PATTERN.fullmatch(str(user_id)) is None or len(indexes) != 1:
        raise IdentityConfigError("用户不存在", "未找到唯一规范用户", 3)
    raw_leaders = values.get(f"USER_{indexes[0]}_LEADER_EMAIL", "").strip()
    return parse_emails(raw_leaders) if raw_leaders else ()


def parse_users(values: Mapping[str, str]) -> tuple[User, ...]:
    indexes = sorted(
        match.group(1)
        for key in values
        if (match := USER_INDEX_PATTERN.fullmatch(key))
    )
    configured: list[User] = []
    seen_ids: set[UserId] = set()
    seen_git_emails: set[str] = set()

    for index in indexes:
        raw_id = values.get(f"USER_{index}_ID", "").strip()
        user_id = UserId(raw_id)
        if USER_ID_PATTERN.fullmatch(raw_id) is None or user_id in seen_ids:
            raise IdentityConfigError(
                "用户配置错误",
                "规范用户标识无效或重复",
            )

        raw_name = values.get(f"USER_{index}_NAME", "").strip()
        is_valid_name = (
            1 <= len(raw_name) <= MAX_USER_NAME_CODE_POINTS
            and not any(unicodedata.category(character) == "Cc" for character in raw_name)
        )
        if not is_valid_name:
            raise IdentityConfigError("用户配置错误", "用户姓名配置无效")

        git_email = parse_email(values.get(f"USER_{index}_GIT_EMAIL", ""))
        normalized_git_email = git_email.casefold()
        if normalized_git_email in seen_git_emails:
            raise IdentityConfigError(
                "用户配置错误",
                "Git 作者邮箱无效或重复",
            )

        configured.append(
            User(
                user_id=user_id,
                user_name=UserName(raw_name),
                git_email=git_email,
            ),
        )
        seen_ids.add(user_id)
        seen_git_emails.add(normalized_git_email)

    if not configured:
        raise IdentityConfigError("用户配置错误", "未配置任何用户")
    return tuple(configured)


def find_user(raw: str, configured: tuple[User, ...]) -> User:
    matches = tuple(user for user in configured if user.user_id == UserId(raw))
    if USER_ID_PATTERN.fullmatch(raw) is None or len(matches) != 1:
        raise IdentityConfigError("用户不存在", "未找到唯一规范用户", 3)
    return matches[0]
