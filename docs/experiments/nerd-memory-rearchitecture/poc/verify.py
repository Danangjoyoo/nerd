from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .dataset import (
    DEVELOPMENT_SEEDS,
    HOLDOUT_SEEDS,
    generate_development_stream,
    generate_transfer_stream,
    make_raw_episode,
)
from .model import (
    BehaviorMemory,
    Episode,
    canonical_digest,
    canonical_json,
    capture_episode,
    chronological_split,
    resolve_current,
)
from .runner import _drift_probe, _runtime_metrics, run_iteration


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_POLICY = {
    "schema_version": "runtime-evidence-policy/v1",
    "sample_count": 500,
    "bounds": {
        "median_prediction_ms": {"operator": "<", "limit_ms": 5.0},
        "p95_prediction_ms": {"operator": "<", "limit_ms": 10.0},
    },
    "repeat_tolerance": {
        "absolute_ms": 0.05,
        "relative_fraction": 0.25,
        "rule": "delta <= max(absolute_ms, relative_fraction * slower_measurement)",
    },
}


def _runtime_evidence(measurements: dict[str, float]) -> dict[str, Any]:
    within_bounds = (
        measurements["sample_count"] == RUNTIME_POLICY["sample_count"]
        and measurements["median_prediction_ms"]
        < RUNTIME_POLICY["bounds"]["median_prediction_ms"]["limit_ms"]
        and measurements["p95_prediction_ms"]
        < RUNTIME_POLICY["bounds"]["p95_prediction_ms"]["limit_ms"]
    )
    return {
        "measurements": measurements,
        "policy": RUNTIME_POLICY,
        "within_bounds": within_bounds,
    }


def deterministic_projection(result: dict[str, Any]) -> dict[str, Any]:
    """Return only evidence whose contract requires exact cross-run equality."""

    unit_tests = result["unit_tests"]
    return {
        "schema_version": "behavioral-memory-deterministic-evidence/v1",
        "artifact_digest": result["artifact_digest"],
        "criterion_vector": {
            key: value
            for key, value in sorted(result["criterion_vector"].items())
            if key != "C10"
        },
        "unit_tests": {
            "exit_code": unit_tests["exit_code"],
            "passed": unit_tests["passed"],
            "summary": unit_tests["summary"],
        },
        "determinism": result["determinism"],
        "safety_probes": result["safety_probes"],
        "cross_agent_evidence": result.get("cross_agent_evidence"),
        "paired_agent_evidence": result.get("paired_agent_evidence"),
        "manifest": result["manifest"],
    }


def _statistic_comparison(
    first: float, second: float, limit_ms: float
) -> dict[str, Any]:
    absolute_delta = abs(first - second)
    tolerance = max(
        RUNTIME_POLICY["repeat_tolerance"]["absolute_ms"],
        RUNTIME_POLICY["repeat_tolerance"]["relative_fraction"]
        * max(abs(first), abs(second)),
    )
    return {
        "first_ms": first,
        "second_ms": second,
        "absolute_delta_ms": absolute_delta,
        "allowed_delta_ms": tolerance,
        "within_tolerance": absolute_delta <= tolerance,
        "first_within_bound": first < limit_ms,
        "second_within_bound": second < limit_ms,
    }


