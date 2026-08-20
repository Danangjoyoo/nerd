from pathlib import Path
import tempfile
import unittest

from scripts.validate_skills import (
    ENDPOINT_ROUTES,
    MANUAL_ONLY_SKILLS,
    PUBLIC_SKILLS,
    REQUIRED_REFERENCES,
    REQUIRED_SCRIPTS,
    _reference_graph,
    _reachable_reference_names,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_endpoint_route_set_is_exact(self):
        self.assertEqual(
            ENDPOINT_ROUTES,
            {
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
            },
        )

    def test_manual_only_skill_set_is_exact(self):
        self.assertEqual(MANUAL_ONLY_SKILLS, ())

    def test_public_skill_set_is_exact(self):
        self.assertEqual(
            PUBLIC_SKILLS,
            (
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
            ),
        )

    def test_reference_ownership_is_exact(self):
        self.assertEqual(
            REQUIRED_REFERENCES,
            {
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
                "nerd-spec": (
                    "spec-template.md",
                    "system-design-template.md",
                ),
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
                "nerd-patrol": (
                    "test-first-remediation.md",
                    "verification.md",
                ),
                "nerd-silent": (),
                "nerd-fast": (),
                "nerd-xfast": (),
            },
        )
        self.assertFalse((ROOT / "skills" / "nerd-execute" / "references").exists())
        self.assertFalse((ROOT / "skills" / "nerd-fast" / "references").exists())
        self.assertFalse((ROOT / "skills" / "nerd-xfast" / "references").exists())
        self.assertEqual(REQUIRED_SCRIPTS["nerd-smart"], ("prompt_hook.py",))
        for skill in ENDPOINT_ROUTES.values():
            if skill != "nerd-execute":
                self.assertEqual(REQUIRED_SCRIPTS[skill], ())
        self.assertEqual(
            REQUIRED_SCRIPTS["nerd-memory"], ("memory.py", "mcp_server.py")
        )
        self.assertEqual(REQUIRED_SCRIPTS["nerd-loop"], ("loop.py",))
        self.assertEqual(REQUIRED_SCRIPTS["nerd-fast"], ("symbol_index.py",))
        self.assertEqual(REQUIRED_SCRIPTS["nerd-xfast"], ())

    def test_ufast_is_archived_outside_public_skills(self):
        self.assertFalse((ROOT / "skills" / "nerd-ufast").exists())
        self.assertTrue(
            (ROOT / "docs" / "experiments" / "nerd-ufast" / "skill" / "SKILL.md").is_file()
        )

    def test_reference_files_match_registry(self):
        for skill, expected in REQUIRED_REFERENCES.items():
            references = ROOT / "skills" / skill / "references"
            actual = (
                {
                    path.relative_to(references).as_posix()
                    for path in references.rglob("*.md")
                }
                if references.is_dir()
                else set()
            )
            with self.subTest(skill=skill):
                self.assertEqual(actual, set(expected))

    def test_reference_reachability_follows_lazy_links(self):
        with tempfile.TemporaryDirectory() as directory:
            references = Path(directory)
            (references / "entry.md").write_text(
                "[Nested](nested.md)", encoding="utf-8"
            )
            (references / "nested.md").write_text("# Nested", encoding="utf-8")
            self.assertEqual(
                _reachable_reference_names(
                    "[Entry](references/entry.md)", references
                ),
                {"entry.md", "nested.md"},
            )

    def test_reference_reachability_supports_safe_nested_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references = root / "references"
            topic = references / "topic"
            topic.mkdir(parents=True)
            (topic / "index.md").write_text(
                "[Core](core.md) [Escape](../../escape.md)",
                encoding="utf-8",
            )
            (topic / "core.md").write_text("# Core", encoding="utf-8")
            (root / "escape.md").write_text("# Escape", encoding="utf-8")

            self.assertEqual(
                _reachable_reference_names(
                    "[Topic](references/topic/index.md)",
                    references,
                ),
                {"topic/index.md", "topic/core.md"},
            )

    def test_reference_graph_resolves_parents_cycles_and_reports_bad_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            references = Path(directory)
            topic = references / "topic"
            topic.mkdir()
            (references / "runtime-contract.md").write_text(
                "[Topic](topic/index.md)", encoding="utf-8"
            )
            (topic / "index.md").write_text(
                "[Core](core.md#scope) [External](https://example.com/research.md)",
                encoding="utf-8",
            )
            (topic / "core.md").write_text(
                "[Runtime](../runtime-contract.md) [Missing](missing.md) "
                "[Unsafe](/tmp/escape.md)",
                encoding="utf-8",
            )

            reachable, violations = _reference_graph(
                "[Runtime](references/runtime-contract.md)",
                references,
            )
            self.assertEqual(
                reachable,
                {"runtime-contract.md", "topic/index.md", "topic/core.md"},
            )
            self.assertTrue(
                any("dangling reference link missing.md" in item for item in violations)
            )
            self.assertTrue(
                any("unsafe reference link /tmp/escape.md" in item for item in violations)
            )

    def test_superpowers_license_files_are_absent(self):
        self.assertEqual(list(ROOT.rglob("LICENSE.superpowers")), [])

    def test_repository_contract(self):
        self.assertEqual(validate_repository(ROOT), [])

    def test_validator_reports_missing_skill_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            violations = validate_repository(Path(directory))
        for skill in PUBLIC_SKILLS:
            self.assertIn(f"missing skill directory: skills/{skill}", violations)


class AttributionTests(unittest.TestCase):
    def test_repository_notice_names_upstream(self):
        body = (ROOT / "THIRD_PARTY_NOTICES.md").read_text()
        for expected in ("obra/superpowers", "6.1.1", "Jesse Vincent", "MIT"):
            self.assertIn(expected, body)

if __name__ == "__main__":
    unittest.main()
