#!/usr/bin/env python3
"""Offline hook protocol checks; no Codex model requests."""

import io
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from contextlib import nullcontext, redirect_stdout
import unittest
from unittest.mock import patch

import hook_probe as probe


class HookProtocolTests(unittest.TestCase):
    def payload(self, **changes):
        payload = {
            "hook_event_name": "UserPromptSubmit", "session_id": "native-session",
            "turn_id": "native-turn", "prompt": probe.PROMPT,
            "transcript_path": "/private/secret/transcript.jsonl", "cwd": "/private/workspace",
        }
        payload.update(changes)
        return payload

    def test_current_documented_fields_cannot_authorize_allocation(self):
        observation = probe.observe(self.payload(), probe.digest(probe.PROMPT.encode()))
        self.assertTrue(observation["prompt_matches_probe"])
        self.assertIsNotNone(observation["turn_id_sha256"])
        self.assertFalse(observation["allocation_supported"])
        self.assertTrue(observation["allocation_blockers"])
        self.assertEqual(observation["context_operations"], [])

    def test_fabricated_origin_and_attachment_fields_never_unlock_allocation(self):
        observation = probe.observe(self.payload(origin="main", attachments=[], complete=True),
                                    probe.digest(probe.PROMPT.encode()))
        self.assertFalse(observation["allocation_supported"])
        self.assertEqual(observation["payload_shape"]["fields"]["attachments"], {"type": "array", "length": 0})

    def test_observation_redacts_prompt_paths_ids_and_unknown_values(self):
        observation = probe.observe(self.payload(prompt="PRIVATE_PROMPT", access_token="PRIVATE_TOKEN"), "irrelevant")
        output = json.dumps(observation)
        for secret in ("PRIVATE_PROMPT", "PRIVATE_TOKEN", "native-session", "native-turn", "/private"):
            self.assertNotIn(secret, output)
        self.assertIn("access_token", output)
        self.assertFalse(observation["prompt_matches_probe"])

    def test_missing_and_changed_native_keys_are_observations_not_inferred_ids(self):
        rows = [probe.observe(self.payload(turn_id=value), probe.digest(probe.PROMPT.encode()))
                for value in (None, "", "one", "two")]
        self.assertEqual([row["turn_id_sha256"] for row in rows[:2]], [None, None])
        self.assertNotEqual(rows[2]["turn_id_sha256"], rows[3]["turn_id_sha256"])
        self.assertTrue(all(not row["allocation_supported"] for row in rows))

    def test_possible_id_is_reported_without_any_context_operation(self):
        for prompt in ("Context ID: ctx_bad", "Quote 'CTX_ABCD'", "delegated handoff ctx_abc"):
            row = probe.observe(self.payload(prompt=prompt), "irrelevant")
            self.assertTrue(row["possible_context_id_in_prompt"])
            self.assertFalse(row["allocation_supported"])

    def test_bad_hook_event_types_fail_predictably(self):
        for value in ([], {}, None, "SubagentStart"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                probe.observe(self.payload(hook_event_name=value), "irrelevant")

    def test_receipts_neither_request_continuation_nor_claim_context_creation(self):
        for event in probe.SAFE_EVENTS:
            response = probe.hook_response(event, "HOOK_OBS_test123")
            self.assertNotIn("decision", response)
            self.assertNotIn("followup_message", response)
            self.assertIn("No Context was allocated", json.dumps(response))
        with self.assertRaises(ValueError):
            probe.hook_response("UserPromptSubmit", "ctx_not_a_receipt")

    def test_registration_uses_supported_project_events_and_shell_safe_arguments(self):
        configuration = probe.hooks_configuration(Path("/tmp/path with spaces/hooks.jsonl"),
                                                   {event: "HOOK_OBS_test123" for event in probe.SAFE_EVENTS})
        self.assertEqual(set(configuration["hooks"]), {"UserPromptSubmit", "Stop"})
        for event, groups in configuration["hooks"].items():
            handler = groups[0]["hooks"][0]
            command = shlex.split(handler["command"])
            self.assertEqual(command[command.index("--journal") + 1], "/tmp/path with spaces/hooks.jsonl")
            self.assertEqual(command[command.index("--event") + 1], event)
            self.assertEqual(handler["type"], "command")

    def test_command_has_no_wrapper_schema_or_allocating_server(self):
        command = probe.command_for(Path("/tmp/native project"), "http://127.0.0.1:1234/v1/logs")
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn('--dangerously-bypass-hook-trust', command)
        self.assertNotIn('--ignore-user-config', command)
        self.assertFalse(any('projects.' in item for item in command))
        self.assertNotIn("--output-schema", command)
        self.assertFalse(any("mcp_servers" in item for item in command))
        self.assertEqual(command[-1], probe.PROMPT)

    def test_real_python_hook_protocol_writes_only_redacted_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "observations.jsonl"
            command = [sys.executable, str(Path(probe.__file__)), "hook", "--event", "UserPromptSubmit",
                       "--journal", str(journal), "--receipt", "HOOK_OBS_test123",
                       "--expected-prompt-sha256", probe.digest(probe.PROMPT.encode())]
            result = subprocess.run(command, input=json.dumps(self.payload()), text=True,
                                    capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
            rows = probe.read_rows(journal)
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["allocation_supported"])
            self.assertNotIn(probe.PROMPT, journal.read_text())
            self.assertEqual(sorted(path.name for path in Path(temporary).iterdir()), ["observations.jsonl"])

    def test_duplicate_native_keys_are_retained_as_failure_without_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "observations.jsonl"
            command = [sys.executable, str(Path(probe.__file__)), "hook", "--event", "UserPromptSubmit",
                       "--journal", str(journal), "--receipt", "HOOK_OBS_test123",
                       "--expected-prompt-sha256", "irrelevant"]
            result = subprocess.run(command, input='{"hook_event_name":"Stop","hook_event_name":"UserPromptSubmit"}',
                                    text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("HOOK_OBS_test123", result.stdout)
            rows = probe.read_rows(journal)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["hook_error"], "ValueError")
            self.assertFalse(rows[0]["allocation_supported"])

    def test_protocol_digest_mismatch_cannot_start_a_client(self):
        class Args:
            reviewed_protocol_sha256 = "wrong"
        with patch.object(probe, "detect_client_version", return_value="codex-cli 0.153.4"), \
                patch.object(probe.subprocess, "Popen", side_effect=AssertionError("client must not start")):
            with self.assertRaisesRegex(ValueError, "digest does not match"):
                probe.run_probe(Args())

    def test_journal_cannot_follow_a_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.write_text("preserve")
            link = Path(temporary) / "journal"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                probe.append_observation(link, {"observation": True})
            self.assertEqual(target.read_text(), "preserve")

    def test_fake_client_runner_keeps_usage_and_missing_hooks_as_observations(self):
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "42"}},
            {"type": "turn.completed", "usage": {"input_tokens": 120, "output_tokens": 2}},
        ]
        fake = SimpleNamespace(stdout=io.StringIO("\n".join(json.dumps(event) for event in events) + "\n"),
                               stderr=io.StringIO(""), wait=lambda **_: 0)
        collector = SimpleNamespace(endpoint="http://127.0.0.1:1234/v1/logs", records=[], failures=[])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(probe.os.environ, {"CODEX_HOME": str(root / "no-auth")}), \
                    patch.object(probe.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                    patch.object(probe, "inspect_registration", return_value={"elapsed_ms": 0}), \
                    patch.object(probe, "registration_issues", return_value=[]), \
                    patch.object(probe.subprocess, "Popen", return_value=fake) as start:
                row = probe.run_process("observed_hooks", root / "run", collector, client_version="codex-cli 0.153.4")
            self.assertEqual(start.call_count, 1)
            self.assertTrue(start.call_args.kwargs["start_new_session"])
            self.assertEqual(start.call_args.kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(row["final_text"], "42")
            summary = probe.summarize_run(row)
            self.assertFalse(summary["expected_hook_presence"])
            self.assertFalse(summary["allocation_supported"])
            self.assertTrue(summary["answer_contains_42"])
            self.assertEqual(summary["unexpected_workspace_changes"], [])
            self.assertEqual(summary["verdict"], "observation_only")
            self.assertFalse(summary["usage"]["complete"])
            self.assertIsNone(summary["usage"]["full_billable_tokens"])
            self.assertEqual(summary["usage"]["request_coverage"], "unknown")
            self.assertTrue(row["runtime_home_removed"])
            self.assertFalse((root / "run/home").exists())

    def test_interruption_kills_owned_group_retains_partial_output_and_cleans_home(self):
        collector = SimpleNamespace(endpoint="http://127.0.0.1:1234/v1/logs", records=[], failures=[])
        waits = iter([KeyboardInterrupt(), 0])
        def wait(**_):
            value = next(waits)
            if isinstance(value, BaseException):
                raise value
            return value
        fake = SimpleNamespace(stdout=io.StringIO('{"type":"thread.started","thread_id":"partial"}\n'),
                               stderr=io.StringIO("partial evidence"), wait=wait, pid=12345)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(probe.os.environ, {"CODEX_HOME": str(root / "no-auth")}), \
                    patch.object(probe.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                    patch.object(probe, "inspect_registration", return_value={"elapsed_ms": 0}), \
                    patch.object(probe, "registration_issues", return_value=[]), \
                    patch.object(probe.subprocess, "Popen", return_value=fake), \
                    patch.object(probe.os, "killpg") as kill:
                row = probe.run_process("baseline", root / "run", collector, client_version="codex-cli 0.153.4")
            kill.assert_called_once_with(12345, probe.signal.SIGKILL)
            self.assertTrue(row["interrupted"])
            self.assertEqual(row["exit_code"], 130)
            self.assertIn("partial evidence", row["stderr"])
            self.assertEqual(row["events"][0]["event"]["thread_id"], "partial")
            self.assertFalse((root / "run/home").exists())

    def test_version_is_observed_and_invalid_output_stops_protocol(self):
        with patch.object(probe.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="codex-cli 0.153.4\n")) as run:
            self.assertEqual(probe.detect_client_version(), "codex-cli 0.153.4")
            self.assertEqual(run.call_args.args[0], ["codex", "--version"])
        with patch.object(probe.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="")):
            with self.assertRaises(ValueError):
                probe.detect_client_version()

    @unittest.skipUnless(shutil.which("codex"), "native metadata-only Codex client unavailable")
    def test_native_project_loading_requires_private_trust_and_lists_exact_hooks(self):
        # No auth, thread/start, turn/start, or model inference. These are native
        # config-read operations exercising the actual previous failure mode.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace, home = root / "project", root / "home"
            (workspace / ".codex").mkdir(parents=True)
            home.mkdir()
            (workspace / ".codex/config.toml").write_text("# Private test fixture\n")
            configuration = probe.hooks_configuration(root / "must-not-exist.jsonl",
                                                      {event: "HOOK_OBS_test123" for event in probe.SAFE_EVENTS})
            (workspace / ".codex/hooks.json").write_text(json.dumps(configuration))
            environment = dict(probe.os.environ, HOME=str(home), CODEX_HOME=str(home))
            missing = probe.inspect_registration(workspace, environment)
            self.assertTrue(probe.registration_issues(missing, workspace, configuration))
            (home / "config.toml").write_text(probe.private_config(workspace))
            loaded = probe.inspect_registration(workspace, environment)
            self.assertEqual(probe.registration_issues(loaded, workspace, configuration), [], loaded)
            self.assertEqual([row["method"] for row in loaded["requests"]],
                             ["initialize", "config/read", "hooks/list"])
            self.assertFalse((root / "must-not-exist.jsonl").exists())
            self.assertEqual(loaded["inference_requests"], 0)
            # Missing, extra, disabled, or changed handlers cannot pass.
            for change in ("command", "enabled", "extra", "missing"):
                altered = json.loads(json.dumps(loaded))
                hooks = altered["hooks_list"]["data"][0]["hooks"]
                if change == "command":
                    hooks[0]["command"] += " --unreviewed"
                elif change == "enabled":
                    hooks[0]["enabled"] = False
                elif change == "extra":
                    hooks.append(dict(hooks[0]))
                else:
                    hooks.pop()
                self.assertTrue(probe.registration_issues(altered, workspace, configuration), change)

    def test_failed_registration_never_starts_model_and_removes_private_home(self):
        collector = SimpleNamespace(endpoint="http://127.0.0.1:1234/v1/logs", records=[], failures=[])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(probe.os.environ, {"CODEX_HOME": str(root / "no-auth")}), \
                    patch.object(probe.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                    patch.object(probe, "inspect_registration", return_value={"elapsed_ms": 0}), \
                    patch.object(probe, "registration_issues", return_value=["project layer disabled"]), \
                    patch.object(probe.subprocess, "Popen", side_effect=AssertionError("model must not start")):
                with self.assertRaisesRegex(ValueError, "preflight failed"):
                    probe.run_process("observed_hooks", root / "run", collector, client_version="codex-cli 0.153.4")
            self.assertFalse((root / "run/home").exists())

    def test_registration_input_changes_block_model_after_successful_metadata(self):
        collector = SimpleNamespace(endpoint="http://127.0.0.1:1234/v1/logs", records=[], failures=[])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            with patch.dict(probe.os.environ, {"CODEX_HOME": str(root / "no-auth")}), \
                    patch.object(probe.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                    patch.object(probe, "inspect_registration", return_value={"elapsed_ms": 0}), \
                    patch.object(probe, "registration_issues", return_value=[]):
                prepared = probe.prepare_runtime("observed_hooks", root, collector)
            (root / "home/config.toml").write_text("# Changed after preflight\n")
            with patch.object(probe.subprocess, "Popen", side_effect=AssertionError("model must not start")):
                with self.assertRaisesRegex(ValueError, "inputs changed"):
                    probe.run_process("observed_hooks", root, collector,
                                      client_version="codex-cli 0.153.4", prepared=prepared)

    def test_metadata_interruption_kills_owned_group_without_submitting_turn(self):
        fake = SimpleNamespace(stdin=io.StringIO(), stdout=io.StringIO(""), stderr=io.StringIO(""),
                               wait=lambda **_: 0, pid=54321)
        with patch.object(probe.subprocess, "Popen", return_value=fake), \
                patch.object(probe.queue.Queue, "get", side_effect=KeyboardInterrupt()), \
                patch.object(probe.os, "killpg") as kill:
            with self.assertRaises(KeyboardInterrupt):
                probe.inspect_registration(Path("/private/project"), {})
        kill.assert_called_once_with(54321, probe.signal.SIGTERM)

    def test_second_arm_registration_failure_prevents_both_model_runs(self):
        protocol = {"source_fingerprints": {}, "client_version": "codex-cli 0.153.4"}
        args = SimpleNamespace(command="run", reviewed_protocol_sha256=probe.digest(protocol))
        collector = SimpleNamespace(endpoint="unused", records=[], failures=[])
        def prepare(arm, root, _):
            (root / "home").mkdir(parents=True)
            return {"metadata": {"issues": [] if arm == "baseline" else ["missing observed hooks"]}}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(probe, "REPO", Path(temporary)), \
                    patch.object(probe, "protocol_record", return_value=protocol), \
                    patch.object(probe, "detect_client_version", return_value=protocol["client_version"]), \
                    patch.object(probe, "fingerprints", return_value={}), \
                    patch.object(probe, "prepare_runtime", side_effect=prepare), \
                    patch.object(probe, "run_process", side_effect=AssertionError("model must not run")), \
                    patch("activation_probe.TelemetryCollector", return_value=nullcontext(collector)), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(probe.run_probe(args), 2)
            summary_path = next(Path(temporary).rglob("summary.json"))
            summary = json.loads(summary_path.read_text())
            self.assertEqual(summary["native_model_processes"], 0)
            self.assertEqual(summary["runs"], [])
            self.assertEqual(summary["registration_preflight_issues"]["observed_hooks"], ["missing observed hooks"])
            self.assertFalse((summary_path.parent / "baseline/home").exists())
            self.assertFalse((summary_path.parent / "observed_hooks/home").exists())


if __name__ == "__main__":
    unittest.main()
