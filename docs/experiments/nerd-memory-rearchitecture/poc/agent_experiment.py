from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Mapping, Sequence

from .shared_memory import SharedBehaviorMemory


EXPERIMENT_SCHEMA = "shared-agent-experiment/v1"
WORKERS = (
    ("worker-alpha", "consumer-typescript-web"),
    ("worker-beta", "consumer-python-cli"),
    ("worker-gamma", "consumer-documentation"),
)
UNKNOWN_COMMANDS = (
    "perform the cobalt zephyr migration",
    "inspect the silent topaz constellation",
    "prepare the winter quartz relay",
)
WRAPPERS = (
    "Please handle {cue} for this task.",
    "The requested operation is {cue}; complete it now.",
    "Can you perform {cue} and report the result?",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def make_cards(
    memory: SharedBehaviorMemory,
    experiment_dir: Path,
    *,
    seed: int = 505,
) -> dict[str, Any]:
    behaviors = memory.behaviors()
    if len(behaviors) < 6:
        raise ValueError("at least six teacher behaviors are required")
    randomizer = random.Random(seed)
    public_by_worker: dict[str, list[dict[str, Any]]] = {}
    gold: dict[str, dict[str, Any]] = {}

    for worker_index, (worker_id, repository) in enumerate(WORKERS):
        cards: list[dict[str, Any]] = []
        for behavior_index, behavior in enumerate(behaviors):
            cue_index = (worker_index + behavior_index) % len(behavior["cue_phrases"])
            cue = behavior["cue_phrases"][cue_index]
            wrapper = WRAPPERS[(worker_index * 2 + behavior_index) % len(WRAPPERS)]
            trial_id = f"{worker_id}-known-{behavior_index + 1:02d}"
            memory_enabled = (worker_index + behavior_index) % 2 == 0
            invalid = bool(behavior["invalid_signals"]) and (
                worker_index + behavior_index
            ) % 3 == 0
            output_signal = (
                behavior["invalid_signals"][0] if invalid else "verified_output"
            )
            cards.append(
                {
                    "trial_id": trial_id,
                    "command": wrapper.format(cue=cue),
                    "memory_enabled": memory_enabled,
                    "consumer_repository": repository,
                    "output_signal": output_signal,
                }
            )
            gold[trial_id] = {
                "kind": "known",
                "worker_id": worker_id,
                "consumer_repository": repository,
                "memory_enabled": memory_enabled,
                "behavior_id": behavior["behavior_id"],
                "action": behavior["action"],
                "tools": behavior["tools"],
                "steps": behavior["steps"],
                "skills": behavior["skills"],
                "reject_output": invalid,
                "source_repository": behavior["source_repository"],
            }

        unknown_trial_id = f"{worker_id}-unknown-01"
        cards.append(
            {
                "trial_id": unknown_trial_id,
                "command": UNKNOWN_COMMANDS[worker_index],
                "memory_enabled": True,
                "consumer_repository": repository,
                "output_signal": "verified_output",
            }
        )
        gold[unknown_trial_id] = {
            "kind": "unknown",
            "worker_id": worker_id,
            "consumer_repository": repository,
            "memory_enabled": True,
        }
        randomizer.shuffle(cards)
        public_by_worker[worker_id] = cards
        _write_json(
            experiment_dir / "cards" / f"{worker_id}.json",
            {
                "schema_version": EXPERIMENT_SCHEMA,
                "worker_id": worker_id,
                "consumer_repository": repository,
                "instructions": {
                    "memory_on": "Query the shared-memory recall CLI, then follow its advisory prediction.",
                    "memory_off": "Do not query or inspect memory; solve from the task card alone and abstain when evidence is absent.",
                },
                "trials": cards,
            },
        )

    conditions: dict[str, set[bool]] = {}
    for expected in gold.values():
        if expected["kind"] == "known":
            conditions.setdefault(expected["behavior_id"], set()).add(
                expected["memory_enabled"]
            )
    if any(values != {False, True} for values in conditions.values()):
        raise AssertionError("every behavior must appear in both experiment conditions")

    gold_document = {
        "schema_version": EXPERIMENT_SCHEMA,
        "seed": seed,
        "teacher_behavior_count": len(behaviors),
        "trials": gold,
    }
    _write_json(experiment_dir / "gold.json", gold_document)
    manifest = {
        "schema_version": EXPERIMENT_SCHEMA,
        "seed": seed,
        "worker_count": len(WORKERS),
        "teacher_behavior_count": len(behaviors),
        "public_card_digest": _digest(public_by_worker),
        "gold_digest": _digest(gold_document),
        "known_trial_count": sum(item["kind"] == "known" for item in gold.values()),
        "unknown_trial_count": sum(item["kind"] == "unknown" for item in gold.values()),
    }
    _write_json(experiment_dir / "manifest.json", manifest)
    return manifest


def _exact_prediction(result: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    return (
        result.get("action") == expected["action"]
        and set(result.get("tools", [])) == set(expected["tools"])
        and result.get("steps", []) == expected["steps"]
        and set(result.get("skills", [])) == set(expected["skills"])
        and result.get("reject_output") is expected["reject_output"]
    )


def evaluate(
    memory: SharedBehaviorMemory,
    experiment_dir: Path,
) -> dict[str, Any]:
    gold_document = _read_json(experiment_dir / "gold.json")
    gold = gold_document["trials"]
    submissions: dict[str, dict[str, Any]] = {}
    for worker_id, _ in WORKERS:
        submission = _read_json(experiment_dir / "submissions" / f"{worker_id}.json")
        if submission.get("worker_id") != worker_id:
            raise ValueError(f"submission identity mismatch for {worker_id}")
        submissions[worker_id] = {
            item["trial_id"]: item for item in submission["trials"]
        }

    on_known = 0
    off_known = 0
    on_success = 0
    off_success = 0
    availability_correct = 0
    cross_repository_correct = 0
    memory_on_invalid = 0
    memory_on_invalid_rejected = 0
    memory_on_valid = 0
    memory_on_valid_rejected = 0
    unknown_count = 0
    unknown_abstained = 0
    workers_with_cross_repository_recall: set[str] = set()
    trial_verdicts: dict[str, dict[str, Any]] = {}

    for trial_id, expected in sorted(gold.items()):
        worker_result = submissions[expected["worker_id"]].get(trial_id)
        if worker_result is None:
            raise ValueError(f"missing submission for {trial_id}")
        if expected["kind"] == "unknown":
            unknown_count += 1
            abstained = worker_result.get("status") == "abstained"
            unknown_abstained += int(abstained)
            trial_verdicts[trial_id] = {"unknown_abstained": abstained}
            continue

        success = _exact_prediction(worker_result, expected)
        if expected["memory_enabled"]:
            on_known += 1
            on_success += int(success)
            if expected["reject_output"]:
                memory_on_invalid += 1
                memory_on_invalid_rejected += int(
                    worker_result.get("reject_output") is True
                )
            else:
                memory_on_valid += 1
                memory_on_valid_rejected += int(
                    worker_result.get("reject_output") is True
                )
            availability = (
                worker_result.get("status") == "recalled"
                and worker_result.get("behavior_id") == expected["behavior_id"]
            )
            availability_correct += int(availability)
            cross_repository = (
                availability
                and worker_result.get("source_repository")
                == expected["source_repository"]
                and expected["source_repository"] != expected["consumer_repository"]
            )
            cross_repository_correct += int(cross_repository)
            if cross_repository:
                workers_with_cross_repository_recall.add(expected["worker_id"])
            trial_verdicts[trial_id] = {
                "condition": "memory_on",
                "exact_task_success": success,
                "availability_correct": availability,
                "cross_repository": cross_repository,
            }
        else:
            off_known += 1
            off_success += int(success)
            trial_verdicts[trial_id] = {
                "condition": "memory_off",
                "exact_task_success": success,
            }

    events = memory.recall_events()
    event_by_trial: dict[str, int] = {}
    for event in events:
        event_by_trial[event["trial_id"]] = event_by_trial.get(event["trial_id"], 0) + 1
    expected_memory_trials = {
        trial_id for trial_id, item in gold.items() if item["memory_enabled"]
    }
    expected_off_trials = set(gold) - expected_memory_trials
    memory_trials_queried_once = all(event_by_trial.get(trial_id) == 1 for trial_id in expected_memory_trials)
    off_trials_not_queried = all(event_by_trial.get(trial_id, 0) == 0 for trial_id in expected_off_trials)

    schema = memory.schema_manifest()
    storage_identifiers = set(schema)
    storage_identifiers.update(column for columns in schema.values() for column in columns)
    no_partition_field = "namespace" not in storage_identifiers
    metrics = {
        "memory_on_exact_success": on_success / on_known if on_known else 0.0,
        "memory_off_exact_success": off_success / off_known if off_known else 0.0,
        "success_gain": (on_success / on_known if on_known else 0.0)
        - (off_success / off_known if off_known else 0.0),
        "shared_availability": availability_correct / on_known if on_known else 0.0,
        "cross_repository_recall": cross_repository_correct / on_known if on_known else 0.0,
        "unknown_abstention": unknown_abstained / unknown_count if unknown_count else 0.0,
        "invalid_output_recall_memory_on": (
            memory_on_invalid_rejected / memory_on_invalid if memory_on_invalid else 0.0
        ),
        "valid_output_false_rejection_memory_on": (
            memory_on_valid_rejected / memory_on_valid if memory_on_valid else 0.0
        ),
    }
    criteria = {
        "E1_teacher_behaviors": memory.behavior_count() >= 6,
        "E2_three_independent_consumers": len(submissions) == 3,
        "E3_shared_availability": metrics["shared_availability"] >= 0.90,
        "E4_cross_repository_recall": (
            metrics["cross_repository_recall"] >= 0.90
            and len(workers_with_cross_repository_recall) == 3
        ),
        "E5_usefulness_gain": metrics["success_gain"] >= 0.50,
        "E6_unknown_abstention": metrics["unknown_abstention"] >= 0.90,
        "E7_condition_isolation": memory_trials_queried_once and off_trials_not_queried,
        "E8_no_storage_partition_field": no_partition_field,
    }
    result = {
        "schema_version": EXPERIMENT_SCHEMA,
        "metrics": metrics,
        "counts": {
            "memory_on_known": on_known,
            "memory_off_known": off_known,
            "unknown": unknown_count,
            "memory_on_invalid": memory_on_invalid,
            "memory_on_valid": memory_on_valid,
            "recall_events": len(events),
            "workers_with_cross_repository_recall": len(workers_with_cross_repository_recall),
        },
        "condition_audit": {
            "memory_trials_queried_once": memory_trials_queried_once,
            "memory_off_trials_not_queried": off_trials_not_queried,
        },
        "criteria": {key: "PASS" if passed else "FAIL" for key, passed in criteria.items()},
        "trial_verdicts": trial_verdicts,
        "passed": all(criteria.values()),
    }
    result["canonical_digest"] = _digest(result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-agent shared-memory experiment")
    parser.add_argument("--db", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    make = subparsers.add_parser("make-cards")
    make.add_argument("--experiment-dir", type=Path, required=True)
    make.add_argument("--seed", type=int, default=505)
    score = subparsers.add_parser("evaluate")
    score.add_argument("--experiment-dir", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    with SharedBehaviorMemory(args.db) as memory:
        if args.command == "make-cards":
            result = make_cards(memory, args.experiment_dir, seed=args.seed)
        else:
            result = evaluate(memory, args.experiment_dir)
            _write_json(args.output, result)
    print(_canonical_json(result))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
