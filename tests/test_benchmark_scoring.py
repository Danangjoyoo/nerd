from pathlib import Path
import random
import unittest

from benchmarks.nerdbench.models import (
    BenchmarkCase,
    Criterion,
    RunResult,
    RunSpec,
)
from benchmarks.nerdbench.scorer import (
    blind_pair,
    build_judge_command,
    build_judge_prompt,
    judge_output_schema,
    score_run,
    validate_judge_result,
)


def make_case(criteria):
    return BenchmarkCase(
        id="case",
        comparison="smart",
        prompt="prompt",
        fixture=None,
        endpoint="document",
        timeout_seconds=30,
        criteria=tuple(criteria),
    )


def make_run(**overrides):
    values = {
        "spec": RunSpec(
            run_id="run",
            case_id="case",
            condition="nerd-smart",
            agent="codex",
            model="test-model",
            repetition=1,
            workspace=Path("/tmp/workspace"),
        ),
        "exit_code": 0,
        "elapsed_seconds": 1.0,
        "final_text": "required safe",
        "output_tokens": 20,
        "events": (),
        "changed_files": ("result.txt",),
        "command_results": {"python3 -m unittest -v": 0},
    }
    values.update(overrides)
    return RunResult(**values)


class ScoringTests(unittest.TestCase):
    def test_weighted_score_and_threshold(self):
        case = make_case(
            (
                Criterion("required", 80, True, "regex", "required"),
                Criterion("optional", 20, False, "regex", "missing"),
            )
        )
        result = score_run(case, make_run(), None)
        self.assertEqual(result.score, 80)
        self.assertTrue(result.passed)

    def test_hard_gate_failure_prevents_pass(self):
        case = make_case(
            (
                Criterion("required", 80, True, "regex", "absent"),
                Criterion("optional", 20, False, "regex", "safe"),
            )
        )
        result = score_run(case, make_run(), None)
        self.assertEqual(result.score, 20)
        self.assertFalse(result.passed)
        self.assertEqual(result.hard_gate_failures, ("required",))

    def test_absent_regex_file_and_command_evaluators(self):
        case = make_case(
            (
                Criterion("safe", 30, True, "absent_regex", "danger"),
                Criterion("file", 30, True, "file", "result.txt"),
                Criterion(
                    "command",
                    40,
                    True,
                    "command",
                    "python3 -m unittest -v::0",
                ),
            )
        )
        self.assertTrue(score_run(case, make_run(), None).passed)

    def test_judge_is_required_for_judge_criterion(self):
        case = make_case((Criterion("quality", 100, True, "judge", "clear"),))
        self.assertFalse(score_run(case, make_run(), None).passed)
        self.assertTrue(
            score_run(case, make_run(), {"quality": True}).passed
        )

    def test_blind_pair_is_seeded_and_hides_conditions(self):
        left = make_run(final_text="left")
        right = make_run(
            spec=RunSpec(
                "other",
                "case",
                "superpowers-brainstorming",
                "codex",
                "test-model",
                1,
                Path("/tmp/other"),
            ),
            final_text="right",
        )
        payload, mapping = blind_pair(left, right, random.Random(7))
        self.assertEqual(set(payload), {"A", "B"})
        self.assertEqual(set(mapping), {"A", "B"})
        self.assertNotIn("condition", repr(payload).casefold())

    def test_malformed_judge_result_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "judge"):
            validate_judge_result(
                {"criteria": {"quality": {"A": "yes", "B": True}}},
                ("quality",),
            )

    def test_judge_prompt_is_blinded_and_complete(self):
        case = make_case(
            (Criterion("quality", 100, True, "judge", "States the endpoint."),)
        )
        body = build_judge_prompt(case, {"A": "first", "B": "second"})
        for expected in (
            "prompt",
            "document",
            "quality",
            "States the endpoint.",
            '"A": "first"',
            '"B": "second"',
        ):
            self.assertIn(expected, body)
        self.assertNotIn("nerd-smart", body)
        self.assertNotIn("superpowers", body.casefold())
        self.assertNotIn("latency", body.casefold())

    def test_judge_command_is_noninteractive_and_schema_bound(self):
        command = build_judge_command(
            Path("/tmp/schema.json"),
            "judge this",
            model="test-model",
            reasoning_effort="xhigh",
        )
        self.assertEqual(command[0:2], ["codex", "exec"])
        for value in (
            "--ephemeral",
            "--json",
            "--sandbox",
            "read-only",
            "--output-schema",
            "/tmp/schema.json",
            "--model",
            "test-model",
            'model_reasoning_effort="xhigh"',
        ):
            self.assertIn(value, command)
        self.assertNotIn("dangerously-bypass", " ".join(command))

    def test_judge_output_schema_declares_every_criterion(self):
        case = make_case(
            (Criterion("quality", 100, True, "judge", "States the endpoint."),)
        )
        schema = judge_output_schema(case)
        criteria = schema["properties"]["criteria"]
        self.assertEqual(set(criteria["properties"]), {"quality"})
        self.assertEqual(criteria["required"], ["quality"])
        decision = criteria["properties"]["quality"]
        self.assertEqual(decision["required"], ["A", "B", "evidence"])
        self.assertFalse(decision["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
