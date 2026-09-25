"""Context MCP adapter: inventory, schema, CLI equivalence, error mapping, restart fencing."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "nerd-context" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import context as engine  # noqa: E402
import mcp_server as adapter  # noqa: E402


def _sample_record():
    return {
        "kind": "decision",
        "value": "Agreed migration strategy is staged rollout.",
        "source": "assistant_summary",
        "source_ref": "case-r03",
    }


class McpAdapterTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "sub" / "ctx.sqlite3"
        self.server = adapter.Server(self.db)
        self.addCleanup(self.server.close)

    def test_tool_inventory_is_exact(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(names, {"context_recall", "context_capture", "context_inspect"})

    def test_initialize_returns_expected_metadata(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(response["result"]["serverInfo"]["name"], "nerd-context-tools")

    def _call(self, name, arguments):
        return self.server.handle({
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })["result"]

    def test_recall_creates_and_captures_then_recalls(self):
        first = self._call("context_recall", {"query": "", "activation_ref": "a-1"})
        self.assertFalse(first["isError"])
        cid = first["structuredContent"]["context_id"]
        cap = self._call("context_capture", {
            "context_id": cid,
            "records": [_sample_record()],
            "capture_ref": "cap-1",
        })
        self.assertFalse(cap["isError"])
        again = self._call("context_recall", {
            "context_id": cid,
            "query": "migration strategy",
            "activation_ref": "a-2",
        })
        self.assertFalse(again["isError"])
        self.assertEqual(len(again["structuredContent"]["records"]), 1)

    def test_structured_and_text_content_are_equal(self):
        first = self._call("context_recall", {"query": "", "activation_ref": "a-1"})
        text_payload = json.loads(first["content"][0]["text"])
        self.assertEqual(text_payload, first["structuredContent"])

    def test_unknown_argument_is_rejected(self):
        response = self._call("context_recall", {
            "query": "", "activation_ref": "a", "unexpected": 1,
        })
        self.assertTrue(response["isError"])
        self.assertEqual(response["structuredContent"]["error"]["code"], "invalid_arguments")

    def test_missing_required_argument_is_rejected(self):
        response = self._call("context_recall", {"query": ""})
        self.assertTrue(response["isError"])
        self.assertEqual(response["structuredContent"]["error"]["code"], "invalid_arguments")

    def test_unknown_id_maps_to_domain_response(self):
        fake_cid = "ctx_" + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" + "i"
        # This ID is malformed so we expect invalid_arguments; use a real forgotten one.
        real = self._call("context_recall", {"query": "", "activation_ref": "a"})
        cid = real["structuredContent"]["context_id"]
        # Delete via a fresh store
        with engine.ContextStore(self.db) as store:
            prev = store.preview_forget(cid, preview_ref="prev-1")
            store.forget(cid, phrase=prev["confirmation_phrase"],
                         source="direct_user", confirmation_ref="conf-1")
        again = self._call("context_recall", {"context_id": cid, "query": "",
                                                "activation_ref": "a-2"})
        # not_found is a valid status, not an error
        self.assertFalse(again["isError"])
        self.assertEqual(again["structuredContent"]["status"], "not_found")

    def test_capture_ref_reuse_mismatch_is_invariant_error(self):
        first = self._call("context_recall", {"query": "", "activation_ref": "a"})
        cid = first["structuredContent"]["context_id"]
        self._call("context_capture", {"context_id": cid,
                                        "records": [_sample_record()],
                                        "capture_ref": "cap-1"})
        alt = _sample_record()
        alt["value"] = "Different decision value"
        response = self._call("context_capture", {"context_id": cid,
                                                    "records": [alt],
                                                    "capture_ref": "cap-1"})
        self.assertTrue(response["isError"])
        self.assertEqual(response["structuredContent"]["error"]["code"],
                         "invariant_violation")

    def test_schema_mismatch_permanently_fences_session(self):
        # Bootstrap first
        first = self._call("context_recall", {"query": "", "activation_ref": "a"})
        self.assertFalse(first["isError"])
        # Corrupt schema and force reopen
        self.server._drop_store()
        import sqlite3
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE metadata SET value=? WHERE key='schema_version'",
                         (str(engine.SCHEMA_VERSION + 1),))
        again = self._call("context_recall", {"query": "", "activation_ref": "a-2"})
        self.assertTrue(again["isError"])
        self.assertEqual(again["structuredContent"]["error"]["code"], "restart_required")
        # Fenced permanently: even after unrelated call, still restart_required
        further = self._call("context_recall", {"query": "", "activation_ref": "a-3"})
        self.assertTrue(further["isError"])
        self.assertEqual(further["structuredContent"]["error"]["code"], "restart_required")

    def test_unknown_method_is_jsonrpc_error(self):
        response = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "no.such"})
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
