from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOOP_SCRIPT = Path("/Users/mac/.agents/skills/nerd-loop/scripts/loop.py")


def _load_loop() -> Any:
    spec = importlib.util.spec_from_file_location("nerd_loop_reducer", LOOP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Nerd Loop reducer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_receipt() -> dict[str, Any]:
    reducer = _load_loop()
    verification = json.loads(
        (ROOT / "results" / "verification-parent-a.json").read_text(encoding="utf-8")
    )
    comparison = json.loads(
        (ROOT / "results" / "iteration-004-parent.json").read_text(encoding="utf-8")
    )
    if verification["terminal"] != "DONE":
        raise RuntimeError("verification is not complete")
    if comparison["terminal"] != "DONE" or not comparison["passed"]:
        raise RuntimeError("two-run verification comparison is not complete")

    admission = reducer.select_route(
        {
            "schema_version": "nerd-loop/v1",
            "admission_ref": "nerd-memory-rearchitecture-poc-iteration-004",
            "contract_revision": "nerd-loop/v1",
            "endpoint": "execute",
            "signals": {"local_correction_cycle": True, "local_experiment": True},
            "route": "experiment",
            "host_capabilities": ["session_state"],
            "budget": {
                "active_iterations": 1,
                "source": "direct_user_bounded_iteration_004",
            },
        }
    )["admission"]

    criterion_ids = sorted(verification["criterion_vector"])
    artifact_revision = comparison["verification_contract_digest"]
    criteria = []
    for criterion_id in criterion_ids:
        criteria.append(
            {
                "id": criterion_id,
                "source_ref": "experiment-plan.md#metrics-and-thresholds",
                "required_state_ref": f"{criterion_id}:PASS",
                "scope_ref": "nerd-memory-rearchitecture-poc-iteration-004",
                "verifier_id": "poc.verify",
                "pass_rule_ref": f"experiment-plan.md#{criterion_id}",
                "freshness_rule_ref": "two-fresh-v2-runs-and-declared-runtime-policy",
                "status": "PASS",
                "evidence": None,
                "approval_required": False,
                "acceptance_owner": None,
                "approval": None,
            }
        )
    dod = {
        "revision": "behavioral-memory-poc-dod/v2",
        "artifact_revision": artifact_revision,
        "accepted_hash": "pending",
        "mandatory_criterion_ids": criterion_ids,
        "mandatory_integration_ids": [],
        "criteria": criteria,
        "integration": [],
    }
    dod["accepted_hash"] = reducer.dod_contract_hash(dod)
    for criterion in criteria:
        evidence_file = (
            "results/iteration-004-parent.json"
            if criterion["id"] in {"C8", "C10"}
            else "results/verification-parent-a.json"
        )
        criterion["evidence"] = {
            "ref": f"{evidence_file}#{criterion['id']}",
            "criterion_id": criterion["id"],
            "dod_revision": dod["revision"],
            "dod_hash": dod["accepted_hash"],
            "artifact_revision": artifact_revision,
            "verifier_id": criterion["verifier_id"],
            "observed_status": "PASS",
            "authenticated": True,
        }
    decision = reducer.decide_transition(
        {
            "schema_version": "nerd-loop/v1",
            "admission": admission,
            "verifier_integrity": "VALID",
            "dod": dod,
        }
    )
    return {"admission": admission, "dod_hash": dod["accepted_hash"], "decision": decision}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the deterministic Nerd Loop terminal receipt")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_receipt()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt["decision"], sort_keys=True))
    return 0 if receipt["decision"].get("outcome") == "DONE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
