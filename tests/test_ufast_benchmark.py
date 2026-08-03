from pathlib import Path
import json
import tempfile
import unittest

from benchmarks.nerdbench.adapters import get_adapter
from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.materialize import materialize_run
from benchmarks.nerdbench.models import RunSpec
from benchmarks.nerdbench.runner import (
    condition_prompt,
    load_config,
    schedule_runs,
)
from benchmarks.nerdbench.ufast_report import (
    build_feedback_trace,
    render_feedback_markdown,
    summarize_ufast,
    write_ufast_artifacts,
)
from benchmarks.run import build_parser


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks" / "pilots" / "ufast-v1-two-cases"
CONFIG = PILOT / "gpt-5.6-luna-high.json"


def make_spec(workspace: Path, condition: str) -> RunSpec:
    return RunSpec(
        run_id=f"ufast-{condition}",
        case_id="ufast-v1-high-complexity",
        condition=condition,
        agent="codex",
        model="gpt-5.6-luna",
        repetition=1,
        workspace=workspace,
        target_id="gpt-5.6-luna-high",
        reasoning_effort="high",
    )


def write_result_fixture(root: Path) -> Path:
    result = root / "ufast-result"
    result.mkdir()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = {
        "run_id": "ufast-pilot-test",
        "created_at": "2026-08-03T00:00:00+00:00",
        "nerd_commit": "deadbeef",
        "agent_versions": {"codex": "codex-cli test"},
        "config": config,
    }
    raw = []
    scores = []
    cases = (
        ("ufast-v1-low-complexity", ("feature.py", "test_feature.py")),
        (
            "ufast-v1-high-complexity",
            ("alpha.py", "beta.py", "test_math_ops.py"),
        ),
    )
    for case_id, changed_files in cases:
        for condition in ("nerd-xfast", "nerd-ufast"):
            treatment = condition == "nerd-ufast"
            run_id = f"{case_id}-{condition}"
            read_command = "sed -n '1,160p' alpha.py beta.py test_math_ops.py"
            events = [
                {"type": "thread.started", "thread_id": run_id},
                {
                    "type": "item.started",
                    "item": {
                        "id": f"{run_id}-read",
                        "type": "command_execution",
                        "command": read_command,
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": f"{run_id}-read",
                        "type": "command_execution",
                        "command": read_command,
                        "exit_code": 0,
                    },
                },
                {
                    "type": "item.started",
                    "item": {
                        "id": f"{run_id}-edit",
                        "type": "file_change",
                        "changes": [
                            f"/Users/test/work/{path}" for path in changed_files
                        ],
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": f"{run_id}-edit",
                        "type": "file_change",
                        "changes": [
                            f"/Users/test/work/{path}" for path in changed_files
                        ],
                    },
                },
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 1200 if treatment else 2000,
                        "cached_input_tokens": 300 if treatment else 500,
                        "output_tokens": 180 if treatment else 400,
                    },
                },
                {
                    "type": "benchmark.proof",
                    "command": "python3 -m unittest verify_behavior -v",
                    "elapsed_seconds": 0.4 if treatment else 0.8,
                    "exit_code": 0,
                },
            ]
            raw.append(
                {
                    "run_id": run_id,
                    "case_id": case_id,
                    "condition": condition,
                    "agent": "codex",
                    "model": "gpt-5.6-luna",
                    "target_id": "gpt-5.6-luna-high",
                    "reasoning_effort": "high",
                    "repetition": 1,
                    "exit_code": 0,
                    "elapsed_seconds": 5.0 if treatment else 10.0,
                    "final_text": "Completed.\nVerification:\nPASS — focused test",
                    "input_tokens": 1200 if treatment else 2000,
                    "cached_input_tokens": 300 if treatment else 500,
                    "output_tokens": 180 if treatment else 400,
                    "events": events,
                    "changed_files": list(changed_files),
                    "command_results": {
                        "python3 -m unittest verify_behavior -v": 0,
                    },
                    "diff_sha256": "a" * 64,
                }
            )
            scores.append(
                {
                    "run_id": run_id,
                    "score": 100.0,
                    "passed": True,
                    "hard_gate_failures": [],
                    "criterion_results": {},
                    "judge_valid": True,
                }
            )
    (result / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (result / "raw.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in raw),
        encoding="utf-8",
    )
    (result / "scores.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in scores),
        encoding="utf-8",
    )
    return result


class UFastBenchmarkTests(unittest.TestCase):
    def test_has_one_low_and_one_high_complexity_case(self):
        cases = load_cases(PILOT / "cases.json")

        self.assertEqual(
            [case.id for case in cases],
            ["ufast-v1-low-complexity", "ufast-v1-high-complexity"],
        )
        self.assertEqual(
            [case.fixture for case in cases],
            ["xfast-v3-greeting", "xfast-batched-edit"],
        )
        for case in cases:
            self.assertEqual(case.comparison, "ufast")
            self.assertEqual(case.endpoint, "execute")
            self.assertTrue(
                (ROOT / "benchmarks" / "fixtures" / case.fixture).is_dir()
            )
            self.assertEqual(
                {criterion.evaluator for criterion in case.criteria},
                {"judge", "file", "command"},
            )

    def test_luna_high_one_rep_plans_four_runs(self):
        config = load_config(CONFIG)

        self.assertEqual(config["agents"], ["codex"])
        self.assertEqual(config["models"], {"codex": "gpt-5.6-luna"})
        self.assertEqual(config["target"]["id"], "gpt-5.6-luna-high")
        self.assertEqual(config["target"]["reasoning_effort"], "high")
        self.assertEqual(config["judge"]["model"], "gpt-5.6-luna")
        self.assertEqual(config["judge"]["reasoning_effort"], "high")
        self.assertEqual(config["repetitions"], 1)
        self.assertEqual(config["parallelism"], 1)
        self.assertEqual(
            config["conditions"],
            {"ufast": ["nerd-xfast", "nerd-ufast"]},
        )

        runs = schedule_runs(config, ROOT / "benchmarks" / "work" / "ufast-v1")

        self.assertEqual(len(runs), 4)
        self.assertEqual({run.repetition for run in runs}, {1})
        self.assertEqual(
            {run.case_id for run in runs},
            {"ufast-v1-low-complexity", "ufast-v1-high-complexity"},
        )
        self.assertEqual(
            {run.condition for run in runs},
            {"nerd-xfast", "nerd-ufast"},
        )
        self.assertEqual({run.model for run in runs}, {"gpt-5.6-luna"})
        self.assertEqual({run.reasoning_effort for run in runs}, {"high"})

    def test_conditions_are_self_contained_and_isolated(self):
        self.assertEqual(
            condition_prompt("nerd-xfast", "Do the task."),
            "Use $nerd-xfast.\n\nDo the task.",
        )
        self.assertEqual(
            condition_prompt("nerd-ufast", "Do the task."),
            "Use $nerd-ufast.\n\nDo the task.",
        )

        case = load_cases(PILOT / "cases.json")[1]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            xfast = materialize_run(case, "nerd-xfast", "codex", base / "xfast")
            ufast = materialize_run(case, "nerd-ufast", "codex", base / "ufast")
            self.assertEqual(
                {path.name for path in (xfast / ".agents" / "skills").iterdir()},
                {"nerd-xfast"},
            )
            self.assertEqual(
                {path.name for path in (ufast / ".agents" / "skills").iterdir()},
                {"nerd-ufast"},
            )
            for condition, workspace in (
                ("nerd-xfast", xfast),
                ("nerd-ufast", ufast),
            ):
                command = get_adapter("codex").build_command(
                    make_spec(workspace, condition),
                    "Do the task.",
                )
                self.assertIn("--ignore-user-config", command)
                self.assertIn("--ignore-rules", command)

    def test_directional_report_and_feedback_trace_are_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(Path(temporary))
            summary = summarize_ufast(result)
            trace = build_feedback_trace(result, summary)
            markdown = render_feedback_markdown(trace)

        self.assertEqual(summary["aggregate"]["pairs"], 2)
        self.assertEqual(summary["aggregate"]["ufast"]["mean_score"], 100.0)
        self.assertEqual(summary["aggregate"]["xfast"]["mean_score"], 100.0)
        self.assertEqual(summary["aggregate"]["delta"]["speed_percent"], 50.0)
        self.assertEqual(
            summary["aggregate"]["delta"]["token_saved_percent"], 55.0
        )
        self.assertEqual(
            set(trace["traces"]), {"nerd-xfast", "nerd-ufast"}
        )
        self.assertEqual(trace["task"]["id"], "ufast-v1-high-complexity")
        self.assertEqual(trace["traces"]["nerd-ufast"]["tool_calls"], 2)
        self.assertEqual(trace["traces"]["nerd-ufast"]["turns_observed"], 1)
        self.assertEqual(trace["traces"]["nerd-ufast"]["input_tokens"], 1200)
        self.assertIsNone(trace["traces"]["nerd-ufast"]["llm_calls"])
        self.assertNotIn("/Users/", json.dumps(trace))
        self.assertIn("Complete Observable Trace", markdown)
        self.assertIn("Unavailable Runtime Internals", markdown)
        self.assertIn("directional", markdown.casefold())
        self.assertNotIn("/tmp/", markdown)

    def test_writes_all_artifacts_without_overwriting_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            result = write_result_fixture(base)
            summary_path = base / "result.json"
            trace_path = base / "trace.json"
            feedback_path = base / "feedback.md"
            expected = write_ufast_artifacts(
                result,
                summary_path,
                trace_path,
                feedback_path,
            )
            self.assertEqual(json.loads(summary_path.read_text()), expected)
            self.assertTrue(trace_path.is_file())
            self.assertTrue(feedback_path.is_file())
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                write_ufast_artifacts(
                    result,
                    summary_path,
                    trace_path,
                    feedback_path,
                )

    def test_cli_exposes_ufast_report(self):
        args = build_parser().parse_args(
            [
                "ufast-report",
                "--results",
                "results",
                "--output",
                "result.json",
                "--trace-output",
                "trace.json",
                "--feedback-output",
                "feedback.md",
            ]
        )
        self.assertEqual(args.command, "ufast-report")


if __name__ == "__main__":
    unittest.main()
