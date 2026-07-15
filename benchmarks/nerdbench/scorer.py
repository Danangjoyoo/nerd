"""Deterministic scoring and blinded pair preparation."""

from __future__ import annotations

import random
import re
import json
import hashlib
from pathlib import Path
import subprocess
import time

from .cases import load_cases
from .adapters import get_adapter
from .models import BenchmarkCase, RunResult, RunSpec, ScoreResult


PAIR_CONDITIONS = {
    "smart": ("nerd-smart", "superpowers-brainstorming"),
    "surgery": ("nerd-surgery", "superpowers-systematic-debugging"),
    "execute": ("nerd-execute", "superpowers-executing-plans"),
    "silent": ("nerd-silent", "regular"),
}
JUDGE_SCHEMA = Path(__file__).resolve().parents[1] / "judge" / "schema.json"
JUDGE_INSTRUCTIONS = """Evaluate outputs A and B independently against each supplied criterion.
Use only the user prompt, allowed scope, criterion labels, and the anonymized outputs.
Do not infer hidden run metadata or aggregate results.
Return only JSON matching the supplied schema."""


def _command_expected(value: str) -> tuple[str, int]:
    command, separator, exit_text = value.rpartition("::")
    if not separator:
        return value, 0
    try:
        expected_exit = int(exit_text)
    except ValueError as error:
        raise ValueError(f"invalid command expectation: {value}") from error
    return command, expected_exit


def _evaluate(
    evaluator: str,
    expected: str,
    run: RunResult,
    judge: dict | None,
    criterion_id: str,
) -> bool:
    if evaluator == "regex":
        return re.search(expected, run.final_text, re.MULTILINE) is not None
    if evaluator == "absent_regex":
        return re.search(expected, run.final_text, re.MULTILINE) is None
    if evaluator == "file":
        return expected in run.changed_files
    if evaluator == "command":
        command, expected_exit = _command_expected(expected)
        return run.command_results.get(command) == expected_exit
    if evaluator == "judge":
        return bool(judge and judge.get(criterion_id) is True)
    raise ValueError(f"unknown evaluator: {evaluator}")


def score_run(
    case: BenchmarkCase,
    run: RunResult,
    judge: dict | None,
) -> ScoreResult:
    if run.exit_code != 0:
        results = {criterion.id: False for criterion in case.criteria}
    else:
        results = {
            criterion.id: _evaluate(
                criterion.evaluator,
                criterion.expected,
                run,
                judge,
                criterion.id,
            )
            for criterion in case.criteria
        }
    score = float(
        sum(
            criterion.weight
            for criterion in case.criteria
            if results[criterion.id]
        )
    )
    hard_failures = tuple(
        criterion.id
        for criterion in case.criteria
        if criterion.hard_gate and not results[criterion.id]
    )
    return ScoreResult(
        score=score,
        passed=score >= 80 and not hard_failures,
        hard_gate_failures=hard_failures,
        criterion_results=results,
    )


def blind_pair(
    left: RunResult,
    right: RunResult,
    rng: random.Random,
) -> tuple[dict[str, str], dict[str, str]]:
    runs = [left, right]
    rng.shuffle(runs)
    payload = {"A": runs[0].final_text, "B": runs[1].final_text}
    mapping = {"A": runs[0].spec.run_id, "B": runs[1].spec.run_id}
    return payload, mapping


def build_judge_prompt(case: BenchmarkCase, outputs: dict[str, str]) -> str:
    criterion_labels = {
        criterion.id: criterion.expected
        for criterion in case.criteria
        if criterion.evaluator == "judge"
    }
    request = {
        "user_prompt": case.prompt,
        "allowed_scope": case.endpoint,
        "criteria": criterion_labels,
        "outputs": {"A": outputs["A"], "B": outputs["B"]},
    }
    return JUDGE_INSTRUCTIONS + "\n\n" + json.dumps(
        request,
        indent=2,
        sort_keys=True,
    )


def build_judge_command(
    schema: Path,
    prompt: str,
    *,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--json",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ignore-rules",
        "--output-schema",
        str(schema),
    ]
    if model:
        command.extend(["--model", model])
    if reasoning_effort:
        command.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])
    command.append(prompt)
    return command


