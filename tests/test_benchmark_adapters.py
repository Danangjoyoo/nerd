from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from benchmarks.nerdbench.adapters import get_adapter
from benchmarks.nerdbench.models import RunSpec
from benchmarks.nerdbench.runner import (
    _changed_files,
    create_run_directory,
    condition_prompt,
    load_config,
    pair_key,
    schedule_runs,
)


ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "tests" / "fixtures" / "benchmark-events"
CONFIG = ROOT / "benchmarks" / "config.json"


def spec(agent: str, model: str | None = None) -> RunSpec:
    return RunSpec(
        run_id="case-agent-1-condition",
        case_id="case",
        condition="condition",
        agent=agent,
        model=model,
        repetition=1,
        workspace=Path("/tmp/benchmark workspace"),
    )


class AdapterCommandTests(unittest.TestCase):
    def test_codex_command_is_safe_and_ephemeral(self):
        command = get_adapter("codex").build_command(spec("codex"), "prompt; echo bad")
        self.assertEqual(command[0:2], ["codex", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("--json", command)
        self.assertIn("workspace-write", command)
        self.assertIn("/tmp/benchmark workspace", command)
        self.assertEqual(command[-1], "prompt; echo bad")

    def test_claude_command_is_noninteractive_and_persistent_state_is_disabled(self):
        command = get_adapter("claude").build_command(
            spec("claude", "claude-test"), "prompt"
        )
        self.assertEqual(command[0:2], ["claude", "-p"])
        self.assertIn("--no-session-persistence", command)
        self.assertIn("acceptEdits", command)
        self.assertIn("claude-test", command)

    def test_cursor_command_uses_workspace_and_sandbox(self):
        command = get_adapter("cursor").build_command(spec("cursor"), "prompt")
        self.assertEqual(command[0:2], ["cursor", "agent"])
        self.assertIn("--workspace", command)
        self.assertIn("enabled", command)
        self.assertNotIn("--dangerously-skip-permissions", command)


class AdapterParseTests(unittest.TestCase):
    def test_codex_jsonl_extracts_final_text_tokens_and_redacts(self):
        stdout = (EVENTS / "codex.jsonl").read_text()
        final, tokens, events = get_adapter("codex").parse(stdout, "")
        self.assertEqual(final, "Codex final answer")
        self.assertEqual(tokens, 42)
        self.assertNotIn("must-redact", repr(events))
        self.assertIn("[REDACTED]", repr(events))

    def test_claude_json_extracts_result_and_tokens(self):
        stdout = (EVENTS / "claude.json").read_text()
        final, tokens, events = get_adapter("claude").parse(stdout, "")
        self.assertEqual(final, "Claude final answer")
        self.assertEqual(tokens, 31)
        self.assertNotIn("must-redact", repr(events))

    def test_cursor_jsonl_extracts_content(self):
        stdout = (EVENTS / "cursor.jsonl").read_text()
        final, tokens, _ = get_adapter("cursor").parse(stdout, "")
        self.assertEqual(final, "Cursor final answer")
        self.assertEqual(tokens, 27)

    def test_missing_usage_is_never_guessed(self):
        final, tokens, _ = get_adapter("codex").parse(
            '{"type":"item.completed","item":{"type":"agent_message","text":"x"}}',
            "",
        )
        self.assertEqual(final, "x")
        self.assertIsNone(tokens)


class RunnerTests(unittest.TestCase):
    def test_release_schedule_has_405_runs(self):
        config = load_config(CONFIG)
        runs = schedule_runs(config, ROOT / "benchmarks" / "work" / "test")
        self.assertEqual(len(runs), 405)
        self.assertEqual(len({run.run_id for run in runs}), 405)

    def test_every_comparative_run_has_matched_opposite_arm(self):
        config = load_config(CONFIG)
        runs = schedule_runs(config, ROOT / "benchmarks" / "work" / "test")
        groups: dict[tuple, list[RunSpec]] = {}
        for run in runs:
            if run.condition == "nerd-patrol":
                continue
            groups.setdefault(pair_key(run), []).append(run)
        self.assertEqual(len(groups), 180)
        self.assertTrue(all(len(group) == 2 for group in groups.values()))
        for group in groups.values():
            self.assertEqual(len({item.condition for item in group}), 2)

    def test_seeded_schedule_is_deterministic(self):
        config = load_config(CONFIG)
        first = schedule_runs(config, Path("/tmp/one"))
        second = schedule_runs(config, Path("/tmp/two"))
        self.assertEqual(
            [item.run_id for item in first],
            [item.run_id for item in second],
        )

    def test_existing_run_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_run_directory(root, "20260715T000000Z-deadbee")
            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                create_run_directory(root, "20260715T000000Z-deadbee")

    def test_changed_files_preserve_the_first_filename_character(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "bench@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Benchmark"], cwd=root, check=True)
            (root / "sequence.py").write_text("before\n")
            subprocess.run(["git", "add", "sequence.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
            (root / "sequence.py").write_text("after\n")
            self.assertEqual(_changed_files(root), ("sequence.py",))

    def test_config_pin_is_exact(self):
        config = load_config(CONFIG)
        self.assertEqual(
            config["upstream"]["commit"],
            "d884ae04edebef577e82ff7c4e143debd0bbec99",
        )
        self.assertEqual(
            config["upstream"]["tag_object"],
            "c984ea2e7aeffdcc865784fd6c5e3ab75da0209a",
        )
        self.assertEqual(config["parallelism"], 1)

    def test_condition_prompt_explicitly_invokes_skill_without_escape(self):
        self.assertEqual(
            condition_prompt("nerd-smart", "Do the task."),
            "Use $nerd-smart.\n\nDo the task.",
        )

    def test_plan_cli_lists_405_without_creating_results(self):
        latest = ROOT / "benchmarks" / "results" / "LATEST"
        before = latest.read_text() if latest.exists() else None
        result = subprocess.run(
            [
                "python3",
                "benchmarks/run.py",
                "plan",
                "--config",
                "benchmarks/config.json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("405 planned agent runs", result.stdout)
        after = latest.read_text() if latest.exists() else None
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
