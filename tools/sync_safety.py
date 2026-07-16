from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Mapping
from configparser import ConfigParser, Error as ConfigParserError
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

from tools.path_safety import (
    REPARSE_POINT,
    SafetyError,
    prepare_safe_parent,
    project_target,
    reject_reparse,
    validate_root,
    validate_safe_descendant,
    validate_sync_path,
)

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
    invalid_character = any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in url
    )
    if not url or invalid_character:
        raise SafetyError("仓库 URL 格式无效。")
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
    scp = re.fullmatch(
        r"([A-Za-z0-9][A-Za-z0-9._-]{0,63})@"
        r"([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)"
        r":([A-Za-z0-9._~/-]+)",
        url,
    )
    if scp:
        path = scp.group(3).removesuffix(".git").rstrip("/")
        if path and not path.startswith("-") and all(
            part not in {"", ".", ".."} for part in path.split("/")
        ):
            return f"{scp.group(1)}@{scp.group(2).lower()}:{path}"
    raise SafetyError("仓库 URL 格式无效。")


def _inspect_git_config(config: Path) -> None:
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


def reject_unsafe_git_config(repository: Path) -> None:
    marker = repository / ".git"
    reject_reparse(marker)
    try:
        if not marker.is_dir():
            raise SafetyError("本地 Git 元数据不是目录。")
        common_file = marker / "commondir"
        worktree_config = marker / "config.worktree"
        reject_reparse(common_file)
        reject_reparse(worktree_config)
        if common_file.exists() or worktree_config.exists():
            raise SafetyError("本地 Git 元数据包含未声明的 worktree 配置。")
    except OSError as error:
        raise SafetyError("本地 Git 元数据无法安全读取。") from error
    _inspect_git_config(marker / "config")
