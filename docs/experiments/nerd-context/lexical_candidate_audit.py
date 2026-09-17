"""Offline evaluation of the bounded lexical (identifier-token) candidate.

Investigation only. Runs once against the frozen 48 gold cases plus a small
set of source-bound generic regressions. Does NOT overwrite the baseline
`budgeted-response-*` archive or the tracked verdict. Never advances Tasks
2–7. Preserves failure honestly if the candidate does not reach 95% required
recall.

Outputs: benchmarks/results/nerd-context/lexical-candidate-<UTC>/
  - summary.json     — baseline vs candidate recall metrics (both modes)
  - rows.json        — per-case, per-mode, per-arm record ids and recalls
  - regressions.json — generic confusable + genuinely-requested-history probes
  - source.json      — sha256 of the exact source files that produced the run
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import budgeted_response
import structured
from budgeted_response import recall_from_ledger
from fixtures import active_records, load_cases, required_records
from structured import StructuredLedger
from structured_candidate import CandidateStructuredLedger, _candidate_terms


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE_FILES = (
    "structured.py",
    "structured_candidate.py",
    "budgeted_response.py",
    "fixtures.py",
    "cases.json",
    "lexical_candidate_audit.py",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_arm(case, ledger_cls, patched: bool):
    """One recall arm for one case and one index mode; returns record ids and recalls."""
    records = active_records(case)
    required = {item["id"] for item in required_records(case)}
    mandatory = {
        item["id"]
        for item in records
        if item["active"] and item["kind"] in {"goal", "boundary", "decision"}
    }
    observed = {}
    for mode in ("normalized_scan", "fts5"):
        with ledger_cls(records, index_mode=mode) as ledger:
            if patched:
                # Route selector + query tokenization through the candidate
                # tokenizer for the duration of this recall.
                original_structured = structured._terms
                original_budgeted = budgeted_response._terms
                try:
                    structured._terms = _candidate_terms  # type: ignore[assignment]
                    budgeted_response._terms = _candidate_terms  # type: ignore[assignment]
                    result = recall_from_ledger(
                        ledger, context_id=case["context_id"], query=case["request"]
                    )
                finally:
                    structured._terms = original_structured
                    budgeted_response._terms = original_budgeted
            else:
                result = recall_from_ledger(
                    ledger, context_id=case["context_id"], query=case["request"]
                )
        chosen = set(result.record_ids)
        observed[mode] = {
            "record_ids": list(result.record_ids),
            "required_recall": len(required & chosen) / len(required),
            "mandatory_recall": len(mandatory & chosen) / len(mandatory),
        }
    return observed


def _summarize(rows, arm: str):
    """Aggregate over selected primary index (normalized_scan) rows."""
    primary = [row for row in rows if row["index_mode"] == "normalized_scan"]
    required = [row[arm]["required_recall"] for row in primary]
    mandatory = [row[arm]["mandatory_recall"] for row in primary]
    complete = sum(1 for value in required if value == 1)
    return {
        "cases": len(primary),
        "required_recall_mean": sum(required) / len(required),
        "required_recall_min": min(required),
        "complete_cases": complete,
        "mandatory_recall_min": min(mandatory),
        "required_recall_gate_pass": all(value >= 0.95 for value in required)
        and (sum(required) / len(required)) >= 0.95,
    }


def _mode_parity(rows, arm: str) -> bool:
    """Both index modes must produce the same record-id set per case for an arm."""
    per_case: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        per_case.setdefault(row["case_id"], {})[row["index_mode"]] = set(
            row[arm]["record_ids"]
        )
    for case_id, modes in per_case.items():
        if modes.get("normalized_scan") != modes.get("fts5"):
            return False
    return True


def _regressions():
    """Small source-bound generic regressions.

    Confusable: request for `service-2` must not pull `service-2-archive-*`
    ahead of the required `service-2` decision. Requested history: a query
    that explicitly names `service-1-archive-3` must return that historical
    evidence record (baseline drops '-' tokens and 1-digit unigrams, so
    `archive` is the strongest matching term — the candidate keeps the whole
    identifier).
    """
    cases = {case["id"]: case for case in load_cases(HERE / "cases.json")}
    probes = []
    # Confusable: for each of the four categories, ensure the baseline case
    # request still finds the required record set — the request already names
    # the subject identifier verbatim.
    confusable_cases = [
        ("resumption-02", "service-2"),
        ("cross_session-05", "package-5"),
        ("supersession-07", "configuration-7"),
        ("distractor-03", "tenant-3"),
    ]
    for case_id, subject in confusable_cases:
        case = cases[case_id]
        records = active_records(case)
        required = {item["id"] for item in required_records(case)}
        arm_results = {}
        for arm_name, cls, patched in (
            ("baseline", StructuredLedger, False),
            ("candidate", CandidateStructuredLedger, True),
        ):
            with cls(records, index_mode="normalized_scan") as ledger:
                if patched:
                    original = (structured._terms, budgeted_response._terms)
                    try:
                        structured._terms = _candidate_terms  # type: ignore
                        budgeted_response._terms = _candidate_terms  # type: ignore
                        result = recall_from_ledger(
                            ledger, context_id=case["context_id"], query=case["request"]
                        )
                    finally:
                        structured._terms, budgeted_response._terms = original
                else:
                    result = recall_from_ledger(
                        ledger, context_id=case["context_id"], query=case["request"]
                    )
            arm_results[arm_name] = {
                "record_ids": list(result.record_ids),
                "required_recall": len(required & set(result.record_ids))
                / len(required),
            }
        probes.append(
            {
                "kind": "confusable_subject",
                "case_id": case_id,
                "subject": subject,
                **arm_results,
            }
        )
    # Requested history: fabricate a query that explicitly names an archive
    # sibling. The historical record's id is `<case>-r09` (first distractor).
    case = cases["resumption-01"]
    records = active_records(case)
    archive_query = (
        "Return the historical note recorded for service-1-archive-3; cite it."
    )
    archive_target = f"{case['id']}-r11"  # 8 events + offsets 1..11 → offset 3 → r11
    arm_results = {}
    for arm_name, cls, patched in (
        ("baseline", StructuredLedger, False),
        ("candidate", CandidateStructuredLedger, True),
    ):
        with cls(records, index_mode="normalized_scan") as ledger:
            if patched:
                original = (structured._terms, budgeted_response._terms)
                try:
                    structured._terms = _candidate_terms  # type: ignore
                    budgeted_response._terms = _candidate_terms  # type: ignore
                    result = recall_from_ledger(
                        ledger, context_id=case["context_id"], query=archive_query
                    )
                finally:
                    structured._terms, budgeted_response._terms = original
            else:
                result = recall_from_ledger(
                    ledger, context_id=case["context_id"], query=archive_query
                )
        arm_results[arm_name] = {
            "record_ids": list(result.record_ids),
            "hits_target": archive_target in result.record_ids,
        }
    probes.append(
        {
            "kind": "requested_history",
            "case_id": case["id"],
            "query": archive_query,
            "target_record": archive_target,
            **arm_results,
        }
    )
    return probes


def run(output: Path) -> dict:
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    rows: list[dict] = []
    for case in load_cases(HERE / "cases.json"):
        if case["category"] == "short_control":
            continue
        baseline = _run_arm(case, StructuredLedger, patched=False)
        candidate = _run_arm(case, CandidateStructuredLedger, patched=True)
        for mode in ("normalized_scan", "fts5"):
            rows.append(
                {
                    "case_id": case["id"],
                    "index_mode": mode,
                    "baseline": baseline[mode],
                    "candidate": candidate[mode],
                }
            )
    summary = {
        "baseline": _summarize(rows, "baseline"),
        "candidate": _summarize(rows, "candidate"),
        "baseline_mode_parity": _mode_parity(rows, "baseline"),
        "candidate_mode_parity": _mode_parity(rows, "candidate"),
    }
    regressions = _regressions()
    source = {name: _sha((HERE / name).read_bytes()) for name in SOURCE_FILES}
    (output / "rows.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (output / "regressions.json").write_text(
        json.dumps(regressions, indent=2), encoding="utf-8"
    )
    (output / "source.json").write_text(
        json.dumps(source, indent=2), encoding="utf-8"
    )
    return {"summary": summary, "output": str(output)}


if __name__ == "__main__":
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    destination = ROOT / "benchmarks/results/nerd-context" / f"lexical-candidate-{stamp}"
    result = run(destination)
    print(json.dumps(result, indent=2))
