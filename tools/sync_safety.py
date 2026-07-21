from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

from tools.git_askpass import (
    RepositoryOriginError,
    repository_origin,
    temporary_askpass,
)
from tools.git_metadata import reject_unsafe_git_config
from tools.path_safety import (
    REPARSE_POINT,
    SafetyError,
    prepare_safe_parent,
    project_target,
    validate_root,
    validate_safe_descendant,
    validate_sync_path,
)
from tools.repository_config import RepositoryCredentials

COMMAND_TIMEOUT_SECONDS: Final = 120
_SAFE_GIT_FAILURE_MESSAGES: Final = frozenset(
    {
        "Git 身份认证配置无效。",
        "Git 命令超时，未报告成功。",
        "Git 命令无法安全启动。",
        "Git 身份认证失败。",
        "Git 命令未安全完成。",
        "仓库提交标识无效，未报告成功。",
        "本地仓库根目录与注册路径不一致。",
        "工作区存在未提交变更，已拒绝同步。",
        "当前分支与注册分支不一致。",
        "仓库 origin 地址与注册配置不一致。",
        "无法可靠判断仓库是否可仅快进同步。",
        "本地历史无法仅快进同步，已拒绝更新。",
    }
)


class GitFailure(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message

    @property
    def safe_message(self) -> str:
        return self.message if self.message in _SAFE_GIT_FAILURE_MESSAGES else "Git 操作失败。"


class CommandSpecCredentialPairingError(Exception):
    def __init__(self) -> None:
        super().__init__("Git 认证配置必须成对提供。")


@dataclass(frozen=True, slots=True)
class CommandSpec:
    arguments: tuple[str, ...]
    working_directory: Path
    secrets: tuple[str, ...] = field(default=(), repr=False)
    credentials: RepositoryCredentials | None = field(default=None, repr=False)
    repository_url: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if (self.credentials is None) != (self.repository_url is None):
            raise CommandSpecCredentialPairingError


def _execute_git(
    spec: CommandSpec, prefix: tuple[str, ...], environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*prefix, *spec.arguments],
        cwd=spec.working_directory,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
        shell=False,
    )


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
        "credential.helper=",
        "-c",
        "protocol.ext.allow=never",
    )
    try:
        if spec.credentials is None:
            completed = _execute_git(spec, prefix, environment)
        else:
            repository_url = spec.repository_url
            if repository_url is None:
                raise GitFailure("Git 身份认证配置无效。")
            try:
                identity = url_identity(repository_url)
                origin = repository_origin(identity)
            except (RepositoryOriginError, SafetyError):
                raise GitFailure("Git 身份认证配置无效。") from None
            credential_prefix = (
                (*prefix, "-c", "http.followRedirects=false")
                if origin[0] == "http"
                else prefix
            )
            with temporary_askpass(empty_hooks_path, spec.credentials, origin) as session:
                try:
                    environment.update(session.environment)
                    environment["GIT_ASKPASS"] = str(session.launcher)
                    completed = _execute_git(spec, credential_prefix, environment)
                finally:
                    for key in tuple(session.environment):
                        environment.pop(key, None)
                    environment["GIT_ASKPASS"] = ""
    except subprocess.TimeoutExpired:
        raise GitFailure("Git 命令超时，未报告成功。") from None
    except OSError:
        raise GitFailure("Git 命令无法安全启动。") from None
    if completed.returncode != 0:
        safe_error = re.sub(
            r"(?i)(https?://)[^/@\s]+@", r"\1***@", completed.stderr.lower()
        )
        credential_secrets = () if spec.credentials is None else (
            spec.credentials.username, spec.credentials.password,
        )
        for secret in (*spec.secrets, *credential_secrets):
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
        hostname = parsed.hostname.lower()
        authority_host = f"[{hostname}]" if ":" in hostname else hostname
        port = f":{parsed_port}" if parsed_port is not None else ""
        path = parsed.path.lstrip("/").removesuffix(".git").rstrip("/")
        return f"{parsed.scheme.lower()}://{authority_host}{port}/{path}"
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
