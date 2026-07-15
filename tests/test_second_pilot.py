from pathlib import Path
import json
import unittest

from benchmarks.nerdbench.runner import load_config, schedule_runs


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "benchmarks" / "pilots" / "second-one-case"
PROMPT = ROOT / "docs" / "prompts" / "claude-second-one-case.md"
SECOND_CASES = {
    "smart-compound-queue",
    "surgery-component-boundary",
    "execute-written-plan",
    "silent-code-only",
}
FIRST_CASES = {
    "smart-ambiguous-focus",
    "surgery-trace-source",
    "execute-blocker",
    "silent-final-only",
}
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


class SecondPilotTests(unittest.TestCase):
    def test_case_bundle_is_exact_and_does_not_overlap_first_pilot(self):
        payload = json.loads((PILOT_DIR / "cases.json").read_text())
        case_ids = {case["id"] for case in payload["cases"]}
        self.assertEqual(case_ids, SECOND_CASES)
        self.assertTrue(case_ids.isdisjoint(FIRST_CASES))
        self.assertEqual(len(payload["cases"]), 4)
        expected = {}
        for comparison in ("smart", "surgery", "execute", "silent"):
            source = json.loads(
                (ROOT / f"benchmarks/cases/{comparison}.json").read_text()
            )
            expected.update({case["id"]: case for case in source["cases"]})
        self.assertEqual(
            {case["id"]: case for case in payload["cases"]},
            {case_id: expected[case_id] for case_id in SECOND_CASES},
        )

    def test_every_target_plans_eight_direct_runs(self):
        for target_id, (agent, model, effort) in TARGETS.items():
            config = load_config(PILOT_DIR / f"{target_id}.json")
            self.assertEqual(config["case_files"], [
                "benchmarks/pilots/second-one-case/cases.json"
            ])
            self.assertEqual(config["repetitions"], 1)
            self.assertEqual(config["target"]["id"], target_id)
            self.assertEqual(config["target"]["reasoning_effort"], effort)
            self.assertEqual(config["agents"], [agent])
            self.assertEqual(config["models"], {agent: model})
            runs = schedule_runs(config, ROOT / "benchmarks/work/second-pilot-test")
            self.assertEqual(len(runs), 8)
            self.assertEqual(len({run.run_id for run in runs}), 8)
            self.assertEqual({run.case_id for run in runs}, SECOND_CASES)
            self.assertEqual({run.repetition for run in runs}, {1})

    def test_claude_prompt_is_direct_bounded_and_explicit(self):
        body = PROMPT.read_text(encoding="utf-8")
        for target_id in (
            "claude-fable-5-xhigh",
            "claude-opus-4-8-xhigh",
            "claude-sonnet-5-xhigh",
            "claude-haiku-4-5",
        ):
            self.assertIn(f"{target_id}.json", body)
        for value in (
            "--release",
            "8 planned agent runs",
            "8 raw",
            "3 unique",
            "8 scores",
            "Silent has no judge criterion",
            "one paid attempt",
            "explicit result",
            "Do not use `--latest`",
        ):
            self.assertIn(value, body)


if __name__ == "__main__":
    unittest.main()
