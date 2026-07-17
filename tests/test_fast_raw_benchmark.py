from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.nerdbench.adapters import get_adapter
from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.materialize import materialize_run
from benchmarks.nerdbench.models import RunSpec
from benchmarks.nerdbench.pair_report import (
    FAST_RAW_END,
    FAST_RAW_START,
    publish_fast_raw_readme,
    render_fast_raw_readme,
    summarize_pair,
    write_pair_summary,
)
from benchmarks.nerdbench.runner import (
    condition_prompt,
    isolated_codex_environment,
    load_config,
    schedule_runs,
)
from benchmarks.run import build_parser


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks" / "pilots" / "fast-raw-one-case"


def make_spec(workspace: Path, condition: str) -> RunSpec:
    return RunSpec(
        run_id="pilot",
        case_id="fast-raw-known-target",
        condition=condition,
        agent="codex",
        model="gpt-5.6-sol",
        repetition=1,
        workspace=workspace,
        target_id="gpt-5.6-sol-xhigh-fast-raw",
        reasoning_effort="xhigh",
    )


def write_result_fixture(
    root: Path,
    *,
    raw_overrides: dict[str, dict] | None = None,
    score_overrides: dict[str, dict] | None = None,
) -> Path:
    result = root / "result"
    result.mkdir()
    manifest = {
        "run_id": "pilot-run",
        "created_at": "2026-07-17T00:00:00+00:00",
        "agent_versions": {"codex": "codex-cli 0.144.1"},
        "config": {
            "target": {
                "id": "gpt-5.6-sol-xhigh-fast-raw",
                "display_name": "GPT 5.6 Sol · xhigh · Fast raw smoke",
                "reasoning_effort": "xhigh",
            },
            "models": {"codex": "gpt-5.6-sol"},
            "conditions": {"fast-raw": ["raw-agent", "nerd-fast-only"]},
            "repetitions": 1,
        },
    }
    common = {
        "case_id": "fast-raw-known-target",
        "agent": "codex",
        "model": "gpt-5.6-sol",
        "target_id": "gpt-5.6-sol-xhigh-fast-raw",
        "reasoning_effort": "xhigh",
        "repetition": 1,
        "exit_code": 0,
    }
    raw = [
        {
            **common,
            "run_id": "raw",
            "condition": "raw-agent",
            "elapsed_seconds": 10.0,
            "output_tokens": 100,
            "events": [],
        },
        {
            **common,
            "run_id": "fast",
            "condition": "nerd-fast-only",
            "elapsed_seconds": 8.0,
            "output_tokens": 80,
            "events": [
                {
                    "type": "item.started",
                    "item": {
                        "command": "python3 .agents/skills/nerd-fast/scripts/"
                        "symbol_index.py ensure; rg --files"
                    },
                }
            ],
        },
    ]
    scores = [
        {
            "run_id": run_id,
            "score": 100.0,
            "passed": True,
            "hard_gate_failures": [],
            "judge_valid": True,
        }
        for run_id in ("raw", "fast")
    ]
    for record in raw:
        record.update((raw_overrides or {}).get(record["run_id"], {}))
    for score in scores:
        score.update((score_overrides or {}).get(score["run_id"], {}))
    (result / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
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


class FastRawConditionTests(unittest.TestCase):
    def test_prompts_are_raw_and_fast_only(self):
        self.assertEqual(condition_prompt("raw-agent", "Do the task."), "Do the task.")
        self.assertEqual(
            condition_prompt("nerd-fast-only", "Do the task."),
            "Use $nerd-fast.\n\nDo the task.",
        )

    def test_materialized_skill_sets_are_exact(self):
        case = load_cases(ROOT / "benchmarks" / "cases" / "fast.json")[0]
        with tempfile.TemporaryDirectory() as temporary:
            raw = materialize_run(case, "raw-agent", "codex", Path(temporary) / "raw")
            fast = materialize_run(
                case,
                "nerd-fast-only",
                "codex",
                Path(temporary) / "fast",
            )
            raw_skills = raw / ".agents" / "skills"
            fast_skills = fast / ".agents" / "skills"
            self.assertEqual(list(raw_skills.iterdir()), [])
            self.assertEqual(
                {path.name for path in fast_skills.iterdir()},
                {"nerd-fast"},
            )

    def test_isolated_codex_home_reuses_auth_without_user_skills(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source_home = base / "source"
            source_home.mkdir()
            (source_home / "auth.json").write_text("{}", encoding="utf-8")
            (source_home / "skills").mkdir()
            (source_home / "config.toml").write_text(
                "model='other'",
                encoding="utf-8",
            )
            user_home = base / "user"
            user_skills = user_home / ".agents" / "skills" / "nerd-silent"
            user_skills.mkdir(parents=True)
            (user_skills / "SKILL.md").write_text("private", encoding="utf-8")
            workspace = base / "workspace"
            workspace.mkdir()
            with isolated_codex_environment(
                make_spec(workspace, "raw-agent"),
                {"CODEX_HOME": str(source_home), "HOME": str(user_home)},
            ) as environment:
                isolated = Path(environment["CODEX_HOME"])
                self.assertNotEqual(isolated, source_home)
                self.assertEqual(Path(environment["HOME"]), isolated)
                self.assertTrue((isolated / "auth.json").is_symlink())
                self.assertFalse((isolated / "skills").exists())
                self.assertFalse((isolated / ".agents" / "skills").exists())
                self.assertFalse((isolated / "config.toml").exists())
            self.assertFalse(isolated.exists())

    def test_isolated_arms_ignore_user_config_without_changing_release_fast(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            adapter = get_adapter("codex")
            raw = adapter.build_command(make_spec(workspace, "raw-agent"), "task")
            fast_only = adapter.build_command(
                make_spec(workspace, "nerd-fast-only"),
                "task",
            )
            release_fast = adapter.build_command(
                make_spec(workspace, "nerd-fast"),
                "task",
            )
            for command in (raw, fast_only):
                self.assertIn("--ignore-user-config", command)
                self.assertIn("--ignore-rules", command)
            self.assertNotIn("--ignore-user-config", release_fast)
            self.assertNotIn("--ignore-rules", release_fast)


class FastRawPilotTests(unittest.TestCase):
    def test_pilot_is_one_complex_repository_summary_case(self):
        payload = json.loads((PILOT / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["cases"]), 1)
        case = payload["cases"][0]
        self.assertEqual(case["id"], "fast-raw-repository-summary")
        self.assertEqual(case["comparison"], "fast-raw")
        self.assertEqual(case["fixture"], "__repository__")
        self.assertEqual(sum(item["weight"] for item in case["criteria"]), 100)
        self.assertTrue(all(item["hard_gate"] for item in case["criteria"]))
        self.assertEqual(
            {item["evaluator"] for item in case["criteria"]},
            {"regex", "clean"},
        )

    def test_repository_snapshot_contains_current_project_and_no_raw_skills(self):
        case = load_cases(PILOT / "cases.json")[0]
        with tempfile.TemporaryDirectory() as temporary:
            with patch(
                "benchmarks.nerdbench.materialize.subprocess.run",
                wraps=subprocess.run,
            ) as run:
                workspace = materialize_run(
                    case,
                    "raw-agent",
                    "codex",
                    Path(temporary) / "repository",
                )
            self.assertTrue(
                any(
                    call.args[0]
                    == ["git", "ls-files", "-co", "--exclude-standard", "-z"]
                    for call in run.call_args_list
                )
            )
            for relative in (
                "README.md",
                "benchmarks/run.py",
                "skills/nerd-fast/SKILL.md",
                "tests/test_readme.py",
            ):
                self.assertTrue((workspace / relative).is_file(), relative)
            self.assertEqual(list((workspace / ".agents" / "skills").iterdir()), [])

    def test_pilot_plans_exactly_two_sol_xhigh_runs(self):
        config = load_config(PILOT / "gpt-5.6-sol-xhigh.json")
        runs = schedule_runs(
            config,
            ROOT / "benchmarks" / "work" / "pilot-test",
        )
        self.assertEqual(config["models"], {"codex": "gpt-5.6-sol"})
        self.assertEqual(config["target"]["reasoning_effort"], "xhigh")
        self.assertEqual(config["repetitions"], 1)
        self.assertEqual(config["parallelism"], 1)
        self.assertEqual(len(runs), 2)
        self.assertEqual(
            {run.condition for run in runs},
            {"raw-agent", "nerd-fast-only"},
        )
        self.assertEqual({run.repetition for run in runs}, {1})


class FastRawReportTests(unittest.TestCase):
    def test_summarizes_one_valid_pair(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_pair(write_result_fixture(Path(temporary)))
        self.assertEqual(summary["baseline"]["score"], 100.0)
        self.assertEqual(summary["treatment"]["score"], 100.0)
        self.assertTrue(summary["baseline"]["passed"])
        self.assertTrue(summary["treatment"]["passed"])
        self.assertEqual(summary["delta"]["latency_percent"], -20.0)
        self.assertEqual(summary["delta"]["output_tokens_percent"], -20.0)
        self.assertEqual(
            summary["controls"],
            {
                "raw_nerd_skill_access": False,
                "treatment_indexer_invoked": True,
            },
        )
        self.assertIn(
            "invoked the bundled symbol indexer",
            render_fast_raw_readme(summary),
        )

    def test_missing_tokens_are_unavailable_not_estimated(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(
                Path(temporary),
                raw_overrides={"fast": {"output_tokens": None}},
            )
            summary = summarize_pair(result)
        self.assertIsNone(summary["delta"]["output_tokens_percent"])
        self.assertIn("Unavailable", render_fast_raw_readme(summary))

    def test_rejects_raw_arm_that_accessed_an_external_nerd_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(
                Path(temporary),
                raw_overrides={
                    "raw": {
                        "events": [
                            {
                                "type": "item.started",
                                "item": {
                                    "command": "sed -n '1,80p' "
                                    "/Users/example/.agents/skills/"
                                    "nerd-silent/SKILL.md"
                                },
                            }
                        ]
                    }
                },
            )
            with self.assertRaisesRegex(ValueError, "raw arm accessed a Nerd skill"):
                summarize_pair(result)

    def test_rejects_fast_arm_that_did_not_run_the_indexer(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(
                Path(temporary),
                raw_overrides={
                    "fast": {
                        "events": [
                            {
                                "type": "item.started",
                                "item": {
                                    "command": "sed -n '1,80p' "
                                    ".agents/skills/nerd-fast/scripts/"
                                    "symbol_index.py"
                                },
                            }
                        ]
                    }
                },
            )
            with self.assertRaisesRegex(ValueError, "Fast arm did not run the indexer"):
                summarize_pair(result)

    def test_rejects_missing_arm_and_failed_accuracy(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(Path(temporary))
            lines = (result / "raw.jsonl").read_text(encoding="utf-8").splitlines()
            (result / "raw.jsonl").write_text(lines[0] + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one run per arm"):
                summarize_pair(result)

        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(
                Path(temporary),
                score_overrides={
                    "fast": {
                        "score": 40.0,
                        "passed": False,
                        "hard_gate_failures": ["proof"],
                    }
                },
            )
            with self.assertRaisesRegex(ValueError, "hard gate failed"):
                summarize_pair(result)

    def test_writes_summary_without_overwriting_different_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            result = write_result_fixture(base)
            output = base / "summary.json"
            expected = write_pair_summary(result, output)
            self.assertEqual(json.loads(output.read_text()), expected)
            output.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                write_pair_summary(result, output)

    def test_publishes_one_deterministic_readme_region(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            summary = summarize_pair(write_result_fixture(base))
            readme = base / "README.md"
            readme.write_text("# Demo\n\n### Method\n\nDetails.\n", encoding="utf-8")
            publish_fast_raw_readme(summary, readme)
            body = readme.read_text(encoding="utf-8")
            self.assertEqual(body.count(FAST_RAW_START), 1)
            self.assertEqual(body.count(FAST_RAW_END), 1)
            self.assertIn(render_fast_raw_readme(summary), body)
            publish_fast_raw_readme(summary, readme)
            self.assertEqual(readme.read_text(encoding="utf-8"), body)

    def test_cli_requires_exact_result_and_summary_paths(self):
        parser = build_parser()
        report = parser.parse_args(
            ["pair-report", "--results", "result-dir", "--output", "summary.json"]
        )
        self.assertEqual(report.results, "result-dir")
        self.assertEqual(report.output, "summary.json")
        self.assertFalse(report.overwrite)
        replacement = parser.parse_args(
            [
                "pair-report",
                "--results",
                "result-dir",
                "--output",
                "summary.json",
                "--overwrite",
            ]
        )
        self.assertTrue(replacement.overwrite)
        publish = parser.parse_args(
            ["pair-publish", "--summary", "summary.json", "--readme", "README.md"]
        )
        self.assertEqual(publish.summary, "summary.json")
        self.assertEqual(publish.readme, "README.md")
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["pair-report", "--latest", "--output", "summary.json"]
            )


if __name__ == "__main__":
    unittest.main()
