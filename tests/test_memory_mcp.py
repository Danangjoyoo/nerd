from __future__ import annotations

from pathlib import Path
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

TOOL_NAMES = {"memory_recall", "memory_settle", "memory_learn", "memory_inspect"}


def empty_endpoint(endpoint: str = "plan") -> dict[str, object]:
    return {
        "endpoint": endpoint,
        "goal": None,
        "task": [],
        "action": [],
        "result": None,
        "boundary": [],
        "verification": [],
        "routing": [],
    }


class ServerSession:
    """Drive one long-lived stdio MCP server process."""

    def __init__(self, db: Path) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(SERVER), str(db)],
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

    def call(self, name: str, arguments: dict) -> dict:
        return self.request("tools/call", {"name": name, "arguments": arguments})["result"]

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
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.session = ServerSession(self.db)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.session.close)
        self.namespace = "user:mcp"

    def recall_arguments(self, **overrides) -> dict:
        arguments = {
            "namespace": self.namespace,
            "episode_id": "episode-1",
            "input_text": "plan the release",
            "context": {"repo": "nerd"},
            "baseline": empty_endpoint("plan"),
            "consent_ref": "thread-1:turn-1",
        }
        arguments.update(overrides)
        return arguments

    def run_cli(self, db: Path, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ENGINE), "--db", str(db), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_initialize_reports_the_server_identity(self):
        response = self.session.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        )
        info = response["result"]["serverInfo"]
        self.assertEqual(info["name"], "nerd-memory-tools")
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")

    def test_tools_list_exposes_exactly_the_four_tools(self):
        tools = self.session.request("tools/list")["result"]["tools"]
        self.assertEqual({tool["name"] for tool in tools}, TOOL_NAMES)
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
            self.assertIn("description", tool)
        inspect_tool = next(t for t in tools if t["name"] == "memory_inspect")
        self.assertTrue(inspect_tool["annotations"]["readOnlyHint"])

    def test_closed_stream_reports_server_stderr(self):
        session = ServerSession.__new__(ServerSession)
        session.process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdin.readline(); "
                "sys.stderr.write('server failed\\n')",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(session.close)

        with self.assertRaisesRegex(AssertionError, "server failed"):
            session.send("{}")

    def test_recall_matches_the_cli_recall_result(self):
        result = self.session.call("memory_recall", self.recall_arguments())
        self.assertFalse(result["isError"])
        structured = result["structuredContent"]

        cli_db = Path(self.temp.name) / "cli.sqlite3"
        completed = self.run_cli(
            cli_db,
            "recall",
            "--namespace",
            self.namespace,
            "--episode-id",
            "episode-1",
            "--input-text",
            "plan the release",
            "--context",
            json.dumps({"repo": "nerd"}),
            "--baseline",
            json.dumps(empty_endpoint("plan")),
            "--consent-ref",
            "thread-1:turn-1",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        cli_payload = json.loads(completed.stdout)

        self.assertEqual(structured["consent"], cli_payload["consent"])
        for field in ("status", "memory_influenced", "proposed_endpoint"):
            self.assertEqual(
                structured["proposal"][field], cli_payload["proposal"][field]
            )

    def test_text_content_carries_the_same_payload_as_structured_content(self):
        result = self.session.call("memory_recall", self.recall_arguments())
        self.assertEqual(
            json.loads(result["content"][0]["text"]), result["structuredContent"]
        )

    def seed_pattern(self, namespace: str, key: str) -> None:
        """Create a real consolidated pattern so isolation has something to leak."""
        self.session.call(
            "memory_recall", self.recall_arguments(namespace=namespace)
        )
        for index in range(3):
            result = self.session.call(
                "memory_learn",
                {
                    "namespace": namespace,
                    "episode_id": f"{key}-seed-{index}",
                    "pattern_type": "action",
                    "pattern_key": key,
                    "value": [f"do {key}"],
                    "scope": {"repo": "nerd"},
                    "triggers": ["build"],
                    "source": "direct_user",
                    "evidence_ref": f"{key}-{index}:turn-2",
                    "min_episodes": 3,
                },
            )
            self.assertFalse(result["isError"], result)

    def test_inspect_reads_only_the_supplied_namespace(self):
        self.seed_pattern(self.namespace, "mine")
        self.seed_pattern("user:other", "theirs")

        result = self.session.call("memory_inspect", {"namespace": self.namespace})

        self.assertFalse(result["isError"])
        structured = result["structuredContent"]
        self.assertEqual(structured["consent"]["namespace"], self.namespace)
        keys = {pattern["pattern_key"] for pattern in structured["patterns"]}
        # Proves the seeding worked, so the exclusion below is not vacuous.
        self.assertIn("mine", keys)
        self.assertNotIn("theirs", keys)
        for pattern in structured["patterns"]:
            self.assertEqual(pattern["namespace"], self.namespace)

    def test_domain_errors_keep_the_cli_error_code(self):
        result = self.session.call(
            "memory_recall", self.recall_arguments(baseline={"unexpected": True})
        )

        self.assertTrue(result["isError"])
        self.assertEqual(result["structuredContent"]["error"]["code"], "invalid_input")
        self.assertFalse(result["structuredContent"]["ok"])

    def test_unknown_tool_is_an_error_result_not_a_crash(self):
        result = self.session.call("memory_nope", {})
        self.assertTrue(result["isError"])
        self.assertEqual(result["structuredContent"]["error"]["code"], "unknown_tool")

        healthy = self.session.request("tools/list")
        self.assertEqual(
            {tool["name"] for tool in healthy["result"]["tools"]}, TOOL_NAMES
        )

    def test_server_recovers_after_a_domain_error(self):
        self.session.call(
            "memory_recall", self.recall_arguments(baseline={"unexpected": True})
        )
        result = self.session.call("memory_recall", self.recall_arguments())
        self.assertFalse(result["isError"])

    def test_malformed_line_does_not_corrupt_the_stream(self):
        response = self.session.send("{not json")
        self.assertEqual(response["error"]["code"], -32700)

        healthy = self.session.request("tools/list")
        self.assertEqual(
            {tool["name"] for tool in healthy["result"]["tools"]}, TOOL_NAMES
        )

    def test_notifications_without_an_id_produce_no_response(self):
        assert self.session.process.stdin
        self.session.process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
        )
        self.session.process.stdin.flush()

        healthy = self.session.request("tools/list")
        self.assertEqual(
            {tool["name"] for tool in healthy["result"]["tools"]}, TOOL_NAMES
        )

    def test_schema_change_reports_restart_required_and_never_retries(self):
        first = self.session.call("memory_recall", self.recall_arguments())
        self.assertFalse(first["isError"])

        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "UPDATE metadata SET value = ? WHERE key = 'schema_version'", ("999",)
            )
            connection.commit()
        finally:
            connection.close()

        result = self.session.call(
            "memory_recall", self.recall_arguments(episode_id="episode-after")
        )
        self.assertTrue(result["isError"])
        self.assertEqual(
            result["structuredContent"]["error"]["code"], "restart_required"
        )

        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "UPDATE metadata SET value = ? WHERE key = 'schema_version'",
                (str(self.current_schema_version()),),
            )
            connection.commit()
        finally:
            connection.close()

        sticky = self.session.call("memory_inspect", {"namespace": self.namespace})
        self.assertTrue(sticky["isError"])
        self.assertEqual(
            sticky["structuredContent"]["error"]["code"], "restart_required"
        )

    @staticmethod
    def current_schema_version() -> int:
        import importlib.util

        spec = importlib.util.spec_from_file_location("nerd_memory_probe", ENGINE)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return int(module.SCHEMA_VERSION)



