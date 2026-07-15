"""Strict JSON loader for public benchmark cases."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BenchmarkCase, Criterion


EVALUATORS = {"regex", "absent_regex", "file", "command", "judge"}
CASE_FIELDS = {
    "id",
    "comparison",
    "prompt",
    "fixture",
    "endpoint",
    "timeout_seconds",
    "criteria",
}
CRITERION_FIELDS = {"id", "weight", "hard_gate", "evaluator", "expected"}


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _load_criterion(raw: object, case_id: str) -> Criterion:
    if not isinstance(raw, dict):
        raise ValueError(f"{case_id}: criterion must be an object")
    unknown = set(raw) - CRITERION_FIELDS
    if unknown:
        raise ValueError(f"{case_id}: unknown criterion fields: {sorted(unknown)}")
    missing = CRITERION_FIELDS - set(raw)
    if missing:
        raise ValueError(f"{case_id}: missing criterion fields: {sorted(missing)}")

    evaluator = _require_string(raw["evaluator"], "evaluator")
    if evaluator not in EVALUATORS:
        raise ValueError(f"{case_id}: unknown evaluator: {evaluator}")
    weight = raw["weight"]
    if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
        raise ValueError(f"{case_id}: criterion weight must be a positive integer")
    if not isinstance(raw["hard_gate"], bool):
        raise ValueError(f"{case_id}: hard_gate must be boolean")

    return Criterion(
        id=_require_string(raw["id"], "criterion id"),
        weight=weight,
        hard_gate=raw["hard_gate"],
        evaluator=evaluator,
        expected=_require_string(raw["expected"], "criterion expected"),
    )


def _load_case(raw: object) -> BenchmarkCase:
    if not isinstance(raw, dict):
        raise ValueError("case must be an object")
    unknown = set(raw) - CASE_FIELDS
    if unknown:
        raise ValueError(f"unknown case fields: {sorted(unknown)}")
    missing = CASE_FIELDS - set(raw)
    if missing:
        raise ValueError(f"missing case fields: {sorted(missing)}")

    case_id = _require_string(raw["id"], "case id")
    timeout = raw["timeout_seconds"]
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError(f"{case_id}: timeout_seconds must be positive")
    fixture = raw["fixture"]
    if fixture is not None:
        fixture = _require_string(fixture, "fixture")
    if not isinstance(raw["criteria"], list) or not raw["criteria"]:
        raise ValueError(f"{case_id}: criteria must be a non-empty list")

    criteria = tuple(_load_criterion(item, case_id) for item in raw["criteria"])
    ids = [item.id for item in criteria]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{case_id}: duplicate criterion id")
    if sum(item.weight for item in criteria) != 100:
        raise ValueError(f"{case_id}: criterion weights must total 100")
    if not any(item.hard_gate for item in criteria):
        raise ValueError(f"{case_id}: at least one criterion must be a hard gate")

    return BenchmarkCase(
        id=case_id,
        comparison=_require_string(raw["comparison"], "comparison"),
        prompt=_require_string(raw["prompt"], "prompt"),
        fixture=fixture,
        endpoint=_require_string(raw["endpoint"], "endpoint"),
        timeout_seconds=timeout,
        criteria=criteria,
    )


def load_cases(path: Path) -> tuple[BenchmarkCase, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load cases from {path}: {error}") from error
    if not isinstance(payload, dict) or set(payload) != {"cases"}:
        raise ValueError("case file must contain only a cases array")
    if not isinstance(payload["cases"], list):
        raise ValueError("cases must be an array")

    cases = tuple(_load_case(item) for item in payload["cases"])
    ids = [item.id for item in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case id")
    return cases
