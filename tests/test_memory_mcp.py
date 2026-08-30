from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "nerd-memory" / "scripts"
SERVER = SCRIPTS / "mcp_server.py"
ENGINE = SCRIPTS / "memory.py"
INSTALL_MCP = ROOT / "scripts" / "install_mcp.py"

TOOL_NAMES = {"memory_recall", "memory_record", "memory_inspect"}
REMOVED_TERMS = (
    "namespace",
    "global_search",
    "proposal",
    "confirmation",
    "grant",
    "enablement",
    "memory_settle",
    "memory_learn",
    "memory_experience",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def episode(episode_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "episode_id": episode_id,
        "repository": "repo-alpha",
        "language": "python",
        "surface": "api",
        "project_kind": "service",
        "raw_input": "Please test the API",
        "action": "test",
        "tools": ["pytest"],
        "steps": ["inspect_tests", "run_pytest", "report"],
        "skills": ["create-unit-tests", "nerd-execute"],
        "output_signals": ["tests_passed"],
        "output_valid": True,
        "output_severity": "none",
        "verified": True,
        "verifier": "pytest",
        "feedback": "accepted",
        "corrected_tools": [],
        "corrected_steps": [],
        "corrected_skills": [],
        "source_kind": "verified_execution",
        "source_agent": "teacher-agent",
        "evidence_ref": f"proof:{episode_id}",
        "observed_at": "2026-08-31T00:00:00.000000Z",
    }
    value.update(overrides)
    return value


def recall_request(event_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "event_id": event_id,
        "raw_input": "test api",
        "repository": "repo-beta",
        "language": "python",
        "surface": "api",
        "project_kind": "service",
        "current": {"action": None, "tools": [], "steps": [], "skills": []},
        "output_signals": [],
        "consumer_agent": "consumer-agent",
    }
    value.update(overrides)
    return value


class ServerSession:
    """Drive one long-lived stdio MCP process."""

    def __init__(self, database: Path) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(SERVER), str(database)],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 0

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        return self.send(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": self._next_id,
                    "method": method,
                    "params": params or {},
                }
            )
        )

    def send(self, raw: str) -> dict:
        assert self.process.stdin and self.process.stdout
        self.process.stdin.write(raw + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise AssertionError(f"server closed the stream; stderr={self.stderr()}")
        return json.loads(line)

    def call(self, name: str, arguments: object) -> dict:
        response = self.request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        return response["result"]

    def stderr(self) -> str:
        assert self.process.stderr
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            return "<server still running after closing stdout>"
        return self.process.stderr.read().strip()

    def close(self) -> None:
        assert self.process.stdin
        try:
            if not self.process.stdin.closed:
                self.process.stdin.close()
            self.process.wait(timeout=10)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.process.kill()
            self.process.wait(timeout=10)
        finally:
            for stream in (self.process.stdout, self.process.stderr):
                if stream and not stream.closed:
                    stream.close()


class MemoryMcpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_module("nerd_behavior_memory_mcp_test", ENGINE)
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "behavior.sqlite3"
        self.session = ServerSession(self.db)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.session.close)

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ENGINE), "--db", str(self.db), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_payload(self, result: dict) -> dict:
        self.assertFalse(result["isError"], result)
        structured = result["structuredContent"]
        self.assertEqual(json.loads(result["content"][0]["text"]), structured)
        return structured

    def error_code(self, name: str, arguments: object) -> str:
        result = self.session.call(name, arguments)
        self.assertTrue(result["isError"], result)
        payload = result["structuredContent"]
        self.assertEqual(json.loads(result["content"][0]["text"]), payload)
        self.assertFalse(payload["ok"])
        return payload["error"]["code"]

    def test_initialize_reports_fixed_protocol_and_v2_identity(self) -> None:
        response = self.session.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        )
        result = response["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertEqual(
            result["serverInfo"],
            {"name": "nerd-memory-tools", "version": "2.0.0"},
        )

    def test_tools_list_exposes_exactly_three_closed_schemas(self) -> None:
        tools = self.session.request("tools/list")["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, TOOL_NAMES)
        for tool in tools:
            schema = tool["inputSchema"]
            self.assertEqual(schema["type"], "object")
            self.assertFalse(schema["additionalProperties"])
            self.assertIn("description", tool)
            self.assertFalse(tool["annotations"]["destructiveHint"])

        by_name = {tool["name"]: tool for tool in tools}
        self.assertFalse(by_name["memory_recall"]["annotations"]["readOnlyHint"])
        self.assertFalse(by_name["memory_record"]["annotations"]["readOnlyHint"])
        self.assertTrue(by_name["memory_inspect"]["annotations"]["readOnlyHint"])
        self.assertEqual(by_name["memory_inspect"]["inputSchema"]["properties"], {})
        self.assertEqual(by_name["memory_inspect"]["inputSchema"]["required"], [])

        recall_schema = by_name["memory_recall"]["inputSchema"]
        self.assertEqual(
            set(recall_schema["required"]),
            {
                "event_id",
                "raw_input",
                "repository",
                "language",
                "surface",
                "project_kind",
                "current",
                "output_signals",
                "consumer_agent",
            },
        )
        self.assertFalse(
            recall_schema["properties"]["current"]["additionalProperties"]
        )

        record_schema = by_name["memory_record"]["inputSchema"]
        self.assertIn("raw_input", record_schema["required"])
        self.assertNotIn("command_cues", record_schema["properties"])
        serialized = json.dumps(tools, sort_keys=True).casefold()
        for term in REMOVED_TERMS:
            self.assertNotIn(term, serialized)

    def test_record_is_thin_engine_adapter_and_raw_input_is_transient(self) -> None:
        raw = "Please test the API transient-marker-42"
        stored = self.assert_payload(
            self.session.call(
                "memory_record", episode("mcp-record", raw_input=raw)
            )
        )
        self.assertFalse(stored["idempotent"])
        self.assertEqual(
            stored["episode"]["command_cues"],
            ["api", "test", "transient-marker-42"],
        )
        self.assertNotIn("raw_input", stored["episode"])

        inspected = self.assert_payload(self.session.call("memory_inspect", {}))
        self.assertNotIn(raw, json.dumps(inspected))

        direct = self.engine.BehaviorMemoryStore(self.db)
        self.addCleanup(direct.close)
        direct_inspect = direct.inspect()
        self.assertEqual(inspected, direct_inspect)

        cli = self.run_cli("inspect")
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertEqual(inspected, json.loads(cli.stdout))

    def test_recall_matches_cli_and_direct_engine_exactly(self) -> None:
        targets = (
            self.db,
            Path(self.temp.name) / "cli.sqlite3",
            Path(self.temp.name) / "direct.sqlite3",
        )
        for target in targets:
            with self.engine.BehaviorMemoryStore(target) as store:
                store.record(**episode("teacher"))

        request = recall_request("recall-1")
        mcp_result = self.assert_payload(
            self.session.call("memory_recall", request)
        )

        cli_db = Path(self.temp.name) / "cli.sqlite3"
        cli = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ENGINE),
                "--db",
                str(cli_db),
                "recall",
                "--request",
                json.dumps(request),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cli.returncode, 0, cli.stderr)

        direct_db = Path(self.temp.name) / "direct.sqlite3"
        with self.engine.BehaviorMemoryStore(direct_db) as store:
            direct_result = store.recall(**request)

        self.assertEqual(mcp_result, json.loads(cli.stdout))
        self.assertEqual(mcp_result, direct_result)

    def test_record_matches_cli_and_direct_engine_shapes(self) -> None:
        request = episode("shape-record")
        mcp_result = self.assert_payload(self.session.call("memory_record", request))

        cli_db = Path(self.temp.name) / "record-cli.sqlite3"
        cli = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ENGINE),
                "--db",
                str(cli_db),
                "record",
                "--episode",
                json.dumps(request),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cli.returncode, 0, cli.stderr)
        cli_result = json.loads(cli.stdout)

        direct_db = Path(self.temp.name) / "record-direct.sqlite3"
        with self.engine.BehaviorMemoryStore(direct_db) as store:
            direct_result = store.record(**request)

        for result in (cli_result, direct_result):
            self.assertEqual(set(result), set(mcp_result))
            self.assertEqual(
                {
                    key: value
                    for key, value in result["episode"].items()
                    if key != "created_at"
                },
                {
                    key: value
                    for key, value in mcp_result["episode"].items()
                    if key != "created_at"
                },
            )

    def test_domain_error_codes_match_cli_and_server_recovers(self) -> None:
        invalid = episode("bad", verified=False)
        mcp_code = self.error_code("memory_record", invalid)
        cli = self.run_cli("record", "--episode", json.dumps(invalid))
        self.assertEqual(cli.returncode, 2)
        self.assertEqual(mcp_code, json.loads(cli.stderr)["error"]["code"])

        healthy = self.session.call("memory_record", episode("healthy"))
        self.assertFalse(healthy["isError"], healthy)

        first_recall = self.session.call(
            "memory_recall", recall_request("replay")
        )
        self.assertFalse(first_recall["isError"], first_recall)
        self.assertEqual(
            self.error_code("memory_recall", recall_request("replay")),
            "invariant_violation",
        )

    def test_missing_and_unknown_arguments_are_invalid_input(self) -> None:
        for name in ("memory_recall", "memory_record"):
            with self.subTest(name=name):
                self.assertEqual(self.error_code(name, {}), "invalid_input")
        self.assertEqual(
            self.error_code("memory_inspect", {"limit": 1}), "invalid_input"
        )
        self.assertEqual(
            self.error_code(
                "memory_recall", {**recall_request("unknown"), "bogus": 1}
            ),
            "invalid_input",
        )

    def test_non_object_arguments_and_unknown_tool_are_isolated(self) -> None:
        self.assertEqual(self.error_code("memory_inspect", []), "invalid_input")
        self.assertEqual(self.error_code("memory_nope", {}), "unknown_tool")
        tools = self.session.request("tools/list")["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, TOOL_NAMES)

    def test_malformed_line_notification_and_method_errors_do_not_break_stream(self) -> None:
        malformed = self.session.send("{not json")
        self.assertEqual(malformed["error"]["code"], -32700)

        assert self.session.process.stdin
        self.session.process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
            + "\n"
        )
        self.session.process.stdin.flush()
        missing_method = self.session.request("no/such/method")
        self.assertEqual(missing_method["error"]["code"], -32601)
        tools = self.session.request("tools/list")["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, TOOL_NAMES)

    def test_non_object_call_params_do_not_break_stream(self) -> None:
        for request_id, params in enumerate(
            ("not-an-object", [], "", 0, None), start=41
        ):
            with self.subTest(params=params):
                malformed = self.session.send(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "tools/call",
                            "params": params,
                        }
                    )
                )
                self.assertEqual(malformed["error"]["code"], -32602)
        tools = self.session.request("tools/list")["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, TOOL_NAMES)

    def test_live_schema_version_change_stays_restart_required(self) -> None:
        self.assert_payload(self.session.call("memory_inspect", {}))
        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "UPDATE metadata SET value='999' WHERE key='schema_version'"
            )
            connection.commit()
        finally:
            connection.close()

        self.assertEqual(self.error_code("memory_inspect", {}), "restart_required")

        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "UPDATE metadata SET value=? WHERE key='schema_version'",
                (str(self.engine.SCHEMA_VERSION),),
            )
            connection.commit()
        finally:
            connection.close()
        self.assertEqual(self.error_code("memory_inspect", {}), "restart_required")

    def test_opening_schema_family_or_version_mismatch_stays_closed(self) -> None:
        cases = (("schema_family", "legacy-memory"), ("schema_version", "999"))
        for key, wrong_value in cases:
            with self.subTest(key=key):
                path = Path(self.temp.name) / f"wrong-{key}.sqlite3"
                with self.engine.BehaviorMemoryStore(path):
                    pass
                connection = sqlite3.connect(path)
                try:
                    connection.execute(
                        "UPDATE metadata SET value=? WHERE key=?", (wrong_value, key)
                    )
                    connection.commit()
                finally:
                    connection.close()

                session = ServerSession(path)
                self.addCleanup(session.close)
                result = session.call("memory_inspect", {})
                self.assertEqual(
                    result["structuredContent"]["error"]["code"],
                    "restart_required",
                )

                connection = sqlite3.connect(path)
                try:
                    restored = (
                        self.engine.SCHEMA_FAMILY
                        if key == "schema_family"
                        else str(self.engine.SCHEMA_VERSION)
                    )
                    connection.execute(
                        "UPDATE metadata SET value=? WHERE key=?", (restored, key)
                    )
                    connection.commit()
                finally:
                    connection.close()
                again = session.call("memory_inspect", {})
                self.assertEqual(
                    again["structuredContent"]["error"]["code"],
                    "restart_required",
                )


class InstallerContractTests(unittest.TestCase):
    def test_installer_manifest_copies_only_runtime_and_expects_three_tools(self) -> None:
        installer = load_module("nerd_install_mcp_contract_test", INSTALL_MCP)
        manifest = installer.SERVERS["nerd-memory-tools"]
        self.assertEqual(
            manifest["runtime_files"], ("mcp_server.py", "memory.py")
        )
        self.assertEqual(manifest["expected_tools"], TOOL_NAMES)

    def test_runtime_defaults_to_global_behavior_database_without_installer_selector(self) -> None:
        installer_text = INSTALL_MCP.read_text(encoding="utf-8").casefold()
        self.assertNotIn("namespace", installer_text)
        self.assertNotIn("global_search", installer_text)
        server_text = SERVER.read_text(encoding="utf-8")
        self.assertIn("default_database_path", server_text)
        self.assertIn("behavior.sqlite3", ENGINE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
