"""Strict prompt-only UFast versus XFast aggregation and README publishing."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
from statistics import mean, median


UFAST_START = "<!-- UFAST_BENCHMARK:START -->"
UFAST_END = "<!-- UFAST_BENCHMARK:END -->"
CASE_FILE = "benchmarks/cases/ufast-phase1-verification.json"
CASE_SHA256 = "6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791"
CASE_IDS = ("xfast-v3-discovery-edit",)
EXPECTED_CONDITIONS = ("nerd-xfast", "nerd-ufast")
EXPECTED_TARGETS = {
    "gpt-5.6-luna-high": ("Luna", "gpt-5.6-luna"),
    "gpt-5.6-terra-high": ("Terra", "gpt-5.6-terra"),
}
EXPECTED_CHANGED_FILES = {
    "normalizers.py",
    "registry.py",
    "test_normalizers.py",
}
SOURCE_HASH_KEYS = (
    "case_corpus",
    "smart_skill",
    "execute_skill",
    "xfast_skill",
    "ufast_skill",
    "benchmark_runner",
    "benchmark_materialize",
    "benchmark_adapters",
    "benchmark_scorer",
    "ufast_report",
)
ROOT = Path(__file__).resolve().parents[2]


def current_source_hashes() -> dict[str, str]:
    paths = {
        "case_corpus": ROOT / CASE_FILE,
        "smart_skill": ROOT / "skills" / "nerd-smart" / "SKILL.md",
        "execute_skill": ROOT / "skills" / "nerd-execute" / "SKILL.md",
        "xfast_skill": ROOT / "skills" / "nerd-xfast" / "SKILL.md",
        "ufast_skill": ROOT / "skills" / "nerd-ufast" / "SKILL.md",
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
        raise ValueError("UFast source hashes do not match the prompt-only source set")
    for key, digest in value.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid UFast source hash: {key}")
    if value["case_corpus"] != CASE_SHA256:
        raise ValueError("UFast case corpus hash drifted")
    return dict(value)


def _validate_manifest(manifest: dict, result: Path) -> tuple[str, str, str]:
    target_id = manifest.get("config", {}).get("target", {}).get("id")
    if target_id not in EXPECTED_TARGETS:
        raise ValueError(f"unexpected UFast target in {result}: {target_id}")
    label, model = EXPECTED_TARGETS[target_id]
    config = manifest.get("config")
    if not isinstance(config, dict):
        raise ValueError(f"missing UFast config in {result}")
    expected = {
        "agents": ["codex"],
        "case_files": [CASE_FILE],
        "conditions": {"xfast": list(EXPECTED_CONDITIONS)},
        "repetitions": 1,
        "parallelism": 1,
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"unexpected UFast {key} in {result}")
    target = config.get("target", {})
    if target.get("reasoning_effort") != "high":
        raise ValueError(f"unexpected UFast reasoning effort in {result}")
    if config.get("models", {}).get("codex") != model:
        raise ValueError(f"unexpected UFast model in {result}")
    if manifest.get("planned_runs") != 2 or manifest.get("smoke") is not False:
        raise ValueError(f"unexpected UFast run plan in {result}")
    commit = manifest.get("nerd_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"invalid UFast source commit in {result}")
    _validate_source_hashes(manifest.get("source_hashes"))
    return label, model, commit


def _validate_run(item: dict, score: dict, target_id: str, model: str) -> None:
    run_id = item["run_id"]
    if item.get("case_id") not in CASE_IDS:
        raise ValueError(f"unexpected UFast case: {run_id}")
    if item.get("condition") not in EXPECTED_CONDITIONS:
        raise ValueError(f"unexpected UFast condition: {run_id}")
    if item.get("agent") != "codex" or item.get("model") != model:
        raise ValueError(f"unexpected UFast agent or model: {run_id}")
    if item.get("target_id") != target_id or item.get("reasoning_effort") != "high":
        raise ValueError(f"unexpected UFast target metadata: {run_id}")
    if item.get("repetition") != 1 or item.get("exit_code") != 0:
        raise ValueError(f"failed or repeated UFast run: {run_id}")
    elapsed = item.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0:
        raise ValueError(f"invalid UFast elapsed time: {run_id}")
    tokens = item.get("output_tokens")
    if tokens is not None and (not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0):
        raise ValueError(f"invalid UFast output tokens: {run_id}")
    commands = item.get("command_results")
    if not isinstance(commands, dict) or not commands or any(value != 0 for value in commands.values()):
        raise ValueError(f"failed UFast external proof: {run_id}")
    changed = item.get("changed_files")
    if not isinstance(changed, list) or set(changed) != EXPECTED_CHANGED_FILES:
        raise ValueError(f"unexpected UFast changed files: {run_id}")
    if item.get("ufast_evidence") is not None:
        raise ValueError(f"prompt-only UFast run contains runtime evidence: {run_id}")
    events = item.get("events")
    if not isinstance(events, list) or any(
        isinstance(event, dict) and event.get("type") == "ufast_tool_call"
        for event in events
    ):
        raise ValueError(f"prompt-only UFast run contains tool telemetry: {run_id}")
    if score.get("run_id") != run_id or score.get("passed") is not True:
        raise ValueError(f"failed UFast score: {run_id}")
    if score.get("judge_valid") is not True or score.get("hard_gate_failures") != []:
        raise ValueError(f"invalid UFast judge or hard gate: {run_id}")
    value = score.get("score")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"invalid UFast score value: {run_id}")


def _arm_stats(items: list[tuple[dict, dict]]) -> dict:
    tokens = [item[0]["output_tokens"] for item in items if item[0]["output_tokens"] is not None]
    return {
        "runs": len(items),
        "mean_score": round(mean(item[1]["score"] for item in items), 4),
        "pass_rate_percent": round(100 * mean(item[1]["passed"] for item in items), 4),
        "hard_gate_failure_runs": sum(bool(item[1]["hard_gate_failures"]) for item in items),
        "median_latency_seconds": round(median(item[0]["elapsed_seconds"] for item in items), 4),
        "median_output_tokens": round(median(tokens), 4) if tokens else None,
    }


def _pair_delta(xfast: tuple[dict, dict], ufast: tuple[dict, dict]) -> dict:
    xrun, xscore = xfast
    urun, uscore = ufast
    speed = (
        100 * (xrun["elapsed_seconds"] - urun["elapsed_seconds"]) / xrun["elapsed_seconds"]
        if xrun["elapsed_seconds"]
        else None
    )
    xtokens = xrun["output_tokens"]
    utokens = urun["output_tokens"]
    token_change = (
        100 * (utokens - xtokens) / xtokens
        if xtokens not in (None, 0) and utokens is not None
        else None
    )
    return {
        "accuracy_points": round(uscore["score"] - xscore["score"], 4),
        "speed_percent": round(speed, 4) if speed is not None else None,
        "token_change_percent": round(token_change, 4) if token_change is not None else None,
        "token_pairs": int(token_change is not None),
    }


def _combined_delta(deltas: list[dict]) -> dict:
    speed = [item["speed_percent"] for item in deltas if item["speed_percent"] is not None]
    tokens = [
        item["token_change_percent"]
        for item in deltas
        if item["token_change_percent"] is not None
    ]
    return {
        "accuracy_points": round(mean(item["accuracy_points"] for item in deltas), 4),
        "speed_percent": round(mean(speed), 4) if speed else None,
        "token_change_percent": round(mean(tokens), 4) if tokens else None,
        "token_pairs": len(tokens),
    }


def summarize_ufast(result_dirs: list[Path]) -> dict:
    if len(result_dirs) != 2 or len(set(map(str, result_dirs))) != 2:
        raise ValueError("UFast report requires exactly two distinct result directories")

    current_hashes = current_source_hashes()
    models = {}
    run_ids = {}
    commits = {}
    codex_versions = {}
    all_pairs = []
    seen_targets = set()
    created_at = []

    for result in result_dirs:
        manifest = json.loads((result / "manifest.json").read_text(encoding="utf-8"))
        label, model, commit = _validate_manifest(manifest, result)
        target_id = manifest["config"]["target"]["id"]
        if target_id in seen_targets:
            raise ValueError(f"duplicate UFast target: {target_id}")
        seen_targets.add(target_id)
        if manifest["source_hashes"] != current_hashes:
            raise ValueError(f"UFast source drifted after run: {result}")

        raw = _read_jsonl(result / "raw.jsonl")
        scores = _index(_read_jsonl(result / "scores.jsonl"), "score")
        if len(raw) != 2 or len(scores) != 2:
            raise ValueError(f"UFast result must contain exactly two workloads: {result}")
        arms = {}
        for item in raw:
            run_id = item.get("run_id")
            if run_id not in scores:
                raise ValueError(f"missing UFast score: {run_id}")
            _validate_run(item, scores[run_id], target_id, model)
            condition = item["condition"]
            if condition in arms:
                raise ValueError(f"duplicate UFast condition: {condition}")
            arms[condition] = (item, scores[run_id])
        if set(arms) != set(EXPECTED_CONDITIONS):
            raise ValueError(f"incomplete UFast condition pair: {result}")
        if arms["nerd-xfast"][0]["changed_files"] != arms["nerd-ufast"][0]["changed_files"]:
            raise ValueError(f"UFast pair changed different files: {result}")

        delta = _pair_delta(arms["nerd-xfast"], arms["nerd-ufast"])
        models[label] = {
            "pairs": 1,
            "xfast": _arm_stats([arms["nerd-xfast"]]),
            "ufast": _arm_stats([arms["nerd-ufast"]]),
            "delta": delta,
        }
        all_pairs.append(arms)
        run_ids[label] = manifest["run_id"]
        commits[label] = commit
        codex_versions[label] = manifest.get("agent_versions", {}).get("codex")
        created_at.append(manifest.get("created_at", ""))

    if seen_targets != set(EXPECTED_TARGETS):
        raise ValueError("UFast report is missing Luna or Terra")
    if len(set(commits.values())) != 1:
        raise ValueError("UFast results use different source commits")

    xfast_items = [pair["nerd-xfast"] for pair in all_pairs]
    ufast_items = [pair["nerd-ufast"] for pair in all_pairs]
    deltas = [models[label]["delta"] for label in sorted(models)]
    return {
        "schema_version": 1,
        "created_at": max(created_at) if created_at else datetime.now(timezone.utc).isoformat(),
        "comparison": "nerd-ufast-vs-nerd-xfast-prompt-only",
        "controls": {
            "case_file": CASE_FILE,
            "case_sha256": CASE_SHA256,
            "case_ids": list(CASE_IDS),
            "conditions": list(EXPECTED_CONDITIONS),
            "models": 2,
            "repetitions": 1,
            "workload_runs": 4,
            "pairs": 2,
            "prompt_only": True,
        },
        "aggregate": {
            "pairs": 2,
            "xfast": _arm_stats(xfast_items),
            "ufast": _arm_stats(ufast_items),
            "delta": _combined_delta(deltas),
        },
        "models": models,
        "run_ids": run_ids,
        "provenance": {
            "nerd_commits": commits,
            "source_hashes": current_hashes,
            "codex_versions": codex_versions,
            "models": {label: model for _, (label, model) in EXPECTED_TARGETS.items()},
        },
        "artifacts": {
            "cases": CASE_FILE,
            "config_dir": "benchmarks/pilots/ufast-vs-xfast/",
            "result_summary": "benchmarks/pilots/ufast-vs-xfast/result.json",
        },
        "limitations": [
            "one Python discovery/edit verification case",
            "one repetition per model",
            "prompt discipline only; no UFast runtime or specialized tools",
            "directional evidence, not a universal latency claim",
        ],
    }


def _direction(value: float | None, positive: str, negative: str) -> str:
    if value is None:
        return "Unavailable"
    if value == 0:
        return "no change"
    return f"{abs(value):.2f}% {positive if value > 0 else negative}"


def _tokens(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value == 0:
        return "no change"
    return f"{abs(value):.2f}% {'more' if value > 0 else 'fewer'}"


def render_ufast_readme(summary: dict) -> str:
    aggregate = summary["aggregate"]
    delta = aggregate["delta"]
    lines = [
        "## UFast: prompt-only three-wave execution",
        "",
        "Nerd UFast currently contains prompt instructions and metadata only. It batches known context, known mutations, and proportionate proof into three waves while preserving the active workflow's accuracy contract. It has no bundled scripts, MCP server, registry, language server, or AST engine.",
        "",
        f"Across this directional pilot, UFast was {_direction(delta['speed_percent'], 'faster', 'slower')} than XFast. UFast used {_tokens(delta['token_change_percent'])} output tokens.",
        "",
        "| Model | XFast accuracy | UFast accuracy | Accuracy delta | XFast latency | UFast latency | Speed | XFast tokens | UFast tokens | Token change |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for label in ("Luna", "Terra"):
        item = summary["models"][label]
        lines.append(
            f"| {label} | {item['xfast']['mean_score']:.2f}% | {item['ufast']['mean_score']:.2f}% | {item['delta']['accuracy_points']:+.2f} points | "
            f"{item['xfast']['median_latency_seconds']:.2f}s | {item['ufast']['median_latency_seconds']:.2f}s | "
            f"{_direction(item['delta']['speed_percent'], 'faster', 'slower')} | "
            f"{item['xfast']['median_output_tokens'] if item['xfast']['median_output_tokens'] is not None else 'N/A'} | "
            f"{item['ufast']['median_output_tokens'] if item['ufast']['median_output_tokens'] is not None else 'N/A'} | "
            f"{_tokens(item['delta']['token_change_percent'])} |"
        )
    lines.extend(
        (
            f"| Combined | {aggregate['xfast']['mean_score']:.2f}% | {aggregate['ufast']['mean_score']:.2f}% | {delta['accuracy_points']:+.2f} points | "
            f"{aggregate['xfast']['median_latency_seconds']:.2f}s | {aggregate['ufast']['median_latency_seconds']:.2f}s | "
            f"{_direction(delta['speed_percent'], 'faster', 'slower')} | "
            f"{aggregate['xfast']['median_output_tokens'] if aggregate['xfast']['median_output_tokens'] is not None else 'N/A'} | "
            f"{aggregate['ufast']['median_output_tokens'] if aggregate['ufast']['median_output_tokens'] is not None else 'N/A'} | "
            f"{_tokens(delta['token_change_percent'])} |",
            "",
            "Method: one unchanged Python discovery/edit verification case, one repetition, and Luna plus Terra at `high` reasoning effort produced 4 fresh isolated Codex processes and 2 matched pairs. Both conditions ignored user configuration and used only their materialized skills plus platform-native tools. This tiny pilot measures prompt discipline, not future specialized-tool performance, and does not establish a universal speedup.",
            "",
            f"[Cases]({CASE_FILE}) · [Pilot configs](benchmarks/pilots/ufast-vs-xfast/) · [Result summary](benchmarks/pilots/ufast-vs-xfast/result.json)",
        )
    )
    return "\n".join(lines)


def write_ufast_summary(
    result_dirs: list[Path],
    output: Path,
    *,
    overwrite: bool = False,
) -> dict:
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite UFast summary: {output}")
    summary = summarize_ufast(result_dirs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def publish_ufast_readme(summary: dict, readme: Path, *, check: bool = False) -> None:
    body = readme.read_text(encoding="utf-8")
    if body.count(UFAST_START) > 1 or body.count(UFAST_END) > 1:
        raise ValueError("README contains duplicate UFast benchmark markers")
    region = f"{UFAST_START}\n{render_ufast_readme(summary)}\n{UFAST_END}"
    pattern = re.compile(
        rf"{re.escape(UFAST_START)}.*?{re.escape(UFAST_END)}",
        re.DOTALL,
    )
    updated = pattern.sub(region, body) if pattern.search(body) else body.rstrip() + "\n\n" + region + "\n"
    if check:
        if updated != body:
            raise ValueError("README UFast benchmark region is out of date")
        return
    readme.write_text(updated, encoding="utf-8")
