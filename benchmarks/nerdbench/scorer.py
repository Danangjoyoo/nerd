"""Deterministic scoring and blinded pair preparation."""

from __future__ import annotations

import random
import re
import json
from pathlib import Path

from .cases import load_cases
from .models import BenchmarkCase, RunResult, RunSpec, ScoreResult


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
    root = config["_root"]
    cases = {}
    for relative in config["case_files"]:
        for case in load_cases(root / relative):
            cases[case.id] = case
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
