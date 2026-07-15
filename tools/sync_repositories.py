#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# ─── 运行说明 ───
# 1. 同步全部项目：python tools/sync_repositories.py
# 2. 同步单个项目：python tools/sync_repositories.py --project <项目 ID>
# 3. 只从仓库根目录 .env 读取三个固定项目 URL。
# ─────────────────

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, NewType, TypedDict

REPOSITORY_ROOT: Final = Path(__file__).absolute().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.sync_safety import (
    CommandSpec,
    GitFailure,
    SafetyError,
    project_target,
    reject_unsafe_git_config,
    run_git,
    url_identity,
    validate_root,
    validate_sync_path,
)

ProjectId = NewType("ProjectId", str)
REMOTE_NAME: Final = "origin"
COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")


class ExitCode(IntEnum):
    SUCCESS, PARTIAL_SUCCESS, CONFIGURATION_FAILURE, OPERATION_FAILURE = 0, 2, 3, 4


class Status(StrEnum):
    SUCCESS, FAILED = "success", "failed"


class ResultJson(TypedDict):
    project_id: str
    status: Status
    local_path: str
    commit: str
    message: str


@dataclass(frozen=True, slots=True)
class ProjectDefinition:
    project_id: ProjectId
    directory: str
    branch: str
    url_key: str


PROJECTS: Final = (
    ProjectDefinition(ProjectId("api"), "api", "main", "PROJECT_API_REPO_URL"),
    ProjectDefinition(ProjectId("web"), "web", "develop", "PROJECT_WEB_REPO_URL"),
    ProjectDefinition(ProjectId("jobs"), "jobs", "main", "PROJECT_JOBS_REPO_URL"),
)
URL_KEYS: Final = frozenset(project.url_key for project in PROJECTS)


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    project_id: ProjectId
    local_path: Path
    url: str
    branch: str


class ConfigError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


def failed(project_id: ProjectId, local_path: Path | None, message: str) -> ResultJson:
    return ResultJson(
        project_id=project_id, status=Status.FAILED,
        local_path="" if local_path is None else str(local_path),
        commit="", message=message,
    )


