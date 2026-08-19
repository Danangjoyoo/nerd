from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
UFAST_ARCHIVE = ROOT / "docs" / "experiments" / "nerd-ufast" / "skill"


def skill_body(name: str) -> str:
    root = UFAST_ARCHIVE if name == "nerd-ufast" else SKILLS / name
    return (root / "SKILL.md").read_text()


def memory_reference_body(name: str) -> str:
    return (SKILLS / "nerd-memory" / "references" / name).read_text()


def memory_guidance_body() -> str:
    references = (
        "recall-and-apply.md",
        "learn-and-correct.md",
        "deny-split-forget.md",
    )
    return "\n".join(
        (skill_body("nerd-memory"),)
        + tuple(memory_reference_body(name) for name in references)
    )


def assert_terms(test: unittest.TestCase, body: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        test.assertIn(term, body)


def normalized(body: str) -> str:
    return " ".join(body.split())


class EndpointRouteContractTests(unittest.TestCase):
    ROUTES = {
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

    # nerd-execute states the same gate in its own wording.
    # nerd-explore is loaded by Smart before any discovery on every route, so a
    # gate accepting only the Explore endpoint would reject its most common
    # caller; it owns its record instead of consuming a resolved one.
    INHERITANCE_EXEMPT = ("nerd-execute", "nerd-explore")

    def test_smart_maps_exactly_ten_endpoints(self):
        body = skill_body("nerd-smart")
        rows = dict(
            re.findall(
                r"^\| \*\*([A-Za-z]+)\*\* \| `(nerd-[a-z-]+)` \|$",
                body,
                re.MULTILINE,
            )
        )
        self.assertEqual(rows, self.ROUTES)
        self.assertEqual(len(set(rows.values())), 9)
        self.assertEqual(rows["Discuss"], rows["Ideate"])
        assert_terms(
            self,
            body,
            (
                "Choose exactly one route",
                "The route owns the deliverable, mutation authority",
                "hand the resolved record to the matched route",
                "Never keep endpoint workflows or templates in Smart",
            ),
        )

    def test_smart_explore_discipline_defers_to_the_explore_route(self):
        body = normalized(skill_body("nerd-smart"))
        assert_terms(
            self,
            body,
            (
                "## Explore Discipline",
                "- Load and read the `nerd-explore` skill first",
                "then follow its exploration discipline",
                "Never run an exploration loop inside Smart",
                "Keep alignment reads minimal",
                "Resolve the endpoint as **Explore** and hand the record to `nerd-explore`",
            ),
        )
        self.assertLess(
            body.index("## Explore Discipline"),
            body.index("## Endpoint Mapping"),
        )
        self.assertLess(
            body.index("## Multi-Goal Intake"),
            body.index("## Explore Discipline"),
        )

    def test_brainstorm_owns_discuss_and_ideate_without_mutation(self):
        body = normalized(skill_body("nerd-brainstorm"))
        assert_terms(
            self,
            body,
            (
                "only the **Discuss** and **Ideate** endpoints",
                "## Focus Record",
                "## Operating Discipline",
                "## Healthy Collaboration",
                "## Discuss",
                "## Ideate",
                "### Diverge",
                "### Examine Objectively",
                "### Converge Together",
                "false balance",
                "same burden of evidence",
                "Do not claim consensus",
                "Do not create or update an artifact",
                "Confirm through Smart before changing endpoints",
            ),
        )

    def test_smart_is_alignment_only(self):
        body = skill_body("nerd-smart")
        references = SKILLS / "nerd-smart" / "references"
        self.assertEqual(
            {path.name for path in references.glob("*.md")},
            {"multi-goal-ledger.md"},
        )
        for forbidden in (
            "## Plan and Execute Delivery",
            "references/brainstorming.md",
            "references/plan-template.md",
            "references/diagnosis-template.md",
        ):
            self.assertNotIn(forbidden, body)

    def test_routes_require_their_exact_resolved_endpoint(self):
        for endpoint, skill in self.ROUTES.items():
            with self.subTest(endpoint=endpoint):
                body = skill_body(skill)
                if skill not in self.INHERITANCE_EXEMPT:
                    expected_endpoint = (
                        "only the **Discuss** and **Ideate** endpoints"
                        if skill == "nerd-brainstorm"
                        else f"only the **{endpoint}** endpoint"
                    )
                    assert_terms(
                        self,
                        body,
                        (
                            "Use `nerd-smart` first",
                            expected_endpoint,
                            "return to Smart before continuing",
                        ),
                    )

    def test_explore_owns_its_record_without_inheriting_smart(self):
        body = skill_body("nerd-explore")
        assert_terms(
            self,
            body,
            (
                "Explore owns its own record",
                "> - **Question:**",
                "> - **Boundary:**",
                "Confirm any endpoint change through `nerd-smart`",
            ),
        )
        for forbidden in (
            "<INHERITANCE>",
            "Use `nerd-smart` first",
            "only the **Explore** endpoint",
        ):
            self.assertNotIn(forbidden, body)

    def test_explore_inlines_speed_without_loading_modifier_routes(self):
        body = skill_body("nerd-explore")
        assert_terms(
            self,
            body,
            (
                "## Fast Discipline",
                "Never load `nerd-fast` or `nerd-xfast`",
                "never alter the caller's analysis depth, proof, or reporting rigor",
                "Never trade accuracy for latency",
            ),
        )

    def test_route_descriptions_are_explicit_and_distinct(self):
        descriptions = {}
        for skill in set(self.ROUTES.values()):
            body = skill_body(skill)
            frontmatter = body.split("---", 2)[1]
            match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
            self.assertIsNotNone(match)
            descriptions[skill] = match.group(1)
        self.assertEqual(len(set(descriptions.values())), len(descriptions))

    def test_read_only_routes_forbid_mutation(self):
        expected = {
            "nerd-brainstorm": "Do not create or update an artifact",
            "nerd-explore": "Do not modify files or external state",
            "nerd-diagnose": "Do not repair, edit, or execute corrective actions",
            "nerd-review": "Do not modify the reviewed artifact",
            "nerd-spec": "Do not turn it into implementation steps",
            "nerd-plan": "Stop before execution",
            "nerd-monitor": "Do not modify the observed process or external state",
        }
        for skill, term in expected.items():
            with self.subTest(skill=skill):
                self.assertIn(term, skill_body(skill))

    def test_route_reference_ownership_is_endpoint_local(self):
        expected = {
            "nerd-smart": {"multi-goal-ledger.md"},
            "nerd-brainstorm": {"brainstorming.md"},
            "nerd-diagnose": {"diagnosis-template.md", "rca-template.md"},
            "nerd-spec": {"spec-template.md", "system-design-template.md"},
            "nerd-document": {
                "document-overview-template.md",
                "document-how-to-template.md",
                "document-reference-template.md",
            },
            "nerd-plan": {
                "plan-template.md",
                "principle-selection.md",
                "comprehensive.md",
                "dry.md",
                "kiss.md",
                "yagni.md",
            },
        }
        for skill, references in expected.items():
            root = SKILLS / skill / "references"
            with self.subTest(skill=skill):
                self.assertEqual(
                    {path.name for path in root.glob("*.md")},
                    references,
                )

    def test_template_routes_preserve_artifact_boundaries(self):
        assert_terms(
            self,
            skill_body("nerd-diagnose"),
            ("Load only the matched template", "Persist an artifact only when"),
        )
        assert_terms(
            self,
            skill_body("nerd-spec"),
            ("Load only the matched template", "Persist an artifact only"),
        )
        assert_terms(
            self,
            skill_body("nerd-document"),
            ("Choose one matched template", "Validate the artifact"),
        )
        assert_terms(
            self,
            skill_body("nerd-plan"),
            (
                "implementation plan template",
                "self-review the finished artifact with `nerd-review` checkpoints",
                "Stop before execution",
            ),
        )

    def test_plan_persistence_depends_on_invocation_source(self):
        body = normalized(skill_body("nerd-plan"))
        assert_terms(
            self,
            body,
            (
                "Always save Markdown",
                "Smart route: runtime temp directory",
                "`/tmp`",
                "`~/.agent/tmp/`",
                "Direct user invocation",
                "`./docs/plans/`",
                "Direct stays direct after Smart resolves Focus",
                "show the path",
            ),
        )

    def test_plan_requires_direction_and_evidence_before_planning(self):
        body = normalized(skill_body("nerd-plan"))
        assert_terms(
            self,
            body,
            (
                "## Evidence Prerequisites",
                "Plan collaboratively",
                "| Plan needs | Collaborate with | Bring back |",
                "`nerd-brainstorm` through **Ideate**",
                "`nerd-explore` through **Explore**",
                "`nerd-diagnose` with `nerd-surgery` through **Diagnose**",
                "Use every prerequisite skill the work genuinely needs",
                "one resolved endpoint at a time",
                "Reuse current handoffs",
                "resume **Plan** through `nerd-smart`",
            ),
        )

    def test_plan_enforces_focus_tdd_tdg_and_safe_parallel_integration(self):
        raw_body = skill_body("nerd-plan")
        body = normalized(raw_body)
        template = normalized(
            (SKILLS / "nerd-plan" / "references" / "plan-template.md").read_text()
        )
        assert_terms(
            self,
            body,
            (
                "Copy the Focus Record",
                "Goal Ledger",
                "Testable work: red, green, refactor",
                "Task Dependency Graph (TDG)",
                "pair one compact task/dependency/wave table with a Mermaid `flowchart LR`",
                "Show sequential edges, parallel fan-out, and synchronization fan-in",
                "Omit the diagram only for a single task",
                "Unless the user requires sequential work",
                "Subagents need disjoint ownership",
                "one worktree and branch per node",
                "Push only with explicit authority",
                "one branch at a time in TDG order",
                "cannot guarantee conflict-free or correct integration",
                "Do not execute them",
            ),
        )
        self.assertIn("| Discipline | Rule |", raw_body)
        assert_terms(
            self,
            template,
            (
                "## Summary",
                "## Task Dependency Graph (TDG)",
                "| Task | Wave | Depends on | Produces |",
                "```mermaid",
                "flowchart LR",
                'task1["Wave 1: T1 Contract"]',
                'task2["Wave 2: T2 Runtime"]',
                'task3["Wave 2: T3 Docs"]',
                "task1 --> task2",
                "task1 --> task3",
                "task2 --> task4",
                "task3 --> task4",
                "Sibling nodes in one wave show parallel work",
                "child waits for every parent",
                "## Ordered Work",
                "**Focus:**",
                "**Interfaces:**",
                "| Action | Path |",
                "| Direction | Contract |",
                "| Consumes |",
                "| Produces |",
                "Write the failing test",
                "Run the test and confirm failure",
                "Implement the minimum change",
                "Run focused and regression proof",
                "| Check | Command | Expected |",
                "| ID | Criterion | Evidence |",
                "## Self Review",
                "| Checkpoint | Nerd Review lens | Evidence question | Status |",
                "Level 1 — concrete defects",
                "Level 2 — consistency and proof",
                "Level 3 — harmful complexity",
                "| Concern | Requirement |",
                "Require explicit authorization before any planned remote push",
            ),
        )
        self.assertLess(
            template.index("## Self Review"), template.index("## Final Validation")
        )

    def test_plan_delivery_is_a_compact_decision_table(self):
        body = skill_body("nerd-plan")
        assert_terms(
            self,
            body,
            (
                "| Principle | Use when | Action |",
                "| **KISS** | Default |",
                "| **Comprehensive** |",
                "| **DRY** |",
                "| **Selection** |",
                "| **Rationale** |",
            ),
        )

    def test_specialties_compose_without_owning_endpoints(self):
        assert_terms(
            self,
            skill_body("nerd-surgery"),
            ("nerd-diagnose", "nerd-execute", "never an endpoint owner"),
        )
        assert_terms(
            self,
            skill_body("nerd-patrol"),
            ("nerd-review", "nerd-execute", "never owns an endpoint"),
        )
        execute = skill_body("nerd-execute")
        self.assertIn("sole owner of the **Execute** endpoint", execute)

    def test_every_route_metadata_names_the_skill(self):
        for skill in self.ROUTES.values():
            path = SKILLS / skill / "agents" / "openai.yaml"
            with self.subTest(skill=skill):
                self.assertIn(f"$" + skill, path.read_text(encoding="utf-8"))


class ReviewContractTests(unittest.TestCase):
    def test_maps_exactly_two_review_types(self):
        body = skill_body("nerd-review")
        section = body.split("## Review Types", 1)[1].split("## Discipline", 1)[0]
        rows = re.findall(
            r"^\| \*\*(Plain|Pull request review)\*\* \|",
            section,
            re.MULTILINE,
        )
        self.assertEqual(rows, ["Plain", "Pull request review"])
        assert_terms(
            self,
            section,
            (
                "Choose exactly one",
                "requested PR, diff, branch, or commit",
                "named artifact/current state plus necessary context",
                "base-to-head delta",
                "only issues introduced or materially worsened by it",
            ),
        )

    def test_patrol_requires_evidence_for_deeper_security_review(self):
        body = skill_body("nerd-review")
        assert_terms(
            self,
            body,
            (
                "Do not auto-route to `nerd-patrol`",
                "only when evidence warrants deeper",
                "security, vulnerability, unsafe-behavior, or exploitability review",
                "preserve Review and never remediate",
            ),
        )

    def test_review_guidance_stays_compact_and_bulleted(self):
        skill = skill_body("nerd-review")
        self.assertLessEqual(len(skill.splitlines()), 125)

        references = SKILLS / "nerd-review" / "references"
        for path in references.rglob("*.md"):
            with self.subTest(reference=path.relative_to(references)):
                body = path.read_text(encoding="utf-8")
                self.assertLessEqual(len(body.splitlines()), 18)
                for label in (
                    "- **Use:**",
                    "- **Level 1:**",
                    "- **Level 2:**",
                    "- **Level 3:**",
                    "- **Proof:**",
                    "- **Escalate:**",
                    "- **Avoid:**",
                ):
                    self.assertIn(label, body)

    def test_stack_and_framework_mappings_match_diagnose(self):
        def mapped_references(skill: str) -> set[str]:
            return set(
                re.findall(
                    r"\(references/((?:stacks|frameworks)/[^)]+\.md)\)",
                    skill_body(skill),
                )
            )

        self.assertEqual(
            mapped_references("nerd-review"),
            mapped_references("nerd-diagnose"),
        )

    def test_separates_three_review_levels_from_severity(self):
        body = skill_body("nerd-review")
        assert_terms(
            self,
            body,
            (
                "## Review Levels",
                "Syntax, compilation or type failure, and concrete code smells",
                "Repository consistency, test coverage, and documentation",
                "Bad architecture, harmful complexity, and design-pattern violations",
                "A level identifies the review lens, not impact",
                "Assign severity from impact and reachability, independently of review level",
                "Critical",
                "High",
                "Medium",
                "Low",
            ),
        )

    def test_requires_focus_mapping_evidence_and_findings_first(self):
        body = skill_body("nerd-review")
        assert_terms(
            self,
            body,
            (
                "**Focus Record**",
                "**Stack mapping**",
                "Prove reachability, trigger, impact, and blast radius",
                "report only findings that survive an adversarial evidence check",
                "Location: <path:line or smallest exact scope>",
                "Review level: <Level 1 | Level 2 | Level 3>",
                "Put findings first",
                "Do not modify the reviewed artifact",
            ),
        )


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
            normalized(body),
            (
                "resolved Focus Record",
                "intention, endpoint, and scope are explicit",
                "endpoint is **Diagnose** or **Execute**",
                "Role is required only when it changes the approach",
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
            r"^\| \*\*(Focus Record|Delivery|Current plan|Execution scope|TODOs|Verification)\*\* \|",
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
                "intention, endpoint, and mutation scope are explicit",
                "endpoint is **Execute**",
                "no material ambiguity remains",
                "Role is required only when it changes the approach",
                "resolve one material question before continuing",
                "Use this template internally",
                "Execute directly",
                "use bounded parallel work only for independent subtasks",
                "retain responsibility for integration",
            ),
        )
        assert_terms(
            self,
            discipline,
            (
                "| **Focus Record** | Mandatory |",
                "Obey Role when present; its omission never blocks clear work",
                "| **Delivery** | Mandatory |",
                "Apply KISS inline",
                "crosses a module or service boundary",
                "three maintained copies",
                "Keep the breakdown internal unless a handoff or decision requires it",
                "| **Current plan** | Conditional |",
                "user created or approved a plan in the current context",
                "do not search for, request, or create a plan",
                "| **Execution scope** | Conditional |",
                "| **TODOs** | Conditional |",
                "two to five TODOs",
                "| **Verification** | Conditional |",
                "proof suited to the affected behavior and risk",
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
            normalized(execution),
            (
                "Apply KISS throughout execution",
                "Cover cross-boundary completeness and proven",
                "duplication only at the thresholds in the Delivery rule",
                "Defer speculative surface as part of KISS",
                "clearest direct existing path",
                "fewer concepts, dependencies, and new boundaries",
                "when they do not reduce correctness or maintainability",
                "Do not add an abstraction, layer, service, dependency",
                "an explicit requirement",
                "an established repository convention",
                "observed evidence",
                "a concrete correctness, security, or measured performance constraint",
                "Do not preserve complexity merely because it appears",
                "simplify the plan",
                "including adjacent callers, callees, configuration, and dependencies when relevant",
                "Read-only evidence gathering does not expand the mutation boundary",
            ),
        )

    def test_executes_with_risk_suited_proof_and_evidence_driven_recovery(self):
        body = skill_body("nerd-execute")
        assert_terms(
            self,
            body,
            (
                "start with a focused test",
                "confirm the expected failure",
                "implement the simplest sufficient change",
                "Add affected integration or risk checks when credible proof requires them",
                "run validation suited to the change",
                "pre-edit baseline only when",
                "record what the evidence disproved",
                "choose the next discriminating check or correction",
                "Stop only at a real blocker",
                "no viable in-scope path remains",
                "required authority or access is missing",
                "Never stop merely because an attempt count was reached",
                "Do not claim a check passed without fresh output",
                "**Done:**",
                "**Verified by:**",
                "**Not verified**",
            ),
        )
        self.assertNotIn("at most two evidence-driven correction attempts", body)

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
                "Do not talk before acting, expose thinking, or narrate reasoning",
                "Emit only requested outputs and the required Finish lines",
                "simplest sufficient solution",
                "recommend one KISS direction",
                "at most two credible alternatives",
                "Every action must directly produce the requested output, unlock a named write, or select final proof",
                "one narrow discovery batch",
                "Stop reading when the smallest sufficient output or complete write set is known",
                "Batch tooling",
                "`rg ... && rg ...`",
                "`grep ... && grep ...`",
                "minimum fact → maximum output → immediate write",
                "reuse fact → immediate write",
                "Never rediscover a sufficient fact",
                "single-agent",
                "For a non-write request",
                "smallest decision-ready answer",
                "one structured, single-agent multi-file patch",
                "Do not dispatch subagents or reviewers",
                "Do not inspect, compile, lint, test, review, narrate, or clean up between writes",
            ),
        )

    def test_stays_silent_scope_bound_and_goal_persistent(self):
        body = skill_body("nerd-xfast")
        assert_terms(
            self,
            body,
            (
                "Act only within the authorized Scope and toward the recorded Goals",
                "Never expand scope, invent goals, or take unrelated action",
                "If any Goal remains unmet, immediately take the next authorized action",
                "Continue without pausing for commentary or confirmation",
                "until every Goal is reached",
                "a real authorization or safety blocker requires the user",
            ),
        )
        self.assertNotIn("Use one reasoning pass", body)

    def test_uses_only_point_or_table_based_rules(self):
        body = skill_body("nerd-xfast")
        markdown = body.split("---", 2)[2]
        prose = [
            line
            for line in markdown.splitlines()
            if line.strip()
            and not line.lstrip().startswith(("#", "-", "|", ">"))
        ]
        self.assertEqual(prose, [])
        self.assertIn("| Rule | Requirement |", markdown)
        self.assertIn("| Request | Action |", markdown)
        self.assertIn("| Mode | Use |", markdown)

    def test_lists_common_batch_tools_and_sed_example(self):
        body = skill_body("nerd-xfast")
        assert_terms(
            self,
            body,
            (
                "Use `&&` to batch related commands in one invocation",
                "later commands run only when earlier commands succeed",
                "| Tool | Use | Batch example |",
                "| `rg` |",
                "| `grep` |",
                "| `sed` |",
                "| `awk` |",
                "| `find` |",
                "| `git` |",
                "`sed -n '1,120p' file_a && sed -n '1,120p' file_b`",
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
        content_words = len(body.replace("|", " ").split())
        self.assertLessEqual(content_words, 950)


class UFastContractTests(unittest.TestCase):
    def test_has_zero_planning_action_chain(self):
        body = skill_body("nerd-ufast")
        assert_terms(
            self,
            body,
            (
                "zero-planning execution skill",
                "Do not create or maintain a Focus Record",
                "Do not narrate intended steps before acting",
                "## Zero-Planning Chain",
                "Task → Immediate action → Verify",
                "Do not restate, decompose, reinterpret, or status-track it",
                "begin the first useful action immediately",
                "one silent bounded decision pass",
                "Do not emit a plan, preamble, approach, future-tense action list",
                "Verification happens only after the requested output is complete",
            ),
        )
        self.assertNotIn("## One Focus", body)
        self.assertNotIn("**Focus Record**", body)

    def test_has_20_row_aggressive_intent_map(self):
        body = skill_body("nerd-ufast")
        section = body.split("## Aggressive Intent Mapping", 1)[1].split(
            "\n## ", 1
        )[0]
        table_lines = [line for line in section.splitlines() if line.startswith("|")]

        self.assertEqual(table_lines[0], "| Intention | Keyword | Action |")
        self.assertEqual(len(table_lines[2:]), 20)
        assert_terms(
            self,
            section,
            (
                "Read the full request",
                "A keyword is a clue, not permission",
                "Use a nearby project pattern for missing how details",
                "Do not guess a different result, target, or permission",
                "### Generic Fallback",
                "If no intention matches the table",
                "Use the plain meaning of the full request",
                "do the smallest local action",
                "Never add a new goal",
                "ask one question",
            ),
        )

    def test_has_no_explanation_output_contract(self):
        body = skill_body("nerd-ufast")
        assert_terms(
            self,
            body,
            (
                "## No Explanation Output",
                "Output only the requested result",
                "Do not explain the analysis, reason, approach, changes, files",
                "the explanation itself is the requested result",
                "Done.\nTests: pass.",
                "Done.\nTests: not run.",
                "Blocked: <short reason>.",
                "Do not add any other text",
            ),
        )
        self.assertNotIn("Report only the produced outcome", body)

    def test_has_safe_single_shot_action_contract(self):
        body = skill_body("nerd-ufast")
        section = body.split("## Single Shot Action", 1)[1].split("\n## ", 1)[0]
        table_lines = [line for line in section.splitlines() if line.startswith("|")]

        self.assertEqual(
            table_lines[0],
            "| Work | How to batch | Example commands |",
        )
        self.assertEqual(len(table_lines[2:]), 7)
        assert_terms(
            self,
            section,
            (
                "one model-to-tool round trip",
                "Use one call for known work",
                "Run dependent steps in order",
                "independent steps together",
                "Call again only when a result chooses the next action",
                "Never hide search, edits, and proof in one shell command",
                "inspect([{symbol:A},{symbol:B}])",
                "inspect([{path:a},{path:b}])",
                "apply_verify(patch,hashes,checks)",
                "sequence(edit,test)",
                "parallel(lint,typecheck,test)",
                "discover(...) → next_call",
                "ask_user()",
            ),
        )
        self.assertNotIn("### Examples", section)
        for unsafe in (
            "unified subshell payload",
            "git checkout -- .",
            "xargs sed",
            "cat <<",
        ):
            self.assertNotIn(unsafe, section)

    def test_prefers_core_mcp_tools_with_safe_fallback(self):
        body = skill_body("nerd-ufast")
        section = body.split("## Core Tools", 1)[1].split("\n## ", 1)[0]
        assert_terms(
            self,
            section,
            (
                "nerd-ufast-tools",
                "After the cache step",
                "call it once",
                "all exact symbol and bounded path queries",
                "when listed in session tools",
                "Never test availability with `command -v`, `which`, or file search",
                "If tool-list visibility is unclear, attempt the call",
                "before any `rg`, `sed`, `find`, or file-read tool",
                "Do not replace it with shell access",
                "infer unavailability from a cache-helper failure",
                "Fall back only when `inspect` is absent or its call returns an error",
                "one `apply_verify` call",
                "apply, verify, and roll back on failed proof",
                "expected hashes for every changed path",
                "For unclear targets",
                "external effects",
                "migrations",
                "existing bounded tools",
            ),
        )

    def test_trusts_existing_patterns(self):
        body = skill_body("nerd-ufast")
        assert_terms(
            self,
            body,
            (
                "## Trust Existing Patterns",
                "Copy the nearest working implementation",
                "Keep its structure, naming, dependencies, errors, and tests",
                "Change only the requested behavior",
                "do not redesign or add abstractions",
                "New endpoint: find the nearest endpoint → clone it",
            ),
        )

    def test_has_best_effort_project_intelligence_cache(self):
        body = skill_body("nerd-ufast")
        assert_terms(
            self,
            body,
            (
                "## Project Intelligence Cache",
                "~/.agent/tmp/nerd-ufast/",
                "project-map.md",
                "conventions.md",
                "commands.md",
                "dependencies.md",
                "history.md",
                "What exists",
                "How this project works",
                "How to verify",
                "Libraries and versions",
                "Confirmed reasons and warnings",
                "##@ key @##",
                "At the start of every task",
                "batch only needed exact keys",
                "before any repository search or read",
                "first project-navigation SSOT",
                "jump directly to cached paths",
                "without rediscovery",
                "A missing cache or key is a cache miss",
                "Fallback to one narrow lookup only when",
                "a cached path or command fails",
                "repository evidence conflicts",
                "project_cache.py get",
                "project_cache.py put",
                "in the background with `&`",
                "never wait",
                "locks and atomically replaces",
                "refresh only failed or conflicting keys",
                "Update only the affected key",
                "Never infer history",
                "cache secrets/file contents",
            ),
        )

    def test_stays_compact(self):
        self.assertLessEqual(len(skill_body("nerd-ufast").split()), 1000)


class MemoryContractTests(unittest.TestCase):
    def test_memory_interaction_output_is_compact(self):
        skill = normalized(skill_body("nerd-memory"))
        recall = memory_reference_body("recall-and-apply.md")
        learning = normalized(memory_reference_body("learn-and-correct.md"))
        denial = memory_reference_body("deny-split-forget.md")

        assert_terms(
            self,
            skill,
            (
                "## Interaction Output",
                "Keep Memory middleware silent",
                "exactly one paragraph",
                "`Nerd-memory memorized: <compact wording>`",
                "at most 30 words after the prefix",
                "Never print templates, contracts, schemas, raw runtime JSON",
            ),
        )
        self.assertIn("Nerd-memory proposes:", recall)
        self.assertIn("Nerd-memory proposes a split:", denial)
        self.assertIn("one compact paragraph", learning)
        self.assertNotIn("> **Memory Proposal**", recall)
        self.assertNotIn("> **Memory Split Proposal**", denial)

    def test_operational_guidance_stays_progressively_disclosed_and_compact(self):
        skill = skill_body("nerd-memory")
        workflows = {
            name: memory_reference_body(name)
            for name in (
                "recall-and-apply.md",
                "learn-and-correct.md",
                "deny-split-forget.md",
            )
        }

        self.assertLessEqual(len(skill.split()), 1000)
        self.assertLessEqual(
            len((skill + workflows["recall-and-apply.md"]).split()),
            1800,
        )
        for name, body in workflows.items():
            self.assertLessEqual(len(body.split()), 800, name)
            self.assertIn(f"references/{name}", skill)
        self.assertIn(
            "Read only the reference matching the active operation",
            normalized(skill),
        )

    def test_defines_all_seven_longitudinal_pattern_types(self):
        body = normalized(memory_guidance_body())
        assert_terms(
            self,
            body,
            (
                "| `goal` |",
                "| `task` |",
                "| `action` |",
                "| `result` |",
                "| `boundary` |",
                "| `verification` |",
                "| `routing` |",
                "independent root task episode",
                "Consolidation creates inactive candidates",
                "does not activate them",
            ),
        )

    def test_memory_influence_always_stops_at_exact_confirmation(self):
        body = normalized(memory_guidance_body())
        assert_terms(
            self,
            body,
            (
                "## Core Contract",
                "taint the whole proposal and stop before acting",
                "generated confirmation phrase from a new, direct user response",
                "trusted thread/turn reference",
                "Never invent or reuse a confirmation-event reference",
                "Silence",
                "This version has no standing-confirmation bypass",
                "Never call an executor from a pending proposal",
                "immediately consume its one-use grant",
                "memory_gate_only",
            ),
        )

    def test_endpoint_routes_every_input_or_explicitly_abstains(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "Build the Memory-Blind Baseline",
                "Every input must yield one of",
                "pending memory proposal",
                "`abstain`",
                "Never force a nearest match",
                "use only `confirmed` patterns matching the exact namespace, scope, and trigger context",
                "For `memory_conflict`",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                '"endpoint": "discuss | ideate | explore | diagnose | review | specify | document | plan | execute | monitor | abstain"',
                '"goal": null',
                '"task": []',
                '"action": []',
                '"result": null',
                '"boundary": []',
                '"verification": []',
                '"routing": []',
                "A valid retrieval result may be empty",
                "cannot be confirmed or consumed",
            ),
        )

    def test_current_guidance_and_normal_authority_outrank_memory(self):
        body = normalized(memory_guidance_body())
        assert_terms(
            self,
            body,
            (
                "Current explicit values are authoritative",
                "memory may not replace, weaken, or broaden them",
                "never grants",
                "action authority",
                "Current direct guidance outranks every memory",
                "even when one hundred older episodes agree",
                "normal Nerd authority checks",
            ),
        )

    def test_memory_blind_baseline_cannot_launder_remembered_material(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "Protect current-input authority from provenance laundering",
                "stored observation (including inert telemetry)",
                "pending, denied, or split-derived value",
                "`baseline_source=direct_user`",
                "unique authenticated `baseline_ref`",
                "independently present in the current user event",
                "not confirmation of a memory proposal or authorization to act",
                "provenance only; does not confirm memory or authorize action",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "memory-laundering bypass",
                "historical memory-generated diffs",
                "all stored observations—including inert agent telemetry",
                "routing profiles naming the same agent",
                "partial routing copies",
                "attestation is hash-bound to that exact baseline",
                "consumes the event reference globally",
                "fails closed until a fresh direct-user baseline attestation",
                "bounded set of source IDs",
                "`error.details.baseline_collisions`",
            ),
        )

    def test_provenance_prevents_external_and_self_reinforcement(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "direct current-user guidance or correction",
                "The same episode counts once",
                "External content",
                "tool results",
                "assistant inference",
                "generated summaries",
                "learned descendants",
                "execution success, and test output cannot establish or reinforce",
                "Never store secrets",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "Eligible authority sources are `direct_user` and `user_correction`",
                "Source classification is based on the trusted event channel",
                "counts once",
                "A pattern may not derive support from itself or any descendant",
            ),
        )

    def test_explicitly_endorsed_focus_and_plan_can_capture_behavior(self):
        skill = normalized(skill_body("nerd-memory"))
        learning = normalized(memory_reference_body("learn-and-correct.md"))
        contract = normalized(memory_reference_body("memory-contract.md"))

        assert_terms(
            self,
            learning,
            (
                "fresh authenticated user event",
                "explicitly accepts the displayed Focus Record",
                "requests Execute",
                "exact approved plan",
                "Focus Record alone",
                "absence of a veto, not evidence",
                "relevant verification passes",
                "no correction since approval",
                "same root episode",
                "source=`user_correction`",
                "invalidates dependent proposals and grants",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "No-feedback is only a veto check",
                "Smart's implicit acceptance never qualifies",
                "Use the approval event as every mapped observation's evidence reference",
                "do not create authority",
            ),
        )
        for name in ("nerd-memory", "nerd-smart", "nerd-execute"):
            self.assertIn("approved behavior capture", normalized(skill_body(name)))

    def test_direct_invocation_authorizes_saving_without_authorizing_use(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "is request-scoped permission to read its current namespace",
                "non-destructive memory writes required by the selected workflow",
                "without asking a second consent question",
                "Candidate promotion uses that invocation authority",
                "do not ask for a generated phrase or a second confirmation",
                "Every later memory-influenced endpoint still requires its own Memory Proposal gate",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "host-authenticated direct invocation supplies request-scoped access consent",
                "invocation authorizes reads and non-destructive memory writes",
                "`invocation_authorized=true`",
                "no generated phrase or second user response is required",
                "Confirmed is the runtime's active-for-retrieval state; it is never action authorization",
            ),
        )

    def test_runtime_activation_is_bounded_opt_in_local_and_namespaced(self):
        raw_body = skill_body("nerd-memory")
        body = normalized(raw_body)
        frontmatter = normalized(raw_body.split("---", 2)[1])
        contract = normalized(memory_reference_body("memory-contract.md"))
        metadata = normalized(
            (SKILLS / "nerd-memory" / "agents" / "openai.yaml").read_text()
        )
        assert_terms(
            self,
            body,
            (
                "python3 <skill-root>/scripts/memory.py",
                "Load Nerd Memory from a host-authenticated direct-user skill invocation",
                "`$nerd-memory` in Codex or `/nerd-memory` in Claude Code and Cursor",
                "or from a Nerd Smart auto-enable",
                "A plain natural-language mention outside these paths is not activation",
                "Without active invocation, do not read operational references",
                "Retained skill text is not a new invocation",
                "start a fresh session when physical context removal is required",
                "`enabled` records local persistence state only",
                "it is never standing permission to access Memory",
                "Never search another namespace",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "local SQLite",
                "uses the Python standard library",
                "host-authenticated direct invocation supplies request-scoped access consent",
                "unless the current direct user event invoked `$nerd-memory` in Codex or `/nerd-memory` in Claude Code or Cursor",
                "calls `enable` with the authenticated invocation-event reference",
                "without asking a second consent question",
                "A plain natural-language mention is not activation",
                "later requests require a new explicit invocation",
                "Memory persists enablement per namespace",
                "Namespace equality is exact",
                "Every successful command writes one JSON value to stdout",
                "A prompt-only simulation does not satisfy this contract",
            ),
        )
        self.assertIn("allow_implicit_invocation: true", metadata)
        self.assertIn("$nerd-memory", metadata)
        self.assertIn("user invokes $nerd-memory (Codex)", frontmatter)
        self.assertIn("/nerd-memory (Claude/Cursor)", frontmatter)
        self.assertIn("or when Nerd Smart auto-enables it", frontmatter)
        self.assertNotIn("disable-model-invocation", frontmatter)
        self.assertNotIn("when Nerd Memory is enabled", frontmatter)

    def test_schema_upgrades_fence_already_open_older_runtimes(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "close and recreate every long-lived `MemoryStore`",
                "never retry a proposal or action through the stale handle",
                "database rejects stale writers",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "Persistent `INSERT`, `UPDATE`, and `DELETE` triggers",
                "connection-local runtime-version function",
                "pre-upgrade connection either lacks that function or reports the older version",
                "stop-and-restart operations",
                "no stale proposal, confirmation, consumption, split, or memory mutation may proceed",
            ),
        )

    def test_conflict_revision_and_forget_invalidate_pending_authority(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "A direct correction immediately contests",
                "invalidates dependent pending proposals and grants",
                "Never resolve two equally authoritative conflicts",
                "Use `preview-forget`",
                "redact dependent denial/split records",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "exact matched pattern IDs and revisions",
                "consumable exactly once",
                "store-globally unused confirmation reference",
                "atomically marks the grant used",
                "preview-forget",
                "Any intervening evidence or lineage change makes the preview stale",
            ),
        )

    def test_agent_skill_tool_and_mcp_routing_is_atomic_and_fail_closed(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        smart = normalized(skill_body("nerd-smart"))
        assert_terms(
            self,
            body,
            (
                "Ordered atomic agent profiles",
                "agent profiles binding skills, tools, and MCP servers",
                "Treat a returned routing profile as a recommendation",
                "Resolve every named agent, skill, tool, and MCP server",
                "never silently drop, substitute, reorder, install, delegate, or invoke",
                "Log actual agent/skill/tool/MCP usage only as inert `agent_inference`",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                '"agent": "codex"',
                '"skills": ["nerd-smart"]',
                '"tools": ["web.run"]',
                '"mcp_servers": ["github"]',
                "`codex`, `claude-code`, or `cursor`",
                "Routing uses `fill` only",
                "must never be merged or cross-combined",
                "current authenticated registry",
                "Missing or disallowed components fail closed",
            ),
        )
        self.assertIn("`nerd-memory` may be auto-enabled by Nerd Smart", smart)
        self.assertNotIn("remembered `routing` chain", smart)

    def test_denial_is_neutral_and_generic_routes_need_confirmed_splits(self):
        body = normalized(memory_guidance_body())
        contract = normalized(memory_reference_body("memory-contract.md"))
        assert_terms(
            self,
            body,
            (
                "Deny a Recommendation",
                "It is evidence only that this exact recommendation was rejected",
                "agent_mistake",
                "human_forgot",
                "route_too_generic",
                "Do not infer the third explanation",
                "Nerd-memory proposes a split",
                "strictly specializes the parent scope",
                "the parent remains the fallback elsewhere",
                "memory write only",
                "requires a fresh endpoint proposal afterward",
            ),
        )
        assert_terms(
            self,
            contract,
            (
                "A denied proposal is terminal",
                "Statistical prevalence must never select a diagnosis",
                "This version implements specialization, not a complete partition",
                "activation_reason=explicit_split",
                "One user event can authorize at most one transition",
                "confirm-split --split-id ID",
                "all unselected applied bindings",
                "returns no endpoint",
            ),
        )

    def test_smart_composes_memory_only_as_a_bounded_specialty(self):
        smart = normalized(skill_body("nerd-smart"))
        hook = normalized(
            (SKILLS / "nerd-smart" / "scripts" / "prompt_hook.py").read_text()
        )
        assert_terms(
            self,
            smart,
            (
                "`nerd-memory` may be auto-enabled by Nerd Smart",
                "when memory retrieval would materially strengthen the confirmed work",
                "Endpoint routes may add one specialty only",
                "without changing the endpoint",
            ),
        )
        self.assertNotIn("When `nerd-memory` is installed and enabled", smart)
        assert_terms(
            self,
            hook,
            (
                "standing authorization applies only to `nerd-smart`",
                "does not load, invoke, enable, or authorize any other skill",
            ),
        )
        self.assertNotIn("nerd-memory", hook)


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
