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
    _smoke_specs,
    _changed_files,
    _timeout_text,
    create_run_directory,
    condition_prompt,
    load_config,
    pair_key,
    schedule_runs,
)


ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "tests" / "fixtures" / "benchmark-events"
CONFIG = ROOT / "benchmarks" / "config.json"


def spec(
    agent: str,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> RunSpec:
    return RunSpec(
        run_id="case-agent-1-condition",
        case_id="case",
        condition="condition",
        agent=agent,
        model=model,
        repetition=1,
        workspace=Path("/tmp/benchmark workspace"),
        target_id="test-target",
        reasoning_effort=reasoning_effort,
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

    def test_codex_command_pins_reasoning_effort(self):
        command = get_adapter("codex").build_command(
            spec("codex", "gpt-5.6-sol", "xhigh"),
            "prompt",
        )
        self.assertIn("gpt-5.6-sol", command)
        self.assertIn("-c", command)
        self.assertIn('model_reasoning_effort="xhigh"', command)

    def test_claude_command_is_noninteractive_and_persistent_state_is_disabled(self):
        command = get_adapter("claude").build_command(
            spec("claude", "claude-test"), "prompt"
        )
        self.assertEqual(command[0:2], ["claude", "-p"])
        self.assertIn("--no-session-persistence", command)
        self.assertIn("acceptEdits", command)
        self.assertIn("claude-test", command)

    def test_claude_command_pins_reasoning_effort(self):
        command = get_adapter("claude").build_command(
            spec("claude", "claude-fable-5", "xhigh"),
            "prompt",
        )
        effort = command.index("--effort")
        self.assertEqual(command[effort + 1], "xhigh")

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
    def test_release_schedule_has_513_runs(self):
        config = load_config(CONFIG)
        runs = schedule_runs(config, ROOT / "benchmarks" / "work" / "test")
        self.assertEqual(len(runs), 513)
        self.assertEqual(len({run.run_id for run in runs}), 513)

    def test_every_comparative_run_has_matched_opposite_arm(self):
        config = load_config(CONFIG)
        runs = schedule_runs(config, ROOT / "benchmarks" / "work" / "test")
        groups: dict[tuple, list[RunSpec]] = {}
        for run in runs:
            if run.condition == "nerd-patrol":
                continue
            groups.setdefault(pair_key(run), []).append(run)
        self.assertEqual(len(groups), 234)
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

    def test_pair_identity_includes_target_and_effort(self):
        base = spec("codex", "gpt-5.6-sol", "xhigh")
        other = replace(base, target_id="other-target")
        self.assertNotEqual(pair_key(base), pair_key(other))
        self.assertIn("test-target", pair_key(base))
        self.assertIn("xhigh", pair_key(base))

    def test_smoke_uses_noninteractive_execute_blocker_case(self):
        config = load_config(CONFIG)
        runs = schedule_runs(config, Path("/tmp/smoke"))
        smoke = _smoke_specs(runs)
        execute = [item for item in smoke if item.run_id.startswith("execute--")]
        self.assertEqual(len(execute), 2)
        self.assertEqual({item.case_id for item in execute}, {"execute-blocker"})

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

    def test_timeout_streams_are_normalized_from_bytes(self):
        self.assertEqual(_timeout_text(b"partial output"), "partial output")
        self.assertEqual(_timeout_text("text output"), "text output")
        self.assertEqual(_timeout_text(None), "")

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
        self.assertEqual(config["judge"]["agent"], "codex")
        self.assertEqual(config["judge"]["model"], "gpt-5.6-terra")
        self.assertEqual(config["judge"]["reasoning_effort"], "xhigh")
        self.assertGreater(config["judge"]["timeout_seconds"], 0)
        self.assertEqual(config["target"]["id"], "cross-agent-default")

    def test_condition_prompt_explicitly_invokes_skill_without_escape(self):
        self.assertEqual(
            condition_prompt("nerd-smart", "Do the task."),
            "Use $nerd-smart.\n\nDo the task.",
        )

    def test_condition_prompt_composes_fast_with_execute(self):
        self.assertEqual(
            condition_prompt("nerd-fast", "Do the task."),
            "Use $nerd-execute and $nerd-fast.\n\nDo the task.",
        )
        self.assertEqual(
            condition_prompt("fast-baseline", "Do the task."),
            "Use $nerd-execute.\n\nDo the task.",
        )

    def test_plan_cli_lists_513_without_creating_results(self):
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
        self.assertIn("513 planned agent runs", result.stdout)
        after = latest.read_text() if latest.exists() else None
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
