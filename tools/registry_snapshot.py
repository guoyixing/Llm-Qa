"""输出供受信同步编排使用的不可变注册表快照。"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Sequence, TypeAlias

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.project_registry import ProjectRegistry, RegistryError, load_project_registry


JsonValue: TypeAlias = str | int | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
_FAILURE = '{"error":"项目注册表加载失败"}'


def snapshot_json(registry: ProjectRegistry) -> str:
    projects: list[JsonValue] = [
        {
            "project_id": project.project_id,
            "name": project.name,
            "code_dir": project.code_dir.as_posix(),
            "standards_dir": project.standards_dir.as_posix(),
            "default_branch": project.default_branch,
            "repository_url_config_key": project.repository_url_config_key,
            "enabled": project.enabled,
        }
        for project in registry.projects
    ]
    invalid_projects: list[JsonValue] = [
        {"project_id": project.project_id, "errors": list(project.errors)}
        for project in registry.invalid_projects
    ]
    payload: dict[str, JsonValue] = {
        "version": registry.version,
        "sha256": registry.sha256,
        "projects": projects,
        "invalid_projects": invalid_projects,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def main(arguments: Sequence[str] | None = None) -> int:
    _configure_stdout_utf8()
    requested = tuple(sys.argv[1:] if arguments is None else arguments)
    if requested:
        print(_FAILURE)
        return 2
    path = Path(__file__).resolve().parents[1] / "project-registry.yaml"
    try:
        print(snapshot_json(load_project_registry(path)))
    except (RegistryError, OSError):
        print(_FAILURE)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
