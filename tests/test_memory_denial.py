from __future__ import annotations

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "nerd-memory" / "scripts" / "memory.py"


def load_engine():
    spec = importlib.util.spec_from_file_location(
        "nerd_memory_denial_engine",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def empty_endpoint() -> dict[str, object]:
    return {
        "endpoint": "execute",
        "goal": None,
        "task": [],
        "action": [],
        "result": None,
        "boundary": [],
        "verification": [],
        "routing": [],
    }


def promote_pattern(store, pattern_id: str) -> dict[str, object]:
    return store.promote(
        pattern_id,
        source="direct_user",
        confirmation_ref=f"trusted-promotion:{pattern_id}",
        invocation_authorized=True,
    )


def forget_pattern(store, pattern_id: str) -> dict[str, object]:
    preview = store.preview_forget(pattern_id)
    return store.forget(
        pattern_id,
        preview["confirmation_phrase"],
        source="direct_user",
        confirmation_ref=f"trusted-forget:{pattern_id}",
    )


def drop_version_fences(connection: sqlite3.Connection) -> None:
    names = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' "
            "AND name LIKE 'nerd_memory_version_fence_%'"
        ).fetchall()
    ]
    for name in names:
        connection.execute(f'DROP TRIGGER "{name}"')


class MemoryDenialTests(unittest.TestCase):
    def setUp(self):
        self.engine = load_engine()
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.store = self.engine.MemoryStore(self.db)
        self.namespace = "user:denial-test"
        self.store.enable(self.namespace, consent_ref="denial-suite:enable")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def make_pattern(
        self,
        *,
        pattern_type: str = "action",
        pattern_key: str = "workflow",
        value: object = None,
        scope: dict[str, object] | None = None,
    ) -> dict[str, object]:
        for index in range(3):
            self.store.observe(
                namespace=self.namespace,
                episode_id=f"{pattern_key}:support:{index}",
                pattern_type=pattern_type,
                pattern_key=pattern_key,
                value=value if value is not None else ["use the default workflow"],
                scope=scope or {"repo": "nerd"},
                triggers=["build"],
                operation="fill",
                source="direct_user",
                evidence_ref=f"evidence:{pattern_key}:{index}",
            )
        candidates = self.store.consolidate(self.namespace, min_episodes=3)
        candidate = next(item for item in candidates if item["pattern_key"] == pattern_key)
        return promote_pattern(self.store, candidate["pattern_id"])

    def propose(
        self,
        *,
        episode_id: str,
        context: dict[str, object] | None = None,
        baseline: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return self.store.propose(
            namespace=self.namespace,
            episode_id=episode_id,
            input_text="Build this feature",
            context=context or {"repo": "nerd", "surface": "cli"},
            baseline=baseline or empty_endpoint(),
        )

    def deny(
        self,
        proposal: dict[str, object],
        *,
        denial_ref: str | None = None,
        source: str = "direct_user",
    ) -> dict[str, object]:
        return self.store.deny(
            proposal["proposal_id"],
            source=source,
            denial_ref=denial_ref or f"trusted-denial:{proposal['proposal_id']}",
        )

    def draft_split(
        self,
        denial: dict[str, object],
        parent: dict[str, object],
        *,
        exception_scope: dict[str, object] | None = None,
        exception_value: object = None,
    ) -> dict[str, object]:
        return self.store.propose_split(
            denial["denial_id"],
            input_text="Build this feature",
            context={"repo": "nerd", "surface": "cli"},
            splits=[
                {
                    "parent_pattern_id": parent["pattern_id"],
                    "exception_scope": exception_scope
                    or {"repo": "nerd", "surface": "cli"},
                    "exception_value": exception_value
                    if exception_value is not None
                    else ["use the CLI-specific workflow"],
                }
            ],
        )

    def confirm_split(
        self,
        split: dict[str, object],
        *,
        phrase: str | None = None,
        confirmation_ref: str | None = None,
        source: str = "direct_user",
    ) -> dict[str, object]:
        return self.store.confirm_split(
            split["split_id"],
            phrase or split["confirmation_phrase"],
            source=source,
            confirmation_ref=(
                confirmation_ref or f"trusted-split:{split['split_id']}"
            ),
        )

    def test_denial_kills_recommendation_without_rewriting_memory(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="denied-after-confirmation")
        grant = self.store.confirm(
            proposal["proposal_id"],
            proposal["confirmation_phrase"],
            source="direct_user",
            confirmation_ref="trusted-event:original-confirmation",
        )
        before = self.store.get_pattern(parent["pattern_id"])

        denial = self.deny(proposal)

        self.assertEqual(denial["status"], "needs_diagnosis")
        self.assertIsNone(denial["resolution"])
        self.assertEqual(
            set(denial["possibilities"]),
            {"agent_mistake", "human_forgot", "route_too_generic"},
        )
        self.assertEqual(denial["memory_blind_baseline"], empty_endpoint())
        self.assertEqual(
            denial["denied_endpoint"]["action"],
            ["use the default workflow"],
        )
        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"],
            "denied",
        )
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.store.consume(proposal["proposal_id"], grant["grant_token"])
        after = self.store.get_pattern(parent["pattern_id"])
        self.assertEqual(after["status"], "confirmed")
        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(after["evidence"], before["evidence"])

    def test_denial_requires_direct_unique_event_and_is_atomic(self):
        self.make_pattern()
        first = self.propose(episode_id="first-denial")
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.deny(first, source="agent_inference")
        self.assertEqual(
            self.store.get_proposal(first["proposal_id"])["status"],
            "pending_confirmation",
        )

        shared_ref = "trusted-event:one-denial-only"
        self.deny(first, denial_ref=shared_ref)
        second = self.propose(episode_id="second-denial")
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.deny(second, denial_ref=shared_ref)
        self.assertEqual(
            self.store.get_proposal(second["proposal_id"])["status"],
            "pending_confirmation",
        )

    def test_trusted_event_cannot_cross_confirm_deny_or_split_boundaries(self):
        parent = self.make_pattern()
        confirmed_proposal = self.propose(episode_id="event-confirmed")
        shared_confirmation_ref = "trusted-event:cross-transition"
        self.store.confirm(
            confirmed_proposal["proposal_id"],
            confirmed_proposal["confirmation_phrase"],
            source="direct_user",
            confirmation_ref=shared_confirmation_ref,
        )

        denied_proposal = self.propose(episode_id="event-denied")
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.deny(denied_proposal, denial_ref=shared_confirmation_ref)
        denial = self.deny(
            denied_proposal,
            denial_ref="trusted-event:actual-denial",
        )
        split = self.draft_split(denial, parent)
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm_split(
                split,
                confirmation_ref="trusted-event:actual-denial",
            )

    def test_consume_and_deny_race_has_exactly_one_winner(self):
        self.make_pattern()
        proposal = self.propose(episode_id="deny-consume-race")
        grant = self.store.confirm(
            proposal["proposal_id"],
            proposal["confirmation_phrase"],
            source="direct_user",
            confirmation_ref="trusted-event:race-confirm",
        )
        barrier = threading.Barrier(2)

        def consume() -> str:
            with self.engine.MemoryStore(self.db) as store:
                barrier.wait(timeout=5)
                try:
                    store.consume(proposal["proposal_id"], grant["grant_token"])
                    return "consumed"
                except self.engine.MemoryInvariantError:
                    return "consume_rejected"

        def deny() -> str:
            with self.engine.MemoryStore(self.db) as store:
                barrier.wait(timeout=5)
                try:
                    store.deny(
                        proposal["proposal_id"],
                        source="direct_user",
                        denial_ref="trusted-event:race-denial",
                    )
                    return "denied"
                except self.engine.MemoryInvariantError:
                    return "denial_rejected"

        with ThreadPoolExecutor(max_workers=2) as pool:
            consume_future = pool.submit(consume)
            deny_future = pool.submit(deny)
            results = {consume_future.result(), deny_future.result()}

        self.assertIn(results, ({"consumed", "denial_rejected"}, {"denied", "consume_rejected"}))
        self.assertIn(
            self.store.get_proposal(proposal["proposal_id"])["status"],
            {"consumed", "denied"},
        )

    def test_non_generic_resolutions_do_not_create_or_reactivate_patterns(self):
        parent = self.make_pattern()
        for resolution in ("agent_mistake", "human_forgot"):
            with self.subTest(resolution=resolution):
                proposal = self.propose(episode_id=f"resolution:{resolution}")
                denial = self.deny(proposal)
                resolved = self.store.resolve_denial(
                    denial["denial_id"],
                    resolution=resolution,
                    confirmation=denial["resolution_phrases"][resolution],
                    source="direct_user",
                    resolution_ref=f"trusted-resolution:{resolution}",
                )
                self.assertEqual(resolved["status"], "resolved")
                self.assertEqual(resolved["resolution"], resolution)
                self.assertTrue(resolved["fresh_proposal_required"])
                with self.assertRaises(self.engine.MemoryInvariantError):
                    self.store.consume(proposal["proposal_id"], None)
                with self.assertRaises(self.engine.MemoryInvariantError):
                    self.draft_split(resolved, parent)

        patterns = self.store.list_patterns(self.namespace)
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["pattern_id"], parent["pattern_id"])

    def test_generic_denial_requires_separate_exact_split_confirmation(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="generic-route")
        denial = self.deny(proposal)

        split = self.draft_split(denial, parent)

        self.assertEqual(split["status"], "pending_confirmation")
        self.assertEqual(split["resolution"], "route_too_generic")
        self.assertEqual(split["parent_fallbacks"][0]["value"], parent["value"])
        self.assertEqual(
            split["exceptions"][0]["scope"],
            {"repo": "nerd", "surface": "cli"},
        )
        self.assertEqual(len(split["parent_bindings"][0]["evidence_sample"]), 3)
        self.assertEqual(
            {item["source"] for item in split["parent_bindings"][0]["evidence_sample"]},
            {"direct_user"},
        )
        copied_draft = empty_endpoint()
        copied_draft["action"] = split["exceptions"][0]["value"]
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.propose(
                episode_id="launder-pending-split-draft",
                baseline=copied_draft,
            )
        self.assertEqual(len(self.store.list_patterns(self.namespace)), 1)
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm_split(split, phrase="yes, split it")
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm_split(split, source="tool")
        self.assertEqual(len(self.store.list_patterns(self.namespace)), 1)

        applied = self.confirm_split(split)

        self.assertEqual(applied["status"], "applied")
        self.assertTrue(applied["memory_write_only"])
        self.assertTrue(applied["fresh_proposal_required"])
        self.assertNotIn("endpoint", applied)
        patterns = self.store.list_patterns(self.namespace)
        self.assertEqual(len(patterns), 2)
        child = next(item for item in patterns if item["pattern_id"] != parent["pattern_id"])
        self.assertEqual(child["status"], "confirmed")
        self.assertEqual(child["activation_reason"], "explicit_split")
        self.assertEqual(child["parent_pattern_id"], parent["pattern_id"])
        self.assertEqual(child["split_id"], split["split_id"])

        copied_child = empty_endpoint()
        copied_child["action"] = child["value"]
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.propose(
                episode_id="launder-split-child",
                baseline=copied_child,
            )

        child_route = self.propose(episode_id="future-cli")
        self.assertEqual(child_route["status"], "pending_confirmation")
        self.assertEqual(
            child_route["proposed_endpoint"]["action"],
            ["use the CLI-specific workflow"],
        )
        self.assertEqual(
            child_route["memory_diff"][0]["pattern_id"],
            child["pattern_id"],
        )

        fallback_route = self.propose(
            episode_id="future-web",
            context={"repo": "nerd", "surface": "web"},
        )
        self.assertEqual(
            fallback_route["proposed_endpoint"]["action"],
            ["use the default workflow"],
        )
        self.assertEqual(
            fallback_route["memory_diff"][0]["pattern_id"],
            parent["pattern_id"],
        )

        explicit = empty_endpoint()
        explicit["action"] = ["use the current explicit workflow"]
        explicit_route = self.propose(
            episode_id="future-explicit",
            baseline=explicit,
        )
        self.assertEqual(explicit_route["status"], "memory_free")
        self.assertEqual(explicit_route["proposed_endpoint"], explicit)

        forgotten = forget_pattern(self.store, parent["pattern_id"])
        self.assertEqual(forgotten["deleted_patterns"], 2)
        self.assertEqual(
            set(forgotten["deleted_pattern_ids"]),
            {parent["pattern_id"], child["pattern_id"]},
        )
        self.assertEqual(self.store.list_patterns(self.namespace), [])
        redacted_split = self.store.get_split(split["split_id"])
        self.assertEqual(redacted_split["status"], "forgotten")
        self.assertEqual(redacted_split["parent_fallbacks"], [])
        self.assertEqual(redacted_split["exceptions"], [])
        self.assertNotIn("resolution", redacted_split)
        self.assertIn("inert tombstone", redacted_split["effect"])
        self.assertEqual(redacted_split["parent_bindings"], [])
        self.assertEqual(redacted_split["unselected_bindings"], [])
        self.assertNotIn("confirmation_phrase", redacted_split)
        self.assertIsNone(redacted_split["confirmation_source"])
        self.assertIsNone(redacted_split["confirmation_ref"])
        redacted_denial = self.store.get_denial(denial["denial_id"])
        self.assertEqual(redacted_denial["status"], "forgotten")
        self.assertEqual(redacted_denial["denial_ref"], "[forgotten]")
        self.assertEqual(redacted_denial["applied_bindings"], [])
        self.assertIsNone(redacted_denial["denied_endpoint"])
        self.assertIsNone(redacted_denial["memory_blind_baseline"])
        self.assertIsNone(redacted_denial["resolution_ref"])
        self.assertNotIn("possibilities", redacted_denial)
        self.assertNotIn("possibility_effects", redacted_denial)
        self.assertNotIn("resolution_phrases", redacted_denial)

    def test_split_rejects_non_specific_mismatched_and_unbound_branches(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="invalid-splits")
        denial = self.deny(proposal)
        other = self.make_pattern(
            pattern_type="verification",
            pattern_key="verification-rule",
            value=["run focused tests"],
        )

        invalid_specs = (
            {
                "parent_pattern_id": parent["pattern_id"],
                "exception_scope": {"repo": "nerd"},
                "exception_value": ["not specific"],
            },
            {
                "parent_pattern_id": parent["pattern_id"],
                "exception_scope": {"repo": "nerd", "surface": "web"},
                "exception_value": ["does not match this case"],
            },
            {
                "parent_pattern_id": other["pattern_id"],
                "exception_scope": {"repo": "nerd", "surface": "cli"},
                "exception_value": ["was not applied"],
            },
            {
                "parent_pattern_id": parent["pattern_id"],
                "exception_scope": {
                    "repo": "nerd",
                    "surface": "cli",
                    "turnId": "volatile-turn",
                },
                "exception_value": ["volatile routing"],
            },
        )
        for spec in invalid_specs:
            with self.subTest(spec=spec):
                with self.assertRaises(self.engine.MemoryInputError):
                    self.store.propose_split(
                        denial["denial_id"],
                        input_text="Build this feature",
                        context={"repo": "nerd", "surface": "cli"},
                        splits=[spec],
                    )

        with self.assertRaises(self.engine.MemoryInputError):
            self.draft_split(
                denial,
                parent,
                exception_scope={
                    "repo": "nerd",
                    "surface": "cli",
                    "api_key": "sk-proj-secret-material-that-must-not-persist",
                },
            )

    def test_denied_generic_execution_stack_can_split_into_a_confirmed_route(self):
        parent_route = [
            {
                "agent": "codex",
                "skills": ["nerd-smart"],
                "tools": ["web.run"],
                "mcp_servers": [],
            }
        ]
        cli_route = [
            {
                "agent": "claude",
                "skills": ["repository-review"],
                "tools": ["shell"],
                "mcp_servers": ["github"],
            }
        ]
        parent = self.make_pattern(
            pattern_type="routing",
            pattern_key="execution-stack",
            value=parent_route,
        )
        proposal = self.propose(episode_id="generic-stack-denied")
        denial = self.deny(proposal)
        split = self.draft_split(
            denial,
            parent,
            exception_value=cli_route,
        )
        applied = self.confirm_split(split)
        self.assertTrue(applied["memory_write_only"])
        self.assertNotIn("endpoint", applied)

        cli_proposal = self.propose(episode_id="fresh-cli-stack")
        self.assertEqual(
            cli_proposal["proposed_endpoint"]["routing"],
            cli_route,
        )
        self.assertEqual(cli_proposal["status"], "pending_confirmation")
        web_proposal = self.propose(
            episode_id="fresh-web-stack",
            context={"repo": "nerd", "surface": "web"},
        )
        self.assertEqual(
            web_proposal["proposed_endpoint"]["routing"],
            parent_route,
        )
        self.assertEqual(web_proposal["status"], "pending_confirmation")

    def test_child_only_forget_redacts_denial_without_deleting_parent_route(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="child-only-forget")
        denial = self.deny(proposal)
        split = self.draft_split(denial, parent)
        applied = self.confirm_split(split)
        child = applied["created_patterns"][0]

        forgotten = forget_pattern(self.store, child["pattern_id"])

        self.assertEqual(forgotten["deleted_pattern_ids"], [child["pattern_id"]])
        surviving = self.store.list_patterns(self.namespace)
        self.assertEqual([item["pattern_id"] for item in surviving], [parent["pattern_id"]])
        self.assertEqual(surviving[0]["status"], "confirmed")
        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"],
            "denied",
        )
        redacted_split = self.store.get_split(split["split_id"])
        self.assertEqual(redacted_split["status"], "forgotten")
        self.assertEqual(redacted_split["parent_fallbacks"], [])
        self.assertEqual(redacted_split["exceptions"], [])
        self.assertEqual(redacted_split["parent_bindings"], [])
        self.assertEqual(redacted_split["unselected_bindings"], [])
        self.assertNotIn("resolution", redacted_split)
        self.assertNotIn("confirmation_phrase", redacted_split)
        self.assertIn("inert tombstone", redacted_split["effect"])
        redacted_denial = self.store.get_denial(denial["denial_id"])
        self.assertEqual(redacted_denial["status"], "forgotten")
        self.assertEqual(redacted_denial["applied_bindings"], [])
        self.assertIsNone(redacted_denial["denied_endpoint"])
        self.assertIsNone(redacted_denial["memory_blind_baseline"])

    def test_parent_revision_and_consent_changes_invalidate_pending_split(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="stale-split")
        denial = self.deny(proposal)
        split = self.draft_split(denial, parent)

        self.store.observe(
            namespace=self.namespace,
            episode_id="new-parent-support",
            pattern_type="action",
            pattern_key="workflow",
            value=["use the default workflow"],
            scope={"repo": "nerd"},
            triggers=["build"],
            operation="fill",
            source="direct_user",
            evidence_ref="evidence:new-parent-support",
        )
        self.store.consolidate(self.namespace, min_episodes=3)

        self.assertEqual(self.store.get_split(split["split_id"])["status"], "invalidated")
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm_split(split)

        fresh_proposal = self.propose(episode_id="consent-stale-split")
        fresh_denial = self.deny(fresh_proposal)
        fresh_split = self.draft_split(fresh_denial, self.store.get_pattern(parent["pattern_id"]))
        self.store.disable(
            self.namespace,
            consent_ref="trusted-event:disable-after-split",
        )
        self.store.enable(
            self.namespace,
            consent_ref="trusted-event:enable-after-split",
        )
        self.assertEqual(
            self.store.get_split(fresh_split["split_id"])["status"],
            "invalidated",
        )
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm_split(fresh_split)

    def test_split_expiry_fails_closed(self):
        self.store.close()
        now = [1_000.0]
        self.store = self.engine.MemoryStore(
            self.db,
            grant_ttl_seconds=5,
            clock=lambda: now[0],
        )
        parent = self.make_pattern()
        proposal = self.propose(episode_id="expiring-split")
        denial = self.deny(proposal)
        split = self.draft_split(denial, parent)
        now[0] += 6

        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm_split(split)
        self.assertEqual(len(self.store.list_patterns(self.namespace)), 1)

    def test_returned_split_mutation_cannot_change_persisted_child(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="mutated-split-object")
        denial = self.deny(proposal)
        split = self.draft_split(denial, parent)
        split["exceptions"][0]["value"] = ["client-side tampering"]

        applied = self.confirm_split(split)

        self.assertEqual(
            applied["created_patterns"][0]["value"],
            ["use the CLI-specific workflow"],
        )

    def test_v3_store_migrates_lineage_schema_and_invalidates_live_proposals(self):
        parent = self.make_pattern()
        proposal = self.propose(episode_id="pre-migration-proposal")
        self.store.close()
        connection = sqlite3.connect(self.db)
        try:
            drop_version_fences(connection)
            connection.execute("DROP TABLE split_parent_bindings")
            connection.execute("DROP TABLE split_proposals")
            connection.execute("DROP TABLE denials")
            connection.execute("ALTER TABLE patterns DROP COLUMN split_id")
            connection.execute("ALTER TABLE patterns DROP COLUMN parent_pattern_id")
            connection.execute("ALTER TABLE patterns DROP COLUMN activation_reason")
            connection.execute(
                "UPDATE metadata SET value = '3' WHERE key = 'schema_version'"
            )
            connection.commit()
        finally:
            connection.close()

        self.store = self.engine.MemoryStore(self.db)

        columns = {
            row[1]
            for row in self.store._connection.execute(
                "PRAGMA table_info(patterns)"
            ).fetchall()
        }
        self.assertTrue(
            {"activation_reason", "parent_pattern_id", "split_id"} <= columns
        )
        migrated_parent = self.store.get_pattern(parent["pattern_id"])
        self.assertEqual(migrated_parent["activation_reason"], "consolidated")
        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"],
            "invalidated",
        )

    def test_failed_schema_migration_rolls_back_every_change_atomically(self):
        self.make_pattern()
        proposal = self.propose(episode_id="migration-rollback-proposal")
        self.store.close()
        connection = sqlite3.connect(self.db)
        try:
            drop_version_fences(connection)
            connection.execute("DROP TABLE split_parent_bindings")
            connection.execute("DROP TABLE split_proposals")
            connection.execute("DROP TABLE denials")
            connection.execute("ALTER TABLE patterns DROP COLUMN split_id")
            connection.execute("ALTER TABLE patterns DROP COLUMN parent_pattern_id")
            connection.execute("ALTER TABLE patterns DROP COLUMN activation_reason")
            connection.execute(
                "UPDATE metadata SET value = '3' WHERE key = 'schema_version'"
            )
            connection.execute(
                """
                CREATE TRIGGER force_migration_failure
                BEFORE UPDATE ON proposals
                WHEN NEW.invalid_reason = 'schema_migrated'
                BEGIN
                    SELECT RAISE(ABORT, 'forced migration failure');
                END
                """
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self.store = self.engine.MemoryStore(self.db)

        connection = sqlite3.connect(self.db)
        try:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(patterns)").fetchall()
            }
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            version = connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()[0]
            status = connection.execute(
                "SELECT status FROM proposals WHERE proposal_id = ?",
                (proposal["proposal_id"],),
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertFalse(
            {"activation_reason", "parent_pattern_id", "split_id"} & columns
        )
        self.assertFalse(
            {"denials", "split_proposals", "split_parent_bindings"} & tables
        )
        self.assertEqual(version, "3")
        self.assertEqual(status, "pending_confirmation")

    def test_composite_endpoint_split_is_atomic_and_exposes_unselected_bindings(self):
        action = self.make_pattern()
        verification = self.make_pattern(
            pattern_type="verification",
            pattern_key="proof",
            value=["run the default proof"],
        )
        proposal = self.propose(episode_id="composite-split")
        denial = self.deny(proposal)

        partial = self.draft_split(denial, action)
        self.assertEqual(
            [item["pattern_id"] for item in partial["unselected_bindings"]],
            [verification["pattern_id"]],
        )

        composite = self.store.propose_split(
            denial["denial_id"],
            input_text="Build this feature",
            context={"repo": "nerd", "surface": "cli"},
            splits=[
                {
                    "parent_pattern_id": action["pattern_id"],
                    "exception_scope": {"repo": "nerd", "surface": "cli"},
                    "exception_value": ["use the CLI-specific workflow"],
                },
                {
                    "parent_pattern_id": verification["pattern_id"],
                    "exception_scope": {"repo": "nerd", "surface": "cli"},
                    "exception_value": ["run the CLI-specific proof"],
                },
            ],
        )
        applied = self.confirm_split(composite)

        self.assertEqual(len(applied["created_patterns"]), 2)
        route = self.propose(episode_id="future-composite")
        self.assertEqual(
            route["proposed_endpoint"]["action"],
            ["use the CLI-specific workflow"],
        )
        self.assertEqual(
            route["proposed_endpoint"]["verification"],
            ["run the CLI-specific proof"],
        )


class MemoryDenialCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.namespace = "user:denial-cli"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *arguments: str) -> dict[str, object] | list[object]:
        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--db",
                str(self.db),
                *arguments,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_json_cli_denial_to_confirmed_contextual_exception(self):
        self.run_cli(
            "enable",
            "--namespace",
            self.namespace,
            "--consent-ref",
            "cli-denial:enable",
        )
        for index in range(3):
            self.run_cli(
                "observe",
                "--namespace",
                self.namespace,
                "--episode-id",
                f"support-{index}",
                "--pattern-type",
                "action",
                "--pattern-key",
                "workflow",
                "--value",
                json.dumps(["use the default workflow"]),
                "--scope",
                json.dumps({"repo": "nerd"}),
                "--triggers",
                json.dumps(["build"]),
                "--source",
                "direct_user",
                "--evidence-ref",
                f"cli-evidence:{index}",
            )
        candidate = self.run_cli(
            "consolidate",
            "--namespace",
            self.namespace,
            "--min-episodes",
            "3",
        )[0]
        parent = self.run_cli(
            "promote",
            "--pattern-id",
            candidate["pattern_id"],
            "--source",
            "direct_user",
            "--confirmation-ref",
            "cli-event:promote",
        )
        proposal = self.run_cli(
            "propose",
            "--namespace",
            self.namespace,
            "--episode-id",
            "denied-cli-task",
            "--input-text",
            "Build this feature",
            "--context",
            json.dumps({"repo": "nerd", "surface": "cli"}),
            "--baseline",
            json.dumps(empty_endpoint()),
        )
        denial = self.run_cli(
            "deny",
            "--proposal-id",
            proposal["proposal_id"],
            "--source",
            "direct_user",
            "--denial-ref",
            "cli-event:deny",
        )
        self.assertEqual(
            self.run_cli("get-denial", "--denial-id", denial["denial_id"])[
                "status"
            ],
            "needs_diagnosis",
        )
        split = self.run_cli(
            "propose-split",
            "--denial-id",
            denial["denial_id"],
            "--input-text",
            "Build this feature",
            "--context",
            json.dumps({"repo": "nerd", "surface": "cli"}),
            "--splits",
            json.dumps(
                [
                    {
                        "parent_pattern_id": parent["pattern_id"],
                        "exception_scope": {"repo": "nerd", "surface": "cli"},
                        "exception_value": ["use the CLI-specific workflow"],
                    }
                ]
            ),
        )
        applied = self.run_cli(
            "confirm-split",
            "--split-id",
            split["split_id"],
            "--phrase",
            split["confirmation_phrase"],
            "--source",
            "direct_user",
            "--confirmation-ref",
            "cli-event:confirm-split",
        )
        self.assertTrue(applied["memory_write_only"])
        self.assertEqual(
            self.run_cli("get-split", "--split-id", split["split_id"])[
                "status"
            ],
            "applied",
        )
        fresh = self.run_cli(
            "propose",
            "--namespace",
            self.namespace,
            "--episode-id",
            "fresh-cli-task",
            "--input-text",
            "Build this feature",
            "--context",
            json.dumps({"repo": "nerd", "surface": "cli"}),
            "--baseline",
            json.dumps(empty_endpoint()),
        )
        self.assertEqual(
            fresh["proposed_endpoint"]["action"],
            ["use the CLI-specific workflow"],
        )


if __name__ == "__main__":
    unittest.main()
