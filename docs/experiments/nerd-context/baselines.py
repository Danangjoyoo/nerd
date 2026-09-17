"""Full-history and equal-budget summary arms for the Context POC."""

from __future__ import annotations

from fixtures import required_records
from structured import serialize_pack


def build_summary_segment(summary: str, *, source_ref: str) -> str:
    return serialize_pack(
        [
            {
                "kind": "summary",
                "value": summary,
                "source": "generated_summary",
                "source_ref": source_ref,
            }
        ]
    )


def build_equal_budget_summary(case: dict, *, max_bytes: int) -> str:
    prose = " ".join(
        f"{event['value']} [{event['source_ref']}]"
        for event in required_records(case)
    )
    summary = build_summary_segment(prose, source_ref=f"{case['id']}-gold-summary")
    if len(summary.encode("utf-8")) > max_bytes:
        raise ValueError("summary exceeds equal pack budget")
    return summary
