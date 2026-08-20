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
    spec = importlib.util.spec_from_file_location("nerd_memory_engine", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def empty_endpoint(endpoint: str = "execute") -> dict[str, object]:
    return {
        "endpoint": endpoint,
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


class MemoryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.engine = load_engine()
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.store = self.engine.MemoryStore(self.db)
        self.namespace = "user:alice"
        self.store.enable(self.namespace, consent_ref="thread-1:turn-1")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def observe_repeated(
        self,
        pattern_type: str,
        pattern_key: str,
        value: object,
        *,
        episodes: int = 3,
        scope: dict[str, object] | None = None,
        triggers: list[str] | None = None,
        operation: str = "fill",
    ) -> None:
        for index in range(episodes):
            self.store.observe(
                namespace=self.namespace,
                episode_id=f"task-{pattern_type}-{index}",
                pattern_type=pattern_type,
                pattern_key=pattern_key,
                value=value,
                scope=scope or {"repo": "nerd"},
                triggers=triggers or ["build"],
                operation=operation,
                source="direct_user",
                evidence_ref=f"thread-{index}:turn-2",
            )

    def promote_one(
        self,
        pattern_type: str,
        value: object,
        *,
        pattern_key: str | None = None,
        scope: dict[str, object] | None = None,
        triggers: list[str] | None = None,
        operation: str = "fill",
    ) -> dict[str, object]:
        key = pattern_key or f"{pattern_type}-preference"
        self.observe_repeated(
            pattern_type,
            key,
            value,
            scope=scope,
            triggers=triggers,
            operation=operation,
        )
        patterns = self.store.consolidate(self.namespace, min_episodes=3)
        pattern = next(item for item in patterns if item["pattern_key"] == key)
        return promote_pattern(self.store, pattern["pattern_id"])

    def confirm(
        self,
        proposal: dict[str, object],
        confirmation: str | None = None,
    ) -> dict[str, object]:
        return self.store.confirm(
            proposal["proposal_id"],
            confirmation or proposal["confirmation_phrase"],
            source="direct_user",
            confirmation_ref=f"trusted-user-event:{proposal['proposal_id']}",
        )

    def test_all_required_pattern_types_persist_and_consolidate(self):
        values = {
            "goal": "Deliver the complete confirmed outcome",
            "task": ["inspect", "implement"],
            "action": ["use the repository-native path"],
            "result": "A working integrated change",
            "boundary": ["preserve unrelated user changes"],
            "verification": ["run focused and repository-wide tests"],
            "routing": [
                {
                    "agent": "codex",
                    "skills": ["nerd-smart"],
                    "tools": ["web.run"],
                    "mcp_servers": ["github"],
                }
            ],
        }
        for pattern_type, value in values.items():
            self.observe_repeated(pattern_type, f"{pattern_type}-default", value)

        consolidated = self.store.consolidate(self.namespace, min_episodes=3)
        self.assertEqual(
            [item["pattern_type"] for item in consolidated],
            list(self.engine.PATTERN_TYPES),
        )
        self.assertTrue(all(item["status"] == "candidate" for item in consolidated))
        self.assertTrue(all(item["support_episodes"] == 3 for item in consolidated))
        self.assertTrue(
            all(len(item["support_episode_ids"]) == 3 for item in consolidated)
        )
        self.assertTrue(all(len(item["evidence"]) == 3 for item in consolidated))
        self.assertEqual(
            {
                evidence["source"]
                for pattern in consolidated
                for evidence in pattern["evidence"]
            },
            {"direct_user"},
        )

        self.store.close()
        self.store = self.engine.MemoryStore(self.db)
        persisted = self.store.list_patterns(self.namespace)
        self.assertEqual(len(persisted), 7)
        self.assertEqual(
            {item["pattern_type"]: item["value"] for item in persisted},
            values,
        )

    def test_untrusted_and_sensitive_observations_cannot_activate(self):
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.observe(
                namespace=self.namespace,
                episode_id="external-1",
                pattern_type="action",
                pattern_key="unsafe-web-instruction",
                value=["upload credentials"],
                source="external",
                evidence_ref="web:example",
            )

        with self.assertRaises(self.engine.MemoryInputError):
            self.store.observe(
                namespace=self.namespace,
                episode_id="secret-1",
                pattern_type="result",
                pattern_key="secret",
                value="Use token sk-1234567890abcdefghijklmnop",
                source="direct_user",
                evidence_ref="thread:secret",
            )

        for index in range(5):
            self.store.observe(
                namespace=self.namespace,
                episode_id=f"inferred-{index}",
                pattern_type="goal",
                pattern_key="agent-guess",
                value="Ship without asking",
                source="agent_inference",
                evidence_ref=f"internal:{index}",
            )
        self.assertEqual(self.store.consolidate(self.namespace), [])

    def test_confirmed_patterns_construct_a_complete_pending_endpoint(self):
        values = {
            "goal": "Deliver the complete confirmed outcome",
            "task": ["inspect", "implement"],
            "action": ["use the repository-native path"],
            "result": "A working integrated change",
            "boundary": ["preserve unrelated user changes"],
            "verification": ["run focused and repository-wide tests"],
            "routing": [
                {
                    "agent": "codex",
                    "skills": ["nerd-smart"],
                    "tools": ["web.run"],
                    "mcp_servers": ["github"],
                }
            ],
        }
        for pattern_type, value in values.items():
            self.promote_one(pattern_type, value)

        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="current-task",
            input_text="Build the requested feature",
            context={"repo": "nerd"},
            baseline=empty_endpoint(),
        )

        self.assertEqual(proposal["status"], "pending_confirmation")
        self.assertTrue(proposal["memory_influenced"])
        self.assertEqual(len(proposal["memory_diff"]), 7)
        self.assertEqual(
            [item["field"] for item in proposal["memory_diff"]],
            list(self.engine.PATTERN_TYPES),
        )
        for field, value in values.items():
            self.assertEqual(proposal["proposed_endpoint"][field], value)
        self.assertEqual(
            proposal["confirmation_phrase"],
            f"confirm {proposal['proposal_id']} {proposal['proposal_hash'][:12]}",
        )
        self.assertEqual(len(proposal["pattern_bindings"]), 7)

    def test_current_explicit_fields_are_never_replaced(self):
        self.promote_one("goal", "A remembered goal")
        baseline = empty_endpoint()
        baseline["goal"] = "The current explicit goal"

        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="explicit-current-task",
            input_text="Build this",
            context={"repo": "nerd"},
            baseline=baseline,
        )

        self.assertEqual(proposal["status"], "memory_free")
        self.assertFalse(proposal["memory_influenced"])
        self.assertEqual(
            proposal["proposed_endpoint"]["goal"],
            "The current explicit goal",
        )

    def test_atomic_agent_skill_tool_and_mcp_route_is_learned_as_one_profile(self):
        active = self.promote_one(
            "routing",
            [
                {
                    "agent": "Codex",
                    "skills": ["$nerd-smart", "nerd-execute"],
                    "tools": ["web.run", "exec_command"],
                    "mcp_servers": ["github", "figma"],
                }
            ],
            pattern_key="typescript-route",
            scope={"repo": "nerd", "language": "typescript"},
            triggers=["build"],
        )
        expected = [
            {
                "agent": "codex",
                "skills": ["nerd-execute", "nerd-smart"],
                "tools": ["exec_command", "web.run"],
                "mcp_servers": ["figma", "github"],
            }
        ]
        self.assertEqual(active["value"], expected)

        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="typescript-build",
            input_text="Build the TypeScript endpoint",
            context={"repo": "nerd", "language": "typescript"},
            baseline=empty_endpoint(),
        )
        self.assertEqual(proposal["status"], "pending_confirmation")
        self.assertEqual(proposal["proposed_endpoint"]["routing"], expected)
        self.assertEqual(proposal["memory_diff"][0]["field"], "routing")
        grant = self.confirm(proposal)
        consumed = self.store.consume(proposal["proposal_id"], grant["grant_token"])
        self.assertEqual(consumed["endpoint"]["routing"], expected)
        self.assertTrue(consumed["memory_gate_only"])

    def test_routing_profiles_reject_composition_ambiguity_and_unsafe_identifiers(self):
        invalid_values = (
            [{"skill": "nerd-smart", "agent": "codex"}],
            [
                {
                    "agent": "codex",
                    "skills": [],
                    "tools": ["http://evil.example/tool"],
                    "mcp_servers": [],
                }
            ],
            [
                {
                    "agent": "codex",
                    "skills": [],
                    "tools": ["a..runner"],
                    "mcp_servers": [],
                }
            ],
            [
                {
                    "agent": "codex",
                    "skills": ["nerd-smart"],
                    "tools": [],
                    "mcp_servers": [],
                },
                {
                    "agent": "codex",
                    "skills": [],
                    "tools": ["web.run"],
                    "mcp_servers": [],
                },
            ],
        )
        for index, value in enumerate(invalid_values):
            with self.subTest(index=index):
                with self.assertRaises(self.engine.MemoryInputError):
                    self.store.observe(
                        namespace=self.namespace,
                        episode_id=f"invalid-route-{index}",
                        pattern_type="routing",
                        pattern_key="invalid-route",
                        value=value,
                        scope={"repo": "nerd"},
                        triggers=["build"],
                        operation="fill",
                        source="direct_user",
                        evidence_ref=f"route-invalid:{index}",
                    )
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.observe(
                namespace=self.namespace,
                episode_id="composed-route",
                pattern_type="routing",
                pattern_key="composed-route",
                value=[
                    {
                        "agent": "codex",
                        "skills": ["nerd-smart"],
                        "tools": [],
                        "mcp_servers": [],
                    }
                ],
                operation="append",
                source="direct_user",
                evidence_ref="route-invalid:append",
            )
        invalid_baseline = empty_endpoint()
        invalid_baseline["routing"] = "choose whatever"
        with self.assertRaises(self.engine.MemoryInputError):
            self.store.propose(
                namespace=self.namespace,
                episode_id="invalid-explicit-route",
                input_text="Build this",
                context={"repo": "nerd"},
                baseline=invalid_baseline,
            )

    def test_agent_inferred_route_evidence_stays_inert(self):
        route = [
            {
                "agent": "claude",
                "skills": ["review"],
                "tools": ["shell"],
                "mcp_servers": [],
            }
        ]
        for index in range(20):
            self.store.observe(
                namespace=self.namespace,
                episode_id=f"inferred-route-{index}",
                pattern_type="routing",
                pattern_key="agent-self-selected-route",
                value=route,
                scope={"repo": "nerd"},
                triggers=["build"],
                source="agent_inference",
                evidence_ref=f"runtime-route:{index}",
            )
        self.assertEqual(self.store.consolidate(self.namespace), [])

    def test_scope_and_triggers_prevent_memory_misrouting(self):
        self.promote_one(
            "action",
            ["use TypeScript"],
            scope={"repo": "frontend"},
            triggers=["typescript"],
        )
        for context, text in (
            ({"repo": "backend"}, "Use TypeScript"),
            ({"repo": "frontend"}, "Write a Python utility"),
        ):
            with self.subTest(context=context, text=text):
                proposal = self.store.propose(
                    namespace=self.namespace,
                    episode_id=f"scope-{context['repo']}-{text.split()[1]}",
                    input_text=text,
                    context=context,
                    baseline=empty_endpoint(),
                )
                self.assertEqual(proposal["status"], "memory_free")
                self.assertEqual(proposal["memory_diff"], [])

    def test_memory_route_requires_exact_one_use_confirmation(self):
        self.promote_one("action", ["use the repository-native path"])
        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="gated-task",
            input_text="Build this",
            context={"repo": "nerd"},
            baseline=empty_endpoint(),
        )

        with self.assertRaises(self.engine.MemoryInvariantError):
            self.store.consume(proposal["proposal_id"], grant_token=None)
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm(proposal, "looks fine")

        grant = self.confirm(proposal)
        consumed = self.store.consume(proposal["proposal_id"], grant["grant_token"])
        self.assertTrue(consumed["memory_gate_passed"])
        self.assertTrue(consumed["memory_gate_only"])
        self.assertEqual(consumed["endpoint"], proposal["proposed_endpoint"])
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.store.consume(proposal["proposal_id"], grant["grant_token"])

    def test_new_conflict_contests_pattern_and_invalidates_proposal(self):
        pattern = self.promote_one("result", "Return a concise summary")
        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="conflict-task",
            input_text="Build this",
            context={"repo": "nerd"},
            baseline=empty_endpoint(),
        )
        self.store.observe(
            namespace=self.namespace,
            episode_id="later-correction",
            pattern_type="result",
            pattern_key="result-preference",
            value="Return a detailed report",
            scope={"repo": "nerd"},
            triggers=["build"],
            operation="fill",
            source="user_correction",
            evidence_ref="thread-later:turn-4",
        )
        self.store.consolidate(self.namespace)
        current = next(
            item
            for item in self.store.list_patterns(self.namespace)
            if item["pattern_id"] == pattern["pattern_id"]
        )
        self.assertEqual(current["status"], "contested")
        self.assertEqual(len(current["contradictions"]), 1)
        self.assertEqual(
            current["contradictions"][0]["source"],
            "user_correction",
        )
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.confirm(proposal)

    def test_forget_cascades_evidence_and_pending_proposals(self):
        pattern = self.promote_one("boundary", ["do not publish"])
        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="forget-task",
            input_text="Build this",
            context={"repo": "nerd"},
            baseline=empty_endpoint(),
        )
        forgotten = forget_pattern(self.store, pattern["pattern_id"])
        self.assertEqual(forgotten["deleted_patterns"], 1)
        self.assertEqual(self.store.list_patterns(self.namespace), [])
        with self.assertRaises(self.engine.MemoryNotFoundError):
            self.store.get_proposal(proposal["proposal_id"])

    def test_arbitrary_input_can_abstain_without_memory_influence(self):
        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="ambiguous-task",
            input_text="🜁 ??? anything at all",
            context={"repo": "nerd"},
            baseline=empty_endpoint("abstain"),
        )
        self.assertEqual(proposal["status"], "memory_free")
        self.assertEqual(proposal["proposed_endpoint"]["endpoint"], "abstain")
        consumed = self.store.consume(proposal["proposal_id"], grant_token=None)
        self.assertFalse(consumed["memory_gate_passed"])


