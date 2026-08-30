from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
import time
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Mapping, Sequence

from .shared_memory import SharedBehaviorMemory


EXPERIMENT_SCHEMA = "paired-agent-experiment/v1"
ANSWER_SCHEMA = "paired-agent-answer/v1"
BEHAVIOR_ID = "bhv-i006-ivory-kestrel"
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)

TEACHER_TRACE: dict[str, Any] = {
    "behavior_id": BEHAVIOR_ID,
    "cue_phrases": [
        "Apply ivory kestrel to this settlement batch",
        "Process this reconciliation with ivory kestrel",
        "Use ivory kestrel for ledger normalization",
    ],
    "action": "reconcile_ivory_batch",
    "tools": ["python", "json", "decimal", "hashlib"],
    "steps": [
        "Normalize account with strip and uppercase; normalize region and status with strip and lowercase",
        "Keep only records whose normalized status is approved",
        "Deduplicate by normalized account using highest integer revision, then lexicographically smallest transaction_id on a tie",
        "Convert amount to integer cents with Decimal times 100 and ROUND_HALF_EVEN",
        "Set risk to review when cents are at least 100000 or region is xx or zz; otherwise set clear",
        "Sort output records by region, account, then transaction_id",
        "Summarize record_count, total_cents, and sorted region_totals",
        "Emit exactly batch_id, records, summary, and batch_fingerprint; each record contains transaction_id, account, region, amount_cents, and risk only",
        "Hash canonical compact sorted-key JSON of records and summary with SHA256 and keep the first 16 hexadecimal characters",
    ],
    "skills": ["data-normalization", "deterministic-validation"],
    "invalid_signals": [
        "The output fingerprint does not match the canonical records and summary"
    ],
}

MEMORY_PROTOCOL = """You are the memory-enabled arm. Read only the assigned public card and input. Query the experimental shared-memory CLI exactly once with the assigned trial ID, save the recall JSON, follow the recalled advisory procedure exactly, write the required answer JSON, then finalize. Do not inspect private gold, teacher artifacts, source code, control outputs, or the SQLite file directly."""

