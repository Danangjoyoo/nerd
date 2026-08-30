from __future__ import annotations

from pathlib import Path
from unittest import mock
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "nerd-memory" / "scripts" / "memory.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("nerd_behavior_memory", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def episode(episode_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "episode_id": episode_id,
        "repository": "repo-alpha",
        "language": "python",
        "surface": "api",
        "project_kind": "service",
        "raw_input": "Please test the API",
        "action": "test",
        "tools": ["pytest"],
        "steps": ["inspect_tests", "run_pytest", "report"],
        "skills": ["create-unit-tests", "nerd-execute"],
        "output_signals": ["tests_passed"],
        "output_valid": True,
        "output_severity": "none",
        "verified": True,
        "verifier": "pytest",
        "feedback": "accepted",
        "corrected_tools": [],
        "corrected_steps": [],
        "corrected_skills": [],
        "source_kind": "verified_execution",
        "source_agent": "teacher-agent",
        "evidence_ref": f"proof:{episode_id}",
        "observed_at": "2026-08-31T00:00:00.000000Z",
    }
    value.update(overrides)
    return value


def recall_request(event_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "event_id": event_id,
        "raw_input": "test api",
        "repository": "another-repository",
        "language": "python",
        "surface": "api",
        "project_kind": "service",
        "current": {"action": None, "tools": [], "steps": [], "skills": []},
        "output_signals": [],
        "consumer_agent": "consumer-agent",
    }
    value.update(overrides)
    return value


class BehaviorMemoryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_engine()
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "behavior.sqlite3"
        self.store = self.engine.BehaviorMemoryStore(self.db)

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_default_path_order(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"NERD_MEMORY_DB": "/tmp/explicit.sqlite3", "CODEX_HOME": "/tmp/codex"},
            clear=True,
        ):
            self.assertEqual(
                self.engine.default_database_path(), Path("/tmp/explicit.sqlite3")
            )
        with mock.patch.dict(os.environ, {"CODEX_HOME": "/tmp/codex"}, clear=True):
            self.assertEqual(
                self.engine.default_database_path(),
                Path("/tmp/codex/nerd-memory/behavior.sqlite3"),
            )
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            self.engine.Path, "home", return_value=Path("/tmp/home")
        ):
            self.assertEqual(
                self.engine.default_database_path(),
                Path("/tmp/home/.codex/nerd-memory/behavior.sqlite3"),
            )

    def test_fresh_schema_has_only_behavioral_tables(self) -> None:
        tables = {
            row[0]
            for row in self.store.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        }
        self.assertEqual(
            tables,
            {
                "metadata",
                "behavior_episodes",
                "recall_events",
                "forget_previews",
                "trusted_event_tombstones",
            },
        )
        inspected = self.store.inspect()
        self.assertEqual(inspected["schema_family"], "global-behavior-memory")
        self.assertEqual(inspected["schema_version"], 1)

    def test_record_round_trips_every_sanitized_field_and_is_idempotent(self) -> None:
        original = episode(
            "root-001",
            command_cues=["API", "tests", "api"],
            feedback="corrected",
            source_kind="user_correction",
            corrected_tools=["uv"],
            corrected_steps=["inspect_pytest", "run_uv", "report"],
            corrected_skills=["create-unit-tests", "nerd-execute"],
        )
        original.pop("raw_input")
        first = self.store.record(**original)
        second = self.store.record(**original)

        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        stored = first["episode"]
        self.assertEqual(stored["sequence"], 1)
        self.assertEqual(stored["episode_id"], "root-001")
        self.assertEqual(stored["repository"], "repo-alpha")
        self.assertEqual(stored["language"], "python")
        self.assertEqual(stored["surface"], "api")
        self.assertEqual(stored["project_kind"], "service")
        self.assertEqual(stored["command_cues"], ["api", "test"])
        self.assertEqual(stored["action"], "test")
        self.assertEqual(stored["tools"], ["pytest"])
        self.assertEqual(stored["steps"], ["inspect_tests", "run_pytest", "report"])
        self.assertEqual(stored["skills"], ["create-unit-tests", "nerd-execute"])
        self.assertEqual(stored["output_signals"], ["tests_passed"])
        self.assertTrue(stored["output_valid"])
        self.assertEqual(stored["output_severity"], "none")
        self.assertTrue(stored["verified"])
        self.assertEqual(stored["verifier"], "pytest")
        self.assertEqual(stored["feedback"], "corrected")
        self.assertEqual(stored["corrected_tools"], ["uv"])
        self.assertEqual(
            stored["corrected_steps"], ["inspect_pytest", "run_uv", "report"]
        )
        self.assertEqual(
            stored["corrected_skills"], ["create-unit-tests", "nerd-execute"]
        )
        self.assertEqual(stored["source_kind"], "user_correction")
        self.assertEqual(stored["source_agent"], "teacher-agent")
        self.assertEqual(stored["evidence_ref"], "proof:root-001")
        self.assertEqual(stored["observed_at"], "2026-08-31T00:00:00.000000Z")
        self.assertRegex(stored["created_at"], r"Z$")

        self.store.close()
        self.store = self.engine.BehaviorMemoryStore(self.db)
        self.assertEqual(self.store.inspect()["episodes"][0], stored)
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.store.record(**episode("root-001", action="implement"))

    def test_positive_admission_requires_verified_accepted_execution(self) -> None:
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(**episode("unverified", verified=False))
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(**episode("assistant", source_kind="assistant_only"))
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(
                **episode(
                    "wrong-correction",
                    feedback="corrected",
                    corrected_tools=["uv"],
                )
            )
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(
                **episode(
                    "empty-correction",
                    feedback="corrected",
                    source_kind="user_correction",
                )
            )

        failed = self.store.record(
            **episode(
                "failed-output",
                output_valid=False,
                output_severity="high",
                output_signals=["secret_leak"],
                feedback="rejected",
            )
        )
        self.assertEqual(failed["episode"]["feedback"], "rejected")
        recalled = self.store.recall(
            **recall_request("guard-only", output_signals=["secret_leak"])
        )
        self.assertTrue(recalled["advice"]["reject_output"])
        self.assertTrue(recalled["advice"]["abstained"])

    def test_m3_majorities_transfer_across_repository_and_emit_provenance(self) -> None:
        for index in range(3):
            self.store.record(**episode(f"pytest-{index}"))
        self.store.record(
            **episode(
                "minority",
                action="implement",
                tools=["apply_patch"],
                steps=["inspect", "patch", "verify"],
                skills=["nerd-execute"],
            )
        )

        result = self.store.recall(**recall_request("recall-majority"))

        self.assertFalse(result["advice"]["abstained"])
        self.assertEqual(result["advice"]["action"], "test")
        self.assertEqual(result["advice"]["tools"], ["pytest"])
        self.assertEqual(
            result["advice"]["step_edges"],
            [["inspect_tests", "run_pytest"], ["run_pytest", "report"]],
        )
        self.assertEqual(result["advice"]["confidence"], 0.75)
        self.assertEqual(result["advice"]["origin"], "behavioral_memory_advice")
        self.assertEqual(
            set(result["advice"]["source_episode_ids"]),
            {"pytest-0", "pytest-1", "pytest-2"},
        )
        event = self.store.inspect()["recall_events"][0]
        self.assertEqual(event["repository"], "another-repository")
        self.assertNotIn("raw_input", event)

    def test_repository_provenance_accepts_a_local_path_without_partitioning(self) -> None:
        self.store.record(
            **episode("path-source", repository="/Users/example/dev/source-repo")
        )
        result = self.store.recall(
            **recall_request(
                "path-consumer", repository="/Users/example/dev/other-repo"
            )
        )

        self.assertEqual(result["advice"]["action"], "test")
        self.assertEqual(
            self.store.inspect()["episodes"][0]["repository"],
            "/Users/example/dev/source-repo",
        )

    def test_m3_abstains_on_no_match_tie_low_confidence_and_context_mismatch(self) -> None:
        self.store.record(**episode("test-one"))
        self.store.record(**episode("implement-one", action="implement"))
        tied = self.store.recall(**recall_request("tie"))
        self.assertTrue(tied["advice"]["abstained"])

        self.store.record(**episode("test-two"))
        self.store.record(**episode("implement-two", action="implement"))
        self.store.record(**episode("test-three"))
        low = self.store.recall(**recall_request("low-confidence"))
        self.assertEqual(low["advice"]["confidence"], 0.6)
        self.assertFalse(low["advice"]["abstained"])

        no_match = self.store.recall(
            **recall_request("no-match", raw_input="document release notes")
        )
        self.assertTrue(no_match["advice"]["abstained"])
        mismatch = self.store.recall(
            **recall_request("context-mismatch", language="typescript")
        )
        self.assertTrue(mismatch["advice"]["abstained"])

    def test_invalid_output_share_at_half_rejects(self) -> None:
        self.store.record(
            **episode(
                "invalid",
                output_valid=False,
                feedback="rejected",
                output_signals=["malformed_json"],
                output_severity="high",
            )
        )
        self.store.record(**episode("valid", output_signals=["malformed_json"]))
        result = self.store.recall(
            **recall_request("guard-half", output_signals=["malformed_json"])
        )
        self.assertTrue(result["advice"]["reject_output"])

    def test_three_compatible_corrections_retire_obsolete_resources(self) -> None:
        for index in range(5):
            self.store.record(**episode(f"old-{index}"))
        for index in range(3):
            self.store.record(
                **episode(
                    f"correction-{index}",
                    feedback="corrected",
                    source_kind="user_correction",
                    corrected_tools=["uv"],
                    corrected_steps=["inspect_pytest", "run_uv", "report"],
                    corrected_skills=["create-unit-tests", "nerd-execute"],
                )
            )

        result = self.store.recall(**recall_request("corrected-recall"))

        self.assertEqual(result["advice"]["tools"], ["uv"])
        self.assertEqual(
            result["advice"]["steps"], ["inspect_pytest", "run_uv", "report"]
        )
        self.assertTrue(
            {"correction-0", "correction-1", "correction-2"}.issubset(
                result["advice"]["source_episode_ids"]
            )
        )

    def test_three_differing_compatible_corrections_retire_old_resources(self) -> None:
        for index in range(5):
            self.store.record(**episode(f"old-varied-{index}"))
        for index, tool in enumerate(("uv", "tox", "nox")):
            self.store.record(
                **episode(
                    f"varied-correction-{index}",
                    feedback="corrected",
                    source_kind="user_correction",
                    corrected_tools=[tool],
                    corrected_steps=[f"run_{tool}", "report"],
                    corrected_skills=["create-unit-tests"],
                )
            )

        result = self.store.recall(**recall_request("varied-correction-recall"))

        self.assertEqual(result["advice"]["tools"], ["nox"])
        self.assertEqual(result["advice"]["steps"], ["run_nox", "report"])

    def test_current_behavior_overrides_nonempty_advice_fields(self) -> None:
        self.store.record(**episode("source"))
        current = {
            "action": "review",
            "tools": ["rg"],
            "steps": [],
            "skills": ["nerd-review"],
        }
        result = self.store.recall(**recall_request("override", current=current))

        self.assertEqual(result["advice"]["action"], "test")
        self.assertEqual(result["resolved_advice"]["action"], "review")
        self.assertEqual(result["resolved_advice"]["tools"], ["rg"])
        self.assertEqual(
            result["resolved_advice"]["steps"],
            ["inspect_tests", "run_pytest", "report"],
        )
        self.assertEqual(result["resolved_advice"]["skills"], ["nerd-review"])
        self.assertEqual(result["overridden_fields"], ["action", "tools", "skills"])
        self.assertEqual(result["resolved_advice"]["authority_source"], "current_request")

    def test_current_step_override_replaces_memory_step_edges(self) -> None:
        self.store.record(**episode("edge-source"))
        result = self.store.recall(
            **recall_request(
                "edge-override",
                current={
                    "action": None,
                    "tools": [],
                    "steps": ["user_first", "user_second"],
                    "skills": [],
                },
            )
        )

        self.assertEqual(result["resolved_advice"]["steps"], ["user_first", "user_second"])
        self.assertEqual(
            result["resolved_advice"]["step_edges"],
            [["user_first", "user_second"]],
        )

    def test_forget_preview_deletes_exact_bound_evidence_and_blocks_replay(self) -> None:
        self.store.record(**episode("delete-me"))
        self.store.record(**episode("keep-me"))
        self.store.recall(**recall_request("bound-audit"))
        preview = self.store.preview_forget(["delete-me"])

        self.assertEqual(preview["episode_ids"], ["delete-me"])
        self.assertRegex(preview["digest"], r"^sha256:[0-9a-f]{64}$")
        forgotten = self.store.forget(
            preview["preview_id"],
            preview["confirmation_phrase"],
            source="direct_user",
            event_ref="user-event:forget-1",
        )

        self.assertEqual(forgotten["deleted_episode_ids"], ["delete-me"])
        self.assertEqual(forgotten["deleted_recall_events"], 1)
        self.assertEqual(
            [item["episode_id"] for item in self.store.inspect()["episodes"]],
            ["keep-me"],
        )
        second = self.store.preview_forget(["keep-me"])
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.store.forget(
                second["preview_id"],
                second["confirmation_phrase"],
                source="direct_user",
                event_ref="user-event:forget-1",
            )

    def test_cli_has_only_new_commands_and_matches_direct_results(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--help"],
            text=True,
            capture_output=True,
            check=True,
        )
        for command in ("record", "recall", "inspect", "preview-forget", "forget"):
            self.assertIn(command, help_result.stdout)
        for legacy in ("enable", "observe", "settle", "learn", "promote"):
            self.assertNotIn(legacy, help_result.stdout)

        payload = episode("cli-record")
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--db",
                str(self.db),
                "record",
                "--episode",
                json.dumps(payload),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        cli_result = json.loads(completed.stdout)
        self.assertEqual(cli_result["episode"]["episode_id"], "cli-record")
        self.assertEqual(self.store.inspect()["counts"]["behavior_episodes"], 1)

        bad = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--db",
                str(self.db),
                "record",
                "--episode",
                json.dumps({**episode("unsafe-cli"), "permissions": ["admin"]}),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stderr)["error"]["code"], "invalid_input")

        malformed = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--unknown"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(malformed.returncode, 2)
        self.assertEqual(
            json.loads(malformed.stderr)["error"]["code"], "invalid_input"
        )
        self.assertNotIn("usage:", malformed.stderr)

    def test_python_api_has_no_partition_selector(self) -> None:
        signatures = "\n".join(
            str(inspect.signature(getattr(self.engine.BehaviorMemoryStore, name)))
            for name in ("record", "recall", "inspect", "preview_forget", "forget")
        ).lower()
        self.assertNotIn("namespace", signatures)
        self.assertNotIn("tenant", signatures)
        self.assertNotIn("global_search", signatures)


if __name__ == "__main__":
    unittest.main()