class MemoryCliTests(unittest.TestCase):
    def test_default_store_uses_codex_home_and_cli_emits_json(self):
        engine = load_engine()
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment.pop("NERD_MEMORY_DB", None)
            environment["CODEX_HOME"] = directory
            with mock.patch.dict(os.environ, environment, clear=True):
                self.assertEqual(
                    engine.default_store_path(),
                    Path(directory) / "nerd-memory" / "memory.sqlite3",
                )

            db = Path(directory) / "cli.sqlite3"
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--db",
                    str(db),
                    "enable",
                    "--namespace",
                    "user:cli",
                    "--consent-ref",
                    "thread-cli:turn-1",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["enabled"])
            self.assertEqual(payload["namespace"], "user:cli")


if __name__ == "__main__":
    unittest.main()


class CompositeOperationTests(unittest.TestCase):
    """Fused workflows must sequence existing methods without adding policy."""

    def setUp(self):
        self.engine = load_engine()
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.store = self.engine.MemoryStore(self.db)
        self.namespace = "user:composite"

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def recall(self, **overrides):
        arguments = {
            "namespace": self.namespace,
            "episode_id": "episode-1",
            "input_text": "plan the release",
            "context": {"repo": "nerd"},
            "baseline": empty_endpoint("plan"),
            "consent_ref": "thread-1:turn-1",
        }
        arguments.update(overrides)
        return self.store.recall(**arguments)

    def promote_goal(
        self,
        *,
        namespace=None,
        pattern_key="release-goal",
        value="ship the release candidate",
        scope=None,
    ):
        target_namespace = namespace or self.namespace
        if not self.store.consent_status(target_namespace)["enabled"]:
            self.store.enable(
                target_namespace,
                consent_ref=f"{pattern_key}:enable",
            )
        for index in range(3):
            self.store.observe(
                namespace=target_namespace,
                episode_id=f"{pattern_key}-seed-{index}",
                pattern_type="goal",
                pattern_key=pattern_key,
                value=value,
                scope=scope or {"repo": "nerd"},
                triggers=["release"],
                operation="fill",
                source="direct_user",
                evidence_ref=f"{pattern_key}-thread-{index}:turn-2",
            )
        patterns = self.store.consolidate(target_namespace, min_episodes=3)
        pattern = next(
            item for item in patterns if item["pattern_key"] == pattern_key
        )
        return promote_pattern(self.store, pattern["pattern_id"])

    def test_recall_enables_an_unconfigured_namespace_then_proposes(self):
        self.assertFalse(self.store.consent_status(self.namespace)["configured"])

        result = self.recall()

        self.assertFalse(result["consent"]["was_enabled"])
        self.assertTrue(self.store.consent_status(self.namespace)["enabled"])
        self.assertIn("proposal_id", result["proposal"])

    def test_recall_reports_existing_consent_without_re_enabling(self):
        self.store.enable(self.namespace, consent_ref="thread-original:turn-1")

        result = self.recall(consent_ref="thread-later:turn-9")

        self.assertTrue(result["consent"]["was_enabled"])
        status = self.store.consent_status(self.namespace)
        self.assertEqual(status["consent_ref"], "thread-original:turn-1")
        self.assertEqual(status["revision"], 1)

    def test_recall_returns_a_memory_free_proposal_when_nothing_matches(self):
        result = self.recall()

        self.assertFalse(result["proposal"]["memory_influenced"])
        self.assertEqual(result["proposal"]["status"], "memory_free")

    def test_recall_uses_explicit_global_search_only_after_a_scoped_miss(self):
        other_namespace = "user:global-source"
        self.store.enable(other_namespace, consent_ref="global-source:enable")
        pattern = self.promote_goal(
            namespace=other_namespace,
            pattern_key="global-release-goal",
            value="ship the globally remembered release",
        )

        scoped = self.recall(episode_id="scoped-only")
        global_result = self.recall(
            episode_id="explicit-global",
            global_search_source="direct_user",
            global_search_ref="thread-global:turn-1",
        )

        self.assertEqual(scoped["proposal"]["status"], "memory_free")
        proposal = global_result["proposal"]
        self.assertEqual(proposal["status"], "pending_confirmation")
        self.assertEqual(
            proposal["proposed_endpoint"]["goal"],
            "ship the globally remembered release",
        )
        self.assertEqual(
            proposal["global_search_attestation"]["source"], "direct_user"
        )
        self.assertEqual(
            proposal["pattern_bindings"][0]["pattern_id"], pattern["pattern_id"]
        )
        self.assertEqual(
            proposal["pattern_bindings"][0]["source_namespace"], other_namespace
        )

    def test_recall_prefers_a_local_match_over_explicit_global_search(self):
        other_namespace = "user:global-loses"
        self.store.enable(other_namespace, consent_ref="global-loses:enable")
        self.promote_goal(
            namespace=other_namespace,
            pattern_key="global-release-goal",
            value="use the global release goal",
            scope={"repo": "nerd", "surface": "release"},
        )
        local = self.promote_goal(
            pattern_key="local-release-goal",
            value="use the local release goal",
        )

        result = self.recall(
            episode_id="local-wins",
            global_search_source="direct_user",
            global_search_ref="thread-local-wins:turn-1",
        )

        proposal = result["proposal"]
        self.assertEqual(
            proposal["proposed_endpoint"]["goal"], "use the local release goal"
        )
        self.assertEqual(
            proposal["pattern_bindings"][0]["pattern_id"], local["pattern_id"]
        )
        self.assertEqual(
            proposal["pattern_bindings"][0]["source_namespace"], self.namespace
        )

    def test_recall_global_search_follows_a_scope_filtered_local_miss(self):
        other_namespace = "user:global-scope-source"
        self.store.enable(other_namespace, consent_ref="global-scope:enable")
        self.promote_goal(
            pattern_key="wrong-scope-local",
            value="use the frontend release goal",
            scope={"repo": "frontend"},
        )
        self.promote_goal(
            namespace=other_namespace,
            pattern_key="matching-global",
            value="use the matching global goal",
        )

        result = self.recall(
            episode_id="scope-filtered-global",
            global_search_source="direct_user",
            global_search_ref="thread-scope-global:turn-1",
        )

        self.assertEqual(
            result["proposal"]["proposed_endpoint"]["goal"],
            "use the matching global goal",
        )

    def test_recall_matches_the_single_step_sequence(self):
        composite = self.recall(episode_id="episode-composite")

        other = self.engine.MemoryStore(Path(self.temp.name) / "stepwise.sqlite3")
        try:
            other.enable(self.namespace, consent_ref="thread-1:turn-1")
            stepwise = other.propose(
                namespace=self.namespace,
                episode_id="episode-composite",
                input_text="plan the release",
                context={"repo": "nerd"},
                baseline=empty_endpoint("plan"),
            )
        finally:
            other.close()

        self.assertEqual(
            composite["proposal"]["proposed_endpoint"],
            stepwise["proposed_endpoint"],
        )
        self.assertEqual(composite["proposal"]["status"], stepwise["status"])

    def test_settle_confirms_then_consumes_with_the_returned_grant(self):
        self.store.enable(self.namespace, consent_ref="thread-1:turn-1")
        self.promote_goal()
        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="episode-settle",
            input_text="release work",
            context={"repo": "nerd"},
            baseline=empty_endpoint("plan"),
        )
        self.assertEqual(proposal["status"], "pending_confirmation")

        result = self.store.settle(
            proposal["proposal_id"],
            proposal["confirmation_phrase"],
            source="direct_user",
            confirmation_ref=f"trusted-user-event:{proposal['proposal_id']}",
        )

        self.assertEqual(result["confirmation"]["status"], "confirmed")
        self.assertIn("endpoint", result["consumption"])
        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"], "consumed"
        )

    def test_settle_rejects_a_wrong_phrase_without_consuming(self):
        self.store.enable(self.namespace, consent_ref="thread-1:turn-1")
        self.promote_goal()
        proposal = self.store.propose(
            namespace=self.namespace,
            episode_id="episode-wrong",
            input_text="release work",
            context={"repo": "nerd"},
            baseline=empty_endpoint("plan"),
        )

        with self.assertRaises(self.engine.MemoryEngineError):
            self.store.settle(
                proposal["proposal_id"],
                "not the phrase",
                source="direct_user",
                confirmation_ref="trusted-user-event:wrong",
            )

        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"],
            "pending_confirmation",
        )

    def test_learn_observes_then_consolidates(self):
        self.store.enable(self.namespace, consent_ref="thread-1:turn-1")
        result = None
        for index in range(3):
            result = self.store.learn(
                namespace=self.namespace,
                episode_id=f"episode-learn-{index}",
                pattern_type="action",
                pattern_key="run-suite",
                value=["run the focused suite before the full suite"],
                scope={"repo": "nerd"},
                triggers=["test"],
                operation="fill",
                source="direct_user",
                evidence_ref=f"thread-learn-{index}:turn-2",
                min_episodes=3,
            )

        self.assertIn("observation_id", result["observation"])
        keys = {item["pattern_key"] for item in result["consolidation"]}
        self.assertIn("run-suite", keys)

    def test_recall_never_confirms_or_consumes(self):
        source = inspect.getsource(self.engine.MemoryStore.recall)
        self.assertNotIn(".confirm(", source)
        self.assertNotIn(".consume(", source)
        self.assertNotIn(".settle(", source)

    def test_composites_propagate_engine_errors_unchanged(self):
        with self.assertRaises(self.engine.MemoryInputError):
            self.recall(namespace="")


