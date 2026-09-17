#!/usr/bin/env python3
"""Synthetic-provider native trace on/off comparison; never sends real credentials.

This private diagnostic activates a version-matched internal trace facility under
explicit experimental authorization. It is not a supported production setting.
"""
import argparse
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

import activation_probe as activation
import batching_probe as batching

HERE, ROOT = batching.HERE, batching.ROOT
MODEL = "gpt-5.4-mini"
VERSION = "codex-cli 0.153.4"
CANARY = "SYNTHETIC_ONLY_TRACE_AUTH_CANARY_46d4cbf9"
PROMPT = "Offline instrumentation fixture. Discover both native recall tools; retrieve independent Memory and exact Context data; return the fixture answer. No ordinary actions."
RUNTIME_KEYS = {"session_id", "thread_id", "turn_id", "root_turn_id", "turn_started_at_unix_ms", "prompt_cache_key"}
CORRELATION_HEADERS = {"x-codex-inference-call-id", "session_id", "x-client-request-id", "traceparent", "tracestate"}
METADATA_HEADERS = {"x-codex-turn-metadata"}
NORMALIZATION = ["explicit session_id/thread_id/turn_id/root_turn_id/turn_started_at_unix_ms and prompt_cache_key runtime fields",
                 "declared x-codex-inference-call-id, native session/request/trace correlation headers",
                 "HTTP Content-Length framing recalculated after runtime-ID normalization",
                 "native tool_search_output item ID (not its schemas, call ID, or tool arguments)",
                 "MCP _meta runtime IDs/progress token and declared codex_bridge_mcp_call_id; semantic name/arguments/results remain exact"]


def private_environment(root, inherited):
    # An allowlist prevents an unknown credential variable from escaping.
    result = {key: inherited[key] for key in ("PATH", "LANG", "LC_ALL", "TZ") if key in inherited}
    result.update(HOME=str(root / "home"), CODEX_HOME=str(root / "home"), TMPDIR=str(root / "tmp"),
                  XDG_CONFIG_HOME=str(root / "xdg-config"), XDG_CACHE_HOME=str(root / "xdg-cache"),
                  XDG_DATA_HOME=str(root / "xdg-data"), OFFLINE_TRACE_SYNTHETIC_KEY=CANARY,
                  PYTHONDONTWRITEBYTECODE="1")
    return result


def memory_arguments():
    return {"event_id": "trace-memory", "raw_input": PROMPT, "repository": "trace-fixture", "language": "text", "surface": "conversation",
            "project_kind": "diagnostic", "current": {"action": "discuss", "tools": [], "steps": [], "skills": []},
            "output_signals": [], "consumer_agent": "codex"}


def response_items(stage, context_id):
    if stage == 1:
        return [{"type": "tool_search_call", "id": "tsc_fixture", "call_id": "call-search", "execution": "client", "status": "completed",
                 "arguments": {"query": "memory_recall context_recall nerd-memory-tools nerd-context", "limit": 6}}]
    if stage == 2:
        return [{"type": "function_call", "id": "fc_memory", "call_id": "call-memory", "name": "memory_recall", "namespace": "mcp__nerd_memory_tools",
                 "arguments": json.dumps(memory_arguments(), separators=(",", ":")), "status": "completed"},
                {"type": "function_call", "id": "fc_context", "call_id": "call-context", "name": "context_recall", "namespace": "mcp__nerd_context",
                 "arguments": json.dumps({"context_id": context_id, "query": PROMPT, "activation_ref": "trace-context"}, separators=(",", ":")), "status": "completed"}]
    return [{"type": "message", "id": "msg_fixture", "role": "assistant", "status": "completed",
             "content": [{"type": "output_text", "text": "Fixture answer: maple lane.", "annotations": []}]}]


def response_bytes(stage, context_id):
    items = response_items(stage, context_id)
    response = {"id": "resp_fixture_" + str(stage), "object": "response", "created_at": 1, "status": "in_progress", "model": MODEL, "output": []}
    events = [{"type": "response.created", "response": response}]
    for index, item in enumerate(items):
        events.append({"type": "response.output_item.added", "output_index": index, "item": {**item, "status": "in_progress"}})
        if item["type"] == "message":
            events.append({"type": "response.output_text.delta", "item_id": item["id"], "output_index": index, "content_index": 0, "delta": item["content"][0]["text"]})
        events.append({"type": "response.output_item.done", "output_index": index, "item": item})
    events.append({"type": "response.completed", "response": {**response, "status": "completed", "output": items,
                   "usage": {"input_tokens": 10 * stage, "output_tokens": 2, "total_tokens": 10 * stage + 2}}})
    return "".join("event: " + event["type"] + "\ndata: " + json.dumps(event) + "\n\n" for event in events).encode()


