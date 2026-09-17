"""Offline-only native instrumentation comparison tests."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trace_probe as trace


class TraceProbeTests(unittest.TestCase):
    def test_environment_cannot_forward_real_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = trace.private_environment(Path(tmp), {"PATH": "/bin", "OPENAI_API_KEY": "real-secret", "CODEX_ACCESS_TOKEN": "real-token", "ARBITRARY_SECRET": "secret"})
        self.assertEqual(env["OFFLINE_TRACE_SYNTHETIC_KEY"], trace.CANARY)
        self.assertNotIn("real-secret", json.dumps(env))
        self.assertNotIn("ARBITRARY_SECRET", env)

    def test_only_enumerated_ids_are_normalized(self):
        value = {"model": "gpt-5.4-mini", "metadata": {"session_id": "changing", "query": "keep"}, "input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "literal session_id stays"}]}]}
        changed = copy.deepcopy(value)
        changed["metadata"]["session_id"] = "another"
        self.assertEqual(trace.normalized(value), trace.normalized(changed))
        changed["metadata"]["query"] = "changed"
        self.assertNotEqual(trace.normalized(value), trace.normalized(changed))

    def test_synthetic_sse_contains_complete_response_and_call_ids(self):
        payload = trace.response_bytes(2, "ctx_fixture")
        self.assertIn(b"response.completed", payload)
        self.assertIn(b"call-memory", payload)
        self.assertIn(b"call-context", payload)
        self.assertIn(b"mcp__nerd_memory_tools", payload)

    def test_semantic_change_cannot_disappear_in_comparison(self):
        off = [{"body": {"model": "gpt-5.4-mini", "tools": [{"name": "recall"}]}, "headers": {"x-codex-inference-call-id": "a"}}]
        on = copy.deepcopy(off)
        on[0]["headers"]["x-codex-inference-call-id"] = "b"
        self.assertEqual(trace.request_comparison(off, on)["differences"], [])
        on[0]["body"]["tools"][0]["name"] = "capture"
        self.assertTrue(trace.request_comparison(off, on)["differences"])


if __name__ == "__main__":
    unittest.main()
