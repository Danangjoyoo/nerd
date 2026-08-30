import json
import tempfile
import unittest
from pathlib import Path

from poc.paired_agent_experiment import (
    ANSWER_SCHEMA,
    TEACHER_TRACE,
    evaluate,
    expected_output,
    finalize,
    prepare,
    start_round,
    verify_teacher_and_record,
)
from poc.shared_memory import SharedBehaviorMemory


class PairedAgentExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.memory = SharedBehaviorMemory(self.root / "memory.sqlite")

    def tearDown(self):
        self.memory.close()
        self.tempdir.cleanup()

    def _read(self, relative: str):
        return json.loads((self.root / relative).read_text())

    def _write(self, relative: str, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    def _verified_teacher(self):
        training = self._read("teacher/input.json")
        response = {
            "schema_version": ANSWER_SCHEMA,
            "round": 0,
            "arm": "teacher",
            "input_digest": self._read("teacher/card.json")["input_digest"],
            "output": expected_output(training),
            "behavior_trace": TEACHER_TRACE,
        }
        path = self._write("teacher/response.json", response)
        return verify_teacher_and_record(self.memory, self.root, path)

    def test_expected_output_applies_non_obvious_procedure(self):
        source = {
            "batch_id": "known",
            "records": [
                {
                    "transaction_id": "tx-b",
                    "account": " a-1 ",
                    "region": "US",
                    "status": "approved",
                    "revision": 2,
                    "amount": "10.005",
                },
                {
                    "transaction_id": "tx-a",
                    "account": "A-1",
                    "region": "eu",
                    "status": "APPROVED",
                    "revision": 2,
                    "amount": "20.015",
                },
                {
                    "transaction_id": "tx-c",
                    "account": "B-2",
                    "region": "xx",
                    "status": "pending",
                    "revision": 4,
                    "amount": "2000.00",
                },
            ],
        }

        result = expected_output(source)

        self.assertEqual(result["records"][0]["transaction_id"], "tx-a")
        self.assertEqual(result["records"][0]["amount_cents"], 2002)
        self.assertEqual(result["summary"]["record_count"], 1)
        self.assertEqual(len(result["batch_fingerprint"]), 16)

    def test_prepare_keeps_public_cards_matched_and_gold_private(self):
        manifest = prepare(self.root, seed=606)

        self.assertEqual(manifest["round_count"], 5)
        for round_number in range(1, 6):
            card = self._read(f"rounds/round-{round_number:02d}/card.json")
            serialized = json.dumps(card)
            self.assertNotIn("deduplicate", serialized.lower())
            self.assertNotIn("round_half_even", serialized.lower())
            self.assertEqual(
                card["input_digest"],
                manifest["round_input_digests"][f"round-{round_number:02d}"],
            )

    def test_teacher_must_pass_before_behavior_is_recorded(self):
        prepare(self.root, seed=606)
        training = self._read("teacher/input.json")
        bad_response = {
            "schema_version": ANSWER_SCHEMA,
            "round": 0,
            "arm": "teacher",
            "input_digest": self._read("teacher/card.json")["input_digest"],
            "output": {"wrong": True},
            "behavior_trace": TEACHER_TRACE,
        }
        bad_path = self._write("teacher/bad-response.json", bad_response)

        with self.assertRaises(ValueError):
            verify_teacher_and_record(self.memory, self.root, bad_path)
        self.assertEqual(self.memory.behavior_count(), 0)

        verdict = self._verified_teacher()
        self.assertTrue(verdict["passed"])
        self.assertEqual(self.memory.behavior_count(), 1)

    def test_five_pair_evaluation_reports_accuracy_tokens_and_speed(self):
        prepare(self.root, seed=606)
        self._verified_teacher()
        for round_number in range(1, 6):
            card = self._read(f"rounds/round-{round_number:02d}/card.json")
            input_data = self._read(f"rounds/round-{round_number:02d}/input.json")
            start_round(
                self.root,
                round_number,
                spawn_order=("memory", "control")
                if round_number % 2
                else ("control", "memory"),
                now_ns=round_number * 10_000_000_000,
            )
            recall = self.memory.recall(
                command=card["command"],
                trial_id=f"iteration006-round-{round_number:02d}-memory",
                consumer_agent=f"round-{round_number:02d}-memory",
                consumer_repository=f"round-{round_number:02d}-memory-repository",
            )
            recall_path = self._write(
                f"recalls/round-{round_number:02d}-memory.json", recall
            )
            memory_response = {
                "schema_version": ANSWER_SCHEMA,
                "round": round_number,
                "arm": "memory",
                "input_digest": card["input_digest"],
                "output": expected_output(input_data),
            }
            control_response = {
                "schema_version": ANSWER_SCHEMA,
                "round": round_number,
                "arm": "control",
                "input_digest": card["input_digest"],
                "output": {},
            }
            memory_path = self._write(
                f"responses/round-{round_number:02d}-memory.json", memory_response
            )
            control_path = self._write(
                f"responses/round-{round_number:02d}-control.json", control_response
            )
            finalize(
                self.root,
                round_number,
                "memory",
                memory_path,
                recall_path=recall_path,
                now_ns=round_number * 10_000_000_000 + 2_000_000_000,
            )
            finalize(
                self.root,
                round_number,
                "control",
                control_path,
                now_ns=round_number * 10_000_000_000 + 1_000_000_000,
            )

        result = evaluate(self.memory, self.root)

        self.assertTrue(result["passed"])
        self.assertEqual(result["accuracy"]["memory"]["exact_mean"], 1.0)
        self.assertEqual(result["accuracy"]["control"]["exact_mean"], 0.0)
        self.assertEqual(result["accuracy"]["paired_exact_gain_mean"], 1.0)
        self.assertEqual(result["speed_seconds"]["memory"]["mean"], 2.0)
        self.assertEqual(result["speed_seconds"]["control"]["mean"], 1.0)
        self.assertIn("observable_lexical_tokens", result)
        self.assertEqual(result["condition_audit"]["memory_recall_once"], True)
        self.assertEqual(result["condition_audit"]["control_recall_zero"], True)
        self.assertEqual(result["relative_comparison"]["rounds_memory_faster"], 0)
        self.assertEqual(
            result["relative_comparison"]["rounds_memory_lower_token_proxy"], 0
        )


if __name__ == "__main__":
    unittest.main()
