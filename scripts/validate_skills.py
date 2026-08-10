#!/usr/bin/env python3
"""Validate the public Nerd skill family without third-party dependencies."""

from __future__ import annotations

from pathlib import Path
import re
import sys


PUBLIC_SKILLS = (
    "nerd-smart",
    "nerd-memory",
    "nerd-loop",
    "nerd-surgery",
    "nerd-patrol",
    "nerd-execute",
    "nerd-silent",
    "nerd-fast",
    "nerd-xfast",
)

MANUAL_ONLY_SKILLS = ("nerd-memory",)

REQUIRED_REFERENCES = {
    "nerd-smart": (
        "brainstorming.md",
        "multi-goal-ledger.md",
        "principle-selection.md",
        "spec-template.md",
        "system-design-template.md",
        "plan-template.md",
        "document-overview-template.md",
        "document-how-to-template.md",
        "document-reference-template.md",
        "diagnosis-template.md",
        "rca-template.md",
        "kiss.md",
        "dry.md",
        "yagni.md",
        "comprehensive.md",
    ),
    "nerd-memory": ("memory-contract.md", "research.md"),
    "nerd-loop": (
        "runtime-contract.md",
        "definition-of-done.md",
        "convergence.md",
        "iteration.md",
        "behavioral-memory.md",
        "loop-profiles.md",
    ),
    "nerd-surgery": (
        "systematic-debugging.md",
        "test-first-repair.md",
        "verification.md",
    ),
    "nerd-patrol": ("test-first-remediation.md", "verification.md"),
    "nerd-execute": (),
    "nerd-silent": (),
    "nerd-fast": (),
    "nerd-xfast": (),
}

REQUIRED_SCRIPTS = {
    "nerd-smart": ("prompt_hook.py",),
    "nerd-memory": ("memory.py",),
    "nerd-loop": ("loop.py",),
    "nerd-surgery": (),
    "nerd-patrol": (),
    "nerd-execute": (),
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


def _reference_links(text: str) -> set[str]:
    return set(
        re.findall(
            r"\]\((?:references/)?([^/#)]+\.md)(?:#[^)]+)?\)",
            text,
        )
    )


def _reachable_reference_names(body: str, references_root: Path) -> set[str]:
    reachable: set[str] = set()
    pending = list(_reference_links(body))
    while pending:
        reference = pending.pop()
        if reference in reachable:
            continue
        path = references_root / reference
        if not path.is_file():
            continue
        reachable.add(reference)
        pending.extend(_reference_links(path.read_text(encoding="utf-8")))
    return reachable


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
        reachable_references = _reachable_reference_names(body, references_root)
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
            for nested_skill in references_root.rglob("SKILL.md"):
                relative = nested_skill.relative_to(root)
                violations.append(f"nested skill is forbidden: {relative}")

        for script in REQUIRED_SCRIPTS[name]:
            path = skill_dir / "scripts" / script
            if not path.is_file():
                violations.append(f"missing file: skills/{name}/scripts/{script}")

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
