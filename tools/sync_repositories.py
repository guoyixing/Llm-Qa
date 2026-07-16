#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, TypedDict

REPOSITORY_ROOT: Final = Path(__file__).absolute().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.project_registry import Project, RegistryError, load_project_registry, select_projects
from tools.repository_config import ProtectedConfigError, parse_dotenv
from tools.sync_cli import ArgumentError, parse_arguments
from tools.sync_safety import (
    CommandSpec, GitFailure, SafetyError, prepare_safe_parent, reject_unsafe_git_config,
    run_git, url_identity, validate_root, validate_safe_descendant,
)

REMOTE_NAME: Final = "origin"
COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
PROJECT_ID_PATTERN: Final = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
URL_KEY_PATTERN: Final = re.compile(r"^PROJECT_[A-Z0-9_]{1,111}_REPO_URL$")


class ExitCode(IntEnum):
    SUCCESS, PARTIAL_SUCCESS, CONFIGURATION_FAILURE, OPERATION_FAILURE = 0, 2, 3, 4


class Status(StrEnum):
    SUCCESS, FAILED = "success", "failed"


class ResultJson(TypedDict):
    project_id: str
    status: Status
    local_path: str
    default_branch: str
    repository_url_config_key: str
    commit: str
    message: str


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    project_id: str
    local_path: Path
    url: str
    default_branch: str
    repository_url_config_key: str


class ConfigError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final = message


def failed(project_id: str, message: str, project: ProjectConfig | None = None) -> ResultJson:
    return ResultJson(
        project_id=project_id,
        status=Status.FAILED,
        local_path="" if project is None else str(project.local_path),
        default_branch="" if project is None else project.default_branch,
        repository_url_config_key="" if project is None else project.repository_url_config_key,
        commit="",
        message=message,
    )


def load_config(
    env_path: Path, projects: tuple[Project, ...]
) -> tuple[tuple[ProjectConfig, ...], tuple[ResultJson, ...]]:
    code_root = REPOSITORY_ROOT / "data" / "code"
    validate_root(code_root)
    prepared: list[tuple[Project, ProjectConfig]] = []
    failures: list[ResultJson] = []
    for project in projects:
        local_path = REPOSITORY_ROOT.joinpath(*project.code_dir.parts)
        candidate = ProjectConfig(
            project.project_id, local_path, "", project.default_branch, project.repository_url_config_key
        )
        try:
            _ = validate_safe_descendant(code_root, local_path, allow_missing=True)
            if not URL_KEY_PATTERN.fullmatch(project.repository_url_config_key):
                raise ConfigError("注册配置键不属于专用仓库 URL 命名空间。")
            prepared.append((project, candidate))
        except SafetyError:
            failures.append(failed(project.project_id, "注册项目路径无效。", candidate))
        except ConfigError as error:
            failures.append(failed(project.project_id, error.message, candidate))
    selected_keys = frozenset(item.repository_url_config_key for item, _ in prepared)
    try:
        source: Mapping[str, tuple[str, ...]] = (
            parse_dotenv(env_path, selected_keys) if selected_keys else {}
        )
    except ProtectedConfigError:
        failures.extend(
            failed(project.project_id, "无法读取注册仓库 URL 配置。", candidate)
            for project, candidate in prepared
        )
        return (), tuple(failures)
    configured: list[ProjectConfig] = []
    for project, candidate in prepared:
        values = source.get(project.repository_url_config_key, ())
        if len(values) != 1 or not values[0].strip():
            message = "注册仓库 URL 配置重复。" if len(values) > 1 else "缺少注册仓库 URL 配置。"
            failures.append(failed(project.project_id, message, candidate))
            continue
        try:
            _ = url_identity(values[0])
        except SafetyError:
            failures.append(failed(project.project_id, "注册仓库 URL 配置无效。", candidate))
            continue
        configured.append(ProjectConfig(
            project.project_id, candidate.local_path, values[0], project.default_branch,
            project.repository_url_config_key,
        )
        )
    return tuple(configured), tuple(failures)


def checked_commit(project: ProjectConfig, empty_hooks_path: Path) -> str:
    commit = run_git(CommandSpec(("rev-parse", "HEAD"), project.local_path), empty_hooks_path)
    if not COMMIT_PATTERN.fullmatch(commit):
        raise GitFailure("仓库提交标识无效，未报告成功。")
    return commit


def _checked_repository(project: ProjectConfig, code_root: Path, empty_hooks_path: Path) -> None:
    _ = validate_safe_descendant(code_root, project.local_path, allow_missing=False)
    reject_unsafe_git_config(project.local_path)
    root_output = run_git(
        CommandSpec(("rev-parse", "--show-toplevel"), project.local_path), empty_hooks_path
    )
    if Path(root_output).resolve() != project.local_path:
        raise GitFailure("本地仓库根目录与注册路径不一致。")


def _success(project: ProjectConfig, commit: str, message: str) -> ResultJson:
    return ResultJson(
        project_id=project.project_id,
        status=Status.SUCCESS,
        local_path=str(project.local_path),
        default_branch=project.default_branch,
        repository_url_config_key=project.repository_url_config_key,
        commit=commit,
        message=message,
    )


