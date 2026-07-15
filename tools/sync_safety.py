from __future__ import annotations

import os
import re
import stat
import subprocess
from collections.abc import Mapping
from configparser import ConfigParser, Error as ConfigParserError
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

REPARSE_POINT: Final = stat.FILE_ATTRIBUTE_REPARSE_POINT
COMMAND_TIMEOUT_SECONDS: Final = 120
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
)


class SafetyError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


class GitFailure(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


@dataclass(frozen=True, slots=True)
class CommandSpec:
    arguments: tuple[str, ...]
    working_directory: Path
    secrets: tuple[str, ...] = ()


def run_git(spec: CommandSpec, empty_hooks_path: Path) -> str:
    allowed_environment = (
        "PATH",
        "HOMEDRIVE",
        "HOMEPATH",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "SSH_AUTH_SOCK",
        "LANG",
        "LC_ALL",
    )
    environment = {
        key: value
        for key in allowed_environment
        if (value := os.environ.get(key)) is not None
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": str(empty_hooks_path),
            "USERPROFILE": str(empty_hooks_path),
            "XDG_CONFIG_HOME": str(empty_hooks_path),
            "GIT_ASKPASS": "",
            "SSH_ASKPASS": "",
            "SSH_ASKPASS_REQUIRE": "never",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
        }
    )
    prefix = (
        "git",
        "--no-pager",
        "-c",
        f"core.hooksPath={empty_hooks_path}",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.pager=cat",
        "-c",
        "protocol.ext.allow=never",
    )
    try:
        completed = subprocess.run(
            [*prefix, *spec.arguments],
            cwd=spec.working_directory,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise GitFailure("Git 命令超时，未报告成功。") from error
    except OSError as error:
        raise GitFailure("Git 命令无法安全启动。") from error
    if completed.returncode != 0:
        safe_error = re.sub(
            r"(?i)(https?://)[^/@\s]+@", r"\1***@", completed.stderr.lower()
        )
        for secret in spec.secrets:
            safe_error = safe_error.replace(secret.lower(), "***") if secret else safe_error
        authentication_failed = any(
            item in safe_error
            for item in (
                "authentication failed",
                "could not read username",
                "permission denied",
                "access denied",
            )
        )
        message = "Git 身份认证失败。" if authentication_failed else "Git 命令未安全完成。"
        raise GitFailure(message)
    return completed.stdout.strip()


def url_identity(url: str) -> str:
    try:
        parsed = urlsplit(url)
        parsed_port = parsed.port
    except ValueError as error:
        raise SafetyError("仓库 URL 格式无效。") from error
    valid_url = (
        parsed.scheme in {"http", "https", "ssh", "git"}
        and parsed.hostname
        and parsed.path not in {"", "/"}
        and parsed.username is None
        and parsed.password is None
        and "?" not in url
        and "#" not in url
    )
    if valid_url and parsed.hostname is not None:
        port = f":{parsed_port}" if parsed_port is not None else ""
        path = parsed.path.lstrip("/").removesuffix(".git").rstrip("/")
        return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}/{path}"
    scp = re.fullmatch(r"[^@\s]+@([^:\s]+):(.+)", url)
    if scp:
        return f"{scp.group(1).lower()}:{scp.group(2).removesuffix('.git').rstrip('/')}"
    raise SafetyError("仓库 URL 格式无效。")


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


def _reject_reparse(path: Path) -> None:
    if _is_reparse(path):
        raise SafetyError("路径不得包含符号链接、junction 或 reparse point。")


def validate_root(root: Path) -> None:
    data_path = root.parent
    repository = data_path.parent
    _reject_reparse(repository)
    _reject_reparse(data_path)
    _reject_reparse(root)
    if not repository.is_dir() or not data_path.is_dir() or not root.is_dir():
        raise SafetyError("仓库内 data/code 路径必须是现有目录。")
    try:
        if repository.resolve(strict=True) != repository or root.resolve(strict=True) != root:
            raise SafetyError("仓库内 data/code 路径不得通过别名解析。")
    except OSError as error:
        raise SafetyError("仓库内 data/code 路径无法安全解析。") from error


def project_target(local_path: Path) -> Path:
    _reject_reparse(local_path)
    if local_path.exists() and not local_path.is_dir():
        raise SafetyError("固定项目路径存在但不是目录。")
    try:
        target = local_path.resolve(strict=False)
    except OSError as error:
        raise SafetyError("固定项目路径无法安全解析。") from error
    if target != local_path:
        raise SafetyError("固定项目路径不得使用别名。")
    return target


def validate_sync_path(local_path: Path) -> None:
    validate_root(local_path.parent)
    _reject_reparse(local_path)
    if local_path.exists() and not local_path.is_dir():
        raise SafetyError("固定项目路径存在但不是目录。")
    try:
        if local_path.resolve(strict=False) != local_path:
            raise SafetyError("同步路径不得通过别名解析。")
    except OSError as error:
        raise SafetyError("同步路径无法安全解析。") from error


def _inspect_git_config(config: Path) -> None:
    _reject_reparse(config)
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


def reject_unsafe_git_config(repository: Path) -> None:
    marker = repository / ".git"
    _reject_reparse(marker)
    try:
        if not marker.is_dir():
            raise SafetyError("本地 Git 元数据不是目录。")
        common_file = marker / "commondir"
        worktree_config = marker / "config.worktree"
        _reject_reparse(common_file)
        _reject_reparse(worktree_config)
        if common_file.exists() or worktree_config.exists():
            raise SafetyError("本地 Git 元数据包含未声明的 worktree 配置。")
    except OSError as error:
        raise SafetyError("本地 Git 元数据无法安全读取。") from error
    _inspect_git_config(marker / "config")
