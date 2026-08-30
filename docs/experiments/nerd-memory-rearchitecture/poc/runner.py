from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from .dataset import (
    DEVELOPMENT_SEEDS,
    HOLDOUT_SEEDS,
    generate_development_raw,
    generate_transfer_stream,
    generate_unknown_stream,
    make_raw_episode,
    template_for_context,
)
from .metrics import average_metrics, evaluate_advisor
from .model import (
    Advice,
    BaselineAdvisor,
    BehaviorMemory,
    Episode,
    canonical_digest,
    canonical_json,
    capture_episode,
    chronological_split,
    edges_from_steps,
)


SCHEMA_VERSION = "behavioral-memory-poc/v1"
DATASET_REVISION = "synthetic-chronological-v1"


class OracleAdvisor:
    """Fixture ceiling, never included in non-oracle improvement comparisons."""

    def advise(
        self,
        command_cues: Sequence[str],
        context: Mapping[str, str],
        output_signals: Sequence[str] = (),
        repository: str = "unknown",
    ) -> Advice:
        del output_signals, repository
        action = next(
            (
                candidate
                for candidate in ("diagnose", "document", "implement", "schema", "test")
                if candidate in command_cues
            ),
            None,
        )
        template = template_for_context(context, action)
        if template is None:
            return Advice(None, (), (), (), (), False, True, 0.0, "oracle", ())
        return Advice(
            action=template.action,
            tools=template.tools,
            steps=template.steps,
            step_edges=edges_from_steps(template.steps),
            skills=template.skills,
            reject_output=False,
            abstained=False,
            confidence=1.0,
            origin="oracle",
            source_episode_ids=(),
        )


def _capture_metrics(raw: Sequence[Mapping[str, Any]], secrets: Sequence[str]) -> tuple[dict[str, float], list[Episode]]:
    episodes: list[Episode] = []
    reconstructed = 0
    leakage = 0
    authority_fields = 0
    for item in raw:
        episode = capture_episode(item)
        persisted = canonical_json(episode.to_dict())
        episodes.append(episode)
        reconstructed += int(Episode.from_dict(json.loads(persisted)) == episode)
        leakage += sum(secret in persisted for secret in secrets)
        authority_fields += sum(field in episode.to_dict() for field in ("authority", "permissions", "endpoint"))
    return {
        "episode_count": float(len(episodes)),
        "reconstruction_rate": reconstructed / len(episodes) if episodes else 1.0,
        "persisted_secret_leak_count": float(leakage),
        "persisted_authority_field_count": float(authority_fields),
        "seeded_secret_count": float(len(secrets)),
    }, episodes


def _runtime_metrics(learner: BehaviorMemory) -> dict[str, float]:
    query = {
        "command_cues": ("test", "api"),
        "context": {"language": "python", "surface": "api", "project_kind": "service"},
        "output_signals": (),
        "repository": "unseen-runtime",
    }
    for _ in range(20):
        learner.advise(**query)
    samples_ms = []
    for _ in range(500):
        started = time.perf_counter_ns()
        learner.advise(**query)
        samples_ms.append((time.perf_counter_ns() - started) / 1_000_000)
    ordered = sorted(samples_ms)
    return {
        "sample_count": 500.0,
        "median_prediction_ms": statistics.median(ordered),
        "p95_prediction_ms": ordered[int(len(ordered) * 0.95) - 1],
    }


def _drift_probe(learner: BehaviorMemory, seed: int) -> list[float]:
    context = {"language": "python", "surface": "api", "project_kind": "service"}
    old = learner.advise(("test", "api"), context, repository=f"unseen-{seed}").tools
    shares = []
    for index in range(3):
        correction = capture_episode(
            make_raw_episode(
                episode_id=f"drift-{seed}-{index}",
                sequence=30_000 + index,
                repository=f"drift-{seed}",
                context=context,
                command="test api",
                action="test",
                tools=old,
                steps=("inspect_pytest", "run_pytest", "report"),
                skills=("create-unit-tests", "nerd-execute"),
                corrected_tools=("uv",),
                corrected_steps=("inspect_pytest", "run_uv", "report"),
                corrected_skills=("create-unit-tests", "nerd-execute"),
                feedback="corrected",
                verified=True,
            )
        )
        learner.observe(correction)
        shares.append(learner.obsolete_usage_share("test", context, old, repository=f"unseen-{seed}"))
    return shares


