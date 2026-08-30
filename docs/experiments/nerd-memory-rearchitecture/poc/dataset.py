from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .model import Episode, capture_episode, edges_from_steps


DEVELOPMENT_SEEDS = (11, 17, 23)
HOLDOUT_SEEDS = (101, 103, 107)


@dataclass(frozen=True)
class Template:
    name: str
    context: dict[str, str]
    action: str
    commands: tuple[str, ...]
    tools: tuple[str, ...]
    steps: tuple[str, ...]
    skills: tuple[str, ...]


TEMPLATES = (
    Template(
        "python-api-test",
        {"language": "python", "surface": "api", "project_kind": "service"},
        "test",
        ("test api", "run api tests", "testing api service"),
        ("python3",),
        ("inspect_pytest", "run_pytest", "report"),
        ("create-unit-tests", "nerd-execute"),
    ),
    Template(
        "typescript-browser-test",
        {"language": "typescript", "surface": "browser", "project_kind": "web"},
        "test",
        ("test browser", "run browser tests", "testing browser ui"),
        ("npm",),
        ("inspect_vitest", "run_vitest", "report"),
        ("create-unit-tests", "nerd-execute"),
    ),
    Template(
        "python-api-diagnose",
        {"language": "python", "surface": "api", "project_kind": "service"},
        "diagnose",
        ("diagnose api failure", "debug api failure", "investigate api error"),
        ("python3", "rg"),
        ("reproduce_api", "trace_request", "classify"),
        ("nerd-surgery",),
    ),
    Template(
        "typescript-browser-diagnose",
        {"language": "typescript", "surface": "browser", "project_kind": "web"},
        "diagnose",
        ("diagnose browser failure", "debug browser error", "investigate ui failure"),
        ("browser", "npm"),
        ("reproduce_ui", "inspect_console", "classify"),
        ("nerd-surgery", "use-playwright-mcp-ui-dev"),
    ),
    Template(
        "typescript-component-implement",
        {"language": "typescript", "surface": "component", "project_kind": "web"},
        "implement",
        ("implement component", "build component", "fix component"),
        ("npm", "rg"),
        ("inspect_component", "edit_component", "run_component_test"),
        ("create-frontend-components", "write-typescript-code-style"),
    ),
    Template(
        "python-service-implement",
        {"language": "python", "surface": "service", "project_kind": "service"},
        "implement",
        ("implement service", "build service", "fix service"),
        ("python3", "rg"),
        ("inspect_service", "edit_service", "run_pytest"),
        ("nerd-execute",),
    ),
    Template(
        "markdown-document",
        {"language": "markdown", "surface": "docs", "project_kind": "documentation"},
        "document",
        ("document guide", "write docs guide", "update documentation guide"),
        ("rg",),
        ("inspect_sources", "draft", "validate_links"),
        ("nerd-document",),
    ),
    Template(
        "postgres-schema",
        {"language": "sql", "surface": "database", "project_kind": "service"},
        "schema",
        ("schema database", "design database migration", "update db schema"),
        ("psql", "rg"),
        ("inspect_schema", "edit_migration", "verify_plan"),
        ("design-postgres-schema", "nerd-execute"),
    ),
)

TEMPLATE_BY_CONTEXT = {
    tuple(template.context[field] for field in ("language", "surface", "project_kind")): template
    for template in TEMPLATES
}
TEMPLATE_BY_CONTEXT_ACTION = {
    (
        *(template.context[field] for field in ("language", "surface", "project_kind")),
        template.action,
    ): template
    for template in TEMPLATES
}


def make_raw_episode(
    *,
    episode_id: str,
    sequence: int,
    repository: str = "atlas",
    context: Mapping[str, str] | None = None,
    raw_command: str | None = None,
    command: str | None = None,
    action: str = "test",
    tools: Sequence[str] = ("python3",),
    steps: Sequence[str] = ("inspect_pytest", "run_pytest", "report"),
    skills: Sequence[str] = ("create-unit-tests", "nerd-execute"),
    output_signals: Sequence[str] = (),
    output_valid: bool = True,
    output_severity: str = "none",
    verified: bool = True,
    verifier: str = "focused-test",
    feedback: str = "accepted",
    corrected_tools: Sequence[str] = (),
    corrected_steps: Sequence[str] = (),
    corrected_skills: Sequence[str] = (),
    authority: str | None = None,
    memory_origin: str = "direct_observation",
) -> dict[str, Any]:
    actual_steps = tuple(steps)
    raw: dict[str, Any] = {
        "episode_id": episode_id,
        "sequence": sequence,
        "repository": repository,
        "context": dict(
            context
            or {"language": "python", "surface": "api", "project_kind": "service"}
        ),
        "raw_command": raw_command if raw_command is not None else (command or "test api"),
        "action": action,
        "tools": list(tools),
        "steps": list(actual_steps),
        "required_edges": [list(edge) for edge in edges_from_steps(actual_steps)],
        "skills": list(skills),
        "output_signals": list(output_signals),
        "output_valid": output_valid,
        "output_severity": output_severity,
        "verified": verified,
        "verifier": verifier,
        "feedback": feedback,
        "corrected_tools": list(corrected_tools),
        "corrected_steps": list(corrected_steps),
        "corrected_skills": list(corrected_skills),
        "cost": {"tool_calls": 2.0, "step_count": float(len(actual_steps))},
        "memory_origin": memory_origin,
        "source_episode_ids": [],
    }
    if authority is not None:
        raw["authority"] = authority
    return raw


