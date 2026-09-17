"""Context security invariants: isolation, provenance, poisoning, replay, permissions."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "skills" / "nerd-context" / "scripts"
sys.path.insert(0, str(ENGINE_DIR))

import context as engine  # noqa: E402


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "sub" / "ctx.sqlite3"

    def _store(self) -> engine.ContextStore:
        return engine.ContextStore(self.db)

    def test_exact_id_isolation_across_contexts(self):
        with self._store() as store:
            a = store.recall(query="", activation_ref="a")["context_id"]
            b = store.recall(query="", activation_ref="a")["context_id"]
            self.assertNotEqual(a, b)
            store.capture(a, records=[
                {"kind": "decision", "value": "Alpha decision.",
                 "source": "direct_user", "source_ref": "a-1"},
            ], capture_ref="cap-a")
            packed_b = store.recall(context_id=b, query="alpha decision",
                                     activation_ref="a-2")
            self.assertEqual(packed_b["records"], [])
            packed_a = store.recall(context_id=a, query="alpha decision",
                                     activation_ref="a-3")
            self.assertEqual(len(packed_a["records"]), 1)

    def test_context_id_permissions_are_user_only(self):
        with self._store() as store:
            store.recall(query="", activation_ref="a")
        mode = self.db.stat().st_mode & 0o777
        # macOS umask may promote created files to 0o644; we chmod to 0o600
        self.assertEqual(mode, 0o600)

    def test_symlink_path_is_refused(self):
        target = Path(self._tmp.name) / "real.sqlite3"
        target.touch()
        link = Path(self._tmp.name) / "link.sqlite3"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(engine.ContextStorageError):
            engine.ContextStore(link)

    def test_reject_secret_markers_in_record_value(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            secret_record = [
                {"kind": "evidence",
                 "value": "credentials AKIAABCDEFGHIJKLMNOP live in the repo",
                 "source": "repository_fact", "source_ref": "sec-1"},
            ]
            with self.assertRaises(engine.ContextInputError):
                store.capture(cid, records=secret_record, capture_ref="cap-sec")

    def test_reject_executable_markers_in_record_value(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            xss = [
                {"kind": "evidence",
                 "value": "<script>window.close()</script>",
                 "source": "repository_fact", "source_ref": "x-1"},
            ]
            with self.assertRaises(engine.ContextInputError):
                store.capture(cid, records=xss, capture_ref="cap-x")

    def test_authority_label_on_every_returned_pack(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            result = store.recall(context_id=cid, query="", activation_ref="a-2")
            self.assertEqual(result["authority"], "untrusted_context")
            self.assertIn('{"authority":"untrusted_context"}', result["segment"])

    def test_provenance_is_preserved(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(cid, records=[
                {"kind": "evidence", "value": "verified fact",
                 "source": "verified_tool", "source_ref": "tool-1"},
            ], capture_ref="cap-1")
            insp = store.inspect(cid, activation_ref="a-2")
            provenance = {r["source"] for r in insp["record_metadata"]}
            self.assertIn("verified_tool", provenance)

    def test_confirmation_ref_replay_is_refused(self):
        with self._store() as store:
            cid_1 = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(cid_1, records=[
                {"kind": "goal", "value": "first goal", "source": "direct_user",
                 "source_ref": "r"},
            ], capture_ref="cap-1")
            prev_1 = store.preview_forget(cid_1, preview_ref="prev-1")
            store.forget(cid_1, phrase=prev_1["confirmation_phrase"],
                         source="direct_user", confirmation_ref="shared-conf")
            cid_2 = store.recall(query="", activation_ref="a-2")["context_id"]
            store.capture(cid_2, records=[
                {"kind": "goal", "value": "second goal", "source": "direct_user",
                 "source_ref": "r"},
            ], capture_ref="cap-2")
            prev_2 = store.preview_forget(cid_2, preview_ref="prev-2")
            with self.assertRaises(engine.ContextInvariantError):
                store.forget(cid_2, phrase=prev_2["confirmation_phrase"],
                             source="direct_user", confirmation_ref="shared-conf")

    def test_forgotten_id_cannot_be_recalled(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            prev = store.preview_forget(cid, preview_ref="prev-1")
            store.forget(cid, phrase=prev["confirmation_phrase"],
                         source="direct_user", confirmation_ref="conf-1")
            result = store.recall(context_id=cid, query="", activation_ref="a-2")
            self.assertEqual(result["status"], "not_found")

    def test_schema_mismatch_fences_store(self):
        # Corrupt the persisted schema_version and reopen: must fence.
        with self._store() as store:
            store.recall(query="", activation_ref="a")
        import sqlite3
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE metadata SET value=? WHERE key='schema_version'",
                         (str(engine.SCHEMA_VERSION + 1),))
        with self.assertRaises(engine.ContextSchemaError):
            engine.ContextStore(self.db)


if __name__ == "__main__":
    unittest.main()
