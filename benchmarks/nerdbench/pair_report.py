"""Strict reporting for one-case, one-repetition paired smoke benchmarks."""

from __future__ import annotations

import json
from pathlib import Path
import re


FAST_RAW_START = "<!-- FAST_RAW_BENCHMARK:START -->"
FAST_RAW_END = "<!-- FAST_RAW_BENCHMARK:END -->"
INDEXER_ENSURE = re.compile(
    r"symbol_index\.py[\"']?\s+ensure(?:\s|[;&|]|$)"
)


def _tool_commands(record: dict) -> list[str]:
    commands = []
    for event in record.get("events", []):
        if event.get("type") not in {"item.started", "item.completed"}:
            continue
        command = event.get("item", {}).get("command")
        if isinstance(command, str):
            commands.append(command)
    return commands


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _percent_delta(treatment: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return round((treatment - baseline) / baseline * 100, 4)


def summarize_pair(result_dir: Path) -> dict:
    manifest_path = result_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    conditions = manifest["config"]["conditions"]
    if len(conditions) != 1:
        raise ValueError("paired smoke config must contain one comparison")
    comparison, arms = next(iter(conditions.items()))
    if not isinstance(arms, list) or len(arms) != 2:
        raise ValueError("paired smoke comparison must contain two ordered arms")
    baseline_name, treatment_name = arms
    if arms != ["raw-agent", "nerd-fast-only"]:
        raise ValueError("paired smoke arms must be raw-agent and nerd-fast-only")

    records = _read_jsonl(result_dir / "raw.jsonl")
    score_records = _read_jsonl(result_dir / "scores.jsonl")
    scores = {item["run_id"]: item for item in score_records}
    if len(scores) != len(score_records):
        raise ValueError("paired smoke scores contain duplicate run IDs")

    grouped = {baseline_name: [], treatment_name: []}
    for record in records:
        condition = record.get("condition")
        if condition in grouped:
            grouped[condition].append(record)
    if any(len(grouped[name]) != 1 for name in grouped):
        raise ValueError("paired smoke evidence must contain exactly one run per arm")
    baseline = grouped[baseline_name][0]
    treatment = grouped[treatment_name][0]
    baseline_commands = "\n".join(_tool_commands(baseline)).replace("\\", "/")
    if "/.agents/skills/nerd-" in baseline_commands:
        raise ValueError("raw arm accessed a Nerd skill")
    treatment_commands = _tool_commands(treatment)
    if not any(
        INDEXER_ENSURE.search(command)
        for command in treatment_commands
    ):
        raise ValueError("Fast arm did not run the indexer")
    identity_fields = (
        "case_id",
        "agent",
        "model",
        "target_id",
        "reasoning_effort",
        "repetition",
    )
    if any(
        baseline.get(field) != treatment.get(field)
        for field in identity_fields
    ):
        raise ValueError("paired smoke arms do not share one run identity")

    def arm(record: dict) -> dict:
        score = scores.get(record["run_id"])
        if record.get("exit_code") != 0 or score is None:
            raise ValueError(f"invalid paired smoke run: {record['run_id']}")
        latency = float(record["elapsed_seconds"])
        if latency <= 0:
            raise ValueError(f"invalid paired smoke latency: {record['run_id']}")
        tokens = record.get("output_tokens")
        if tokens is not None and (
            not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0
        ):
            raise ValueError(f"invalid paired smoke token count: {record['run_id']}")
        return {
            "condition": record["condition"],
            "score": float(score["score"]),
            "passed": bool(score["passed"]),
            "hard_gate_failures": list(score.get("hard_gate_failures", [])),
            "latency_seconds": round(latency, 4),
            "output_tokens": tokens,
        }

    baseline_arm = arm(baseline)
    treatment_arm = arm(treatment)
    if any(
        not item["passed"] or item["hard_gate_failures"]
        for item in (baseline_arm, treatment_arm)
    ):
        raise ValueError("paired smoke accuracy hard gate failed")

    baseline_tokens = baseline_arm["output_tokens"]
    treatment_tokens = treatment_arm["output_tokens"]
    token_delta = (
        _percent_delta(float(treatment_tokens), float(baseline_tokens))
        if isinstance(baseline_tokens, int)
        and not isinstance(baseline_tokens, bool)
        and isinstance(treatment_tokens, int)
        and not isinstance(treatment_tokens, bool)
        else None
    )
    return {
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "created_at": manifest["created_at"],
        "comparison": comparison,
        "case_id": baseline["case_id"],
        "target": manifest["config"]["target"],
        "model": baseline["model"],
        "agent_version": manifest.get("agent_versions", {}).get("codex"),
        "repetitions": manifest["config"]["repetitions"],
        "baseline": baseline_arm,
        "treatment": treatment_arm,
        "controls": {
            "raw_nerd_skill_access": False,
            "treatment_indexer_invoked": True,
        },
        "delta": {
            "accuracy_points": round(
                treatment_arm["score"] - baseline_arm["score"],
                4,
            ),
            "latency_percent": _percent_delta(
                treatment_arm["latency_seconds"],
                baseline_arm["latency_seconds"],
            ),
            "output_tokens_percent": token_delta,
        },
        "limitations": [
            "one case",
            "one repetition",
            "directional evidence only",
        ],
    }


def write_pair_summary(
    result_dir: Path,
    output: Path,
    *,
    overwrite: bool = False,
) -> dict:
    summary = summarize_pair(result_dir)
    body = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if output.exists():
        if output.read_text(encoding="utf-8") == body:
            return summary
        if not overwrite:
            raise FileExistsError(f"refusing to overwrite different summary: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")
    return summary


def _signed(value: float | None, suffix: str = "") -> str:
    return "Unavailable" if value is None else f"{value:+.2f}{suffix}"


def render_fast_raw_readme(summary: dict) -> str:
    baseline = summary["baseline"]
    treatment = summary["treatment"]
    delta = summary["delta"]
    baseline_tokens = baseline["output_tokens"]
    treatment_tokens = treatment["output_tokens"]
    return "\n".join(
        [
            "### Nerd Fast smoke benchmark",
            "",
            "GPT-5.6 Sol at `xhigh`; one repository-summary case and one "
            "repetition. Directional evidence only.",
            "",
            "| Metric | Raw agent | Nerd Fast only | Delta |",
            "| --- | ---: | ---: | ---: |",
            f"| Accuracy | {baseline['score']:.1f}% | "
            f"{treatment['score']:.1f}% | "
            f"{_signed(delta['accuracy_points'], ' points')} |",
            f"| Latency | {baseline['latency_seconds']:.2f}s | "
            f"{treatment['latency_seconds']:.2f}s | "
            f"{_signed(delta['latency_percent'], '%')} |",
            f"| Output tokens | "
            f"{baseline_tokens if baseline_tokens is not None else 'Unavailable'} | "
            f"{treatment_tokens if treatment_tokens is not None else 'Unavailable'} | "
            f"{_signed(delta['output_tokens_percent'], '%')} |",
            "",
            "Both arms use deterministic factual-coverage and clean-worktree "
            "hard gates. The raw arm has no Nerd skills; the treatment has only "
            "Nerd Fast.",
            "The Nerd Fast arm invoked the bundled symbol indexer during its "
            "first discovery batch.",
            "",
            "[Pilot configuration]"
            "(benchmarks/pilots/fast-raw-one-case/gpt-5.6-sol-xhigh.json) · "
            "[Result summary]"
            "(benchmarks/pilots/fast-raw-one-case/result.json)",
        ]
    )


def publish_fast_raw_readme(summary: dict, readme: Path) -> None:
    body = readme.read_text(encoding="utf-8")
    region = f"{FAST_RAW_START}\n{render_fast_raw_readme(summary)}\n{FAST_RAW_END}"
    start_count = body.count(FAST_RAW_START)
    end_count = body.count(FAST_RAW_END)
    if (start_count, end_count) == (0, 0):
        anchor = "### Method"
        if body.count(anchor) != 1:
            raise ValueError("README Method anchor must occur exactly once")
        body = body.replace(anchor, region + "\n\n" + anchor)
    elif (start_count, end_count) == (1, 1):
        prefix, tail = body.split(FAST_RAW_START, 1)
        _, suffix = tail.split(FAST_RAW_END, 1)
        body = prefix + region + suffix
    else:
        raise ValueError("Fast raw benchmark markers must be unique")
    readme.write_text(body, encoding="utf-8")
