from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ROOT / ".opencode" / "commands" / "sync-repositories.md",
    ROOT / ".opencode" / "commands" / "daily-review.md",
    ROOT / ".opencode" / "commands" / "code-review.md",
)
RESULT_FIELDS = (
    "project_id",
    "status",
    "local_path",
    "default_branch",
    "repository_url_config_key",
    "commit",
    "message",
)


class CommandContractTests(unittest.TestCase):
    def test_all_commands_use_root_registry_without_fixed_projects(self) -> None:
        for path in COMMANDS:
            content = path.read_text(encoding="utf-8")
            self.assertIn("project-registry.yaml", content, path.name)
            self.assertNotIn("project=api", content, path.name)
            self.assertNotIn("project=web", content, path.name)
            self.assertNotIn("project=jobs", content, path.name)
            self.assertNotIn("data/code/api", content, path.name)
            self.assertNotIn("data/code/web", content, path.name)
            self.assertNotIn("data/code/jobs", content, path.name)

    def test_sync_commands_define_all_result_fields(self) -> None:
        for name in ("sync-repositories.md", "daily-review.md"):
            content = (ROOT / ".opencode" / "commands" / name).read_text(
                encoding="utf-8"
            )
            for field in RESULT_FIELDS:
                self.assertIn(f"`{field}`", content, name)
            self.assertIn("success", content, name)
            self.assertIn("failed", content, name)

    def test_daily_review_requires_one_bound_sync_invocation(self) -> None:
        content = (ROOT / ".opencode" / "commands" / "daily-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("只调用一次", content)
        self.assertIn("python tools/registry_snapshot.py", content)
        self.assertIn("--registry-sha256", content)
        self.assertIn("同一注册表快照", content)
        self.assertIn("额外", content)

    def test_manual_review_forbids_synchronization(self) -> None:
        content = (ROOT / ".opencode" / "commands" / "code-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不得调用同步脚本或同步命令", content)
        self.assertIn("不得声称工作区已同步或是远端最新", content)


if __name__ == "__main__":
    unittest.main()
