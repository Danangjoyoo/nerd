from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_HTML = ROOT / "docs" / "benchmark" / "nerd-cost-accuracy.html"


class BenchmarkDocsTests(unittest.TestCase):
    def test_gpt_smart_latency_uses_complex_case_run(self):
        body = BENCHMARK_HTML.read_text(encoding="utf-8")
        expected_rows = (
            "smart: { accuracy: [100, 100], latency: [82.8831, 89.8903], n: 2, latencyN: 1 }",
            "smart: { accuracy: [100, 30], latency: [78.7681, 88.7246], n: 2, latencyN: 1 }",
            "smart: { accuracy: [100, 65], latency: [65.3245, 84.4268], n: 2, latencyN: 1 }",
            "smart: { accuracy: [100, 100], latency: [46.8634, 72.0816], n: 2, latencyN: 1 }",
        )
        for row in expected_rows:
            self.assertIn(row, body)

        self.assertIn("result[`${metric}N`] ?? result.n", body)


if __name__ == "__main__":
    unittest.main()
