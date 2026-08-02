from pathlib import Path
import json
import tempfile
import unittest

from benchmarks.nerdbench.adapters import get_adapter
from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.materialize import materialize_run
from benchmarks.nerdbench.models import RunSpec
from benchmarks.nerdbench.runner import condition_prompt, load_config, schedule_runs
from benchmarks.nerdbench.xfast_report import (
    XFAST_END,
    XFAST_START,
    publish_xfast_readme,
    render_xfast_readme,
    summarize_xfast,
    write_xfast_summary,
)
from benchmarks.run import build_parser


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "cases" / "xfast.json"
PILOT = ROOT / "benchmarks" / "pilots" / "xfast-vs-fast"
V2_PILOT = ROOT / "benchmarks" / "pilots" / "xfast-v2-one-case"
V3_PILOT = ROOT / "benchmarks" / "pilots" / "xfast-v3-five-cases"
TARGETS = {
    "Luna": ("gpt-5.6-luna-high", "gpt-5.6-luna"),
    "Terra": ("gpt-5.6-terra-high", "gpt-5.6-terra"),
    "Sol": ("gpt-5.6-sol-high", "gpt-5.6-sol"),
}


def make_spec(workspace: Path, condition: str) -> RunSpec:
    return RunSpec(
        run_id="xfast-test",
        case_id="xfast-batched-edit",
        condition=condition,
        agent="codex",
        model="gpt-5.6-sol",
        repetition=1,
        workspace=workspace,
        target_id="gpt-5.6-sol-high",
        reasoning_effort="high",
    )


