from pathlib import Path
import json
import unittest

from benchmarks.nerdbench.runner import load_config, schedule_runs


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "benchmarks" / "pilots" / "gpt-smart-complex-one-case"
CASE_ID = "smart-complex-pressure"
TARGETS = {
    "gpt-5.6-sol-xhigh": "gpt-5.6-sol",
    "gpt-5.6-terra-xhigh": "gpt-5.6-terra",
    "gpt-5.6-luna-xhigh": "gpt-5.6-luna",
    "gpt-5.5-xhigh": "gpt-5.5",
}


class GptSmartComplexPilotTests(unittest.TestCase):
    def test_case_is_new_complex_and_judgeable(self):
        cases_path = PILOT_DIR / "cases.json"
        self.assertTrue(cases_path.is_file())
        payload = json.loads(cases_path.read_text())
        self.assertEqual(len(payload["cases"]), 1)
        case = payload["cases"][0]
        self.assertEqual(case["id"], CASE_ID)
        self.assertEqual(case["comparison"], "smart")
        self.assertIsNone(case["fixture"])
        self.assertEqual(case["endpoint"], "discuss")
        self.assertEqual(sum(item["weight"] for item in case["criteria"]), 100)
        self.assertTrue(any(item["evaluator"] == "judge" for item in case["criteria"]))
        self.assertTrue(any(item["hard_gate"] for item in case["criteria"]))

        public_cases = json.loads((ROOT / "benchmarks/cases/smart.json").read_text())
        self.assertNotIn(CASE_ID, {item["id"] for item in public_cases["cases"]})

    def test_four_gpt_targets_plan_two_candidates_and_one_judge_pair(self):
        total_candidates = 0
        for target_id, model in TARGETS.items():
            config_path = PILOT_DIR / f"{target_id}.json"
            self.assertTrue(config_path.is_file())
            config = load_config(config_path)
            self.assertEqual(config["agents"], ["codex"])
            self.assertEqual(config["models"], {"codex": model})
            self.assertEqual(config["target"]["id"], target_id)
            self.assertEqual(config["target"]["reasoning_effort"], "xhigh")
            self.assertEqual(config["repetitions"], 1)
            self.assertEqual(
                config["case_files"],
                ["benchmarks/pilots/gpt-smart-complex-one-case/cases.json"],
            )
            self.assertEqual(
                config["conditions"],
                {"smart": ["nerd-smart", "superpowers-brainstorming"]},
            )
            runs = schedule_runs(config, ROOT / "benchmarks/work/smart-complex-test")
            self.assertEqual(len(runs), 2)
            self.assertEqual({run.case_id for run in runs}, {CASE_ID})
            self.assertEqual(
                {run.condition for run in runs},
                {"nerd-smart", "superpowers-brainstorming"},
            )
            total_candidates += len(runs)
        self.assertEqual(total_candidates, 8)


if __name__ == "__main__":
    unittest.main()
