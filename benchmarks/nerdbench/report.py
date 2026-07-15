"""Aggregate immutable benchmark evidence and render reviewable reports."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import statistics


COMPARISONS = {
    "smart": ("nerd-smart", "superpowers-brainstorming"),
    "surgery": ("nerd-surgery", "superpowers-systematic-debugging"),
    "execute": ("nerd-execute", "superpowers-executing-plans"),
    "silent": ("nerd-silent", "regular"),
}


def _round(value: float) -> float:
    return round(float(value), 4)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("percentile requires samples")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _wilson(successes: int, total: int) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total
            + z * z / (4 * total * total)
        )
        / denominator
    )
    return [_round(max(0, center - margin) * 100), _round(min(1, center + margin) * 100)]


def _bootstrap_ci(
    values: list[float],
    *,
    statistic,
    seed: int,
    label: str,
    repetitions: int = 1000,
) -> list[float]:
    if not values:
        return [0.0, 0.0]
    label_seed = int(hashlib.sha256(label.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed + label_seed)
    samples = [
        statistic([rng.choice(values) for _ in values])
        for _ in range(repetitions)
    ]
    return [_round(_percentile(samples, 0.025)), _round(_percentile(samples, 0.975))]


def _arm_stats(entries: list[dict], seed: int, label: str) -> dict:
    scores = [entry["score"] for entry in entries]
    latencies = [entry["elapsed_seconds"] for entry in entries]
    passes = sum(bool(entry["passed"]) for entry in entries)
    return {
        "samples": len(entries),
        "mean_score": _round(statistics.fmean(scores)),
        "mean_score_ci95": _bootstrap_ci(
            scores,
            statistic=statistics.fmean,
            seed=seed,
            label=label + "-score",
        ),
        "pass_rate": _round(passes / len(entries) * 100),
        "pass_rate_ci95": _wilson(passes, len(entries)),
        "p50_latency_seconds": _round(statistics.median(latencies)),
        "p95_latency_seconds": _round(_percentile(latencies, 0.95)),
    }


def _pair_identity(record: dict) -> tuple:
    return (
        record["case_id"],
        record["agent"],
        record.get("model"),
        record["repetition"],
    )


def _valid_entries(records: list[dict], scores: list[dict]) -> dict[str, dict]:
    score_index = {item["run_id"]: item for item in scores}
    entries = {}
    for record in records:
        score = score_index.get(record["run_id"])
        if record.get("exit_code") != 0 or not score:
            continue
        if score.get("judge_valid") is False:
            continue
        entry = dict(record)
        entry.update(
            {
                "score": float(score["score"]),
                "passed": bool(score["passed"]),
                "hard_gate_failures": tuple(score.get("hard_gate_failures", ())),
            }
        )
        entries[record["run_id"]] = entry
    return entries


def _pairs(
    records: list[dict],
    treatment: str,
    baseline: str,
) -> list[tuple[dict, dict]]:
    grouped: dict[tuple, dict[str, dict]] = {}
    for record in records:
        if record["condition"] not in {treatment, baseline}:
            continue
        grouped.setdefault(_pair_identity(record), {})[record["condition"]] = record
    return [
        (group[treatment], group[baseline])
        for group in grouped.values()
        if treatment in group and baseline in group
    ]


def _standard_comparison(
    name: str,
    pairs: list[tuple[dict, dict]],
    seed: int,
) -> dict:
    treatment_entries = [pair[0] for pair in pairs]
    baseline_entries = [pair[1] for pair in pairs]
    score_deltas = [
        treatment["score"] - baseline["score"]
        for treatment, baseline in pairs
    ]
    pass_deltas = [
        (float(treatment["passed"]) - float(baseline["passed"])) * 100
        for treatment, baseline in pairs
    ]
    latency_deltas = [
        (treatment["elapsed_seconds"] - baseline["elapsed_seconds"])
        / baseline["elapsed_seconds"]
        * 100
        for treatment, baseline in pairs
        if baseline["elapsed_seconds"] > 0
    ]
    sufficient = len(pairs) >= 5 and len(latency_deltas) >= 5
    return {
        "publication_state": "publishable" if sufficient else "insufficient-data",
        "valid_pairs": len(pairs),
        "treatment": _arm_stats(treatment_entries, seed, name + "-treatment")
        if treatment_entries
        else None,
        "baseline": _arm_stats(baseline_entries, seed, name + "-baseline")
        if baseline_entries
        else None,
        "paired": {
            "score_delta": _round(statistics.fmean(score_deltas))
            if score_deltas
            else None,
            "score_delta_ci95": _bootstrap_ci(
                score_deltas,
                statistic=statistics.fmean,
                seed=seed,
                label=name + "-score-delta",
            )
            if score_deltas
            else None,
            "pass_rate_delta": _round(statistics.fmean(pass_deltas))
            if pass_deltas
            else None,
            "latency_delta_percent": _round(statistics.median(latency_deltas))
            if latency_deltas
            else None,
            "latency_delta_ci95": _bootstrap_ci(
                latency_deltas,
                statistic=statistics.median,
                seed=seed,
                label=name + "-latency-delta",
            )
            if latency_deltas
            else None,
        },
    }


def _silent_comparison(
    pairs: list[tuple[dict, dict]],
    seed: int,
) -> dict:
    result = _standard_comparison("silent", pairs, seed)
    exclusions: Counter[str] = Counter()
    token_pairs = []
    for silent, regular in pairs:
        if silent["hard_gate_failures"] or regular["hard_gate_failures"]:
            exclusions["hard-gate"] += 1
            continue
        if silent["score"] < regular["score"] - 2:
            exclusions["accuracy-drop"] += 1
            continue
        if silent.get("output_tokens") is None or regular.get("output_tokens") is None:
            exclusions["missing-usage"] += 1
            continue
        if regular["output_tokens"] <= 0:
            exclusions["invalid-regular-token-count"] += 1
            continue
        token_pairs.append((silent, regular))

    savings = [
        (regular["output_tokens"] - silent["output_tokens"])
        / regular["output_tokens"]
        * 100
        for silent, regular in token_pairs
    ]
    enough_tokens = len(token_pairs) >= 5 and not exclusions.get("missing-usage")
    result["publication_state"] = (
        "publishable"
        if result["publication_state"] == "publishable" and enough_tokens
        else "insufficient-data"
    )
    result["valid_pairs"] = {
        "accuracy": len(pairs),
        "latency": len(
            [
                pair
                for pair in pairs
                if pair[0]["elapsed_seconds"] >= 0
                and pair[1]["elapsed_seconds"] > 0
            ]
        ),
        "tokens": len(token_pairs),
    }
    result["tokens"] = {
        "regular_median": _round(
            statistics.median(
                [regular["output_tokens"] for _, regular in token_pairs]
            )
        )
        if token_pairs
        else None,
        "silent_median": _round(
            statistics.median([silent["output_tokens"] for silent, _ in token_pairs])
        )
        if token_pairs
        else None,
        "saved_percent": _round(statistics.median(savings)) if savings else None,
        "saved_percent_ci95": _bootstrap_ci(
            savings,
            statistic=statistics.median,
            seed=seed,
            label="silent-token-savings",
        )
        if savings
        else None,
        "exclusions": dict(sorted(exclusions.items())),
    }
    return result


def aggregate_results(
    records: list[dict],
    scores: list[dict],
    manifest: dict,
) -> dict:
    valid = list(_valid_entries(records, scores).values())
    seed = int(manifest.get("config", {}).get("seed", 0))
    comparisons = {}
    for name, (treatment, baseline) in COMPARISONS.items():
        matched = _pairs(valid, treatment, baseline)
        if name == "silent":
            comparisons[name] = _silent_comparison(matched, seed)
        else:
            comparisons[name] = _standard_comparison(name, matched, seed)

    states = [item["publication_state"] for item in comparisons.values()]
    publication = (
        "publishable"
        if not manifest.get("smoke") and all(state == "publishable" for state in states)
        else "insufficient-data"
    )
    patrol_records = [
        record for record in valid if record["condition"] == "nerd-patrol"
    ]
    return {
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "created_at": manifest["created_at"],
        "publication_state": publication,
        "nerd_commit": manifest["nerd_commit"],
        "upstream_commit": manifest["upstream_commit"],
        "agent_versions": manifest.get("agent_versions", {}),
        "repetitions": manifest.get("config", {}).get("repetitions"),
        "comparisons": comparisons,
        "patrol": {
            "valid_runs": len(patrol_records),
            "passed_runs": sum(record["passed"] for record in patrol_records),
        },
    }


def _format(value, suffix: str = "") -> str:
    if value is None:
        return "insufficient data"
    return f"{value:.1f}{suffix}"


def render_summary_markdown(summary: dict) -> str:
    lines = [
        f"# Nerd Benchmark {summary['run_id']}",
        "",
        f"Publication state: **{summary['publication_state']}**",
        "",
        "| Comparison | Accuracy score | Pass rate | p50 latency | p95 latency | Paired score delta | Paired latency delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ("smart", "surgery", "execute"):
        item = summary["comparisons"][name]
        treatment = item["treatment"]
        if not treatment:
            lines.append(f"| {name.title()} | insufficient data | insufficient data | insufficient data | insufficient data | insufficient data | insufficient data |")
            continue
        lines.append(
            f"| {name.title()} | {_format(treatment['mean_score'], '%')} | "
            f"{_format(treatment['pass_rate'], '%')} | "
            f"{_format(treatment['p50_latency_seconds'], 's')} | "
            f"{_format(treatment['p95_latency_seconds'], 's')} | "
            f"{_format(item['paired']['score_delta'])} | "
            f"{_format(item['paired']['latency_delta_percent'], '%')} |"
        )

    silent = summary["comparisons"]["silent"]
    lines.extend(
        [
            "",
            "## Silent",
            "",
            "| Metric | Regular | Silent | Change |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    if silent["treatment"] and silent["baseline"]:
        lines.extend(
            [
                f"| Accuracy score | {_format(silent['baseline']['mean_score'], '%')} | {_format(silent['treatment']['mean_score'], '%')} | {_format(silent['paired']['score_delta'])} |",
                f"| Pass rate | {_format(silent['baseline']['pass_rate'], '%')} | {_format(silent['treatment']['pass_rate'], '%')} | {_format(silent['paired']['pass_rate_delta'])} |",
                f"| p50 latency | {_format(silent['baseline']['p50_latency_seconds'], 's')} | {_format(silent['treatment']['p50_latency_seconds'], 's')} | {_format(silent['paired']['latency_delta_percent'], '%')} |",
                f"| p95 latency | {_format(silent['baseline']['p95_latency_seconds'], 's')} | {_format(silent['treatment']['p95_latency_seconds'], 's')} | — |",
                f"| Tokens saved | {_format(silent['tokens']['regular_median'])} | {_format(silent['tokens']['silent_median'])} | {_format(silent['tokens']['saved_percent'], '%')} |",
            ]
        )
    else:
        lines.append("| Accuracy score | insufficient data | insufficient data | insufficient data |")

    lines.extend(
        [
            "",
            "## Patrol",
            "",
            f"Conformance runs: {summary['patrol']['passed_runs']}/{summary['patrol']['valid_runs']} passed.",
            "",
        ]
    )
    return "\n".join(lines)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_report(result_dir: Path, *, check: bool = False) -> dict:
    manifest = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
    records = _read_jsonl(result_dir / "raw.jsonl")
    scores = _read_jsonl(result_dir / "scores.jsonl")
    summary = aggregate_results(records, scores, manifest)
    json_body = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    markdown_body = render_summary_markdown(summary)
    if check:
        if not (result_dir / "summary.json").is_file():
            raise ValueError("summary.json is missing")
        if (result_dir / "summary.json").read_text(encoding="utf-8") != json_body:
            raise ValueError("summary.json is stale")
        if not (result_dir / "summary.md").is_file():
            raise ValueError("summary.md is missing")
        if (result_dir / "summary.md").read_text(encoding="utf-8") != markdown_body:
            raise ValueError("summary.md is stale")
        return summary
    (result_dir / "summary.json").write_text(json_body, encoding="utf-8")
    (result_dir / "summary.md").write_text(markdown_body, encoding="utf-8")
    return summary