def normalized(value, path=()):
    if isinstance(value, list):
        return [normalized(item, path + (str(index),)) for index, item in enumerate(value)]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in RUNTIME_KEYS and ("metadata" in path or key == "prompt_cache_key" or "internal_chat_message_metadata_passthrough" in path):
                result[key] = "<runtime:" + key + ">"
            elif key == "id" and value.get("type") == "tool_search_output":
                result[key] = "<runtime:tool_search_output_id>"
            else:
                result[key] = normalized(item, path + (key,))
        return result
    return value


def request_comparison(off, on):
    def normalize_request(row):
        headers = {}
        for key, value in row["headers"].items():
            key = key.lower()
            if key in CORRELATION_HEADERS or key == "content-length":
                continue
            if key in METADATA_HEADERS:
                try:
                    value = normalized(json.loads(value), ("metadata",))
                except ValueError:
                    pass
            headers[key] = value
        return {"body": normalized(row["body"]), "headers": headers}
    a, b = [normalize_request(row) for row in off], [normalize_request(row) for row in on]
    differences = []
    if len(a) != len(b):
        differences.append({"path": "request_count", "off": len(a), "on": len(b)})
    def compare(left, right, path):
        if type(left) is not type(right):
            differences.append({"path": path, "off_sha256": batching.digest(left), "on_sha256": batching.digest(right)})
        elif isinstance(left, dict):
            for key in sorted(set(left) | set(right)):
                if key not in left or key not in right:
                    differences.append({"path": path + "." + key, "missing_side": "off" if key not in left else "on"})
                else:
                    compare(left[key], right[key], path + "." + key)
        elif isinstance(left, list):
            if len(left) != len(right):
                differences.append({"path": path + ".length", "off": len(left), "on": len(right)})
            for index, (x, y) in enumerate(zip(left, right)):
                compare(x, y, path + "[" + str(index) + "]")
        elif left != right:
            differences.append({"path": path, "off_sha256": batching.digest(left), "on_sha256": batching.digest(right)})
    for index, (left, right) in enumerate(zip(a, b)):
        compare(left, right, "requests[" + str(index) + "]")
    return {"differences": differences, "normalized_off_sha256": batching.digest(a), "normalized_on_sha256": batching.digest(b), "normalization": NORMALIZATION}


def source_fingerprints():
    paths = [HERE / "trace_probe.py", HERE / "test_trace_probe.py"] + batching.source_paths()
    return {str(path.relative_to(ROOT)): batching.digest(path.read_bytes()) for path in paths}


