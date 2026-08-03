"""Strict aggregation and README publishing for Nerd UFast versus XFast."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
from statistics import mean, median


UFAST_START = "<!-- UFAST_BENCHMARK:START -->"
UFAST_END = "<!-- UFAST_BENCHMARK:END -->"
CASE_FILE = "benchmarks/cases/ufast-phase1-verification.json"
CASE_SHA256 = "6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791"
CASE_IDS = (
    "xfast-v3-discovery-edit",
)
EXPECTED_CONDITIONS = ("nerd-xfast", "nerd-ufast")
EXPECTED_TARGETS = {
    "gpt-5.6-luna-high": ("Luna", "gpt-5.6-luna"),
    "gpt-5.6-terra-high": ("Terra", "gpt-5.6-terra"),
}
SOURCE_HASH_KEYS = (
    "case_corpus",
    "xfast_skill",
    "ufast_skill",
    "ufast_core",
    "ufast_index",
    "ufast_registry",
    "ufast_verify",
    "ufast_server",
    "benchmark_runner",
    "benchmark_materialize",
    "benchmark_adapters",
    "benchmark_scorer",
    "ufast_report",
)
TOOL_NAMES = {
    "ufast_project_index",
    "ufast_fast_search",
    "ufast_safe_edit",
    "ufast_test_runner",
}
ROOT = Path(__file__).resolve().parents[2]


def current_source_hashes() -> dict[str, str]:
    paths = {
        "case_corpus": ROOT / "benchmarks" / "cases" / "ufast-phase1-verification.json",
        "xfast_skill": ROOT / "skills" / "nerd-xfast" / "SKILL.md",
        "ufast_skill": ROOT / "skills" / "nerd-ufast" / "SKILL.md",
        "ufast_core": ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_core.py",
        "ufast_index": ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_index.py",
        "ufast_registry": ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_registry.py",
        "ufast_verify": ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_verify.py",
        "ufast_server": ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_mcp.py",
        "benchmark_runner": ROOT / "benchmarks" / "nerdbench" / "runner.py",
        "benchmark_materialize": ROOT / "benchmarks" / "nerdbench" / "materialize.py",
        "benchmark_adapters": ROOT / "benchmarks" / "nerdbench" / "adapters.py",
        "benchmark_scorer": ROOT / "benchmarks" / "nerdbench" / "scorer.py",
        "ufast_report": Path(__file__).resolve(),
    }
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise ValueError(f"missing UFast evidence file: {path}")
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"invalid UFast JSON object at {path}:{number}")
        records.append(value)
    return records


def _index(records: list[dict], label: str) -> dict[str, dict]:
    indexed = {}
    for item in records:
        run_id = item.get("run_id")
        if not isinstance(run_id, str) or run_id in indexed:
            raise ValueError(f"duplicate or invalid UFast {label} run id: {run_id!r}")
        indexed[run_id] = item
    return indexed


def _validate_source_hashes(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(SOURCE_HASH_KEYS):
        raise ValueError("UFast source hashes do not match the frozen source set")
    for key, digest in value.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid UFast source hash: {key}")
    if value["case_corpus"] != CASE_SHA256:
        raise ValueError("UFast case corpus hash drifted")
    return dict(value)


def _validate_tool_call(call: object, run_id: str) -> dict:
    if not isinstance(call, dict) or call.get("type") != "ufast_tool_call":
        raise ValueError(f"invalid UFast tool call evidence: {run_id}")
    if call.get("tool") not in TOOL_NAMES:
        raise ValueError(f"unknown UFast tool call evidence: {run_id}")
    if not isinstance(call.get("status"), str):
        raise ValueError(f"missing UFast tool status: {run_id}")
    for field in ("operation_ms", "cold_start_ms"):
        value = call.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise ValueError(f"invalid UFast {field}: {run_id}")
    return call


def _validate_isolation(item: dict) -> None:
    run_id = item["run_id"]
    evidence = item.get("ufast_evidence")
    if not isinstance(evidence, dict) or set(evidence) != {
        "runtime_present",
        "config_present",
        "user_config_ignored",
        "tool_calls",
    }:
        raise ValueError(f"missing UFast isolation evidence: {run_id}")
    calls = evidence.get("tool_calls")
    if not isinstance(calls, list):
        raise ValueError(f"invalid UFast tool call list: {run_id}")
    normalized_events = [
        event
        for event in item.get("events", [])
        if isinstance(event, dict) and event.get("type") == "ufast_tool_call"
    ]

    if item["condition"] == "nerd-ufast":
        if (
            evidence.get("runtime_present") is not True
            or evidence.get("config_present") is not True
            or evidence.get("user_config_ignored") is not False
        ):
            raise ValueError(f"UFast runtime/config isolation failed: {run_id}")
        if not calls:
            raise ValueError(f"UFast run has no selected tool call: {run_id}")
        if len(calls) > 6:
            raise ValueError(f"UFast run exceeds the tool call policy: {run_id}")
        calls = [_validate_tool_call(call, run_id) for call in calls]
        if not any(
            call.get("tool") in {"ufast_project_index", "ufast_fast_search"}
            for call in calls
        ):
            raise ValueError(f"UFast run has no project context route: {run_id}")
        if not any(call.get("tool") == "ufast_safe_edit" for call in calls):
            raise ValueError(f"UFast run has no safe-edit route: {run_id}")
        if normalized_events != calls:
            raise ValueError(f"UFast normalized tool events disagree: {run_id}")
    else:
        if (
            evidence.get("runtime_present") is not False
            or evidence.get("config_present") is not False
            or evidence.get("user_config_ignored") is not True
            or calls
            or normalized_events
        ):
            raise ValueError(f"XFast contains a UFast runtime, config, or tool leak: {run_id}")


def _validate_result(path: Path) -> tuple[str, dict, list[dict], dict[str, dict], dict[str, str]]:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"missing UFast manifest: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"invalid UFast manifest: {path}")
    config = manifest.get("config")
    if not isinstance(config, dict):
        raise ValueError(f"missing UFast config: {path}")
    target = config.get("target")
    if not isinstance(target, dict) or target.get("id") not in EXPECTED_TARGETS:
        raise ValueError(f"unexpected UFast target: {path}")
    target_id = target["id"]
    label, model = EXPECTED_TARGETS[target_id]
    if (
        config.get("agents") != ["codex"]
        or config.get("models") != {"codex": model}
        or target.get("reasoning_effort") != "high"
        or config.get("case_files") != [CASE_FILE]
        or config.get("conditions") != {"xfast": list(EXPECTED_CONDITIONS)}
        or config.get("repetitions") != 1
        or config.get("parallelism") != 1
        or manifest.get("planned_runs") != 2
        or manifest.get("smoke") is not False
    ):
        raise ValueError(f"UFast manifest does not match the frozen matrix: {label}")
    source_hashes = _validate_source_hashes(manifest.get("source_hashes"))
    if source_hashes != current_source_hashes():
        raise ValueError(f"UFast evidence does not match the current frozen source: {label}")

    raw = _read_jsonl(path / "raw.jsonl")
    scores = _index(_read_jsonl(path / "scores.jsonl"), "score")
    raw_index = _index(raw, "raw")
    if len(raw) != 2 or len(scores) != 2 or set(raw_index) != set(scores):
        raise ValueError(f"UFast evidence must contain two unique matched runs: {label}")
    identities = {
        (item.get("case_id"), item.get("repetition"), item.get("condition"))
        for item in raw
    }
    expected = {
        (case_id, 1, condition)
        for case_id in CASE_IDS
        for condition in EXPECTED_CONDITIONS
    }
    if identities != expected:
        raise ValueError(f"UFast run matrix is incomplete: {label}")

    for item in raw:
        run_id = item["run_id"]
        score = scores[run_id]
        elapsed = item.get("elapsed_seconds")
        tokens = item.get("output_tokens")
        if (
            item.get("exit_code") != 0
            or item.get("agent") != "codex"
            or item.get("model") != model
            or item.get("target_id") != target_id
            or item.get("reasoning_effort") != "high"
            or score.get("judge_valid") is not True
            or score.get("passed") is not True
            or score.get("hard_gate_failures") != []
            or not isinstance(score.get("score"), (int, float))
            or isinstance(score.get("score"), bool)
        ):
            raise ValueError(f"invalid UFast run evidence: {run_id}")
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed <= 0:
            raise ValueError(f"invalid UFast latency: {run_id}")
        if tokens is not None and (
            not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0
        ):
            raise ValueError(f"invalid UFast token count: {run_id}")
        if not isinstance(item.get("events"), list):
            raise ValueError(f"invalid UFast event list: {run_id}")
        _validate_isolation(item)
    return label, manifest, raw, scores, source_hashes


def _arm(records: list[dict], scores: dict[str, dict]) -> dict:
    values = [float(scores[item["run_id"]]["score"]) for item in records]
    token_values = [item.get("output_tokens") for item in records]
    complete_tokens = all(
        isinstance(value, int) and not isinstance(value, bool) for value in token_values
    )
    return {
        "runs": len(records),
        "mean_score": round(mean(values), 4),
        "pass_rate_percent": round(
            mean(bool(scores[item["run_id"]].get("passed")) for item in records) * 100,
            4,
        ),
        "hard_gate_failure_runs": sum(
            bool(scores[item["run_id"]].get("hard_gate_failures")) for item in records
        ),
        "median_latency_seconds": round(
            median(float(item["elapsed_seconds"]) for item in records), 4
        ),
        "median_output_tokens": round(median(token_values), 4) if complete_tokens else None,
    }


def _tool_metrics(records: list[dict]) -> dict:
    calls_by_run = [item["ufast_evidence"]["tool_calls"] for item in records]
    cold_starts = [float(calls[0]["cold_start_ms"]) for calls in calls_by_run if calls]
    operation_totals = [
        sum(float(call["operation_ms"]) for call in calls) for calls in calls_by_run if calls
    ]
    applied = [
        any(
            call.get("tool") == "ufast_safe_edit"
            and call.get("status") == "applied"
            for call in calls
        )
        for calls in calls_by_run
    ]
    return {
        "hit_rate_percent": round(mean(bool(calls) for calls in calls_by_run) * 100, 4),
        "tool_call_runs": sum(bool(calls) for calls in calls_by_run),
        "applied_runs": sum(applied),
        "fallback_runs": sum(not value for value in applied),
        "median_cold_start_ms": round(median(cold_starts), 4),
        "median_operation_ms": round(median(operation_totals), 4),
        "project_index_runs": sum(
            any(call.get("tool") == "ufast_project_index" for call in calls)
            for calls in calls_by_run
        ),
        "fast_search_runs": sum(
            any(call.get("tool") == "ufast_fast_search" for call in calls)
            for calls in calls_by_run
        ),
        "test_runner_runs": sum(
            any(call.get("tool") == "ufast_test_runner" for call in calls)
            for calls in calls_by_run
        ),
    }


def _metrics(records: list[dict], scores: dict[str, dict]) -> dict:
    grouped: dict[tuple[str, str, int], dict[str, dict]] = {}
    for item in records:
        key = (item["target_id"], item["case_id"], int(item["repetition"]))
        grouped.setdefault(key, {})[item["condition"]] = item
    if not grouped or any(set(arms) != set(EXPECTED_CONDITIONS) for arms in grouped.values()):
        raise ValueError("UFast evidence must contain complete pairs")
    xfast = [arms["nerd-xfast"] for arms in grouped.values()]
    ufast = [arms["nerd-ufast"] for arms in grouped.values()]
    accuracy = []
    speed = []
    token_change = []
    for arms in grouped.values():
        control = arms["nerd-xfast"]
        treatment = arms["nerd-ufast"]
        accuracy.append(
            float(scores[treatment["run_id"]]["score"])
            - float(scores[control["run_id"]]["score"])
        )
        speed.append(
            (float(control["elapsed_seconds"]) - float(treatment["elapsed_seconds"]))
            / float(control["elapsed_seconds"])
            * 100
        )
        control_tokens = control.get("output_tokens")
        treatment_tokens = treatment.get("output_tokens")
        if (
            isinstance(control_tokens, int)
            and not isinstance(control_tokens, bool)
            and control_tokens > 0
            and isinstance(treatment_tokens, int)
            and not isinstance(treatment_tokens, bool)
        ):
            token_change.append((treatment_tokens - control_tokens) / control_tokens * 100)
    return {
        "pairs": len(grouped),
        "xfast": _arm(xfast, scores),
        "ufast": _arm(ufast, scores),
        "delta": {
            "accuracy_points": round(mean(accuracy), 4),
            "speed_percent": round(median(speed), 4),
            "token_change_percent": round(median(token_change), 4)
            if len(token_change) == len(grouped)
            else None,
            "token_pairs": len(token_change),
        },
        "ufast_tools": _tool_metrics(ufast),
    }


def summarize_ufast(result_dirs: list[Path]) -> dict:
    if len(result_dirs) != 2:
        raise ValueError("UFast summary requires exactly two result directories")
    models = {}
    manifests = {}
    hashes = None
    all_raw = []
    all_scores = {}
    for path in result_dirs:
        label, manifest, raw, scores, current_hashes = _validate_result(Path(path))
        if label in models:
            raise ValueError(f"duplicate UFast target: {label}")
        if hashes is None:
            hashes = current_hashes
        elif hashes != current_hashes:
            raise ValueError("UFast result directories contain source drift")
        models[label] = _metrics(raw, scores)
        manifests[label] = manifest
        all_raw.extend(raw)
        all_scores.update(scores)
    if set(models) != {"Luna", "Terra"}:
        raise ValueError("UFast summary requires Luna and Terra")
    assert hashes is not None
    ordered = ("Luna", "Terra")
    return {
        "schema_version": 1,
        "comparison": "nerd-ufast-vs-nerd-xfast",
        "created_at": max(manifests[label]["created_at"] for label in ordered),
        "run_ids": {label: manifests[label]["run_id"] for label in ordered},
        "provenance": {
            "nerd_commits": {
                label: manifests[label].get("nerd_commit") for label in ordered
            },
            "codex_versions": {
                label: manifests[label].get("agent_versions", {}).get("codex")
                for label in ordered
            },
            "models": {
                label: EXPECTED_TARGETS[manifests[label]["config"]["target"]["id"]][1]
                for label in ordered
            },
            "source_hashes": hashes,
        },
        "models": {label: models[label] for label in ordered},
        "aggregate": _metrics(all_raw, all_scores),
        "controls": {
            "fresh_isolated_agents": True,
            "same_model_and_effort_within_pairs": True,
            "reasoning_effort": "high",
            "verified_host": "Codex",
            "models": 2,
            "cases": 1,
            "repetitions_per_model": 1,
            "workload_runs": 4,
            "pairs": 2,
            "case_file": CASE_FILE,
            "case_sha256": CASE_SHA256,
        },
        "limitations": [
            "one Python discovery/edit verification case",
            "one repetition per model",
            "directional evidence, not a universal latency claim",
            "the local MCP fast path is verified only on Codex",
        ],
        "artifacts": {
            "cases": CASE_FILE,
            "config_dir": "benchmarks/pilots/ufast-vs-xfast/",
            "result_summary": "benchmarks/pilots/ufast-vs-xfast/result.json",
        },
    }


def write_ufast_summary(
    result_dirs: list[Path],
    output: Path,
    *,
    overwrite: bool = False,
) -> dict:
    summary = summarize_ufast(result_dirs)
    body = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if output.exists():
        if output.read_text(encoding="utf-8") == body:
            return summary
        if not overwrite:
            raise FileExistsError(f"refusing to overwrite different UFast summary: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")
    return summary


def _signed(value: float, suffix: str = "") -> str:
    return f"{value:+.2f}{suffix}"


def _speed(value: float) -> str:
    if round(value, 2) == 0:
        return "equal within displayed precision"
    return f"{abs(value):.2f}% {'faster' if value > 0 else 'slower'}"


def _token_change(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if round(value, 2) == 0:
        return "equal within displayed precision"
    return f"{abs(value):.2f}% {'fewer' if value < 0 else 'more'}"


def _tokens(value: float | None) -> str:
    return "Unavailable" if value is None else f"{value:.0f}"


def render_ufast_readme(summary: dict) -> str:
    rows = []
    for label, metrics in [
        *((name, summary["models"][name]) for name in ("Luna", "Terra")),
        ("Combined", summary["aggregate"]),
    ]:
        rows.append(
            f"| {label} | {metrics['xfast']['mean_score']:.2f}% | "
            f"{metrics['ufast']['mean_score']:.2f}% | "
            f"{_signed(metrics['delta']['accuracy_points'], ' points')} | "
            f"{metrics['xfast']['median_latency_seconds']:.2f}s | "
            f"{metrics['ufast']['median_latency_seconds']:.2f}s | "
            f"{_speed(metrics['delta']['speed_percent'])} | "
            f"{_tokens(metrics['xfast']['median_output_tokens'])} | "
            f"{_tokens(metrics['ufast']['median_output_tokens'])} | "
            f"{_token_change(metrics['delta']['token_change_percent'])} | "
            f"{metrics['ufast_tools']['hit_rate_percent']:.2f}% | "
            f"{metrics['ufast_tools']['fallback_runs']} |"
        )
    aggregate = summary["aggregate"]
    tools = aggregate["ufast_tools"]
    artifacts = summary["artifacts"]
    fallback_label = (
        "fallback run" if tools["fallback_runs"] == 1 else "fallback runs"
    )
    speed_value = aggregate["delta"]["speed_percent"]
    speed_sentence = (
        "UFast and XFast were equal within displayed latency precision."
        if round(speed_value, 2) == 0
        else f"UFast was {_speed(speed_value)} than XFast."
    )
    return "\n".join(
        [
            "## UFast: routed deterministic project tools",
            "",
            "Nerd UFast is a generic tool-backed modifier with an operation registry. Phase 1 batches indexed queries, atomic multi-file edits, and concurrent allowlisted checks. V0 reuses fresh structured evidence; V1 runs safe local proof automatically or asks before broader proof. Language-specific LSP and AST backends can register later without changing the public routing contract.",
            "",
            f"Across this directional pilot, {speed_sentence} UFast used {_token_change(aggregate['delta']['token_change_percent'])} output tokens.",
            "",
            "| Model | XFast accuracy | UFast accuracy | Accuracy delta | XFast latency | UFast latency | Speed | XFast tokens | UFast tokens | Token change | Tool hit | Fallbacks |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |",
            *rows,
            "",
            f"The UFast route had a {tools['hit_rate_percent']:.2f}% tool hit rate, {tools['fallback_runs']} {fallback_label}, {tools['project_index_runs']} project-index runs, {tools['fast_search_runs']} fast-search runs, {tools['test_runner_runs']} standalone test-runner runs, {tools['median_cold_start_ms']:.2f} ms median cold start, and {tools['median_operation_ms']:.2f} ms median total tool-operation time per run.",
            "",
            "Method: one Python discovery/edit verification case, one repetition, and Luna plus Terra at `high` reasoning effort produced 4 fresh Codex processes and 2 matched pairs. The case exercises one adapter, not UFast's generic scope. The exact prompt and proof commands are shared by both arms. This tiny verification does not establish a universal speedup. Codex is the only verified UFast tool host in this release; other hosts install the skill but fall back until their tool integration is verified.",
            "",
            f"[Cases]({artifacts['cases']}) · [Pilot configs]({artifacts['config_dir']}) · [Result summary]({artifacts['result_summary']})",
        ]
    )


def publish_ufast_readme(summary: dict, readme: Path, *, check: bool = False) -> None:
    body = readme.read_text(encoding="utf-8")
    region = f"{UFAST_START}\n{render_ufast_readme(summary)}\n{UFAST_END}"
    start_count = body.count(UFAST_START)
    end_count = body.count(UFAST_END)
    if (start_count, end_count) == (0, 0):
        anchor = "\n## Verify locally\n"
        if anchor in body:
            prefix, suffix = body.split(anchor, 1)
            updated = prefix.rstrip() + "\n\n" + region + "\n" + anchor + suffix
        else:
            updated = body.rstrip() + "\n\n" + region + "\n"
    elif (start_count, end_count) == (1, 1):
        prefix, tail = body.split(UFAST_START, 1)
        _, suffix = tail.split(UFAST_END, 1)
        updated = prefix + region + suffix
    else:
        raise ValueError("UFast benchmark markers must be unique")
    if check:
        if body != updated:
            raise ValueError("UFast README benchmark is out of date")
        return
    readme.write_text(updated, encoding="utf-8")
