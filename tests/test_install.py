from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.sh"
PACKAGE = "danangjoyoo/nerd"


class InstallScriptTests(unittest.TestCase):
    def _run(self, target: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            log = temp / "npx.log"
            fake_npx = temp / "npx"
            fake_npx.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$NERD_INSTALL_LOG\"\n",
                encoding="utf-8",
            )
            fake_npx.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{temp}{os.pathsep}{env['PATH']}"
            env["NERD_INSTALL_LOG"] = str(log)
            result = subprocess.run(
                ["sh", str(INSTALLER), target],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            arguments = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
            return result, arguments

    def test_installs_all_skills_for_each_named_client(self):
        for target, agent in (
            ("claude", "claude-code"),
            ("codex", "codex"),
            ("cursor", "cursor"),
        ):
            with self.subTest(target=target):
                result, arguments = self._run(target)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    arguments,
                    [
                        "skills",
                        "add",
                        PACKAGE,
                        "--global",
                        "--agent",
                        agent,
                        "--skill",
                        "*",
                        "--yes",
                    ],
                )

    def test_all_installs_to_the_three_supported_clients(self):
        result, arguments = self._run("all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            arguments,
            [
                "skills",
                "add",
                PACKAGE,
                "--global",
                "--agent",
                "claude-code",
                "codex",
                "cursor",
                "--skill",
                "*",
                "--yes",
            ],
        )

    def test_unknown_client_fails_without_running_npx(self):
        result, arguments = self._run("unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", result.stderr.casefold())
        self.assertEqual(arguments, [])


if __name__ == "__main__":
    unittest.main()
