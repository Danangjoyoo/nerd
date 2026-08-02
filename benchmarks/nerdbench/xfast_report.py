"""Strict aggregation and README publication for the XFast pilot."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median


XFAST_START = "<!-- XFAST_BENCHMARK:START -->"
XFAST_END = "<!-- XFAST_BENCHMARK:END -->"
EXPECTED_TARGETS = {
    "gpt-5.6-luna-high": ("Luna", "gpt-5.6-luna"),
    "gpt-5.6-terra-high": ("Terra", "gpt-5.6-terra"),
    "gpt-5.6-sol-high": ("Sol", "gpt-5.6-sol"),
}
EXPECTED_CONDITIONS = ["xfast-baseline", "nerd-xfast"]
PILOT_PROFILES = {
    "benchmarks/cases/xfast.json": {
        "comparison": "xfast-vs-fast",
        "cases": {"xfast-batched-edit", "xfast-discovery-edit"},
        "repetitions": 2,
        "config_dir": "benchmarks/pilots/xfast-vs-fast/",
        "result_summary": "benchmarks/pilots/xfast-vs-fast/result.json",
    },
    "benchmarks/pilots/xfast-v2-one-case/cases.json": {
        "comparison": "xfast-v2-vs-fast",
        "cases": {"xfast-v2-batched-edit"},
        "repetitions": 1,
        "config_dir": "benchmarks/pilots/xfast-v2-one-case/",
        "result_summary": "benchmarks/pilots/xfast-v2-one-case/result.json",
    },
    "benchmarks/pilots/xfast-v3-five-cases/cases.json": {
        "comparison": "xfast-v3-vs-fast",
        "cases": {
            "xfast-v3-batched-edit",
            "xfast-v3-discovery-edit",
            "xfast-v3-independent-work",
            "xfast-v3-greeting",
            "xfast-v3-slugify",
        },
        "repetitions": 1,
        "config_dir": "benchmarks/pilots/xfast-v3-five-cases/",
        "result_summary": "benchmarks/pilots/xfast-v3-five-cases/result.json",
    },
}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _validate_result(
    path: Path,
) -> tuple[str, dict, list[dict], dict[str, dict], str]:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest.get("config", {})
    target = config.get("target", {})
    target_id = target.get("id")
    if target_id not in EXPECTED_TARGETS:
        raise ValueError(f"unexpected XFast target: {target_id}")
    label, model = EXPECTED_TARGETS[target_id]
    if config.get("agents") != ["codex"] or config.get("models") != {"codex": model}:
        raise ValueError(f"invalid XFast agent/model controls for {target_id}")
    if target.get("reasoning_effort") != "high":
        raise ValueError(f"XFast target must use high effort: {target_id}")
    if config.get("conditions") != {"xfast": EXPECTED_CONDITIONS}:
        raise ValueError(f"invalid XFast conditions for {target_id}")
    case_files = config.get("case_files")
    if not isinstance(case_files, list) or len(case_files) != 1:
        raise ValueError(f"invalid XFast case corpus for {target_id}")
    profile_id = case_files[0]
    try:
        profile = PILOT_PROFILES[profile_id]
    except KeyError as error:
        raise ValueError(f"invalid XFast case corpus for {target_id}") from error
    repetitions = profile["repetitions"]
    if config.get("repetitions") != repetitions or config.get("parallelism") != 1:
        raise ValueError(f"invalid XFast repetition controls for {target_id}")

    raw = _read_jsonl(path / "raw.jsonl")
    score_records = _read_jsonl(path / "scores.jsonl")
    scores = {item["run_id"]: item for item in score_records}
    expected_run_count = len(profile["cases"]) * repetitions * 2
    if (
        len(raw) != expected_run_count
        or len(scores) != expected_run_count
        or len(scores) != len(score_records)
    ):
        raise ValueError(
            f"XFast evidence must contain {expected_run_count} unique runs: "
            f"{target_id}"
        )
    identities = {
        (
            item.get("case_id"),
            item.get("repetition"),
            item.get("condition"),
        )
        for item in raw
    }
    expected = {
        (case_id, repetition, condition)
        for case_id in profile["cases"]
        for repetition in range(1, repetitions + 1)
        for condition in EXPECTED_CONDITIONS
    }
    if identities != expected:
        raise ValueError(f"XFast run matrix is incomplete: {target_id}")
    for item in raw:
        score = scores.get(item.get("run_id"))
        if (
            item.get("exit_code") != 0
            or item.get("model") != model
            or item.get("target_id") != target_id
            or item.get("reasoning_effort") != "high"
            or score is None
            or score.get("judge_valid") is not True
        ):
            raise ValueError(f"invalid XFast run evidence: {item.get('run_id')}")
        elapsed = item.get("elapsed_seconds")
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed <= 0:
            raise ValueError(f"invalid XFast latency: {item.get('run_id')}")
        tokens = item.get("output_tokens")
        if tokens is not None and (
            not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0
        ):
            raise ValueError(f"invalid XFast token count: {item.get('run_id')}")
    return label, manifest, raw, scores, profile_id


def _arm(records: list[dict], scores: dict[str, dict]) -> dict:
    values = [float(scores[item["run_id"]]["score"]) for item in records]
    token_values = [item.get("output_tokens") for item in records]
    tokens_complete = all(isinstance(item, int) and not isinstance(item, bool) for item in token_values)
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
        "median_latency_seconds": round(median(float(item["elapsed_seconds"]) for item in records), 4),
        "median_output_tokens": round(median(token_values), 4) if tokens_complete else None,
    }


def _metrics(records: list[dict], scores: dict[str, dict]) -> dict:
    grouped: dict[tuple[str, str, int], dict[str, dict]] = {}
    for item in records:
        grouped.setdefault(
            (item["target_id"], item["case_id"], int(item["repetition"])),
            {},
        )[
            item["condition"]
        ] = item
    if not grouped or any(
        set(arms) != set(EXPECTED_CONDITIONS) for arms in grouped.values()
    ):
        raise ValueError("XFast evidence must contain complete pairs")
    baseline = [arms["xfast-baseline"] for arms in grouped.values()]
    treatment = [arms["nerd-xfast"] for arms in grouped.values()]
    accuracy = []
    speed = []
    token_saved = []
    for arms in grouped.values():
        fast = arms["xfast-baseline"]
        xfast = arms["nerd-xfast"]
        accuracy.append(float(scores[xfast["run_id"]]["score"]) - float(scores[fast["run_id"]]["score"]))
        speed.append((float(fast["elapsed_seconds"]) - float(xfast["elapsed_seconds"])) / float(fast["elapsed_seconds"]) * 100)
        fast_tokens = fast.get("output_tokens")
        xfast_tokens = xfast.get("output_tokens")
        if (
            isinstance(fast_tokens, int)
            and not isinstance(fast_tokens, bool)
            and fast_tokens > 0
            and isinstance(xfast_tokens, int)
            and not isinstance(xfast_tokens, bool)
        ):
            token_saved.append((fast_tokens - xfast_tokens) / fast_tokens * 100)
    return {
        "pairs": len(grouped),
        "fast": _arm(baseline, scores),
        "xfast": _arm(treatment, scores),
        "delta": {
            "accuracy_points": round(mean(accuracy), 4),
            "speed_percent": round(median(speed), 4),
            "token_saved_percent": round(median(token_saved), 4)
            if len(token_saved) == len(grouped)
            else None,
            "token_pairs": len(token_saved),
        },
    }


def summarize_xfast(result_dirs: list[Path]) -> dict:
    if len(result_dirs) != 3:
        raise ValueError("XFast summary requires exactly three result directories")
    models = {}
    manifests = {}
    all_raw = []
    all_scores = {}
    profile_id = None
    for path in result_dirs:
        label, manifest, raw, scores, current_profile = _validate_result(Path(path))
        if profile_id is None:
            profile_id = current_profile
        elif profile_id != current_profile:
            raise ValueError("XFast result directories use different pilot profiles")
        if label in models:
            raise ValueError(f"duplicate XFast target: {label}")
        models[label] = _metrics(raw, scores)
        manifests[label] = manifest
        all_raw.extend(raw)
        all_scores.update(scores)
    if set(models) != {"Luna", "Terra", "Sol"}:
        raise ValueError("XFast summary requires Luna, Terra, and Sol")
    if profile_id is None:
        raise ValueError("XFast summary has no pilot profile")
    profile = PILOT_PROFILES[profile_id]
    case_count = len(profile["cases"])
    repetitions = profile["repetitions"]
    return {
        "schema_version": 1,
        "comparison": profile["comparison"],
        "created_at": max(item["created_at"] for item in manifests.values()),
        "run_ids": {label: manifests[label]["run_id"] for label in ("Luna", "Terra", "Sol")},
        "provenance": {
            "nerd_commits": {
                label: manifests[label].get("nerd_commit")
                for label in ("Luna", "Terra", "Sol")
            },
            "codex_versions": {
                label: manifests[label].get("agent_versions", {}).get("codex")
                for label in ("Luna", "Terra", "Sol")
            },
            "models": {
                label: EXPECTED_TARGETS[
                    manifests[label]["config"]["target"]["id"]
                ][1]
                for label in ("Luna", "Terra", "Sol")
            },
        },
        "models": {label: models[label] for label in ("Luna", "Terra", "Sol")},
        "aggregate": _metrics(all_raw, all_scores),
        "controls": {
            "fresh_isolated_agents": True,
            "same_model_and_effort_within_pairs": True,
            "reasoning_effort": "high",
            "cases": case_count,
            "repetitions_per_model": repetitions,
            "case_file": profile_id,
        },
        "limitations": [
            f"{case_count} coding case{'s' if case_count != 1 else ''}",
            f"{repetitions} repetition{'s' if repetitions != 1 else ''} per model",
            "per-model results are directional evidence",
        ],
        "artifacts": {
            "cases": profile_id,
            "config_dir": profile["config_dir"],
            "result_summary": profile["result_summary"],
        },
    }


def write_xfast_summary(
    result_dirs: list[Path],
    output: Path,
    *,
    overwrite: bool = False,
) -> dict:
    summary = summarize_xfast(result_dirs)
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


def _saved(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    return f"{value:.2f}% saved" if value >= 0 else f"{-value:.2f}% more"


def render_xfast_readme(summary: dict) -> str:
    rows = []
    speed = summary["aggregate"]["delta"]["speed_percent"]
    speed_result = (
        "Unavailable"
        if speed is None
        else f"{speed:.2f}% faster"
        if speed >= 0
        else f"{-speed:.2f}% slower"
    )
    token_delta = summary["aggregate"]["delta"]["token_saved_percent"]
    token_result = (
        "Unavailable"
        if token_delta is None
        else f"{token_delta:.2f}% fewer"
        if token_delta >= 0
        else f"{-token_delta:.2f}% more"
    )
    ordered = [
        (label, summary["models"][label])
        for label in ("Luna", "Terra", "Sol")
    ]
    for label, metrics in [*ordered, ("Combined", summary["aggregate"])]:
        rows.append(
            f"| {label} | {metrics['fast']['mean_score']:.2f}% | "
            f"{metrics['xfast']['mean_score']:.2f}% | "
            f"{_signed(metrics['delta']['accuracy_points'], ' points')} | "
            f"{metrics['fast']['median_latency_seconds']:.2f}s | "
            f"{metrics['xfast']['median_latency_seconds']:.2f}s | "
            f"{_signed(metrics['delta']['speed_percent'], '%')} | "
            f"{_saved(metrics['delta']['token_saved_percent'])} |"
        )
    case_count = summary["controls"]["cases"]
    repetitions = summary["controls"]["repetitions_per_model"]
    case_phrase = (
        "one coding case"
        if case_count == 1
        else "two cases"
        if case_count == 2
        else f"{case_count} cases"
    )
    repetition_phrase = (
        "one repetition"
        if repetitions == 1
        else "two repetitions"
        if repetitions == 2
        else f"{repetitions} repetitions"
    )
    artifacts = summary.get(
        "artifacts",
        {
            "cases": "benchmarks/cases/xfast.json",
            "config_dir": "benchmarks/pilots/xfast-vs-fast/",
            "result_summary": "benchmarks/pilots/xfast-vs-fast/result.json",
        },
    )
    return "\n".join(
        [
            "## Now available xfast!",
            "",
            "Nerd XFast is the self-contained, throughput-first coding path. It intentionally trades accuracy, completeness, and verification breadth in pursuit of lower latency through one immutable action chain, immediate writes, and no self-selected proof.",
            "",
            f"In this pilot, XFast was {speed_result} and used {token_result} "
            "output tokens.",
            "",
            "| Model | Fast accuracy | XFast accuracy | Accuracy delta | Fast latency | XFast latency | Speed | Output tokens |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            *rows,
            "",
            f"Notes: this is a directional pilot with {case_phrase} and "
            f"{repetition_phrase} per model. Each arm ran in a fresh isolated "
            "Codex process with the same model at `high` reasoning effort. "
            "Accuracy reduction is accepted by design; token savings are shown "
            "only when every paired run reported token usage.",
            "",
            f"[Cases]({artifacts['cases']}) · "
            f"[Pilot configs]({artifacts['config_dir']}) · "
            f"[Result summary]({artifacts['result_summary']})",
        ]
    )


def publish_xfast_readme(summary: dict, readme: Path, *, check: bool = False) -> None:
    body = readme.read_text(encoding="utf-8")
    region = f"{XFAST_START}\n{render_xfast_readme(summary)}\n{XFAST_END}"
    start_count = body.count(XFAST_START)
    end_count = body.count(XFAST_END)
    if (start_count, end_count) == (0, 0):
        base = body.rstrip()
    elif (start_count, end_count) == (1, 1):
        prefix, tail = body.split(XFAST_START, 1)
        _, suffix = tail.split(XFAST_END, 1)
        base = (prefix.rstrip() + "\n\n" + suffix.lstrip()).rstrip()
    else:
        raise ValueError("XFast benchmark markers must be unique")
    updated = base + "\n\n" + region + "\n"
    if check:
        if body != updated:
            raise ValueError("XFast README benchmark is out of date")
        return
    readme.write_text(updated, encoding="utf-8")
