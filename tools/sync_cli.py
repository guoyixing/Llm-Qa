from __future__ import annotations

import re
from typing import Final


SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")


class ArgumentError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


def parse_arguments(
    arguments: tuple[str, ...],
) -> tuple[str | None, tuple[str, ...] | None, bool]:
    if not arguments:
        return None, None, False
    if arguments in (("--help",), ("-h",)):
        return None, None, True
    if len(arguments) % 2:
        raise ArgumentError("同步参数格式无效。")
    expected_sha256: str | None = None
    requested: list[str] = []
    for index in range(0, len(arguments), 2):
        option, value = arguments[index : index + 2]
        if option == "--registry-sha256" and expected_sha256 is None:
            if not SHA256_PATTERN.fullmatch(value):
                raise ArgumentError("注册表快照摘要格式无效。")
            expected_sha256 = value
        elif option == "--project" and value:
            requested.append(value)
        else:
            raise ArgumentError("同步参数格式无效。")
    return expected_sha256, tuple(requested) or None, False
