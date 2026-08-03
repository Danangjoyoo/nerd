from pathlib import Path
import tempfile
import unittest

from benchmarks.nerdbench.adapters import get_adapter
from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.materialize import materialize_run
from benchmarks.nerdbench.models import RunSpec
from benchmarks.nerdbench.runner import (
    _ufast_source_hashes,
    condition_prompt,
    isolated_codex_environment,
)
from benchmarks.nerdbench.ufast_report import current_source_hashes


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "cases" / "ufast-phase1-verification.json"


def spec(workspace: Path, condition: str) -> RunSpec:
    return RunSpec(
        run_id=f"ufast-test-{condition}",
        case_id="xfast-v3-discovery-edit",
        condition=condition,
        agent="codex",
        model="gpt-5.6-luna",
        repetition=1,
        workspace=workspace,
        target_id="gpt-5.6-luna-high",
        reasoning_effort="high",
    )


class UFastConditionTests(unittest.TestCase):
    def test_runner_and_reporter_share_one_frozen_prompt_source_set(self):
        config = {"conditions": {"xfast": ["nerd-xfast", "nerd-ufast"]}}
        hashes = current_source_hashes()
        self.assertEqual(_ufast_source_hashes(config), hashes)
        self.assertEqual(
            set(hashes),
            {
                "case_corpus",
                "xfast_skill",
                "ufast_skill",
                "benchmark_runner",
                "benchmark_materialize",
                "benchmark_adapters",
                "benchmark_scorer",
                "ufast_report",
            },
        )
        self.assertIsNone(
            _ufast_source_hashes({"conditions": {"xfast": ["nerd-xfast"]}})
        )

    def test_prompt_and_materialized_skill_sets_are_exact(self):
        self.assertEqual(
            condition_prompt("nerd-ufast", "Do the task."),
            (
                "Use $nerd-smart and $nerd-execute and $nerd-ufast.\n\n"
                "Do the task."
            ),
        )
        case = load_cases(CASES)[0]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            ufast = materialize_run(case, "nerd-ufast", "codex", base / "ufast")
            xfast = materialize_run(case, "nerd-xfast", "codex", base / "xfast")
            self.assertEqual(
                {path.name for path in (ufast / ".agents" / "skills").iterdir()},
                {"nerd-smart", "nerd-execute", "nerd-ufast"},
            )
            self.assertEqual(
                {path.name for path in (xfast / ".agents" / "skills").iterdir()},
                {"nerd-xfast"},
            )
            self.assertFalse(
                (ufast / ".agents" / "skills" / "nerd-ufast" / "scripts").exists()
            )

    def test_both_prompt_conditions_ignore_user_config_and_add_no_runtime(self):
        adapter = get_adapter("codex")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for condition in ("nerd-ufast", "nerd-xfast"):
                workspace = base / condition
                workspace.mkdir()
                run_spec = spec(workspace, condition)
                command = adapter.build_command(run_spec, "Do the task.")
                self.assertIn("--ignore-rules", command)
                self.assertIn("--ignore-user-config", command)

                with isolated_codex_environment(run_spec, environ={}) as environment:
                    isolated_home = Path(environment["CODEX_HOME"])
                    self.assertFalse((isolated_home / "config.toml").exists())
                    self.assertNotIn("NERD_UFAST_WORKSPACE", environment)
                    self.assertNotIn("NERD_UFAST_LOG", environment)


if __name__ == "__main__":
    unittest.main()
