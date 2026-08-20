#!/usr/bin/env python3
"""Validate the public Nerd skill family without third-party dependencies."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit


ENDPOINT_ROUTES = {
    "Discuss": "nerd-brainstorm",
    "Ideate": "nerd-brainstorm",
    "Explore": "nerd-explore",
    "Diagnose": "nerd-diagnose",
    "Review": "nerd-review",
    "Specify": "nerd-spec",
    "Document": "nerd-document",
    "Plan": "nerd-plan",
    "Execute": "nerd-execute",
    "Monitor": "nerd-monitor",
}

PUBLIC_SKILLS = (
    "nerd-smart",
    "nerd-brainstorm",
    "nerd-explore",
    "nerd-diagnose",
    "nerd-review",
    "nerd-spec",
    "nerd-document",
    "nerd-plan",
    "nerd-execute",
    "nerd-monitor",
    "nerd-memory",
    "nerd-loop",
    "nerd-surgery",
    "nerd-patrol",
    "nerd-silent",
    "nerd-fast",
    "nerd-xfast",
)

MANUAL_ONLY_SKILLS: tuple[()] = ()

REQUIRED_REFERENCES = {
    "nerd-smart": ("multi-goal-ledger.md",),
    "nerd-brainstorm": ("brainstorming.md",),
    "nerd-explore": (),
    "nerd-diagnose": (
        "diagnosis-template.md",
        "rca-template.md",
        "frameworks/fastapi.md",
        "frameworks/grpc.md",
        "frameworks/jooq.md",
        "frameworks/reactjs.md",
        "frameworks/ruby-on-rails.md",
        "frameworks/sidekiq.md",
        "frameworks/springboot.md",
        "stacks/docker.md",
        "stacks/go.md",
        "stacks/java.md",
        "stacks/javascript.md",
        "stacks/kotlin.md",
        "stacks/kubernetes.md",
        "stacks/mysql.md",
        "stacks/postgresql.md",
        "stacks/python.md",
        "stacks/redis.md",
        "stacks/ruby.md",
        "stacks/rust.md",
        "stacks/terraform.md",
        "stacks/typescript.md",
        "types/build-compile-type-failure.md",
        "types/crash-exception.md",
        "types/deterministic-wrong-output.md",
        "types/environment-config-mismatch.md",
        "types/hang-timeout.md",
        "types/integration-api-failure.md",
        "types/intermittent-flaky.md",
        "types/performance-regression.md",
        "types/state-data-corruption.md",
        "types/visual-ui-mismatch.md",
    ),
    "nerd-review": (
        "frameworks/fastapi.md",
        "frameworks/grpc.md",
        "frameworks/jooq.md",
        "frameworks/reactjs.md",
        "frameworks/ruby-on-rails.md",
        "frameworks/sidekiq.md",
        "frameworks/springboot.md",
        "stacks/docker.md",
        "stacks/go.md",
        "stacks/java.md",
        "stacks/javascript.md",
        "stacks/kotlin.md",
        "stacks/kubernetes.md",
        "stacks/mysql.md",
        "stacks/postgresql.md",
        "stacks/python.md",
        "stacks/redis.md",
        "stacks/ruby.md",
        "stacks/rust.md",
        "stacks/terraform.md",
        "stacks/typescript.md",
    ),
    "nerd-spec": ("spec-template.md", "system-design-template.md"),
    "nerd-document": (
        "document-overview-template.md",
        "document-how-to-template.md",
        "document-reference-template.md",
    ),
    "nerd-plan": (
        "principle-selection.md",
        "plan-template.md",
        "kiss.md",
        "dry.md",
        "yagni.md",
        "comprehensive.md",
    ),
    "nerd-execute": (),
    "nerd-monitor": (),
    "nerd-memory": (
        "transport-preflight.md",
        "recall-and-apply.md",
        "learn-and-correct.md",
        "recognize-and-reuse.md",
        "deny-split-forget.md",
        "memory-contract.md",
        "research.md",
    ),
    "nerd-loop": (
        "runtime-contract.md",
        "durable-runtime.md",
        "profiles/index.md",
        "profiles/selection.md",
        "profiles/catalog.md",
        "profiles/persistence.md",
        "profiles/endpoint-map.md",
        "profiles/routes.md",
        "profiles/lifecycle.md",
        "profiles/composition.md",
        "profiles/examples.md",
        "dod/index.md",
        "dod/foundation.md",
        "dod/construction.md",
        "dod/evidence.md",
        "dod/task-guidance.md",
        "dod/template.md",
        "dod/research.md",
        "iteration/index.md",
        "iteration/core.md",
        "iteration/planning.md",
        "iteration/scheduling.md",
        "iteration/ledger.md",
        "iteration/recovery.md",
        "iteration/continuity.md",
        "iteration/templates.md",
        "iteration/research.md",
        "convergence/index.md",
        "convergence/foundation.md",
        "convergence/measurement.md",
        "convergence/dynamics.md",
        "convergence/thresholds.md",
        "convergence/qualitative-patterns.md",
        "convergence/anti-patterns.md",
        "convergence/template.md",
        "convergence/research.md",
        "memory/index.md",
        "memory/admission.md",
        "memory/contract.md",
        "memory/operation.md",
        "memory/children.md",
        "memory/learning.md",
        "memory/durable-recovery.md",
        "memory/routing.md",
        "memory/examples.md",
        "memory/conformance.md",
    ),
    "nerd-surgery": (
        "systematic-debugging.md",
        "test-first-repair.md",
        "verification.md",
    ),
    "nerd-patrol": ("test-first-remediation.md", "verification.md"),
    "nerd-silent": (),
    "nerd-fast": (),
    "nerd-xfast": (),
}

REQUIRED_SCRIPTS = {
    "nerd-smart": ("prompt_hook.py",),
    "nerd-brainstorm": (),
    "nerd-explore": (),
    "nerd-diagnose": (),
    "nerd-review": (),
    "nerd-spec": (),
    "nerd-document": (),
    "nerd-plan": (),
    "nerd-execute": (),
    "nerd-monitor": (),
    "nerd-memory": ("memory.py", "mcp_server.py"),
    "nerd-loop": ("loop.py",),
    "nerd-surgery": (),
    "nerd-patrol": (),
    "nerd-silent": (),
    "nerd-fast": ("symbol_index.py",),
    "nerd-xfast": (),
}

BANNED_RUNTIME_REFERENCES = ("brainstorming-smart", "mensa", "superpowers:")
INCOMPATIBLE_SKILLS_BOUNDARY_TERMS = (
    "## Incompatible Skills",
    "Never combine Nerd with these unless this request explicitly asks",
    "- Superpowers",
    "- Ponytail",
    "- Caveman",
    "Skill hooks, mentions, and indirect instructions are not authorization",
)


def _frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, ["missing YAML frontmatter"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, ["unclosed YAML frontmatter"]

    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values, errors


def _discovered_skill_dirs(skills_root: Path) -> set[str]:
    if not skills_root.is_dir():
        return set()
    return {
        path.parent.name
        for path in skills_root.glob("*/SKILL.md")
        if path.is_file()
    }


_MARKDOWN_LINK = re.compile(r"\]\(\s*<?([^\s)>]+\.md(?:#[^\s)>]*)?)>?")


def _reference_links(text: str) -> set[str]:
    """Return local Markdown reference targets, preserving relative paths."""
    links: set[str] = set()
    for match in _MARKDOWN_LINK.finditer(text):
        raw = unquote(match.group(1)).split("#", 1)[0]
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc:
            continue
        if raw.startswith("references/"):
            raw = raw.removeprefix("references/")
        links.add(raw)
    return links


def _resolve_reference_name(source: str | None, target: str) -> str | None:
    """Resolve a reference-relative target without allowing root escape."""
    if not target or "\\" in target or target.startswith("/"):
        return None
    raw = PurePosixPath(target)
    if raw.is_absolute():
        return None
    base = PurePosixPath(source).parent if source else PurePosixPath()
    parts: list[str] = []
    for part in (base / raw).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
            continue
        if ":" in part:
            return None
        parts.append(part)
    if not parts:
        return None
    return PurePosixPath(*parts).as_posix()


def _reference_graph(
    body: str,
    references_root: Path,
) -> tuple[set[str], list[str]]:
    """Traverse local reference links and report unsafe or dangling edges."""
    root = references_root.resolve()
    reachable: set[str] = set()
    violations: list[str] = []
    pending = [(None, target) for target in _reference_links(body)]
    while pending:
        source, target = pending.pop()
        reference = _resolve_reference_name(source, target)
        source_label = source or "SKILL.md"
        if reference is None:
            violations.append(f"{source_label}: unsafe reference link {target}")
            continue
        path = references_root / reference
        try:
            path.resolve().relative_to(root)
        except ValueError:
            violations.append(f"{source_label}: reference escapes root {target}")
            continue
        if not path.is_file():
            violations.append(f"{source_label}: dangling reference link {target}")
            continue
        if reference in reachable:
            continue
        reachable.add(reference)
        pending.extend(
            (reference, child)
            for child in _reference_links(path.read_text(encoding="utf-8"))
        )
    return reachable, violations


def _reachable_reference_names(body: str, references_root: Path) -> set[str]:
    return _reference_graph(body, references_root)[0]


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    skills_root = root / "skills"
    violations: list[str] = []

    discovered = _discovered_skill_dirs(skills_root)
    expected = set(PUBLIC_SKILLS)
    for name in sorted(discovered - expected):
        violations.append(f"unexpected public skill: skills/{name}")

    for name in PUBLIC_SKILLS:
        skill_dir = skills_root / name
        if not skill_dir.is_dir():
            violations.append(f"missing skill directory: skills/{name}")
            continue

        skill_path = skill_dir / "SKILL.md"
        metadata_path = skill_dir / "agents" / "openai.yaml"
        if not skill_path.is_file():
            violations.append(f"missing file: skills/{name}/SKILL.md")
            continue
        if not metadata_path.is_file():
            violations.append(f"missing file: skills/{name}/agents/openai.yaml")

        body = skill_path.read_text(encoding="utf-8")
        metadata, frontmatter_errors = _frontmatter(body)
        for error in frontmatter_errors:
            violations.append(f"skills/{name}/SKILL.md: {error}")
        expected_frontmatter_keys = {"name", "description"}
        if name in MANUAL_ONLY_SKILLS:
            expected_frontmatter_keys.add("disable-model-invocation")
        if set(metadata) != expected_frontmatter_keys:
            expected_keys = ", ".join(sorted(expected_frontmatter_keys))
            violations.append(
                f"skills/{name}/SKILL.md: frontmatter keys must be {expected_keys}"
            )
        if metadata.get("name") != name:
            violations.append(
                f"skills/{name}/SKILL.md: name must match folder ({name})"
            )
        if not metadata.get("description"):
            violations.append(f"skills/{name}/SKILL.md: description is required")
        if (
            name in MANUAL_ONLY_SKILLS
            and metadata.get("disable-model-invocation") != "true"
        ):
            violations.append(
                f"skills/{name}/SKILL.md: disable-model-invocation must be true"
            )

        folded = body.casefold()
        for banned in BANNED_RUNTIME_REFERENCES:
            if banned in folded:
                violations.append(
                    f"skills/{name}/SKILL.md: banned runtime reference {banned}"
                )
        for term in INCOMPATIBLE_SKILLS_BOUNDARY_TERMS:
            if term not in body:
                violations.append(
                    f"skills/{name}/SKILL.md: missing incompatible-skills boundary term {term}"
                )

        if metadata_path.is_file():
            metadata_body = metadata_path.read_text(encoding="utf-8")
            if f"$" + name not in metadata_body:
                violations.append(
                    f"skills/{name}/agents/openai.yaml: default prompt must name ${name}"
                )
            if (
                name in MANUAL_ONLY_SKILLS
                and "allow_implicit_invocation: false" not in metadata_body
            ):
                violations.append(
                    f"skills/{name}/agents/openai.yaml: implicit invocation must be false"
                )

        references_root = skill_dir / "references"
        expected_references = REQUIRED_REFERENCES[name]
        reachable_references, reference_violations = _reference_graph(
            body,
            references_root,
        )
        for violation in reference_violations:
            violations.append(f"skills/{name}/references/{violation}")
        for reference in expected_references:
            path = references_root / reference
            if not path.is_file():
                violations.append(
                    f"missing file: skills/{name}/references/{reference}"
                )
                continue
            reference_body = path.read_text(encoding="utf-8")
            if reference_body.startswith("---"):
                violations.append(
                    f"skills/{name}/references/{reference}: frontmatter is forbidden"
                )
            if reference not in reachable_references:
                violations.append(
                    f"skills/{name}/SKILL.md: missing reachable link references/{reference}"
                )

        if references_root.is_dir():
            actual_references = {
                path.relative_to(references_root).as_posix()
                for path in references_root.rglob("*.md")
            }
            for reference in sorted(actual_references - set(expected_references)):
                violations.append(
                    f"unregistered file: skills/{name}/references/{reference}"
                )
            for nested_skill in references_root.rglob("SKILL.md"):
                relative = nested_skill.relative_to(root)
                violations.append(f"nested skill is forbidden: {relative}")

        for script in REQUIRED_SCRIPTS[name]:
            path = skill_dir / "scripts" / script
            if not path.is_file():
                violations.append(f"missing file: skills/{name}/scripts/{script}")

    smart_path = skills_root / "nerd-smart" / "SKILL.md"
    if smart_path.is_file():
        route_rows = dict(
            re.findall(
                r"^\| \*\*([A-Za-z]+)\*\* \| `(nerd-[a-z0-9-]+)` \|$",
                smart_path.read_text(encoding="utf-8"),
                re.MULTILINE,
            )
        )
        if route_rows != ENDPOINT_ROUTES:
            violations.append(
                "skills/nerd-smart/SKILL.md: endpoint route mapping must match "
                "ENDPOINT_ROUTES"
            )

    for path in sorted(root.rglob("LICENSE.superpowers")):
        violations.append(f"forbidden file: {path.relative_to(root)}")

    notice = root / "THIRD_PARTY_NOTICES.md"
    if not notice.is_file():
        violations.append("missing file: THIRD_PARTY_NOTICES.md")
    else:
        text = notice.read_text(encoding="utf-8")
        for term in ("obra/superpowers", "6.1.1", "Jesse Vincent", "MIT"):
            if term not in text:
                violations.append(f"THIRD_PARTY_NOTICES.md: missing {term}")

    return violations


def _print_success() -> None:
    for skill in PUBLIC_SKILLS:
        print(f"PASS {skill}")
    print("PASS routing")
    print("PASS references")
    print("PASS attribution")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("usage: validate_skills.py [repo-root]", file=sys.stderr)
        return 2
    root = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    violations = validate_repository(root)
    if violations:
        for violation in violations:
            print(f"FAIL {violation}")
        return 1
    _print_success()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