def judge_output_schema(case: BenchmarkCase) -> dict:
    decision = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "A": {"type": "boolean"},
            "B": {"type": "boolean"},
            "evidence": {"type": "string"},
        },
        "required": ["A", "B", "evidence"],
    }
    criterion_ids = [
        item.id for item in case.criteria if item.evaluator == "judge"
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "criteria": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    criterion_id: decision for criterion_id in criterion_ids
                },
                "required": criterion_ids,
            }
        },
        "required": ["criteria"],
    }


def validate_judge_result(result: object, criterion_ids: tuple[str, ...]) -> dict:
    if not isinstance(result, dict) or set(result) != {"criteria"}:
        raise ValueError("judge result must contain only criteria")
    criteria = result["criteria"]
    if not isinstance(criteria, dict) or set(criteria) != set(criterion_ids):
        raise ValueError("judge criteria do not match requested criteria")
    for criterion_id, value in criteria.items():
        if not isinstance(value, dict):
            raise ValueError(f"judge criterion {criterion_id} must be an object")
        if set(value) != {"A", "B", "evidence"}:
            raise ValueError(
                f"judge criterion {criterion_id} must contain A, B, and evidence"
            )
        if not isinstance(value["A"], bool) or not isinstance(value["B"], bool):
            raise ValueError(f"judge criterion {criterion_id} decisions must be boolean")
        if not isinstance(value["evidence"], str) or not value["evidence"].strip():
            raise ValueError(f"judge criterion {criterion_id} needs evidence")
    return result


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _case_index(config: dict) -> dict[str, BenchmarkCase]:
    cases = {}
    for relative in config["case_files"]:
        for case in load_cases(config["_root"] / relative):
            cases[case.id] = case
    return cases


def _pair_seed(seed: int, identity: str) -> int:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return seed + int(digest[:8], 16)


def judge_tasks(
    records: list[dict],
    cases: dict[str, BenchmarkCase],
    seed: int,
) -> list[dict]:
    grouped: dict[tuple, dict[str, dict]] = {}
    patrol = []
    for record in records:
        case = cases[record["case_id"]]
        if not any(item.evaluator == "judge" for item in case.criteria):
            continue
        if case.comparison == "patrol":
            patrol.append(record)
            continue
        identity = (
            record.get("target_id", "default"),
            record["case_id"],
            record["agent"],
            record.get("model"),
            record.get("reasoning_effort"),
            int(record["repetition"]),
        )
        grouped.setdefault(identity, {})[record["condition"]] = record

    tasks = []
    for identity, arms in sorted(grouped.items(), key=lambda item: repr(item[0])):
        case = cases[identity[1]]
        expected = PAIR_CONDITIONS[case.comparison]
        if not all(condition in arms for condition in expected):
            continue
        left = _run_result(arms[expected[0]])
        right = _run_result(arms[expected[1]])
        identity_text = "::".join(str(value) for value in identity)
        outputs, mapping = blind_pair(
            left,
            right,
            random.Random(_pair_seed(seed, identity_text)),
        )
        tasks.append(
            {
                "task_id": identity_text,
                "case_id": case.id,
                "outputs": outputs,
                "mapping": mapping,
            }
        )

    for record in sorted(patrol, key=lambda item: item["run_id"]):
        tasks.append(
            {
                "task_id": "patrol::" + record["run_id"],
                "case_id": record["case_id"],
                "outputs": {"A": record.get("final_text", ""), "B": record.get("final_text", "")},
                "mapping": {"A": record["run_id"], "B": record["run_id"]},
            }
        )
    return tasks


