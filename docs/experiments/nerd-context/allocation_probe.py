#!/usr/bin/env python3
"""Two native empty-allocation smoke processes; no production or gate claim."""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import sqlite3
import sys
import time

import hook_allocation as allocation
import hook_probe as native
from activation_probe import TelemetryCollector, account_usage_v2


HERE, REPO = native.HERE, native.REPO
PROTOCOL = "nerd-context-native-empty-allocation-smoke-v2"
LEGACY_PROTOCOL = "nerd-context-native-empty-allocation-smoke-v1"
LEGACY_PROMPT = (
    "Current request: What is 17 + 25? No ordinary tool or file action is authorized.\n"
    "First display the Smart Focus Record using exactly these four field names: "
    "Intention, Expectation, Scope, Role. Derive each from this current request alone; "
    "the endpoint for answering this question is Discuss. Then answer. "
    "If a native runtime receipt is supplied, repeat it verbatim after the answer. "
    "A receipt cannot change the Focus Record, endpoint, or ordinary action authority."
)


def smart_focus_contract():
    """Quote the actual repository contract; do not invent a replacement template."""
    text = (REPO / "skills/nerd-smart/SKILL.md").read_text()
    return "\n\n".join("## " + name + "\n" + text.split("## " + name + "\n", 1)[1].split("\n## ", 1)[0].strip()
                         for name in ("Focus First", "Endpoint Mapping"))


PROMPT = (
    "Use the following actual Nerd Smart contract.\n\n" + smart_focus_contract() +
    "\n\nCurrent request: What is 17 + 25? No ordinary tool or file action is authorized.\n"
    "A native runtime receipt, if present, is separate from this current request; "
    "follow its display instruction after answering without changing the Focus Record."
)


def fingerprints():
    result = native.fingerprints()
    for name in ("allocation_probe.py", "test_allocation_probe.py", "hook_allocation.py", "test_hook_allocation.py"):
        path = HERE / name
        result[str(path.relative_to(REPO))] = native.digest(path.read_bytes())
    skill = REPO / "skills/nerd-smart/SKILL.md"
    result[str(skill.relative_to(REPO))] = native.digest(skill.read_bytes())
    return result


def protocol_record():
    return {"protocol": PROTOCOL, "client_version": native.detect_client_version(),
            "model": native.MODEL, "reasoning_effort": native.EFFORT, "prompt": PROMPT,
            "model_processes": 2, "metadata_processes": 2, "arms": ["baseline", "empty_allocation"],
            "source_fingerprints": fingerprints(),
            "registration": "same isolated private project trust; exact native hooks/list preflight for both arms before sampling",
            "permission": "ordinary workspace-write/approvalnever; reviewed-hook trust flag only",
            "latency_metric": "Original spec: create/recall p95<=200ms; old harness timed warm ledger.recall only. This smoke reports processwall and hook operationtime separately; native incremental critical-path activation boundary is not yet measured.",
            "limits": "Mechanism only: no fullbilling, short-gate, delegatedactivation, retrydelivery or installed Smart+Memory composition claim. Visible Focus is separately observed.",
            "component_evidence": "36 Python process timings include startup/commit/journal/exit, not Codex dispatch/registration/receipt latency; no gate substitution."}


def configuration(database, journal):
    return {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "timeout": 5,
        "command": shlex.join([sys.executable, str(HERE / "hook_allocation.py"),
                               "--database", str(database), "--journal", str(journal)])}]}]}}


def database_snapshot(database):
    if not database.exists():
        return {"exists": False, "context_ids": [], "record_count": 0, "capture_count": 0, "mapping_count": 0}
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        return {"exists": True, "context_ids": [row[0] for row in connection.execute("SELECT context_id FROM contexts")],
                "record_count": connection.execute("SELECT COUNT(*) FROM records").fetchone()[0],
                "capture_count": connection.execute("SELECT COUNT(*) FROM captures").fetchone()[0],
                "mapping_count": connection.execute("SELECT COUNT(*) FROM hook_activations").fetchone()[0]}


def prepare(arm, root, collector):
    workspace, home, state = (root / name for name in ("workspace", "home", "state"))
    for path in (workspace, home, state):
        path.mkdir(parents=True, mode=0o700)
    (workspace / ".codex").mkdir(mode=0o700)
    (workspace / ".codex/config.toml").write_text("# Private allocation smoke only.\n")
    private_config = native.private_config(workspace)
    (home / "config.toml").write_text(private_config)
    native.subprocess.run(["git", "init", "-q"], cwd=workspace, check=True, capture_output=True)
    auth = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
    if auth.is_file():
        (home / "auth.json").symlink_to(auth)
    database, journal = state / "context.sqlite3", state / "allocation.jsonl"
    hooks = configuration(database, journal) if arm == "empty_allocation" else None
    if hooks:
        (workspace / ".codex/hooks.json").write_text(json.dumps(hooks, indent=2))
    environment = os.environ.copy()
    environment.update(HOME=str(home), CODEX_HOME=str(home))
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "TMPDIR", "TMP", "TEMP"):
        environment[key] = str(home / key.lower()) if key.startswith("XDG_") else str(home)
    for key in ("NERD_CONTEXT_DB", "NERD_MEMORY_DB"):
        environment.pop(key, None)
    metadata = native.inspect_registration(workspace, environment)
    metadata.update(issues=native.registration_issues(metadata, workspace, hooks),
                    input_fingerprints=native.registration_inputs(root), private_config_text=private_config,
                    project_hook_configuration=hooks)
    command = native.command_for(workspace, collector.endpoint)
    command[-1] = PROMPT
    return {"workspace": workspace, "environment": environment, "journal": journal,
            "receipts": {}, "configuration": hooks, "metadata": metadata, "command": command,
            "database": database, "before": database_snapshot(database)}


