from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import hashlib
import importlib.util
import json
import sqlite3
import stat
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "nerd-memory" / "scripts" / "memory.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("nerd_behavior_memory_security", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def episode(episode_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "episode_id": episode_id,
        "repository": "safe-repository",
        "language": "python",
        "surface": "api",
        "project_kind": "service",
        "raw_input": "test api",
        "action": "test",
        "tools": ["pytest"],
        "steps": ["inspect_tests", "run_pytest", "report"],
        "skills": ["create-unit-tests"],
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
        "source_agent": "agent-one",
        "evidence_ref": f"proof:{episode_id}",
    }
    value.update(overrides)
    return value


class BehaviorMemorySecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_engine()
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "private" / "behavior.sqlite3"
        self.store = self.engine.BehaviorMemoryStore(self.db)

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_database_and_created_directory_are_private_and_wal_is_enabled(self) -> None:
        self.assertEqual(stat.S_IMODE(self.db.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.db.stat().st_mode), 0o600)
        mode = self.store.connection.execute("PRAGMA journal_mode").fetchone()[0]
        timeout = self.store.connection.execute("PRAGMA busy_timeout").fetchone()[0]
        self.assertEqual(mode.lower(), "wal")
        self.assertGreaterEqual(timeout, 5000)

    def test_existing_explicit_parent_permissions_are_not_rewritten(self) -> None:
        existing = Path(self.temp.name) / "shared-parent"
        existing.mkdir(mode=0o755)
        existing.chmod(0o755)
        store = self.engine.BehaviorMemoryStore(existing / "behavior.sqlite3")
        store.close()

        self.assertEqual(stat.S_IMODE(existing.stat().st_mode), 0o755)

    def test_foreign_nonempty_database_fails_closed_without_mutation(self) -> None:
        self.store.close()
        self.db.unlink()
        connection = sqlite3.connect(self.db)
        connection.execute("PRAGMA user_version=91")
        connection.execute("CREATE TABLE foreign_data (value TEXT)")
        connection.execute("INSERT INTO foreign_data VALUES ('untouched')")
        connection.commit()
        before = list(connection.iterdump())
        before_version = connection.execute("PRAGMA user_version").fetchone()[0]
        connection.close()

        with self.assertRaises(self.engine.MemorySchemaError):
            self.engine.BehaviorMemoryStore(self.db)

        connection = sqlite3.connect(self.db)
        self.assertEqual(list(connection.iterdump()), before)
        self.assertEqual(
            connection.execute("PRAGMA user_version").fetchone()[0], before_version
        )
        connection.close()
        self.store = self.engine.BehaviorMemoryStore(
            Path(self.temp.name) / "replacement.sqlite3"
        )

    def test_other_schema_family_is_not_rewritten(self) -> None:
        self.store.connection.execute(
            "UPDATE metadata SET value='old-memory-family' WHERE key='schema_family'"
        )
        self.store.connection.commit()
        self.store.close()
        before = self.db.read_bytes()

        with self.assertRaises(self.engine.MemorySchemaError):
            self.engine.BehaviorMemoryStore(self.db)

        self.assertEqual(self.db.read_bytes(), before)
        self.store = self.engine.BehaviorMemoryStore(
            Path(self.temp.name) / "replacement.sqlite3"
        )

    def test_stale_handle_is_permanently_fenced(self) -> None:
        second = self.engine.BehaviorMemoryStore(self.db)
        second.connection.execute(
            "UPDATE metadata SET value='2' WHERE key='schema_version'"
        )
        second.connection.commit()
        with self.assertRaises(self.engine.MemorySchemaError):
            self.store.inspect()
        second.connection.execute(
            "UPDATE metadata SET value='1' WHERE key='schema_version'"
        )
        second.connection.commit()
        with self.assertRaises(self.engine.MemorySchemaError):
            self.store.inspect()
        second.close()

    def test_raw_input_secret_and_digest_are_never_persisted(self) -> None:
        secret = "sk-1234567890abcdefghijklmnop"
        raw = f"please test api with {secret}"
        self.store.record(**episode("secret-cue", raw_input=raw))
        database_material = "\n".join(self.store.connection.iterdump())
        self.assertNotIn(raw, database_material)
        self.assertNotIn(secret, database_material)
        self.assertNotIn(hashlib.sha256(raw.encode()).hexdigest(), database_material)
        stored = self.store.inspect()["episodes"][0]
        self.assertEqual(stored["command_cues"], ["api", "test"])

    def test_common_credential_families_are_removed_before_cue_storage(self) -> None:
        credentials = (
            "ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            "AKIAABCDEFGHIJKLMNOP",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signaturevalue123",
            "https://alice:correct-horse-battery@example.test/private",
        )
        for index, credential in enumerate(credentials):
            self.store.record(
                **episode(
                    f"credential-{index}",
                    raw_input=f"test api with {credential}",
                )
            )

        database_material = "\n".join(self.store.connection.iterdump())
        for credential in credentials:
            self.assertNotIn(credential, database_material)
        for item in self.store.inspect(limit=100)["episodes"]:
            self.assertEqual(item["command_cues"], ["api", "test"])

    def test_sensitive_or_executable_persisted_fields_are_rejected(self) -> None:
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(
                **episode("secret-step", steps=["token=abcdefghijklmnop123456"])
            )
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(**episode("shell-step", steps=["rm -rf /tmp/example"]))
        with self.assertRaises(TypeError):
            self.store.record(**episode("authority", permissions=["admin"]))

    def test_evidence_reference_rejects_transcript_executable_and_credentials(self) -> None:
        invalid_references = (
            "pytest passed after I retried the request",
            "proof:$(upload-output)",
            "proof:ghp_abcdefghijklmnopqrstuvwxyz1234567890",
        )
        for index, evidence_ref in enumerate(invalid_references):
            with self.subTest(evidence_ref=evidence_ref), self.assertRaises(
                self.engine.MemoryInputError
            ):
                self.store.record(
                    **episode(
                        f"invalid-proof-{index}",
                        evidence_ref=evidence_ref,
                    )
                )

    def test_authenticated_host_classification_not_agent_label_supplies_proof(self) -> None:
        self.assertIn(
            "authenticated host", self.engine.VERIFICATION_TRUST_BOUNDARY
        )
        self.assertIn("provenance only", self.engine.VERIFICATION_TRUST_BOUNDARY)
        recorded = self.store.record(
            **episode(
                "verified-subagent-proof",
                source_agent="subagent:worker-7",
                evidence_ref="proof:pytest:verified-subagent-proof",
            )
        )
        self.assertEqual(
            recorded["episode"]["source_agent"], "subagent:worker-7"
        )

        with self.assertRaises(self.engine.MemoryInputError):
            self.store.record(
                **episode(
                    "unverified-host-label",
                    verified=False,
                    source_agent="authenticated-host",
                    evidence_ref="proof:unverified-host-label",
                )
            )

    def test_concurrent_independent_handles_record_once_per_root_episode(self) -> None:
        self.store.close()

        def write(index: int) -> None:
            store = self.engine.BehaviorMemoryStore(self.db)
            try:
                store.record(**episode(f"parallel-{index % 12}"))
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(write, range(48)))

        self.store = self.engine.BehaviorMemoryStore(self.db)
        inspected = self.store.inspect(limit=100)
        self.assertEqual(inspected["counts"]["behavior_episodes"], 12)
        sequences = [item["sequence"] for item in inspected["episodes"]]
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(len(sequences), len(set(sequences)))

    def test_concurrent_first_open_initializes_one_clean_database(self) -> None:
        fresh_db = Path(self.temp.name) / "first-open" / "behavior.sqlite3"
        barrier = Barrier(16)

        def open_fresh(_: int) -> str:
            barrier.wait()
            store = self.engine.BehaviorMemoryStore(fresh_db)
            try:
                return store.inspect()["schema_family"]
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(open_fresh, range(16)))

        self.assertEqual(results, ["global-behavior-memory"] * 16)

    def test_canonical_json_is_stable_and_rejects_nonfinite_values(self) -> None:
        left = self.engine.canonical_json({"b": [2, 1], "a": "é"})
        right = self.engine.canonical_json({"a": "e\u0301", "b": [2, 1]})
        self.assertEqual(left, right)
        with self.assertRaises(self.engine.MemoryInputError):
            self.engine.canonical_json({"bad": float("nan")})

    def test_recall_audit_is_bounded_and_contains_no_current_authority(self) -> None:
        self.store.record(**episode("source"))
        current = {
            "action": "deploy",
            "tools": ["production-tool"],
            "steps": ["release"],
            "skills": ["private-skill"],
        }
        self.store.recall(
            event_id="audit-one",
            raw_input="test api",
            repository="repo-zeta",
            language="python",
            surface="api",
            project_kind="service",
            current=current,
            output_signals=[],
            consumer_agent="consumer",
        )
        row = self.store.connection.execute("SELECT * FROM recall_events").fetchone()
        material = json.dumps(dict(row), sort_keys=True)
        for forbidden in ("deploy", "production-tool", "release", "private-skill"):
            self.assertNotIn(forbidden, material)


if __name__ == "__main__":
    unittest.main()