def _combine_evaluations(items: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    return average_metrics(items)


def _hypothesis_verdicts(metrics: Mapping[str, float], improvements: Mapping[str, float]) -> dict[str, str]:
    return {
        "H1": "PASS"
        if metrics["capture_reconstruction_rate"] == 1.0
        and metrics["persisted_secret_leak_count"] == 0.0
        else "FAIL",
        "H2": "PASS" if improvements["selection_macro_set_f1"] >= 0.08 else "FAIL",
        "H3": "PASS"
        if metrics["mandatory_edge_violation_rate"] < 0.05
        and improvements["workflow_edge_f1"] >= 0.10
        else "FAIL",
        "H4": "PASS"
        if metrics["invalid_output_recall"] >= 0.90
        and metrics["false_rejection_rate"] <= 0.02
        and metrics["severe_false_acceptance_count"] == 0.0
        else "FAIL",
        "H5": "PASS"
        if improvements["unseen_repository_action_accuracy"] >= 0.10
        and metrics["cross_context_contamination"] < 0.02
        else "FAIL",
        "H6": "PASS" if metrics["obsolete_usage_share_after_three"] < 0.10 else "FAIL",
        "H7": "UNTESTED",
    }


def run_iteration(
    iteration: int,
    *,
    seeds: Sequence[int] = DEVELOPMENT_SEEDS,
    include_timing: bool = True,
    phase: str = "development",
) -> dict[str, Any]:
    if iteration not in (1, 2, 3):
        raise ValueError("iteration must be 1, 2, or 3")
    per_seed: list[dict[str, Any]] = []
    baseline_by_name: dict[str, list[dict[str, Any]]] = {name: [] for name in ("B0", "B1", "B2", "B3")}
    dataset_material: list[dict[str, Any]] = []
    runtime_learner: BehaviorMemory | None = None

    for seed in seeds:
        raw, secrets = generate_development_raw(seed)
        capture, episodes = _capture_metrics(raw, secrets)
        dataset_material.extend(episode.to_dict() for episode in episodes)
        train, calibration, test = chronological_split(episodes)
        source_index = {episode.episode_id: episode for episode in train}
        learner = BehaviorMemory(profile=iteration).fit(train, calibration)
        runtime_learner = learner
        test_metrics = evaluate_advisor(learner, test, source_index)
        transfer = generate_transfer_stream(seed)
        transfer_metrics = evaluate_advisor(learner, transfer, source_index)
        unknown = generate_unknown_stream(seed)
        unknown_abstention = sum(
            learner.advise(
                episode.command_cues,
                episode.context,
                repository=episode.repository,
            ).abstained
            for episode in unknown
        ) / len(unknown)

        baselines: dict[str, Any] = {
            "B0": BaselineAdvisor("B0").fit(train),
            "B1": BaselineAdvisor("B1").fit(train),
            "B2": BaselineAdvisor("B2").fit(train),
            "B3": OracleAdvisor(),
        }
        for name, baseline in baselines.items():
            measured = evaluate_advisor(baseline, test)
            transfer_measured = evaluate_advisor(baseline, transfer)
            measured["unseen_repository_action_accuracy"] = transfer_measured["action_accuracy"]
            baseline_by_name[name].append(measured)

        drift_series = _drift_probe(learner, seed)
        per_seed.append(
            {
                "seed": seed,
                "capture": capture,
                "test": test_metrics,
                "transfer": transfer_metrics,
                "unknown_abstention_rate": unknown_abstention,
                "drift_obsolete_usage_share": drift_series,
                "split": {
                    "train": len(train),
                    "calibration": len(calibration),
                    "test": len(test),
                    "train_max_sequence": max(item.sequence for item in train),
                    "calibration_min_sequence": min(item.sequence for item in calibration),
                    "calibration_max_sequence": max(item.sequence for item in calibration),
                    "test_min_sequence": min(item.sequence for item in test),
                },
            }
        )

    capture_average = average_metrics([item["capture"] for item in per_seed])
    test_average = _combine_evaluations([item["test"] for item in per_seed])
    transfer_average = _combine_evaluations([item["transfer"] for item in per_seed])
    baseline_metrics = {
        name: _combine_evaluations(items) for name, items in baseline_by_name.items()
    }
    metrics = {
        "capture_reconstruction_rate": capture_average["reconstruction_rate"],
        "persisted_secret_leak_count": sum(item["capture"]["persisted_secret_leak_count"] for item in per_seed),
        "persisted_authority_field_count": sum(item["capture"]["persisted_authority_field_count"] for item in per_seed),
        "action_accuracy": test_average["action_accuracy"],
        "tool_set_f1": test_average["tool_set_f1"],
        "skill_set_f1": test_average["skill_set_f1"],
        "selection_macro_set_f1": test_average["macro_set_f1"],
        "workflow_edge_f1": test_average["workflow_edge_f1"],
        "mandatory_edge_violation_rate": test_average["mandatory_edge_violation_rate"],
        "invalid_output_recall": test_average["invalid_output_recall"],
        "false_rejection_rate": test_average["false_rejection_rate"],
        "severe_false_acceptance_count": sum(item["test"]["severe_false_acceptance_count"] for item in per_seed),
        "cross_context_contamination": transfer_average["cross_context_contamination"],
        "unseen_repository_action_accuracy": transfer_average["action_accuracy"],
        "unknown_abstention_rate": sum(item["unknown_abstention_rate"] for item in per_seed) / len(per_seed),
        "known_abstention_rate": test_average["known_abstention_rate"],
        "obsolete_usage_share_after_one": sum(item["drift_obsolete_usage_share"][0] for item in per_seed) / len(per_seed),
        "obsolete_usage_share_after_two": sum(item["drift_obsolete_usage_share"][1] for item in per_seed) / len(per_seed),
        "obsolete_usage_share_after_three": sum(item["drift_obsolete_usage_share"][2] for item in per_seed) / len(per_seed),
    }
    best_selection_baseline = max(
        baseline_metrics[name]["macro_set_f1"] for name in ("B0", "B1", "B2")
    )
    best_workflow_baseline = max(
        baseline_metrics[name]["workflow_edge_f1"] for name in ("B0", "B1", "B2")
    )
    improvements = {
        "selection_macro_set_f1": metrics["selection_macro_set_f1"] - best_selection_baseline,
        "workflow_edge_f1": metrics["workflow_edge_f1"] - best_workflow_baseline,
        "unseen_repository_action_accuracy": (
            metrics["unseen_repository_action_accuracy"]
            - baseline_metrics["B2"]["unseen_repository_action_accuracy"]
        ),
    }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "iteration": iteration,
        "model_revision": f"M{iteration}",
        "dataset_revision": DATASET_REVISION,
        "dataset_digest": canonical_digest(dataset_material),
        "seeds": list(seeds),
        "split_policy": {"train": 0.60, "calibration": 0.20, "test": 0.20},
        "per_seed": per_seed,
        "baselines": baseline_metrics,
        "metrics": metrics,
        "improvements": improvements,
        "hypotheses": _hypothesis_verdicts(metrics, improvements),
    }
    if include_timing:
        assert runtime_learner is not None
        result["runtime"] = _runtime_metrics(runtime_learner)
    deterministic_view = {key: value for key, value in result.items() if key != "runtime"}
    result["canonical_digest"] = canonical_digest(deterministic_view)
    return result


def write_result(result: Mapping[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the behavioral-memory POC")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--iteration", type=int, choices=(1, 2, 3))
    group.add_argument("--final", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.final:
        result = run_iteration(3, seeds=HOLDOUT_SEEDS, phase="holdout")
    else:
        result = run_iteration(args.iteration, seeds=DEVELOPMENT_SEEDS)
    write_result(result, args.output)
    print(json.dumps({
        "output": str(args.output),
        "digest": result["canonical_digest"],
        "hypotheses": result["hypotheses"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
