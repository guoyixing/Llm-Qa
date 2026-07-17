from __future__ import annotations

import os
import shutil
import stat
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from tools.repository_config import RepositoryCredentials


_USERNAME = "LLM_QA_ASKPASS_USERNAME"
_PASSWORD = "LLM_QA_ASKPASS_PASSWORD"
_SCHEME = "LLM_QA_ASKPASS_SCHEME"
_HOST = "LLM_QA_ASKPASS_HOST"
_PORT = "LLM_QA_ASKPASS_PORT"
_PYTHON = "LLM_QA_ASKPASS_PYTHON"
_SCRIPT = "LLM_QA_ASKPASS_SCRIPT"

_RESPONDER = r'''import os
import re
import sys
from urllib.parse import unquote_to_bytes, urlsplit

def main():
    if len(sys.argv) != 2:
        return 1
    match = re.fullmatch(r"(Username|Password) for '([^']+)': ?", sys.argv[1])
    if match is None:
        return 1
    kind, target = match.groups()
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in target):
        return 1
    try:
        parsed = urlsplit(target)
        scheme = parsed.scheme.lower()
        port = parsed.port
    except ValueError:
        return 1
    if port is None:
        port = 80 if scheme == "http" else 443
    if (
        scheme not in {"http", "https"}
        or parsed.hostname is None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or (kind == "Username" and parsed.username is not None)
        or scheme != os.environ.get("LLM_QA_ASKPASS_SCHEME")
        or parsed.hostname.lower() != os.environ.get("LLM_QA_ASKPASS_HOST")
        or str(port) != os.environ.get("LLM_QA_ASKPASS_PORT")
    ):
        return 1
    if kind == "Password":
        if parsed.username is None:
            return 1
        if re.search(r"%(?![0-9A-Fa-f]{2})", parsed.username):
            return 1
        try:
            prompt_username = unquote_to_bytes(parsed.username).decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return 1
        if prompt_username != os.environ.get("LLM_QA_ASKPASS_USERNAME"):
            return 1
    key = "LLM_QA_ASKPASS_USERNAME" if kind == "Username" else "LLM_QA_ASKPASS_PASSWORD"
    value = os.environ.get(key)
    if value is None:
        return 1
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stdout.write(value + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''

_WINDOWS_LAUNCHER = """@echo off
setlocal DisableDelayedExpansion
\"%LLM_QA_ASKPASS_PYTHON%\" \"%LLM_QA_ASKPASS_SCRIPT%\" \"%~1\"
"""
_POSIX_LAUNCHER = """#!/bin/sh
exec "$LLM_QA_ASKPASS_PYTHON" "$LLM_QA_ASKPASS_SCRIPT" "$1"
"""


class RepositoryOriginError(Exception):
    def __init__(self) -> None:
        super().__init__("HTTP/HTTPS 仓库地址无效。")


@dataclass(frozen=True, slots=True)
class AskPassSession:
    launcher: Path
    environment: dict[str, str] = field(repr=False)


def repository_origin(repository_url: str) -> tuple[str, str, int]:
    try:
        parsed = urlsplit(repository_url)
        scheme = parsed.scheme.lower()
        port = parsed.port
    except ValueError as error:
        raise RepositoryOriginError from error
    if scheme not in {"http", "https"} or parsed.hostname is None:
        raise RepositoryOriginError
    if port is None:
        port = 80 if scheme == "http" else 443
    return scheme, parsed.hostname.lower(), port


@contextmanager
def temporary_askpass(
    hooks_directory: Path,
    credentials: RepositoryCredentials,
    origin: tuple[str, str, int],
) -> Iterator[AskPassSession]:
    parent = hooks_directory.resolve(strict=True)
    if not parent.is_dir():
        raise OSError("AskPass 父目录无效。")
    directory = Path(tempfile.mkdtemp(prefix="git-askpass-", dir=parent))
    environment: dict[str, str] = {}
    try:
        responder = directory / "responder.py"
        responder.write_text(_RESPONDER, encoding="utf-8", newline="\n")
        responder.chmod(stat.S_IRUSR | stat.S_IWUSR)
        if os.name == "nt":
            launcher = directory / "askpass.cmd"
            launcher.write_text(_WINDOWS_LAUNCHER, encoding="utf-8", newline="")
        else:
            launcher = directory / "askpass.sh"
            launcher.write_text(_POSIX_LAUNCHER, encoding="utf-8", newline="\n")
            launcher.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        environment.update(
            {
                _USERNAME: credentials.username,
                _PASSWORD: credentials.password,
                _SCHEME: origin[0],
                _HOST: origin[1],
                _PORT: str(origin[2]),
                _PYTHON: sys.executable,
                _SCRIPT: str(responder.resolve()),
            }
        )
        yield AskPassSession(launcher.resolve(), environment)
    finally:
        for key in tuple(environment):
            environment[key] = ""
        environment.clear()
        shutil.rmtree(directory)
