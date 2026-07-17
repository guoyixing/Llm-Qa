from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

from tools.repository_config import RepositoryCredentials


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
    url: str = field(repr=False)
    default_branch: str
    repository_url_config_key: str
    credentials: RepositoryCredentials | None = field(default=None, repr=False)


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
