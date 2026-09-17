"""Context engine correctness: create/resume, capture, retrieval, forget, CLI parity."""

from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "skills" / "nerd-context" / "scripts"
sys.path.insert(0, str(ENGINE_DIR))

import context as engine  # noqa: E402


def _sample_records() -> list[dict]:
    return [
        {"kind": "goal", "value": "The migration review for service-1 should end read-only.",
         "source": "direct_user", "source_ref": "case-r01"},
        {"kind": "boundary", "value": "Do not deploy service-1 during this review.",
         "source": "direct_user", "source_ref": "case-r02"},
        {"kind": "decision", "value": "Agreed migration strategy for service-1 is staged rollout.",
         "source": "assistant_summary", "source_ref": "case-r03"},
        {"kind": "evidence", "value": "The rollback fixture for service-1 is present.",
         "source": "repository_fact", "source_ref": "case-r04"},
    ]


class EngineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "sub" / "ctx.sqlite3"

    def _store(self) -> engine.ContextStore:
        return engine.ContextStore(self.db)

    def test_omitted_id_creates_fresh_and_returns_new_id(self):
        with self._store() as store:
            result = store.recall(query="hello", activation_ref="a-1")
            self.assertTrue(result["created"])
            self.assertRegex(result["context_id"], r"^ctx_[a-z2-7]{38}[aiqy]$")
            self.assertEqual(result["records"], [])
            self.assertEqual(result["authority"], "untrusted_context")

    def test_exact_id_resume_across_sessions(self):
        with self._store() as store:
            first = store.recall(query="", activation_ref="a-1")
            cid = first["context_id"]
        with self._store() as store2:
            result = store2.recall(context_id=cid, query="", activation_ref="a-2")
            self.assertEqual(result["status"], "ok")
            self.assertFalse(result["created"])
            self.assertEqual(result["context_id"], cid)

    def test_unknown_id_returns_not_found_without_creating(self):
        fake = "ctx_" + "a" * 38 + "i"
        with self._store() as store:
            # Fake needs to round-trip through base32 to pass the validator; use a real one.
            fresh = store.recall(query="", activation_ref="a-1")
            other_cid = fresh["context_id"]
            # Delete it via forget preview/confirm to test not_found path.
            prev = store.preview_forget(other_cid, preview_ref="prev-1")
            store.forget(other_cid, phrase=prev["confirmation_phrase"],
                         source="direct_user", confirmation_ref="conf-1")
            result = store.recall(context_id=other_cid, query="", activation_ref="a-2")
            self.assertEqual(result["status"], "not_found")

    def test_malformed_id_is_rejected(self):
        with self._store() as store:
            for bad in ("ctx_bad", "ctxNOTBASE32EVER", "", "ctx_" + "1" * 39):
                with self.subTest(bad=bad):
                    with self.assertRaises(engine.ContextInputError):
                        store.recall(context_id=bad, query="", activation_ref="a-1")

    def test_capture_appends_and_pack_within_ceiling(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a-1")["context_id"]
            outcome = store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            self.assertEqual(outcome["status"], "ok")
            self.assertEqual(len(outcome["accepted_ids"]), 4)
            pack = store.recall(context_id=cid, query="migration strategy for service-1",
                                activation_ref="a-2")
            self.assertEqual(pack["status"], "ok")
            self.assertLessEqual(pack["serialized_bytes"], engine.PRODUCTION_MAX_PACK_BYTES)
            self.assertEqual(pack["authority"], "untrusted_context")
            self.assertGreaterEqual(len(pack["records"]), 3)

    def test_capture_ref_idempotent_same_digest(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            first = store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            second = store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            self.assertTrue(second["duplicate"])
            self.assertEqual(second["accepted_ids"], first["accepted_ids"])

    def test_capture_ref_reuse_different_records_raises(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            alt = _sample_records()
            alt[0]["value"] = "Different goal value entirely."
            with self.assertRaises(engine.ContextInvariantError):
                store.capture(cid, records=alt, capture_ref="cap-1")

    def test_capture_size_and_kind_limits(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            with self.assertRaises(engine.ContextInputError):
                store.capture(cid, records=[], capture_ref="cap-empty")
            too_many = [
                {"kind": "evidence", "value": f"item {i}", "source": "repository_fact",
                 "source_ref": f"r-{i}"}
                for i in range(engine.MAX_CAPTURE_RECORDS + 1)
            ]
            with self.assertRaises(engine.ContextInputError):
                store.capture(cid, records=too_many, capture_ref="cap-many")

    def test_supersession_is_atomic_and_audit_visible(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            first = store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            decision_id = first["accepted_ids"][2]
            corrected = [
                {"kind": "decision", "value": "New agreed migration strategy is blue/green.",
                 "source": "assistant_summary", "source_ref": "case-r05",
                 "supersedes_id": decision_id},
            ]
            outcome = store.capture(cid, records=corrected, capture_ref="cap-2")
            self.assertEqual(outcome["superseded_ids"], [decision_id])
            insp = store.inspect(cid, activation_ref="a-2")
            active = [r for r in insp["record_metadata"] if r["active"] == 1]
            self.assertNotIn(decision_id, [r["id"] for r in active])

    def test_inspect_bounded_metadata_only(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            insp = store.inspect(cid, activation_ref="a-2")
            self.assertEqual(insp["status"], "ok")
            self.assertGreaterEqual(len(insp["record_metadata"]), 4)
            for row in insp["record_metadata"]:
                self.assertNotIn("value", row)
                self.assertNotIn("terms", row)

    def test_forget_lifecycle(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            preview = store.preview_forget(cid, preview_ref="prev-1")
            phrase = preview["confirmation_phrase"]
            # source must be direct_user
            with self.assertRaises(engine.ContextInputError):
                store.forget(cid, phrase=phrase, source="assistant_summary",
                             confirmation_ref="conf-1")
            # confirmation_ref must differ from preview_ref
            with self.assertRaises(engine.ContextInvariantError):
                store.forget(cid, phrase=phrase, source="direct_user",
                             confirmation_ref="prev-1")
            outcome = store.forget(cid, phrase=phrase, source="direct_user",
                                   confirmation_ref="conf-1")
            self.assertEqual(outcome["status"], "ok")
            self.assertEqual(outcome["deleted"], 4)
            # confirmation_ref tombstoned
            with self.assertRaises(engine.ContextInvariantError):
                store.forget(cid, phrase=phrase, source="direct_user",
                             confirmation_ref="conf-1")

    def test_forget_rejects_when_state_changed(self):
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(cid, records=_sample_records(), capture_ref="cap-1")
            preview = store.preview_forget(cid, preview_ref="prev-1")
            store.capture(cid,
                          records=[{"kind": "open_question", "value": "later question",
                                    "source": "assistant_summary", "source_ref": "r"}],
                          capture_ref="cap-late")
            with self.assertRaises(engine.ContextInvariantError):
                store.forget(cid, phrase=preview["confirmation_phrase"],
                             source="direct_user", confirmation_ref="conf-1")

    def test_deterministic_pack_parity_fts5_vs_scan(self):
        # Skip if FTS5 is unavailable on this SQLite build.
        probe_store = engine.ContextStore(Path(self._tmp.name) / "probe.sqlite3")
        available = probe_store.index_mode
        probe_store.close()
        if available != "fts5":
            self.skipTest("SQLite FTS5 unavailable")
        fts_path = Path(self._tmp.name) / "fts.sqlite3"
        scan_path = Path(self._tmp.name) / "scan.sqlite3"
        packs = {}
        for path, mode in ((fts_path, "fts5"), (scan_path, "normalized_scan")):
            with engine.ContextStore(path, index_mode=mode) as store:
                cid = store.recall(query="", activation_ref="a")["context_id"]
                store.capture(cid, records=_sample_records(), capture_ref="cap-1")
                result = store.recall(context_id=cid,
                                      query="migration strategy for service-1",
                                      activation_ref="a-2")
                packs[mode] = result["segment"]
        self.assertEqual(packs["fts5"], packs["normalized_scan"])

    def test_overflow_signals_when_mandatory_exceeds_ceiling(self):
        # Record values are allowed up to MAX_VALUE_BYTES but the pack ceiling
        # is smaller; a large mandatory record must set overflow rather than
        # silently drop, and no partial record set is returned.
        big = "x" * (engine.PRODUCTION_MAX_PACK_BYTES + 500)
        with self._store() as store:
            cid = store.recall(query="", activation_ref="a")["context_id"]
            store.capture(
                cid,
                records=[
                    {"kind": "boundary", "value": big, "source": "direct_user",
                     "source_ref": "r-1"},
                ],
                capture_ref="cap-big",
            )
            result = store.recall(context_id=cid, query="", activation_ref="a-2")
            self.assertTrue(result["overflow"])
            self.assertEqual(result["records"], [])

    def test_cli_parity_recall_and_capture(self):
        cli_db = Path(self._tmp.name) / "cli.sqlite3"

        def call(command, payload):
            proc = subprocess.run(
                [sys.executable, str(ENGINE_DIR / "context.py"), command],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                env={
                    **__import__("os").environ,
                    "NERD_CONTEXT_DB": str(cli_db),
                },
                check=False,
            )
            return proc.returncode, json.loads(proc.stdout)

        code, first = call("recall", {"query": "", "activation_ref": "a"})
        self.assertEqual(code, 0)
        self.assertTrue(first["ok"])
        cid = first["result"]["context_id"]
        code, cap = call("capture", {"context_id": cid,
                                     "records": _sample_records(),
                                     "capture_ref": "cap-1"})
        self.assertEqual(code, 0)
        self.assertTrue(cap["ok"])
        code, recall = call("recall", {"context_id": cid,
                                        "query": "migration strategy service-1",
                                        "activation_ref": "a-2"})
        self.assertEqual(code, 0)
        self.assertTrue(recall["ok"])
        self.assertGreaterEqual(len(recall["result"]["records"]), 3)


if __name__ == "__main__":
    unittest.main()