def parse_dotenv(path: Path) -> Mapping[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ConfigError("无法安全读取 .env 配置。") from error
    values: dict[str, str] = {}
    for number, source in enumerate(lines, start=1):
        line = source.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, raw_value = line.partition("=")
        key = key.strip()
        if key not in URL_KEYS:
            continue
        if not separator:
            raise ConfigError(f".env 第 {number} 行格式无效。")
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        _ = values.setdefault(key, value)
    return values


def repository_url(source: Mapping[str, str], key: str) -> str:
    value = source.get(key, "").strip()
    if not value:
        raise ConfigError(f"缺少必填配置 {key}。")
    return value


def load_config(env_path: Path) -> tuple[tuple[ProjectConfig, ...], tuple[ResultJson, ...]]:
    source = parse_dotenv(env_path)
    scaffold_root = env_path.parent.resolve()
    root = scaffold_root / "data" / "code"
    validate_root(root)
    projects: list[ProjectConfig] = []
    failures: list[ResultJson] = []
    targets: set[Path] = set()
    for definition in PROJECTS:
        local_path = root / definition.directory
        try:
            target = project_target(local_path)
            if target in targets:
                raise SafetyError("固定项目路径不得解析到重复目标。")
            url = repository_url(source, definition.url_key)
            _ = url_identity(url)
            projects.append(ProjectConfig(definition.project_id, local_path, url, definition.branch))
            targets.add(target)
        except (ConfigError, SafetyError) as error:
            failures.append(failed(definition.project_id, local_path, error.message))
        except (OSError, ValueError):
            failures.append(failed(definition.project_id, local_path, "固定项目配置无效。"))
    return tuple(projects), tuple(failures)


def checked_commit(project: ProjectConfig, empty_hooks_path: Path) -> str:
    commit = run_git(CommandSpec(("rev-parse", "HEAD"), project.local_path), empty_hooks_path)
    if not COMMIT_PATTERN.fullmatch(commit):
        raise GitFailure("仓库提交标识无效，未报告成功。")
    return commit


def synchronize(project: ProjectConfig, empty_hooks_path: Path) -> ResultJson:
    try:
        validate_sync_path(project.local_path)
        if not project.local_path.exists():
            arguments = (
                "clone", "--origin", REMOTE_NAME, "--branch", project.branch,
                "--single-branch", "--", project.url, str(project.local_path),
            )
            _ = run_git(
                CommandSpec(arguments, project.local_path.parent, (project.url,)),
                empty_hooks_path,
            )
            commit = checked_commit(project, empty_hooks_path)
            return ResultJson(
                project_id=project.project_id,
                status=Status.SUCCESS,
                local_path=str(project.local_path),
                commit=commit,
                message="仓库已安全克隆。",
            )
        reject_unsafe_git_config(project.local_path)
        root_output = run_git(
            CommandSpec(("rev-parse", "--show-toplevel"), project.local_path),
            empty_hooks_path,
        )
        root = Path(root_output).resolve()
        if root != project.local_path:
            raise GitFailure("本地仓库根目录与固定路径不一致。")
        if run_git(
            CommandSpec(("status", "--porcelain=v1"), project.local_path),
            empty_hooks_path,
        ):
            raise GitFailure("工作区存在未提交变更，已拒绝同步。")
        current_branch = run_git(
            CommandSpec(("branch", "--show-current"), project.local_path),
            empty_hooks_path,
        )
        if current_branch != project.branch:
            raise GitFailure("当前分支与固定分支不一致。")
        actual_url = run_git(
            CommandSpec(("remote", "get-url", REMOTE_NAME), project.local_path),
            empty_hooks_path,
        )
        if url_identity(actual_url) != url_identity(project.url):
            raise GitFailure("仓库 origin 地址与固定配置不一致。")
        previous_commit = checked_commit(project, empty_hooks_path)
        _ = run_git(
            CommandSpec(("fetch", "--prune", REMOTE_NAME), project.local_path),
            empty_hooks_path,
        )
        remote_ref = f"refs/remotes/{REMOTE_NAME}/{project.branch}"
        counts = run_git(
            CommandSpec(
                ("rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"),
                project.local_path,
            ),
            empty_hooks_path,
        ).split()
        if len(counts) != 2 or not all(value.isdecimal() for value in counts):
            raise GitFailure("无法可靠判断仓库是否可仅快进同步。")
        if int(counts[0]) != 0:
            raise GitFailure("本地历史无法仅快进同步，已拒绝更新。")
        _ = run_git(
            CommandSpec(
                ("pull", "--ff-only", REMOTE_NAME, project.branch),
                project.local_path,
            ),
            empty_hooks_path,
        )
        commit = checked_commit(project, empty_hooks_path)
        message = "仓库已仅快进同步。" if previous_commit != commit else "仓库已是最新状态。"
        return ResultJson(
            project_id=project.project_id,
            status=Status.SUCCESS,
            local_path=str(project.local_path),
            commit=commit,
            message=message,
        )
    except (GitFailure, SafetyError) as error:
        return failed(project.project_id, project.local_path, error.message)
    except ConfigError as error:
        return failed(project.project_id, project.local_path, error.message)
    except (OSError, ValueError):
        return failed(project.project_id, project.local_path, "本地操作未安全完成。")


def parse_arguments(arguments: tuple[str, ...]) -> tuple[str | None, bool]:
    if not arguments or arguments in (("--help",), ("-h",)):
        return None, bool(arguments)
    if len(arguments) == 2 and arguments[0] == "--project" and arguments[1]:
        return arguments[1], False
    raise ConfigError("参数无效。用法：python tools/sync_repositories.py [--project <项目 ID>]。")


def emit(results: tuple[ResultJson, ...]) -> None:
    print(json.dumps(results, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    try:
        selected, show_help = parse_arguments(tuple(sys.argv[1:]))
        if show_help:
            print("用法：python tools/sync_repositories.py [--project <项目 ID>]\n安全克隆或仅快进同步全部项目或指定项目。")
            return ExitCode.SUCCESS
        configured, config_failures = load_config(REPOSITORY_ROOT / ".env")
        projects = (
            configured
            if selected is None
            else tuple(item for item in configured if item.project_id == selected)
        )
        failures = (
            config_failures
            if selected is None
            else tuple(item for item in config_failures if item["project_id"] == selected)
        )
        if not projects and not failures:
            emit((failed(ProjectId(selected or "*"), None, "指定的项目 ID 未配置。"),))
            return ExitCode.OPERATION_FAILURE
        with TemporaryDirectory(prefix="review-git-hooks-") as empty_hooks:
            synced = tuple(synchronize(project, Path(empty_hooks)) for project in projects)
        results = failures + synced
        emit(results)
        successes = sum(result["status"] == Status.SUCCESS for result in results)
        if successes == len(results):
            return ExitCode.SUCCESS
        return ExitCode.PARTIAL_SUCCESS if successes else ExitCode.OPERATION_FAILURE
    except (ConfigError, SafetyError) as error:
        emit((failed(ProjectId("*"), None, error.message),))
        return ExitCode.CONFIGURATION_FAILURE
    except OSError:
        emit((failed(ProjectId("*"), None, "全局路径或临时安全目录无法使用。"),))
        return ExitCode.CONFIGURATION_FAILURE
    except KeyboardInterrupt:
        emit((failed(ProjectId("*"), None, "同步已被中断，未报告成功。"),))
        return ExitCode.OPERATION_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
