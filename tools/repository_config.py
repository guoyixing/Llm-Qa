from __future__ import annotations

from pathlib import Path
from typing import Final


class ProtectedConfigError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


def parse_dotenv(path: Path, selected_keys: frozenset[str]) -> dict[str, tuple[str, ...]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ProtectedConfigError("无法安全读取受保护仓库配置。") from error
    values: dict[str, list[str]] = {}
    for source in lines:
        key, separator, raw_value = source.strip().partition("=")
        key = key.strip()
        if key not in selected_keys:
            continue
        value = raw_value.strip() if separator else ""
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values.setdefault(key, []).append(value)
    return {key: tuple(items) for key, items in values.items()}
