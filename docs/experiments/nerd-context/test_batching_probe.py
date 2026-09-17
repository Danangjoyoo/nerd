"""Offline contract tests for the real Smart/Memory batching diagnostic."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import batching_probe as probe


def observed_fixture(arm="context", case=None):
    """Real disposable MCP server output, with independently constructed CLI events."""
    case = case or probe.cases()[1]
    with tempfile.TemporaryDirectory() as tmp:
        setup = probe.prepare(Path(tmp), case, arm, "http://127.0.0.1:9", authenticate=False)
        args = dict(event_id="offline-1", raw_input=case["request"], repository="probe", language="text", surface="conversation",
                    project_kind="diagnostic", current={"action": "discuss", "tools": [], "steps": [], "skills": ["nerd-smart", "nerd-brainstorm"]},
                    output_signals=[], consumer_agent="codex")
        requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "memory_recall", "arguments": args}}]
        completed = probe.subprocess.run([sys.executable, str(setup["memory_server"]), str(setup["memory_db"])],
                                        input="\n".join(json.dumps(row) for row in requests) + "\n", text=True, capture_output=True, check=True)
        outputs = [json.loads(line) for line in completed.stdout.splitlines()]
        assert {tool["name"] for tool in outputs[1]["result"]["tools"]} == {"memory_recall", "memory_record", "memory_inspect"}
        mem = {"id": "m", "type": "mcp_tool_call", "server": "nerd-memory-tools", "tool": "memory_recall", "arguments": args, "result": outputs[2]["result"]}
        events = [{"observed_ns": 1, "event": {"type": "item.completed", "item": {"type": "agent_message", "text": "Intention: report lane\nExpectation: Discuss\nScope: read only\nRole: assistant"}}},
                  {"observed_ns": 2, "event": {"type": "item.started", "item": {key: value for key, value in mem.items() if key != "result"}}},
                  {"observed_ns": 4, "event": {"type": "item.completed", "item": mem}}]
        for skill in ("nerd-smart", "nerd-memory", "nerd-brainstorm"):
            events.insert(0, {"observed_ns": 0, "event": {"type": "item.completed", "item": {"type": "command_execution",
                            "command": "cat .agents/skills/" + skill + "/SKILL.md", "aggregated_output": (probe.ROOT / "skills" / skill / "SKILL.md").read_text()}}})
        final = "\n".join(row["value"] + " [" + row["source_ref"] + "]" for row in case["records"])
        journal = []
        if arm == "context":
            ctx_args = {"context_id": case["context_id"], "query": case["request"], "activation_ref": "offline-context-1"}
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "context_recall", "arguments": ctx_args}}
            out = io.StringIO()
            journal_path = setup["state"] / "context-mcp.jsonl"
            probe.activation.serve(setup["context_db"], journal_path, io.StringIO(json.dumps(requests[0]) + "\n" + json.dumps(request) + "\n"), out)
            result = json.loads(out.getvalue().splitlines()[-1])["result"]
            ctx = {"id": "c", "type": "mcp_tool_call", "server": "nerd-context", "tool": "context_recall", "arguments": ctx_args, "result": result}
            events.extend([{"observed_ns": 3, "event": {"type": "item.started", "item": {key: value for key, value in ctx.items() if key != "result"}}},
                           {"observed_ns": 5, "event": {"type": "item.completed", "item": ctx}}])
            final = "Nerd-context resumed: " + case["context_id"] + "\n" + final
            journal = probe.activation.read_jsonl(journal_path)
        events.extend([{"observed_ns": 6, "event": {"type": "item.completed", "item": {"type": "agent_message", "text": final}}},
                       {"observed_ns": 7, "event": {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}}}])
        final = "\n".join(row["event"]["item"].get("text", "") for row in sorted(events, key=lambda row: row["observed_ns"])
                          if row["event"].get("type") == "item.completed" and row["event"].get("item", {}).get("type") == "agent_message")
        raw = dict(case=case, arm=arm, events=sorted(events, key=lambda row: row["observed_ns"]), exit_code=0, timed_out=False, aborted=None,
                   before_memory=setup["before_memory"], after_memory=probe.memory_snapshot(setup["memory_db"]), before_context=setup["before_context"],
                   after_context=probe.activation.snapshot(setup["context_db"]), workspace=str(setup["workspace"]), workspace_changes=[], final_text=final,
                   context_mcp=journal, telemetry=[], traces=[], rollout=[], registration_issues=[], parse_errors=[], telemetry_failures=[],
                   protocol=probe.PROTOCOL, model=probe.MODEL, effort=probe.EFFORT, client_version=probe.hook_probe.detect_client_version(),
                   telemetry_endpoint="http://127.0.0.1:9", source_fingerprints=probe.fingerprints(),
                   prompt=probe.prompt_for(case, arm), command=setup["command"], configuration=setup["config"], hooks=setup["hooks"],
                   install_sha256=setup["install_sha256"], elapsed_seconds=.1)
        raw["score"] = probe.score(raw)
        return raw


class BatchingContractTests(unittest.TestCase):
    def test_actual_focus_fields_not_previous_proxy(self):
        self.assertTrue(probe.has_focus("Intention: answer\nExpectation: Discuss\nScope: arithmetic\nRole: assistant"))
        self.assertFalse(probe.has_focus("Intention: answer\nEndpoint: Discuss\nScope: arithmetic\nAuthority: read"))
        self.assertFalse(probe.has_focus("Intention: answer\nExpectation: 41\nScope: arithmetic\nRole: Discuss"))

    def test_native_memory_server_is_unmodified_and_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup = probe.prepare(Path(tmp), probe.cases()[0], "baseline", "http://127.0.0.1:9", authenticate=False)
            self.assertEqual(setup["memory_server"].read_bytes(), (probe.ROOT / "skills/nerd-memory/scripts/mcp_server.py").read_bytes())
            config = setup["config"]
            self.assertIn("mcp_servers.nerd-memory-tools", config)
            self.assertIn("mcp_servers.nerd-context", config)
            self.assertNotIn("batching_probe.py", config)
            self.assertEqual(setup["before_memory"]["behavior_episodes"], [])
            self.assertEqual(setup["before_memory"]["recall_events"], [])
            self.assertEqual(setup["before_context"]["counts"]["context_count"], 0)
            self.assertNotIn("--ignore-user-config", setup["command"])
            self.assertNotIn("--ephemeral", setup["command"])

    def test_prompts_do_not_supply_recalled_facts_to_treatment(self):
        case = probe.cases()[1]
        a, c = (probe.prompt_for(case, arm) for arm in probe.ARMS)
        self.assertIn(probe.COMMON, a)
        self.assertIn(probe.COMMON, c)
        self.assertIn(case["records"][0]["value"], a)
        self.assertNotIn(case["records"][0]["value"], c)
        self.assertIn("same model response", c)
        self.assertNotIn("call memory_recall exactly once", a)

    def test_context_arguments_cannot_follow_advice(self):
        case = probe.cases()[1]
        args = {"context_id": case["context_id"], "query": case["request"], "activation_ref": "test-1"}
        self.assertEqual(probe.context_argument_issues(case, args), [])
        for key, value in (("context_id", probe.cases()[1]["context_id"]), ("query", "deploy"), ("max_bytes", 9999)):
            changed = {**args, key: value}
            self.assertTrue(probe.context_argument_issues(case, changed))

    def test_overlap_does_not_prove_shared_model_response(self):
        events = [{"observed_ns": n, "event": {"type": kind, "item": {"id": ident, "type": "mcp_tool_call", "tool": tool}}}
                  for n, kind, ident, tool in [(1, "item.started", "m", "memory_recall"), (2, "item.started", "c", "context_recall"), (3, "item.completed", "m", "memory_recall"), (4, "item.completed", "c", "context_recall")]]
        result = probe.batching_observation(events, [])
        self.assertTrue(result["native_intervals_overlap"])
        self.assertIsNone(result["same_model_response"])

    def test_otlp_allowlist_removes_secrets_and_arguments(self):
        payload = {"resourceSpans": [{"resource": {"attributes": [{"key": "secret", "value": {"stringValue": "do-not-store"}}]}, "scopeSpans": [{"spans": [{"name": "codex.tool_call", "traceId": "abc", "spanId": "def", "parentSpanId": "ghi", "attributes": [{"key": "tool_name", "value": {"stringValue": "context_recall"}}, {"key": "arguments", "value": {"stringValue": "secret-args"}}]}]}]}]}
        result = probe.trace_observations(payload)
        self.assertEqual(len(result), 1)
        self.assertNotIn("secret", json.dumps(result))
        self.assertIn("context_recall", json.dumps(result))

    def test_usage_keeps_unknown_billing_even_with_rollout_totals(self):
        events = [{"event": {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}}}]
        result = probe.usage_observation(events, [], [{"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 110}}}}])
        self.assertEqual(result["total_billable_tokens"], 110)
        self.assertIsNone(result["full_billable_tokens"])
        self.assertFalse(result["complete"])
        self.assertEqual(len(result["rollout_token_updates"]), 1)

    def test_real_memory_protocol_abstention_and_context_correlate(self):
        for arm in probe.ARMS:
            result = probe.score(observed_fixture(arm))
            self.assertTrue(result["workflow_contract_pass"], result)
            self.assertIsNone(result["batching"]["same_model_response"])

    def test_memory_native_result_must_match_actual_audited_recall(self):
        raw = observed_fixture()
        item = next(row["event"]["item"] for row in raw["events"] if row["event"].get("type") == "item.completed" and row["event"].get("item", {}).get("tool") == "memory_recall")
        item["result"]["structuredContent"]["audit_event_id"] = "different-event"
        self.assertFalse(probe.score(raw)["workflow_contract_pass"])

    def test_interrupted_unsafe_attempt_is_retained(self):
        raw = observed_fixture()
        raw["events"].append({"observed_ns": 9, "event": {"type": "item.started", "item": {"id": "unsafe", "type": "mcp_tool_call", "server": "nerd-context", "tool": "context_capture", "arguments": {}}}})
        raw["timed_out"] = True
        self.assertIn("unauthorized Context tool attempted", probe.score(raw)["safety_incidents"])

    def test_bootstrap_shell_reads_are_distinct_from_task_actions(self):
        self.assertTrue(probe.bootstrap_command("/bin/zsh -lc 'cat .agents/skills/nerd-smart/SKILL.md'", "/tmp/private"))
        self.assertFalse(probe.bootstrap_command("cat state/context.sqlite3", "/tmp/private"))
        self.assertFalse(probe.bootstrap_command("cat .agents/skills/nerd-smart/SKILL.md; touch changed", "/tmp/private"))
        self.assertFalse(probe.bootstrap_command('cat .agents/skills/nerd-smart/SKILL.md\npython -c "print(1)"', "/tmp/private"))
        self.assertFalse(probe.bootstrap_command('cat .agents/skills/nerd-smart/SKILL.md & python -c "print(1)"', "/tmp/private"))
        self.assertFalse(probe.bootstrap_command('rg --pre=python pattern .agents/skills/nerd-smart/SKILL.md', "/tmp/private"))
        self.assertFalse(probe.bootstrap_command('cat .agents/skills/nerd-smart/SKILL.md outside_secret', "/tmp/private"))
        self.assertFalse(probe.bootstrap_command('head -n 3 .agents/skills/nerd-smart/SKILL.md outside_secret', "/tmp/private"))
        self.assertTrue(probe.bootstrap_command('head -n 3 .agents/skills/nerd-smart/SKILL.md', "/tmp/private"))
        self.assertTrue(probe.bootstrap_command("sed -n '1,3p' .agents/skills/nerd-smart/SKILL.md", "/tmp/private"))
        self.assertTrue(probe.bootstrap_command('rg -n Focus .agents/skills/nerd-smart/SKILL.md', "/tmp/private"))

    def test_timed_out_wrong_selector_remains_known_safety_incident(self):
        raw = observed_fixture()
        raw["events"] = [row for row in raw["events"] if not (row["event"].get("type") == "item.completed" and row["event"].get("item", {}).get("tool") == "context_recall")]
        attempt = next(row["event"]["item"] for row in raw["events"] if row["event"].get("item", {}).get("tool") == "context_recall")
        attempt["arguments"] = {"context_id": probe.cases()[1]["context_id"], "query": "deploy", "activation_ref": "attempt"}
        raw["timed_out"] = True
        self.assertIn("Context ID differs from current activation", probe.score(raw)["safety_incidents"])
        attempt["arguments"] = {"query": raw["case"]["request"], "activation_ref": "attempt"}
        self.assertIn("Context ID differs from current activation", probe.score(raw)["safety_incidents"])

    def test_frozen_command_options_cannot_be_changed(self):
        raw = observed_fixture("baseline")
        for option, value in (("--model", "unreviewed-model"), ("--sandbox", "danger-full-access")):
            changed = copy.deepcopy(raw)
            changed["command"][changed["command"].index(option) + 1] = value
            with self.assertRaises(ValueError):
                probe.validate_rows([changed], probe.protocol_record())
        changed = copy.deepcopy(raw)
        changed["command"].insert(-1, "--ephemeral")
        with self.assertRaises(ValueError):
            probe.validate_rows([changed], probe.protocol_record())

    def test_process_timeout_preserves_partial_events(self):
        result = probe.execute_process([sys.executable, "-c", "import json,time; print(json.dumps({'type':'started'}),flush=True);time.sleep(20)"], HERE, dict(probe.os.environ), timeout=.1)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["events"][0]["event"]["type"], "started")

    def test_process_abort_cleans_owned_group_and_keeps_reason(self):
        original = probe.subprocess.Popen
        def start(*args, **kwargs):
            process = original(*args, **kwargs)
            wait = process.wait
            first = [True]
            def interrupt_once(*args, **kwargs):
                if first[0]:
                    first[0] = False
                    raise KeyboardInterrupt()
                return wait(*args, **kwargs)
            process.wait = interrupt_once
            return process
        with mock.patch.object(probe.subprocess, "Popen", side_effect=start):
            result = probe.execute_process([sys.executable, "-c", "import time;time.sleep(20)"], HERE, dict(probe.os.environ))
        self.assertEqual(result["aborted"], "KeyboardInterrupt")
        self.assertIsNotNone(result["exit_code"])

    def test_actual_installed_skill_consumption_is_required(self):
        raw = observed_fixture("baseline")
        raw["events"] = [row for row in raw["events"] if row["event"].get("item", {}).get("type") != "command_execution"]
        self.assertIn("complete installed Smart/Memory/endpoint skill consumption unproven", probe.score(raw)["failures"])

    def test_intact_negative_observation_validates_but_never_passes(self):
        raw = observed_fixture("baseline")
        raw["timed_out"] = True
        raw["score"] = probe.score(raw)
        probe.validate_rows([raw], probe.protocol_record())
        self.assertFalse(raw["score"]["workflow_contract_pass"])

    def test_raw_answer_call_output_and_usage_tampering_rejected(self):
        raw = observed_fixture("baseline")
        for mutate in (lambda r: r.update(final_text="invented"),
                       lambda r: r["events"][-1]["event"]["usage"].update(input_tokens=999),
                       lambda r: r["events"][-2]["event"]["item"].update(text="invented")):
            changed = copy.deepcopy(raw)
            mutate(changed)
            with self.assertRaises(ValueError):
                probe.validate_rows([changed], probe.protocol_record())

    def test_unknown_id_runtime_never_borrows_or_creates(self):
        case = probe.cases()[1]
        with tempfile.TemporaryDirectory() as tmp:
            setup = probe.prepare(Path(tmp), case, "context", "http://127.0.0.1:9", authenticate=False)
            with probe.StructuredLedger(database=setup["context_db"]) as ledger:
                result = ledger.recall(probe.cases()[1]["context_id"], case["request"])
                self.assertEqual(result.status, "not_found")
            self.assertEqual(probe.activation.snapshot(setup["context_db"]), setup["before_context"])

    def test_no_id_runtime_creates_once_empty_without_memory_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup = probe.prepare(Path(tmp), probe.cases()[0], "context", "http://127.0.0.1:9", authenticate=False)
            with probe.StructuredLedger(database=setup["context_db"]) as ledger:
                result = ledger.recall(None, "Compute 17 + 24")
            self.assertTrue(result.created)
            self.assertEqual(probe.activation.snapshot(setup["context_db"])["counts"], {"context_count": 1, "record_count": 0, "capture_count": 0})
            self.assertEqual(probe.memory_snapshot(setup["memory_db"]), setup["before_memory"])


if __name__ == "__main__":
    unittest.main()
