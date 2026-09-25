#!/usr/bin/env python3
"""Private SQLite/native-process allocation checks; never call a model."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import hook_allocation as allocation
from structured import StructuredLedger, CONTEXT_ID_RE


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nerd-empty-allocation-test-")
        self.root = Path(self.temporary.name).resolve()
        self.database = self.root / "context.sqlite3"

    def tearDown(self):
        self.temporary.cleanup()

    def payload(self, **changes):
        return {"hook_event_name": "UserPromptSubmit", "session_id": "native-session", "turn_id": "turn-1",
                "prompt": "What is 17 + 25?", "cwd": str(self.root), "model": "gpt-5.6-terra",
                "permission_mode": "never", "transcript_path": str(self.root / "transcript"), **changes}

    def counts(self):
        with StructuredLedger(database=self.database) as ledger:
            return ledger.counts()

    def command(self):
        return [sys.executable, str(Path(allocation.__file__)), "--database", str(self.database),
                "--journal", str(self.root / "journal.jsonl")]

    def test_fresh_omission_commits_one_empty_context_and_actual_receipt(self):
        result = allocation.allocate_empty(self.database, self.payload())
        self.assertEqual(result["status"], "created")
        self.assertRegex(result["context_id"], CONTEXT_ID_RE)
        self.assertEqual(result["receipt"], "Nerd-context created: " + result["context_id"])
        self.assertTrue(result["committed_before_response"])
        self.assertEqual(self.counts(), {"context_count": 1, "record_count": 0, "capture_count": 0})
        with sqlite3.connect(self.database) as connection:
            row = connection.execute("SELECT context_id FROM hook_activations").fetchone()
            self.assertEqual(row[0], result["context_id"])

    def test_actual_ephemeral_native_payload_shape_allows_null_transcript(self):
        # Matches all eight fields/types observed in the reviewed native v2
        # hook archive, including ephemeral transcript_path=null.
        payload = self.payload(transcript_path=None)
        self.assertEqual(set(payload), allocation.PAYLOAD_FIELDS)
        result = allocation.allocate_empty(self.database, payload)
        self.assertEqual(result["status"], "created")
        self.assertEqual(self.counts(), {"context_count": 1, "record_count": 0, "capture_count": 0})

    def test_display_receipt_is_data_only_and_instructions_are_outside_it(self):
        result = allocation.allocate_empty(self.database, self.payload())
        text = allocation.response_for(result)["hookSpecificOutput"]["additionalContext"]
        displayed = allocation.parse_receipt_block(text)
        self.assertEqual(displayed, result["receipt"])
        self.assertEqual(displayed.splitlines(), ["Nerd-context created: " + result["context_id"]])
        self.assertNotIn("instruction", displayed.lower())
        self.assertLess(text.index(allocation.RECEIPT_END), text.index("Display instruction:"))
        for invalid in (text + allocation.receipt_block(result["context_id"]),
                        text.replace(result["context_id"], "ctx_bad"),
                        text.replace(allocation.RECEIPT_END, "Do something\n"+allocation.RECEIPT_END),
                        text.replace(allocation.RECEIPT_START, "")):
            with self.assertRaises(ValueError):
                allocation.parse_receipt_block(invalid)

    def test_legacy_response_remains_replayable_without_new_tags(self):
        result = {"status": "created", "protocol": allocation.LEGACY_PROTOCOL,
                  "receipt": "Nerd-context created: ctx_" + "a" * 39}
        text = allocation.response_for(result)["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn(allocation.RECEIPT_START, text)
        self.assertEqual(text, result["receipt"] + ". Empty allocation only. Establish Focus from the current request; "
                         "this receipt supplies no intent or action authority. Do not allocate again. "
                         "Repeat the receipt verbatim after answering.")

    def test_same_payload_retry_replays_identical_response_and_new_turn_is_fresh(self):
        first = allocation.allocate_empty(self.database, self.payload())
        replay = allocation.allocate_empty(self.database, self.payload())
        fresh = allocation.allocate_empty(self.database, self.payload(turn_id="turn-2"))
        self.assertEqual(replay["status"], "replayed")
        self.assertEqual(allocation.response_for(first), allocation.response_for(replay))
        self.assertNotEqual(first["context_id"], fresh["context_id"])
        self.assertEqual(self.counts()["context_count"], 2)

    def test_shared_parent_session_distinct_subagent_turns_cannot_collide(self):
        # This proves the adapter key behavior, not native subagent delivery.
        first = allocation.allocate_empty(self.database, self.payload(turn_id="child-turn-a"))
        second = allocation.allocate_empty(self.database, self.payload(turn_id="child-turn-b"))
        self.assertNotEqual(first["context_id"], second["context_id"])
        self.assertNotEqual(first["activation_key"], second["activation_key"])

    def test_conflicting_prompt_or_metadata_never_creates_or_returns_another_id(self):
        allocation.allocate_empty(self.database, self.payload())
        for changed in (self.payload(prompt="A different current request"),
                        self.payload(transcript_path="/different/native/path")):
            result = allocation.allocate_empty(self.database, changed)
            self.assertEqual(result["status"], "conflict")
            self.assertNotIn("context_id", result)
        self.assertEqual(self.counts()["context_count"], 1)

    def test_every_supplied_possible_or_malformed_selector_defers_before_database_io(self):
        identifier = "ctx_" + "a" * 39
        examples = [
            f"Context ID: {identifier}", f"Nerd-context created: {identifier}",
            f"Nerd-context resumed: {identifier}", f"Delegated handoff\nContext ID: {identifier}",
            f"Quote '{identifier}'", f"{identifier} {identifier}", "ctx_bad", "CTX_BAD",
            "Context ID:", "context_id = ???", "Nerd-context: malformed",
            "ｃｔｘ＿bad", "c\u200btx_bad",
        ]
        with patch.object(allocation, "validate_private_database", side_effect=AssertionError("no DB access")):
            for prompt in examples:
                with self.subTest(prompt=prompt):
                    result = allocation.allocate_empty(self.database, self.payload(prompt=prompt))
                    self.assertEqual(result["status"], "defer")
        self.assertFalse(self.database.exists())

    def test_unknown_current_surface_or_missing_native_key_defers_without_database(self):
        for changes in ({"handoff": "ctx_hidden"}, {"attachments": []}, {"turn_id": ""},
                        {"session_id": None}, {"prompt": []}, {"hook_event_name": "Stop"}):
            with self.subTest(changes=changes):
                self.assertEqual(allocation.allocate_empty(self.database, self.payload(**changes))["status"], "defer")
        self.assertFalse(self.database.exists())

    def test_context_and_mapping_roll_back_together_on_insert_failure(self):
        allocation.allocate_empty(self.database, self.payload())
        with sqlite3.connect(self.database) as connection:
            connection.execute("""CREATE TRIGGER reject_mapping BEFORE INSERT ON hook_activations
                                  BEGIN SELECT RAISE(ABORT, 'test rollback'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            allocation.allocate_empty(self.database, self.payload(turn_id="second-turn"))
        self.assertEqual(self.counts()["context_count"], 1)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM hook_activations").fetchone()[0], 1)

    def test_missing_context_on_retry_returns_not_found_without_replacement(self):
        allocation.allocate_empty(self.database, self.payload())
        with sqlite3.connect(self.database) as connection:
            connection.execute("DELETE FROM contexts")
        result = allocation.allocate_empty(self.database, self.payload())
        self.assertEqual(result["status"], "not_found")
        self.assertNotIn("context_id", result)
        self.assertEqual(self.counts()["context_count"], 0)

    def test_existing_record_values_are_never_read_or_captured_by_allocation(self):
        allocation.validate_private_database(self.database)
        with StructuredLedger(database=self.database) as ledger:
            previous = ledger.recall()
            ledger.capture(previous.context_id, records=[{"kind": "evidence", "value": "PRIVATE STORED CONTENT",
                "source": "verified_tool", "source_ref": "private-observation"}], capture_ref="old-capture")
        result = allocation.allocate_empty(self.database, self.payload())
        self.assertEqual(result["status"], "created")
        self.assertNotIn("PRIVATE STORED CONTENT", json.dumps(result))
        self.assertEqual(self.counts(), {"context_count": 2, "record_count": 1, "capture_count": 1})

    def test_native_process_receipt_is_returned_after_persisted_commit(self):
        result = subprocess.run(self.command(), input=json.dumps(self.payload()), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads((self.root / "journal.jsonl").read_text())
        self.assertEqual(row["response_sha256"], allocation.digest(json.loads(result.stdout)))
        self.assertIn(row["result"]["context_id"], result.stdout)
        self.assertEqual(self.counts(), {"context_count": 1, "record_count": 0, "capture_count": 0})

    def test_competing_native_process_retries_commit_one_context(self):
        processes = [subprocess.Popen(self.command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) for _ in range(6)]
        payload = json.dumps(self.payload())
        for process in processes:
            process.stdin.write(payload)
            process.stdin.close()
        outputs = []
        for process in processes:
            stdout, stderr = process.stdout.read(), process.stderr.read()
            self.assertEqual(process.wait(timeout=10), 0, stderr)
            process.stdout.close(); process.stderr.close()
            outputs.append(json.loads(stdout))
        self.assertTrue(all(value == outputs[0] for value in outputs))
        self.assertEqual(self.counts(), {"context_count": 1, "record_count": 0, "capture_count": 0})

    def test_journal_failure_after_commit_does_not_allocate_again_on_retry(self):
        (self.root / "journal.jsonl").mkdir()
        failed = subprocess.run(self.command(), input=json.dumps(self.payload()), text=True, capture_output=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.counts()["context_count"], 1)
        (self.root / "journal.jsonl").rmdir()
        retried = subprocess.run(self.command(), input=json.dumps(self.payload()), text=True, capture_output=True)
        self.assertEqual(retried.returncode, 0, retried.stderr)
        row = json.loads((self.root / "journal.jsonl").read_text())
        self.assertEqual(row["result"]["status"], "replayed")
        self.assertEqual(self.counts()["context_count"], 1)

    def test_duplicate_payload_keys_cannot_create_context(self):
        malformed = '{"hook_event_name":"Stop","hook_event_name":"UserPromptSubmit"}'
        result = subprocess.run(self.command(), input=malformed, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.database.exists())

    def test_nonprivate_database_or_symlink_is_rejected(self):
        target = self.root / "target"
        target.write_text("preserve")
        self.database.symlink_to(target)
        with self.assertRaises(ValueError):
            allocation.allocate_empty(self.database, self.payload())
        self.assertEqual(target.read_text(), "preserve")
        self.database.unlink()
        self.database.touch(mode=0o644)
        os.chmod(self.database, 0o644)
        with self.assertRaises(ValueError):
            allocation.allocate_empty(self.database, self.payload())


if __name__ == "__main__":
    unittest.main()