def write_result_fixture(
    root: Path,
    label: str,
    target_id: str,
    model: str,
    *,
    missing_tokens: bool = False,
    case_file: str = "benchmarks/cases/xfast.json",
    case_ids: tuple[str, ...] = (
        "xfast-batched-edit",
        "xfast-discovery-edit",
    ),
    repetitions: int = 2,
) -> Path:
    result = root / label.casefold()
    result.mkdir()
    run_id = f"pilot-{label.casefold()}"
    manifest = {
        "run_id": run_id,
        "created_at": "2026-08-03T00:00:00+00:00",
        "nerd_commit": "deadbeef",
        "agent_versions": {"codex": "codex-cli test"},
        "config": {
            "agents": ["codex"],
            "models": {"codex": model},
            "target": {
                "id": target_id,
                "display_name": f"GPT 5.6 {label} · high · XFast",
                "reasoning_effort": "high",
            },
            "case_files": [case_file],
            "conditions": {
                "xfast": ["xfast-baseline", "nerd-xfast"],
            },
            "repetitions": repetitions,
            "parallelism": 1,
            "seed": 7152026,
        },
    }
    raw = []
    scores = []
    for case_id in case_ids:
        for repetition in range(1, repetitions + 1):
            for condition in ("xfast-baseline", "nerd-xfast"):
                treatment = condition == "nerd-xfast"
                record_id = f"{target_id}-{case_id}-r{repetition}-{condition}"
                raw.append(
                    {
                        "run_id": record_id,
                        "case_id": case_id,
                        "condition": condition,
                        "agent": "codex",
                        "model": model,
                        "target_id": target_id,
                        "reasoning_effort": "high",
                        "repetition": repetition,
                        "exit_code": 0,
                        "elapsed_seconds": 6.0 if treatment else 10.0,
                        "output_tokens": None
                        if missing_tokens and treatment
                        else (500 if treatment else 1000),
                        "events": [],
                        "changed_files": [],
                        "command_results": {},
                    }
                )
                scores.append(
                    {
                        "run_id": record_id,
                        "score": 90.0 if treatment else 100.0,
                        "passed": True,
                        "hard_gate_failures": [],
                        "criterion_results": {},
                        "judge_valid": True,
                    }
                )
    (result / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (result / "raw.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in raw),
        encoding="utf-8",
    )
    (result / "scores.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in scores),
        encoding="utf-8",
    )
    return result


def write_matrix(
    root: Path,
    *,
    missing_tokens: bool = False,
    case_file: str = "benchmarks/cases/xfast.json",
    case_ids: tuple[str, ...] = (
        "xfast-batched-edit",
        "xfast-discovery-edit",
    ),
    repetitions: int = 2,
) -> list[Path]:
    return [
        write_result_fixture(
            root,
            label,
            target_id,
            model,
            missing_tokens=missing_tokens,
            case_file=case_file,
            case_ids=case_ids,
            repetitions=repetitions,
        )
        for label, (target_id, model) in TARGETS.items()
    ]


class XFastCorpusTests(unittest.TestCase):
    def test_has_exactly_two_multi_file_cases(self):
        cases = load_cases(CASES)
        self.assertEqual(
            {case.id for case in cases},
            {"xfast-batched-edit", "xfast-discovery-edit"},
        )
        self.assertTrue(all(case.comparison == "xfast" for case in cases))
        self.assertTrue(all(case.endpoint == "execute" for case in cases))
        for case in cases:
            evaluators = {criterion.evaluator for criterion in case.criteria}
            self.assertIn("judge", evaluators)
            self.assertIn("command", evaluators)
            self.assertIn("file", evaluators)
            self.assertEqual(sum(item.weight for item in case.criteria), 100)

    def test_v2_case_is_outcome_only(self):
        cases = load_cases(V2_PILOT / "cases.json")
        self.assertEqual([case.id for case in cases], ["xfast-v2-batched-edit"])
        prompt = cases[0].prompt.casefold()
        for leaked_instruction in (
            "one edit set",
            "finish all edits",
            "focused read pass",
            "then run",
            "python3",
        ):
            self.assertNotIn(leaked_instruction, prompt)

    def test_v3_has_five_outcome_only_independently_proven_cases(self):
        cases = load_cases(V3_PILOT / "cases.json")
        self.assertEqual(len(cases), 5)
        self.assertEqual(len({case.id for case in cases}), 5)
        for case in cases:
            self.assertEqual(case.comparison, "xfast")
            evaluators = {criterion.evaluator for criterion in case.criteria}
            self.assertEqual(evaluators, {"judge", "file", "command"})
            prompt = case.prompt.casefold()
            for leaked_instruction in (
                "one edit set",
                "finish all edits",
                "focused read pass",
                "then run",
                "python3",
            ):
                self.assertNotIn(leaked_instruction, prompt)


class XFastConditionTests(unittest.TestCase):
    def test_prompts_compose_regular_fast_but_xfast_is_self_contained(self):
        self.assertEqual(
            condition_prompt("xfast-baseline", "Do the task."),
            "Use $nerd-smart and $nerd-execute and $nerd-fast.\n\nDo the task.",
        )
        self.assertEqual(
            condition_prompt("nerd-xfast", "Do the task."),
            "Use $nerd-xfast.\n\nDo the task.",
        )

    def test_materialized_skill_sets_are_exact(self):
        case = load_cases(CASES)[0]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            regular = materialize_run(
                case,
                "xfast-baseline",
                "codex",
                base / "regular",
            )
            xfast = materialize_run(
                case,
                "nerd-xfast",
                "codex",
                base / "xfast",
            )
            regular_skills = regular / ".agents" / "skills"
            xfast_skills = xfast / ".agents" / "skills"
            self.assertEqual(
                {path.name for path in regular_skills.iterdir()},
                {"nerd-smart", "nerd-execute", "nerd-fast"},
            )
            self.assertEqual(
                {path.name for path in xfast_skills.iterdir()},
                {"nerd-xfast"},
            )

    def test_both_arms_ignore_user_configuration(self):
        adapter = get_adapter("codex")
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            for condition in ("xfast-baseline", "nerd-xfast"):
                command = adapter.build_command(
                    make_spec(workspace, condition),
                    "Do the task.",
                )
                self.assertIn("--ignore-user-config", command)
                self.assertIn("--ignore-rules", command)
                self.assertIn('model_reasoning_effort="high"', command)


class XFastConfigTests(unittest.TestCase):
    def test_three_high_configs_plan_twenty_four_fresh_runs(self):
        all_run_ids = set()
        for label, (target_id, model) in TARGETS.items():
            config = load_config(PILOT / f"{target_id}.json")
            self.assertEqual(config["agents"], ["codex"])
            self.assertEqual(config["models"], {"codex": model})
            self.assertEqual(config["target"]["id"], target_id)
            self.assertEqual(config["target"]["reasoning_effort"], "high")
            self.assertEqual(config["repetitions"], 2)
            self.assertEqual(config["parallelism"], 1)
            self.assertEqual(
                config["conditions"],
                {"xfast": ["xfast-baseline", "nerd-xfast"]},
            )
            runs = schedule_runs(config, ROOT / "benchmarks" / "work" / label)
            self.assertEqual(len(runs), 8)
            self.assertEqual({run.repetition for run in runs}, {1, 2})
            self.assertEqual(
                {run.condition for run in runs},
                {"xfast-baseline", "nerd-xfast"},
            )
            self.assertTrue(all(run.run_id not in all_run_ids for run in runs))
            all_run_ids.update(run.run_id for run in runs)
        self.assertEqual(len(all_run_ids), 24)

    def test_v2_three_high_configs_plan_six_fresh_runs(self):
        all_run_ids = set()
        for label, (target_id, model) in TARGETS.items():
            config = load_config(V2_PILOT / f"{target_id}.json")
            self.assertEqual(config["models"], {"codex": model})
            self.assertEqual(config["target"]["reasoning_effort"], "high")
            self.assertEqual(config["repetitions"], 1)
            self.assertEqual(config["parallelism"], 1)
            runs = schedule_runs(config, ROOT / "benchmarks" / "work" / f"v2-{label}")
            self.assertEqual(len(runs), 2)
            self.assertEqual({run.repetition for run in runs}, {1})
            self.assertEqual(
                {run.condition for run in runs},
                {"xfast-baseline", "nerd-xfast"},
            )
            self.assertTrue(all(run.run_id not in all_run_ids for run in runs))
            all_run_ids.update(run.run_id for run in runs)
        self.assertEqual(len(all_run_ids), 6)

    def test_v3_three_high_configs_plan_thirty_fresh_runs(self):
        all_run_ids = set()
        for label, (target_id, model) in TARGETS.items():
            config = load_config(V3_PILOT / f"{target_id}.json")
            self.assertEqual(config["models"], {"codex": model})
            self.assertEqual(config["target"]["reasoning_effort"], "high")
            self.assertEqual(config["repetitions"], 1)
            self.assertEqual(config["parallelism"], 1)
            runs = schedule_runs(config, ROOT / "benchmarks" / "work" / f"v3-{label}")
            self.assertEqual(len(runs), 10)
            self.assertEqual({run.repetition for run in runs}, {1})
            self.assertEqual(
                {run.condition for run in runs},
                {"xfast-baseline", "nerd-xfast"},
            )
            self.assertTrue(all(run.run_id not in all_run_ids for run in runs))
            all_run_ids.update(run.run_id for run in runs)
        self.assertEqual(len(all_run_ids), 30)


class XFastReportTests(unittest.TestCase):
    def test_summarizes_four_pairs_per_model_and_twelve_combined(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_xfast(write_matrix(Path(temporary)))
        self.assertEqual(summary["aggregate"]["pairs"], 12)
        self.assertEqual(summary["models"]["Luna"]["pairs"], 4)
        self.assertEqual(summary["models"]["Luna"]["fast"]["mean_score"], 100.0)
        self.assertEqual(summary["models"]["Luna"]["xfast"]["mean_score"], 90.0)
        self.assertEqual(
            summary["models"]["Luna"]["delta"]["accuracy_points"],
            -10.0,
        )
        self.assertEqual(
            summary["models"]["Luna"]["delta"]["speed_percent"],
            40.0,
        )
        self.assertEqual(
            summary["models"]["Luna"]["delta"]["token_saved_percent"],
            50.0,
        )
        self.assertTrue(summary["controls"]["fresh_isolated_agents"])
        self.assertEqual(summary["provenance"]["models"]["Sol"], "gpt-5.6-sol")
        self.assertIn("directional", " ".join(summary["limitations"]).casefold())

    def test_summarizes_v2_one_pair_per_model_and_three_combined(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_xfast(
                write_matrix(
                    Path(temporary),
                    case_file="benchmarks/pilots/xfast-v2-one-case/cases.json",
                    case_ids=("xfast-v2-batched-edit",),
                    repetitions=1,
                )
            )
        self.assertEqual(summary["comparison"], "xfast-v2-vs-fast")
        self.assertEqual(summary["aggregate"]["pairs"], 3)
        self.assertEqual(summary["models"]["Luna"]["pairs"], 1)
        self.assertEqual(summary["controls"]["cases"], 1)
        self.assertEqual(summary["controls"]["repetitions_per_model"], 1)
        rendered = render_xfast_readme(summary)
        self.assertIn("one coding case and one repetition", rendered)
        self.assertIn("xfast-v2-one-case/result.json", rendered)

    def test_summarizes_v3_five_pairs_per_model_and_fifteen_combined(self):
        case_ids = (
            "xfast-v3-batched-edit",
            "xfast-v3-discovery-edit",
            "xfast-v3-independent-work",
            "xfast-v3-greeting",
            "xfast-v3-slugify",
        )
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_xfast(
                write_matrix(
                    Path(temporary),
                    case_file="benchmarks/pilots/xfast-v3-five-cases/cases.json",
                    case_ids=case_ids,
                    repetitions=1,
                )
            )
        self.assertEqual(summary["comparison"], "xfast-v3-vs-fast")
        self.assertEqual(summary["aggregate"]["pairs"], 15)
        self.assertEqual(summary["models"]["Luna"]["pairs"], 5)
        self.assertEqual(summary["controls"]["cases"], 5)
        rendered = render_xfast_readme(summary)
        self.assertIn("5 cases and one repetition", rendered)
        self.assertIn("xfast-v3-five-cases/result.json", rendered)

    def test_missing_tokens_are_unavailable_not_estimated(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_xfast(
                write_matrix(Path(temporary), missing_tokens=True)
            )
        self.assertIsNone(
            summary["aggregate"]["delta"]["token_saved_percent"]
        )
        self.assertIn("Unavailable", render_xfast_readme(summary))

    def test_writes_summary_without_overwriting_different_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            results = write_matrix(base)
            output = base / "result.json"
            expected = write_xfast_summary(results, output)
            self.assertEqual(json.loads(output.read_text()), expected)
            output.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                write_xfast_summary(results, output)

    def test_publishes_one_checked_readme_region_with_accuracy_warning(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            summary = summarize_xfast(write_matrix(base))
            readme = base / "README.md"
            readme.write_text("# Demo\n\n## Benchmarks\n\nOld.\n", encoding="utf-8")
            publish_xfast_readme(summary, readme)
            body = readme.read_text(encoding="utf-8")
            self.assertEqual(body.count(XFAST_START), 1)
            self.assertEqual(body.count(XFAST_END), 1)
            self.assertEqual(body.count("## Now available xfast!"), 1)
            self.assertIn("intentionally trades accuracy", body)
            self.assertIn("two cases and two repetitions", body)
            self.assertIn("fresh isolated Codex process", body)
            self.assertIn("`high` reasoning effort", body)
            self.assertIn("40.00% faster", body)
            self.assertLess(body.index("| Terra |"), body.index("| Sol |"))
            self.assertLess(body.index("## Benchmarks"), body.index(XFAST_START))
            self.assertTrue(body.rstrip().endswith(XFAST_END))
            publish_xfast_readme(summary, readme, check=True)
            readme.write_text(body.replace("40.00%", "39.00%", 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "out of date"):
                publish_xfast_readme(summary, readme, check=True)

    def test_cli_requires_three_results_and_explicit_summary(self):
        parser = build_parser()
        report = parser.parse_args(
            [
                "xfast-report",
                "--results",
                "luna",
                "terra",
                "sol",
                "--output",
                "result.json",
            ]
        )
        self.assertEqual(report.results, ["luna", "terra", "sol"])
        self.assertEqual(report.output, "result.json")
        publish = parser.parse_args(
            [
                "xfast-publish",
                "--summary",
                "result.json",
                "--readme",
                "README.md",
                "--check",
            ]
        )
        self.assertTrue(publish.check)


if __name__ == "__main__":
    unittest.main()
