from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def skill_body(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def assert_terms(test: unittest.TestCase, body: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        test.assertIn(term, body)


class SmartContractTests(unittest.TestCase):
    def test_bare_smart_stays_in_smart_without_loading_specialties(self):
        body = skill_body("nerd-smart")
        metadata = (SKILLS / "nerd-smart" / "agents" / "openai.yaml").read_text()
        assert_terms(
            self,
            body,
            (
                "A bare `nerd smart` invocation stays in Nerd Smart",
                "Do not load, invoke, or route to a primary specialty",
                "`route nerd`",
                "`use nerd`",
                "`auto nerd`",
                "If none of those phrases is present, remain in Nerd Smart",
                "A direct specialty invocation is handled by that named specialty",
            ),
        )
        frontmatter = body.split("---", 2)[1]
        self.assertIn("working role before substantive work", frontmatter)
        self.assertNotIn("appropriate Nerd specialty", frontmatter)
        self.assertIn("opt-in specialty routing", metadata)
        self.assertNotIn(
            "Route exactly one primary specialty after focus is established",
            body,
        )

    def test_explicit_nerd_routing_selects_one_specialty_and_global_modifiers(self):
        body = skill_body("nerd-smart")
        assert_terms(
            self,
            body,
            (
                "nerd-surgery",
                "nerd-patrol",
                "nerd-execute",
                "nerd-silent",
                "nerd-fast",
                "exactly one primary specialty",
                "modifier",
            ),
        )

    def test_preserves_focus_and_decision_records(self):
        body = skill_body("nerd-smart")
        assert_terms(
            self,
            body,
            (
                "**Focus Record**",
                "**Decision Record**",
                "**Intention:**",
                "**Expectation:**",
                "**Scope:**",
                "**Role:**",
                "at most two clarification rounds",
            ),
        )

    def test_centralizes_behavior_in_exactly_ten_endpoint_mappings(self):
        body = skill_body("nerd-smart")
        mapping = body.split("## Endpoint Mapping", 1)[1].split(
            "## Focus First", 1
        )[0]
        rows = re.findall(r"^\| \*\*[A-Za-z]+\*\* \|", mapping, re.MULTILINE)

        self.assertEqual(len(rows), 10)
        assert_terms(
            self,
            mapping,
            (
                "Discuss",
                "Ideate",
                "Explore",
                "Diagnose",
                "Review",
                "Specify",
                "Document",
                "Plan",
                "Execute",
                "Monitor",
                "The endpoint controls the next action and stopping boundary",
                "does not authorize specialty routing",
                "one brief self-review",
            ),
        )
        self.assertIn(
            "**Expectation:** [One endpoint from Endpoint Mapping]",
            body,
        )
        stop_rule = body.split("## Stop at the Endpoint", 1)[1]
        self.assertIn("Follow the confirmed row in Endpoint Mapping", stop_rule)
        self.assertNotIn("- Discuss or ideate", stop_rule)

    def test_confirmation_style_balances_question_cost_and_risk(self):
        body = skill_body("nerd-smart")
        confirmation = body.split("## Confirmation Style", 1)[1].split(
            "## Route Only When Explicitly Authorized", 1
        )[0]

        assert_terms(
            self,
            confirmation,
            (
                "Ask one question at a time",
                "two or three mutually exclusive options",
                "recommended option first",
                "Do not ask about low-impact details",
                "Do ask when the answer materially changes",
            ),
        )
        focus = body.split("## Focus First", 1)[1].split(
            "## Confirmation Style", 1
        )[0]
        self.assertIn("Follow Confirmation Style", focus)

    def test_uses_internal_brainstorming_reference(self):
        body = skill_body("nerd-smart")
        self.assertIn("references/brainstorming.md", body)
        self.assertNotIn("superpowers:", body.casefold())


class SurgeryContractTests(unittest.TestCase):
    def test_preserves_diagnostic_records(self):
        body = skill_body("nerd-surgery")
        assert_terms(
            self,
            body,
            (
                "**Case Record**",
                "**Diagnosis**",
                "**Uncertainty Check**",
                "**Source Request**",
                "**Verification Experiment**",
                "**Architecture Check**",
                "Confirmed",
                "Probable",
                "Unknown",
            ),
        )

    def test_requires_resolved_focus_and_runs_one_experiment_loop(self):
        body = skill_body("nerd-surgery")
        discipline = body.split("## Surgery Discipline", 1)[1].split(
            "## Diagnostic Contract", 1
        )[0]
        rows = re.findall(
            r"^\| \*\*(Focus|Observe|Map|Experiment|Analyze|Iterate)\*\* \|",
            discipline,
            re.MULTILINE,
        )

        self.assertEqual(len(rows), 6)
        assert_terms(
            self,
            body,
            (
                "resolved Focus Record",
                "all four fields are explicit",
                "endpoint is **Diagnose** or **Execute**",
                "Do not investigate or repair before the record is resolved",
            ),
        )
        assert_terms(
            self,
            discipline,
            (
                "base diagnostic frame",
                "hypothesis, not evidence",
                "user inputs and symptom",
                "Check Generic Diagnostic Mappings first",
                "smallest discriminating experiment",
                "Compare predicted and observed signals",
                "Supported**, **Rejected**, or **Inconclusive",
                "repeat from Observe",
                "one short, sharp question",
                "two or three mutually exclusive options",
                "recommended option first",
            ),
        )

    def test_limits_failed_corrections_and_escalates_architecture(self):
        body = skill_body("nerd-surgery")
        correction = body.split("## Correction Discipline", 1)[1].split(
            "## Records", 1
        )[0]

        assert_terms(
            self,
            correction,
            (
                "Treat every correction as one hypothesis test",
                "one causal variable",
                "same reproducer",
                "never stack speculative fixes",
                "After the first failed correction",
                "After the second failed correction",
                "Do not attempt a third correction",
            ),
        )

    def test_repair_is_conditional_and_evidence_bound(self):
        body = skill_body("nerd-surgery")
        assert_terms(
            self,
            body,
            (
                "references/systematic-debugging.md",
                "references/test-first-repair.md",
                "references/verification.md",
                "attempt",
                "fresh proof",
            ),
        )
        self.assertNotIn("superpowers:", body.casefold())

    def test_uses_exactly_ten_optional_generic_diagnostic_mappings(self):
        body = skill_body("nerd-surgery")
        mapping = body.split("## Generic Diagnostic Mappings", 1)[1].split(
            "## Surgery Discipline", 1
        )[0]
        rows = re.findall(r"^\| \*\*[0-9]+\*\* \|", mapping, re.MULTILINE)

        self.assertEqual(len(rows), 10)
        assert_terms(
            self,
            mapping,
            (
                "Deterministic wrong output",
                "Intermittent or flaky",
                "Crash or exception",
                "Hang or timeout",
                "Performance regression",
                "State or data corruption",
                "Integration or API failure",
                "Build, compile, or type failure",
                "Environment or configuration mismatch",
                "Visual or UI mismatch",
            ),
        )
        self.assertIn("Check Generic Diagnostic Mappings first", body)
        self.assertIn("Mappings select evidence; they never establish cause", body)
        self.assertNotIn("lookup at `## Generic Diagnostic Mapping` first", body)


class PatrolContractTests(unittest.TestCase):
    def test_preserves_scope_and_finding_records(self):
        body = skill_body("nerd-patrol")
        assert_terms(
            self,
            body,
            (
                "**Patrol Scope**",
                "**Scope Check**",
                "**Security Finding**",
                "**Validation Needed**",
                "**Patrol Result**",
                "Confirmed Finding",
                "Needs Validation",
                "Dismissed",
            ),
        )

    def test_requires_reachability_and_safe_proof(self):
        body = skill_body("nerd-patrol")
        assert_terms(
            self,
            body,
            (
                "advisory alone is not a finding",
                "No confirmed findings within this scope",
                "references/test-first-remediation.md",
                "references/verification.md",
            ),
        )
        self.assertNotIn("superpowers:", body.casefold())

    def test_uses_exactly_ten_optional_generic_security_mappings(self):
        body = skill_body("nerd-patrol")
        mapping = body.split("## Generic Security Mappings", 1)[1].split(
            "## Scope First", 1
        )[0]
        rows = re.findall(r"^\| \*\*[0-9]+\*\* \|", mapping, re.MULTILINE)

        self.assertEqual(len(rows), 10)
        assert_terms(
            self,
            mapping,
            (
                "Authentication or session",
                "Authorization or object access",
                "Injection or command execution",
                "File or path handling",
                "Deserialization or parsing",
                "Secrets or cryptography",
                "Network request forgery",
                "Browser or client security",
                "Concurrency or business logic",
                "Dependency or configuration exposure",
            ),
        )
        self.assertIn("Use a mapping only when", body)
        self.assertIn(
            "Mappings select evidence; they never establish a finding", body
        )
        self.assertNotIn("always scan", body.casefold())


class ExecuteContractTests(unittest.TestCase):
    def test_requires_resolved_focus_and_uses_conditional_discipline(self):
        body = skill_body("nerd-execute")
        discipline = body.split("## Execution Discipline", 1)[1].split(
            "## Execute Directly", 1
        )[0]
        rows = re.findall(
            r"^\| \*\*(Focus Record|Current plan|Execution scope|TODOs|Verification)\*\* \|",
            discipline,
            re.MULTILINE,
        )

        self.assertEqual(len(rows), 5)
        assert_terms(
            self,
            body,
            (
                "<INHERITANCE>",
                "<FAST-TRACK>",
                "resolved Focus Record",
                "all four fields are explicit",
                "endpoint is **Execute**",
                "no material ambiguity remains",
                "resolve one material question before continuing",
                "Use this template internally",
                "Execute inline without subagents",
            ),
        )
        assert_terms(
            self,
            discipline,
            (
                "| **Focus Record** | Mandatory |",
                "| **Current plan** | Conditional |",
                "user created or approved a plan in the current context",
                "do not search for, request, or create a plan",
                "| **Execution scope** | Conditional |",
                "| **TODOs** | Conditional |",
                "two to five TODOs",
                "| **Verification** | Conditional |",
                "smallest relevant check",
                "**Not verified**",
            ),
        )
        self.assertNotIn("Contract: [outcome]", body)
        self.assertNotIn("## Gate Repository Pattern Context", body)

    def test_executes_with_minimal_test_recovery_and_completion_evidence(self):
        body = skill_body("nerd-execute")
        assert_terms(
            self,
            body,
            (
                "write or update one focused test",
                "confirm the expected failure",
                "implement the minimum change",
                "pre-edit baseline only when",
                "two evidence-driven correction attempts",
                "Do not claim a check passed without fresh output",
                "**Done:**",
                "**Verified by:**",
                "**Not verified**",
            ),
        )

    def test_uses_exactly_ten_optional_generic_proof_mappings(self):
        body = skill_body("nerd-execute")
        mapping = body.split("## Generic Mappings", 1)[1].split(
            "## Execution Discipline", 1
        )[0]
        rows = re.findall(r"^\| \*\*[0-9]+\*\* \|", mapping, re.MULTILINE)

        self.assertEqual(len(rows), 10)
        assert_terms(
            self,
            mapping,
            (
                "New behavior",
                "Bug fix",
                "Refactor",
                "API or contract",
                "Persistence or schema",
                "UI behavior",
                "Configuration or build",
                "External integration",
                "Performance or concurrency",
                "Documentation or static artifact",
            ),
        )
        self.assertIn("Use a mapping only when", body)
        self.assertNotIn("always match", body.casefold())
        self.assertNotIn("Generic Micro-Task Execution Mapping", body)

    def test_removes_obsolete_execute_lifecycle_and_reference_loading(self):
        body = skill_body("nerd-execute")
        for obsolete in (
            "**Build Contract**",
            "**Build Baseline**",
            "**Repository Gravity**",
            "**Build Milestone**",
            "**Build Checkpoint**",
            "references/plan-execution.md",
            "references/test-first-build.md",
            "references/verification.md",
        ):
            self.assertNotIn(obsolete, body)
        self.assertNotIn("superpowers:", body.casefold())

    def test_metadata_describes_the_fast_track_without_mandating_patterns(self):
        metadata = (SKILLS / "nerd-execute" / "agents" / "openai.yaml").read_text()
        self.assertIn(
            'short_description: "Fast execution from a resolved focus record"',
            metadata,
        )
        self.assertIn("$nerd-execute", metadata)
        self.assertIn("resolved Focus Record", metadata)
        self.assertIn("proportionate scope, TODOs, and verification", metadata)
        self.assertNotIn("against repository patterns", metadata)


class SilentContractTests(unittest.TestCase):
    def test_activation_and_economist_role_are_explicit(self):
        body = skill_body("nerd-silent")
        assert_terms(
            self,
            body,
            (
                "Act as the Economist",
                "final only",
                "code only",
                "findings only",
                "minimal output",
                "Do not activate from vague words",
            ),
        )

    def test_suppresses_narration_without_reducing_final_result(self):
        body = skill_body("nerd-silent")
        assert_terms(
            self,
            body,
            (
                "Hard Narration Suppression",
                "**Silent Clarification**",
                "**Silent Approval**",
                "**Silent Conflict**",
                "**Silent Blocker**",
                "**Decision Checkpoint**",
                "**Milestone Plan**",
                "normal complete final result",
                "correctness",
                "verification",
            ),
        )


class FastContractTests(unittest.TestCase):
    def test_is_an_explicitly_composable_latency_modifier_with_accuracy_floor(self):
        body = skill_body("nerd-fast")
        metadata = (SKILLS / "nerd-fast" / "agents" / "openai.yaml").read_text()
        assert_terms(
            self,
            body,
            (
                "global modifier",
                "never a primary specialty",
                "never replaces or restarts the active workflow",
                "nerd-silent",
                "only when the user explicitly invokes both modifiers",
                "Never activate, infer, or auto-compose",
                "correctness",
                "authorization",
                "safety",
                "proof",
                "no hard total tool limit",
            ),
        )
        self.assertNotIn(
            "when both operational latency and presentation cost matter",
            body,
        )
        self.assertIn('$nerd-fast', metadata)
        self.assertIn('latency', metadata.casefold())
        self.assertNotIn("superpowers:", body.casefold())

    def test_uses_exactly_ten_ordered_gates(self):
        body = skill_body("nerd-fast")
        gates = body.split("## Gates", 1)[1].split("## Verification-Cost Gate", 1)[0]
        rows = re.findall(
            r"^\| \*\*(Inheritance|Reuse|Freshness|Need|Batch|Dependency|Escalation|Recovery|Verification cost|Stop)\*\* \|",
            gates,
            re.MULTILINE,
        )
        self.assertEqual(
            rows,
            [
                "Inheritance",
                "Reuse",
                "Freshness",
                "Need",
                "Batch",
                "Dependency",
                "Escalation",
                "Recovery",
                "Verification cost",
                "Stop",
            ],
        )

    def test_gives_concrete_batch_commands_without_platform_coupling(self):
        body = skill_body("nerd-fast")
        self.assertIn("## Concrete Command Batching", body)
        batching = body.split("## Concrete Command Batching", 1)[1].split(
            "## Verification-Cost Gate", 1
        )[0]
        assert_terms(
            self,
            batching,
            (
                "sed -n '1,160p' src/a.py; sed -n '40,120p' tests/test_a.py",
                "rg -n 'timeout|retry' src tests docs",
                "git status --short; git diff --stat; git diff --check",
                "python3 -m compileall src && pytest tests/unit -q && python3 scripts/validate.py",
                "primary-command || compatible-fallback-command",
                "Use equivalent tools",
                "Use `;` only when later operations remain useful",
                "Use `&&` when success is a prerequisite",
                "Use `||` only for intentional recovery or fallback",
                "Only chain commands when the execution tool invokes a shell interpreter",
            ),
        )

    def test_requires_recoverable_mutation_batches(self):
        body = skill_body("nerd-fast")
        assert_terms(
            self,
            body,
            (
                "Before dispatching a mutation batch",
                "idempotent, transactional, or safely recoverable",
                "keep mutations sequential and inspect state between them",
            ),
        )

    def test_prefers_targeted_edits_for_localized_mutations(self):
        body = skill_body("nerd-fast")
        assert_terms(
            self,
            body,
            (
                "Prefer a structured patch or targeted-edit primitive",
                "Do not reproduce unchanged file content",
                "Rewrite a whole file only when",
            ),
        )

    def test_dispatches_routine_authorized_tools_without_optional_preamble(self):
        body = skill_body("nerd-fast")
        assert_terms(
            self,
            body,
            (
                "For routine authorized operations, invoke the tool immediately",
                "approval, safety, a material decision, or a required progress update",
                "Silent controls overall narration and final presentation",
            ),
        )

    def test_uses_early_read_volume_gate_for_symbol_index(self):
        body = skill_body("nerd-fast")
        self.assertIn("## Read-Volume Gate", body)
        self.assertLess(body.index("## Read-Volume Gate"), body.index("## Gates"))
        gate = body.split("## Read-Volume Gate", 1)[1].split("## Gates", 1)[0]
        assert_terms(
            self,
            gate,
            (
                "At task start, before the first source read",
                "total estimated lines",
                "`x <= 200`",
                "skip `symbol_index.py`",
                "`x > 200`",
                "run `ensure` once before source reads",
                "`find` without implicit refresh",
                "Do not wait until 200 lines have already been read",
                "exact-file read or narrow text search",
                "scripts/symbol_index.py",
                "Universal Ctags is optional",
                "confirm source before mutation",
            ),
        )
        self.assertNotIn("three or more exact-symbol lookups", body)

    def test_verification_cost_gate_has_five_tiers_and_bounded_escalation(self):
        body = skill_body("nerd-fast")
        verification = body.split("## Verification-Cost Gate", 1)[1].split(
            "## Generic Operational Mappings", 1
        )[0]
        tiers = re.findall(r"^\| \*\*(V[0-4])\*\* \|", verification, re.MULTILINE)
        self.assertEqual(tiers, ["V0", "V1", "V2", "V3", "V4"])
        assert_terms(
            self,
            verification,
            (
                "lowest tier that directly supports the exact claim",
                "Any file mutation, structural refactor, or code addition requires at least V1",
                "Any behavioral completion claim after mutation requires fresh proof",
                "Do not run a full suite merely because one exists",
                "Do not rerun an unchanged passing check",
                "After two evidence-driven correction attempts",
                "narrow the claim",
                "Not verified",
            ),
        )
        triggers = verification.split("### Verification Escalation Triggers", 1)[1]
        self.assertEqual(len(re.findall(r"^- ", triggers, re.MULTILINE)), 5)

    def test_reuses_incremental_state_across_language_runtimes(self):
        body = skill_body("nerd-fast")
        verification = body.split("## Verification-Cost Gate", 1)[1].split(
            "## Generic Operational Mappings", 1
        )[0]
        self.assertIn("### Incremental and Runtime-Aware Verification", verification)
        assert_terms(
            self,
            verification,
            (
                "dependency, compiler, transpiler, test, runtime, and build caches",
                "active daemons and watch processes",
                "syntax, type, lint, compile, or AST check",
                "one test method, case, file, package, or affected component",
                "clearing caches, reinstalling dependencies, rebuilding unaffected targets",
                "recreating environments, or restarting healthy services",
                "clean builds, broad suites, or environment resets",
                "pytest tests/test_api.py::test_login",
                "vitest run path/to/api.test.ts",
                "bundle exec rspec spec/api_spec.rb:42",
                "./gradlew test --tests 'pkg.ApiTest.login'",
                "go test ./pkg/api -run '^TestLogin$'",
                "Treat commands, languages, and build systems as illustrations",
                "narrowest equivalent check supported by the active project",
            ),
        )

    def test_uses_exactly_ten_operational_mappings_and_four_waves(self):
        body = skill_body("nerd-fast")
        mapping = body.split("## Generic Operational Mappings", 1)[1].split(
            "## Execution Discipline", 1
        )[0]
        rows = re.findall(r"^\| \*\*[0-9]+\*\* \|", mapping, re.MULTILINE)
        self.assertEqual(len(rows), 10)
        assert_terms(
            self,
            mapping,
            (
                "Current context is sufficient",
                "Exact file, symbol, command, or target is named",
                "Local target is unknown",
                "Multiple targets are independent",
                "genuine dependencies",
                "approved plan",
                "Current or external information",
                "failure or contradiction",
                "Verification is expensive",
                "earlier turn or retry",
            ),
        )
        discipline = body.split("## Execution Discipline", 1)[1]
        record_fields = re.findall(
            r"^\| \*\*(Recipe|Known|Unknown|Next batch|Proof|Stop)\*\* \|",
            discipline,
            re.MULTILINE,
        )
        self.assertEqual(
            record_fields,
            ["Recipe", "Known", "Unknown", "Next batch", "Proof", "Stop"],
        )
        waves = re.findall(
            r"^\| \*\*(Reuse|Discover|Execute|Prove)\*\* \|",
            discipline,
            re.MULTILINE,
        )
        self.assertEqual(waves, ["Reuse", "Discover", "Execute", "Prove"])
        assert_terms(
            self,
            discipline,
            (
                "Selected mapping",
                "Reusable current evidence",
                "One critical missing fact",
                "Independent operations to execute together",
                "Lowest sufficient fresh verification tier",
                "Exact completion condition",
            ),
        )


class FamilyContractTests(unittest.TestCase):
    def test_frontmatter_names_match_paths(self):
        for path in SKILLS.glob("*/SKILL.md"):
            match = re.search(r"^name:\s*([^\n]+)$", path.read_text(), re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1).strip(), path.parent.name)


if __name__ == "__main__":
    unittest.main()