def compare_verifications(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_projection = deterministic_projection(first)
    second_projection = deterministic_projection(second)
    first_computed_digest = canonical_digest(first_projection)
    second_computed_digest = canonical_digest(second_projection)
    stored_digests_valid = (
        first.get("deterministic_evidence_digest") == first_computed_digest
        and second.get("deterministic_evidence_digest") == second_computed_digest
    )
    deterministic_exact = stored_digests_valid and first_projection == second_projection
    policies_equal = (
        first["runtime"]["policy"] == second["runtime"]["policy"] == RUNTIME_POLICY
    )
    first_runtime = first["runtime"]["measurements"]
    second_runtime = second["runtime"]["measurements"]
    statistic_results = {
        name: _statistic_comparison(
            first_runtime[name],
            second_runtime[name],
            RUNTIME_POLICY["bounds"][name]["limit_ms"],
        )
        for name in ("median_prediction_ms", "p95_prediction_ms")
    }
    sample_counts_exact = (
        first_runtime["sample_count"]
        == second_runtime["sample_count"]
        == RUNTIME_POLICY["sample_count"]
    )
    both_within_bounds = (
        sample_counts_exact
        and all(
            item["first_within_bound"] and item["second_within_bound"]
            for item in statistic_results.values()
        )
        and first["runtime"]["within_bounds"]
        and second["runtime"]["within_bounds"]
        and first["criterion_vector"].get("C10") == "PASS"
        and second["criterion_vector"].get("C10") == "PASS"
    )
    within_repeat_tolerance = all(
        item["within_tolerance"] for item in statistic_results.values()
    )
    runtime_policy_passed = (
        policies_equal and both_within_bounds and within_repeat_tolerance
    )
    passed = (
        deterministic_exact
        and runtime_policy_passed
        and first.get("terminal") == second.get("terminal") == "DONE"
    )
    contract_projection = {
        "schema_version": "behavioral-memory-verification-comparison/v1",
        "deterministic_evidence_digest": first_computed_digest
        if deterministic_exact
        else None,
        "runtime_policy": RUNTIME_POLICY,
        "deterministic_evidence_exact": deterministic_exact,
        "runtime_policy_passed": runtime_policy_passed,
        "both_terminals_done": first.get("terminal") == second.get("terminal") == "DONE",
        "passed": passed,
    }
    contract_digest = canonical_digest(contract_projection)
    return {
        "schema_version": "behavioral-memory-verification-comparison/v1",
        "iteration": 4,
        "causal_variable": "reproducibility_semantics_for_noisy_timing",
        "deterministic_evidence_exact": deterministic_exact,
        "deterministic_evidence_digest": first_computed_digest
        if deterministic_exact
        else None,
        "stored_digests_valid": stored_digests_valid,
        "raw_outputs_equal": first == second,
        "runtime_evidence": {
            "policy": RUNTIME_POLICY,
            "policies_equal": policies_equal,
            "sample_counts_exact": sample_counts_exact,
            "both_runs_within_bounds": both_within_bounds,
            "within_repeat_tolerance": within_repeat_tolerance,
            "within_declared_policy": runtime_policy_passed,
            "statistics": statistic_results,
        },
        "criterion_vector": {
            "C8": "PASS" if deterministic_exact else "FAIL",
            "C10": "PASS" if runtime_policy_passed else "FAIL",
        },
        "hypotheses": {"H7": "UNTESTED", "H8": "PASS", "H9": "PASS"},
        "verification_contract_digest": contract_digest,
        "passed": passed,
        "terminal": "DONE" if passed else "FAILED",
    }


def _unit_tests() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": f"{sys.executable} -m unittest discover -s tests -v",
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "summary": completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "",
    }


def _determinism() -> dict[str, Any]:
    comparisons = []
    for iteration in (1, 2, 3):
        first = run_iteration(iteration, seeds=DEVELOPMENT_SEEDS, include_timing=False)
        second = run_iteration(iteration, seeds=DEVELOPMENT_SEEDS, include_timing=False)
        recorded = json.loads(
            (ROOT / "results" / f"iteration-{iteration:03d}.json").read_text(encoding="utf-8")
        )
        comparisons.append(
            {
                "phase": "development",
                "iteration": iteration,
                "recorded_digest": recorded["canonical_digest"],
                "first_digest": first["canonical_digest"],
                "second_digest": second["canonical_digest"],
                "equal": recorded["canonical_digest"]
                == first["canonical_digest"]
                == second["canonical_digest"],
            }
        )
    first_holdout = run_iteration(3, seeds=HOLDOUT_SEEDS, include_timing=False, phase="holdout")
    second_holdout = run_iteration(3, seeds=HOLDOUT_SEEDS, include_timing=False, phase="holdout")
    recorded_holdout = json.loads(
        (ROOT / "results" / "final-holdout.json").read_text(encoding="utf-8")
    )
    comparisons.append(
        {
            "phase": "holdout-post-freeze-rerun",
            "iteration": 3,
            "recorded_digest": recorded_holdout["canonical_digest"],
            "first_digest": first_holdout["canonical_digest"],
            "second_digest": second_holdout["canonical_digest"],
            "equal": recorded_holdout["canonical_digest"]
            == first_holdout["canonical_digest"]
            == second_holdout["canonical_digest"],
        }
    )
    return {"passed": all(item["equal"] for item in comparisons), "comparisons": comparisons}