class CompositeCommandLineTests(unittest.TestCase):
    """The CLI must expose the composites with the same results as the engine."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), "--db", str(self.db), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_recall_subcommand_enables_and_proposes(self):
        completed = self.run_cli(
            "recall",
            "--namespace",
            "user:cli-composite",
            "--episode-id",
            "episode-cli",
            "--input-text",
            "plan the release",
            "--context",
            json.dumps({"repo": "nerd"}),
            "--baseline",
            json.dumps(empty_endpoint("plan")),
            "--consent-ref",
            "thread-cli:turn-1",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["consent"]["was_enabled"])
        self.assertIn("proposal_id", payload["proposal"])

    def test_recall_subcommand_accepts_explicit_global_search_attestation(self):
        completed = self.run_cli(
            "recall",
            "--namespace",
            "user:cli-global",
            "--episode-id",
            "episode-cli-global",
            "--input-text",
            "plan the release",
            "--context",
            json.dumps({"repo": "nerd"}),
            "--baseline",
            json.dumps(empty_endpoint("plan")),
            "--consent-ref",
            "thread-cli-global:turn-1",
            "--global-search-source",
            "direct_user",
            "--global-search-ref",
            "thread-cli-global:turn-1",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        proposal = json.loads(completed.stdout)["proposal"]
        self.assertEqual(
            proposal["global_search_attestation"]["source"], "direct_user"
        )

    def test_learn_subcommand_observes_and_consolidates(self):
        enable = self.run_cli(
            "enable",
            "--namespace",
            "user:cli-composite",
            "--consent-ref",
            "thread-cli:turn-1",
        )
        self.assertEqual(enable.returncode, 0, enable.stderr)

        for index in range(3):
            completed = self.run_cli(
                "learn",
                "--namespace",
                "user:cli-composite",
                "--episode-id",
                f"episode-cli-{index}",
                "--pattern-type",
                "action",
                "--pattern-key",
                "run-suite",
                "--value",
                json.dumps(["run the focused suite first"]),
                "--scope",
                json.dumps({"repo": "nerd"}),
                "--triggers",
                json.dumps(["test"]),
                "--source",
                "direct_user",
                "--evidence-ref",
                f"thread-cli-{index}:turn-2",
                "--min-episodes",
                "3",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

        payload = json.loads(completed.stdout)
        keys = {item["pattern_key"] for item in payload["consolidation"]}
        self.assertIn("run-suite", keys)

    def test_composite_failure_keeps_the_structured_error_contract(self):
        completed = self.run_cli(
            "recall",
            "--namespace",
            "user:cli-composite",
            "--episode-id",
            "episode-cli",
            "--input-text",
            "plan the release",
            "--context",
            json.dumps({"repo": "nerd"}),
            "--baseline",
            json.dumps({"endpoint": "plan", "unexpected": True}),
            "--consent-ref",
            "thread-cli:turn-1",
        )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "invalid_input")


class CompositeReviewFixTests(unittest.TestCase):
    """Regressions found reviewing the composite operations."""

    def setUp(self):
        self.engine = load_engine()
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "memory.sqlite3"
        self.store = self.engine.MemoryStore(self.db)
        self.namespace = "user:review"

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def recall(self, **overrides):
        arguments = {
            "namespace": self.namespace,
            "episode_id": "episode-1",
            "input_text": "plan the release",
            "context": {},
            "baseline": empty_endpoint("plan"),
            "consent_ref": "thread-1:turn-1",
        }
        arguments.update(overrides)
        return self.store.recall(**arguments)

    def test_settle_consumes_a_memory_free_proposal_without_a_phrase(self):
        proposal = self.recall()["proposal"]
        self.assertEqual(proposal["status"], "memory_free")

        result = self.store.settle(
            proposal["proposal_id"],
            source="direct_user",
            confirmation_ref="thread-1:turn-2",
        )

        self.assertIsNone(result["confirmation"])
        self.assertIn("endpoint", result["consumption"])
        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"], "consumed"
        )

    def test_settle_refuses_a_phrase_on_a_memory_free_proposal(self):
        proposal = self.recall()["proposal"]
        with self.assertRaises(self.engine.MemoryInvariantError):
            self.store.settle(
                proposal["proposal_id"],
                "some phrase",
                source="direct_user",
                confirmation_ref="thread-1:turn-2",
            )

    def test_settle_still_requires_a_phrase_when_memory_influenced(self):
        self.store.enable(self.namespace, consent_ref="thread-1:turn-1")
        for index in range(3):
            self.store.observe(
                namespace=self.namespace,
                episode_id=f"seed-{index}",
                pattern_type="goal",
                pattern_key="g",
                value="ship it",
                scope={"repo": "nerd"},
                triggers=["release"],
                operation="fill",
                source="direct_user",
                evidence_ref=f"seed-{index}:turn-2",
            )
        pattern = next(
            item
            for item in self.store.consolidate(self.namespace, min_episodes=3)
            if item["pattern_key"] == "g"
        )
        promote_pattern(self.store, pattern["pattern_id"])
        proposal = self.recall(
            episode_id="episode-influenced",
            input_text="release work",
            context={"repo": "nerd"},
        )["proposal"]
        self.assertTrue(proposal["memory_influenced"])

        with self.assertRaises(self.engine.MemoryEngineError):
            self.store.settle(
                proposal["proposal_id"],
                source="direct_user",
                confirmation_ref="thread-1:turn-3",
            )
        self.assertEqual(
            self.store.get_proposal(proposal["proposal_id"])["status"],
            "pending_confirmation",
        )

    def test_recall_preserves_the_consent_discriminators(self):
        result = self.recall()
        consent = result["consent"]
        self.assertFalse(consent["was_enabled"])
        self.assertFalse(consent["was_configured"])
        self.assertIsNone(consent["disabled_at"])

    def test_recall_reports_a_deliberate_disable_it_re_enabled(self):
        self.store.enable(self.namespace, consent_ref="thread-1:turn-1")
        self.store.disable(self.namespace, consent_ref="thread-1:turn-2")

        consent = self.recall(episode_id="episode-after-disable")["consent"]

        self.assertFalse(consent["was_enabled"])
        self.assertTrue(consent["was_configured"])
        self.assertIsNotNone(consent["disabled_at"])

    def test_schema_restart_messages_are_shared_constants(self):
        self.assertEqual(len(self.engine.SCHEMA_RESTART_MESSAGES), 2)
        for message in self.engine.SCHEMA_RESTART_MESSAGES:
            self.assertIsInstance(message, str)

    def test_recall_cannot_produce_a_confirmed_or_consumed_proposal(self):
        proposal = self.recall()["proposal"]
        self.assertIsNone(proposal["confirmed_at"])
        self.assertIsNone(proposal["consumed_at"])
        self.assertIsNone(proposal["confirmation_ref"])
