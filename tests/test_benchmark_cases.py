from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.nerdbench.cases import load_cases


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "cases"

EXPECTED_CASES = {
    "smart": {
        "smart-ambiguous-focus",
        "smart-compound-queue",
        "smart-invalid-premise",
        "smart-plan-endpoint",
        "smart-confirmed-small-task",
    },
    "surgery": {
        "surgery-trace-source",
        "surgery-component-boundary",
        "surgery-not-reproducible",
        "surgery-repair-under-uncertainty",
        "surgery-repeated-failure",
    },
    "execute": {
        "execute-small-feature",
        "execute-written-plan",
        "execute-repository-convention",
        "execute-preexisting-failure",
        "execute-blocker",
    },
    "silent": {
        "silent-final-only",
        "silent-code-only",
        "silent-findings-only",
        "silent-minimal-report",
        "silent-verification-conflict",
    },
    "patrol": {
        "patrol-auth-pr",
        "patrol-vague-scope",
        "patrol-advisory-without-reachability",
        "patrol-secret-logging",
        "patrol-no-findings",
    },
}


def criterion(**overrides):
    value = {
        "id": "required",
        "weight": 100,
        "hard_gate": True,
        "evaluator": "regex",
        "expected": "result",
    }
    value.update(overrides)
    return value


def case(**overrides):
    value = {
        "id": "valid-case",
        "comparison": "smart",
        "prompt": "Return a result.",
        "fixture": None,
        "endpoint": "document",
        "timeout_seconds": 60,
        "criteria": [criterion()],
    }
    value.update(overrides)
    return value


class BenchmarkCaseTests(unittest.TestCase):
    def write_cases(self, directory: str, cases: list[dict]) -> Path:
        path = Path(directory) / "cases.json"
        path.write_text(json.dumps({"cases": cases}))
        return path

    def test_case_weights_sum_to_one_hundred(self):
        with tempfile.TemporaryDirectory() as directory:
            loaded = load_cases(self.write_cases(directory, [case()]))[0]
        self.assertEqual(sum(item.weight for item in loaded.criteria), 100)

    def test_case_requires_at_least_one_hard_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            loaded = load_cases(self.write_cases(directory, [case()]))[0]
        self.assertTrue(any(item.hard_gate for item in loaded.criteria))

    def test_duplicate_case_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_cases(directory, [case(), case()])
            with self.assertRaisesRegex(ValueError, "duplicate case id"):
                load_cases(path)

    def test_unknown_evaluator_is_rejected(self):
        invalid = case(criteria=[criterion(evaluator="guess")])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unknown evaluator"):
                load_cases(self.write_cases(directory, [invalid]))

    def test_unknown_fields_are_rejected(self):
        invalid = case(answer="leaked")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unknown case fields"):
                load_cases(self.write_cases(directory, [invalid]))

    def test_invalid_weights_and_timeout_are_rejected(self):
        invalid = case(
            timeout_seconds=0,
            criteria=[criterion(weight=90)],
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                load_cases(self.write_cases(directory, [invalid]))


class BenchmarkCorpusTests(unittest.TestCase):
    def test_exact_case_ids(self):
        for comparison, expected in EXPECTED_CASES.items():
            actual = {item.id for item in load_cases(CASES / f"{comparison}.json")}
            self.assertEqual(actual, expected)

    def test_every_comparison_has_five_valid_cases(self):
        for comparison in EXPECTED_CASES:
            loaded = load_cases(CASES / f"{comparison}.json")
            self.assertEqual(len(loaded), 5)
            for item in loaded:
                self.assertEqual(sum(c.weight for c in item.criteria), 100)
                self.assertTrue(any(c.hard_gate for c in item.criteria))

    # def test_fixture_baseline_manifest_is_true(self):
    #     manifest = json.loads(
    #         (ROOT / "benchmarks" / "fixtures" / "baselines.json").read_text()
    #     )
    #     for entry in manifest:
    #         result = subprocess.run(
    #             entry["command"],
    #             cwd=ROOT / "benchmarks" / "fixtures" / entry["fixture"],
    #             capture_output=True,
    #             text=True,
    #         )
    #         self.assertEqual(
    #             result.returncode,
    #             entry["expected_exit"],
    #             msg=f"{entry['fixture']}: {result.stdout}\n{result.stderr}",
    #         )


class MaterializationTests(unittest.TestCase):
    def test_materialization_is_fresh_and_hides_rubrics(self):
        from benchmarks.nerdbench.materialize import materialize_run

        case_item = load_cases(CASES / "execute.json")[0]
        with tempfile.TemporaryDirectory() as directory:
            first = materialize_run(
                case_item, "nerd-execute", "codex", Path(directory) / "one"
            )
            second = materialize_run(
                case_item, "nerd-execute", "codex", Path(directory) / "two"
            )
            self.assertNotEqual(first, second)
            self.assertTrue((first / ".git").exists())
            self.assertFalse((first / "benchmarks" / "cases").exists())
            self.assertTrue((first / ".agents" / "skills" / "nerd-execute").exists())

    def test_upstream_commit_mismatch_is_rejected(self):
        from benchmarks.nerdbench.materialize import verify_superpowers_checkout

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=path, check=True)
            subprocess.run(["git", "config", "user.email", "bench@example.com"], cwd=path, check=True)
            subprocess.run(["git", "config", "user.name", "Benchmark"], cwd=path, check=True)
            (path / "README").write_text("wrong")
            subprocess.run(["git", "add", "README"], cwd=path, check=True)
            subprocess.run(["git", "commit", "-qm", "wrong"], cwd=path, check=True)
            with self.assertRaisesRegex(ValueError, "pinned commit"):
                verify_superpowers_checkout(path)

    def test_upstream_verifies_tag_object_and_dereferenced_commit(self):
        from benchmarks.nerdbench import materialize

        def resolve(command, _cwd):
            if command[-1] == "HEAD":
                return "d884ae04edebef577e82ff7c4e143debd0bbec99"
            return "c984ea2e7aeffdcc865784fd6c5e3ab75da0209a"

        with patch.object(materialize, "_run", side_effect=resolve) as run:
            materialize.verify_superpowers_checkout(Path("/upstream"))
        self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