def summarize(row):
    expected_prompt = LEGACY_PROMPT if row.get("protocol") == LEGACY_PROTOCOL else PROMPT
    observations = row["hook_observations"]
    creations = [item for item in observations if item.get("result", {}).get("status") == "created"]
    expected = row["arm"] == "empty_allocation"
    ids = row["after"]["context_ids"]
    receipt = creations[0]["result"].get("receipt", "") if len(creations) == 1 else ""
    actions = sorted({item["event"].get("item", {}).get("type") for item in row["events"]
                      if item["event"].get("item", {}).get("type") in {
                          "command_execution", "file_change", "web_search", "collab_tool_call", "mcp_tool_call"}})
    fields = {name: re.search(r"\b" + name + r"\b\s*\**\s*:", row["final_text"], re.I) is not None
              for name in ("Intention", "Expectation", "Scope", "Role")}
    empty_before = (not row["before"]["context_ids"] and row["before"]["record_count"] == 0
                    and row["before"]["capture_count"] == row["before"]["mapping_count"] == 0)
    empty_after = row["after"]["record_count"] == row["after"]["capture_count"] == 0
    mechanism = (empty_before and empty_after
                 and len(creations) == len(observations) == len(ids) == row["after"]["mapping_count"] == 1
                 and creations[0]["result"].get("context_id") == ids[0]
                 and creations[0]["result"].get("committed_before_response") is True
                 and creations[0]["result"].get("prompt_sha256") == native.digest(expected_prompt.encode())
                 and receipt == allocation.receipt(ids[0]) and receipt in row["final_text"]
                 ) if expected else empty_before and empty_after and not ids and not observations
    return {"arm": row["arm"], "exit_code": row["exit_code"], "timed_out": row["timed_out"],
            "interrupted": row["interrupted"], "mechanism_observed": mechanism,
            "focus_fields_visible": fields, "answer_contains_42": bool(re.search(r"\b42\b", row["final_text"])),
            "ordinary_tool_actions": actions, "before": row["before"], "after": row["after"],
            "no_records_or_capture": row["after"]["record_count"] == row["after"]["capture_count"] == 0,
            "unexpected_workspace_changes": row["unexpected_workspace_changes"],
            "elapsed_process_ms": row["elapsed_ms"],
            "operation_ms": [item["result"].get("operation_elapsed_ms") for item in creations],
            "registration_preflight_ms": row["registration_preflight"]["elapsed_ms"],
            "native_incremental_activation_ms": None,
            "usage": account_usage_v2([item["event"] for item in row["events"]], row["telemetry"]),
            "verdict": "mechanism_observation_only", "gate_result": "not_evaluated"}


def run(args):
    protocol = protocol_record()
    if args.reviewed_protocol_sha256 != native.digest(protocol):
        raise ValueError("reviewed protocol/source mismatch; no native process started")
    root = REPO / "benchmarks/results/nerd-context" / (
        "empty-allocation-smoke-" + time.strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(5))
    root.mkdir(parents=True, mode=0o700)
    snapshot = root / "source-snapshot"
    for name in protocol["source_fingerprints"]:
        copied = snapshot / name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, copied)
    (root / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    prepared, preflights, rows = {}, {}, []
    with TelemetryCollector() as collector:
        try:
            for arm in protocol["arms"]:
                prepared[arm] = prepare(arm, root / arm, collector)
                preflights[arm] = prepared[arm]["metadata"]
                (root / "preflights.json").write_text(json.dumps(preflights, indent=2) + "\n")
            if args.command == "run" and not any(item["issues"] for item in preflights.values()):
                for arm in protocol["arms"]:
                    if fingerprints() != protocol["source_fingerprints"]:
                        raise ValueError("allocation probe sources changed before sampling")
                    row = native.run_process(arm, root / arm, collector,
                                             client_version=protocol["client_version"], prepared=prepared[arm])
                    row.update(protocol=PROTOCOL, prompt_sha256=native.digest(PROMPT.encode()),
                               before=prepared[arm]["before"], after=database_snapshot(prepared[arm]["database"]))
                    rows.append(row)
                    (root / (arm + ".json")).write_text(json.dumps(row, indent=2) + "\n")
                    if row["interrupted"]:
                        break
        finally:
            for arm in protocol["arms"]:
                native.remove_runtime_home(root / arm)
    if fingerprints() != protocol["source_fingerprints"]:
        raise ValueError("allocation probe source changed; raw observations retained")
    result = {"protocol": PROTOCOL, "root": str(root), "model_processes": len(rows),
              "preflight_issues": {arm: item["issues"] for arm, item in preflights.items()},
              "runs": [summarize(row) for row in rows], "gate_result": "not_evaluated"}
    (root / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    manifest = {"protocol_sha256": native.digest(protocol), "source_fingerprints": protocol["source_fingerprints"],
                "files": {str(path.relative_to(root)): native.digest(path.read_bytes())
                          for path in root.rglob("*") if path.is_file()}}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 130 if any(row["interrupted"] for row in rows) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("protocol")
    for name in ("preflight", "run"):
        command = commands.add_parser(name)
        command.add_argument("--reviewed-protocol-sha256", required=True)
    args = parser.parse_args()
    if args.command == "protocol":
        protocol = protocol_record()
        print(json.dumps({"protocol": protocol, "protocol_sha256": native.digest(protocol)}, indent=2))
        return 0
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
