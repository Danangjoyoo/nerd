#!/usr/bin/env python3
"""Allocation smoke protocol regressions; no model requests."""

from contextlib import nullcontext, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import allocation_probe as probe


class AllocationProbeTests(unittest.TestCase):
    def test_shared_prompt_uses_actual_smart_fields_and_is_unambiguous_omission(self):
        payload = {"cwd": "/private/project", "hook_event_name": "UserPromptSubmit", "model": "gpt-5.6-terra",
                   "permission_mode": "never", "prompt": probe.PROMPT, "session_id": "native-session",
                   "transcript_path": None, "turn_id": "native-turn"}
        self.assertEqual(probe.allocation.classify_activation(payload)["status"], "omitted")
        for field in ("Intention", "Expectation", "Scope", "Role"):
            self.assertIn(field, probe.PROMPT)
        self.assertNotIn("Authority:", probe.PROMPT)
        skill = (probe.REPO / "skills/nerd-smart/SKILL.md").read_text()
        for name in ("Focus First", "Endpoint Mapping"):
            actual = skill.split("## " + name + "\n", 1)[1].split("\n## ", 1)[0].strip()
            self.assertIn(actual, probe.PROMPT)
        self.assertIn("**Expectation:** [One endpoint from Endpoint Mapping]", probe.PROMPT)
        self.assertIn("**Role:** [Single best role]", probe.PROMPT)
        self.assertIn("| **Discuss** | Receive an answer", probe.PROMPT)

    def test_only_prompt_hook_registered_and_no_context_tool_wrapper(self):
        value = probe.configuration(Path("/private/state/context.sqlite3"), Path("/private/state/journal"))
        self.assertEqual(set(value["hooks"]), {"UserPromptSubmit"})
        command = value["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertIn("hook_allocation.py", command)
        self.assertNotIn("context_recall", command)
        self.assertNotIn("Stop", command)

    def test_digest_mismatch_prevents_native_processes(self):
        with patch.object(probe, "protocol_record", return_value={"source_fingerprints": {}}), \
                patch.object(probe, "prepare", side_effect=AssertionError("no process")):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                probe.run(SimpleNamespace(command="run", reviewed_protocol_sha256="bad"))

    def test_second_preflight_failure_blocks_both_model_processes(self):
        protocol = {"source_fingerprints": {}, "arms": ["baseline", "empty_allocation"], "client_version": "test"}
        args = SimpleNamespace(command="run", reviewed_protocol_sha256=probe.native.digest(protocol))
        def prepare(arm, root, collector):
            (root / "home").mkdir(parents=True)
            return {"metadata": {"issues": [] if arm == "baseline" else ["missing hook"]}}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(probe, "REPO", Path(temporary)), \
                    patch.object(probe, "protocol_record", return_value=protocol), \
                    patch.object(probe, "fingerprints", return_value={}), \
                    patch.object(probe, "prepare", side_effect=prepare), \
                    patch.object(probe, "TelemetryCollector", return_value=nullcontext(SimpleNamespace())), \
                    patch.object(probe.native, "run_process", side_effect=AssertionError("no model")), \
                    redirect_stdout(io.StringIO()):
                probe.run(args)
            summary = json.loads(next(Path(temporary).rglob("summary.json")).read_text())
            self.assertEqual(summary["model_processes"], 0)
            self.assertEqual(summary["preflight_issues"]["empty_allocation"], ["missing hook"])
            self.assertFalse(list(Path(temporary).rglob("home")))

    def raw_row(self):
        identifier = "ctx_" + "a" * 39
        result = {"status": "created", "context_id": identifier, "receipt": probe.allocation.receipt(identifier),
                  "committed_before_response": True, "prompt_sha256": probe.native.digest(probe.PROMPT.encode()),
                  "operation_elapsed_ms": 2}
        return {"arm": "empty_allocation", "hook_observations": [{"result": result}], "events": [], "telemetry": [],
                "before": {"exists": False, "context_ids": [], "record_count": 0, "capture_count": 0, "mapping_count": 0},
                "after": {"exists": True, "context_ids": [identifier], "record_count": 0, "capture_count": 0, "mapping_count": 1},
                "final_text": "Intention: calculate\nExpectation: Discuss\nScope: arithmetic\nRole: calculator\n42\n"+result["receipt"],
                "exit_code": 0, "timed_out": False, "interrupted": False, "unexpected_workspace_changes": [],
                "elapsed_ms": 100, "registration_preflight": {"elapsed_ms": 2}}

    def test_real_id_echo_and_commit_match_are_required_but_never_a_gate_pass(self):
        row = self.raw_row()
        result = probe.summarize(row)
        self.assertTrue(result["mechanism_observed"])
        self.assertTrue(all(result["focus_fields_visible"].values()))
        self.assertEqual(result["gate_result"], "not_evaluated")
        self.assertIsNone(result["native_incremental_activation_ms"])
        self.assertFalse(result["usage"]["complete"])
        for change in ("receipt", "db", "commit", "prompt", "duplicate", "before", "records", "capture"):
            changed = self.raw_row()
            if change == "receipt":
                changed["final_text"] = "42"
            elif change == "db":
                changed["after"]["context_ids"] = ["ctx_"+"b"*38+"a"]
            elif change == "commit":
                changed["hook_observations"][0]["result"]["committed_before_response"] = False
            elif change == "prompt":
                changed["hook_observations"][0]["result"]["prompt_sha256"] = "changed"
            elif change == "duplicate":
                changed["hook_observations"].append(dict(changed["hook_observations"][0]))
            elif change == "before":
                changed["before"]["context_ids"] = ["ctx_previous"]
            elif change == "records":
                changed["after"]["record_count"] = 1
            else:
                changed["after"]["capture_count"] = 1
            self.assertFalse(probe.summarize(changed)["mechanism_observed"], change)


if __name__ == "__main__":
    unittest.main()
