from __future__ import annotations

import os
import re
from collections.abc import Mapping
from configparser import ConfigParser, Error as ConfigParserError
from pathlib import Path
from typing import Final

from tools.path_safety import (
    SafetyError,
    reject_reparse,
    validate_safe_descendant,
)

GIT_PATH_FILE_MAX_BYTES: Final = 4096
ALLOWED_GIT_OPTIONS: Final = (
    (
        "core",
        frozenset(
            {
                "repositoryformatversion",
                "filemode",
                "bare",
                "logallrefupdates",
                "ignorecase",
                "symlinks",
                "precomposeunicode",
            }
        ),
    ),
    ("remote", frozenset({"url", "fetch"})),
    ("branch", frozenset({"remote", "merge"})),
    ("push", frozenset({"autosetupremote"})),
)


def _inspect_git_config(config: Path) -> None:
    """Reject Git configuration outside the synchronization allowlist."""
    reject_reparse(config)
    try:
        parser = ConfigParser(interpolation=None, strict=False)
        parser.read_string(config.read_text(encoding="utf-8"))
    except (ConfigParserError, OSError, UnicodeError) as error:
        raise SafetyError("本地 Git 配置无法安全读取。") from error
    defaults: Mapping[str, str] = parser.defaults()
    if defaults:
        raise SafetyError("本地 Git 配置包含未声明或危险键。")
    sections: list[str] = parser.sections()
    for section in sections:
        family = re.split(r"[ .]", section, maxsplit=1)[0].lower()
        allowed = next(
            (options for name, options in ALLOWED_GIT_OPTIONS if name == family),
            None,
        )
        options: list[str] = parser.options(section)
        if allowed is None or not set(options).issubset(allowed):
            raise SafetyError("本地 Git 配置包含未声明或危险键。")


def _read_git_path_file(path: Path, prefix: str = "") -> str:
    """Parse one bounded Git metadata path without following reparse points."""
    reject_reparse(path)
    try:
        if not path.is_file() or path.stat().st_size > GIT_PATH_FILE_MAX_BYTES:
            raise SafetyError("本地 Git 元数据路径文件无效。")
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise SafetyError("本地 Git 元数据路径文件无法安全读取。") from error
    if len(lines) != 1 or not lines[0].startswith(prefix):
        raise SafetyError("本地 Git 元数据路径文件无效。")
    value = lines[0][len(prefix) :]
    if not value or value != value.strip() or any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise SafetyError("本地 Git 元数据路径文件无效。")
    return value


def _metadata_path(base: Path, value: str) -> Path:
    """Normalize a Git metadata path before applying the trusted boundary."""
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return Path(os.path.normpath(candidate))


def _reject_worktree_config(path: Path) -> None:
    """Reject per-worktree configuration that bypasses the common allowlist."""
    reject_reparse(path)
    try:
        if path.exists():
            raise SafetyError("本地 Git 元数据包含未声明的 worktree 配置。")
    except OSError as error:
        raise SafetyError("本地 Git 元数据无法安全读取。") from error


def _standalone_common_dir(marker: Path, code_root: Path | None) -> Path:
    """Validate standalone metadata with an optional trusted root boundary."""
    try:
        if not marker.is_dir():
            raise SafetyError("本地 Git 元数据不是目录。")
        common_dir = (
            marker
            if code_root is None
            else validate_safe_descendant(code_root, marker, allow_missing=False)
        )
        common_file = common_dir / "commondir"
        reject_reparse(common_file)
        if common_file.exists():
            raise SafetyError("本地 Git 元数据包含未声明的 worktree 配置。")
    except OSError as error:
        raise SafetyError("本地 Git 元数据无法安全读取。") from error
    return common_dir


def reject_unsafe_git_config(
    repository: Path, code_root: Path | None = None
) -> None:
    """Validate standalone or linked-worktree metadata before invoking Git."""
    marker = repository / ".git"
    reject_reparse(marker)
    if code_root is None:
        common_dir = _standalone_common_dir(marker, None)
        _reject_worktree_config(common_dir / "config.worktree")
        _inspect_git_config(common_dir / "config")
        return
    _ = validate_safe_descendant(code_root, repository, allow_missing=False)
    try:
        if marker.is_dir():
            common_dir = _standalone_common_dir(marker, code_root)
        elif marker.is_file():
            admin_dir = validate_safe_descendant(
                code_root,
                _metadata_path(
                    repository,
                    _read_git_path_file(marker, "gitdir: "),
                ),
                allow_missing=False,
            )
            common_dir = validate_safe_descendant(
                code_root,
                _metadata_path(
                    admin_dir,
                    _read_git_path_file(admin_dir / "commondir"),
                ),
                allow_missing=False,
            )
            if admin_dir.parent != common_dir / "worktrees":
                raise SafetyError("本地 Git worktree 元数据关系无效。")
            back_pointer = _metadata_path(
                admin_dir,
                _read_git_path_file(admin_dir / "gitdir"),
            )
            if back_pointer != marker:
                raise SafetyError("本地 Git worktree 元数据关系无效。")
            _reject_worktree_config(admin_dir / "config.worktree")
        else:
            raise SafetyError("本地 Git 元数据不是目录。")
    except OSError as error:
        raise SafetyError("本地 Git 元数据无法安全读取。") from error
    _reject_worktree_config(common_dir / "config.worktree")
    _inspect_git_config(common_dir / "config")
