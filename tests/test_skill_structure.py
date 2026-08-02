from pathlib import Path
import tempfile
import unittest

from scripts.validate_skills import (
    PUBLIC_SKILLS,
    REQUIRED_REFERENCES,
    REQUIRED_SCRIPTS,
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
                "nerd-fast",
                "nerd-xfast",
            ),
        )

    def test_reference_ownership_is_exact(self):
        self.assertEqual(
            REQUIRED_REFERENCES,
            {
                "nerd-smart": (
                    "brainstorming.md",
                    "spec-template.md",
                    "system-design-template.md",
                    "plan-template.md",
                    "document-overview-template.md",
                    "document-how-to-template.md",
                    "document-reference-template.md",
                    "diagnosis-template.md",
                    "rca-template.md",
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
                "nerd-execute": (),
                "nerd-silent": (),
                "nerd-fast": (),
                "nerd-xfast": (),
            },
        )
        self.assertFalse((ROOT / "skills" / "nerd-execute" / "references").exists())
        self.assertFalse((ROOT / "skills" / "nerd-fast" / "references").exists())
        self.assertFalse((ROOT / "skills" / "nerd-xfast" / "references").exists())
        self.assertEqual(REQUIRED_SCRIPTS["nerd-smart"], ("prompt_hook.py",))
        self.assertEqual(REQUIRED_SCRIPTS["nerd-fast"], ("symbol_index.py",))
        self.assertEqual(REQUIRED_SCRIPTS["nerd-xfast"], ())

    def test_smart_reference_files_match_registry(self):
        references = ROOT / "skills" / "nerd-smart" / "references"
        actual = {path.name for path in references.glob("*.md")}
        self.assertEqual(actual, set(REQUIRED_REFERENCES["nerd-smart"]))

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