def _scenario(seed: int, cycle: int, template_index: int) -> tuple[tuple[str, ...], bool, str]:
    marker = (seed + cycle + template_index) % 12
    if marker == 0:
        return ("secret_leak",), False, "high"
    if marker == 1:
        return ("destructive_scope",), False, "high"
    if marker == 2:
        return ("missing_verification",), False, "medium"
    if marker == 3:
        return ("format_mismatch",), False, "low"
    if marker == 4:
        return ("warning_only",), True, "none"
    return (), True, "none"


def generate_development_raw(seed: int) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    rng = random.Random(seed)
    repositories = ("atlas", "beacon", "cinder")
    raw_episodes: list[dict[str, Any]] = []
    seeded_secrets: list[str] = []
    sequence = 0
    for cycle in range(15):
        order = list(range(len(TEMPLATES)))
        rng.shuffle(order)
        for template_index in order:
            template = TEMPLATES[template_index]
            signals, valid, severity = _scenario(seed, cycle, template_index)
            command = template.commands[(seed + cycle + template_index) % len(template.commands)]
            if sequence % 17 == 0:
                secret = f"sk-seeded-{seed:03d}-{sequence:03d}-abcdefghijklmnopqrstuvwxyz"
                command += f" token={secret}"
                seeded_secrets.append(secret)
            if valid:
                tools, steps, skills = template.tools, template.steps, template.skills
                feedback = "accepted"
            else:
                tools, steps, skills = ("unverified-tool",), ("emit", "skip_verify"), ("wrong-skill",)
                feedback = "rejected"
            raw_episodes.append(
                make_raw_episode(
                    episode_id=f"dev-{seed}-{sequence:03d}",
                    sequence=sequence,
                    repository=repositories[(cycle + template_index + seed) % len(repositories)],
                    context=template.context,
                    command=command,
                    action=template.action,
                    tools=tools,
                    steps=steps,
                    skills=skills,
                    output_signals=signals,
                    output_valid=valid,
                    output_severity=severity,
                    verified=valid,
                    feedback=feedback,
                )
            )
            sequence += 1
    return raw_episodes, tuple(seeded_secrets)


def generate_development_stream(seed: int) -> list[Episode]:
    raw, _ = generate_development_raw(seed)
    return [capture_episode(item) for item in raw]


def generate_transfer_stream(seed: int) -> list[Episode]:
    rng = random.Random(seed + 1000)
    episodes: list[Episode] = []
    sequence = 10_000
    repository = f"unseen-{seed}"
    for cycle in range(3):
        order = list(range(len(TEMPLATES)))
        rng.shuffle(order)
        for template_index in order:
            template = TEMPLATES[template_index]
            raw = make_raw_episode(
                episode_id=f"transfer-{seed}-{sequence}",
                sequence=sequence,
                repository=repository,
                context=template.context,
                command=template.commands[(cycle + template_index) % len(template.commands)],
                action=template.action,
                tools=template.tools,
                steps=template.steps,
                skills=template.skills,
            )
            episodes.append(capture_episode(raw))
            sequence += 1
    return episodes


def generate_unknown_stream(seed: int) -> list[Episode]:
    episodes = []
    for index in range(12):
        raw = make_raw_episode(
            episode_id=f"unknown-{seed}-{index}",
            sequence=20_000 + index,
            repository=f"unknown-{seed}",
            context={"language": "rust", "surface": "satellite", "project_kind": "unknown"},
            command=f"quantum teleport payload {index}",
            action="unknown_action",
            tools=("unknown-tool",),
            steps=("unknown-start", "unknown-end"),
            skills=("unknown-skill",),
        )
        episodes.append(capture_episode(raw))
    return episodes


def template_for_context(
    context: Mapping[str, str], action: str | None = None
) -> Template | None:
    context_tuple = tuple(
        context.get(field, "unknown") for field in ("language", "surface", "project_kind")
    )
    if action is not None:
        return TEMPLATE_BY_CONTEXT_ACTION.get((*context_tuple, action))
    return TEMPLATE_BY_CONTEXT.get(context_tuple)
