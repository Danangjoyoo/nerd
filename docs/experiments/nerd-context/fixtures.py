"""Deterministic chronological corpus materialization for the Context experiment."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re


CATEGORY_COUNTS = {
    "resumption": 12,
    "cross_session": 12,
    "supersession": 12,
    "distractor": 12,
    "short_control": 12,
}
ID_RE = re.compile(r"^ctx_[a-z2-7]{38}[aiqy]$")
REQUIRED_PROMPT_LABELS = ("Intention", "Request", "Scope", "Authority")
DISTRACTOR_SOURCES = ("repository_fact", "meeting_note", "ticket_comment", "prior_agent_note")
SOURCE_LABELS = {
    "direct_user": "project owner note",
    "repository_fact": "repository observation",
    "meeting_note": "review meeting note",
    "ticket_comment": "tracking ticket comment",
    "prior_agent_note": "earlier handoff note",
}
RECORD_SOURCE_CLASSES = {
    "direct_user": "direct_user",
    "repository_fact": "repository_fact",
    "meeting_note": "assistant_summary",
    "ticket_comment": "assistant_summary",
    "prior_agent_note": "assistant_summary",
}


def _context_id(case_id: str) -> str:
    raw = hashlib.sha256(f"nerd-context-poc:{case_id}".encode()).digest()[:24]
    encoded = base64.b32encode(raw).decode("ascii").rstrip("=").lower()
    value = f"ctx_{encoded}"
    if not ID_RE.fullmatch(value):
        raise AssertionError("generated non-canonical context ID")
    return value


def _format(value: str, number: int) -> str:
    return value.format(n=number)


def _historical_distractor(category: str, number: int, offset: int) -> str:
    subjects = {
        "resumption": f"service-{number}-archive-{offset}",
        "cross_session": f"package-{number}-archive-{offset}",
        "supersession": f"configuration-{number}-revision-{offset}",
        "distractor": f"tenant-{number}-archive-{offset}",
    }
    details = {
        "resumption": "A previously closed migration used a one-step rehearsal and recorded no pending handoff.",
        "cross_session": "A prior release review was closed after an unrelated client check and has no open action.",
        "supersession": "A historical configuration note recorded an earlier revision for a completed environment.",
        "distractor": "A closed audit note recorded a separate evidence bundle with no outstanding finding.",
    }
    return f"Historical note for {subjects[category]}. {details[category]}"


def _event_history(event: dict, *, filler_words: int) -> str:
    source = SOURCE_LABELS[event["history_source"]]
    lines = [f"Source {event['source_ref']} — {source}: {event['value']}"]
    filler = (
        "The source transcript preserves surrounding chronology, filenames, review cadence, and "
        "closed work notes without adding a new instruction or changing the observation above."
    ).split()
    words: list[str] = []
    while len(words) < filler_words:
        words.extend(filler[: filler_words - len(words)])
    if words:
        lines.append(" ".join(words))
    return "\n".join(lines)


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2 or set(payload.get("groups", {})) != set(CATEGORY_COUNTS):
        raise ValueError("invalid context experiment corpus schema")
    cases: list[dict] = []
    for category, expected_count in CATEGORY_COUNTS.items():
        template = payload["groups"][category]
        if template.get("count") != expected_count:
            raise ValueError(f"{category} must define exactly {expected_count} cases")
        for number in range(1, expected_count + 1):
            case_id = f"{category}-{number:02d}"
            case = {
                "id": case_id,
                "category": category,
                "intention": _format(template["intention"], number),
                "request": _format(template["request"], number),
                "scope": _format(template["scope"], number),
                "authority": _format(template["authority"], number),
                "events": [],
            }
            if category != "short_control":
                case["context_id"] = _context_id(case_id)
            for index, event in enumerate(template["events"], start=1):
                if event["source"] not in SOURCE_LABELS:
                    raise ValueError(f"{case_id} has an unsupported source")
                item = {
                    "id": f"{case_id}-r{index:02d}",
                    "kind": event["kind"],
                    "value": _format(event["value"], number),
                    "source": RECORD_SOURCE_CLASSES[event["source"]],
                    "history_source": event["source"],
                    "source_ref": f"{case_id}-event-{index:02d}",
                    "event_index": index,
                    "revision": index,
                    "required": bool(event.get("required", True)),
                }
                if "supersedes_event" in event:
                    item["supersedes_event"] = int(event["supersedes_event"])
                case["events"].append(item)
            for offset in range(1, int(template.get("historical_distractor_count", 0)) + 1):
                index = len(case["events"]) + 1
                history_source = DISTRACTOR_SOURCES[(number + offset - 2) % len(DISTRACTOR_SOURCES)]
                case["events"].append(
                    {
                        "id": f"{case_id}-r{index:02d}",
                        "kind": "evidence",
                        "value": _historical_distractor(category, number, offset),
                        "source": RECORD_SOURCE_CLASSES[history_source],
                        "history_source": history_source,
                        "source_ref": f"{case_id}-event-{index:02d}",
                        "event_index": index,
                        "revision": index,
                        "required": False,
                    }
                )
            if category != "short_control":
                case["capture_checkpoints"] = [4, len(case["events"])]
            cases.append(case)
    ids = [case["context_id"] for case in cases if "context_id" in case]
    if len(ids) != len(set(ids)):
        raise ValueError("context IDs must be unique")
    return cases


def active_records(case: dict, *, through_event: int | None = None) -> list[dict]:
    """Return evaluator records at a chronological prefix; metadata is not history text."""
    eligible = [
        dict(event)
        for event in case["events"]
        if through_event is None or event["event_index"] <= through_event
    ]
    superseded = {
        event["supersedes_event"]
        for event in eligible
        if "supersedes_event" in event
    }
    for event in eligible:
        event["active"] = event["event_index"] not in superseded
        event["context_id"] = case.get("context_id")
    return eligible


def required_records(case: dict, *, through_event: int | None = None) -> list[dict]:
    return [
        event
        for event in active_records(case, through_event=through_event)
        if event["active"] and event["required"]
    ]


def materialize_history(
    case: dict,
    *,
    through_event: int | None = None,
    after_event: int | None = None,
) -> str:
    """Render chronological source observations without evaluator-only metadata."""
    events = case["events"]
    end = len(events) if through_event is None else through_event
    start = 0 if after_event is None else after_event
    if not 0 <= start <= end <= len(events):
        raise ValueError("invalid chronological history range")
    selected = [event for event in events if start < event["event_index"] <= end]
    if not selected:
        return ""
    total_words = 9_000 + (int(case["id"].rsplit("-", 1)[1]) - 1) * 650
    per_event, remainder = divmod(total_words, len(events))
    return "\n\n".join(
        _event_history(
            event,
            filler_words=per_event + (1 if event["event_index"] <= remainder else 0),
        )
        for event in selected
    )


def build_resumption_prompt(case: dict) -> str:
    lines = [
        f"Intention: {case['intention']}",
        f"Request: {case['request']}",
        f"Scope: {case['scope']}",
        f"Authority: {case['authority']}",
    ]
    if "context_id" in case:
        lines.append(f"Context ID: {case['context_id']}")
    return "\n".join(lines)


def request_is_resolved(prompt: str, context_id: str | None) -> bool:
    if context_id and context_id not in prompt:
        return False
    return all(f"{label}:" in prompt for label in REQUIRED_PROMPT_LABELS)
