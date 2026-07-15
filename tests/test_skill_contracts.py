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

    def test_explicit_nerd_routing_selects_one_specialty_and_silent_modifier(self):
        body = skill_body("nerd-smart")
        assert_terms(
            self,
            body,
            (
                "nerd-surgery",
                "nerd-patrol",
                "nerd-execute",
                "nerd-silent",
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
                "Confirmed",
                "Probable",
                "Unknown",
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
            "## Diagnostic Contract", 1
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
        self.assertIn("Use a mapping only when", body)
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
    def test_uses_fast_track_and_optional_repository_pattern_gate(self):
        body = skill_body("nerd-execute")
        assert_terms(
            self,
            body,
            (
                "<INHERITANCE>",
                "<FAST-TRACK>",
                "nerd-smart",
                "Non-code",
                "Code",
                "Wait for the answer unless the user already opted in or out",
                "If approved",
                "If declined",
                "Never create a repository-pattern artifact",
                "Execute inline without subagents",
            ),
        )

    def test_executes_with_minimal_test_recovery_and_completion_contract(self):
        body = skill_body("nerd-execute")
        assert_terms(
            self,
            body,
            (
                "Contract: [outcome] | Files: [boundary] | Verify: [targeted check]",
                "two to five internal items",
                "do not create milestones, checkpoints, gravity records",
                "write or update one focused test",
                "confirm the expected failure",
                "implement the minimum change",
                "pre-edit baseline only when",
                "two evidence-driven correction attempts",
                "Do not claim success without its output",
                "**Done:**",
                "**Verified by:**",
                "**Not verified**",
            ),
        )

    def test_uses_exactly_ten_optional_generic_proof_mappings(self):
        body = skill_body("nerd-execute")
        mapping = body.split("## Generic Mappings", 1)[1].split(
            "## Gate Repository Pattern Context", 1
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
        self.assertIn('short_description: "Lean implementation with optional pattern scan"', metadata)
        self.assertIn("$nerd-execute", metadata)
        self.assertIn("test-first workflow and fresh verification", metadata)
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


class FamilyContractTests(unittest.TestCase):
    def test_frontmatter_names_match_paths(self):
        for path in SKILLS.glob("*/SKILL.md"):
            match = re.search(r"^name:\s*([^\n]+)$", path.read_text(), re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1).strip(), path.parent.name)


if __name__ == "__main__":
    unittest.main()
