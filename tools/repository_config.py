from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final


@dataclass(frozen=True, slots=True)
class RepositoryCredentials:
    username: str = field(repr=False)
    password: str = field(repr=False)


class ProtectedConfigError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


class RepositoryCredentialError(Exception):
    pass


def credential_keys(url_key: str) -> tuple[str, str]:
    prefix = url_key.removesuffix("_URL")
    return f"{prefix}_USERNAME", f"{prefix}_PASSWORD"


def repository_credentials(
    source: Mapping[str, tuple[str, ...]],
    sibling_keys: tuple[str, str],
    *,
    transport: str,
) -> RepositoryCredentials | None:
    username_key, password_key = sibling_keys
    username_values = source.get(username_key, ())
    password_values = source.get(password_key, ())
    if not username_values and not password_values:
        return None
    valid_pair = (
        transport in {"http", "https"}
        and len(username_values) == 1
        and len(password_values) == 1
        and _valid_credential_value(username_values[0])
        and _valid_credential_value(password_values[0])
    )
    if not valid_pair:
        raise RepositoryCredentialError
    return RepositoryCredentials(username_values[0], password_values[0])


def _valid_credential_value(value: str) -> bool:
    return bool(value) and len(value) <= 1024 and all(
        unicodedata.category(character) != "Cc" for character in value
    )


def parse_dotenv(path: Path, selected_keys: frozenset[str]) -> dict[str, tuple[str, ...]]:
    text: str | None
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            text = stream.read()
    except (OSError, UnicodeError):
        text = None
    if text is None:
        raise ProtectedConfigError("无法安全读取受保护仓库配置。")
    values: dict[str, list[str]] = {}
    lines = text.split("\n")
    for index, source in enumerate(lines):
        if index < len(lines) - 1 and source.endswith("\r"):
            source = source[:-1]
        raw_key, separator, raw_value = source.partition("=")
        key = raw_key.strip()
        if key not in selected_keys:
            continue
        credential_key = key.endswith(("_REPO_USERNAME", "_REPO_PASSWORD"))
        value = raw_value if separator and credential_key else raw_value.strip() if separator else ""
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values.setdefault(key, []).append(value)
    return {key: tuple(items) for key, items in values.items()}
