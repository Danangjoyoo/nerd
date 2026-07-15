"""Immutable benchmark data contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Criterion:
    id: str
    weight: int
    hard_gate: bool
    evaluator: str
    expected: str


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    comparison: str
    prompt: str
    fixture: str | None
    endpoint: str
    timeout_seconds: int
    criteria: tuple[Criterion, ...]


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    case_id: str
    condition: str
    agent: str
    model: str | None
    repetition: int
    workspace: Path
    target_id: str = "default"
    reasoning_effort: str | None = None


@dataclass(frozen=True)
class RunResult:
    spec: RunSpec
    exit_code: int
    elapsed_seconds: float
    final_text: str
    output_tokens: int | None
    events: tuple[dict, ...]
    changed_files: tuple[str, ...]
    command_results: dict[str, int]


@dataclass(frozen=True)
class ScoreResult:
    score: float
    passed: bool
    hard_gate_failures: tuple[str, ...]
    criterion_results: dict[str, bool]
