from pathlib import Path
import unittest

from benchmarks.nerdbench.runner import _smoke_specs, load_config, schedule_runs


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "benchmarks" / "configs"
TARGETS = {
    "gpt-5.6-sol-xhigh": ("codex", "gpt-5.6-sol", "xhigh"),
    "gpt-5.6-terra-xhigh": ("codex", "gpt-5.6-terra", "xhigh"),
    "gpt-5.6-luna-xhigh": ("codex", "gpt-5.6-luna", "xhigh"),
    "gpt-5.5-xhigh": ("codex", "gpt-5.5", "xhigh"),
    "claude-fable-5-xhigh": ("claude", "claude-fable-5", "xhigh"),
    "claude-opus-4-8-xhigh": ("claude", "claude-opus-4-8", "xhigh"),
    "claude-sonnet-5-xhigh": ("claude", "claude-sonnet-5", "xhigh"),
    "claude-haiku-4-5": ("claude", "claude-haiku-4-5", None),
}


class BenchmarkMatrixTests(unittest.TestCase):
    def test_exact_target_configs_plan_120_unique_runs_each(self):
        all_run_ids = set()
        for target_id, (agent, model, effort) in TARGETS.items():
            config_path = CONFIG_DIR / f"{target_id}.json"
            self.assertTrue(config_path.is_file(), config_path)
            config = load_config(config_path)
            self.assertEqual(config["target"]["id"], target_id)
            self.assertEqual(config["target"]["reasoning_effort"], effort)
            self.assertEqual(config["agents"], [agent])
            self.assertEqual(config["models"], {agent: model})
            runs = schedule_runs(config, ROOT / "benchmarks/work/matrix-test")
            self.assertEqual(len(runs), 120)
            self.assertEqual(len({item.run_id for item in runs}), 120)
            self.assertTrue(all(item.target_id == target_id for item in runs))
            self.assertTrue(all(item.reasoning_effort == effort for item in runs))
            self.assertTrue(all(item.run_id not in all_run_ids for item in runs))
            all_run_ids.update(item.run_id for item in runs)
            self.assertEqual(len(_smoke_specs(runs)), 8)
        self.assertEqual(len(all_run_ids), 960)

    def test_all_targets_share_one_pinned_judge(self):
        judges = {
            tuple(sorted(load_config(path)["judge"].items()))
            for path in CONFIG_DIR.glob("*.json")
        }
        self.assertEqual(len(judges), 1)
        judge = dict(next(iter(judges)))
        self.assertEqual(judge["agent"], "codex")
        self.assertEqual(judge["model"], "gpt-5.6-terra")
        self.assertEqual(judge["reasoning_effort"], "xhigh")


if __name__ == "__main__":
    unittest.main()
