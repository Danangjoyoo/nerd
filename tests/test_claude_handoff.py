from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "docs" / "prompts" / "claude-model-benchmark.md"


class ClaudeHandoffTests(unittest.TestCase):
    def test_prompt_is_self_contained_and_uses_exact_targets(self):
        body = PROMPT.read_text(encoding="utf-8")
        for value in (
            "claude-fable-5-xhigh.json",
            "claude-opus-4-8-xhigh.json",
            "claude-sonnet-5-xhigh.json",
            "claude-haiku-4-5.json",
            "claude-fable-5",
            "claude-opus-4-8",
            "claude-sonnet-5",
            "claude-haiku-4-5",
            "120",
            "60",
        ):
            self.assertIn(value, body)

    def test_prompt_uses_explicit_result_paths_and_preserves_public_state(self):
        body = PROMPT.read_text(encoding="utf-8")
        for value in (
            "benchmarks/run.py run",
            "benchmarks/run.py judge",
            "benchmarks/run.py score",
            "benchmarks/run.py report",
            "--results",
            "Do not modify `README.md`",
            "Do not commit, push, tag, or publish",
            "Do not fabricate",
        ):
            self.assertIn(value, body)


if __name__ == "__main__":
    unittest.main()
