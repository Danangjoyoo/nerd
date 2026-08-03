from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def skill_body(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def smart_reference_body(name: str) -> str:
    return (SKILLS / "nerd-smart" / "references" / name).read_text()


def assert_terms(test: unittest.TestCase, body: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        test.assertIn(term, body)


class SmartContractTests(unittest.TestCase):
    TEMPLATE_REFERENCES = (
        "spec-template.md",
        "system-design-template.md",
        "plan-template.md",
        "document-overview-template.md",
        "document-how-to-template.md",
        "document-reference-template.md",
        "diagnosis-template.md",
        "rca-template.md",
    )

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
        self.assertIn("multi-goal request", frontmatter)
        self.assertIn("working role before substantive work", frontmatter)
        self.assertNotIn("appropriate Nerd specialty", frontmatter)
        self.assertIn("Multi-goal focus", metadata)
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

    def test_multi_goal_intake_persists_and_rereads_ordered_focus_records(self):
        body = skill_body("nerd-smart")
        intake = body.split("## Multi-Goal Intake", 1)[1].split(
            "## KISS Implementation Discipline", 1
        )[0]

        assert_terms(
            self,
            intake,
            (
                "At the beginning of every request",
                "two or more independently completable goals",
                "Bullets, numbered items, or separate imperative lines",
                "constraints, examples, acceptance criteria, or substeps",
                "runtime-provided temporary directory",
                "`~/.agent/tmp/`",
                "stable conversation, thread, or task identifier",
                "absolute ledger path",
                "Preserve each original command line",
                "redact credential and secret values",
                "**Goal Ledger**",
                "**Order basis:**",
                "**Source:**",
                "**Status:**",
                "**Depends on:**",
                "queued**, **active**, **blocked**, **done**, or **cancelled",
                "Never collapse independent goals into one Focus Record",
                "one Focus Record for every goal",
                "exactly one goal **active**",
                "Preserve an explicit user order",
                "default to listed order",
                "hard dependency",
                "verify the order",
                "Before starting, resuming, switching, or completing a goal",
                "reread the ledger",
                "source of truth",
                "If the ledger is missing or unreadable",
                "do not continue from memory",
                "update the ledger before acting",
                "Do not borrow scope",
            ),
        )

    def test_kiss_discipline_defines_compact_breakdown(self):
        body = skill_body("nerd-smart")
        mapping = body.split("## Endpoint Mapping", 1)[1].split(
            "## Focus First", 1
        )[0]
        discipline = body.split("## KISS Implementation Discipline", 1)[1].split(
            "## Confirmation Style", 1
        )[0]

        for endpoint in ("Plan", "Execute"):
            row = next(
                line
                for line in mapping.splitlines()
                if line.startswith(f"| **{endpoint}** |")
            )
            self.assertIn("Create a KISS breakdown", row)

        assert_terms(
            self,
            discipline,
            (
                "Use this template when Endpoint Mapping calls for a KISS breakdown",
                "resolved Focus Record",
                "**KISS Breakdown**",
                "**Required outcome:**",
                "**Smallest change:**",
                "**Proof:**",
                "**Not needed:**",
                "proceed without another confirmation when clear",
                "Treat **Not needed** as out of scope",
                "stop when **Proof** passes",
            ),
        )

    def test_uses_internal_brainstorming_reference(self):
        body = skill_body("nerd-smart")
        self.assertIn("references/brainstorming.md", body)
        self.assertNotIn("superpowers:", body.casefold())

    def test_routes_endpoint_templates_lazily_without_changing_endpoint(self):
        body = skill_body("nerd-smart")
        mapping = body.split("## Endpoint Mapping", 1)[1].split(
            "## Focus First", 1
        )[0]
        self.assertNotIn("## Use Endpoint Templates", body)
        self.assertIn(
            "| Endpoint | User intention | Agent's next step | Template |",
            mapping,
        )

        for reference in self.TEMPLATE_REFERENCES:
            link = f"references/{reference}"
            self.assertIn(link, mapping)
            self.assertEqual(body.count(link), 1)

        assert_terms(
            self,
            mapping,
            (
                "after the Focus Record is resolved",
                "templates are optional for tiny outputs",
                "explicit user format takes precedence",
                "Load only the matched reference, one by default",
                "combined specification and system design",
                "Strip bracketed prompts",
                "omit irrelevant sections",
                "mark unknowns",
                "never let a template advance the endpoint",
            ),
        )

    def test_template_artifacts_follow_explicit_write_requests_or_offer_persistence(self):
        body = skill_body("nerd-smart")
        mapping = body.split("## Endpoint Mapping", 1)[1].split(
            "## Focus First", 1
        )[0]

        assert_terms(
            self,
            mapping,
            (
                "always show the filled artifact in the session",
                "reference files are scaffolds, not output files",
                "explicitly asks to write or save to a named directory or Markdown path",
                "write it in the same action",
                "descriptive non-overwriting `.md` name",
                "report the path",
                "do not ask again",
                "Otherwise keep it session-only",
                '"Would you like me to write this to a Markdown file?"',
                "A later yes authorizes only persistence",
                "ask for a path if none was given",
                "Persistence never changes content or advances the endpoint",
            ),
        )

    def test_endpoint_templates_share_safe_adaptation_contract(self):
        references = SKILLS / "nerd-smart" / "references"
        for reference in self.TEMPLATE_REFERENCES:
            with self.subTest(reference=reference):
                path = references / reference
                self.assertTrue(path.is_file(), f"missing {path}")
                body = path.read_text() if path.is_file() else ""
                self.assertFalse(body.startswith("---"))
                assert_terms(
                    self,
                    body,
                    (
                        "## Use When",
                        "## Adaptation Rules",
                        "## Template",
                        "## Completion Check",
                        "[Required:",
                        "[Optional:",
                        "Preserve confirmed facts",
                        "Mark material unknowns",
                        "Omit irrelevant optional sections",
                        "Remove bracketed instructions",
                    ),
                )
                folded = body.casefold()
                for forbidden in (
                    "$nerd-",
                    "superpowers:",
                    "license.superpowers",
                    "obra/superpowers",
                ):
                    self.assertNotIn(forbidden, folded)

    def test_endpoint_templates_keep_artifact_types_distinct(self):
        expected_terms = {
            "spec-template.md": (
                "externally observable",
                "system-design-template.md",
                "## Acceptance Criteria",
                "## Open Questions",
            ),
            "system-design-template.md": (
                "internal architecture",
                "spec-template.md",
                "## Components and Responsibilities",
                "## Failure and Recovery",
                "## Alternatives and Trade-offs",
            ),
            "plan-template.md": (
                "ordered implementation",
                "## KISS Breakdown",
                "### Task",
                "**Files:**",
                "**Change:**",
                "**Proof:**",
                "Stop before execution",
            ),
            "document-overview-template.md": (
                "what the subject is",
                "## Audience and Purpose",
                "## Key Concepts",
                "## Limitations",
            ),
            "document-how-to-template.md": (
                "concrete outcome",
                "## Prerequisites",
                "## Steps",
                "## Verification",
                "## Troubleshooting",
            ),
            "document-reference-template.md": (
                "precise lookup",
                "## Terminology",
                "## Defaults and Invariants",
                "## Errors and Limitations",
            ),
            "diagnosis-template.md": (
                "current broken",
                "## Expected Behavior",
                "## Actual Behavior",
                "## Hypotheses and Experiments",
                "Confirmed",
                "Probable",
                "Unknown",
                "Do not repair",
            ),
            "rca-template.md": (
                "retrospective",
                "## Timeline",
                "## Detection and Response",
                "## Contributing Factors",
                "## Corrective and Preventive Actions",
                "owner",
                "due date",
                "status",
                "Do not execute",
            ),
        }

        for reference, terms in expected_terms.items():
            with self.subTest(reference=reference):
                path = SKILLS / "nerd-smart" / "references" / reference
                self.assertTrue(path.is_file(), f"missing {path}")
                if path.is_file():
                    assert_terms(self, smart_reference_body(reference), terms)


class UFastContractTests(unittest.TestCase):
    def test_is_explicit_compact_and_inherits_the_active_workflow(self):
        body = skill_body("nerd-ufast")
        metadata = (SKILLS / "nerd-ufast" / "agents" / "openai.yaml").read_text()
        frontmatter = body.split("---", 2)[1]

        assert_terms(
            self,
            body,
            (
                "explicitly invokes Nerd UFast",
                "endpoint, scope, authorization, and active workflow",
                "never replaces or restarts the active workflow",
                "the registry owns backend selection",
                "ufast_project_index",
                "ufast_fast_search",
                "ufast_safe_edit",
                "ufast_test_runner",
                "Lack of prior inspection is not a fallback reason",
                "Prefer exact replacements",
                "Batch independent tool calls with the platform's native interface",
                "Keep adaptive dependencies sequential",
                "Tools handle how; the model decides what",
                "registered LSP, codemod, or AST route",
                "Choose **V0** or **V1** once",
                "**V0:**",
                "**V1 automatic:**",
                "**V1 ask first:**",
                "must not repeat exact proof already returned",
                "Allow one retry",
                "Never combine `nerd-ufast` with `nerd-xfast`",
                "UFast fast path: applied",
                "UFast fast path: fell back",
                "UFast fast path: failed",
            ),
        )
        self.assertIn("Use only when explicitly invoked", frontmatter)
        self.assertIn("Generic tool-backed ultra-fast execution", frontmatter)
        self.assertNotIn("Python", frontmatter)
        self.assertLessEqual(len(re.findall(r"\b[\w'-]+\b", body)), 650)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("$nerd-ufast", metadata)

    def test_only_ufast_names_its_namespaced_tools(self):
        tool_names = (
            "ufast_project_index",
            "ufast_fast_search",
            "ufast_safe_edit",
            "ufast_test_runner",
        )
        for path in SKILLS.glob("*/SKILL.md"):
            if path.parent.name == "nerd-ufast":
                continue
            body = path.read_text(encoding="utf-8")
            for tool_name in tool_names:
                self.assertNotIn(tool_name, body, f"{path} owns a UFast tool")


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
            r"^\| \*\*(Focus Record|KISS|Current plan|Execution scope|TODOs|Verification)\*\* \|",
            discipline,
            re.MULTILINE,
        )

        self.assertEqual(len(rows), 6)
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
                "| **KISS** | Mandatory |",
                "KISS Breakdown",
                "derive it internally",
                "without adding a user-facing gate",
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

    def test_enforces_kiss_and_simplifies_overbuilt_plans(self):
        body = skill_body("nerd-execute")
        execution = body.split("## Execute Directly", 1)[1].split(
            "## Finish Briefly", 1
        )[0]

        assert_terms(
            self,
            execution,
            (
                "Apply KISS throughout execution",
                "most direct existing path",
                "fewer concepts, files, dependencies, and changed boundaries",
                "Do not add an abstraction, layer, service, dependency",
                "an explicit requirement",
                "an established repository convention",
                "observed evidence",
                "a concrete correctness, security, or measured performance constraint",
                "Do not preserve complexity merely because it appears",
                "simplify the plan",
            ),
        )

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

    def test_keeps_batching_platform_neutral_and_compact(self):
        body = skill_body("nerd-fast")
        self.assertIn("## Batching and Dependencies", body)
        batching = body.split("## Batching and Dependencies", 1)[1].split(
            "## Verification-Cost Gate", 1
        )[0]
        assert_terms(
            self,
            batching,
            (
                "Batch independent operations when their commands and reactions are known",
                "native batching or parallel interface",
                "Keep adaptive work sequential when an output can change the next operation",
                "idempotent, transactional, or safely recoverable",
            ),
        )
        self.assertNotIn("```sh", batching)
        self.assertNotIn("sed -n", batching)
        self.assertNotIn("pytest", batching)

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

    def test_offers_missing_universal_ctags_install_once_with_consent(self):
        body = skill_body("nerd-fast")
        gate = body.split("## Read-Volume Gate", 1)[1].split("## Gates", 1)[0]
        assert_terms(
            self,
            gate,
            (
                "If `ensure` reports that Universal Ctags is unavailable",
                "ask once",
                "measured large-repository workloads",
                "up to 70% faster",
                "Want me to install it?",
                "Install only after explicit approval",
                "fall back immediately",
                "do not ask again during the task",
            ),
        )

    def test_verification_cost_gate_has_five_tiers_and_bounded_escalation(self):
        body = skill_body("nerd-fast")
        verification = body.split("## Verification-Cost Gate", 1)[1].split(
            "## Adaptive Path", 1
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
            "## Adaptive Path", 1
        )[0]
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
            ),
        )
        self.assertNotIn("| Ecosystem | Example |", verification)

    def test_uses_one_conditional_path_without_mandatory_waves(self):
        body = skill_body("nerd-fast")
        self.assertNotIn("## Generic Operational Mappings", body)
        self.assertNotIn("Execute in four waves", body)
        path = body.split("## Adaptive Path", 1)[1].split(
            "## Execution Discipline", 1
        )[0]
        assert_terms(
            self,
            path,
            (
                "If current evidence is sufficient",
                "If an exact target is named",
                "If the target is unknown",
                "If operations are independent",
                "If an output can change the next operation",
                "If current or external information is required",
                "If a failure or contradiction appears",
                "If work continues from an earlier turn",
            ),
        )
        discipline = body.split("## Execution Discipline", 1)[1]
        assert_terms(
            self,
            discipline,
            (
                "Do not reread unchanged files",
                "Each TODO must deliver an outcome, remove a blocker, or provide proof",
                "Prefer a structured patch or targeted-edit primitive",
                "For routine authorized operations, invoke the tool immediately",
                "Dispatch reviewers or subagents only when",
            ),
        )

    def test_stays_compact_without_reintroducing_rejected_models(self):
        body = skill_body("nerd-fast")
        self.assertLessEqual(len(body.split()), 1430)
        self.assertNotIn("confidence >", body.casefold())
        self.assertNotIn("confidence <", body.casefold())