def _safety_probes() -> dict[str, bool]:
    raw = make_raw_episode(
        episode_id="verify-secret",
        sequence=1,
        raw_command=(
            "test api token=sk-live-abcdefghijklmnopqrstuvwxyz123456 "
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345"
        ),
        authority="deploy production",
    )
    episode = capture_episode(raw)
    persisted = canonical_json(episode.to_dict())
    reconstruction = Episode.from_dict(json.loads(persisted)) == episode
    redacted = (
        "sk-live-abcdefghijklmnopqrstuvwxyz123456" not in persisted
        and "abcdefghijklmnopqrstuvwxyz012345" not in persisted
    )
    authority_absent = all(
        field not in episode.to_dict()
        for field in ("authority", "permissions", "endpoint", "current_instructions")
    )

    stream = generate_development_stream(11)
    train, calibration, _ = chronological_split(stream)
    learner = BehaviorMemory(profile=3).fit(train, calibration)
    context = {"language": "python", "surface": "api", "project_kind": "service"}
    advice = learner.advise(("test", "api"), context, ("secret_leak",))
    invalid_rejected = advice.reject_output
    override = resolve_current(advice, {"tools": ["current-user-tool"]})
    current_override = override["tools"] == ["current-user-tool"]

    source_index = {item.episode_id: item for item in train}
    context_clean = True
    for transfer in generate_transfer_stream(11):
        recommendation = learner.advise(
            transfer.command_cues,
            transfer.context,
            repository=transfer.repository,
        )
        for source_id in recommendation.source_episode_ids:
            context_clean = context_clean and source_index[source_id].context == transfer.context

    drift = _drift_probe(learner, 11)
    drift_retired = drift[-1] < 0.10
    unknown = learner.advise(
        ("quantum", "teleport"),
        {"language": "rust", "surface": "satellite", "project_kind": "unknown"},
    )
    return {
        "capture_reconstructs": reconstruction,
        "seeded_secrets_redacted": redacted,
        "authority_fields_absent": authority_absent,
        "current_values_override": current_override,
        "high_severity_invalid_rejected": invalid_rejected,
        "context_provenance_clean": context_clean,
        "three_corrections_retire": drift_retired,
        "unknown_query_abstains": unknown.abstained,
    }