def run(output):
    if batching.hook_probe.detect_client_version() != VERSION:
        raise ValueError("exact audited native version required")
    output = output.resolve()
    old_umask = os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(output, 0o700)
    sources = source_fingerprints()
    for name in sources:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    case = batching.cases()[1]
    requests, responses, server_errors = [], [], []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                if self.path != "/v1/responses" or self.headers.get("Authorization") != "Bearer " + CANARY:
                    raise ValueError("unexpected endpoint/authentication; no forwarding exists")
                requests.append({"path": self.path, "body": body, "headers": dict(self.headers.items())})
                if len(requests) > 3:
                    raise ValueError("scripted native request budget exceeded")
                response = response_bytes(len(requests), case["context_id"])
                responses.append(response.decode())
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)
            except (ValueError, TypeError) as error:
                server_errors.append(str(error))
                self.send_response(400)
                self.end_headers()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    results = []
    try:
        for enabled in (False, True):
            arm = "on" if enabled else "off"
            requests.clear()
            responses.clear()
            server_errors.clear()
            runtime = output / "runtime"
            setup = batching.prepare(runtime, case, "context", "http://127.0.0.1:9", authenticate=False)
            (runtime / "tmp").mkdir()
            # Explicit authorization for exact private audit/read tools, identical
            # off/on. Other tools stay visible but prompt under policy never.
            config = setup["config"].replace('[mcp_servers.nerd-context]', 'default_tools_approval_mode="prompt"\n[mcp_servers.nerd-memory-tools.tools.memory_recall]\napproval_mode="approve"\n[mcp_servers.nerd-context]')
            config += 'default_tools_approval_mode="prompt"\n[mcp_servers.nerd-context.tools.context_recall]\napproval_mode="approve"\n'
            (setup["workspace"] / ".codex/config.toml").write_text(config)
            # Keep this instrumentation workload small: actual separate MCP
            # servers and native discovery, with no Smart behavior claim.
            (setup["workspace"] / ".codex/hooks.json").unlink()
            environment = private_environment(runtime, os.environ)
            trace_root = output / "native-trace"
            if enabled:
                trace_root.mkdir(mode=0o700)
                environment["CODEX_ROLLOUT_TRACE_ROOT"] = str(trace_root)
            endpoint = "http://127.0.0.1:" + str(server.server_port)
            command = ["codex", "exec", "--json", "--strict-config", "--ignore-rules", "--sandbox", "workspace-write", "-C", str(setup["workspace"]),
                       "--model", MODEL, "-c", 'model_reasoning_effort="low"', "-c", 'approval_policy="never"',
                       "-c", 'model_provider="offline-trace"', "-c", 'model_providers.offline-trace.name="Synthetic local trace fixture"',
                       "-c", 'model_providers.offline-trace.base_url=' + json.dumps(endpoint + "/v1"),
                       "-c", 'model_providers.offline-trace.env_key="OFFLINE_TRACE_SYNTHETIC_KEY"',
                       "-c", 'model_providers.offline-trace.requires_openai_auth=false', "-c", 'model_providers.offline-trace.wire_api="responses"',
                       "-c", 'features.enable_request_compression=false', PROMPT]
            start = time.monotonic_ns()
            process = batching.execute_process(command, setup["workspace"], environment, timeout=30)
            elapsed = (time.monotonic_ns() - start) / 1e9
            raw = {"arm": arm, "command": command, "environment": environment, "config": config, "client_version": VERSION,
                   "source_fingerprints": sources, "requests": copy.deepcopy(requests), "synthetic_responses": list(responses),
                   "server_errors": list(server_errors), "elapsed_seconds": elapsed, **process,
                   "memory_after": batching.memory_snapshot(setup["memory_db"]), "context_before": setup["before_context"],
                   "context_after": activation.snapshot(setup["context_db"]), "context_mcp": activation.read_jsonl(setup["state"] / "context-mcp.jsonl")}
            batching.write_json(output / (arm + ".json"), raw)
            results.append(raw)
            shutil.rmtree(runtime)
        trace_files = [path for path in (output / "native-trace").rglob("*") if path.is_file()]
        comparison = request_comparison(results[0]["requests"], results[1]["requests"])
        trace_audit = [{"path": str(path.relative_to(output)), "sha256": batching.digest(path.read_bytes()), "bytes": path.stat().st_size,
                        "synthetic_auth_canary_occurrences": path.read_bytes().count(CANARY.encode())} for path in trace_files]
        aggregate = {"protocol": "native-rollout-trace-offline-v1", "live_model_requests": 0, "synthetic_provider_only": True,
                     "source_set_sha256": batching.digest(sources), "comparison": comparison, "trace_files": trace_audit,
                     "runs": [{"arm": row["arm"], "elapsed_seconds": row["elapsed_seconds"], "exit_code": row["exit_code"],
                               "request_count": len(row["requests"]), "native_calls": [event["event"]["item"].get("tool") for event in row["events"] if event["event"].get("type") == "item.completed" and event["event"].get("item", {}).get("type") == "mcp_tool_call"],
                               "memory_audits": len(row["memory_after"]["recall_events"]), "server_errors": row["server_errors"]} for row in results],
                     "limitations": ["Internal version-matched experimental trace facility; not a documented production setting.",
                                     "HTTP synthetic provider differs from authenticated ChatGPT websocket transport.",
                                     "Scripted outputs establish instrumentation behavior, not model quality or task economics.",
                                     "No inference charge or complete warmup/billing coverage is established.",
                                     "Canary inspection is fixture-specific; no general trace redaction guarantee."]}
        batching.write_json(output / "aggregate.json", aggregate)
        if sources != source_fingerprints():
            raise ValueError("sources changed during offline comparison")
        manifest = {"protocol": aggregate["protocol"], "source_fingerprints": sources,
                    "files": {str(path.relative_to(output)): batching.digest(path.read_bytes()) for path in output.rglob("*") if path.is_file()}}
        batching.write_json(output / "manifest.json", manifest)
        print(json.dumps({"root": str(output), "manifest_sha256": batching.digest((output / "manifest.json").read_bytes()), "differences": len(comparison["differences"]), "runs": aggregate["runs"]}))
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
        os.umask(old_umask)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    run(parser.parse_args().output_root)
