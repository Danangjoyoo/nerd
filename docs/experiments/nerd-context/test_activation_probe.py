from __future__ import annotations

import io
import json
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import activation_probe as probe
from structured import StructuredLedger


def transport_event(input_tokens, output_tokens, number):
    return {"timeUnixNano": str(number), "body": {"stringValue": "codex.sse_event"},
            "attributes": [{"key": key, "value": {"stringValue": str(value)}} for key, value in {
                "event.kind": "response.completed", "input_token_count": input_tokens,
                "output_token_count": output_tokens}.items()]}


class ActivationProbeTests(unittest.TestCase):
    def test_stdio_protocol_exposes_exact_inventory_and_only_model_call_creates_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with StructuredLedger(database=root / "ledger.sqlite3") as ledger:
                self.assertEqual(ledger.counts()["context_count"], 0)
            requests = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                    "name": "context_recall", "arguments": {"query": "Compute 17 + 24", "activation_ref": "test-activation"}}},
            ]
            output = io.StringIO()
            probe.serve(root / "ledger.sqlite3", root / "mcp.jsonl",
                        io.StringIO("\n".join(map(json.dumps, requests))), output)
            responses = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual([row["id"] for row in responses], [1, 2, 3])
            self.assertEqual({tool["name"] for tool in responses[1]["result"]["tools"]},
                             {"context_recall", "context_capture", "context_inspect"})
            receipt = json.loads(responses[2]["result"]["content"][0]["text"])
            self.assertTrue(receipt["created"])
            self.assertEqual(receipt["record_ids"], [])
            with StructuredLedger(database=root / "ledger.sqlite3") as ledger:
                self.assertEqual(ledger.counts(), {"context_count": 1, "record_count": 0, "capture_count": 0})
            journal = [json.loads(line) for line in (root / "mcp.jsonl").read_text().splitlines()]
            self.assertEqual(sum(row["direction"] == "request" for row in journal), 4)

    def test_model_roundtrips_and_cumulative_usage_are_not_cli_process_counts(self):
        logs = [transport_event(100, 10, 1), transport_event(120, 20, 2)]
        events = [{"type": "turn.completed", "usage": {"input_tokens": 220, "output_tokens": 30}}]
        usage = probe.account_usage(events, logs, minimum_responses=2)
        self.assertEqual(usage["model_response_count"], 2)
        self.assertEqual(usage["total_billable_tokens"], 250)
        self.assertTrue(usage["complete"])
        self.assertEqual(probe.account_usage(events, logs + [logs[-1]], minimum_responses=2), usage)

    def test_incomplete_or_ambiguous_usage_retains_known_cost_and_never_passes(self):
        logs = [transport_event(100, 10, 1), transport_event(120, 20, 2)]
        for events, canonical in (([], None), ([{"type": "turn.completed", "usage": {"input_tokens": 120, "output_tokens": 20}}], 140)):
            usage = probe.account_usage(events, logs, minimum_responses=2)
            self.assertFalse(usage["complete"])
            self.assertEqual(usage["total_billable_tokens"], canonical)
            self.assertEqual(usage["known_response_billable_tokens"], 250)

    def test_real_stdio_child_dispatches_exact_id_and_rejects_duplicate_json(self):
        case = probe.make_cases()[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with StructuredLedger(case["records"], database=root / "ledger.sqlite3"):
                pass
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                "name": "context_recall", "arguments": {"context_id": case["context_id"],
                "query": case["request"], "activation_ref": "real-stdio"}}}
            source = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}) + "\n" + json.dumps(request) + "\n"
            source += '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"context_recall","arguments":{"query":"x","query":"y","activation_ref":"dup"}}}\n'
            result = subprocess.run([sys.executable, str(probe.HERE / "activation_probe.py"), "serve", "--database", str(root / "ledger.sqlite3"),
                                     "--journal", str(root / "journal.jsonl")], input=source, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [json.loads(line) for line in result.stdout.splitlines()]
            recalled = json.loads(rows[1]["result"]["content"][0]["text"])
            self.assertEqual(recalled["context_id"], case["context_id"])
            self.assertFalse(recalled["created"])
            self.assertTrue(all(record["value"] in recalled["segment"] for record in case["records"]))
            self.assertIn("error", rows[2])
            self.assertEqual(probe.snapshot(root / "ledger.sqlite3")["counts"]["context_count"], 1)

    def test_paired_commands_have_identical_tool_surface_without_output_schema_or_hook(self):
        case = probe.make_cases()[0]
        commands = [probe.command_for(Path("/private/work"), Path("/private/state/db"), Path("/private/state/log"),
                                      "http://127.0.0.1:12345/v1/logs", probe.prompt_for(case, arm)) for arm in ("baseline", "context")]
        self.assertEqual(commands[0][:-1], commands[1][:-1])
        self.assertNotEqual(commands[0][-1], commands[1][-1])
        self.assertNotIn("--output-schema", commands[0])
        self.assertTrue(all("hook" not in argument for argument in commands[0][:-1]))
        self.assertEqual(sum(argument.startswith("mcp_servers.") and ".command=" in argument for argument in commands[0]), 1)

    def test_telemetry_retains_transport_counters_without_resource_credentials(self):
        record = transport_event(100, 20, 1)
        record["attributes"] += [{"key": "authorization", "value": {"stringValue": "must-never-retain"}},
                                  {"key": "user.email", "value": {"stringValue": "private@example.test"}}]
        payload = {"resourceLogs": [{"resource": {"private": "metadata"}, "scopeLogs": [{"logRecords": [record]}]}]}
        retained = probe.transport_records(payload)
        self.assertNotIn("must-never-retain", json.dumps(retained))
        self.assertNotIn("private@example.test", json.dumps(retained))
        self.assertEqual(probe.attributes(retained[0])["input_token_count"], "100")

    def test_fake_codex_process_drives_real_mcp_and_records_two_model_responses(self):
        case = probe.make_cases()[0]
        collector = type("Collector", (), {"endpoint": "http://127.0.0.1:12345/v1/logs", "records": [], "failures": []})()

        class FakeCodex:
            pid = 12345

            def __init__(self, command, **kwargs):
                self.stderr = io.StringIO("")
                server_args = json.loads(next(arg.split("=", 1)[1] for arg in command if arg.startswith("mcp_servers.nerd-context.args=")))
                database = Path(server_args[server_args.index("--database") + 1])
                journal = Path(server_args[server_args.index("--journal") + 1])

                def stream():
                    yield json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "Intention: arithmetic; Endpoint: answer; Scope: current request; Authority: private Context creation only."}}) + "\n"
                    requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize"},
                                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "context_recall",
                                    "arguments": {"query": case["request"], "activation_ref": "fake-model-activation"}}}]
                    output = io.StringIO()
                    probe.serve(database, journal, io.StringIO("\n".join(map(json.dumps, requests))), output)
                    result = json.loads(output.getvalue().splitlines()[-1])["result"]
                    receipt = json.loads(result["content"][0]["text"])
                    text = f"Nerd-context created: {receipt['context_id']}\nAnswer: 41"
                    yield json.dumps({"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "nerd-context", "tool": "context_recall",
                        "arguments": requests[-1]["params"]["arguments"], "result": result}}) + "\n"
                    yield json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": text}}) + "\n"
                    collector.records.extend([transport_event(100, 10, 1), transport_event(120, 20, 2)])
                    yield json.dumps({"type": "turn.completed", "usage": {"input_tokens": 220, "output_tokens": 30}}) + "\n"
                self.stdout = stream()

            def wait(self, timeout=None):
                return 0

        with tempfile.TemporaryDirectory() as directory, patch.object(probe.subprocess, "Popen", FakeCodex), \
             patch.object(probe.subprocess, "run", return_value=type("Result", (), {"returncode": 0})()):
            raw = probe.run_process(case, "context", Path(directory), collector)
        self.assertTrue(raw["score"]["activation_contract_pass"], raw["score"])
        self.assertFalse(raw["score"]["pass"])
        self.assertEqual(raw["score"]["usage"]["observed_response_completions"], 2)
        self.assertIsNone(raw["score"]["usage"]["model_response_count"])
        self.assertEqual(raw["score"]["usage"]["total_billable_tokens"], 250)
        self.assertEqual(raw["after"]["counts"], {"context_count": 1, "record_count": 0, "capture_count": 0})
        self.assertIn("Nerd-context created:", raw["final_text"])
        discovered = copy.deepcopy(raw)
        discovered["events"].insert(0, {"observed_ns": 0, "event": {"type": "item.completed", "item": {"type": "tool_search", "query": "context_recall"}}})
        self.assertEqual(probe.score_run(discovered)["usage"]["minimum_model_responses"], 3)
        self.assertFalse(probe.score_run(discovered)["usage"]["complete"])
        for mutate in (
            lambda row: row.update(final_text="41\nNerd-context created: fabricated"),
            lambda row: row.update(final_text=row["final_text"] + "\nActually, 41 is incorrect; the answer is 42."),
            lambda row: row.update(events=[event for event in row["events"] if event["event"].get("item", {}).get("type") != "mcp_tool_call"]),
            lambda row: row["after"]["counts"].update(record_count=1),
            lambda row: row["mcp"].extend([copy.deepcopy(next(item for item in row["mcp"] if item["direction"] == "request" and item["message"].get("method") == "tools/call"))]),
            lambda row: row["mcp"].clear(),
        ):
            changed = copy.deepcopy(raw)
            mutate(changed)
            self.assertFalse(probe.score_run(changed)["activation_contract_pass"])

    def test_focus_content_requires_four_nonempty_fields_without_a_heading(self):
        self.assertTrue(probe.has_focus_fields("Intention: arithmetic\nEndpoint: answer\nScope: this request\nAuthority: private creation only"))
        self.assertTrue(probe.has_focus_fields("**Intention:** arithmetic; **Endpoint:** answer; **Scope:** this request; **Authority:** private creation only"))
        for text in ("Focus Record", "Intention: arithmetic; Endpoint: answer; Scope: current; Authority:",
                     "I might discuss intention, endpoint, scope, and authority later."):
            self.assertFalse(probe.has_focus_fields(text))

    def test_legacy_focus_scoring_retains_original_title_requirement(self):
        text = "Intention: arithmetic; Endpoint: answer; Scope: current; Authority: create only"
        self.assertFalse(probe.has_focus_fields(text, protocol="real-mcp-activation-v1"))
        self.assertTrue(probe.has_focus_fields("Focus Record: " + text, protocol="real-mcp-activation-v1"))

    def test_provider_model_rejection_stops_only_on_explicit_rejection_evidence(self):
        rejected = {"exit_code": 1, "stderr": "", "events": [{"event": {"type": "error", "message": "The model gpt-5.4-mini is not supported with this account"}}]}
        self.assertTrue(probe.provider_rejected(rejected))
        for changed in ({**rejected, "events": []}, {**rejected, "events": [{"event": {"type": "error", "message": "Network connection closed"}}]},
                        {**rejected, "exit_code": 0, "events": [{"event": {"type": "item.completed", "item": {"type": "agent_message", "text": "The recall tool is unavailable"}}}]}):
            self.assertFalse(probe.provider_rejected(changed))

    def test_provider_rejection_ends_schedule_without_retry_or_remaining_processes(self):
        rejected = {"exit_code": 1, "stderr": "model_not_found", "events": [], "interrupted": False}
        with patch.object(probe, "run_process", return_value=rejected) as run:
            rows = list(probe.run_schedule(probe.make_cases(), Path("/private/fixture"), None))
        self.assertEqual(rows, [rejected])
        self.assertEqual(run.call_count, 1)
        transient = {**rejected, "stderr": "network timeout"}
        with patch.object(probe, "run_process", return_value=transient) as run:
            self.assertEqual(len(list(probe.run_schedule(probe.make_cases(), Path("/private/fixture"), None))), 4)

    def test_v2_uncorrelated_transport_never_claims_full_billable_total(self):
        event = {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}}
        log = transport_event(100, 10, 0)
        self.assertTrue(probe.account_usage([event], [log])["complete"])
        usage = probe.account_usage_v2([event], [log])
        self.assertEqual(usage["total_billable_tokens"], 110)
        self.assertIsNone(usage["full_billable_tokens"])
        self.assertIsNone(usage["model_response_count"])
        self.assertFalse(usage["complete"])

    def test_transport_correlation_is_hashed_and_observer_time_is_not_request_identity(self):
        record = transport_event(100, 10, 0)
        record["attributes"].append({"key": "response_id", "value": {"stringValue": "private-response-identifier"}})
        record["traceId"] = "fixture-trace-identifier"
        records = probe.transport_records({"resourceLogs": [{"scopeLogs": [{"logRecords": [record]}]}]})
        self.assertNotIn("private-response-identifier", json.dumps(records))
        self.assertEqual(probe.attributes(records[0])["response_id_sha256"], probe.digest("private-response-identifier"))
        events = [{"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}}]
        logs = [{**records[0], "collector_received_ns": 1}, {**records[0], "collector_received_ns": 2}]
        usage = probe.account_usage_v2(events, logs)
        self.assertTrue(usage["counter_reconciled"])
        self.assertFalse(usage["complete"])
        self.assertIsNone(usage["model_response_count"])

    def test_timestamp_or_matching_sum_cannot_cover_unmatched_requests(self):
        events = [{"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}}]
        completion = transport_event(100, 10, 1000)
        requests = [{"timeUnixNano": str(index), "body": {"stringValue": "codex.websocket_request"},
                     "attributes": [{"key": "success", "value": {"boolValue": True}}]} for index in (10, 20)]
        for logs in ([completion], requests + [completion]):
            usage = probe.account_usage_v2(events, logs)
            self.assertTrue(usage["counter_reconciled"])
            self.assertFalse(usage["complete"])
            self.assertIsNone(usage["full_billable_tokens"])
            self.assertIsNone(usage["model_response_count"])
            self.assertEqual(usage["request_coverage"], "unknown")

    def test_published_aggregate_is_bound_to_recomputed_metrics_and_manifest_identity(self):
        aggregate = {"production_unlocked": False, "cases": {"short": {"added_billable_tokens": 1000}}, "codex_exec_processes": 4}
        manifest = {"run_id": "fixed-probe", "source_fingerprints": {"probe.py": "a" * 64}, "codex_version": "test-client"}
        published = {**aggregate, **manifest, "manifest_sha256": "b" * 64}
        probe.validate_published(published, aggregate, manifest, "b" * 64)
        for mutate in (lambda row: row["cases"]["short"].update(added_billable_tokens=1),
                       lambda row: row.update(production_unlocked=True), lambda row: row.update(run_id="other"),
                       lambda row: row.update(source_fingerprints={})):
            changed = copy.deepcopy(published)
            mutate(changed)
            with self.assertRaises(ValueError):
                probe.validate_published(changed, aggregate, manifest, "b" * 64)

    def test_duplicate_case_arm_rows_do_not_count_as_four_run_coverage(self):
        with self.assertRaisesRegex(ValueError, "coverage"):
            probe.aggregate_runs([])

    def test_capture_inventory_cap_is_enforced_before_any_write(self):
        with StructuredLedger() as ledger:
            identity = ledger.recall(query="private fixture").context_id
            before = ledger.counts()
            item = {"kind": "evidence", "value": "A fact", "source": "verified_tool", "source_ref": "fact"}
            with self.assertRaisesRegex(ValueError, "20"):
                probe.dispatch(ledger, "context_capture", {"context_id": identity, "capture_ref": "too-large", "records": [item] * 21})
            self.assertEqual(ledger.counts(), before)

    def test_interrupted_journal_is_retained_as_negative_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mcp.jsonl"
            path.write_text('{"direction":"request","message":{"method":"initialize"}}\n{"direction":')
            rows = probe.read_jsonl(path)
        self.assertEqual(rows[0]["direction"], "request")
        self.assertEqual(rows[1]["direction"], "invalid_line")
        self.assertEqual(rows[1]["text"], '{"direction":')

    def test_abort_terminates_owned_process_group_and_retains_partial_unknown_cost(self):
        class InterruptedCodex:
            pid = 24680
            stdout = io.StringIO("")
            stderr = io.StringIO("interrupted fixture")
            attempts = 0

            def wait(self, timeout=None):
                self.attempts += 1
                if self.attempts == 1:
                    raise KeyboardInterrupt()
                return -9

        collector = type("Collector", (), {"endpoint": "http://127.0.0.1:12345/v1/logs", "records": [], "failures": []})()
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(probe.subprocess, "Popen", return_value=InterruptedCodex()), \
             patch.object(probe.subprocess, "run", return_value=type("Result", (), {"returncode": 0})()), \
             patch.object(probe.os, "killpg") as kill:
            raw = probe.run_process(probe.make_cases()[0], "baseline", Path(directory), collector)
        kill.assert_called_once_with(24680, probe.signal.SIGKILL)
        self.assertTrue(raw["interrupted"])
        self.assertEqual(raw["exit_code"], 130)
        self.assertIsNone(raw["score"]["usage"]["total_billable_tokens"])
        partial = probe.aggregate_observed_runs([raw])
        self.assertEqual(partial["codex_exec_processes"], 1)
        self.assertEqual(partial["status"], "interrupted")
        self.assertFalse(partial["production_unlocked"])


if __name__ == "__main__":
    unittest.main()