def verify() -> dict[str, Any]:
    final_path = ROOT / "results" / "final-holdout.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    cross_agent = json.loads(
        (ROOT / "results" / "iteration-005.json").read_text(encoding="utf-8")
    )
    paired_agent = json.loads(
        (ROOT / "results" / "iteration-006.json").read_text(encoding="utf-8")
    )
    metrics = final["metrics"]
    improvements = final["improvements"]
    unit_tests = _unit_tests()
    determinism = _determinism()
    safety = _safety_probes()

    runtime_stream = generate_development_stream(107)
    train, calibration, _ = chronological_split(runtime_stream)
    runtime = _runtime_evidence(
        _runtime_metrics(BehaviorMemory(profile=3).fit(train, calibration))
    )

    manifest_paths = [
        "README.md",
        "architecture.md",
        "hypotheses.md",
        "experiment-plan.md",
        "reports/iteration-001.md",
        "reports/iteration-002.md",
        "reports/iteration-003.md",
        "reports/iteration-004.md",
        "reports/iteration-005.md",
        "reports/iteration-006.md",
        "results/iteration-001.json",
        "results/iteration-002.json",
        "results/iteration-003.json",
        "results/iteration-004.json",
        "results/iteration-005.json",
        "results/iteration-005/shared-memory.sqlite",
        "results/iteration-005/teacher-export.json",
        "results/iteration-005/manifest.json",
        "results/iteration-005/gold.json",
        "results/iteration-005/cards/worker-alpha.json",
        "results/iteration-005/cards/worker-beta.json",
        "results/iteration-005/cards/worker-gamma.json",
        "results/iteration-005/submissions/worker-alpha.json",
        "results/iteration-005/submissions/worker-beta.json",
        "results/iteration-005/submissions/worker-gamma.json",
        "results/iteration-006.json",
        "results/iteration-006/shared-memory.sqlite",
        "results/iteration-006/teacher-export.json",
        "results/iteration-006/manifest.json",
        "results/iteration-006/private/procedure.json",
        "results/iteration-006/private/gold/teacher.json",
        "results/iteration-006/protocols/memory.txt",
        "results/iteration-006/protocols/control.txt",
        "results/iteration-006/teacher/card.json",
        "results/iteration-006/teacher/input.json",
        "results/iteration-006/teacher/response.json",
        "results/final-holdout.json",
        "results/loop-terminal.json",
        "results/verification-run-b.json",
        "final-report.md",
    ]
    for round_number in range(1, 6):
        round_id = f"round-{round_number:02d}"
        manifest_paths.extend(
            [
                f"results/iteration-006/rounds/{round_id}/card.json",
                f"results/iteration-006/rounds/{round_id}/input.json",
                f"results/iteration-006/private/gold/{round_id}.json",
                f"results/iteration-006/responses/{round_id}-memory.json",
                f"results/iteration-006/responses/{round_id}-control.json",
                f"results/iteration-006/recalls/{round_id}-memory.json",
                f"results/iteration-006/submissions/{round_id}-memory.json",
                f"results/iteration-006/submissions/{round_id}-control.json",
            ]
        )
    manifest = {path: (ROOT / path).is_file() for path in manifest_paths}
    final_report_text = (ROOT / "final-report.md").read_text(encoding="utf-8")

    criteria = {
        "C1": metrics["capture_reconstruction_rate"] == 1.0
        and metrics["persisted_secret_leak_count"] == 0.0,
        "C2": improvements["selection_macro_set_f1"] >= 0.08,
        "C3": metrics["mandatory_edge_violation_rate"] < 0.05
        and improvements["workflow_edge_f1"] >= 0.10,
        "C4": metrics["invalid_output_recall"] >= 0.90
        and metrics["false_rejection_rate"] <= 0.02
        and metrics["severe_false_acceptance_count"] == 0,
        "C5": improvements["unseen_repository_action_accuracy"] >= 0.10
        and metrics["cross_context_contamination"] < 0.02,
        "C6": metrics["obsolete_usage_share_after_three"] < 0.10,
        "C7": metrics["unknown_abstention_rate"] >= 0.90
        and metrics["known_abstention_rate"] <= 0.05,
        "C8": determinism["passed"],
        "C9": unit_tests["passed"] and all(safety.values()),
        "C10": runtime["within_bounds"],
        "C11": all(manifest.values()),
        "C12": "H7" in final_report_text
        and "UNTESTED" in final_report_text
        and final["hypotheses"]["H7"] == "UNTESTED",
        "C13": cross_agent.get("passed") is True
        and all(status == "PASS" for status in cross_agent.get("criteria", {}).values())
        and cross_agent.get("canonical_digest")
        == canonical_digest(
            {
                key: value
                for key, value in cross_agent.items()
                if key != "canonical_digest"
            }
        )
        and "H8" in final_report_text,
        "C14": paired_agent.get("passed") is True
        and all(status == "PASS" for status in paired_agent.get("criteria", {}).values())
        and paired_agent.get("canonical_digest")
        == canonical_digest(
            {
                key: value
                for key, value in paired_agent.items()
                if key != "canonical_digest"
            }
        )
        and "H9" in final_report_text,
    }
    criterion_vector = {
        key: "PASS" if passed else "FAIL" for key, passed in sorted(criteria.items())
    }
    result = {
        "schema_version": "behavioral-memory-verification/v4",
        "artifact_digest": canonical_digest(
            {
                "simulator": final["canonical_digest"],
                "cross_agent": cross_agent["canonical_digest"],
                "paired_agent": paired_agent["canonical_digest"],
            }
        ),
        "criterion_vector": criterion_vector,
        "unit_tests": unit_tests,
        "determinism": determinism,
        "safety_probes": safety,
        "cross_agent_evidence": {
            "canonical_digest": cross_agent["canonical_digest"],
            "passed": cross_agent["passed"],
            "criteria": cross_agent["criteria"],
            "metrics": cross_agent["metrics"],
            "counts": cross_agent["counts"],
            "condition_audit": cross_agent["condition_audit"],
        },
        "paired_agent_evidence": {
            "canonical_digest": paired_agent["canonical_digest"],
            "passed": paired_agent["passed"],
            "criteria": paired_agent["criteria"],
            "accuracy": paired_agent["accuracy"],
            "speed_seconds": paired_agent["speed_seconds"],
            "observable_lexical_tokens": paired_agent[
                "observable_lexical_tokens"
            ],
            "condition_audit": paired_agent["condition_audit"],
            "relative_comparison": paired_agent["relative_comparison"],
            "token_measure_limit": paired_agent["token_measure_limit"],
        },
        "runtime": runtime,
        "manifest": manifest,
        "terminal": "DONE" if all(criteria.values()) else "FAILED",
    }
    result["deterministic_evidence_digest"] = canonical_digest(
        deterministic_projection(result)
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the behavioral-memory POC")
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("FIRST", "SECOND"),
        type=Path,
        help="Compare two verification outputs under the declared evidence contract",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.compare:
        first = json.loads(args.compare[0].read_text(encoding="utf-8"))
        second = json.loads(args.compare[1].read_text(encoding="utf-8"))
        result = compare_verifications(first, second)
        success = result["passed"]
        summary = {
            "terminal": result["terminal"],
            "deterministic_evidence_exact": result["deterministic_evidence_exact"],
            "runtime_within_declared_policy": result["runtime_evidence"][
                "within_declared_policy"
            ],
        }
    else:
        result = verify()
        success = result["terminal"] == "DONE"
        summary = {
            "terminal": result["terminal"],
            "criterion_vector": result["criterion_vector"],
            "deterministic_evidence_digest": result[
                "deterministic_evidence_digest"
            ],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
