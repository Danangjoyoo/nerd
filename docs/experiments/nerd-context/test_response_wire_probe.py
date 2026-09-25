import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import response_wire_probe as wire


class WireTests(unittest.TestCase):
    def test_isolated_environment_uses_no_inherited_credentials(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "secret", "CUSTOM_SECRET": "secret"}):
            environment = wire.isolated_environment(Path(directory))
            self.assertNotIn("OPENAI_API_KEY", environment)
            self.assertNotIn("CUSTOM_SECRET", environment)
            self.assertEqual(environment["OFFLINE_SYNTHETIC_KEY"], "offline-not-a-real-credential")
            self.assertFalse((Path(environment["CODEX_HOME"]) / "auth.json").exists())

    def test_scripted_discovery_is_client_executed_then_two_real_fixture_calls(self):
        request = {"input": [{"type": "message", "content": [{"type": "input_text", "text": wire.PROMPT}]}]}
        search = wire.scripted_output(request)[0]
        self.assertEqual((search["type"], search["execution"]), ("tool_search_call", "client"))
        result = {"type": "tool_search_output", "call_id": wire.SEARCH_ID,
                  "tools": [{"type": "namespace", "name": "mcp__response_fixture", "tools": [{"name": "context_recall"}]}]}
        calls = wire.scripted_output({"input": [result]})
        self.assertEqual({item["call_id"] for item in calls}, {wire.CALL_ID, wire.ERROR_CALL_ID})
        self.assertEqual([json.loads(item["arguments"]) for item in calls], [{"overflow": False}, {"overflow": True}])
        self.assertTrue(all(item["namespace"] == "mcp__response_fixture" for item in calls))

    def test_missing_native_tool_never_substitutes_a_shell_call(self):
        with self.assertRaises(ValueError):
            wire.scripted_output({"input": [{"type": "tool_search_output", "call_id": wire.SEARCH_ID, "tools": []}]})

    def test_server_exposes_matching_text_structured_and_error_status(self):
        requests = [{"jsonrpc": "2.0", "id": index, "method": "tools/call",
                     "params": {"name": "context_recall", "arguments": {"overflow": error}, "_meta": {"callId": "observed"}}}
                    for index, error in enumerate((False, True))]
        stream = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            wire.serve(Path(directory) / "journal.jsonl", io.StringIO("\n".join(json.dumps(item) for item in requests)), stream)
        outputs = [json.loads(line)["result"] for line in stream.getvalue().splitlines()]
        for output in outputs:
            self.assertEqual(json.loads(output["content"][0]["text"]), output["structuredContent"])
        self.assertEqual([output["isError"] for output in outputs], [False, True])

    def test_request_without_actual_prompt_gets_no_scripted_actions(self):
        self.assertEqual(wire.scripted_output({"input": []}), [])

    def test_command_is_local_provider_and_normal_sandbox(self):
        command = wire.command_for(Path("/private/workspace"), Path("/private/journal"), "http://127.0.0.1:12345")
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
        self.assertIn('model_providers.offline.base_url="http://127.0.0.1:12345/v1"', command)
        self.assertIn('model_providers.offline.requires_openai_auth=false', command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)


if __name__ == "__main__":
    unittest.main()
