"""严格解析和选择根项目注册表。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
import hashlib
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Final, Iterable

from tools.registry_yaml import ParsedProject, RegistryYamlError, Scalar, YamlErrorCode, parse_registry_yaml


class RegistryErrorCode(StrEnum):
    READ_FAILED = "read_failed"
    INVALID_ENCODING = "invalid_encoding"
    UNSAFE_SYNTAX = "unsafe_syntax"
    INVALID_TOP_LEVEL = "invalid_top_level"
    INVALID_VERSION = "invalid_version"
    INVALID_PROJECTS = "invalid_projects"
    DUPLICATE_PROJECT_ID = "duplicate_project_id"


class RegistryError(Exception):
    """不包含注册表原文的稳定全局错误。"""

    def __init__(self, code: RegistryErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class Project:
    project_id: str
    name: str
    code_dir: PurePosixPath
    standards_dir: PurePosixPath
    default_branch: str
    repository_url_config_key: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class InvalidProject:
    project_id: str | None
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectRegistry:
    version: int
    sha256: str
    projects: tuple[Project, ...]
    invalid_projects: tuple[InvalidProject, ...]


class SelectionCode(StrEnum):
    UNSAFE_ID = "unsafe_id"
    UNKNOWN_ID = "unknown_id"
    DISABLED_ID = "disabled_id"
    INVALID_ID = "invalid_id"


@dataclass(frozen=True, slots=True)
class SelectionDiagnostic:
    code: SelectionCode
    project_id: str | None
    message: str


@dataclass(frozen=True, slots=True)
class ProjectSelection:
    projects: tuple[Project, ...]
    diagnostics: tuple[SelectionDiagnostic, ...]


_PROJECT_ID: Final = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
_URL_KEY: Final = re.compile(r"PROJECT_[A-Z0-9_]{1,111}_REPO_URL\Z")
_BRANCH_CHARS: Final = re.compile(r"[A-Za-z0-9._/-]+\Z")
_FIELDS: Final = frozenset(
    {"project_id", "name", "code_dir", "standards_dir", "default_branch", "repository_url_config_key", "enabled"}
)
_REQUIRED: Final = _FIELDS - {"enabled"}

@dataclass(frozen=True, slots=True)
class _Candidate:
    project: Project | None
    project_id: str | None
    code_parts: tuple[str, ...] | None
    standards_parts: tuple[str, ...] | None
    url_key: str | None
    errors: tuple[str, ...]


def _global(code: RegistryErrorCode, message: str) -> RegistryError:
    return RegistryError(code, message)


def _string(values: dict[str, Scalar], field: str, errors: list[str]) -> str | None:
    value = values.get(field)
    if not isinstance(value, str) or not value.strip() or any(ord(character) < 32 or ord(character) == 127 for character in value):
        errors.append(f"字段 {field} 必须是非空字符串")
        return None
    return value


def _unsafe_ancestor(repository_root: Path, parts: tuple[str, ...]) -> bool:
    current = repository_root
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    for part in parts:
        current /= part
        try:
            status = current.lstat()
        except FileNotFoundError:
            return False
        except OSError:
            return True
        attributes = status.st_file_attributes if sys.platform == "win32" else 0
        if stat.S_ISLNK(status.st_mode) or bool(attributes & reparse_flag):
            return True
    return False


def _path(
    value: str | None,
    root: tuple[str, str],
    field: str,
    errors: list[str],
    repository_root: Path,
) -> tuple[str, ...] | None:
    if value is None or "\\" in value or value.startswith(("/", "//")) or re.match(r"[A-Za-z]:", value):
        errors.append(f"字段 {field} 必须是安全的仓库相对 POSIX 路径")
        return None
    parts = tuple(value.split("/"))
    if len(parts) <= 2 or parts[:2] != root or any(part in {"", ".", ".."} for part in parts):
        errors.append(f"字段 {field} 必须严格位于 {'/'.join(root)} 下")
        return None
    if _unsafe_ancestor(repository_root, parts):
        errors.append(f"字段 {field} 不得经过符号链接或重解析点")
        return None
    return parts


def _branch_valid(value: str) -> bool:
    segments = value.split("/")
    return bool(
        _BRANCH_CHARS.fullmatch(value)
        and value[0].isalnum()
        and value[-1] not in "./"
        and ".." not in value
        and "//" not in value
        and "@{" not in value
        and all(segment and not segment.startswith(".") and not segment.endswith(".lock") for segment in segments)
    )


def _candidate(raw: ParsedProject, repository_root: Path) -> _Candidate:
    values = dict(raw.values)
    errors: list[str] = []
    unknown = set(values) - _FIELDS
    missing = _REQUIRED - set(values)
    if unknown:
        errors.append("项目包含未知字段")
    if missing:
        errors.append("项目缺少必需字段")
    project_id = _string(values, "project_id", errors)
    name = _string(values, "name", errors)
    code = _string(values, "code_dir", errors)
    standards = _string(values, "standards_dir", errors)
    branch = _string(values, "default_branch", errors)
    url_key = _string(values, "repository_url_config_key", errors)
    enabled_value = values.get("enabled", True)
    enabled = enabled_value if isinstance(enabled_value, bool) else None
    if enabled is None:
        errors.append("字段 enabled 必须是 Boolean")
    if project_id is not None and not _PROJECT_ID.fullmatch(project_id):
        errors.append("字段 project_id 格式无效")
    if branch is not None and not _branch_valid(branch):
        errors.append("字段 default_branch 格式无效")
    if url_key is not None and (len(url_key) > 128 or not _URL_KEY.fullmatch(url_key)):
        errors.append("字段 repository_url_config_key 不属于专用命名空间")
    code_parts = _path(code, ("data", "code"), "code_dir", errors, repository_root)
    standards_parts = _path(standards, ("standards", "projects"), "standards_dir", errors, repository_root)
    project = None
    if not errors and project_id is not None and name is not None and code is not None and standards is not None and branch is not None and url_key is not None and enabled is not None:
        project = Project(project_id, name, PurePosixPath(code), PurePosixPath(standards), branch, url_key, enabled)
    return _Candidate(project, project_id, code_parts, standards_parts, url_key, tuple(errors))


def _collisions(candidates: tuple[_Candidate, ...]) -> tuple[_Candidate, ...]:
    error_sets = [list(candidate.errors) for candidate in candidates]
    for index, left in enumerate(candidates):
        for other_index in range(index + 1, len(candidates)):
            right = candidates[other_index]
            for left_parts, right_parts, message in (
                (left.code_parts, right.code_parts, "code_dir 与其他项目重叠"),
                (left.standards_parts, right.standards_parts, "standards_dir 与其他项目重叠"),
            ):
                if left_parts is not None and right_parts is not None:
                    folded_left = tuple(part.casefold() for part in left_parts)
                    folded_right = tuple(part.casefold() for part in right_parts)
                    shortest = min(len(folded_left), len(folded_right))
                    if folded_left[:shortest] == folded_right[:shortest]:
                        error_sets[index].append(message)
                        error_sets[other_index].append(message)
            if left.url_key is not None and left.url_key == right.url_key:
                error_sets[index].append("repository_url_config_key 与其他项目重复")
                error_sets[other_index].append("repository_url_config_key 与其他项目重复")
    return tuple(replace(candidate, project=None if errors else candidate.project, errors=tuple(dict.fromkeys(errors))) for candidate, errors in zip(candidates, error_sets, strict=True))


def load_project_registry(path: str | Path) -> ProjectRegistry:
    registry_path = Path(path)
    try:
        source = registry_path.read_bytes()
    except OSError:
        raise _global(RegistryErrorCode.READ_FAILED, "项目注册表缺失或不可读") from None
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise _global(RegistryErrorCode.INVALID_ENCODING, "项目注册表不是有效 UTF-8") from None
    digest = hashlib.sha256(source).hexdigest()
    try:
        parsed = parse_registry_yaml(text)
    except RegistryYamlError as error:
        codes = {
            YamlErrorCode.UNSAFE_SYNTAX: RegistryErrorCode.UNSAFE_SYNTAX,
            YamlErrorCode.INVALID_TOP_LEVEL: RegistryErrorCode.INVALID_TOP_LEVEL,
            YamlErrorCode.INVALID_PROJECTS: RegistryErrorCode.INVALID_PROJECTS,
        }
        raise _global(codes[error.code], str(error)) from None
    version = parsed.version
    if version != 1 or isinstance(version, bool):
        raise _global(RegistryErrorCode.INVALID_VERSION, "注册表版本必须是整数 1")
    raw_projects = parsed.projects
    ids = [dict(raw.values).get("project_id") for raw in raw_projects]
    string_ids = [value for value in ids if isinstance(value, str)]
    if len(string_ids) != len(set(string_ids)):
        raise _global(RegistryErrorCode.DUPLICATE_PROJECT_ID, "项目注册表包含重复 project_id")
    candidates = _collisions(tuple(_candidate(raw, registry_path.parent) for raw in raw_projects))
    return ProjectRegistry(
        version,
        digest,
        tuple(candidate.project for candidate in candidates if candidate.project is not None),
        tuple(InvalidProject(candidate.project_id, candidate.errors) for candidate in candidates if candidate.errors),
    )


def select_projects(registry: ProjectRegistry, requested_ids: Iterable[str] | None = None) -> ProjectSelection:
    if requested_ids is None:
        return ProjectSelection(tuple(project for project in registry.projects if project.enabled), ())
    valid = {project.project_id: project for project in registry.projects}
    invalid = {project.project_id for project in registry.invalid_projects if project.project_id is not None}
    seen: set[str] = set()
    selected: list[Project] = []
    diagnostics: list[SelectionDiagnostic] = []
    for requested in requested_ids:
        if requested in seen:
            continue
        seen.add(requested)
        if not _PROJECT_ID.fullmatch(requested):
            diagnostics.append(SelectionDiagnostic(SelectionCode.UNSAFE_ID, None, "项目选择包含不安全标识，已跳过"))
        elif requested in invalid:
            diagnostics.append(SelectionDiagnostic(SelectionCode.INVALID_ID, requested, f"项目 {requested} 的注册项无效，已跳过"))
        elif requested not in valid:
            diagnostics.append(SelectionDiagnostic(SelectionCode.UNKNOWN_ID, requested, f"项目 {requested} 未注册，已跳过"))
        elif not valid[requested].enabled:
            diagnostics.append(SelectionDiagnostic(SelectionCode.DISABLED_ID, requested, f"项目 {requested} 已禁用，已跳过"))
        else:
            selected.append(valid[requested])
    return ProjectSelection(tuple(selected), tuple(diagnostics))
