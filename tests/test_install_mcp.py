from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "docs" / "experiments" / "nerd-ufast" / "install_mcp.py"
SHARED_INSTALLER_PATH = ROOT / "scripts" / "install_mcp.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_installer():
    return _load_module("install_mcp", INSTALLER_PATH)


def _load_shared_installer():
    return _load_module("shared_install_mcp", SHARED_INSTALLER_PATH)


STUB_SERVER = '''#!/usr/bin/env python3
import json
import sys

TOOLS = json.loads({tools!r})

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    request = json.loads(line)
    method = request.get("method")
    if method == "initialize":
        result = {{
            "protocolVersion": "2025-06-18",
            "capabilities": {{"tools": {{}}}},
            "serverInfo": {{"name": "stub", "version": "0"}},
        }}
    elif method == "tools/list":
        result = {{"tools": [{{"name": name, "inputSchema": {{"type": "object"}}}} for name in TOOLS]}}
    else:
        continue
    sys.stdout.write(
        json.dumps({{"jsonrpc": "2.0", "id": request.get("id"), "result": result}}) + "\\n"
    )
    sys.stdout.flush()
'''


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


class SharedInstallMcpTests(unittest.TestCase):
    """Cover the generic, server-agnostic installer at scripts/install_mcp.py."""

    # Reuse the fake-CLI / temp-HOME harness from the UFast installer tests.
    _environment = InstallMcpTests._environment

    def _stub_source(self, root: Path, name: str, tools) -> Path:
        source = root / f"source-{name}"
        source.mkdir(parents=True, exist_ok=True)
        (source / "mcp_server.py").write_text(
            STUB_SERVER.format(tools=json.dumps(sorted(tools))), encoding="utf-8"
        )
        (source / "payload.py").write_text("VALUE = 1\n", encoding="utf-8")
        return source

    def _install(self, installer, root: Path, home: Path, environment, name: str, *,
                 tools=("alpha", "beta"), expected_tools=None, agents=("codex",)):
        return installer.install_server(
            agents,
            server_name=name,
            runtime_directory=Path(f".nerd/mcp/{name}"),
            source_directory=self._stub_source(root, name, tools),
            runtime_files=("mcp_server.py", "payload.py"),
            expected_tools=set(expected_tools if expected_tools is not None else tools),
            home=home,
            environment=environment,
        )

    def _state(self, home: Path):
        return json.loads(
            (home / ".nerd/mcp/registrations.json").read_text(encoding="utf-8")
        )

    def test_command_environment_preserves_explicit_codex_home(self):
        installer = _load_shared_installer()
        environment = {
            "NERD_INSTALL_HOME": "/tmp/nerd-home",
            "CODEX_HOME": "/tmp/custom-codex-home",
        }

        result = installer._command_environment(Path("/tmp/nerd-home"), environment)

        self.assertEqual(result["HOME"], "/tmp/nerd-home")
        self.assertEqual(result["CODEX_HOME"], "/tmp/custom-codex-home")

    def test_registers_two_servers_without_collision(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, _ = self._environment(temp)
            first = self._install(installer, temp, home, environment, "nerd-a")
            second = self._install(installer, temp, home, environment, "nerd-b")
            self.assertTrue((first / "mcp_server.py").is_file())
            self.assertTrue((second / "payload.py").is_file())
            state = self._state(home)
            self.assertEqual(set(state), {"nerd-a", "nerd-b"})
            self.assertEqual(set(state["nerd-a"]), {"codex"})
            self.assertEqual(set(state["nerd-b"]), {"codex"})

    def test_conflicting_foreign_registration_raises(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, _ = self._environment(temp, conflict=True)
            with self.assertRaisesRegex(RuntimeError, "conflicting MCP registration"):
                self._install(installer, temp, home, environment, "nerd-a")

    def test_reinstall_keeps_the_recorded_state_stable(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, _ = self._environment(temp)
            state_path = home / ".nerd" / "mcp" / "registrations.json"
            self._install(installer, temp, home, environment, "nerd-a")
            first = json.loads(state_path.read_text(encoding="utf-8"))
            self._install(installer, temp, home, environment, "nerd-a")
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), first)

    def test_reinstall_repairs_a_registration_removed_behind_the_state_file(self):
        """The state file must never be trusted as proof the agent still has it."""
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, log = self._environment(temp)
            self._install(installer, temp, home, environment, "nerd-a")
            first_adds = log.read_text(encoding="utf-8").count("mcp add")
            self._install(installer, temp, home, environment, "nerd-a")
            second_adds = log.read_text(encoding="utf-8").count("mcp add")

            # The stub CLI reports the registration as missing, so a second run
            # must re-add it rather than short-circuit on the state file.
            self.assertGreater(second_adds, first_adds)

    def test_a_missing_agent_cli_does_not_block_the_other_agents(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, _ = self._environment(temp)
            (temp / "codex").unlink()
            # Confine PATH to the stub directory so the removed CLI cannot
            # resolve to the real codex binary on this machine.
            environment["PATH"] = str(temp)

            with self.assertRaisesRegex(RuntimeError, "codex CLI is required"):
                self._install(
                    installer,
                    temp,
                    home,
                    environment,
                    "nerd-a",
                    agents=("codex", "claude-code"),
                )

            state = json.loads(
                (home / ".nerd" / "mcp" / "registrations.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("claude-code", state["nerd-a"])
            self.assertNotIn("codex", state["nerd-a"])

    def test_health_check_rejects_unexpected_tool_set(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, log = self._environment(temp)
            with self.assertRaisesRegex(RuntimeError, "unexpected tools"):
                self._install(
                    installer,
                    temp,
                    home,
                    environment,
                    "nerd-a",
                    tools=("alpha", "gamma"),
                    expected_tools={"alpha", "beta"},
                )
            self.assertFalse(log.exists())
            self.assertFalse((home / ".nerd/mcp/registrations.json").exists())

    def test_legacy_ufast_agents_key_is_preserved(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, _ = self._environment(temp)
            state_path = home / ".nerd/mcp/registrations.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            legacy = {"agents": {"codex": {"server": "/legacy/nerd-ufast/mcp_server.py"}}}
            state_path.write_text(json.dumps(legacy), encoding="utf-8")
            self._install(installer, temp, home, environment, "nerd-a")
            state = self._state(home)
            self.assertEqual(state["agents"], legacy["agents"])
            self.assertEqual(set(state), {"agents", "nerd-a"})

    def test_registers_current_interpreter_not_bare_python3(self):
        installer = _load_shared_installer()
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            home = temp / "home"
            home.mkdir()
            environment, log = self._environment(temp)
            runtime = self._install(
                installer,
                temp,
                home,
                environment,
                "nerd-a",
                agents=("claude-code", "codex", "cursor"),
            )
            server = runtime / "mcp_server.py"
            calls = log.read_text(encoding="utf-8")
            self.assertIn(f"codex|mcp add nerd-a -- {sys.executable} {server}", calls)
            self.assertIn(
                f"claude|mcp add --scope user nerd-a -- {sys.executable} {server}", calls
            )
            self.assertIn(f'"command":"{sys.executable}"', calls)
            self.assertNotIn("-- python3 ", calls)
            state = self._state(home)
            self.assertEqual(
                state["nerd-a"]["codex"], {"server": str(server)}
            )


if __name__ == "__main__":
    unittest.main()
