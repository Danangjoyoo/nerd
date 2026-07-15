from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
RELEASE = ROOT / ".github/workflows/release.yml"
SKILLS = (
    "nerd-smart",
    "nerd-surgery",
    "nerd-patrol",
    "nerd-execute",
    "nerd-silent",
)


class WorkflowContractTests(unittest.TestCase):
    def test_workflows_exist(self):
        self.assertTrue(CI.is_file())
        self.assertTrue(RELEASE.is_file())

    def test_ci_runs_deterministic_checks(self):
        body = CI.read_text(encoding="utf-8")
        for command in (
            "python3 -m compileall -q scripts benchmarks tests",
            "python3 -m unittest discover -s tests -v",
            "python3 scripts/validate_skills.py",
            "npx skills add . --list",
            "python3 benchmarks/run.py plan --config benchmarks/config.json",
            'RUN_ID="$(sed -n',
            'if [ "$RUN_ID" = "pending" ]',
            "Benchmark results pending a complete release run.",
            "python3 benchmarks/run.py publish",
            "--allow-historical",
            "--check",
        ):
            self.assertIn(command, body)

    def test_workflows_are_read_only_and_safe(self):
        for path in (CI, RELEASE):
            body = path.read_text(encoding="utf-8")
            self.assertIn("permissions:", body)
            self.assertIn("contents: read", body)
            self.assertNotIn("pull_request_target", body)
            self.assertNotIn("contents: write", body)
            self.assertNotIn("secrets.", body)

    def test_release_checks_tag_and_public_sources(self):
        body = RELEASE.read_text(encoding="utf-8")
        for fragment in (
            "v*",
            "workflow_dispatch",
            "https://github.com/Danangjoyoo/nerd/tree/$GITHUB_REF_NAME",
            "npx skills add danangjoyoo/nerd --list",
            "--copy",
            "--global",
            "--yes",
            "--agent codex",
            "--agent claude-code",
            "--agent cursor",
            "cancel-in-progress: false",
        ):
            self.assertIn(fragment, body)
        for skill in SKILLS:
            self.assertIn(skill, body)

    def test_release_counts_exactly_five_public_skills(self):
        body = RELEASE.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_SKILL_COUNT=5", body)
        self.assertIn("grep -E", body)
        self.assertIn("wc -l", body)


if __name__ == "__main__":
    unittest.main()
