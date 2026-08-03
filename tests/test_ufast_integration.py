from pathlib import Path
import json
import tempfile
import unittest

from benchmarks.nerdbench.adapters import get_adapter
from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.materialize import materialize_run
from benchmarks.nerdbench.models import RunSpec
from benchmarks.nerdbench.runner import (
    _read_ufast_telemetry,
    condition_prompt,
    isolated_codex_environment,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "pilots" / "xfast-v3-five-cases" / "cases.json"


def spec(workspace: Path, condition: str) -> RunSpec:
    return RunSpec(
        run_id=f"ufast-test-{condition}",
        case_id="xfast-v3-greeting",
        condition=condition,
        agent="codex",
        model="gpt-5.6-luna",
        repetition=1,
        workspace=workspace,
        target_id="gpt-5.6-luna-high",
        reasoning_effort="high",
    )


class UFastConditionTests(unittest.TestCase):
    def test_telemetry_reader_normalizes_only_bounded_tool_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "telemetry.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "tool": "ufast_apply_workspace_change",
                        "status": "applied",
                        "runtime_version": "0.1.0",
                        "operation_ms": 14,
                        "cold_start_ms": 22,
                        "changed_files": ["feature.py"],
                        "checks": [
                            {"name": "syntax", "exit_code": 0},
                        ],
                        "rolled_back": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            events = _read_ufast_telemetry(path)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "ufast_tool_call")
        self.assertEqual(events[0]["tool"], "ufast_apply_workspace_change")
        self.assertEqual(events[0]["changed_files"], ["feature.py"])
        self.assertEqual(events[0]["checks"], [{"name": "syntax", "exit_code": 0}])

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
            self.assertTrue(
                (
                    ufast
                    / ".agents"
                    / "skills"
                    / "nerd-ufast"
                    / "scripts"
                    / "ufast_mcp.py"
                ).is_file()
            )
            self.assertFalse(any(xfast.rglob("ufast_mcp.py")))

    def test_codex_uses_only_the_ufast_isolated_configuration(self):
        adapter = get_adapter("codex")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for condition in ("nerd-ufast", "nerd-xfast"):
                workspace = base / condition
                workspace.mkdir()
                run_spec = spec(workspace, condition)
                command = adapter.build_command(run_spec, "Do the task.")
                self.assertIn("--ignore-rules", command)
                if condition == "nerd-ufast":
                    self.assertNotIn("--ignore-user-config", command)
                else:
                    self.assertIn("--ignore-user-config", command)

                with isolated_codex_environment(run_spec, environ={}) as environment:
                    isolated_home = Path(environment["CODEX_HOME"])
                    config = isolated_home / "config.toml"
                    if condition == "nerd-ufast":
                        self.assertTrue(config.is_file())
                        body = config.read_text(encoding="utf-8")
                        self.assertIn("[mcp_servers.nerd_ufast]", body)
                        self.assertIn("ufast_mcp.py", body)
                        self.assertIn(str(workspace), body)
                        self.assertIn("NERD_UFAST_LOG", body)
                        self.assertEqual(
                            environment["NERD_UFAST_WORKSPACE"],
                            str(workspace),
                        )
                        self.assertEqual(
                            Path(environment["NERD_UFAST_LOG"]).parent,
                            isolated_home,
                        )
                    else:
                        self.assertFalse(config.exists())
                        self.assertNotIn("NERD_UFAST_WORKSPACE", environment)
                        self.assertNotIn("NERD_UFAST_LOG", environment)


if __name__ == "__main__":
    unittest.main()