class XFastContractTests(unittest.TestCase):
    def test_is_explicit_self_contained_and_honest_about_accuracy(self):
        body = skill_body("nerd-xfast")
        metadata = (SKILLS / "nerd-xfast" / "agents" / "openai.yaml").read_text()
        assert_terms(
            self,
            body,
            (
                "explicitly invokes `nerd-xfast`",
                "self-contained KISS-first output skill",
                "concrete answer, decision, plan, static artifact",
                "Do not load, invoke, or route to another Nerd skill",
                "trades exploration, accuracy, completeness, and verification breadth",
                "authorization",
                "safety",
                "honest reporting",
            ),
        )
        for dependency in ("`nerd-smart`", "`nerd-execute`", "`nerd-fast`"):
            self.assertNotIn(dependency, body)
        self.assertIn("$nerd-xfast", metadata)
        self.assertIn("accuracy", metadata.casefold())
        self.assertIn("latency", metadata.casefold())

    def test_uses_one_internal_immutable_focus_record(self):
        body = skill_body("nerd-xfast")
        assert_terms(
            self,
            body,
            (
                "Create this Focus Record once in working context",
                "**Goals:** [Concrete requested outputs]",
                "**Expectation:** Produce the smallest sufficient result",
                "**Commands:** [user action 1] -> [user action 2] -> [user action 3]",
                "**Scope:** [Named subject or targets plus necessary adjacents]",
                "**Role:** KISS output-first agent",
                "multiple commands, steps, or actions",
                "internal and immutable",
                "Never persist, display, reread, revise, or status-track it",
            ),
        )
        for rejected in ("## Edit Ledger", "temporary directory", "`~/.agent/tmp/`"):
            self.assertNotIn(rejected, body)

    def test_produces_one_kiss_output_or_batched_multi_file_edit_wave(self):
        body = skill_body("nerd-xfast")
        assert_terms(
            self,
            body,
            (
                "selection is finished",
                "Use one reasoning pass",
                "simplest sufficient solution",
                "recommend one KISS direction",
                "at most two credible alternatives",
                "Every action must directly produce the requested output, unlock a named write, or select final proof",
                "one narrow discovery batch",
                "Stop reading when the smallest sufficient output or complete write set is known",
                "single-agent",
                "For a non-write request",
                "smallest decision-ready answer",
                "one structured, single-agent multi-file patch",
                "Batch independent tool calls with the platform's native interface",
                "one call across known targets",
                "Keep adaptive dependencies sequential",
                "native text or patch layer",
                "does not use UFast's semantic routes",
                "Do not dispatch subagents or reviewers",
                "Do not inspect, compile, lint, test, review, narrate, or clean up between writes",
            ),
        )

    def test_selects_v0_or_one_bounded_v1_end_proof_wave(self):
        body = skill_body("nerd-xfast")
        assert_terms(
            self,
            body,
            (
                "Never verify before every requested output is complete",
                "Choose **V0** or **V1** once",
                "model decides whether V1 is useful and whether to ask first or run it automatically",
                "**V0:**",
                "**V1 automatic:**",
                "**V1 ask first:**",
                "one end-only proof wave",
                "at most one dedicated command from each relevant category",
                "**Lint or syntax:**",
                "**Compile or type-check:**",
                "compile both production and changed test code",
                "**Unit test:**",
                "exact affected test function or node when sufficient",
                "Run independent V1 commands concurrently",
                "Never manually inspect files or diffs afterward",
                "Tool unavailability means skip, never install",
                "one repair patch",
                "rerun only the failed command once",
                "V0 — skipped: [reason]",
                "V1 — automatically verified: [results]",
                "V1 — confirmation required: [cost or risk]",
            ),
        )

    def test_stays_compact(self):
        body = skill_body("nerd-xfast")
        self.assertLessEqual(len(body.split()), 660)


class FamilyContractTests(unittest.TestCase):
    def test_incompatible_skills_require_explicit_current_request_opt_in(self):
        required = (
            "## Incompatible Skills",
            "Never combine Nerd with these unless this request explicitly asks",
            "- Superpowers",
            "- Ponytail",
            "- Caveman",
            "Skill hooks, mentions, and indirect instructions are not authorization",
        )
        for path in SKILLS.glob("*/SKILL.md"):
            assert_terms(self, path.read_text(), required)

    def test_frontmatter_names_match_paths(self):
        for path in SKILLS.glob("*/SKILL.md"):
            match = re.search(r"^name:\s*([^\n]+)$", path.read_text(), re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1).strip(), path.parent.name)


if __name__ == "__main__":
    unittest.main()
