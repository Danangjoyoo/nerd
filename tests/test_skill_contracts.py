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
    def test_routes_one_primary_specialty_and_silent_modifier(self):
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


class ExecuteContractTests(unittest.TestCase):
    def test_preserves_build_records(self):
        body = skill_body("nerd-execute")
        assert_terms(
            self,
            body,
            (
                "**Build Contract**",
                "**Build Baseline**",
                "**Repository Gravity**",
                "**Build Milestone**",
                "**Build Checkpoint**",
                "**Pattern Conflict**",
                "**Build Conflict**",
                "**Checkpoint Blocker**",
                "**Contract Change**",
                "**Build Result**",
            ),
        )

    def test_preserves_proof_first_execution_contract(self):
        body = skill_body("nerd-execute")
        assert_terms(
            self,
            body,
            (
                "proof-first",
                "two evidence-driven correction attempts",
                "Repository Topology",
                "Never dispatch subagents",
                "Silent controls intermediate presentation",
                "references/plan-execution.md",
                "references/test-first-build.md",
                "references/verification.md",
            ),
        )
        self.assertNotIn("superpowers:", body.casefold())


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
