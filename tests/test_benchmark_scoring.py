from pathlib import Path
import json
import random
import tempfile
import threading
import time
import unittest
from unittest import mock

from benchmarks.nerdbench.models import (
    BenchmarkCase,
    Criterion,
    RunResult,
    RunSpec,
)
from benchmarks.nerdbench.scorer import (
    _judge_index,
    blind_pair,
    build_judge_command,
    build_judge_prompt,
    judge_result_directory,
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

    def test_clean_evaluator_requires_no_changed_files(self):
        case = make_case(
            (Criterion("clean", 100, True, "clean", "no changed files"),)
        )
        self.assertTrue(
            score_run(case, make_run(changed_files=()), None).passed
        )
        self.assertFalse(score_run(case, make_run(), None).passed)

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

    def test_concurrent_judges_invoke_each_task_once(self):
        case = make_case(
            (Criterion("quality", 100, True, "judge", "States the endpoint."),)
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_dir = root / "results"
            result_dir.mkdir()
            raw = []
            for run_id, condition in (
                ("nerd", "nerd-smart"),
                ("baseline", "superpowers-brainstorming"),
            ):
                raw.append(
                    {
                        "agent": "codex",
                        "case_id": "case",
                        "changed_files": [],
                        "command_results": {},
                        "condition": condition,
                        "elapsed_seconds": 1.0,
                        "events": [],
                        "exit_code": 0,
                        "final_text": run_id,
                        "model": "test-model",
                        "output_tokens": 1,
                        "reasoning_effort": "xhigh",
                        "repetition": 1,
                        "run_id": run_id,
                        "target_id": "test-target",
                    }
                )
            (result_dir / "raw.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in raw),
                encoding="utf-8",
            )
            config = {
                "_root": root,
                "seed": 7,
                "judge": {
                    "agent": "codex",
                    "model": "judge-model",
                    "reasoning_effort": "xhigh",
                    "timeout_seconds": 30,
                },
            }
            started = threading.Event()
            invoke_count = 0
            count_lock = threading.Lock()
            errors = []

            def fake_invoke(*_args, **_kwargs):
                nonlocal invoke_count
                with count_lock:
                    invoke_count += 1
                started.set()
                time.sleep(0.1)
                return {
                    "criteria": {
                        "quality": {
                            "A": True,
                            "B": True,
                            "evidence": "Both state the endpoint.",
                        }
                    }
                }, 0.1

            def run_judge():
                try:
                    judge_result_directory(result_dir, config)
                except Exception as error:  # pragma: no cover - assertion aid
                    errors.append(error)

            with mock.patch(
                "benchmarks.nerdbench.scorer._case_index",
                return_value={"case": case},
            ), mock.patch(
                "benchmarks.nerdbench.scorer._invoke_judge",
                side_effect=fake_invoke,
            ):
                first = threading.Thread(target=run_judge)
                second = threading.Thread(target=run_judge)
                first.start()
                self.assertTrue(started.wait(timeout=1))
                second.start()
                first.join(timeout=2)
                second.join(timeout=2)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(invoke_count, 1)
            judge_records = [
                json.loads(line)
                for line in (result_dir / "judges.jsonl").read_text().splitlines()
            ]
            self.assertEqual(len(judge_records), 1)

    def test_duplicate_judge_tasks_are_rejected_before_scoring(self):
        case = make_case(
            (Criterion("quality", 100, True, "judge", "States the endpoint."),)
        )
        record = {
            "case_id": "case",
            "criteria": {
                "quality": {
                    "A": True,
                    "B": True,
                    "evidence": "Both state the endpoint.",
                }
            },
            "mapping": {"A": "nerd", "B": "baseline"},
            "task_id": "duplicate-task",
        }
        with tempfile.TemporaryDirectory() as temporary:
            result_dir = Path(temporary)
            (result_dir / "judges.jsonl").write_text(
                json.dumps(record) + "\n" + json.dumps(record) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate judge task"):
                _judge_index(result_dir, {"case": case})


if __name__ == "__main__":
    unittest.main()
