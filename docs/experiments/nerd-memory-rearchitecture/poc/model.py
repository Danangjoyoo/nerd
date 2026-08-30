from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


CONTEXT_FIELDS = ("language", "surface", "project_kind")
AUTHORITY_FIELDS = {
    "authority",
    "current_instructions",
    "endpoint",
    "permissions",
    "authorization",
}
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{16,}"),
    re.compile(r"(?i)(?:password|passwd|token|secret|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----"),
)
STOP_CUES = {
    "a",
    "an",
    "and",
    "authorization",
    "bearer",
    "for",
    "please",
    "redacted",
    "run",
    "the",
    "token",
    "password",
}
CUE_ALIASES = {
    "tests": "test",
    "testing": "test",
    "debug": "diagnose",
    "investigate": "diagnose",
    "fix": "implement",
    "build": "implement",
    "docs": "document",
    "documentation": "document",
    "database": "schema",
    "migration": "schema",
    "ui": "browser",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sanitize_text(text: str) -> str:
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(" REDACTED ", sanitized)
    return sanitized


def command_cues(text: str) -> tuple[str, ...]:
    tokens = []
    for token in TOKEN_RE.findall(sanitize_text(text).lower()):
        normalized = CUE_ALIASES.get(token, token)
        if normalized not in STOP_CUES and normalized not in tokens:
            tokens.append(normalized)
    return tuple(sorted(tokens))


def _string_tuple(value: Iterable[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(sanitize_text(str(item)) for item in value)


def _context(value: Mapping[str, Any]) -> dict[str, str]:
    return {
        field: sanitize_text(str(value.get(field, "unknown")))
        for field in CONTEXT_FIELDS
    }


def context_key(context: Mapping[str, str]) -> tuple[str, str, str]:
    return tuple(context.get(field, "unknown") for field in CONTEXT_FIELDS)  # type: ignore[return-value]


def edges_from_steps(steps: Sequence[str]) -> tuple[tuple[str, str], ...]:
    return tuple((steps[index], steps[index + 1]) for index in range(len(steps) - 1))


@dataclass(eq=True)
class Episode:
    episode_id: str
    sequence: int
    repository: str
    context: dict[str, str]
    command_cues: tuple[str, ...]
    action: str
    tools: tuple[str, ...]
    steps: tuple[str, ...]
    required_edges: tuple[tuple[str, str], ...]
    skills: tuple[str, ...]
    output_signals: tuple[str, ...]
    output_valid: bool
    output_severity: str
    verified: bool
    verifier: str
    feedback: str
    corrected_tools: tuple[str, ...] = ()
    corrected_steps: tuple[str, ...] = ()
    corrected_skills: tuple[str, ...] = ()
    cost: dict[str, float] = field(default_factory=dict)
    memory_origin: str = "direct_observation"
    source_episode_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "sequence": self.sequence,
            "repository": self.repository,
            "context": dict(sorted(self.context.items())),
            "command_cues": list(self.command_cues),
            "action": self.action,
            "tools": list(self.tools),
            "steps": list(self.steps),
            "required_edges": [list(edge) for edge in self.required_edges],
            "skills": list(self.skills),
            "output_signals": list(self.output_signals),
            "output_valid": self.output_valid,
            "output_severity": self.output_severity,
            "verified": self.verified,
            "verifier": self.verifier,
            "feedback": self.feedback,
            "corrected_tools": list(self.corrected_tools),
            "corrected_steps": list(self.corrected_steps),
            "corrected_skills": list(self.corrected_skills),
            "cost": dict(sorted(self.cost.items())),
            "memory_origin": self.memory_origin,
            "source_episode_ids": list(self.source_episode_ids),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Episode":
        return cls(
            episode_id=str(value["episode_id"]),
            sequence=int(value["sequence"]),
            repository=str(value["repository"]),
            context=_context(value["context"]),
            command_cues=_string_tuple(value["command_cues"]),
            action=str(value["action"]),
            tools=_string_tuple(value["tools"]),
            steps=_string_tuple(value["steps"]),
            required_edges=tuple(tuple(str(part) for part in edge) for edge in value["required_edges"]),
            skills=_string_tuple(value["skills"]),
            output_signals=_string_tuple(value["output_signals"]),
            output_valid=bool(value["output_valid"]),
            output_severity=str(value["output_severity"]),
            verified=bool(value["verified"]),
            verifier=str(value["verifier"]),
            feedback=str(value["feedback"]),
            corrected_tools=_string_tuple(value.get("corrected_tools")),
            corrected_steps=_string_tuple(value.get("corrected_steps")),
            corrected_skills=_string_tuple(value.get("corrected_skills")),
            cost={str(key): float(item) for key, item in value.get("cost", {}).items()},
            memory_origin=str(value.get("memory_origin", "direct_observation")),
            source_episode_ids=_string_tuple(value.get("source_episode_ids")),
        )


def capture_episode(raw: Mapping[str, Any]) -> Episode:
    # Authority-bearing fields are intentionally ignored rather than represented.
    _ = AUTHORITY_FIELDS.intersection(raw)
    steps = _string_tuple(raw.get("steps"))
    corrected_steps = _string_tuple(raw.get("corrected_steps"))
    return Episode(
        episode_id=sanitize_text(str(raw["episode_id"])),
        sequence=int(raw["sequence"]),
        repository=sanitize_text(str(raw.get("repository", "unknown"))),
        context=_context(raw.get("context", {})),
        command_cues=command_cues(str(raw.get("raw_command", ""))),
        action=sanitize_text(str(raw.get("action", "unknown"))),
        tools=_string_tuple(raw.get("tools")),
        steps=steps,
        required_edges=tuple(
            tuple(sanitize_text(str(part)) for part in edge)
            for edge in raw.get("required_edges", edges_from_steps(steps))
        ),
        skills=_string_tuple(raw.get("skills")),
        output_signals=_string_tuple(raw.get("output_signals")),
        output_valid=bool(raw.get("output_valid", True)),
        output_severity=sanitize_text(str(raw.get("output_severity", "none"))),
        verified=bool(raw.get("verified", False)),
        verifier=sanitize_text(str(raw.get("verifier", "unknown"))),
        feedback=sanitize_text(str(raw.get("feedback", "none"))),
        corrected_tools=_string_tuple(raw.get("corrected_tools")),
        corrected_steps=corrected_steps,
        corrected_skills=_string_tuple(raw.get("corrected_skills")),
        cost={sanitize_text(str(key)): float(value) for key, value in raw.get("cost", {}).items()},
        memory_origin=sanitize_text(str(raw.get("memory_origin", "direct_observation"))),
        source_episode_ids=_string_tuple(raw.get("source_episode_ids")),
    )


def chronological_split(
    episodes: Sequence[Episode],
) -> tuple[list[Episode], list[Episode], list[Episode]]:
    ordered = sorted(episodes, key=lambda item: (item.sequence, item.episode_id))
    train_end = math.floor(len(ordered) * 0.60)
    calibration_end = train_end + math.floor(len(ordered) * 0.20)
    return ordered[:train_end], ordered[train_end:calibration_end], ordered[calibration_end:]


@dataclass(frozen=True)
class Advice:
    action: str | None
    tools: tuple[str, ...]
    steps: tuple[str, ...]
    step_edges: tuple[tuple[str, str], ...]
    skills: tuple[str, ...]
    reject_output: bool
    abstained: bool
    confidence: float
    origin: str
    source_episode_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "tools": list(self.tools),
            "steps": list(self.steps),
            "step_edges": [list(edge) for edge in self.step_edges],
            "skills": list(self.skills),
            "reject_output": self.reject_output,
            "abstained": self.abstained,
            "confidence": self.confidence,
            "origin": self.origin,
            "source_episode_ids": list(self.source_episode_ids),
        }


def resolve_current(advice: Advice, explicit: Mapping[str, Any]) -> dict[str, Any]:
    """Apply current explicit choices outside the learner; explicit always wins."""

    resolved = advice.to_dict()
    for field_name in ("action", "tools", "steps", "skills"):
        if field_name in explicit and explicit[field_name] is not None:
            resolved[field_name] = explicit[field_name]
    resolved["authority_source"] = "current_request"
    return resolved


class BehaviorMemory:
    """Small deterministic advisor used to test behavioral-memory mechanisms."""

    def __init__(self, profile: int):
        if profile not in (1, 2, 3):
            raise ValueError("profile must be 1, 2, or 3")
        self.profile = profile
        self.action_counts: defaultdict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
        self.action_sources: defaultdict[tuple[Any, ...], defaultdict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.resource_counts: defaultdict[
            tuple[str, tuple[Any, ...]], Counter[tuple[str, ...]]
        ] = defaultdict(Counter)
        self.resource_sources: defaultdict[
            tuple[str, tuple[Any, ...], tuple[str, ...]], set[str]
        ] = defaultdict(set)
        self.guard_counts: defaultdict[str, Counter[bool]] = defaultdict(Counter)
        self.guard_threshold = 0.50
        self.abstain_threshold = 0.60
        self.correction_streak: defaultdict[tuple[str, tuple[str, str, str]], int] = defaultdict(int)
        self.retired: defaultdict[
            tuple[str, tuple[Any, ...]], set[tuple[str, ...]]
        ] = defaultdict(set)
        self.episodes: dict[str, Episode] = {}

    def _action_key(self, cue: str, context: Mapping[str, str], repository: str) -> tuple[Any, ...]:
        if self.profile == 1:
            return (cue,)
        return (cue, *context_key(context))

    def _resource_key(
        self, action: str, context: Mapping[str, str], repository: str
    ) -> tuple[Any, ...]:
        if self.profile == 1:
            return (action,)
        return (action, *context_key(context))

    def fit(
        self, train: Sequence[Episode], calibration: Sequence[Episode] | None = None
    ) -> "BehaviorMemory":
        for episode in sorted(train, key=lambda item: (item.sequence, item.episode_id)):
            self.observe(episode)
        if self.profile == 3 and calibration:
            self._calibrate(calibration)
        return self

    def _calibrate(self, calibration: Sequence[Episode]) -> None:
        best: tuple[float, float] | None = None
        for threshold in (0.50, 0.60, 0.70, 0.80, 0.90):
            invalid = valid = rejected_invalid = rejected_valid = 0
            for episode in calibration:
                should_reject = self._guard_decision(episode.output_signals, threshold)
                if episode.output_valid:
                    valid += 1
                    rejected_valid += int(should_reject)
                else:
                    invalid += 1
                    rejected_invalid += int(should_reject)
            recall = rejected_invalid / invalid if invalid else 1.0
            false_rejection = rejected_valid / valid if valid else 0.0
            if recall >= 0.90 and false_rejection <= 0.02:
                best = (false_rejection, threshold)
                break
        if best is not None:
            self.guard_threshold = best[1]

    def observe(self, episode: Episode) -> None:
        self.episodes[episode.episode_id] = episode
        invalid = not episode.output_valid or episode.feedback == "rejected"
        for signal in episode.output_signals:
            self.guard_counts[signal][invalid] += 1

        if self.profile == 3:
            eligible = episode.verified and episode.output_valid and episode.feedback in {
                "accepted",
                "corrected",
            }
        else:
            eligible = True
        if not eligible:
            return

        context = episode.context
        for cue in episode.command_cues:
            key = self._action_key(cue, context, episode.repository)
            self.action_counts[key][episode.action] += 1
            self.action_sources[key][episode.action].add(episode.episode_id)

        tools = episode.corrected_tools if episode.feedback == "corrected" and episode.corrected_tools else episode.tools
        steps = episode.corrected_steps if episode.feedback == "corrected" and episode.corrected_steps else episode.steps
        skills = episode.corrected_skills if episode.feedback == "corrected" and episode.corrected_skills else episode.skills
        key = self._resource_key(episode.action, context, episode.repository)

        if self.profile == 3 and episode.feedback == "corrected":
            streak_key = (episode.action, context_key(context))
            self.correction_streak[streak_key] += 1
            if self.correction_streak[streak_key] >= 3:
                for kind, replacement in (("tools", tools), ("steps", steps), ("skills", skills)):
                    counter = self.resource_counts[(kind, key)]
                    self.retired[(kind, key)].update(value for value in counter if value != replacement)

        for kind, value in (("tools", tools), ("steps", steps), ("skills", skills)):
            self.resource_counts[(kind, key)][value] += 1
            self.resource_sources[(kind, key, value)].add(episode.episode_id)

    @staticmethod
    def _winner(counter: Counter[Any], excluded: set[Any] | None = None) -> tuple[Any | None, int, int]:
        excluded = excluded or set()
        available = [(count, value) for value, count in counter.items() if value not in excluded]
        if not available:
            return None, 0, 0
        available.sort(key=lambda item: (-item[0], canonical_json(item[1])))
        total = sum(count for count, _ in available)
        return available[0][1], available[0][0], total

    def _predict_action(
        self, cues: Sequence[str], context: Mapping[str, str], repository: str
    ) -> tuple[str | None, float, set[str]]:
        aggregate: Counter[str] = Counter()
        source_map: defaultdict[str, set[str]] = defaultdict(set)
        for cue in sorted(set(cues)):
            key = self._action_key(cue, context, repository)
            aggregate.update(self.action_counts.get(key, {}))
            for action, sources in self.action_sources.get(key, {}).items():
                source_map[action].update(sources)
        winner, count, total = self._winner(aggregate)
        if winner is None:
            return None, 0.0, set()
        confidence = count / total if total else 0.0
        return str(winner), confidence, source_map[str(winner)]

    def _predict_resource(
        self, kind: str, key: tuple[Any, ...]
    ) -> tuple[tuple[str, ...], set[str]]:
        winner, _, _ = self._winner(
            self.resource_counts.get((kind, key), Counter()),
            self.retired.get((kind, key), set()),
        )
        if winner is None:
            return (), set()
        value = tuple(winner)
        return value, set(self.resource_sources.get((kind, key, value), set()))

    def _guard_decision(self, signals: Sequence[str], threshold: float | None = None) -> bool:
        threshold = self.guard_threshold if threshold is None else threshold
        for signal in signals:
            counts = self.guard_counts.get(signal, Counter())
            total = counts[True] + counts[False]
            if total and counts[True] / total >= threshold:
                return True
        return False

    def advise(
        self,
        command_cues: Sequence[str],
        context: Mapping[str, str],
        output_signals: Sequence[str] = (),
        repository: str = "unknown",
    ) -> Advice:
        action, confidence, sources = self._predict_action(command_cues, context, repository)
        abstained = action is None or (self.profile == 3 and confidence < self.abstain_threshold)
        reject_output = self.profile == 3 and self._guard_decision(output_signals)
        if abstained or action is None:
            return Advice(
                action=None,
                tools=(),
                steps=(),
                step_edges=(),
                skills=(),
                reject_output=reject_output,
                abstained=True,
                confidence=confidence,
                origin="behavioral_memory_advice",
                source_episode_ids=tuple(sorted(sources)),
            )

        key = self._resource_key(action, context, repository)
        tools, tool_sources = self._predict_resource("tools", key)
        steps, step_sources = self._predict_resource("steps", key)
        skills, skill_sources = self._predict_resource("skills", key)
        sources.update(tool_sources)
        sources.update(step_sources)
        sources.update(skill_sources)
        return Advice(
            action=action,
            tools=tools,
            steps=steps,
            step_edges=edges_from_steps(steps),
            skills=skills,
            reject_output=reject_output,
            abstained=False,
            confidence=confidence,
            origin="behavioral_memory_advice",
            source_episode_ids=tuple(sorted(sources)),
        )

    def obsolete_usage_share(
        self,
        action: str,
        context: Mapping[str, str],
        obsolete_tools: Sequence[str],
        repository: str = "unknown",
    ) -> float:
        key = self._resource_key(action, context, repository)
        value = tuple(obsolete_tools)
        if value in self.retired.get(("tools", key), set()):
            return 0.0
        counter = self.resource_counts.get(("tools", key), Counter())
        total = sum(counter.values())
        return counter[value] / total if total else 0.0


class BaselineAdvisor:
    def __init__(self, kind: str):
        if kind not in {"B0", "B1", "B2"}:
            raise ValueError("baseline kind must be B0, B1, or B2")
        self.kind = kind
        self.action_counts: defaultdict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
        self.resource_counts: defaultdict[
            tuple[str, tuple[Any, ...]], Counter[tuple[str, ...]]
        ] = defaultdict(Counter)

    def fit(self, episodes: Sequence[Episode]) -> "BaselineAdvisor":
        for episode in episodes:
            if not (episode.output_valid and episode.verified and episode.feedback == "accepted"):
                continue
            if self.kind == "B1":
                self.action_counts[("global",)][episode.action] += 1
                resource_key = (episode.action,)
            elif self.kind == "B2":
                for cue in episode.command_cues:
                    self.action_counts[(episode.repository, cue)][episode.action] += 1
                resource_key = (episode.repository, episode.action)
            else:
                continue
            for name, value in (("tools", episode.tools), ("steps", episode.steps), ("skills", episode.skills)):
                self.resource_counts[(name, resource_key)][value] += 1
        return self

    @staticmethod
    def _winner(counter: Counter[Any]) -> Any | None:
        if not counter:
            return None
        return sorted(counter.items(), key=lambda item: (-item[1], canonical_json(item[0])))[0][0]

    def advise(
        self,
        command_cues: Sequence[str],
        context: Mapping[str, str],
        output_signals: Sequence[str] = (),
        repository: str = "unknown",
    ) -> Advice:
        del context, output_signals
        if self.kind == "B0":
            action = None
        elif self.kind == "B1":
            action = self._winner(self.action_counts[("global",)])
        else:
            aggregate: Counter[str] = Counter()
            for cue in command_cues:
                aggregate.update(self.action_counts.get((repository, cue), {}))
            action = self._winner(aggregate)
        if action is None:
            return Advice(None, (), (), (), (), False, True, 0.0, "baseline", ())
        key = (action,) if self.kind == "B1" else (repository, action)
        tools = self._winner(self.resource_counts.get(("tools", key), Counter())) or ()
        steps = self._winner(self.resource_counts.get(("steps", key), Counter())) or ()
        skills = self._winner(self.resource_counts.get(("skills", key), Counter())) or ()
        return Advice(
            str(action), tuple(tools), tuple(steps), edges_from_steps(steps), tuple(skills),
            False, False, 1.0, "baseline", (),
        )
