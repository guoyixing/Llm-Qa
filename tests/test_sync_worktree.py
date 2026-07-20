from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tools.sync_models import Status
from tools.sync_repositories import ProjectConfig, synchronize

GIT_EXECUTABLE = shutil.which("git")


@unittest.skipUnless(GIT_EXECUTABLE is not None, "Git 不可用")
class SyncWorktreeIntegrationTests(unittest.TestCase):
    def run_setup_git(
        self,
        working_directory: Path,
        *arguments: str,
        environment: dict[str, str] | None = None,
    ) -> None:
        executable = GIT_EXECUTABLE
        if executable is None:
            self.fail("Git 不可用")
        subprocess.run(
            [executable, *arguments],
            cwd=working_directory,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

    def available_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        return port

    def test_synchronizes_real_linked_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary).resolve()
            code_root = temporary_root / "data" / "code"
            code_root.mkdir(parents=True)
            remote = temporary_root / "remote.git"
            primary = code_root / "primary"
            linked = code_root / "linked"
            hooks = temporary_root / "hooks"
            hooks.mkdir()
            allowed_environment = (
                "PATH",
                "SYSTEMROOT",
                "TEMP",
                "TMP",
                "HOMEDRIVE",
                "HOMEPATH",
            )
            setup_environment = {
                key: value
                for key in allowed_environment
                if (value := os.environ.get(key)) is not None
            }
            setup_environment.update({
                "GIT_CONFIG_NOSYSTEM": "1",
                "HOME": str(hooks),
                "USERPROFILE": str(hooks),
                "XDG_CONFIG_HOME": str(hooks),
            })

            self.run_setup_git(
                temporary_root,
                "init",
                "--bare",
                "--initial-branch=main",
                str(remote),
                environment=setup_environment,
            )

            self.run_setup_git(
                code_root,
                "init",
                "--initial-branch=main",
                str(primary),
                environment=setup_environment,
            )
            (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            self.run_setup_git(
                primary,
                "add",
                "tracked.txt",
                environment=setup_environment,
            )
            commit_environment = {
                **setup_environment,
                "GIT_AUTHOR_NAME": "Sync Test",
                "GIT_AUTHOR_EMAIL": "sync@example.invalid",
                "GIT_COMMITTER_NAME": "Sync Test",
                "GIT_COMMITTER_EMAIL": "sync@example.invalid",
            }
            self.run_setup_git(
                primary,
                "commit",
                "-m",
                "initial",
                environment=commit_environment,
            )
            self.run_setup_git(
                primary,
                "branch",
                "linked",
                environment=setup_environment,
            )
            self.run_setup_git(
                primary,
                "push",
                str(remote),
                "main",
                "linked",
                environment=setup_environment,
            )
            self.run_setup_git(
                primary,
                "worktree",
                "add",
                str(linked),
                "linked",
                environment=setup_environment,
            )

            port = self.available_port()
            repository_url = f"git://127.0.0.1:{port}/remote.git"
            self.run_setup_git(
                primary,
                "remote",
                "add",
                "origin",
                repository_url,
                environment=setup_environment,
            )
            (linked / "tracked.txt").write_text("updated\n", encoding="utf-8")
            self.run_setup_git(
                linked,
                "add",
                "tracked.txt",
                environment=setup_environment,
            )
            self.run_setup_git(
                linked,
                "commit",
                "-m",
                "update",
                environment=commit_environment,
            )
            self.run_setup_git(
                linked,
                "push",
                str(remote),
                "linked",
                environment=setup_environment,
            )
            self.run_setup_git(
                linked,
                "reset",
                "--hard",
                "HEAD^",
                environment=setup_environment,
            )

            project = ProjectConfig(
                "example-service",
                linked,
                repository_url,
                "linked",
                "PROJECT_EXAMPLE_SERVICE_REPO_URL",
            )

            executable = GIT_EXECUTABLE
            if executable is None:
                self.fail("Git 不可用")
            daemon = subprocess.Popen(
                [
                    executable,
                    "daemon",
                    "--reuseaddr",
                    "--export-all",
                    "--listen=127.0.0.1",
                    f"--port={port}",
                    f"--base-path={temporary_root}",
                    str(temporary_root),
                ],
                cwd=Path.cwd(),
                env=setup_environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                deadline = time.monotonic() + 5
                while True:
                    if daemon.poll() is not None:
                        self.fail("本地 Git 服务启动失败")
                    try:
                        with socket.create_connection(
                            ("127.0.0.1", port), timeout=0.1
                        ):
                            break
                    except OSError:
                        if time.monotonic() >= deadline:
                            self.fail("本地 Git 服务未在限定时间内就绪")
                        try:
                            daemon.wait(timeout=0.05)
                        except subprocess.TimeoutExpired:
                            continue
                        self.fail("本地 Git 服务启动失败")
                result = synchronize(project, code_root, hooks)
                synchronized_content = (linked / "tracked.txt").read_text(
                    encoding="utf-8"
                )
            finally:
                daemon.terminate()
                try:
                    daemon.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    daemon.kill()
                    daemon.wait(timeout=5)

        self.assertEqual(result["status"], Status.SUCCESS, result)
        self.assertEqual(result["message"], "仓库已仅快进同步。")
        self.assertEqual(synchronized_content, "updated\n")
        self.assertRegex(result["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            set(result),
            {
                "project_id",
                "status",
                "local_path",
                "default_branch",
                "repository_url_config_key",
                "commit",
                "message",
            },
        )


if __name__ == "__main__":
    unittest.main()
