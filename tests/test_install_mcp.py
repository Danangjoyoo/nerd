from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "docs" / "experiments" / "nerd-ufast" / "install_mcp.py"


def _load_installer():
    spec = importlib.util.spec_from_file_location("install_mcp", INSTALLER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InstallMcpTests(unittest.TestCase):
    def _environment(self, temp: Path, *, conflict: bool = False):
        log = temp / "agent.log"
        script = temp / "agent-cli"
        script.write_text(
            "#!/bin/sh\n"
            "printf '%s|%s\\n' \"$(basename \"$0\")\" \"$*\" >> \"$NERD_MCP_TEST_LOG\"\n"
            + (
                "if [ \"$1 $2\" = \"mcp get\" ]; then printf '%s\\n' '{\"command\":\"other-server\",\"args\":[]}'; exit 0; fi\n"
                if conflict
                else "if [ \"$1 $2\" = \"mcp get\" ]; then exit 1; fi\n"
            )
            + "if [ \"$1 $2 $3\" = \"agent mcp list\" ]; then exit 0; fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
        for name in ("codex", "claude", "cursor"):
            (temp / name).symlink_to(script)
        environment = os.environ.copy()
        environment["PATH"] = f"{temp}{os.pathsep}{environment['PATH']}"
        environment["NERD_MCP_TEST_LOG"] = str(log)
        return environment, log

    def test_installs_server_and_registers_all_agents(self):
        installer = _load_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, log = self._environment(temp)
            installed = installer.install(
                ("claude-code", "codex", "cursor"),
                home=home,
                environment=environment,
            )
            self.assertTrue((installed / "mcp_server.py").is_file())
            self.assertTrue((installed / "ufast_tools.py").is_file())
            calls = log.read_text(encoding="utf-8")
            self.assertIn("codex|mcp add nerd-ufast-tools -- python3", calls)
            self.assertIn("claude|mcp add --scope user nerd-ufast-tools -- python3", calls)
            self.assertIn("cursor|--add-mcp", calls)
            self.assertIn("cursor|agent mcp enable nerd-ufast-tools", calls)
            state = json.loads(
                (home / ".nerd/mcp/registrations.json").read_text(encoding="utf-8")
            )
            self.assertEqual(set(state["agents"]), {"claude-code", "codex", "cursor"})

    def test_reinstall_is_idempotent(self):
        installer = _load_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, log = self._environment(temp)
            installer.install(("codex",), home=home, environment=environment)
            first = log.read_text(encoding="utf-8")
            installer.install(("codex",), home=home, environment=environment)
            self.assertEqual(log.read_text(encoding="utf-8"), first)

    def test_conflicting_registration_blocks(self):
        installer = _load_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, _ = self._environment(temp, conflict=True)
            with self.assertRaisesRegex(RuntimeError, "conflicting MCP registration"):
                installer.install(("codex",), home=home, environment=environment)

    def test_missing_requested_cli_fails(self):
        installer = _load_installer()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            home.mkdir()
            environment = os.environ.copy()
            environment["PATH"] = "/nonexistent"
            with self.assertRaisesRegex(RuntimeError, "codex CLI is required"):
                installer.install(("codex",), home=home, environment=environment)


if __name__ == "__main__":
    unittest.main()
