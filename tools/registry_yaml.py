"""项目注册表专用的最小 YAML 行解析器。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
import re
from typing import Final, TypeAlias


Scalar: TypeAlias = str | bool | int


class YamlErrorCode(StrEnum):
    UNSAFE_SYNTAX = "unsafe_syntax"
    INVALID_TOP_LEVEL = "invalid_top_level"
    INVALID_PROJECTS = "invalid_projects"


class RegistryYamlError(Exception):
    def __init__(self, code: YamlErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ParsedProject:
    values: tuple[tuple[str, Scalar], ...]


@dataclass(frozen=True, slots=True)
class ParsedRegistry:
    version: Scalar
    projects: tuple[ParsedProject, ...]


_PLAIN: Final = re.compile(r"[-A-Za-z0-9._/: +()\\]+\Z")
_KEY: Final = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")


def _error(code: YamlErrorCode, message: str) -> RegistryYamlError:
    return RegistryYamlError(code, message)


def _scalar(raw: str) -> Scalar:
    if not raw or raw != raw.strip():
        raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表包含空值或多余空白")
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, UnicodeError):
            raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表包含无效字符串") from None
        if not isinstance(value, str):
            raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表包含不支持的值")
        return value
    if raw in {"true", "false"}:
        return raw == "true"
    if re.fullmatch(r"0|[1-9][0-9]*", raw):
        return int(raw)
    if raw.startswith(("'", "[", "{", "|", ">", "&", "*", "!")) or not _PLAIN.fullmatch(raw):
        raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表包含不支持或不安全的语法")
    return raw


def _mapping(line: str, prefix: str) -> tuple[str, Scalar]:
    body = line.removeprefix(prefix)
    if ": " not in body:
        raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表映射语法无效")
    key, raw = body.split(": ", 1)
    if ": " in raw or not _KEY.fullmatch(key):
        raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表键语法无效")
    return key, _scalar(raw)


def parse_registry_yaml(text: str) -> ParsedRegistry:
    """只解析注册表固定 schema 所需的 YAML 子集。"""
    if "\t" in text or "\x00" in text:
        raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表包含不安全字符")
    lines = tuple(
        line.rstrip("\r")
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    if any(line.strip() in {"---", "..."} or line.lstrip().startswith("%") for line in lines):
        raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表包含文档指令或标记")
    top: dict[str, Scalar | None] = {}
    projects: list[ParsedProject] = []
    current: dict[str, Scalar] | None = None
    in_projects = False
    for line in lines:
        if not line.startswith(" "):
            if line == "projects:":
                key, value = "projects", None
                in_projects = True
            else:
                key, value = _mapping(line, "")
                in_projects = False
            if key in top:
                raise _error(YamlErrorCode.INVALID_TOP_LEVEL, "注册表顶层键重复")
            top[key] = value
            continue
        if not in_projects:
            raise _error(YamlErrorCode.INVALID_TOP_LEVEL, "注册表顶层缩进无效")
        if line.startswith("  - "):
            if current is not None:
                projects.append(ParsedProject(tuple(current.items())))
            current = {}
            key, value = _mapping(line, "  - ")
        elif line.startswith("    ") and not line.startswith("     ") and current is not None:
            key, value = _mapping(line, "    ")
        else:
            raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表项目缩进或结构无效")
        if key in current:
            raise _error(YamlErrorCode.UNSAFE_SYNTAX, "注册表项目键重复")
        current[key] = value
    if current is not None:
        projects.append(ParsedProject(tuple(current.items())))
    if set(top) != {"version", "projects"}:
        raise _error(YamlErrorCode.INVALID_TOP_LEVEL, "注册表顶层结构无效")
    if top["projects"] is not None:
        raise _error(YamlErrorCode.INVALID_PROJECTS, "注册表 projects 必须是块列表")
    version = top["version"]
    if version is None:
        raise _error(YamlErrorCode.INVALID_TOP_LEVEL, "注册表 version 不得为空")
    return ParsedRegistry(version, tuple(projects))
