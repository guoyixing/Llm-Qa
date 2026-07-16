from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import cast


ROOT = Path(__file__).resolve().parents[1]


class OpenCodePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
        config = cast(dict[str, object], raw)
        cls.permissions = cast(dict[str, object], config["permission"])

    def test_registry_has_exact_read_permission(self) -> None:
        read_rules = cast(dict[str, str], self.permissions["read"])
        self.assertEqual(read_rules["project-registry.yaml"], "allow")
        self.assertEqual(read_rules["opencode.json"], "allow")
        self.assertNotEqual(read_rules.get("*.yaml"), "allow")
        self.assertNotEqual(read_rules.get("**/*.yaml"), "allow")

    def test_secret_read_denials_remain(self) -> None:
        read_rules = cast(dict[str, str], self.permissions["read"])
        self.assertEqual(read_rules["*.env"], "deny")
        self.assertEqual(read_rules["*.env.*"], "deny")
        self.assertEqual(read_rules["**/.env"], "deny")
        self.assertEqual(read_rules["**/.env.*"], "deny")

    def test_sync_permission_is_dynamic_but_not_broad_python(self) -> None:
        bash_rules = cast(dict[str, str], self.permissions["bash"])
        self.assertEqual(bash_rules["python *"], "deny")
        self.assertEqual(bash_rules["python tools/registry_snapshot.py"], "allow")
        self.assertEqual(
            bash_rules["python tools/sync_repositories.py --registry-sha256 *"],
            "ask",
        )
        self.assertEqual(
            bash_rules["python tools/sync_repositories.py --project *"],
            "ask",
        )
        self.assertNotIn(
            "python tools/sync_repositories.py --project \"api\"",
            bash_rules,
        )


if __name__ == "__main__":
    unittest.main()