CONTROL_PROTOCOL = """You are the memory-blind control arm. Read only the assigned public card and input. Do not query or inspect behavioral memory, recall files, private gold, teacher artifacts, source code, or another agent's output. Solve the task using only the public card, write the required answer JSON, then finalize."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _lexical_tokens(value: str) -> int:
    return len(TOKEN_RE.findall(value))


def expected_output(source: Mapping[str, Any]) -> dict[str, Any]:
    selected: dict[str, dict[str, Any]] = {}
    for raw in source["records"]:
        status = str(raw["status"]).strip().lower()
        if status != "approved":
            continue
        account = str(raw["account"]).strip().upper()
        candidate = {
            "transaction_id": str(raw["transaction_id"]),
            "account": account,
            "region": str(raw["region"]).strip().lower(),
            "revision": int(raw["revision"]),
            "amount": str(raw["amount"]),
        }
        current = selected.get(account)
        if (
            current is None
            or candidate["revision"] > current["revision"]
            or (
                candidate["revision"] == current["revision"]
                and candidate["transaction_id"] < current["transaction_id"]
            )
        ):
            selected[account] = candidate

    records: list[dict[str, Any]] = []
    for item in selected.values():
        amount_cents = int(
            (Decimal(item["amount"]) * Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_EVEN
            )
        )
        records.append(
            {
                "transaction_id": item["transaction_id"],
                "account": item["account"],
                "region": item["region"],
                "amount_cents": amount_cents,
                "risk": "review"
                if amount_cents >= 100_000 or item["region"] in {"xx", "zz"}
                else "clear",
            }
        )
    records.sort(key=lambda item: (item["region"], item["account"], item["transaction_id"]))
    region_totals: dict[str, int] = {}
    for item in records:
        region_totals[item["region"]] = region_totals.get(item["region"], 0) + item[
            "amount_cents"
        ]
    summary = {
        "record_count": len(records),
        "total_cents": sum(item["amount_cents"] for item in records),
        "region_totals": dict(sorted(region_totals.items())),
    }
    fingerprint_payload = {"records": records, "summary": summary}
    fingerprint = hashlib.sha256(
        _canonical_json(fingerprint_payload).encode()
    ).hexdigest()[:16]
    return {
        "batch_id": source["batch_id"],
        "records": records,
        "summary": summary,
        "batch_fingerprint": fingerprint,
    }


def _make_input(seed: int, batch_index: int) -> dict[str, Any]:
    randomizer = random.Random(seed + batch_index * 997)
    accounts = ["a-17", "b-04", "c-92", "d-31", "e-08", "f-55"]
    regions = ["us", "eu", "apac", "xx", "ca", "zz"]
    records: list[dict[str, Any]] = []
    for index, account in enumerate(accounts):
        region = regions[(index + batch_index) % len(regions)]
        amount_whole = randomizer.randint(25, 1800)
        mills = randomizer.choice(["005", "015", "025", "995"])
        display_account = f" {account.lower()} " if index % 2 == 0 else account.upper()
        records.append(
            {
                "transaction_id": f"b{batch_index:02d}-a{index:02d}",
                "account": display_account,
                "region": region.upper() if index % 2 else region,
                "status": "APPROVED" if index % 2 else " approved ",
                "revision": 1,
                "amount": f"{amount_whole}.{mills}",
            }
        )
        if index % 2 == batch_index % 2:
            records.append(
                {
                    "transaction_id": f"b{batch_index:02d}-z{index:02d}",
                    "account": account.upper(),
                    "region": regions[(index + batch_index + 1) % len(regions)],
                    "status": "approved",
                    "revision": 2,
                    "amount": f"{amount_whole + 100}.{mills}",
                }
            )
    records.append(
        {
            "transaction_id": f"b{batch_index:02d}-pending",
            "account": "a-17",
            "region": "zz",
            "status": "pending",
            "revision": 9,
            "amount": "9999.995",
        }
    )
    randomizer.shuffle(records)
    return {"batch_id": f"settlement-{batch_index:02d}", "records": records}


def prepare(experiment_dir: Path, *, seed: int = 606) -> dict[str, Any]:
    experiment_dir = Path(experiment_dir)
    teacher_input = _make_input(seed, 0)
    teacher_digest = _digest(teacher_input)
    _write_json(experiment_dir / "teacher" / "input.json", teacher_input)
    _write_json(
        experiment_dir / "teacher" / "card.json",
        {
            "schema_version": EXPERIMENT_SCHEMA,
            "round": 0,
            "arm": "teacher",
            "command": TEACHER_TRACE["cue_phrases"][0],
            "input_path": "teacher/input.json",
            "input_digest": teacher_digest,
            "private_procedure_path": "private/procedure.json",
            "response_path": "teacher/response.json",
        },
    )
    procedure = {
            "schema_version": EXPERIMENT_SCHEMA,
            "behavior_trace": TEACHER_TRACE,
            "required_answer_schema": ANSWER_SCHEMA,
            "output_contract": {
                "top_level_fields": [
                    "batch_id",
                    "records",
                    "summary",
                    "batch_fingerprint",
                ],
                "record_fields": [
                    "transaction_id",
                    "account",
                    "region",
                    "amount_cents",
                    "risk",
                ],
                "summary_fields": [
                    "record_count",
                    "total_cents",
                    "region_totals",
                ],
                "fingerprint_input": {
                    "records": "the final records array",
                    "summary": "the final summary object",
                },
                "canonical_json": "UTF-8 JSON with sorted keys and separators comma/colon, no spaces",
            },
        }
    _write_json(experiment_dir / "private" / "procedure.json", procedure)
    _write_json(
        experiment_dir / "private" / "gold" / "teacher.json",
        expected_output(teacher_input),
    )
    (experiment_dir / "protocols").mkdir(parents=True, exist_ok=True)
    (experiment_dir / "protocols" / "memory.txt").write_text(
        MEMORY_PROTOCOL + "\n", encoding="utf-8"
    )
    (experiment_dir / "protocols" / "control.txt").write_text(
        CONTROL_PROTOCOL + "\n", encoding="utf-8"
    )

    round_digests: dict[str, str] = {}
    for round_number in range(1, 6):
        round_key = f"round-{round_number:02d}"
        round_input = _make_input(seed, round_number)
        input_digest = _digest(round_input)
        round_digests[round_key] = input_digest
        round_dir = experiment_dir / "rounds" / round_key
        _write_json(round_dir / "input.json", round_input)
        _write_json(
            round_dir / "card.json",
            {
                "schema_version": EXPERIMENT_SCHEMA,
                "round": round_number,
                "command": TEACHER_TRACE["cue_phrases"][round_number % 3],
                "input_path": f"rounds/{round_key}/input.json",
                "input_digest": input_digest,
                "memory_response_path": f"responses/{round_key}-memory.json",
                "control_response_path": f"responses/{round_key}-control.json",
                "required_answer_schema": ANSWER_SCHEMA,
            },
        )
        _write_json(
            experiment_dir / "private" / "gold" / f"{round_key}.json",
            expected_output(round_input),
        )
    manifest = {
        "schema_version": EXPERIMENT_SCHEMA,
        "seed": seed,
        "round_count": 5,
        "teacher_input_digest": teacher_digest,
        "private_procedure_digest": _digest(procedure),
        "round_input_digests": round_digests,
        "token_measure": {
            "name": "observable_lexical_tokens",
            "pattern": TOKEN_RE.pattern,
            "includes": ["arm_protocol", "public_card", "recall_advice", "submitted_answer"],
            "excludes": [
                "system_and_developer_prompts",
                "hidden_reasoning",
                "tool_traffic",
                "billed_model_tokens",
            ],
        },
    }
    manifest["canonical_digest"] = _digest(manifest)
    _write_json(experiment_dir / "manifest.json", manifest)
    return manifest


def verify_teacher_and_record(
    memory: SharedBehaviorMemory,
    experiment_dir: Path,
    response_path: Path,
) -> dict[str, Any]:
    experiment_dir = Path(experiment_dir)
    response = _read_json(response_path)
    card = _read_json(experiment_dir / "teacher" / "card.json")
    gold = _read_json(experiment_dir / "private" / "gold" / "teacher.json")
    if response.get("schema_version") != ANSWER_SCHEMA:
        raise ValueError("teacher answer schema mismatch")
    if response.get("round") != 0 or response.get("arm") != "teacher":
        raise ValueError("teacher answer identity mismatch")
    if response.get("input_digest") != card["input_digest"]:
        raise ValueError("teacher input digest mismatch")
    if response.get("output") != gold:
        raise ValueError("teacher output did not pass exact verification")
    if response.get("behavior_trace") != TEACHER_TRACE:
        raise ValueError("teacher behavior trace does not match the performed procedure")

    record = memory.record(
        behavior_id=TEACHER_TRACE["behavior_id"],
        cue_phrases=TEACHER_TRACE["cue_phrases"],
        action=TEACHER_TRACE["action"],
        tools=TEACHER_TRACE["tools"],
        steps=TEACHER_TRACE["steps"],
        skills=TEACHER_TRACE["skills"],
        invalid_signals=TEACHER_TRACE["invalid_signals"],
        source_agent="iteration006-teacher",
        source_repository="teacher-finance-repository",
        verification_id="verify-i006-" + _digest(gold).split(":", 1)[1][:16],
        verified=True,
    )
    verdict = {
        "schema_version": EXPERIMENT_SCHEMA,
        "passed": True,
        "teacher_output_exact": True,
        "behavior_id": record["behavior_id"],
        "input_digest": card["input_digest"],
        "output_digest": _digest(gold),
        "recorded_behavior_count": memory.behavior_count(),
    }
    verdict["canonical_digest"] = _digest(verdict)
    _write_json(experiment_dir / "teacher" / "verdict.json", verdict)
    return verdict


def start_round(
    experiment_dir: Path,
    round_number: int,
    *,
    spawn_order: Sequence[str],
    now_ns: int | None = None,
) -> dict[str, Any]:
    if tuple(spawn_order) not in {("memory", "control"), ("control", "memory")}:
        raise ValueError("spawn order must contain memory and control exactly once")
    path = Path(experiment_dir) / "timing" / f"round-{round_number:02d}-start.json"
    if path.exists():
        raise ValueError(f"round {round_number} already started")
    card = _read_json(
        Path(experiment_dir) / "rounds" / f"round-{round_number:02d}" / "card.json"
    )
    started_at = time.time_ns() if now_ns is None else now_ns
    record = {
        "schema_version": EXPERIMENT_SCHEMA,
        "round": round_number,
        "input_digest": card["input_digest"],
        "spawn_order": list(spawn_order),
        "started_at_unix_ns": started_at,
    }
    _write_json(path, record)
    return record


def finalize(
    experiment_dir: Path,
    round_number: int,
    arm: str,
    response_path: Path,
    *,
    recall_path: Path | None = None,
    now_ns: int | None = None,
) -> dict[str, Any]:
    if arm not in {"memory", "control"}:
        raise ValueError("arm must be memory or control")
    experiment_dir = Path(experiment_dir)
    submission_path = (
        experiment_dir / "submissions" / f"round-{round_number:02d}-{arm}.json"
    )
    if submission_path.exists():
        raise ValueError(f"round {round_number} {arm} already finalized")
    card = _read_json(
        experiment_dir / "rounds" / f"round-{round_number:02d}" / "card.json"
    )
    start = _read_json(
        experiment_dir / "timing" / f"round-{round_number:02d}-start.json"
    )
    response = _read_json(response_path)
    if response.get("schema_version") != ANSWER_SCHEMA:
        raise ValueError("answer schema mismatch")
    if response.get("round") != round_number or response.get("arm") != arm:
        raise ValueError("answer identity mismatch")
    if response.get("input_digest") != card["input_digest"]:
        raise ValueError("answer input digest mismatch")
    if not isinstance(response.get("output"), dict):
        raise ValueError("answer output must be an object")

    recall: dict[str, Any] | None = None
    if arm == "memory":
        if recall_path is None:
            raise ValueError("memory answer requires recall evidence")
        recall = _read_json(recall_path)
        if recall.get("status") != "recalled" or recall.get("behavior_id") != BEHAVIOR_ID:
            raise ValueError("memory recall did not return the verified behavior")
    elif recall_path is not None:
        raise ValueError("control answer cannot include recall evidence")

    protocol = (experiment_dir / "protocols" / f"{arm}.txt").read_text(encoding="utf-8")
    token_parts = {
        "arm_protocol": _lexical_tokens(protocol),
        "public_card": _lexical_tokens(_canonical_json(card)),
        "recall_advice": _lexical_tokens(_canonical_json(recall)) if recall else 0,
        "submitted_answer": _lexical_tokens(_canonical_json(response)),
    }
    finished_at = time.time_ns() if now_ns is None else now_ns
    elapsed_seconds = (finished_at - start["started_at_unix_ns"]) / 1_000_000_000
    if elapsed_seconds < 0:
        raise ValueError("finalization precedes round start")
    submission = {
        "schema_version": EXPERIMENT_SCHEMA,
        "round": round_number,
        "arm": arm,
        "input_digest": card["input_digest"],
        "output": response["output"],
        "recall": recall,
        "timing": {
            "started_at_unix_ns": start["started_at_unix_ns"],
            "finalized_at_unix_ns": finished_at,
            "elapsed_seconds": elapsed_seconds,
            "spawn_order": start["spawn_order"],
        },
        "observable_lexical_tokens": {
            "parts": token_parts,
            "total": sum(token_parts.values()),
        },
    }
    _write_json(submission_path, submission)
    return submission


def _flatten(value: Any, path: str = "$") -> dict[str, Any]:
    if isinstance(value, dict):
        flattened: dict[str, Any] = {}
        for key in sorted(value):
            flattened.update(_flatten(value[key], f"{path}.{key}"))
        return flattened
    if isinstance(value, list):
        flattened = {}
        for index, item in enumerate(value):
            flattened.update(_flatten(item, f"{path}[{index}]"))
        return flattened
    return {path: value}


def _leaf_accuracy(actual: Any, expected: Any) -> float:
    actual_flat = _flatten(actual)
    expected_flat = _flatten(expected)
    paths = set(actual_flat) | set(expected_flat)
    if not paths:
        return 1.0
    matches = sum(actual_flat.get(path) == expected_flat.get(path) for path in paths)
    return matches / len(paths)


def _summary(values: Sequence[float]) -> dict[str, float]:
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "population_stddev": statistics.pstdev(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def evaluate(memory: SharedBehaviorMemory, experiment_dir: Path) -> dict[str, Any]:
    experiment_dir = Path(experiment_dir)
    teacher = _read_json(experiment_dir / "teacher" / "verdict.json")
    per_round: list[dict[str, Any]] = []
    exact_by_arm: dict[str, list[float]] = {"memory": [], "control": []}
    leaf_by_arm: dict[str, list[float]] = {"memory": [], "control": []}
    speed_by_arm: dict[str, list[float]] = {"memory": [], "control": []}
    tokens_by_arm: dict[str, list[float]] = {"memory": [], "control": []}
    matched_inputs = True
    for round_number in range(1, 6):
        round_key = f"round-{round_number:02d}"
        gold = _read_json(experiment_dir / "private" / "gold" / f"{round_key}.json")
        submissions = {
            arm: _read_json(
                experiment_dir / "submissions" / f"{round_key}-{arm}.json"
            )
            for arm in ("memory", "control")
        }
        matched_inputs = matched_inputs and (
            submissions["memory"]["input_digest"]
            == submissions["control"]["input_digest"]
            == _read_json(experiment_dir / "rounds" / round_key / "card.json")[
                "input_digest"
            ]
        )
        round_result: dict[str, Any] = {"round": round_number, "arms": {}}
        for arm, submission in submissions.items():
            exact = float(submission["output"] == gold)
            leaf = _leaf_accuracy(submission["output"], gold)
            elapsed = float(submission["timing"]["elapsed_seconds"])
            tokens = float(submission["observable_lexical_tokens"]["total"])
            exact_by_arm[arm].append(exact)
            leaf_by_arm[arm].append(leaf)
            speed_by_arm[arm].append(elapsed)
            tokens_by_arm[arm].append(tokens)
            round_result["arms"][arm] = {
                "exact_accuracy": exact,
                "leaf_accuracy": leaf,
                "elapsed_seconds": elapsed,
                "observable_lexical_tokens": int(tokens),
            }
        round_result["paired_differences"] = {
            "exact_accuracy": round_result["arms"]["memory"]["exact_accuracy"]
            - round_result["arms"]["control"]["exact_accuracy"],
            "leaf_accuracy": round_result["arms"]["memory"]["leaf_accuracy"]
            - round_result["arms"]["control"]["leaf_accuracy"],
            "elapsed_seconds": round_result["arms"]["memory"]["elapsed_seconds"]
            - round_result["arms"]["control"]["elapsed_seconds"],
            "observable_lexical_tokens": round_result["arms"]["memory"][
                "observable_lexical_tokens"
            ]
            - round_result["arms"]["control"]["observable_lexical_tokens"],
        }
        per_round.append(round_result)

    events = memory.recall_events()
    event_counts: dict[str, int] = {}
    for event in events:
        event_counts[event["trial_id"]] = event_counts.get(event["trial_id"], 0) + 1
    memory_recall_once = all(
        event_counts.get(f"iteration006-round-{round_number:02d}-memory") == 1
        for round_number in range(1, 6)
    )
    control_recall_zero = all(
        event_counts.get(f"iteration006-round-{round_number:02d}-control", 0) == 0
        for round_number in range(1, 6)
    )

    paired_exact = [
        memory - control
        for memory, control in zip(exact_by_arm["memory"], exact_by_arm["control"])
    ]
    paired_leaf = [
        memory - control
        for memory, control in zip(leaf_by_arm["memory"], leaf_by_arm["control"])
    ]
    paired_speed = [
        memory - control
        for memory, control in zip(speed_by_arm["memory"], speed_by_arm["control"])
    ]
    paired_tokens = [
        memory - control
        for memory, control in zip(tokens_by_arm["memory"], tokens_by_arm["control"])
    ]
    accuracy = {
        arm: {
            "exact_mean": statistics.mean(exact_by_arm[arm]),
            "exact_median": statistics.median(exact_by_arm[arm]),
            "leaf_mean": statistics.mean(leaf_by_arm[arm]),
            "leaf_median": statistics.median(leaf_by_arm[arm]),
        }
        for arm in ("memory", "control")
    }
    accuracy["paired_exact_gain_mean"] = statistics.mean(paired_exact)
    accuracy["paired_leaf_gain_mean"] = statistics.mean(paired_leaf)
    speed_summary = {arm: _summary(speed_by_arm[arm]) for arm in ("memory", "control")}
    speed_summary["paired_memory_minus_control"] = _summary(paired_speed)
    token_summary = {arm: _summary(tokens_by_arm[arm]) for arm in ("memory", "control")}
    token_summary["paired_memory_minus_control"] = _summary(paired_tokens)
    condition_audit = {
        "memory_recall_once": memory_recall_once,
        "control_recall_zero": control_recall_zero,
        "recorded_recall_event_count": len(events),
    }
    relative_comparison = {
        "exact_accuracy_gain_percentage_points": accuracy[
            "paired_exact_gain_mean"
        ]
        * 100,
        "leaf_accuracy_gain_percentage_points": accuracy["paired_leaf_gain_mean"]
        * 100,
        "memory_time_change_percent_vs_control": (
            (speed_summary["memory"]["mean"] / speed_summary["control"]["mean"])
            - 1
        )
        * 100,
        "memory_token_proxy_change_percent_vs_control": (
            (token_summary["memory"]["mean"] / token_summary["control"]["mean"])
            - 1
        )
        * 100,
        "rounds_memory_faster": sum(
            difference < 0 for difference in paired_speed
        ),
        "rounds_memory_lower_token_proxy": sum(
            difference < 0 for difference in paired_tokens
        ),
    }
    criteria = {
        "F1_teacher_verification": teacher.get("passed") is True
        and teacher.get("recorded_behavior_count") == 1,
        "F2_replication_completeness": len(per_round) == 5,
        "F3_matched_inputs": matched_inputs,
        "F4_recall_isolation": memory_recall_once and control_recall_zero,
        "F5_memory_accuracy": accuracy["memory"]["exact_mean"] >= 0.80,
        "F6_paired_advantage": accuracy["paired_exact_gain_mean"] >= 0.40,
        "F7_cost_reporting": all(
            key in speed_summary and key in token_summary
            for key in ("memory", "control", "paired_memory_minus_control")
        ),
    }
    result: dict[str, Any] = {
        "schema_version": EXPERIMENT_SCHEMA,
        "teacher": teacher,
        "round_count": 5,
        "accuracy": accuracy,
        "speed_seconds": speed_summary,
        "observable_lexical_tokens": token_summary,
        "token_measure_limit": "Proxy excludes system/developer prompts, hidden reasoning, tool traffic, and billed model tokens.",
        "condition_audit": condition_audit,
        "relative_comparison": relative_comparison,
        "per_round": per_round,
        "criteria": {key: "PASS" if passed else "FAIL" for key, passed in criteria.items()},
        "passed": all(criteria.values()),
    }
    result["canonical_digest"] = _digest(result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Iteration 006 paired-agent experiment")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--experiment-dir", type=Path, required=True)
    prepare_parser.add_argument("--seed", type=int, default=606)

    teacher = subparsers.add_parser("record-teacher")
    teacher.add_argument("--db", type=Path, required=True)
    teacher.add_argument("--experiment-dir", type=Path, required=True)
    teacher.add_argument("--response", type=Path, required=True)

    start = subparsers.add_parser("start-round")
    start.add_argument("--experiment-dir", type=Path, required=True)
    start.add_argument("--round", type=int, required=True)
    start.add_argument("--spawn-order", nargs=2, required=True)

    finish = subparsers.add_parser("finalize")
    finish.add_argument("--experiment-dir", type=Path, required=True)
    finish.add_argument("--round", type=int, required=True)
    finish.add_argument("--arm", choices=("memory", "control"), required=True)
    finish.add_argument("--response", type=Path, required=True)
    finish.add_argument("--recall", type=Path)

    score = subparsers.add_parser("evaluate")
    score.add_argument("--db", type=Path, required=True)
    score.add_argument("--experiment-dir", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "prepare":
        result = prepare(args.experiment_dir, seed=args.seed)
        success = True
    elif args.command == "record-teacher":
        with SharedBehaviorMemory(args.db) as memory:
            result = verify_teacher_and_record(memory, args.experiment_dir, args.response)
        success = result["passed"]
    elif args.command == "start-round":
        result = start_round(
            args.experiment_dir,
            args.round,
            spawn_order=args.spawn_order,
        )
        success = True
    elif args.command == "finalize":
        result = finalize(
            args.experiment_dir,
            args.round,
            args.arm,
            args.response,
            recall_path=args.recall,
        )
        success = True
    else:
        with SharedBehaviorMemory(args.db) as memory:
            result = evaluate(memory, args.experiment_dir)
        _write_json(args.output, result)
        success = result["passed"]
    print(_canonical_json(result))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
