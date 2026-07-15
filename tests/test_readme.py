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
MODELS = ("Sol", "Terra", "Luna", "GPT 5.5", "Opus", "Fable", "Sonnet", "Haiku")


def _graph_rows(body: str, heading: str, next_heading: str):
    start = f"### {heading}"
    end = f"### {next_heading}"
    if start not in body or end not in body:
        return "", {}
    region = body.split(start, 1)[1].split(end, 1)[0]
    pattern = re.compile(
        r"^(Sol|Terra|Luna|GPT 5\.5|Opus|Fable|Sonnet|Haiku)\s+"
        r"(Nerd|Superpowers)\s+\[([█░]{20})\]\s+"
        r"(\d+\.\d)(%|s)$",
        re.MULTILINE,
    )
    rows = {
        (model, variant): (float(value), unit, bar.count("█"))
        for model, variant, bar, value, unit in pattern.findall(region)
    }
    header_pattern = re.compile(
        r"^=+\s*(Sol|Terra|Luna|GPT 5\.5|Opus|Fable|Sonnet|Haiku)\s*=+$"
    )
    row_pattern = re.compile(
        r"^(Nerd|Superpowers)\s+\[([█░]{20})\]\s+(\d+\.\d)(%|s)$"
    )
    model = None
    for line in region.splitlines():
        header = header_pattern.match(line)
        if header:
            model = header.group(1)
            continue
        row = row_pattern.match(line)
        if model and row:
            variant, bar, value, unit = row.groups()
            rows[(model, variant)] = (float(value), unit, bar.count("█"))
    return region, rows


class ReadmeContractTests(unittest.TestCase):
    def test_header_has_nerd_banner_and_skills_badge(self):
        body = README.read_text(encoding="utf-8")
        expected_header = (
            "# Nerd\n\n"
            "![Nerd mascot banner](assets/nerd-banner.png)\n\n"
            "[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/"
            "badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) "
            "[![skills.sh](https://skills.sh/b/danangjoyoo/nerd)]"
            "(https://skills.sh/danangjoyoo/nerd)\n"
        )
        self.assertTrue(body.startswith(expected_header))

        banner = ROOT / "assets" / "nerd-banner.png"
        self.assertTrue(banner.is_file())
        self.assertEqual(banner.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_install_command_is_current(self):
        body = README.read_text(encoding="utf-8")
        commands = {
            "Codex": "codex",
            "Claude Code": "claude-code",
            "Cursor": "cursor",
        }
        for label, agent in commands.items():
            command = (
                f"# {label}\n"
                "npx skills add danangjoyoo/nerd \\\n"
                "  --global \\\n"
                f"  --agent {agent} \\\n"
                "  --skill '*' \\\n"
                "  --yes"
            )
            self.assertIn(command, body)
        self.assertIn("./scripts/install.sh {claude|codex|cursor|all}", body)
        self.assertNotIn("--agent codex | claude-code | cursor", body)
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

    def test_accuracy_graph_uses_smart_pair_for_each_model(self):
        body = README.read_text(encoding="utf-8")
        region, rows = _graph_rows(body, "Accuracy", "Latency")
        expected = {
            "Sol": ((100.0, 20), (100.0, 20)),
            "Terra": ((100.0, 20), (30.0, 6)),
            "Luna": ((100.0, 20), (65.0, 13)),
            "GPT 5.5": ((100.0, 20), (100.0, 20)),
            "Opus": ((100.0, 20), (65.0, 13)),
            "Fable": ((100.0, 20), (65.0, 13)),
            "Sonnet": ((100.0, 20), (65.0, 13)),
            "Haiku": ((100.0, 20), (30.0, 6)),
        }
        self.assertEqual(len(rows), 16)
        for model, (nerd, reference) in expected.items():
            self.assertEqual(rows[(model, "Nerd")], (nerd[0], "%", nerd[1]))
            self.assertEqual(
                rows[(model, "Superpowers")],
                (reference[0], "%", reference[1]),
            )
        for workflow in ("Smart", "Surgery", "Execute", "Silent"):
            self.assertNotIn(workflow, region)

    def test_latency_graph_uses_smart_pair_for_each_model(self):
        body = README.read_text(encoding="utf-8")
        region, rows = _graph_rows(body, "Latency", "Token savings")
        expected = {
            "Sol": ((82.9, 9), (89.9, 10)),
            "Terra": ((78.8, 9), (88.7, 10)),
            "Luna": ((65.3, 7), (84.4, 9)),
            "GPT 5.5": ((46.9, 5), (72.1, 8)),
            "Opus": ((35.6, 4), (114.4, 13)),
            "Fable": ((109.9, 12), (103.1, 11)),
            "Sonnet": ((32.5, 4), (169.6, 19)),
            "Haiku": ((30.6, 3), (28.4, 3)),
        }
        self.assertEqual(len(rows), 16)
        for model, (nerd, reference) in expected.items():
            self.assertEqual(rows[(model, "Nerd")], (nerd[0], "s", nerd[1]))
            self.assertEqual(
                rows[(model, "Superpowers")],
                (reference[0], "s", reference[1]),
            )
        self.assertIn("Nerd Smart versus Superpowers Brainstorming", region)
        self.assertIn("no aggregation", region)
        for workflow in ("Surgery", "Execute", "Silent"):
            self.assertNotIn(workflow, region)

    def test_token_graph_has_one_nerd_bar_per_model(self):
        body = README.read_text(encoding="utf-8")
        region, rows = _graph_rows(body, "Token savings", "Method")
        expected = {
            "Sol": (55.9, 19),
            "Terra": (6.9, 2),
            "Luna": (33.3, 11),
            "GPT 5.5": (59.9, 20),
            "Opus": (43.4, 14),
            "Fable": (44.5, 15),
            "Sonnet": (58.4, 19),
            "Haiku": (6.5, 2),
        }
        self.assertEqual(len(rows), 8)
        for model, (value, blocks) in expected.items():
            self.assertEqual(rows[(model, "Nerd")], (value, "%", blocks))
            self.assertNotIn((model, "Superpowers"), rows)
        for workflow in ("Smart", "Surgery", "Execute", "Silent"):
            self.assertNotIn(workflow, region)

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
            170,
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
