from pathlib import Path
from unittest.mock import patch
import json
import os
import tempfile
import unittest

from benchmarks.nerdbench.runner import load_config, schedule_runs


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "benchmarks" / "pilots" / "smart-principle-two-cases"
CASE_IDS = {"smart-principle-dry", "smart-principle-yagni"}
COMPARISON = "smart-principle"
CONDITIONS = ["nerd-smart-baseline", "nerd-smart"]
TARGETS = {
    "claude-sonnet-4-6-medium": "claude-sonnet-4-6",
    "claude-opus-4-8-medium": "claude-opus-4-8",
}


class SmartPrinciplePilotTests(unittest.TestCase):
    def test_case_bundle_pairs_a_dry_case_with_a_yagni_case(self):
        payload = json.loads((PILOT_DIR / "cases.json").read_text())
        cases = {case["id"]: case for case in payload["cases"]}
        self.assertEqual(set(cases), CASE_IDS)
        self.assertEqual(
            cases["smart-principle-dry"]["fixture"], "smart-principle-duplication"
        )
        self.assertIsNone(cases["smart-principle-yagni"]["fixture"])
        for case in cases.values():
            self.assertEqual(case["comparison"], COMPARISON)
            self.assertEqual(case["endpoint"], "plan")
            self.assertTrue(any(item["hard_gate"] for item in case["criteria"]))

    def test_each_run_gets_a_private_scratch_directory(self):
        from benchmarks.nerdbench.runner import (
            isolated_codex_environment,
            schedule_runs,
        )

        config = load_config(PILOT_DIR / "claude-sonnet-4-6-medium.json")
        runs = schedule_runs(config, ROOT / "benchmarks/work/principle-scratch-test")
        shared = dict(os.environ)
        scratches = []
        for spec in runs:
            with isolated_codex_environment(spec, shared) as environment:
                for key in ("TMPDIR", "TMP", "TEMP"):
                    self.assertNotEqual(environment[key], shared.get(key))
                self.assertTrue(Path(environment["TMPDIR"]).is_dir())
                scratches.append(environment["TMPDIR"])
        # A plan written by one run must not be visible to the next.
        self.assertEqual(len(set(scratches)), len(runs))

    def test_prerun_cleanup_removes_only_named_paths(self):
        from benchmarks.nerdbench import runner

        with tempfile.TemporaryDirectory() as directory:
            owned = Path(directory) / "orders-coupon-min-length-plan.md"
            bystander = Path(directory) / "unrelated-user-file.md"
            owned.write_text("stale plan", encoding="utf-8")
            bystander.write_text("do not touch", encoding="utf-8")

            with patch.object(runner, "PRERUN_CLEANUP_PATHS", (owned,)):
                removed = runner._clear_leaked_artifacts()
                self.assertEqual(removed, [str(owned)])
                self.assertFalse(owned.exists())
                self.assertTrue(bystander.exists())
                # Idempotent: a clean start reports nothing removed.
                self.assertEqual(runner._clear_leaked_artifacts(), [])

    def test_cleanup_paths_are_exact_files_not_globs(self):
        from benchmarks.nerdbench.runner import PRERUN_CLEANUP_PATHS

        self.assertTrue(PRERUN_CLEANUP_PATHS)
        for path in PRERUN_CLEANUP_PATHS:
            self.assertTrue(path.is_absolute())
            for wildcard in ("*", "?", "["):
                self.assertNotIn(wildcard, str(path))

    def test_every_registry_knows_the_baseline_condition(self):
        from benchmarks.nerdbench.materialize import (
            LOCAL_CONDITIONS,
            OUT_OF_TREE_SKILL_SOURCES,
        )
        from benchmarks.nerdbench.runner import CONDITION_SKILLS
        from benchmarks.nerdbench.scorer import PAIR_CONDITIONS

        self.assertIn("nerd-smart-baseline", LOCAL_CONDITIONS)
        self.assertIn("nerd-smart-baseline", OUT_OF_TREE_SKILL_SOURCES)
        # Both arms must be invoked identically, or the pair measures the
        # invocation rather than the skill body.
        self.assertEqual(
            CONDITION_SKILLS["nerd-smart-baseline"], CONDITION_SKILLS["nerd-smart"]
        )
        self.assertEqual(set(PAIR_CONDITIONS[COMPARISON]), set(CONDITIONS))

    def test_duplication_fixture_repeats_the_rule_at_three_call_sites(self):
        source = (
            ROOT
            / "benchmarks"
            / "fixtures"
            / "smart-principle-duplication"
            / "orders.py"
        ).read_text(encoding="utf-8")
        self.assertEqual(source.count("len(coupon) < 4 or not coupon.isalnum()"), 3)

    def test_every_target_plans_four_paired_medium_runs(self):
        for target_id, model in TARGETS.items():
            config = load_config(PILOT_DIR / f"{target_id}.json")
            self.assertEqual(
                config["case_files"],
                ["benchmarks/pilots/smart-principle-two-cases/cases.json"],
            )
            self.assertEqual(config["repetitions"], 1)
            self.assertEqual(config["target"]["id"], target_id)
            self.assertEqual(config["target"]["reasoning_effort"], "medium")
            self.assertEqual(config["agents"], ["claude"])
            self.assertEqual(config["models"], {"claude": model})
            self.assertEqual(config["conditions"], {COMPARISON: CONDITIONS})
            runs = schedule_runs(config, ROOT / "benchmarks/work/principle-pilot-test")
            self.assertEqual(len(runs), 4)
            self.assertEqual({run.case_id for run in runs}, CASE_IDS)
            self.assertEqual({run.condition for run in runs}, set(CONDITIONS))
            self.assertEqual({run.repetition for run in runs}, {1})


if __name__ == "__main__":
    unittest.main()
