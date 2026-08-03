from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fixtures import checks_for, expected_hashes, materialize, patch_for
from tools import canonical_apply


CONFIG_PATH = ROOT / "cases.json"
RAW_PATH = ROOT / "results" / "raw.json"
REPORT_PATH = ROOT / "results" / "report.md"
SERVER_PATH = ROOT / "tool_server.py"


class RpcError(RuntimeError):
    pass


class RpcClient:
    def __init__(self) -> None:
        started = time.perf_counter_ns()
        self.process = subprocess.Popen(
            [sys.executable, str(SERVER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 1
        self.call("ping", {})
        self.startup_ms = (time.perf_counter_ns() - started) / 1_000_000

    def call(self, method: str, params: dict) -> dict:
        if self.process.stdin is None or self.process.stdout is None:
            raise RpcError("tool server pipes are unavailable")
        request_id = self._next_id
        self._next_id += 1
        request = json.dumps(
            {"id": request_id, "method": method, "params": params},
            sort_keys=True,
            separators=(",", ":"),
        )
        request_line = request + "\n"
        started = time.perf_counter_ns()
        self.process.stdin.write(request_line)
        self.process.stdin.flush()
        response_line = self.process.stdout.readline()
        elapsed_ns = time.perf_counter_ns() - started
        if not response_line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read()
            raise RpcError(f"tool server closed unexpectedly: {stderr.strip()}")
        response = json.loads(response_line)
        if response.get("id") != request_id:
            raise RpcError("tool response id mismatch")
        if "error" in response:
            error = response["error"]
            raise RpcError(f"{error['type']}: {error['message']}")
        return {
            "result": response["result"],
            "observed_ns": elapsed_ns,
            "operation_ns": response["operation_ns"],
            "request_bytes": len(request_line.encode("utf-8")),
            "response_bytes": len(response_line.encode("utf-8")),
            "requests": 1,
            "process_count": response["result"].get("process_count", 0),
        }

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                self.call("shutdown", {})
            except (BrokenPipeError, RpcError):
                pass
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()
        self.process.wait(timeout=5)

    def __enter__(self) -> "RpcClient":
        return self

    def __exit__(self, *_args) -> None:
        self.close()


def _inspect_call(client: RpcClient, route: str, case: dict, root: Path) -> dict:
    return client.call(
        f"{route}.inspect",
        {
            "workspace": str(root),
            "symbol": case["symbol"],
            "context_lines": case["context_lines"],
            "max_results": case["max_results"],
        },
    )


def _apply_call(
    client: RpcClient,
    route: str,
    case_id: str,
    root: Path,
) -> dict:
    materialize(case_id, root)
    patch = patch_for(case_id)
    hashes = expected_hashes(case_id, root)
    checks = checks_for(case_id)
    if route == "candidate":
        return client.call(
            "candidate.apply_verify",
            {
                "workspace": str(root),
                "patch": patch,
                "expected_hashes": hashes,
                "checks": checks,
            },
        )
    started = time.perf_counter_ns()
    applied = client.call(
        "baseline.apply_patch",
        {
            "workspace": str(root),
            "patch": patch,
            "expected_hashes": hashes,
        },
    )
    verified = client.call(
        "baseline.verify",
        {
            "workspace": str(root),
            "changed_paths": applied["result"]["changed_paths"],
            "checks": checks,
        },
    )
    observed_ns = time.perf_counter_ns() - started
    result = {
        "patch_status": applied["result"]["patch_status"],
        "changed_paths": applied["result"]["changed_paths"],
        "diff_sha256": verified["result"]["diff_sha256"],
        "checks": verified["result"]["checks"],
        "exit_codes": verified["result"]["exit_codes"],
        "rolled_back": False,
        "process_count": (
            applied["process_count"] + verified["process_count"]
        ),
    }
    return {
        "result": result,
        "observed_ns": observed_ns,
        "operation_ns": applied["operation_ns"] + verified["operation_ns"],
        "request_bytes": applied["request_bytes"] + verified["request_bytes"],
        "response_bytes": applied["response_bytes"] + verified["response_bytes"],
        "requests": 2,
        "process_count": result["process_count"],
    }


def _metric(call: dict) -> dict:
    return {
        "observed_ms": call["observed_ns"] / 1_000_000,
        "operation_ms": call["operation_ns"] / 1_000_000,
        "request_bytes": call["request_bytes"],
        "response_bytes": call["response_bytes"],
        "requests": call["requests"],
        "process_count": call["process_count"],
    }


def _assert_equivalent(kind: str, baseline: dict, candidate: dict) -> None:
    if kind == "inspect":
        left = baseline["result"]["matches"]
        right = candidate["result"]["matches"]
    else:
        left = canonical_apply(baseline["result"])
        right = canonical_apply(candidate["result"])
    if left != right:
        raise AssertionError(
            "baseline and candidate output differ:\n"
            f"baseline={json.dumps(left, sort_keys=True)}\n"
            f"candidate={json.dumps(right, sort_keys=True)}"
        )


def _run_case(
    client: RpcClient,
    kind: str,
    case: dict,
    workspace_root: Path,
    warmups: int,
    samples: int,
    seed: int,
) -> dict:
    case_id = case["id"]
    baseline_root = workspace_root / f"{case_id}-baseline"
    candidate_root = workspace_root / f"{case_id}-candidate"
    if kind == "inspect":
        materialize(case_id, baseline_root)
        materialize(case_id, candidate_root)
        call = lambda route, root: _inspect_call(client, route, case, root)
    else:
        call = lambda route, root: _apply_call(client, route, case_id, root)

    cold_baseline = call("baseline", baseline_root)
    cold_candidate = call("candidate", candidate_root)
    _assert_equivalent(kind, cold_baseline, cold_candidate)

    randomizer = random.Random(seed)
    pairs = []
    total_pairs = warmups + samples
    for pair_index in range(total_pairs):
        order = ["baseline", "candidate"]
        randomizer.shuffle(order)
        calls = {}
        for route in order:
            root = baseline_root if route == "baseline" else candidate_root
            calls[route] = call(route, root)
        _assert_equivalent(kind, calls["baseline"], calls["candidate"])
        if pair_index >= warmups:
            pairs.append(
                {
                    "pair": pair_index - warmups + 1,
                    "order": order,
                    "baseline": _metric(calls["baseline"]),
                    "candidate": _metric(calls["candidate"]),
                }
            )
    return {
        "id": case_id,
        "kind": kind,
        "cold": {
            "baseline": _metric(cold_baseline),
            "candidate": _metric(cold_candidate),
        },
        "pairs": pairs,
    }


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _bootstrap_interval(
    differences: list[float], samples: int, seed: int
) -> tuple[float, float]:
    randomizer = random.Random(seed)
    medians = []
    count = len(differences)
    for _ in range(samples):
        draw = [differences[randomizer.randrange(count)] for _ in range(count)]
        medians.append(statistics.median(draw))
    return _percentile(medians, 0.025), _percentile(medians, 0.975)


def summarize_case(case: dict, bootstrap_samples: int, seed: int) -> dict:
    baseline = [pair["baseline"]["observed_ms"] for pair in case["pairs"]]
    candidate = [pair["candidate"]["observed_ms"] for pair in case["pairs"]]
    differences = [left - right for left, right in zip(baseline, candidate)]
    baseline_p50 = statistics.median(baseline)
    candidate_p50 = statistics.median(candidate)
    baseline_p95 = _percentile(baseline, 0.95)
    candidate_p95 = _percentile(candidate, 0.95)
    lower, upper = _bootstrap_interval(differences, bootstrap_samples, seed)
    speed_percent = (baseline_p50 - candidate_p50) / baseline_p50 * 100
    if candidate_p50 < baseline_p50 and candidate_p95 < baseline_p95 and lower > 0:
        decision = "faster"
    elif (
        candidate_p50 > baseline_p50
        and candidate_p95 > baseline_p95
        and upper < 0
    ):
        decision = "slower"
    else:
        decision = "inconclusive"

    def median_metric(route: str, key: str) -> float:
        return statistics.median(pair[route][key] for pair in case["pairs"])

    return {
        "id": case["id"],
        "kind": case["kind"],
        "samples": len(case["pairs"]),
        "decision": decision,
        "baseline_p50_ms": baseline_p50,
        "candidate_p50_ms": candidate_p50,
        "baseline_p95_ms": baseline_p95,
        "candidate_p95_ms": candidate_p95,
        "speed_percent": speed_percent,
        "median_paired_difference_ms": statistics.median(differences),
        "paired_difference_ci95_ms": [lower, upper],
        "baseline_operation_p50_ms": median_metric("baseline", "operation_ms"),
        "candidate_operation_p50_ms": median_metric("candidate", "operation_ms"),
        "baseline_requests": median_metric("baseline", "requests"),
        "candidate_requests": median_metric("candidate", "requests"),
        "baseline_processes": median_metric("baseline", "process_count"),
        "candidate_processes": median_metric("candidate", "process_count"),
        "baseline_request_bytes": median_metric("baseline", "request_bytes"),
        "candidate_request_bytes": median_metric("candidate", "request_bytes"),
        "baseline_response_bytes": median_metric("baseline", "response_bytes"),
        "candidate_response_bytes": median_metric("candidate", "response_bytes"),
    }


def build_summary(raw: dict) -> list[dict]:
    config = raw["config"]
    return [
        summarize_case(
            case,
            config["bootstrap_samples"],
            config["seed"] + index,
        )
        for index, case in enumerate(raw["cases"])
    ]


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def render_report(raw: dict, summary: list[dict]) -> str:
    lines = [
        "# Inspect and Apply/Verify Tool Latency Results",
        "",
        "This is a tool-only local JSONL RPC benchmark. It contains no LLM, agent,",
        "prompt, or Nerd skill. Fixture setup and resets are excluded from timing.",
        "",
        "| Comparison | Case | Baseline p50 | Custom p50 | Change | Baseline p95 | Custom p95 | Result | Requests |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for item in summary:
        requests = (
            f"{int(item['baseline_requests'])} → "
            f"{int(item['candidate_requests'])}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    item["kind"],
                    item["id"],
                    f"{_fmt(item['baseline_p50_ms'])} ms",
                    f"{_fmt(item['candidate_p50_ms'])} ms",
                    f"{item['speed_percent']:+.2f}%",
                    f"{_fmt(item['baseline_p95_ms'])} ms",
                    f"{_fmt(item['candidate_p95_ms'])} ms",
                    item["decision"],
                    requests,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Proof details",
            "",
        ]
    )
    for item in summary:
        lower, upper = item["paired_difference_ci95_ms"]
        lines.extend(
            [
                f"### {item['id']}",
                "",
                f"- Samples: {item['samples']} valid paired measurements.",
                f"- Median paired saving: {_fmt(item['median_paired_difference_ms'])} ms.",
                f"- 95% bootstrap interval: [{_fmt(lower)}, {_fmt(upper)}] ms.",
                f"- Operation p50: {_fmt(item['baseline_operation_p50_ms'])} ms baseline; {_fmt(item['candidate_operation_p50_ms'])} ms custom.",
                f"- Spawned processes: {int(item['baseline_processes'])} baseline; {int(item['candidate_processes'])} custom.",
                f"- Request bytes: {int(item['baseline_request_bytes'])} baseline; {int(item['candidate_request_bytes'])} custom.",
                f"- Response bytes: {int(item['baseline_response_bytes'])} baseline; {int(item['candidate_response_bytes'])} custom.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "The baseline and custom routes share this experiment's persistent local",
            "JSONL transport. These values demonstrate local operation and orchestration",
            "latency on the recorded host; they do not measure Codex's private built-in",
            "tool transport or prove agent-level speed.",
            "",
        ]
    )
    return "\n".join(lines)


def _command_first_line(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return result.stdout.splitlines()[0] if result.stdout else "unavailable"


def _git_commit() -> str:
    return _command_first_line(["git", "rev-parse", "--short", "HEAD"])


def run() -> dict:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="inspect-apply-verify-") as temporary:
        workspace_root = Path(temporary)
        with RpcClient() as client:
            cases = []
            for index, case in enumerate(config["inspect"]):
                cases.append(
                    _run_case(
                        client,
                        "inspect",
                        case,
                        workspace_root,
                        config["warmup_pairs"],
                        config["measured_pairs"],
                        config["seed"] + index,
                    )
                )
            offset = len(config["inspect"])
            for index, case in enumerate(config["apply_verify"]):
                cases.append(
                    _run_case(
                        client,
                        "apply_verify",
                        case,
                        workspace_root,
                        config["warmup_pairs"],
                        config["measured_pairs"],
                        config["seed"] + offset + index,
                    )
                )
            startup_ms = client.startup_ms
    raw = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "rg": _command_first_line(["rg", "--version"]),
            "git": _command_first_line(["git", "--version"]),
            "git_commit": _git_commit(),
            "pid": os.getpid(),
            "server_startup_ms": startup_ms,
        },
        "cases": cases,
    }
    raw["summary"] = build_summary(raw)
    return raw


def write_results(raw: dict) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(raw, raw["summary"]), encoding="utf-8")


def check_results() -> None:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    expected_summary = build_summary(raw)
    if raw.get("summary") != expected_summary:
        raise SystemExit("raw summary does not reproduce from paired samples")
    expected_report = render_report(raw, expected_summary)
    if REPORT_PATH.read_text(encoding="utf-8") != expected_report:
        raise SystemExit("report does not reproduce from raw evidence")
    for case in raw["cases"]:
        if len(case["pairs"]) != raw["config"]["measured_pairs"]:
            raise SystemExit(f"invalid pair count: {case['id']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        check_results()
        print("PASS: raw evidence and report reproduce")
        return 0
    raw = run()
    write_results(raw)
    print(render_report(raw, raw["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

