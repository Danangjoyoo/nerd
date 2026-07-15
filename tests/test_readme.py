from pathlib import Path
import re
import unittest

from benchmarks.nerdbench.report import pending_readme_results, render_readme_results


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SKILLS = (
    "nerd-smart",
    "nerd-surgery",
    "nerd-patrol",
    "nerd-execute",
    "nerd-silent",
)
START = "<!-- BENCHMARK_RESULTS:START -->"
END = "<!-- BENCHMARK_RESULTS:END -->"


class ReadmeContractTests(unittest.TestCase):
    def test_install_command_is_current(self):
        body = README.read_text(encoding="utf-8")
        self.assertIn("npx skills add danangjoyoo/nerd", body)
        self.assertNotIn("danangjoyoo/mensa", body.casefold())

    def test_every_public_skill_is_listed_once(self):
        body = README.read_text(encoding="utf-8")
        for name in SKILLS:
            self.assertEqual(body.count(f"`{name}`"), 1)

    def test_benchmark_markers_are_unique(self):
        body = README.read_text(encoding="utf-8")
        self.assertEqual(body.count("<!-- BENCHMARK_RUN:"), 1)
        self.assertEqual(body.count(START), 1)
        self.assertEqual(body.count(END), 1)

    def test_pending_benchmark_copy_is_exact_and_has_no_numeric_claims(self):
        body = README.read_text(encoding="utf-8")
        match = re.search(r"<!-- BENCHMARK_RUN:([^ ]+) -->", body)
        self.assertIsNotNone(match)
        region = body.split(START, 1)[1].split(END, 1)[0].strip()
        if match.group(1) == "pending":
            self.assertEqual(region, pending_readme_results())
            self.assertNotRegex(region, r"\d+(?:\.\d+)?%")
            return
        summary_path = ROOT / "benchmarks/results" / match.group(1) / "summary.json"
        self.assertTrue(summary_path.is_file())
        summary = __import__("json").loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(region, render_readme_results(summary))

    def test_readme_remains_sharp(self):
        self.assertLessEqual(
            len(README.read_text(encoding="utf-8").splitlines()),
            120,
        )

    def test_ci_badge_is_current(self):
        body = README.read_text(encoding="utf-8")
        badge = (
            "[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/"
            "ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/"
            "workflows/ci.yml)"
        )
        self.assertIn(badge, body)


if __name__ == "__main__":
    unittest.main()
