from pathlib import Path
import tempfile
import unittest

from benchmarks.nerdbench.report import (
    aggregate_results,
    render_readme_results,
    render_summary_markdown,
    write_report,
)


ARMS = {
    "smart": ("nerd-smart", "superpowers-brainstorming"),
    "surgery": ("nerd-surgery", "superpowers-systematic-debugging"),
    "execute": ("nerd-execute", "superpowers-executing-plans"),
    "silent": ("nerd-silent", "regular"),
}


def manifest():
    return {
        "run_id": "20260715T000000Z-deadbee",
        "created_at": "2026-07-15T00:00:00+00:00",
        "smoke": False,
        "planned_runs": 405,
        "nerd_commit": "deadbeef",
        "upstream_commit": "c984ea2e7aeffdcc865784fd6c5e3ab75da0209a",
        "config": {"repetitions": 3, "seed": 7},
        "agent_versions": {
            "codex": "codex-test",
            "claude": "claude-test",
            "cursor": "cursor-test",
        },
    }


def build_fixture():
    records = []
    scores = []
    for comparison, (treatment, baseline) in ARMS.items():
        count = 6 if comparison == "silent" else 5
        for index in range(count):
            case_id = f"{comparison}-case-{index}"
            for condition in (treatment, baseline):
                is_treatment = condition == treatment
                run_id = f"{comparison}--{case_id}--codex--r1--{condition}"
                if comparison == "silent":
                    score = 89.0 if is_treatment else 90.0
                    latency = 4.0 if is_treatment else 5.0
                    tokens = 300 if is_treatment else 500
                    if index == 5:
                        score = 80.0 if is_treatment else 90.0
                        tokens = 100 if is_treatment else 1000
                else:
                    score = 90.0 if is_treatment else 80.0
                    latency = 8.0 if is_treatment else 10.0
                    tokens = 100
                records.append(
                    {
                        "run_id": run_id,
                        "case_id": case_id,
                        "condition": condition,
                        "agent": "codex",
                        "model": "test-model",
                        "repetition": 1,
                        "exit_code": 0,
                        "elapsed_seconds": latency,
                        "output_tokens": tokens,
                    }
                )
                scores.append(
                    {
                        "run_id": run_id,
                        "score": score,
                        "passed": score >= 80,
                        "hard_gate_failures": [],
                        "judge_valid": True,
                    }
                )
    return records, scores


class AggregateReportTests(unittest.TestCase):
    def test_accuracy_latency_and_silent_tokens(self):
        records, scores = build_fixture()
        summary = aggregate_results(records, scores, manifest())

        self.assertEqual(summary["publication_state"], "publishable")
        smart = summary["comparisons"]["smart"]
        self.assertEqual(smart["treatment"]["mean_score"], 90.0)
        self.assertEqual(smart["baseline"]["mean_score"], 80.0)
        self.assertEqual(smart["paired"]["score_delta"], 10.0)
        self.assertEqual(smart["paired"]["latency_delta_percent"], -20.0)

        silent = summary["comparisons"]["silent"]
        self.assertEqual(silent["valid_pairs"]["accuracy"], 6)
        self.assertEqual(silent["valid_pairs"]["latency"], 6)
        self.assertEqual(silent["valid_pairs"]["tokens"], 5)
        self.assertEqual(silent["tokens"]["regular_median"], 500.0)
        self.assertEqual(silent["tokens"]["silent_median"], 300.0)
        self.assertEqual(silent["tokens"]["saved_percent"], 40.0)
        self.assertIn("accuracy-drop", silent["tokens"]["exclusions"])

    def test_intervals_are_bounded_and_reproducible(self):
        records, scores = build_fixture()
        first = aggregate_results(records, scores, manifest())
        second = aggregate_results(records, scores, manifest())
        self.assertEqual(first, second)
        interval = first["comparisons"]["smart"]["treatment"]["pass_rate_ci95"]
        self.assertGreaterEqual(interval[0], 0)
        self.assertLessEqual(interval[1], 100)

    def test_fewer_than_five_pairs_is_insufficient(self):
        records, scores = build_fixture()
        records = [
            item
            for item in records
            if not item["case_id"].startswith("execute-case-4")
        ]
        scores = [
            item
            for item in scores
            if not item["run_id"].startswith("execute--execute-case-4")
        ]
        summary = aggregate_results(records, scores, manifest())
        self.assertEqual(
            summary["comparisons"]["execute"]["publication_state"],
            "insufficient-data",
        )
        self.assertEqual(summary["publication_state"], "insufficient-data")

    def test_summary_markdown_contains_requested_metrics(self):
        records, scores = build_fixture()
        body = render_summary_markdown(
            aggregate_results(records, scores, manifest())
        )
        for term in (
            "Accuracy score",
            "Pass rate",
            "p50 latency",
            "p95 latency",
            "Tokens saved",
            "Patrol",
        ):
            self.assertIn(term, body)

    def test_readme_renderer_uses_release_evidence(self):
        records, scores = build_fixture()
        summary = aggregate_results(records, scores, manifest())
        body = render_readme_results(summary)
        self.assertIn("| Comparison | Nerd score | Baseline score", body)
        self.assertIn("Smart vs Superpowers Brainstorming", body)
        self.assertIn("90.0%", body)
        self.assertIn("80.0%", body)
        self.assertIn("-20.00%", body)
        self.assertIn("Eligible paired output tokens", body)
        self.assertIn("500", body)
        self.assertIn("300", body)
        self.assertIn("-40.0%", body)
        self.assertIn("| p50 latency | 5.0s | 4.0s | -20.00% |", body)
        self.assertIn("5 valid pairs", body)
        self.assertIn("21 cases", body)
        self.assertIn("Nerd `deadbeef`", body)
        self.assertIn(
            "Superpowers `c984ea2e7aeffdcc865784fd6c5e3ab75da0209a`",
            body,
        )
        self.assertIn(
            "benchmarks/results/20260715T000000Z-deadbee/summary.md",
            body,
        )

    def test_readme_renderer_rejects_insufficient_evidence(self):
        records, scores = build_fixture()
        records = [
            item for item in records
            if not item["case_id"].startswith("smart-case-4")
        ]
        scores = [
            item for item in scores
            if not item["run_id"].startswith("smart--smart-case-4")
        ]
        summary = aggregate_results(records, scores, manifest())
        with self.assertRaisesRegex(ValueError, "not publishable"):
            render_readme_results(summary)


class ReportFileTests(unittest.TestCase):
    def test_write_and_check_are_deterministic(self):
        records, scores = build_fixture()
        with tempfile.TemporaryDirectory() as directory:
            result_dir = Path(directory)
            (result_dir / "manifest.json").write_text(__import__("json").dumps(manifest()))
            (result_dir / "raw.jsonl").write_text(
                "\n".join(__import__("json").dumps(item) for item in records) + "\n"
            )
            (result_dir / "scores.jsonl").write_text(
                "\n".join(__import__("json").dumps(item) for item in scores) + "\n"
            )
            write_report(result_dir)
            write_report(result_dir, check=True)
            self.assertTrue((result_dir / "summary.json").is_file())
            self.assertTrue((result_dir / "summary.md").is_file())


if __name__ == "__main__":
    unittest.main()