def synchronize(project: ProjectConfig, code_root: Path, empty_hooks_path: Path) -> ResultJson:
    try:
        _ = validate_safe_descendant(code_root, project.local_path, allow_missing=True)
        if not project.local_path.exists():
            _ = prepare_safe_parent(code_root, project.local_path)
            _ = validate_safe_descendant(code_root, project.local_path, allow_missing=True)
            arguments = (
                "clone", "--origin", REMOTE_NAME, "--branch", project.default_branch,
                "--single-branch", "--", project.url, str(project.local_path),
            )
            _ = run_git(CommandSpec(arguments, project.local_path.parent, (project.url,)), empty_hooks_path)
            _checked_repository(project, code_root, empty_hooks_path)
            return _success(project, checked_commit(project, empty_hooks_path), "仓库已安全克隆。")
        _checked_repository(project, code_root, empty_hooks_path)
        if run_git(CommandSpec(("status", "--porcelain=v1"), project.local_path), empty_hooks_path):
            raise GitFailure("工作区存在未提交变更，已拒绝同步。")
        branch = run_git(CommandSpec(("branch", "--show-current"), project.local_path), empty_hooks_path)
        if branch != project.default_branch:
            raise GitFailure("当前分支与注册分支不一致。")
        actual_url = run_git(CommandSpec(("remote", "get-url", REMOTE_NAME), project.local_path), empty_hooks_path)
        if url_identity(actual_url) != url_identity(project.url):
            raise GitFailure("仓库 origin 地址与注册配置不一致。")
        previous = checked_commit(project, empty_hooks_path)
        _ = run_git(CommandSpec(("fetch", "--prune", REMOTE_NAME), project.local_path), empty_hooks_path)
        remote_ref = f"refs/remotes/{REMOTE_NAME}/{project.default_branch}"
        counts = run_git(
            CommandSpec(("rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"), project.local_path),
            empty_hooks_path,
        ).split()
        if len(counts) != 2 or not all(value.isdecimal() for value in counts):
            raise GitFailure("无法可靠判断仓库是否可仅快进同步。")
        if int(counts[0]) != 0:
            raise GitFailure("本地历史无法仅快进同步，已拒绝更新。")
        pull = CommandSpec(("pull", "--ff-only", REMOTE_NAME, project.default_branch), project.local_path)
        _ = run_git(pull, empty_hooks_path)
        commit = checked_commit(project, empty_hooks_path)
        message = "仓库已仅快进同步。" if previous != commit else "仓库已是最新状态。"
        return _success(project, commit, message)
    except (GitFailure, SafetyError, OSError, ValueError):
        return failed(project.project_id, "本地仓库同步未安全完成。", project)


def emit(results: tuple[ResultJson, ...]) -> None:
    print(json.dumps(results, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    try:
        expected_sha256, requested, show_help = parse_arguments(tuple(sys.argv[1:]))
        if show_help:
            print("用法：python tools/sync_repositories.py [--registry-sha256 <摘要>] [--project <项目 ID>]...\n安全同步注册表中的项目。")
            return ExitCode.SUCCESS
        registry = load_project_registry(REPOSITORY_ROOT / "project-registry.yaml")
        if expected_sha256 is not None and registry.sha256 != expected_sha256:
            raise ConfigError("注册表快照已变化，已拒绝同步。")
        if requested is None:
            safe_requested: tuple[str, ...] | None = None
            unsafe_count = 0
        else:
            safe_requested = tuple(item for item in requested if PROJECT_ID_PATTERN.fullmatch(item))
            unsafe_count = len(requested) - len(safe_requested)
        selection = select_projects(registry, safe_requested) if safe_requested or requested is None else None
        selected = () if selection is None else selection.projects
        failures: list[ResultJson] = [] if requested is not None else [
            failed(
                item.project_id
                if item.project_id is not None and PROJECT_ID_PATTERN.fullmatch(item.project_id)
                else "*",
                "注册项目配置无效。",
            )
            for item in registry.invalid_projects
        ]
        failures.extend(failed("*", "项目选择格式无效。") for _ in range(unsafe_count))
        if selection is not None:
            failures.extend(
                failed(
                    item.project_id if item.project_id and PROJECT_ID_PATTERN.fullmatch(item.project_id) else "*",
                    "项目未注册、已禁用或配置无效。",
                )
                for item in selection.diagnostics
            )
        configured, config_failures = load_config(REPOSITORY_ROOT / ".env", selected) if selected else ((), ())
        failures.extend(config_failures)
        with TemporaryDirectory(prefix="review-git-hooks-") as empty_hooks:
            code_root = REPOSITORY_ROOT / "data" / "code"
            synced = tuple(synchronize(item, code_root, Path(empty_hooks)) for item in configured)
        results = (*failures, *synced)
        if not results:
            results = (failed("*", "无可同步项目"),)
        emit(tuple(results))
        successes = sum(result["status"] == Status.SUCCESS for result in results)
        if successes == len(results):
            return ExitCode.SUCCESS
        return ExitCode.PARTIAL_SUCCESS if successes else ExitCode.OPERATION_FAILURE
    except (ArgumentError, ConfigError, RegistryError, SafetyError):
        emit((failed("*", "全局注册表或同步配置无效。"),))
        return ExitCode.CONFIGURATION_FAILURE
    except OSError:
        emit((failed("*", "全局路径或临时安全目录无法使用。"),))
        return ExitCode.CONFIGURATION_FAILURE
    except KeyboardInterrupt:
        emit((failed("*", "同步已被中断，未报告成功。"),))
        return ExitCode.OPERATION_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