class MemoryMcpArgumentContractTests(unittest.TestCase):
    """Argument errors must match the CLI's code, not degrade to internal_error."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.session = ServerSession(self.db)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.session.close)

    def error_code(self, name: str, arguments: dict) -> str:
        result = self.session.call(name, arguments)
        self.assertTrue(result["isError"], result)
        return result["structuredContent"]["error"]["code"]

    def test_missing_required_argument_is_invalid_input(self):
        for name in ("memory_inspect", "memory_recall", "memory_settle", "memory_learn"):
            with self.subTest(tool=name):
                self.assertEqual(self.error_code(name, {}), "invalid_input")

    def test_unknown_argument_is_rejected_not_silently_ignored(self):
        self.assertEqual(
            self.error_code("memory_inspect", {"namespace": "user:x", "bogus": 1}),
            "invalid_input",
        )

    def test_argument_errors_match_the_cli_error_code(self):
        completed = subprocess.run(
            [sys.executable, str(ENGINE), "--db", str(self.db), "list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(
            json.loads(completed.stderr)["error"]["code"],
            self.error_code("memory_inspect", {}),
        )

    def test_valid_arguments_still_pass(self):
        result = self.session.call("memory_inspect", {"namespace": "user:x"})
        self.assertFalse(result["isError"], result)


class MemoryMcpReviewFixTests(unittest.TestCase):
    """Regressions found reviewing the MCP adapter."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.session = ServerSession(self.db)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.session.close)
        self.namespace = "user:review"

    def recall(self, **overrides):
        arguments = {
            "namespace": self.namespace,
            "episode_id": "episode-1",
            "input_text": "plan the release",
            "context": {},
            "baseline": empty_endpoint("plan"),
            "consent_ref": "thread-1:turn-1",
        }
        arguments.update(overrides)
        return self.session.call("memory_recall", arguments)

    def test_settle_consumes_a_memory_free_proposal(self):
        proposal = self.recall()["structuredContent"]["proposal"]
        self.assertEqual(proposal["status"], "memory_free")

        result = self.session.call(
            "memory_settle",
            {
                "proposal_id": proposal["proposal_id"],
                "source": "direct_user",
                "confirmation_ref": "thread-1:turn-2",
            },
        )

        self.assertFalse(result["isError"], result)
        self.assertIn("endpoint", result["structuredContent"]["consumption"])

    def test_settle_never_returns_a_grant_token(self):
        proposal = self.recall()["structuredContent"]["proposal"]
        result = self.session.call(
            "memory_settle",
            {
                "proposal_id": proposal["proposal_id"],
                "source": "direct_user",
                "confirmation_ref": "thread-1:turn-2",
            },
        )
        self.assertNotIn("grant_token", json.dumps(result["structuredContent"]))

    def test_recall_exposes_the_consent_discriminators(self):
        consent = self.recall()["structuredContent"]["consent"]
        self.assertIn("was_configured", consent)
        self.assertIn("disabled_at", consent)

    def test_a_stale_engine_copy_fails_closed_and_stays_closed(self):
        """A runtime copy older than the store must refuse, not retry forever.

        The installer copies memory.py next to the server, so an upgraded skill
        with a stale MCP runtime opens a store newer than its own engine. That
        raises at open time, not through the live-handle guard.
        """
        self.recall()
        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "UPDATE metadata SET value = ? WHERE key = 'schema_version'", ("999",)
            )
            connection.commit()
        finally:
            connection.close()

        stale = ServerSession(self.db)
        self.addCleanup(stale.close)
        self.session = stale
        first = self.session.call("memory_inspect", {"namespace": self.namespace})
        self.assertTrue(first["isError"])
        self.assertEqual(
            first["structuredContent"]["error"]["code"], "restart_required"
        )
        again = self.session.call("memory_inspect", {"namespace": self.namespace})
        self.assertEqual(
            again["structuredContent"]["error"]["code"], "restart_required"
        )

    def test_baseline_collision_details_survive_the_adapter(self):
        # Drive a baseline collision and require the structured details the CLI emits.
        self.recall()
        for index in range(3):
            self.session.call(
                "memory_learn",
                {
                    "namespace": self.namespace,
                    "episode_id": f"seed-{index}",
                    "pattern_type": "goal",
                    "pattern_key": "g",
                    "value": "ship the release",
                    "scope": {"repo": "nerd"},
                    "triggers": ["release"],
                    "source": "direct_user",
                    "evidence_ref": f"seed-{index}:turn-2",
                    "min_episodes": 3,
                },
            )
        colliding = empty_endpoint("plan")
        colliding["goal"] = "ship the release"
        result = self.session.call(
            "memory_recall",
            {
                "namespace": self.namespace,
                "episode_id": "episode-collide",
                "input_text": "release work",
                "context": {"repo": "nerd"},
                "baseline": colliding,
                "consent_ref": "thread-1:turn-1",
            },
        )
        if result["isError"]:
            error = result["structuredContent"]["error"]
            self.assertIn("details", error)
            self.assertIn("baseline_collisions", error["details"])


if __name__ == "__main__":
    unittest.main()
