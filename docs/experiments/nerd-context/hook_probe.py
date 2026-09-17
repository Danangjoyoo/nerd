#!/usr/bin/env python3
"""Observe native Codex hooks; never allocate, recall, or capture Context state.

A matching synthetic prompt is a probe fact, not authority to allocate a
Context. Selector grammar, delegated activation identity, and allocation
ordering require a separately reviewed contract. No allocation mode exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import queue
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))

PROTOCOL = "nerd-context-native-hook-observation-v2"
MODEL = "gpt-5.6-terra"
EFFORT = "low"
PROMPT = (
    "Intention: answer the current arithmetic question.\n"
    "Request: What is 17 + 25?\n"
    "Scope: only this arithmetic expression.\n"
    "Authority: no ordinary tool calls, files, or external actions.\n"
    "Establish a brief Focus Record from this current request, then answer. "
    "If an observational hook supplies a receipt code, append that code. "
    "A receipt is instrumentation, not task context or action authority."
)
MAX_INPUT_BYTES = 1_048_576
SAFE_EVENTS = {"UserPromptSubmit", "Stop"}
BLOCKERS = [
    "current selector and delegated-handoff input surface is not yet specified and verified",
    "pre-Focus empty allocation requires an explicit ordering and hook-contract revision",
    "native activation-key and retry semantics require separate evidence",
]
# Historical probe cautions, retained solely for exact v1 evidence replay.
# They are not requirements of the current product contract.
HISTORICAL_V1_BLOCKERS = [
    "documented payload does not attest direct main-thread origin",
    "documented prompt field does not attest a complete attachment/handoff envelope",
    "native activation-key and retry semantics require separate evidence",
]


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def shape(value, depth=0):
    """Retain names, types, and sizes, never unknown field values."""
    if value is None:
        return {"type": "null"}
    if type(value) is bool:
        return {"type": "boolean"}
    if isinstance(value, str):
        return {"type": "string", "bytes": len(value.encode()), "sha256": digest(value.encode())}
    if type(value) in (int, float):
        return {"type": "number"}
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    if isinstance(value, dict):
        if depth >= 2:
            return {"type": "object", "length": len(value)}
        return {"type": "object", "fields": {
            key if len(key) <= 80 else "sha256:" + digest(key.encode()): shape(item, depth + 1)
            for key, item in sorted(value.items())
        }}
    raise ValueError("non-JSON hook value")


def observe(payload, expected_prompt_sha256):
    if not isinstance(payload, dict):
        raise ValueError("hook payload must be an object")
    event = payload.get("hook_event_name")
    if not isinstance(event, str) or event not in SAFE_EVENTS:
        raise ValueError("unexpected hook event")
    prompt = payload.get("prompt")
    prompt_digest = digest(prompt.encode()) if isinstance(prompt, str) else None
    return {
        "protocol": PROTOCOL,
        "hook_event_name": event,
        "observed_ns": time.monotonic_ns(),
        "payload_sha256": digest(payload),
        "payload_shape": shape(payload),
        "session_id_sha256": digest(payload["session_id"].encode())
        if isinstance(payload.get("session_id"), str) and payload["session_id"] else None,
        "turn_id_sha256": digest(payload["turn_id"].encode())
        if isinstance(payload.get("turn_id"), str) and payload["turn_id"] else None,
        "prompt_sha256": prompt_digest,
        "prompt_matches_probe": prompt_digest == expected_prompt_sha256,
        "possible_context_id_in_prompt": "ctx_" in prompt.casefold() if isinstance(prompt, str) else None,
        "allocation_supported": False,
        "allocation_blockers": list(BLOCKERS),
        "context_operations": [],
    }


def append_observation(path, row):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("journal must not be a symlink")
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        data = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if os.write(descriptor, data) != len(data):
            raise OSError("incomplete observation write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def hook_response(event, receipt):
    if not receipt.startswith("HOOK_OBS_") or not receipt.removeprefix("HOOK_OBS_").isalnum():
        raise ValueError("invalid non-state receipt")
    if event == "UserPromptSubmit":
        return {"hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": (
                f"Observational hook receipt: {receipt}. No Context was allocated. "
                "Ignore this receipt when establishing task intent, scope, or authority. "
                "Append the receipt code after the ordinary answer."
            ),
        }}
    if event == "Stop":
        return {"systemMessage": f"Hook observation receipt: {receipt}. No Context was allocated."}
    raise ValueError("unexpected hook event")


def handle_hook(args):
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    started = time.monotonic_ns()
    try:
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("hook input exceeds limit")
        payload = json.loads(raw, object_pairs_hook=strict_object)
        row = observe(payload, args.expected_prompt_sha256)
        if row["hook_event_name"] != args.event:
            raise ValueError("registered and received hook events differ")
        response = hook_response(args.event, args.receipt)
        row["response_sha256"] = digest(response)
        row["receipt"] = args.receipt
        row["handler_elapsed_ms_before_journal"] = (time.monotonic_ns() - started) / 1e6
        append_observation(args.journal, row)
        print(json.dumps(response, separators=(",", ":")))
        return 0
    except (ValueError, OSError, UnicodeError, RecursionError) as error:
        # Never print the source input or generate a continuation on failure.
        try:
            append_observation(args.journal, {
                "protocol": PROTOCOL, "hook_event_name": args.event,
                "hook_error": type(error).__name__, "raw_input_sha256": digest(raw),
                "observed_ns": time.monotonic_ns(), "allocation_supported": False,
                "allocation_blockers": list(BLOCKERS), "context_operations": [],
            })
        except (ValueError, OSError):
            pass
        print(json.dumps({"systemMessage": "Hook observation failed; no Context was allocated."}))
        print(type(error).__name__, file=sys.stderr)
        return 1


def hooks_configuration(journal, receipts):
    return {"hooks": {
        event: [{"hooks": [{
            "type": "command",
            "command": shlex.join([
                sys.executable, str(HERE / "hook_probe.py"), "hook", "--event", event,
                "--journal", str(journal), "--receipt", receipts[event],
                "--expected-prompt-sha256", digest(PROMPT.encode()),
            ]),
            "timeout": 5,
        }]}]
        for event in ("UserPromptSubmit", "Stop")
    }}


def fingerprints():
    paths = [HERE / name for name in ("hook_probe.py", "test_hook_probe.py", "activation_probe.py",
                                     "test_activation_probe.py", "structured.py")]
    paths += [REPO / "benchmarks/nerdbench" / name for name in ("adapters.py", "models.py")]
    return {str(path.relative_to(REPO)): digest(path.read_bytes()) for path in paths}


def detect_client_version():
    result = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=10, check=False)
    version = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"codex-cli [0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", version):
        raise ValueError("installed Codex version could not be established")
    return version


def protocol_record(client_version):
    return {
        "protocol": PROTOCOL, "model": MODEL, "reasoning_effort": EFFORT,
        "client_version": client_version,
        "prompt": PROMPT, "source_fingerprints": fingerprints(),
        "process_runs": 2, "arms": ["baseline", "observed_hooks"],
        "metadata_only_processes": 2,
        "registration": "isolated CODEX_HOME/config.toml contains only explicit project trust; project .codex/hooks.json",
        "registration_preflight": "initialize, config/read, hooks/list only; both arms must match exact frozen definitions before any model process",
        "private_config_template": '[projects."<workspace>"]\ntrust_level = "trusted"\n',
        "hook_trust": "one-off reviewed definitions via --dangerously-bypass-hook-trust",
        "hook_documentation": "https://learn.chatgpt.com/docs/hooks",
        "permissions": "ordinary workspace-write sandbox and approval_policy=never; no sandbox or action-authority bypass",
        "observations": "UserPromptSubmit payload shape, extra-context receipt, Stop payload and event-stream receipt",
        "allocation_supported": False, "allocation_blockers": BLOCKERS,
        "claim_boundary": "native hook capability only; not allocation, ID parsing, lifecycle parity, UI proof, or a gate result",
    }


def command_for(workspace, endpoint):
    return [
        "codex", "exec", "--ephemeral", "--json", "--ignore-rules",
        "--strict-config", "--sandbox", "workspace-write", "-C", str(workspace),
        "--dangerously-bypass-hook-trust", "--model", MODEL,
        "-c", 'approval_policy="never"', "-c", f'model_reasoning_effort="{EFFORT}"',
        "-c", 'otel.environment="nerd-context-hook-observation"',
        "-c", "otel.exporter={otlp-http={endpoint=" + json.dumps(endpoint) + ',protocol="json"}}',
        "-c", "otel.log_user_prompt=false", PROMPT,
    ]


def private_config(workspace):
    return '[projects.' + json.dumps(str(workspace)) + ']\ntrust_level = "trusted"\n'


def registration_inputs(root):
    paths = [root / "home/config.toml", root / "workspace/.codex/config.toml"]
    hook_path = root / "workspace/.codex/hooks.json"
    if hook_path.exists():
        paths.append(hook_path)
    return {str(path.relative_to(root)): digest(path.read_bytes()) for path in paths}


def inspect_registration(workspace, environment):
    """Native metadata RPCs only: never create a thread or submit a turn."""
    command = ["codex", "app-server", "--strict-config", "--listen", "stdio://"]
    started = time.monotonic_ns()
    process = subprocess.Popen(command, cwd=workspace, env=environment, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               start_new_session=True)
    received, errors = queue.Queue(), []
    def read_stdout():
        for line in process.stdout:
            received.put(line)
        received.put(None)
    stdout_thread = threading.Thread(target=read_stdout)
    stderr_thread = threading.Thread(target=lambda: errors.append(process.stderr.read()))
    stdout_thread.start()
    stderr_thread.start()
    requests = []
    def rpc(identifier, method, params):
        request = {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
        requests.append(request)
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            line = received.get(timeout=max(0.001, deadline - time.monotonic()))
            if line is None:
                raise ValueError("metadata process ended before response")
            message = json.loads(line, object_pairs_hook=strict_object)
            if message.get("id") == identifier:
                if "error" in message or not isinstance(message.get("result"), dict):
                    raise ValueError("metadata RPC failed")
                return message["result"]
        raise ValueError("metadata RPC timed out")
    result = {"command": command, "requests": requests, "inference_requests": 0}
    try:
        rpc(1, "initialize", {"clientInfo": {"name": "nerd-hook-observer", "version": "2"},
                              "capabilities": {"experimentalApi": True}})
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "initialized"}) + "\n")
        process.stdin.flush()
        config = rpc(2, "config/read", {"cwd": str(workspace), "includeLayers": True})
        result["config_layers"] = [{"name": layer.get("name"), "disabledReason": layer.get("disabledReason"),
                                    "config_keys": sorted(layer.get("config", {}))}
                                   for layer in config.get("layers", [])]
        result["hooks_list"] = rpc(3, "hooks/list", {"cwds": [str(workspace)]})
    except (ValueError, OSError, queue.Empty) as error:
        result["error"] = type(error).__name__ + ": " + str(error)
    finally:
        process.stdin.close()
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        stdout_thread.join()
        stderr_thread.join()
        process.stdout.close()
        process.stderr.close()
    result["stderr"] = "".join(errors)
    result["elapsed_ms"] = (time.monotonic_ns() - started) / 1e6
    return result


def registration_issues(metadata, workspace, configuration):
    issues = []
    if metadata.get("error"):
        issues.append("native metadata request failed")
    layers = [layer for layer in metadata.get("config_layers", [])
              if isinstance(layer.get("name"), dict) and layer["name"].get("type") == "project"
              and layer["name"].get("dotCodexFolder") == str(workspace / ".codex")]
    if len(layers) != 1 or layers[0].get("disabledReason") is not None:
        issues.append("expected project layer is not active")
    data = metadata.get("hooks_list", {}).get("data", [])
    if len(data) != 1 or data[0].get("cwd") != str(workspace):
        return issues + ["unexpected hooks/list workspace"]
    listing = data[0]
    if listing.get("warnings") or listing.get("errors"):
        issues.append("hooks/list reported warnings or errors")
    expected = []
    for event, groups in (configuration or {}).get("hooks", {}).items():
        for group in groups:
            for handler in group["hooks"]:
                expected.append((event[0].lower() + event[1:], handler["command"], handler["timeout"]))
    actual = []
    for hook in listing.get("hooks", []):
        if (hook.get("handlerType") != "command" or hook.get("enabled") is not True
                or hook.get("async") is not False or hook.get("matcher") is not None
                or hook.get("source") != "project" or hook.get("isManaged") is not False
                or hook.get("sourcePath") != str(workspace / ".codex/hooks.json")
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(hook.get("currentHash")))):
            issues.append("unexpected hook definition metadata")
        actual.append((hook.get("eventName"), hook.get("command"), hook.get("timeoutSec")))
    if sorted(actual) != sorted(expected):
        issues.append("native hooks differ from exact reviewed definitions")
    return issues


def prepare_runtime(arm, root, collector):
    workspace, home, state = (root / name for name in ("workspace", "home", "state"))
    for directory in (workspace, home, state):
        directory.mkdir(parents=True, mode=0o700)
    (workspace / ".codex").mkdir(mode=0o700)
    (workspace / ".codex/config.toml").write_text("# Native project-hook observation only.\n")
    config_text = private_config(workspace)
    (home / "config.toml").write_text(config_text)
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True, capture_output=True)
    original_codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    auth = original_codex_home / "auth.json"
    if auth.is_file():
        (home / "auth.json").symlink_to(auth)
    journal = state / "hooks.jsonl"
    receipts = {event: "HOOK_OBS_" + secrets.token_hex(12) for event in SAFE_EVENTS}
    configuration = hooks_configuration(journal, receipts) if arm == "observed_hooks" else None
    if configuration:
        (workspace / ".codex/hooks.json").write_text(json.dumps(configuration, indent=2))
    environment = os.environ.copy()
    environment.update({"HOME": str(home), "CODEX_HOME": str(home)})
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "TMPDIR", "TMP", "TEMP"):
        environment[key] = str(home / key.lower()) if key.startswith("XDG_") else str(home)
    for key in ("NERD_CONTEXT_DB", "NERD_MEMORY_DB"):
        environment.pop(key, None)
    metadata = inspect_registration(workspace, environment)
    metadata["issues"] = registration_issues(metadata, workspace, configuration)
    metadata["input_fingerprints"] = registration_inputs(root)
    metadata["private_config_text"] = config_text
    metadata["project_hook_configuration"] = configuration
    return {"workspace": workspace, "environment": environment, "journal": journal, "receipts": receipts,
            "configuration": configuration, "metadata": metadata,
            "command": command_for(workspace, collector.endpoint)}


def remove_runtime_home(root):
    home = root / "home"
    if home.is_symlink():
        home.unlink()
    elif home.exists():
        shutil.rmtree(home)


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(line, object_pairs_hook=strict_object) for line in path.read_text().splitlines() if line]


def summarize_run(row):
    from activation_probe import account_usage, account_usage_v2
    usage_function = account_usage if row.get("protocol") == "nerd-context-native-hook-observation-v1" else account_usage_v2
    observations = row["hook_observations"]
    upstream = [item for item in observations if item["hook_event_name"] == "UserPromptSubmit"]
    stops = [item for item in observations if item["hook_event_name"] == "Stop"]
    expected = row["arm"] == "observed_hooks"
    receipt = row["receipts"]["UserPromptSubmit"]
    exact_prompt = bool(upstream) and all(item.get("prompt_matches_probe", False) for item in upstream)
    bound = bool(upstream) and all(item.get("session_id_sha256") and item.get("turn_id_sha256") for item in upstream)
    actions = sorted({item["event"].get("item", {}).get("type") for item in row["events"]
                      if item["event"].get("item", {}).get("type") in {
                          "command_execution", "file_change", "web_search", "collab_tool_call", "mcp_tool_call"}})
    result = {
        "arm": row["arm"], "client_version": row["client_version"],
        "exit_code": row["exit_code"], "timed_out": row["timed_out"], "interrupted": row["interrupted"],
        "user_prompt_hook_count": len(upstream), "stop_hook_count": len(stops),
        "observed_current_prompt_matches": exact_prompt, "observed_nonempty_activation_keys": bound,
        "prompt_receipt_in_final": receipt in row["final_text"],
        "stop_receipt_in_event_stream": row["receipts"]["Stop"] in row["stdout"] + row["stderr"],
        "expected_hook_presence": bool(upstream and stops) if expected else not observations,
        "hook_errors": [item["hook_error"] for item in observations if "hook_error" in item],
        "ordinary_tool_actions": actions,
        "unexpected_workspace_changes": row["unexpected_workspace_changes"],
        "answer_contains_42": bool(re.search(r"\b42\b", row["final_text"])),
        "usage": usage_function([item["event"] for item in row["events"]], row["telemetry"]),
        "elapsed_ms": row["elapsed_ms"],
        "allocation_supported": False, "allocation_blockers": list(BLOCKERS),
        "verdict": "observation_only",
    }
    if row.get("protocol") == "nerd-context-native-hook-observation-v1":
        result["allocation_blockers"] = list(HISTORICAL_V1_BLOCKERS)
    else:
        result["registration_preflight"] = {
            "issues": row["registration_preflight"]["issues"],
            "elapsed_ms": row["registration_preflight"]["elapsed_ms"],
            "input_fingerprints": row["registration_preflight"]["input_fingerprints"],
        }
    return result


def run_process(arm, root, collector, *, client_version, prepared=None):
    try:
        row = _run_process(arm, root, collector, client_version=client_version, prepared=prepared)
    finally:
        remove_runtime_home(root)
    row["runtime_home_removed"] = not (root / "home").exists()
    return row


def _run_process(arm, root, collector, *, client_version, prepared=None):
    from benchmarks.nerdbench.adapters import get_adapter
    prepared = prepared or prepare_runtime(arm, root, collector)
    workspace, command = prepared["workspace"], prepared["command"]
    journal, receipts = prepared["journal"], prepared["receipts"]
    if prepared["metadata"]["issues"]:
        raise ValueError("native registration preflight failed; no model process was run")
    if registration_inputs(root) != prepared["metadata"]["input_fingerprints"]:
        raise ValueError("native registration inputs changed after preflight")
    before_files = {str(path.relative_to(workspace)): digest(path.read_bytes()) for path in workspace.rglob("*")
                    if path.is_file() and ".git" not in path.relative_to(workspace).parts}
    start_index = len(collector.records)
    started = time.monotonic_ns()
    process = subprocess.Popen(command, cwd=workspace, env=prepared["environment"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    observed_lines, errors = [], []
    def read_stdout():
        for line in process.stdout:
            observed_lines.append({"observed_ns": time.monotonic_ns(), "line": line})
    stdout_thread = threading.Thread(target=read_stdout)
    stderr_thread = threading.Thread(target=lambda: errors.append(process.stderr.read()))
    stdout_thread.start()
    stderr_thread.start()
    timed_out, interrupted = False, False
    try:
        exit_code = process.wait(timeout=120)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        exit_code = 124
    except KeyboardInterrupt:
        interrupted = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        exit_code = 130
    stdout_thread.join()
    stderr_thread.join()
    stdout = "".join(item["line"] for item in observed_lines)
    stderr = "".join(errors)
    ended = time.monotonic_ns()
    events = []
    for item in observed_lines:
        try:
            event = json.loads(item["line"])
            if isinstance(event, dict):
                events.append({"observed_ns": item["observed_ns"], "event": event})
        except json.JSONDecodeError:
            pass
    final, _, _ = get_adapter("codex").parse(stdout, stderr)
    after_files = {str(path.relative_to(workspace)): digest(path.read_bytes()) for path in workspace.rglob("*")
                   if path.is_file() and ".git" not in path.relative_to(workspace).parts}
    return {
        "protocol": PROTOCOL, "arm": arm, "model": MODEL, "reasoning_effort": EFFORT,
        "client_version": client_version,
        "command": command, "prompt_sha256": digest(PROMPT.encode()), "receipts": receipts,
        "events": events, "stdout": stdout, "stderr": stderr, "final_text": final,
        "exit_code": exit_code, "timed_out": timed_out, "interrupted": interrupted,
        "elapsed_ms": (ended - started) / 1e6,
        "telemetry": collector.records[start_index:], "telemetry_failures": list(collector.failures),
        "registration_preflight": prepared["metadata"],
        "hook_observations": read_rows(journal),
        "project_hook_configuration": prepared["configuration"],
        "workspace_files": sorted(str(path.relative_to(workspace)) for path in workspace.rglob("*")
                                  if path.is_file() and ".git" not in path.relative_to(workspace).parts),
        "unexpected_workspace_changes": sorted(name for name in before_files.keys() | after_files.keys()
                                               if before_files.get(name) != after_files.get(name)),
        "allocation_supported": False,
    }


def run_probe(args):
    from activation_probe import TelemetryCollector
    protocol = protocol_record(detect_client_version())
    if args.reviewed_protocol_sha256 != digest(protocol):
        raise ValueError("reviewed protocol/source digest does not match; no client was run")
    base = REPO / "benchmarks/results/nerd-context"
    base.mkdir(parents=True, exist_ok=True)
    root = base / ("hook-observation-" + time.strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(5))
    root.mkdir(mode=0o700)
    snapshot = root / "source-snapshot"
    snapshot.mkdir(mode=0o700)
    for relative in protocol["source_fingerprints"]:
        copied = snapshot / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes((REPO / relative).read_bytes())
    (root / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    rows, preflights, prepared = [], {}, {}
    preflight_only = args.command == "preflight"
    with TelemetryCollector() as collector:
        try:
            for arm in ("baseline", "observed_hooks"):
                prepared[arm] = prepare_runtime(arm, root / arm, collector)
                preflights[arm] = prepared[arm]["metadata"]
                (root / "registration-preflights.json").write_text(json.dumps(preflights, indent=2) + "\n")
            if not preflight_only and not any(item["issues"] for item in preflights.values()):
                for arm in ("baseline", "observed_hooks"):
                    if fingerprints() != protocol["source_fingerprints"]:
                        raise ValueError("probe dependencies changed before execution")
                    row = run_process(arm, root / arm, collector, client_version=protocol["client_version"],
                                      prepared=prepared[arm])
                    rows.append(row)
                    (root / (arm + ".json")).write_text(json.dumps(row, indent=2) + "\n")
                    if row["interrupted"]:
                        break
        finally:
            for arm in ("baseline", "observed_hooks"):
                remove_runtime_home(root / arm)
    if fingerprints() != protocol["source_fingerprints"]:
        raise ValueError("probe dependencies changed during execution; raw observations retained")
    result = {"protocol": PROTOCOL, "run_root": str(root), "runs": [summarize_run(row) for row in rows],
              "preflight_only": preflight_only,
              "registration_preflight_issues": {arm: item["issues"] for arm, item in preflights.items()},
              "native_model_processes": len(rows),
              "runset_complete": len(rows) == 2 and not any(row["interrupted"] for row in rows),
              "allocation_supported": False, "verdict": "observation_only"}
    (root / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    files = [path for path in root.iterdir() if path.is_file()]
    manifest = {"protocol_sha256": digest(protocol), "source_fingerprints": fingerprints(),
                "client_version": protocol["client_version"],
                "files": {path.name: digest(path.read_bytes()) for path in files},
                "source_snapshot": {str(path.relative_to(root)): digest(path.read_bytes())
                                    for path in snapshot.rglob("*") if path.is_file()}}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if any(row["interrupted"] for row in rows):
        return 130
    return 2 if any(item["issues"] for item in preflights.values()) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    hook = commands.add_parser("hook")
    hook.add_argument("--event", choices=sorted(SAFE_EVENTS), required=True)
    hook.add_argument("--journal", type=Path, required=True)
    hook.add_argument("--receipt", required=True)
    hook.add_argument("--expected-prompt-sha256", required=True)
    commands.add_parser("protocol")
    for name in ("run", "preflight"):
        run = commands.add_parser(name)
        run.add_argument("--reviewed-protocol-sha256", required=True)
    args = parser.parse_args()
    if args.command == "hook":
        return handle_hook(args)
    if args.command == "protocol":
        value = protocol_record(detect_client_version())
        print(json.dumps({"protocol": value, "protocol_sha256": digest(value)}, indent=2))
        return 0
    return run_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