def _invoke_judge(
    prompt: str,
    config: dict,
    workspace: Path,
    case: BenchmarkCase,
) -> tuple[dict, float]:
    judge = config["judge"]
    schema_path = workspace / "judge-output-schema.json"
    schema_path.write_text(
        json.dumps(judge_output_schema(case), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    command = build_judge_command(
        schema_path,
        prompt,
        model=judge.get("model"),
        reasoning_effort=judge.get("reasoning_effort"),
    )
    started = time.monotonic()
    process = subprocess.run(
        command,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=judge["timeout_seconds"],
    )
    elapsed = time.monotonic() - started
    if process.returncode != 0:
        raise RuntimeError(
            f"judge exited {process.returncode}: {process.stderr.strip()}"
        )
    final, _, _ = get_adapter("codex").parse(process.stdout, process.stderr)
    try:
        result = json.loads(final)
    except json.JSONDecodeError as error:
        raise ValueError("judge did not return valid JSON") from error
    return result, elapsed


def judge_result_directory(result_dir: Path, config: dict) -> list[dict]:
    cases = _case_index(config)
    records = _read_jsonl(result_dir / "raw.jsonl")
    tasks = judge_tasks(records, cases, int(config["seed"]))
    output_path = result_dir / "judges.jsonl"
    existing = _read_jsonl(output_path)
    completed = {record["task_id"] for record in existing}
    workspace = config["_root"] / "benchmarks" / "work" / (
        result_dir.name + "-judge"
    )
    workspace.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as output:
        for task in tasks:
            if task["task_id"] in completed:
                continue
            case = cases[task["case_id"]]
            prompt = build_judge_prompt(case, task["outputs"])
            result, elapsed = _invoke_judge(prompt, config, workspace, case)
            criterion_ids = tuple(
                item.id for item in case.criteria if item.evaluator == "judge"
            )
            result = validate_judge_result(result, criterion_ids)
            if task["mapping"]["A"] == task["mapping"]["B"]:
                for criterion in result["criteria"].values():
                    if criterion["A"] != criterion["B"]:
                        raise ValueError("judge disagreed on duplicated Patrol output")
            record = {
                "task_id": task["task_id"],
                "case_id": case.id,
                "mapping": task["mapping"],
                "criteria": result["criteria"],
                "judge_agent": config["judge"]["agent"],
                "judge_model": config["judge"].get("model"),
                "elapsed_seconds": elapsed,
            }
            output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()
            existing.append(record)
    return existing


def _judge_index(result_dir: Path, cases: dict[str, BenchmarkCase]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for record in _read_jsonl(result_dir / "judges.jsonl"):
        mapping = record.get("mapping")
        if not isinstance(mapping, dict) or set(mapping) != {"A", "B"}:
            raise ValueError("judge record mapping must contain A and B")
        case_id = record.get("case_id")
        if case_id not in cases:
            raise ValueError(f"judge record has unknown case: {case_id}")
        criterion_ids = tuple(
            item.id for item in cases[case_id].criteria if item.evaluator == "judge"
        )
        validated = validate_judge_result(
            {"criteria": record.get("criteria")},
            criterion_ids,
        )
        for label, run_id in mapping.items():
            index.setdefault(run_id, {}).update(
                {
                    criterion_id: value[label]
                    for criterion_id, value in validated["criteria"].items()
                }
            )
    return index


def _run_result(record: dict) -> RunResult:
    spec = RunSpec(
        run_id=record["run_id"],
        case_id=record["case_id"],
        condition=record["condition"],
        agent=record["agent"],
        model=record.get("model"),
        repetition=int(record["repetition"]),
        workspace=Path("."),
        target_id=record.get("target_id", "default"),
        reasoning_effort=record.get("reasoning_effort"),
    )
    return RunResult(
        spec=spec,
        exit_code=int(record["exit_code"]),
        elapsed_seconds=float(record["elapsed_seconds"]),
        final_text=record.get("final_text", ""),
        output_tokens=record.get("output_tokens"),
        events=tuple(record.get("events", ())),
        changed_files=tuple(record.get("changed_files", ())),
        command_results={
            str(key): int(value)
            for key, value in record.get("command_results", {}).items()
        },
    )


def score_result_directory(result_dir: Path, config: dict) -> list[dict]:
    cases = _case_index(config)
    judges = _judge_index(result_dir, cases)
    score_records = []
    for record in _read_jsonl(result_dir / "raw.jsonl"):
        case = cases[record["case_id"]]
        judge_ids = tuple(
            criterion.id
            for criterion in case.criteria
            if criterion.evaluator == "judge"
        )
        run_judge = judges.get(record["run_id"], {})
        judge_valid = all(criterion_id in run_judge for criterion_id in judge_ids)
        scored = score_run(case, _run_result(record), run_judge)
        score_records.append(
            {
                "run_id": record["run_id"],
                "score": scored.score,
                "passed": scored.passed,
                "hard_gate_failures": list(scored.hard_gate_failures),
                "criterion_results": scored.criterion_results,
                "judge_valid": judge_valid,
            }
        )
    body = "".join(
        json.dumps(item, sort_keys=True) + "\n"
        for item in score_records
    )
    (result_dir / "scores.jsonl").write_text(body, encoding="utf-8")
    return score_records
