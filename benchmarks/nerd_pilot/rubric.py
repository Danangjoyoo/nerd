"""Deterministic 6-point rubric for Nerd pilot cases."""

from __future__ import annotations

import re
from typing import Any


CASES = {
    "case1": {
        "unknown_context_id": "ctx_223twgnc7h5wvublifm2hexampledoesntmatteri",
        "smallest_unknown_phrases": (
            "bounded lexical",
            "identifier-token candidate",
            "token savings",
            "typed-ledger-pass",
            "generated capture",
            "40% token",
            "40%",
            "query/rubric",
            "economics",
            "break-even",
        ),
    },
    "case2": {
        "unknown_context_id": "ctx_lexicalfakecandidatesnapshotforbenchmarkingi",
        "smallest_unknown_phrases": (
            "held-out",
            "held out",
            "generated capture",
            "generated-capture",
            "live",
            "same fixtures",
            "same 48",
            "fresh preregistration",
            "not a production",
            "not production",
            "does not unlock",
            "typed-ledger-pass",
            "token savings",
            "quality delta",
        ),
    },
    "case3": {
        "unknown_context_id": "ctx_securityreviewboundarysessionexamplenobodyi",
        "smallest_unknown_phrases": (
            "adversarial",
            "generated capture",
            "generated-capture",
            "live",
            "live run",
            "authority",
            "untrusted_context",
            "typed-ledger-pass",
            "production gate",
            "production release",
            "held-out",
        ),
    },
}


def _focus_record_present(text: str) -> bool:
    return "Focus Record" in text and all(
        re.search(rf"\*\*{field}:\*\*", text)
        for field in ("Intention", "Expectation", "Scope", "Role")
    )


def _endpoint_named(text: str) -> bool:
    return any(
        re.search(rf"\*\*Expectation:\*\*[^\n]*\b{endpoint}\b", text)
        for endpoint in (
            "Discuss", "Ideate", "Explore", "Diagnose", "Review",
            "Specify", "Document", "Plan", "Execute", "Monitor",
        )
    )


def _memory_blind_then_memory(text: str) -> bool:
    lowered = text.casefold()
    return "memory-blind" in lowered and "advisory" in lowered


def _unknown_id_not_found(text: str, unknown_id: str) -> bool:
    if unknown_id not in text or "not_found" not in text:
        return False
    if re.search(
        r"(search|guess|substitute|infer)ed?\s+(a|another|the)\s+(context|id)",
        text.casefold(),
    ):
        return False
    return True


def _fresh_receipt(text: str) -> bool:
    return re.search(r"Nerd-context created:\s*ctx_[a-z2-7]{38}[aiqy]", text) is not None


def _smallest_unknown_named(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(phrase.casefold() in lowered for phrase in phrases)


def score(text: str, case_id: str) -> dict[str, Any]:
    if case_id not in CASES:
        raise ValueError(f"unknown case_id: {case_id}")
    cfg = CASES[case_id]
    criteria = (
        ("focus_record_present", "Focus Record present with all four labelled fields.",
         _focus_record_present(text)),
        ("endpoint_named", "Endpoint chosen and named from the endpoint mapping.",
         _endpoint_named(text)),
        ("memory_blind_then_memory", "Memory-blind step demonstrated before Memory advisory line.",
         _memory_blind_then_memory(text)),
        ("unknown_id_not_found_no_substitute",
         "Unknown ID is treated as not_found without search or substitution.",
         _unknown_id_not_found(text, cfg["unknown_context_id"])),
        ("fresh_context_receipt",
         "Fresh Context creation described with Nerd-context created receipt.",
         _fresh_receipt(text)),
        ("smallest_choice_changing_unknown_named",
         "Names one specific smallest-choice-changing unknown appropriate to the case.",
         _smallest_unknown_named(text, cfg["smallest_unknown_phrases"])),
    )
    hits = [
        {"criterion": key, "description": description, "passed": bool(passed)}
        for key, description, passed in criteria
    ]
    total = sum(1 for hit in hits if hit["passed"])
    return {
        "case_id": case_id,
        "score": total,
        "maximum": len(criteria),
        "accuracy_percent": round(100.0 * total / len(criteria), 2),
        "criteria": hits,
    }
