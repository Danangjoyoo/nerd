from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "docs" / "experiments" / "nerd-ufast" / "skill" / "scripts"
SERVER = SCRIPTS / "mcp_server.py"
sys.path.insert(0, str(SCRIPTS))


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _patch(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


class UFastMcpTests(unittest.TestCase):
    def test_server_initializes_and_lists_exact_tools(self):
        requests = (
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        result = subprocess.run(
            [sys.executable, str(SERVER)],
            input="".join(json.dumps(item) + "\n" for item in requests),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "nerd-ufast-tools")
        tools = responses[1]["result"]["tools"]
        self.assertEqual({item["name"] for item in tools}, {"inspect", "apply_verify"})
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")

    def test_inspect_batches_queries_and_refreshes_changed_files(self):
        from ufast_tools import InspectIndex

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace / "feature.py"
            source.write_text("def alpha():\n    return 1\n", encoding="utf-8")
            index = InspectIndex()
            first = index.inspect(
                str(workspace),
                [{"symbol": "alpha"}, {"path": "feature.py", "start_line": 1, "end_line": 1}],
                context_lines=1,
                max_results=10,
                max_bytes=4096,
            )
            self.assertFalse(first["cache_hit"])
            self.assertEqual(len(first["results"]), 2)
            source.write_text("def beta():\n    return 2\n", encoding="utf-8")
            second = index.inspect(
                str(workspace),
                [{"symbol": "beta"}],
                context_lines=1,
                max_results=10,
                max_bytes=4096,
            )
            self.assertFalse(second["cache_hit"])
            self.assertEqual(second["results"][0]["matches"][0]["path"], "feature.py")

    def test_inspect_rejects_workspace_escape(self):
        from ufast_tools import InspectIndex

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            with self.assertRaisesRegex(ValueError, "escapes workspace"):
                InspectIndex().inspect(
                    str(workspace),
                    [{"path": "../secret.txt"}],
                    context_lines=0,
                    max_results=1,
                    max_bytes=1024,
                )

    def test_inspect_isolates_missing_paths_inside_a_batch(self):
        from ufast_tools import InspectIndex

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "feature.py").write_text(
                "def alpha():\n    return 1\n",
                encoding="utf-8",
            )
            result = InspectIndex().inspect(
                str(workspace),
                [{"path": "missing.py"}, {"symbol": "alpha"}],
                context_lines=1,
                max_results=10,
                max_bytes=4096,
            )
            self.assertEqual(result["results"][0]["matches"], [])
            self.assertEqual(
                result["results"][0]["error"],
                "path is not a regular file: missing.py",
            )
            self.assertEqual(
                result["results"][1]["matches"][0]["path"],
                "feature.py",
            )

    def test_apply_verify_succeeds_and_rejects_stale_hash(self):
        from ufast_tools import apply_verify

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace / "feature.py"
            before = "VALUE = 1\n"
            after = "VALUE = 2\n"
            source.write_text(before, encoding="utf-8")
            result = apply_verify(
                str(workspace),
                _patch("feature.py", before, after),
                {"feature.py": _hash(source)},
                [{"argv": [sys.executable, "-c", "import feature; assert feature.VALUE == 2"]}],
                timeout_seconds=5,
                max_output_bytes=1024,
            )
            self.assertEqual(result["patch_status"], "applied")
            self.assertFalse(result["rolled_back"])
            self.assertEqual(source.read_text(encoding="utf-8"), after)

            source.write_text(before, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale starting hash"):
                apply_verify(
                    str(workspace),
                    _patch("feature.py", before, after),
                    {"feature.py": "0" * 64},
                    [],
                    timeout_seconds=5,
                    max_output_bytes=1024,
                )
            self.assertEqual(source.read_text(encoding="utf-8"), before)

    def test_apply_verify_rolls_back_timeout_and_bounds_output(self):
        from ufast_tools import apply_verify

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace / "feature.py"
            before = "VALUE = 1\n"
            after = "VALUE = 2\n"
            source.write_text(before, encoding="utf-8")
            result = apply_verify(
                str(workspace),
                _patch("feature.py", before, after),
                {"feature.py": _hash(source)},
                [
                    {"argv": [sys.executable, "-c", "print('x' * 1000)"]},
                    {"argv": [sys.executable, "-c", "import time; time.sleep(0.2)"], "timeout_seconds": 0.02},
                ],
                timeout_seconds=1,
                max_output_bytes=32,
            )
            self.assertEqual(result["patch_status"], "verification_failed")
            self.assertTrue(result["rolled_back"])
            self.assertEqual(source.read_text(encoding="utf-8"), before)
            self.assertTrue(result["checks"][0]["stdout_truncated"])
            self.assertLessEqual(len(result["checks"][0]["stdout"].encode()), 32)
            self.assertTrue(result["checks"][1]["timed_out"])


if __name__ == "__main__":
    unittest.main()
