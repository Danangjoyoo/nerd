from pathlib import Path
import tempfile
import unittest

from scripts.validate_skills import (
    PUBLIC_SKILLS,
    REQUIRED_REFERENCES,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_public_skill_set_is_exact(self):
        self.assertEqual(
            PUBLIC_SKILLS,
            (
                "nerd-smart",
                "nerd-surgery",
                "nerd-patrol",
                "nerd-execute",
                "nerd-silent",
            ),
        )

    def test_reference_ownership_is_exact(self):
        self.assertEqual(
            REQUIRED_REFERENCES,
            {
                "nerd-smart": ("brainstorming.md",),
                "nerd-surgery": (
                    "systematic-debugging.md",
                    "test-first-repair.md",
                    "verification.md",
                ),
                "nerd-patrol": (
                    "test-first-remediation.md",
                    "verification.md",
                ),
                "nerd-execute": (
                    "plan-execution.md",
                    "test-first-build.md",
                    "verification.md",
                ),
                "nerd-silent": (),
            },
        )

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

    def test_derived_skills_carry_identical_license(self):
        derived = PUBLIC_SKILLS[:-1]
        licenses = [
            (ROOT / "skills" / skill / "LICENSE.superpowers").read_text()
            for skill in derived
        ]
        self.assertTrue(licenses[0].strip())
        self.assertTrue(all(body == licenses[0] for body in licenses[1:]))


if __name__ == "__main__":
    unittest.main()
