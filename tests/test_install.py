from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.sh"
HOOK = ROOT / "skills" / "nerd-smart" / "scripts" / "prompt_hook.py"
PACKAGE = "danangjoyoo/nerd"


class InstallScriptTests(unittest.TestCase):
    def _run(
        self,
        target: str,
        *,
        runs: int = 1,
        initial_files: dict[str, str] | None = None,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_home = temp / "home"
            fake_home.mkdir()
            log = temp / "npx.log"
            fake_npx = temp / "npx"
            fake_npx.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$NERD_INSTALL_LOG\"\n",
                encoding="utf-8",
            )
            fake_npx.chmod(0o755)
            fake_agent = temp / "agent-cli"
            fake_agent.write_text(
                "#!/bin/sh\n"
                "if [ \"$1 $2\" = \"mcp get\" ]; then exit 1; fi\n"
                "if [ \"$1 $2 $3\" = \"agent mcp list\" ]; then exit 0; fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_agent.chmod(0o755)
            for name in ("codex", "claude", "cursor"):
                (temp / name).symlink_to(fake_agent)
            for relative, body in (initial_files or {}).items():
                path = fake_home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")

            env = os.environ.copy()
            env["PATH"] = f"{temp}{os.pathsep}{env['PATH']}"
            env["NERD_INSTALL_LOG"] = str(log)
            env["NERD_INSTALL_HOME"] = str(fake_home)
            results = []
            for _ in range(runs):
                results.append(
                    subprocess.run(
                        ["sh", str(INSTALLER), target],
                        cwd=ROOT,
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                )

            arguments = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
            files = {
                path.relative_to(fake_home).as_posix(): path.read_text(encoding="utf-8")
                for path in fake_home.rglob("*")
                if path.is_file()
            }
            return results, arguments, files

    def test_installs_all_skills_for_each_named_client(self):
        for target, agent in (
            ("claude", "claude-code"),
            ("codex", "codex"),
            ("cursor", "cursor"),
        ):
            with self.subTest(target=target):
                results, arguments, _ = self._run(target)
                self.assertEqual(results[0].returncode, 0, results[0].stderr)
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
        results, arguments, _ = self._run("all")
        self.assertEqual(results[0].returncode, 0, results[0].stderr)
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

    def test_each_client_receives_a_native_smart_hook(self):
        cases = (
            ("claude", ".claude/settings.json", "UserPromptSubmit", "claude-code"),
            ("codex", ".codex/hooks.json", "UserPromptSubmit", "codex"),
            ("cursor", ".cursor/hooks.json", "sessionStart", "cursor"),
        )
        for target, config_path, event, agent in cases:
            with self.subTest(target=target):
                results, _, files = self._run(target)
                self.assertEqual(results[0].returncode, 0, results[0].stderr)
                config = json.loads(files[config_path])
                entries = config["hooks"][event]
                handler = entries[0] if agent == "cursor" else entries[0]["hooks"][0]
                self.assertIn("prompt_hook.py", handler["command"])
                self.assertIn(f"--agent {agent}", handler["command"])
                self.assertIn(".nerd/hooks/prompt_hook.py", files)

    def test_all_configures_every_supported_client(self):
        results, _, files = self._run("all")
        self.assertEqual(results[0].returncode, 0, results[0].stderr)
        self.assertIn(".claude/settings.json", files)
        self.assertIn(".codex/hooks.json", files)
        self.assertIn(".cursor/hooks.json", files)

    def test_install_does_not_register_archived_ufast_tools(self):
        results, _, files = self._run("all")
        self.assertEqual(results[0].returncode, 0, results[0].stderr)
        self.assertFalse(any(path.startswith(".nerd/mcp/") for path in files))

    def test_reinstall_is_idempotent_and_preserves_existing_hooks(self):
        existing = json.dumps(
            {
                "description": "keep me",
                "hooks": {
                    "Stop": [
                        {
                            "hooks": [
                                {"type": "command", "command": "existing-hook"}
                            ]
                        }
                    ]
                },
            }
        )
        results, _, files = self._run(
            "codex",
            runs=2,
            initial_files={".codex/hooks.json": existing},
        )
        self.assertTrue(all(result.returncode == 0 for result in results))
        config = json.loads(files[".codex/hooks.json"])
        self.assertEqual(config["description"], "keep me")
        self.assertEqual(config["hooks"]["Stop"][0]["hooks"][0]["command"], "existing-hook")
        self.assertEqual(len(config["hooks"]["UserPromptSubmit"]), 1)

    def test_prompt_hook_emits_agent_specific_context(self):
        for agent, event, context_path in (
            (
                "claude-code",
                "UserPromptSubmit",
                ("hookSpecificOutput", "additionalContext"),
            ),
            (
                "codex",
                "UserPromptSubmit",
                ("hookSpecificOutput", "additionalContext"),
            ),
            ("cursor", "sessionStart", ("additional_context",)),
        ):
            with self.subTest(agent=agent):
                result = subprocess.run(
                    ["python3", str(HOOK), "--agent", agent],
                    input=json.dumps({"hook_event_name": event}),
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                context = payload
                for key in context_path:
                    context = context[key]
                self.assertIn("Always invoke", context)
                self.assertIn("nerd-smart", context)
                self.assertIn("No hook authorizes combining Nerd", context)
                for incompatible in ("Superpowers", "Ponytail", "Caveman"):
                    self.assertIn(incompatible, context)
                self.assertIn("only an explicit user request", context)

    def test_unknown_client_fails_without_running_npx(self):
        results, arguments, files = self._run("unknown")
        self.assertNotEqual(results[0].returncode, 0)
        self.assertIn("usage:", results[0].stderr.casefold())
        self.assertEqual(arguments, [])
        self.assertEqual(files, {})


if __name__ == "__main__":
    unittest.main()
