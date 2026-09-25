#!/usr/bin/env python3
"""Measure 36 native Python allocation processes; no Codex or model calls.

Component timing includes interpreter startup, SQLite initialization/commit,
journal fsync, response serialization and process exit. It excludes native
Codex hook dispatch/registration/receipt delivery and cannot pass a user gate.
"""

import hashlib
import json
import math
from pathlib import Path
import secrets
import subprocess
import sys
import time

from hook_allocation import PROTOCOL as ALLOCATION_PROTOCOL, digest, strict_object
from structured import StructuredLedger


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROTOCOL = "nerd-context-empty-allocation-component-latency-v1"
SAMPLES = 36


def fingerprints():
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in (
        "allocation_latency.py", "hook_allocation.py", "test_hook_allocation.py", "structured.py")}


def run():
    sources = fingerprints()
    root = REPO / "benchmarks/results/nerd-context" / (
        "empty-allocation-latency-" + time.strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(5))
    root.mkdir(parents=True, mode=0o700)
    state = root / "state"
    state.mkdir(mode=0o700)
    database, journal = state / "context.sqlite3", state / "hooks.jsonl"
    snapshot = root / "source-snapshot"
    snapshot.mkdir(mode=0o700)
    for name in sources:
        (snapshot / name).write_bytes((HERE / name).read_bytes())
    protocol = {
        "protocol": PROTOCOL, "allocation_protocol": ALLOCATION_PROTOCOL,
        "samples": SAMPLES, "model_calls": 0, "source_fingerprints": sources,
        "python": sys.version, "python_executable": sys.executable,
        "schedule": "36 distinct synthetic turn IDs, same parent session/current text; first database cold, remaining warm",
        "timing": "parent monotonic immediately before Popen through communicate exit; includes Python startup+SQLite+commit+journal fsync+exit",
        "limitations": "Synthetic native-shaped payload; no Codex dispatch, registration, model receipt delivery, delegation proof, or gate claim.",
    }
    (root / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    rows, seen = [], set()
    for index in range(SAMPLES):
        if fingerprints() != sources:
            raise ValueError("allocation measurement sources changed")
        payload = {"hook_event_name": "UserPromptSubmit", "session_id": "component-parent-session",
                   "turn_id": f"component-turn-{index + 1}", "prompt": "What is 17 + 25?",
                   "cwd": str(state), "model": "gpt-5.6-terra", "permission_mode": "never", "transcript_path": None}
        command = [sys.executable, str(HERE / "hook_allocation.py"),
                   "--database", str(database), "--journal", str(journal)]
        started = time.monotonic_ns()
        result = subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True, timeout=10)
        elapsed = (time.monotonic_ns() - started) / 1e6
        observations = [json.loads(line, object_pairs_hook=strict_object) for line in journal.read_text().splitlines()]
        observed = observations[-1] if observations else {}
        allocated = observed.get("result", {})
        with StructuredLedger(database=database) as ledger:
            counts = ledger.counts()
        try:
            response = json.loads(result.stdout, object_pairs_hook=strict_object)
        except ValueError:
            response = None
        valid = (result.returncode == 0 and allocated.get("status") == "created"
                 and allocated.get("context_id") not in seen and len(observations) == index + 1
                 and counts == {"context_count": index + 1, "record_count": 0, "capture_count": 0}
                 and observed.get("response_sha256") == digest(response)
                 and allocated.get("context_id", "MISSING") in result.stdout)
        seen.add(allocated.get("context_id"))
        rows.append({"sample": index + 1, "command": command, "payload": payload,
                     "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                     "elapsed_ms": elapsed, "observation": observed, "counts": counts, "valid": valid})
        (root / "raw.json").write_text(json.dumps(rows, indent=2) + "\n")
        if not valid:
            break
    if fingerprints() != sources:
        raise ValueError("allocation measurement sources changed; observations retained")
    times = sorted(row["elapsed_ms"] for row in rows)
    result = {"protocol": PROTOCOL, "root": str(root), "sample_count": len(rows), "model_calls": 0,
              "all_samples_valid": len(rows) == SAMPLES and all(row["valid"] for row in rows),
              "component_ms": {"minimum": min(times), "median": (times[(len(times)-1)//2]+times[len(times)//2])/2,
                               "p95_nearest_rank": times[math.ceil(.95 * len(times)) - 1], "maximum": max(times),
                               "first_cold_sample": rows[0]["elapsed_ms"]},
              "allocation_count": len(seen), "gate_result": "not_evaluated"}
    (root / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    manifest = {"protocol_sha256": digest(protocol), "source_fingerprints": sources,
                "files": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in root.rglob("*") if path.is_file()}}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_samples_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
