import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from poc.agent_experiment import WORKERS, evaluate, make_cards
from poc.shared_memory import SharedBehaviorMemory


class SharedBehaviorMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "shared.sqlite"
        self.memory = SharedBehaviorMemory(self.db_path)

    def tearDown(self):
        self.memory.close()
        self.tempdir.cleanup()

    def _record(self):
        self.memory.record(
            behavior_id="amber-lantern",
            cue_phrases=("amber lantern", "light the amber lantern"),
            action="inspect_then_seal",
            tools=("rg", "python"),
            steps=("inspect", "validate", "seal"),
            skills=("nerd-explore", "nerd-execute"),
            invalid_signals=("seal_missing", "validation_failed"),
            source_agent="teacher",
            source_repository="teacher-repository",
            verification_id="verify-amber-1",
            verified=True,
        )

    def test_schema_has_no_namespace_column_or_table(self):
        self._record()
        connection = sqlite3.connect(self.db_path)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            columns = {
                row[1]
                for table in tables
                for row in connection.execute(f"PRAGMA table_info({table})")
            }
        finally:
            connection.close()

        self.assertNotIn("namespace", tables)
        self.assertNotIn("namespace", columns)

    def test_recall_crosses_repository_context_and_keeps_provenance(self):
        self._record()

        recalled = self.memory.recall(
            command="please light the amber lantern now",
            consumer_agent="worker-one",
            consumer_repository="unseen-repository",
        )

        self.assertEqual(recalled["status"], "recalled")
        self.assertEqual(recalled["behavior_id"], "amber-lantern")
        self.assertEqual(recalled["source_repository"], "teacher-repository")
        self.assertEqual(recalled["consumer_repository"], "unseen-repository")
        self.assertEqual(recalled["tools"], ["rg", "python"])

    def test_unknown_command_abstains(self):
        self._record()

        recalled = self.memory.recall(
            command="calculate lunar tide harmonics",
            consumer_agent="worker-one",
            consumer_repository="unseen-repository",
        )

        self.assertEqual(recalled["status"], "abstained")
        self.assertIsNone(recalled["behavior_id"])

    def test_invalid_signal_is_rejected_after_recall(self):
        self._record()

        recalled = self.memory.recall(
            command="amber lantern",
            consumer_agent="worker-one",
            consumer_repository="unseen-repository",
            output_signal="validation_failed",
        )

        self.assertTrue(recalled["reject_output"])
        self.assertEqual(recalled["matched_invalid_signal"], "validation_failed")

    def test_unverified_behavior_is_not_recorded(self):
        with self.assertRaises(ValueError):
            self.memory.record(
                behavior_id="unverified",
                cue_phrases=("unverified cue",),
                action="unsafe_action",
                tools=("unsafe-tool",),
                steps=("run",),
                skills=(),
                invalid_signals=(),
                source_agent="teacher",
                source_repository="teacher-repository",
                verification_id="missing",
                verified=False,
            )

        self.assertEqual(self.memory.behavior_count(), 0)


class SharedAgentExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.memory = SharedBehaviorMemory(self.root / "shared.sqlite")
        for index in range(6):
            self.memory.record(
                behavior_id=f"pattern-{index}",
                cue_phrases=(f"marker{index} signal{index}", f"invoke marker{index} signal{index}"),
                action=f"action-{index}",
                tools=(f"tool-{index}",),
                steps=(f"step-{index}-a", f"step-{index}-b"),
                skills=(f"skill-{index}",),
                invalid_signals=(f"invalid-{index}",),
                source_agent="teacher",
                source_repository="teacher-repository",
                verification_id=f"verification-{index}",
                verified=True,
            )

    def tearDown(self):
        self.memory.close()
        self.tempdir.cleanup()

    def test_cards_are_counterbalanced_and_do_not_expose_answers(self):
        make_cards(self.memory, self.root, seed=505)
        gold = json.loads((self.root / "gold.json").read_text())
        by_behavior = {}
        for expected in gold["trials"].values():
            if expected["kind"] == "known":
                by_behavior.setdefault(expected["behavior_id"], set()).add(
                    expected["memory_enabled"]
                )
        self.assertTrue(all(conditions == {False, True} for conditions in by_behavior.values()))

        for worker_id, _ in WORKERS:
            public = json.loads((self.root / "cards" / f"{worker_id}.json").read_text())
            serialized = json.dumps(public)
            self.assertNotIn('"action"', serialized)
            self.assertNotIn('"tools"', serialized)
            self.assertNotIn('"behavior_id"', serialized)

    def test_evaluator_proves_shared_recall_and_usefulness_against_off_control(self):
        make_cards(self.memory, self.root, seed=505)
        gold = json.loads((self.root / "gold.json").read_text())["trials"]
        for worker_id, repository in WORKERS:
            public = json.loads((self.root / "cards" / f"{worker_id}.json").read_text())
            trials = []
            for card in public["trials"]:
                expected = gold[card["trial_id"]]
                if card["memory_enabled"]:
                    result = self.memory.recall(
                        command=card["command"],
                        trial_id=card["trial_id"],
                        consumer_agent=worker_id,
                        consumer_repository=repository,
                        output_signal=card["output_signal"],
                    )
                else:
                    result = {
                        "status": "abstained",
                        "behavior_id": None,
                        "action": None,
                        "tools": [],
                        "steps": [],
                        "skills": [],
                        "reject_output": False,
                        "source_repository": None,
                    }
                result["trial_id"] = card["trial_id"]
                trials.append(result)
            submission = {"worker_id": worker_id, "trials": trials}
            path = self.root / "submissions" / f"{worker_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(submission))

        result = evaluate(self.memory, self.root)

        self.assertTrue(result["passed"])
        self.assertEqual(result["metrics"]["memory_on_exact_success"], 1.0)
        self.assertEqual(result["metrics"]["memory_off_exact_success"], 0.0)
        self.assertEqual(result["metrics"]["cross_repository_recall"], 1.0)
        self.assertEqual(result["metrics"]["invalid_output_recall_memory_on"], 1.0)
        self.assertEqual(result["metrics"]["valid_output_false_rejection_memory_on"], 0.0)


if __name__ == "__main__":
    unittest.main()
