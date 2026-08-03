"""Strict directional reporting and trace export for the UFast v1 pilot."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from statistics import mean, median

from .adapters import sanitize, usage_tokens
from .cases import load_cases


ROOT = Path(__file__).resolve().parents[2]
CASE_FILE = "benchmarks/pilots/ufast-v1-two-cases/cases.json"
EXPECTED_CASES = {
    "ufast-v1-low-complexity",
    "ufast-v1-high-complexity",
}
TRACE_CASE = "ufast-v1-high-complexity"
EXPECTED_CONDITIONS = ["nerd-xfast", "nerd-ufast"]
EXPECTED_TARGET = "gpt-5.6-luna-high"
EXPECTED_MODEL = "gpt-5.6-luna"
PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])/(?:Users|private|var|tmp)/[^\s\"'`]+"
)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _valid_number(value, *, positive: bool = False) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (value > 0 if positive else value >= 0)
    )


def _validate_result(path: Path) -> tuple[dict, list[dict], dict[str, dict]]:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest.get("config", {})
    target = config.get("target", {})
    if config.get("agents") != ["codex"]:
        raise ValueError("UFast pilot must use one Codex agent")
    if config.get("models") != {"codex": EXPECTED_MODEL}:
        raise ValueError("UFast pilot must use Luna only")
    if target.get("id") != EXPECTED_TARGET or target.get("reasoning_effort") != "high":
        raise ValueError("UFast pilot must use Luna at high effort")
    if config.get("conditions") != {"ufast": EXPECTED_CONDITIONS}:
        raise ValueError("invalid UFast benchmark conditions")
    if config.get("case_files") != [CASE_FILE]:
        raise ValueError("invalid UFast case corpus")
    if config.get("repetitions") != 1 or config.get("parallelism") != 1:
        raise ValueError("UFast pilot requires one repetition and parallelism one")

    raw = _read_jsonl(path / "raw.jsonl")
    score_records = _read_jsonl(path / "scores.jsonl")
    scores = {item.get("run_id"): item for item in score_records}
    if len(raw) != 4 or len(scores) != 4 or len(scores) != len(score_records):
        raise ValueError("UFast evidence must contain four unique scored runs")
    if len({item.get("run_id") for item in raw}) != len(raw):
        raise ValueError("UFast raw evidence contains duplicate run IDs")
    expected = {
        (case_id, 1, condition)
        for case_id in EXPECTED_CASES
        for condition in EXPECTED_CONDITIONS
    }
    actual = {
        (item.get("case_id"), item.get("repetition"), item.get("condition"))
        for item in raw
    }
    if actual != expected:
        raise ValueError("UFast run matrix is incomplete")

    for item in raw:
        score = scores.get(item.get("run_id"))
        if (
            item.get("exit_code") != 0
            or item.get("model") != EXPECTED_MODEL
            or item.get("target_id") != EXPECTED_TARGET
            or item.get("reasoning_effort") != "high"
            or score is None
            or score.get("judge_valid") is not True
        ):
            raise ValueError(f"invalid UFast run evidence: {item.get('run_id')}")
        if not _valid_number(item.get("elapsed_seconds"), positive=True):
            raise ValueError(f"invalid UFast latency: {item.get('run_id')}")
        for key in ("input_tokens", "cached_input_tokens", "output_tokens"):
            value = item.get(key)
            if value is not None and not (
                isinstance(value, int) and not isinstance(value, bool) and value >= 0
            ):
                raise ValueError(f"invalid UFast {key}: {item.get('run_id')}")
        if not isinstance(item.get("events"), list):
            raise ValueError(f"missing UFast events: {item.get('run_id')}")
    return manifest, raw, scores


def _arm(records: list[dict], scores: dict[str, dict]) -> dict:
    token_values = [item.get("output_tokens") for item in records]
    complete_tokens = all(
        isinstance(item, int) and not isinstance(item, bool) for item in token_values
    )
    return {
        "runs": len(records),
        "mean_score": round(
            mean(float(scores[item["run_id"]]["score"]) for item in records), 4
        ),
        "pass_rate_percent": round(
            mean(bool(scores[item["run_id"]].get("passed")) for item in records)
            * 100,
            4,
        ),
        "hard_gate_failure_runs": sum(
            bool(scores[item["run_id"]].get("hard_gate_failures"))
            for item in records
        ),
        "median_latency_seconds": round(
            median(float(item["elapsed_seconds"]) for item in records), 4
        ),
        "median_output_tokens": round(median(token_values), 4)
        if complete_tokens
        else None,
    }


def _paired_metrics(records: list[dict], scores: dict[str, dict]) -> dict:
    grouped: dict[tuple[str, int], dict[str, dict]] = {}
    for item in records:
        grouped.setdefault(
            (item["case_id"], int(item["repetition"])), {}
        )[item["condition"]] = item
    if len(grouped) != 2 or any(
        set(arms) != set(EXPECTED_CONDITIONS) for arms in grouped.values()
    ):
        raise ValueError("UFast evidence must contain two complete pairs")

    baseline = [arms["nerd-xfast"] for arms in grouped.values()]
    treatment = [arms["nerd-ufast"] for arms in grouped.values()]
    accuracy = []
    speed = []
    token_saved = []
    cases = {}
    for (case_id, _), arms in grouped.items():
        xfast = arms["nerd-xfast"]
        ufast = arms["nerd-ufast"]
        accuracy_delta = float(scores[ufast["run_id"]]["score"]) - float(
            scores[xfast["run_id"]]["score"]
        )
        speed_delta = (
            (float(xfast["elapsed_seconds"]) - float(ufast["elapsed_seconds"]))
            / float(xfast["elapsed_seconds"])
            * 100
        )
        accuracy.append(accuracy_delta)
        speed.append(speed_delta)
        xfast_tokens = xfast.get("output_tokens")
        ufast_tokens = ufast.get("output_tokens")
        token_delta = None
        if (
            isinstance(xfast_tokens, int)
            and not isinstance(xfast_tokens, bool)
            and xfast_tokens > 0
            and isinstance(ufast_tokens, int)
            and not isinstance(ufast_tokens, bool)
        ):
            token_delta = (xfast_tokens - ufast_tokens) / xfast_tokens * 100
            token_saved.append(token_delta)
        cases[case_id] = {
            "accuracy_delta_points": round(accuracy_delta, 4),
            "speed_percent": round(speed_delta, 4),
            "token_saved_percent": round(token_delta, 4)
            if token_delta is not None
            else None,
        }
    return {
        "pairs": len(grouped),
        "xfast": _arm(baseline, scores),
        "ufast": _arm(treatment, scores),
        "delta": {
            "accuracy_points": round(mean(accuracy), 4),
            "speed_percent": round(median(speed), 4),
            "token_saved_percent": round(median(token_saved), 4)
            if len(token_saved) == len(grouped)
            else None,
            "token_pairs": len(token_saved),
        },
        "cases": dict(sorted(cases.items())),
    }


def summarize_ufast(result_dir: Path) -> dict:
    manifest, raw, scores = _validate_result(Path(result_dir))
    return {
        "schema_version": 1,
        "comparison": "ufast-v1-vs-xfast",
        "created_at": manifest.get("created_at"),
        "run_id": manifest.get("run_id"),
        "provenance": {
            "nerd_commit": manifest.get("nerd_commit"),
            "codex_version": manifest.get("agent_versions", {}).get("codex"),
            "model": EXPECTED_MODEL,
            "reasoning_effort": "high",
        },
        "controls": {
            "cases": 2,
            "repetitions": 1,
            "models": 1,
            "arms": EXPECTED_CONDITIONS,
            "fresh_isolated_agents": True,
        },
        "aggregate": _paired_metrics(raw, scores),
        "limitations": [
            "two coding cases",
            "one repetition",
            "one model",
            "directional evidence only",
            "individual LLM-call timing and complete runtime tool manifests may be unavailable",
        ],
    }


def _redact(value):
    value = sanitize(value)
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return PATH_PATTERN.sub("[REDACTED_PATH]", value)
    return value


def _tool_events(events: list[dict]) -> list[dict]:
    tools = []
    for event in events:
        if event.get("type") != "item.started":
            continue
        item = event.get("item", {})
        item_type = item.get("type")
        if item_type not in {
            "command_execution",
            "file_change",
            "mcp_tool_call",
            "web_search",
            "collab_tool_call",
        }:
            continue
        tools.append(
            {
                "type": item_type,
                "command": item.get("command"),
                "name": item.get("name"),
                "changes": item.get("changes"),
            }
        )
    return tools


def _command_kind(command: str) -> str:
    tokens = command.casefold()
    if re.search(r"(?:^|\s)(?:rtk\s+)?(?:rg|grep|find)(?:\s|$)", tokens):
        return "search"
    if re.search(r"(?:^|\s)(?:rtk\s+)?(?:sed|cat|head|tail)(?:\s|$)", tokens):
        return "read"
    if "apply_patch" in tokens:
        return "edit"
    return "command"


def _trace_metrics(record: dict) -> dict:
    events = record.get("events", [])
    tools = _tool_events(events)
    commands = [item["command"] for item in tools if isinstance(item.get("command"), str)]
    kinds = [_command_kind(command) for command in commands]
    file_changes = sum(item.get("type") == "file_change" for item in tools)
    counts = Counter(kinds)
    command_counts = Counter(commands)
    repeated_reads = sum(
        count - 1
        for command, count in command_counts.items()
        if count > 1 and _command_kind(command) == "read"
    )
    repeated_searches = sum(
        count - 1
        for command, count in command_counts.items()
        if count > 1 and _command_kind(command) == "search"
    )
    proofs = [event for event in events if event.get("type") == "benchmark.proof"]
    usage = usage_tokens(events)
    for key in usage:
        if usage[key] is None:
            usage[key] = record.get(key)
    final_text = record.get("final_text", "")
    return {
        "run_id": record["run_id"],
        "elapsed_seconds": round(float(record["elapsed_seconds"]), 4),
        "turns_observed": sum(event.get("type") == "turn.completed" for event in events),
        "llm_calls": None,
        "tool_calls": len(tools),
        "tool_calls_by_type": dict(sorted(Counter(item["type"] for item in tools).items())),
        "commands_by_kind": dict(sorted(counts.items())),
        "repeated_reads": repeated_reads,
        "repeated_searches": repeated_searches,
        "file_change_calls": file_changes,
        "verification_count": len(proofs),
        "verification_seconds": round(
            sum(float(item.get("elapsed_seconds", 0.0)) for item in proofs), 4
        ),
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "output_tokens": usage["output_tokens"],
        "output_words": len(final_text.split()),
        "event_offsets_available": False,
        "observed_tools": tools,
        "changed_files": list(record.get("changed_files", [])),
        "proofs": proofs,
        "final_output": final_text,
        "events": _redact(events),
    }


def _skill_overlap() -> dict:
    entries = {}
    boundaries = {
        "nerd-fast": "Accuracy-preserving global latency modifier",
        "nerd-xfast": "Self-contained lossy path for broad concrete outputs",
        "nerd-ufast": "Self-contained eligibility-gated deterministic changes",
    }
    for name, boundary in boundaries.items():
        body = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        folded = body.casefold()
        entries[name] = {
            "words": len(body.split()),
            "boundary": boundary,
            "mentions_reuse": "reuse" in folded,
            "mentions_batch": "batch" in folded,
            "mentions_latency": "latency" in folded,
            "mentions_focused_proof": "focused" in folded
            and ("proof" in folded or "verification" in folded),
        }
    return entries


def build_feedback_trace(result_dir: Path, summary: dict | None = None) -> dict:
    manifest, raw, _ = _validate_result(Path(result_dir))
    summary = summarize_ufast(result_dir) if summary is None else summary
    cases = {case.id: case for case in load_cases(ROOT / CASE_FILE)}
    records = {
        item["condition"]: item for item in raw if item["case_id"] == TRACE_CASE
    }
    if set(records) != set(EXPECTED_CONDITIONS):
        raise ValueError("Feedback 1 trace requires both high-complexity arms")
    trace = {
        "schema_version": 1,
        "feedback": "docs/feedbacks/ufast-1.md",
        "task": {
            "id": TRACE_CASE,
            "prompt": cases[TRACE_CASE].prompt,
            "fixture": cases[TRACE_CASE].fixture,
        },
        "runtime": {
            "framework": "Codex CLI",
            "agent_version": manifest.get("agent_versions", {}).get("codex"),
            "model": EXPECTED_MODEL,
            "reasoning_effort": "high",
            "workspace": "fresh isolated fixture repository per run",
            "codex_home": "fresh temporary CODEX_HOME and HOME; authentication symlink only",
            "user_configuration": "ignored",
            "condition_invocations": {
                "nerd-xfast": "Use $nerd-xfast.",
                "nerd-ufast": "Use $nerd-ufast.",
            },
            "installed_skills": {
                "nerd-xfast": ["nerd-xfast"],
                "nerd-ufast": ["nerd-ufast"],
            },
            "known_context_order": [
                "fixture materialization",
                "isolated skill installation",
                "explicit condition invocation plus user task",
                "runtime-managed context (internal order unavailable)",
            ],
        },
        "summary": summary["aggregate"],
        "traces": {
            condition: _trace_metrics(records[condition])
            for condition in EXPECTED_CONDITIONS
        },
        "skill_overlap": _skill_overlap(),
        "unavailable": [
            "hidden system prompt content",
            "hidden developer prompt content",
            "complete runtime tool capability manifest",
            "internal prompt injection placement",
            "individual LLM-call count and timing when not emitted by Codex",
            "per-event timing when not emitted by Codex",
        ],
        "limitations": summary["limitations"],
        "stop_gate": "Feedback 1 only; later feedback was not inspected.",
    }
    return _redact(trace)


def _display(value, suffix: str = "") -> str:
    if value is None:
        return "Unavailable"
    return f"{value}{suffix}"


def _recommendations(trace: dict) -> list[str]:
    xfast = trace["traces"]["nerd-xfast"]
    ufast = trace["traces"]["nerd-ufast"]
    recommendations = []
    if ufast["tool_calls"] >= xfast["tool_calls"]:
        recommendations.append(
            "Tighten the UFast action chain only if trace review identifies a removable tool call."
        )
    if ufast["repeated_reads"] or ufast["repeated_searches"]:
        recommendations.append(
            "Eliminate the repeated exact read or search shown in the trace."
        )
    if ufast["elapsed_seconds"] >= xfast["elapsed_seconds"]:
        recommendations.append(
            "Profile the longest observable UFast phase before changing prompt text."
        )
    elif ufast["input_tokens"] is not None and xfast["input_tokens"] is not None and ufast[
        "input_tokens"
    ] >= xfast["input_tokens"]:
        recommendations.append(
            "Reduce UFast skill/context input while preserving the eligibility gate."
        )
    if not recommendations:
        recommendations.append(
            "Preserve the current bounds and validate the observed advantage on a larger, separately approved corpus."
        )
    return recommendations[:3]


def render_feedback_markdown(trace: dict) -> str:
    xfast = trace["traces"]["nerd-xfast"]
    ufast = trace["traces"]["nerd-ufast"]
    lines = [
        "# UFast Feedback 1 — Trace-First Evidence",
        "",
        "## Scope",
        "",
        f"Task: `{trace['task']['id']}` — {trace['task']['prompt']}",
        "",
        "This is a two-case, one-repetition, one-model directional pilot. It is not release-quality statistical evidence.",
        "",
        "## Performance Summary",
        "",
        "| Metric | XFast | UFast |",
        "| --- | ---: | ---: |",
        f"| Elapsed | {_display(xfast['elapsed_seconds'], 's')} | {_display(ufast['elapsed_seconds'], 's')} |",
        f"| Observable turns | {_display(xfast['turns_observed'])} | {_display(ufast['turns_observed'])} |",
        f"| Individual LLM calls | {_display(xfast['llm_calls'])} | {_display(ufast['llm_calls'])} |",
        f"| Tool calls | {xfast['tool_calls']} | {ufast['tool_calls']} |",
        f"| Input tokens | {_display(xfast['input_tokens'])} | {_display(ufast['input_tokens'])} |",
        f"| Cached input tokens | {_display(xfast['cached_input_tokens'])} | {_display(ufast['cached_input_tokens'])} |",
        f"| Output tokens | {_display(xfast['output_tokens'])} | {_display(ufast['output_tokens'])} |",
        f"| Repeated reads | {xfast['repeated_reads']} | {ufast['repeated_reads']} |",
        f"| Repeated searches | {xfast['repeated_searches']} | {ufast['repeated_searches']} |",
        f"| Verification commands | {xfast['verification_count']} | {ufast['verification_count']} |",
        f"| Verification time | {xfast['verification_seconds']}s | {ufast['verification_seconds']}s |",
        f"| Final-output words | {xfast['output_words']} | {ufast['output_words']} |",
        "",
        "## Complete Observable Trace",
    ]
    for condition, label in (("nerd-xfast", "XFast"), ("nerd-ufast", "UFast")):
        lines.extend(
            [
                "",
                f"### {label}",
                "",
                "```json",
                json.dumps(trace["traces"][condition]["events"], indent=2, sort_keys=True),
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "## Accessible Runtime Context",
            "",
            f"- Framework: {trace['runtime']['framework']} ({trace['runtime']['agent_version']})",
            f"- Model: `{trace['runtime']['model']}` at `{trace['runtime']['reasoning_effort']}` effort",
            f"- Workspace: {trace['runtime']['workspace']}",
            f"- Runtime home: {trace['runtime']['codex_home']}",
            f"- User configuration: {trace['runtime']['user_configuration']}",
            "- Known context order: " + " → ".join(trace["runtime"]["known_context_order"]),
            "",
            "Observed tools are listed in `feedback-1-trace.json`; the complete capability manifest is unavailable.",
            "",
            "## Unavailable Runtime Internals",
            "",
            *[f"- {item}" for item in trace["unavailable"]],
            "",
            "## Skill Overlap",
            "",
            "| Skill | Words | Reuse | Batch | Latency | Focused proof | Boundary |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for name, item in trace["skill_overlap"].items():
        lines.append(
            f"| `{name}` | {item['words']} | {item['mentions_reuse']} | {item['mentions_batch']} | {item['mentions_latency']} | {item['mentions_focused_proof']} | {item['boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Observed Bottlenecks and Next Decisions",
            "",
            *[f"- {item}" for item in _recommendations(trace)],
            "",
            "The suggested 20-task benchmark is deferred; the approved pilot remains two tasks.",
            "",
            "## Stop Gate",
            "",
            trace["stop_gate"],
            "",
        ]
    )
    return "\n".join(lines)


def _json_body(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_ufast_artifacts(
    result_dir: Path,
    summary_output: Path,
    trace_output: Path,
    feedback_output: Path,
    *,
    check: bool = False,
) -> dict:
    summary = summarize_ufast(result_dir)
    trace = build_feedback_trace(result_dir, summary)
    outputs = {
        Path(summary_output): _json_body(summary),
        Path(trace_output): _json_body(trace),
        Path(feedback_output): render_feedback_markdown(trace),
    }
    if check:
        for path, expected in outputs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                raise ValueError(f"stale UFast artifact: {path}")
        return summary
    existing = [path for path in outputs if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite UFast evidence: {existing[0]}")
    for path, body in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return summary
