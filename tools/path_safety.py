from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Final

REPARSE_POINT: Final = stat.FILE_ATTRIBUTE_REPARSE_POINT


class SafetyError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


def _is_reparse(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise SafetyError("路径元数据无法安全读取。") from error
    is_windows_reparse = os.name == "nt" and bool(
        metadata.st_file_attributes & REPARSE_POINT
    )
    return stat.S_ISLNK(metadata.st_mode) or is_windows_reparse


def reject_reparse(path: Path) -> None:
    if _is_reparse(path):
        raise SafetyError("路径不得包含符号链接、junction 或 reparse point。")


def _validate_lexical_descendant(
    trusted_root: Path, candidate: Path, *, allow_root: bool
) -> tuple[Path, tuple[str, ...]]:
    root_text = os.fspath(trusted_root)
    candidate_text = os.fspath(candidate)
    if not os.path.isabs(root_text) or not os.path.isabs(candidate_text):
        raise SafetyError("受信根目录和候选路径必须是绝对路径。")
    if os.path.abspath(root_text) != root_text or os.path.abspath(candidate_text) != candidate_text:
        raise SafetyError("路径不得包含别名或当前目录、上级目录跳转。")

    normalized_root = os.path.normcase(root_text)
    normalized_candidate = os.path.normcase(candidate_text)
    try:
        common = os.path.commonpath((normalized_root, normalized_candidate))
    except ValueError as error:
        raise SafetyError("候选路径与受信根目录不在同一文件系统边界内。") from error
    if common != normalized_root:
        raise SafetyError("候选路径必须位于受信根目录之下。")

    root_parts = trusted_root.parts
    candidate_parts = candidate.parts
    if candidate_parts[: len(root_parts)] != root_parts:
        raise SafetyError("候选路径不得使用大小写或路径别名。")
    relative_parts = candidate_parts[len(root_parts) :]
    if not relative_parts:
        if allow_root:
            return trusted_root, ()
        raise SafetyError("候选路径不得等于受信根目录。")
    if any(part in {"", ".", ".."} for part in relative_parts):
        raise SafetyError("候选路径不得包含当前目录或上级目录跳转。")
    return candidate, relative_parts


def _inspect_directory(path: Path, *, allow_missing: bool) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        if allow_missing:
            return False
        raise SafetyError("路径必须是现有目录。") from None
    except OSError as error:
        raise SafetyError("路径元数据无法安全读取。") from error
    is_windows_reparse = os.name == "nt" and bool(
        metadata.st_file_attributes & REPARSE_POINT
    )
    if stat.S_ISLNK(metadata.st_mode) or is_windows_reparse:
        raise SafetyError("路径不得包含符号链接、junction 或 reparse point。")
    if not stat.S_ISDIR(metadata.st_mode):
        raise SafetyError("路径的现有组成部分必须是目录。")
    return True


def validate_safe_descendant(
    trusted_root: Path,
    candidate: Path,
    allow_missing: bool,
    allow_root: bool = False,
) -> Path:
    target, relative_parts = _validate_lexical_descendant(
        trusted_root, candidate, allow_root=allow_root
    )
    if not _inspect_directory(trusted_root, allow_missing=False):
        raise SafetyError("受信根目录必须是现有目录。")
    try:
        if os.fspath(trusted_root.resolve(strict=True)) != os.fspath(trusted_root):
            raise SafetyError("受信根目录不得通过别名解析。")
    except OSError as error:
        raise SafetyError("受信根目录无法安全解析。") from error

    current = trusted_root
    missing_found = False
    for part in relative_parts:
        current /= part
        if missing_found:
            continue
        exists = _inspect_directory(current, allow_missing=allow_missing)
        if not exists:
            missing_found = True
            continue
        try:
            if os.fspath(current.resolve(strict=True)) != os.fspath(current):
                raise SafetyError("候选路径不得通过别名解析。")
        except OSError as error:
            raise SafetyError("候选路径无法安全解析。") from error

    if missing_found:
        return target
    try:
        if os.fspath(target.resolve(strict=True)) != os.fspath(target):
            raise SafetyError("候选路径不得通过别名解析。")
    except OSError as error:
        raise SafetyError("候选路径无法安全解析。") from error
    return target


def prepare_safe_parent(trusted_root: Path, candidate: Path) -> Path:
    target = validate_safe_descendant(
        trusted_root, candidate, allow_missing=True, allow_root=False
    )
    parent = target.parent
    current = trusted_root
    parent_parts = parent.parts[len(trusted_root.parts) :]
    for part in parent_parts:
        current /= part
        try:
            os.mkdir(current)
        except FileExistsError:
            pass
        except OSError as error:
            raise SafetyError("无法安全创建候选路径的父目录。") from error
        _ = validate_safe_descendant(
            trusted_root, current, allow_missing=False, allow_root=False
        )
    return validate_safe_descendant(
        trusted_root, target, allow_missing=True, allow_root=False
    )


def validate_root(root: Path) -> None:
    data_path = root.parent
    repository = data_path.parent
    reject_reparse(repository)
    reject_reparse(data_path)
    reject_reparse(root)
    if not repository.is_dir() or not data_path.is_dir() or not root.is_dir():
        raise SafetyError("仓库内 data/code 路径必须是现有目录。")
    try:
        if repository.resolve(strict=True) != repository or root.resolve(strict=True) != root:
            raise SafetyError("仓库内 data/code 路径不得通过别名解析。")
    except OSError as error:
        raise SafetyError("仓库内 data/code 路径无法安全解析。") from error


def project_target(local_path: Path) -> Path:
    return validate_safe_descendant(
        local_path.parent, local_path, allow_missing=True, allow_root=False
    )


def validate_sync_path(local_path: Path) -> None:
    validate_root(local_path.parent)
    _ = validate_safe_descendant(
        local_path.parent, local_path, allow_missing=True, allow_root=False
    )
