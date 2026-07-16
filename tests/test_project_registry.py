from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.project_registry import (
    RegistryError,
    RegistryErrorCode,
    SelectionCode,
    load_project_registry,
    select_projects,
)
from tools.registry_yaml import ParsedRegistry, parse_registry_yaml
from tools.registry_snapshot import main as snapshot_main, snapshot_json


def project_block(
    project_id: str = "alpha",
    code_dir: str = "data/code/alpha",
    standards_dir: str = "standards/projects/alpha",
    url_key: str = "PROJECT_ALPHA_REPO_URL",
    enabled: str = "true",
) -> str:
    return (
        f"  - project_id: {project_id}\n"
        "    name: Alpha Project\n"
        f"    code_dir: {code_dir}\n"
        f"    standards_dir: {standards_dir}\n"
        "    default_branch: main\n"
        f"    repository_url_config_key: {url_key}\n"
        f"    enabled: {enabled}\n"
    )


def registry_text(*projects: str) -> str:
    return "# registry\nversion: 1\nprojects:\n" + "".join(projects)


class RegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.path = self.root / "project-registry.yaml"

    def write(self, text: str) -> Path:
        self.path.write_text(text, encoding="utf-8")
        return self.path

    def assert_global(self, text: str, code: RegistryErrorCode) -> None:
        with self.assertRaises(RegistryError) as raised:
            load_project_registry(self.write(text))
        self.assertEqual(raised.exception.code, code)

    def test_loads_valid_plain_and_json_strings(self) -> None:
        text = registry_text(project_block().replace("name: Alpha Project", 'name: "项目 Alpha"'))

        result = load_project_registry(self.write(text))

        self.assertEqual(result.version, 1)
        self.assertEqual(result.projects[0].name, "项目 Alpha")
        self.assertEqual(result.invalid_projects, ())

    def test_load_reads_exact_bytes_once_and_returns_lowercase_sha256(self) -> None:
        text = registry_text(project_block())
        self.write(text)
        original_read = Path.read_bytes
        reads = 0

        def counted_read(path: Path) -> bytes:
            nonlocal reads
            reads += 1
            return original_read(path)

        with patch.object(Path, "read_bytes", counted_read):
            result = load_project_registry(self.path)

        self.assertEqual(reads, 1)
        self.assertEqual(result.sha256, hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertRegex(result.sha256, r"^[0-9a-f]{64}$")

    def test_digest_changes_when_only_comment_bytes_change(self) -> None:
        first = load_project_registry(self.write(registry_text(project_block())))
        second = load_project_registry(self.write(registry_text(project_block()) + "# changed\n"))

        self.assertNotEqual(first.sha256, second.sha256)
        self.assertEqual(first.projects, second.projects)

    def test_missing_file_and_invalid_utf8_are_global(self) -> None:
        with self.assertRaises(RegistryError) as missing:
            load_project_registry(self.path)
        self.path.write_bytes(b"version: \xff")

        with self.assertRaises(RegistryError) as invalid:
            load_project_registry(self.path)

        self.assertEqual(missing.exception.code, RegistryErrorCode.READ_FAILED)
        self.assertEqual(invalid.exception.code, RegistryErrorCode.INVALID_ENCODING)

    def test_rejects_unsafe_yaml_syntax_globally(self) -> None:
        cases = (
            "\tversion: 1\nprojects:\n",
            "%YAML 1.2\nversion: 1\nprojects:\n",
            "---\nversion: 1\nprojects:\n",
            "version: &v 1\nprojects:\n",
            "version: *v\nprojects:\n",
            "version: !int 1\nprojects:\n",
            "version: [1]\nprojects:\n",
            "version: |\nprojects:\n",
            "version: '1'\nprojects:\n",
            "version: 1 # comment\nprojects:\n",
            "version:\nprojects:\n",
            "version: 1\nprojects:\n   - project_id: alpha\n",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assert_global(text, RegistryErrorCode.UNSAFE_SYNTAX)

    def test_rejects_duplicate_mapping_keys(self) -> None:
        self.assert_global("version: 1\nversion: 1\nprojects:\n", RegistryErrorCode.INVALID_TOP_LEVEL)
        duplicated = project_block().replace("    name:", "    project_id: beta\n    name:")
        self.assert_global(registry_text(duplicated), RegistryErrorCode.UNSAFE_SYNTAX)

    def test_rejects_invalid_top_level_version_and_projects_type(self) -> None:
        self.assert_global("version: 1\nprojects:\nextra: value\n", RegistryErrorCode.INVALID_TOP_LEVEL)
        self.assert_global("version: \"1\"\nprojects:\n", RegistryErrorCode.INVALID_VERSION)
        self.assert_global("version: 2\nprojects:\n", RegistryErrorCode.INVALID_VERSION)
        self.assert_global("version: 1\nprojects: false\n", RegistryErrorCode.INVALID_PROJECTS)

    def test_global_and_entry_diagnostics_do_not_reflect_unsafe_source(self) -> None:
        secret = "SECRET_TOKEN=do-not-reflect"
        with self.assertRaises(RegistryError) as raised:
            load_project_registry(self.write(f'version: "{secret}"\nprojects:\n'))
        invalid = project_block(code_dir=f'"data/code/../{secret}"')

        result = load_project_registry(self.write(registry_text(invalid)))

        self.assertNotIn(secret, str(raised.exception))
        self.assertNotIn(secret, " ".join(result.invalid_projects[0].errors))

    def test_duplicate_project_id_is_global_even_when_entries_are_invalid(self) -> None:
        duplicate = project_block() + project_block(code_dir="bad", standards_dir="bad", url_key="BAD")

        self.assert_global(registry_text(duplicate), RegistryErrorCode.DUPLICATE_PROJECT_ID)

    def test_entry_field_errors_do_not_block_valid_entries(self) -> None:
        invalid = project_block(project_id="bad-id").replace("    name: Alpha Project\n", "    mystery: value\n")
        valid = project_block("beta", "data/code/beta", "standards/projects/beta", "PROJECT_BETA_REPO_URL")

        result = load_project_registry(self.write(registry_text(invalid, valid)))

        self.assertEqual(tuple(project.project_id for project in result.projects), ("beta",))
        self.assertEqual(result.invalid_projects[0].project_id, "bad-id")
        self.assertGreaterEqual(len(result.invalid_projects[0].errors), 2)

    def test_wrong_field_types_are_entry_errors(self) -> None:
        wrong = project_block(enabled="1").replace("name: Alpha Project", "name: true")

        result = load_project_registry(self.write(registry_text(wrong)))

        self.assertEqual(result.projects, ())
        self.assertTrue(any("name" in error for error in result.invalid_projects[0].errors))
        self.assertTrue(any("enabled" in error for error in result.invalid_projects[0].errors))

    def test_validates_project_id_and_url_namespace_boundaries(self) -> None:
        cases = (
            project_block(project_id="A"),
            project_block(project_id="a" * 65),
            project_block(url_key="NON_PROJECT_REPO_URL"),
            project_block(url_key=f"PROJECT_{'A' * 112}_REPO_URL"),
        )
        for block in cases:
            with self.subTest(block=block):
                result = load_project_registry(self.write(registry_text(block)))
                self.assertEqual(result.projects, ())

    def test_validates_narrow_branch_contract(self) -> None:
        invalid_branches = ("-main", ".main", "feature//x", "feature/../x", "feature/@{x", "feature\\x", "feature/.x", "x.", "x/", "x.lock", "x lock", "x;whoami")
        for branch in invalid_branches:
            with self.subTest(branch=branch):
                block = project_block().replace("default_branch: main", f'default_branch: "{branch.replace(chr(92), chr(92) * 2)}"')
                result = load_project_registry(self.write(registry_text(block)))
                self.assertEqual(result.projects, ())

    def test_rejects_unsafe_paths_and_accepts_strict_descendants(self) -> None:
        paths = ("data/code", "/data/code/x", "C:/data/code/x", "data\\code\\x", "data/code/./x", "data/code/../x", "data/code//x", "other/code/x")
        for unsafe in paths:
            with self.subTest(path=unsafe):
                result = load_project_registry(self.write(registry_text(project_block(code_dir=unsafe))))
                self.assertEqual(result.projects, ())

    def test_path_roots_are_exact_case_sensitive_entry_rules(self) -> None:
        wrong_code = project_block(code_dir="DATA/CODE/alpha")
        wrong_standards = project_block(standards_dir="STANDARDS/PROJECTS/alpha")
        for block in (wrong_code, wrong_standards):
            with self.subTest(block=block):
                result = load_project_registry(self.write(registry_text(block)))
                self.assertEqual(result.projects, ())
                self.assertEqual(result.invalid_projects[0].project_id, "alpha")

    def test_rejects_existing_symbolic_link_ancestor(self) -> None:
        target = self.root / "outside"
        target.mkdir()
        (self.root / "data").mkdir()
        try:
            (self.root / "data" / "code").symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("当前平台不允许创建测试符号链接")

        result = load_project_registry(self.write(registry_text(project_block())))

        self.assertEqual(result.projects, ())
        self.assertIn("符号链接", result.invalid_projects[0].errors[0])

    def test_invalidates_all_equal_and_nested_path_collisions_case_insensitively(self) -> None:
        alpha = project_block()
        beta = project_block("beta", "data/code/ALPHA/child", "standards/projects/beta", "PROJECT_BETA_REPO_URL")

        result = load_project_registry(self.write(registry_text(alpha, beta)))

        self.assertEqual(result.projects, ())
        self.assertEqual({entry.project_id for entry in result.invalid_projects}, {"alpha", "beta"})

    def test_code_and_standards_collisions_are_independent(self) -> None:
        alpha = project_block()
        beta = project_block("beta", "data/code/beta", "standards/projects/alpha", "PROJECT_BETA_REPO_URL")
        gamma = project_block("gamma", "data/code/gamma", "standards/projects/gamma", "PROJECT_GAMMA_REPO_URL")

        result = load_project_registry(self.write(registry_text(alpha, beta, gamma)))

        self.assertEqual(tuple(project.project_id for project in result.projects), ("gamma",))
        self.assertEqual(len(result.invalid_projects), 2)

    def test_duplicate_url_key_invalidates_every_member(self) -> None:
        beta = project_block("beta", "data/code/beta", "standards/projects/beta", "PROJECT_ALPHA_REPO_URL")

        result = load_project_registry(self.write(registry_text(project_block(), beta)))

        self.assertEqual(result.projects, ())
        self.assertEqual(len(result.invalid_projects), 2)

    def test_default_selection_preserves_order_and_silently_skips_disabled(self) -> None:
        disabled = project_block("beta", "data/code/beta", "standards/projects/beta", "PROJECT_BETA_REPO_URL", "false")
        registry = load_project_registry(self.write(registry_text(project_block(), disabled)))

        selection = select_projects(registry)

        self.assertEqual(tuple(project.project_id for project in selection.projects), ("alpha",))
        self.assertEqual(selection.diagnostics, ())

    def test_explicit_selection_deduplicates_and_reports_each_skip_kind(self) -> None:
        disabled = project_block("beta", "data/code/beta", "standards/projects/beta", "PROJECT_BETA_REPO_URL", "false")
        invalid = project_block("broken", "bad", "standards/projects/broken", "PROJECT_BROKEN_REPO_URL")
        registry = load_project_registry(self.write(registry_text(project_block(), disabled, invalid)))

        selection = select_projects(registry, ("alpha", "alpha", "beta", "broken", "missing", "bad;SECRET_TOKEN=raw"))

        self.assertEqual(tuple(project.project_id for project in selection.projects), ("alpha",))
        self.assertEqual(tuple(item.code for item in selection.diagnostics), (SelectionCode.DISABLED_ID, SelectionCode.INVALID_ID, SelectionCode.UNKNOWN_ID, SelectionCode.UNSAFE_ID))
        rendered = " ".join(item.message for item in selection.diagnostics)
        self.assertNotIn("SECRET_TOKEN", rendered)
        self.assertNotIn("bad;", rendered)
        self.assertIsNone(selection.diagnostics[-1].project_id)

    def test_results_are_immutable(self) -> None:
        registry = load_project_registry(self.write(registry_text(project_block())))

        with self.assertRaises(FrozenInstanceError):
            setattr(registry, "version", 2)

    def test_yaml_parser_output_is_typed_and_immutable(self) -> None:
        parsed = parse_registry_yaml(registry_text(project_block()))

        self.assertIsInstance(parsed, ParsedRegistry)
        self.assertIsInstance(parsed.projects, tuple)
        self.assertIsInstance(parsed.projects[0].values, tuple)
        with self.assertRaises(FrozenInstanceError):
            setattr(parsed, "version", 2)

    def test_snapshot_json_has_only_trusted_fields_and_no_source_secret(self) -> None:
        secret = "SECRET_TOKEN=do-not-serialize"
        valid = project_block()
        invalid = project_block(
            "broken",
            f'"data/code/../{secret}"',
            "standards/projects/broken",
            "PROJECT_BROKEN_REPO_URL",
        )
        registry = load_project_registry(self.write(registry_text(valid, invalid)))

        rendered = snapshot_json(registry)
        payload = json.loads(rendered)

        self.assertEqual(set(payload), {"version", "sha256", "projects", "invalid_projects"})
        self.assertEqual(
            set(payload["projects"][0]),
            {"project_id", "name", "code_dir", "standards_dir", "default_branch", "repository_url_config_key", "enabled"},
        )
        self.assertEqual(set(payload["invalid_projects"][0]), {"project_id", "errors"})
        self.assertNotIn(secret, rendered)
        self.assertNotIn("http", rendered.lower())
        self.assertNotIn(": ", rendered)

    def test_snapshot_cli_rejects_arguments_with_fixed_json(self) -> None:
        output = io.StringIO()

        with patch("sys.stdout", output):
            exit_code = snapshot_main(("unexpected",))

        self.assertEqual(exit_code, 2)
        self.assertEqual(output.getvalue(), '{"error":"项目注册表加载失败"}\n')

    def test_repository_sample_is_valid_and_disabled(self) -> None:
        root = Path(__file__).resolve().parents[1]

        registry = load_project_registry(root / "project-registry.yaml")

        self.assertEqual(len(registry.projects), 1)
        self.assertFalse(registry.projects[0].enabled)
        self.assertEqual(select_projects(registry).projects, ())
        self.assertTrue(registry.projects[0].repository_url_config_key.startswith("PROJECT_"))


if __name__ == "__main__":
    unittest.main()
