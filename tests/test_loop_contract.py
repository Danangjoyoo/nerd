from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "skills" / "nerd-loop"


def body(relative: str) -> str:
    return (LOOP / relative).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def topic_body(topic: str) -> str:
    root = LOOP / "references" / topic
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.glob("*.md"))
    )


class LoopContractTests(unittest.TestCase):
    def test_large_optional_topics_use_compact_routing_indexes(self):
        topics = ("iteration", "profiles", "convergence", "dod", "memory")
        for topic in topics:
            with self.subTest(topic=topic):
                topic_root = LOOP / "references" / topic
                index = topic_root / "index.md"
                self.assertTrue(index.is_file())
                index_words = len(index.read_text(encoding="utf-8").split())
                self.assertLessEqual(index_words, 500)
                child_words = []
                for chunk in topic_root.glob("*.md"):
                    words = len(chunk.read_text(encoding="utf-8").split())
                    self.assertLessEqual(
                        words,
                        1_600,
                        chunk,
                    )
                    if chunk != index:
                        child_words.append(words)
                self.assertLessEqual(index_words + max(child_words), 2_000)

        for obsolete in (
            "iteration.md",
            "loop-profiles.md",
            "convergence.md",
            "definition-of-done.md",
            "behavioral-memory.md",
        ):
            self.assertFalse((LOOP / "references" / obsolete).exists())

    def test_common_loop_instructions_stay_within_context_budget(self):
        skill_words = len(body("SKILL.md").split())
        runtime_words = len(body("references/runtime-contract.md").split())
        durable_words = len(body("references/durable-runtime.md").split())

        self.assertLessEqual(skill_words, 1_100)
        self.assertLessEqual(runtime_words, 1_700)
        self.assertLessEqual(durable_words, 2_100)
        self.assertLessEqual(skill_words + runtime_words, 2_700)
        self.assertLessEqual(skill_words + runtime_words + durable_words, 4_800)

    def test_reference_load_boundaries_are_state_driven(self):
        skill = normalized(body("SKILL.md"))
        runtime = body("references/runtime-contract.md")
        durable = normalized(body("references/durable-runtime.md"))
        memory = topic_body("memory")

        self.assertIn("Admitted state is `S2` or `S3`", skill)
        self.assertIn("durable checkpoint on a lower profile", skill)
        self.assertNotIn("`INTENT_COMMITTED`", runtime)
        self.assertNotIn("ROUTING_PROFILE_", runtime)
        self.assertIn("`INTENT_COMMITTED`", durable)
        self.assertNotIn("ROUTING_PROFILE_", durable)
        self.assertIn("ROUTING_PROFILE_ACTIVATED", memory)
        self.assertIn(
            "Nerd Memory composes only when the current user explicitly invokes it",
            skill,
        )

    def test_skill_covers_the_original_task_completion_goal(self):
        skill = normalized(body("SKILL.md"))
        for term in (
            "any authorized task—not only code generation",
            "least expensive useful sequence",
            "automatic verification",
            "Definition of Done",
            "exactly one primary focus",
            "Convergence describes target-relative dynamics",
            "Never relabel a non-success stop as done",
            "Self-Refinement Loop",
        ):
            self.assertIn(term, skill)

        for reference in (
            "runtime-contract.md",
            "durable-runtime.md",
            "profiles/index.md",
            "dod/index.md",
            "iteration/index.md",
            "convergence/index.md",
            "memory/index.md",
        ):
            self.assertIn(f"references/{reference}", skill)

    def test_runtime_contract_has_closed_disjoint_vocabularies(self):
        contract = normalized(body("references/runtime-contract.md"))
        for vocabulary in (
            "PASS | FAIL | UNKNOWN | ERROR",
            "NOT_ASSESSED | PROGRESSING | LEARNING | SETTLING | PLATEAUED | PREMATURELY_CONVERGED | STUCK | OSCILLATING | DIVERGING | INCONCLUSIVE | FALSE_CONVERGENCE",
            "PROPOSED | PLANNED | READY | CLAIMED | ACTIVE | VERIFYING | VERIFIED | WAITING | BLOCKED | SUPERSEDED | CANCELLED",
            "ADMITTING | READY | ACTIVE | VERIFYING | PAUSED | RECONCILING | TERMINAL",
            "DONE | BLOCKED | CANCELLED | UNSAFE | IMPOSSIBLE | FAILED | EXHAUSTED | STOPPED | HANDOFF",
        ):
            self.assertIn(vocabulary, contract)

        self.assertIn("Never use one vocabulary as another", contract)
        self.assertIn("Dynamics describe the trace, never the terminal result", contract)
        self.assertIn("`PAUSED` is a loop phase; `WAITING` is a work-node status", contract)

    def test_transition_priority_and_done_are_deterministic(self):
        contract = body("references/runtime-contract.md")
        transition = contract.split("## Transition Priority", 1)[1].split(
            "## Extensions and Conformance", 1
        )[0].casefold()
        ordered = (
            "stop unauthorized or unsafe work",
            "honor authoritative cancellation",
            "reconcile an ambiguous effect",
            "apply current user or higher-authority revisions",
            "validate verifier integrity",
            "if the completion expression passes, return `done`",
            "apply a reached hard terminal",
            "enter `PAUSED`",
            "diagnose dynamics",
            "select the lexicographically first eligible ready focus",
        )
        offsets = [transition.index(term.casefold()) for term in ordered]
        self.assertEqual(offsets, sorted(offsets))

        self.assertIn("`DONE` is reachable only through the DoD decision", contract)
        self.assertIn(
            "only authenticated DoD evidence reaches `DONE`",
            normalized(contract),
        )

    def test_durable_effects_use_two_phase_commit_order(self):
        durable = body("references/durable-runtime.md")
        protocol = durable.split("## Two-Phase Effect Protocol", 1)[1].split(
            "## Unknown Effects and Recovery", 1
        )[0]
        ordered = (
            "**Intent commit:**",
            "`INTENT_COMMITTED`",
            "**Execute:**",
            "**Outcome observation:**",
            "`ACTION_OBSERVED`",
            "`VERIFICATION_RECORDED`",
            "`ITERATION_COMMITTED`",
            "Exactly one cause-labelled successor",
        )
        protocol_folded = protocol.casefold()
        offsets = [protocol_folded.index(term.casefold()) for term in ordered]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn("Never require a receipt before its action", protocol)
        iteration = topic_body("iteration")
        self.assertNotIn("ACTION_PLANNED", iteration)
        self.assertNotIn("ITERATION_SELECTED and ACTION_INTENT", iteration)

    def test_memory_integration_uses_seven_fields_and_atomic_routing(self):
        memory = normalized(topic_body("memory"))
        contract = normalized(body("references/runtime-contract.md"))
        for text in (memory, contract):
            self.assertNotIn("six-field", text.casefold())
            self.assertNotIn("six pattern", text.casefold())

        for term in (
            "`goal`, `task`, `action`, `result`, `boundary`, `verification`, and `routing`",
            "authenticated registry",
            "fail closed",
            "Advance exactly one index",
            "Route completion never proves the task DoD",
        ):
            self.assertTrue(term in memory or term in contract, term)

        self.assertIn("## Mapping the Seven Pattern Types", body("references/memory/contract.md"))
        self.assertIn("| `routing` |", body("references/memory/contract.md"))
        self.assertIn("all seven pattern types compile", memory)

    def test_runtime_claims_are_bound_to_evidence_authority_and_revisions(self):
        contract = normalized(body("references/runtime-contract.md"))
        durable = normalized(body("references/durable-runtime.md"))
        memory = normalized(topic_body("memory"))

        for term in (
            "trusted-adapter inputs",
            "cannot self-attest",
            "Freeze the sorted mandatory and integration ID sets",
            "host-authenticated record bound to the criterion",
            "exact admitted envelope",
        ):
            self.assertIn(term, contract)

        for term in (
            "Every event carries the next expected revision",
            "same ID with different content",
            "freeze the exact accepted DoD definition",
            "complete authenticated criterion and integration evidence",
        ):
            self.assertIn(term, durable)

        for term in (
            "Resolve every agent, skill, tool, and MCP identifier in every profile",
            "explicit agent-bound authority map",
            "authenticated completion receipt",
            "hashed identity of its exact `ITERATION_COMMITTED` event",
            "reachable revision",
        ):
            self.assertIn(term, memory)

    def test_dod_verdicts_and_approval_decisions_are_authenticated(self):
        contract = normalized(body("references/runtime-contract.md"))
        dod = normalized(topic_body("dod"))
        for term in (
            "exact DoD hash and revision",
            "Criterion status is a checked projection of that authenticated verdict",
            "without evidence it is `UNKNOWN`",
            "`APPROVED | REJECTED` decision",
            "Presence alone is not approval",
            "each displayed status equals its verdict",
            "explicitly `APPROVED`",
        ):
            self.assertTrue(term in contract or term in dod, term)

    def test_all_reducers_share_admission_and_cumulative_budget(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "Its `admission_hash` covers every envelope field except the hash itself",
            "Pass that exact admitted envelope and current cumulative budget state to `decide`, `effect`, and `routing`",
            "one authenticated cumulative `budget_state`",
            "never accept a free-standing `budget_remaining`",
            "Every committed iteration consumes exactly one unit",
            "Reject stale, skipped, reset, or cross-admission budget state",
        ):
            self.assertIn(term, contract)

    def test_transition_validation_is_staged_by_priority(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "Parse only through the first matching priority stage",
            "Malformed same-stage or higher-priority inputs fail closed",
            "malformed lower-priority admission, DoD, budget, wake, value, or dynamics data cannot suppress an earlier safety, cancellation, reconciliation, or revision result",
        ):
            self.assertIn(term, contract)

    def test_profile_floor_and_routing_compatibility_are_explicit(self):
        contract = normalized(body("references/runtime-contract.md"))
        profiles = normalized(topic_body("profiles"))
        memory = normalized(topic_body("memory"))
        for term in (
            "`high_impact` and `high_consequence`",
            "`primary | modifier | middleware | controller`",
            "at most one primary specialty",
            "A selected incompatible pair fails admission",
            "ordinary S2 checkpoint does not pay for effect reconciliation",
        ):
            self.assertTrue(
                term in contract or term in profiles or term in memory,
                term,
            )

    def test_terminal_receipts_and_handoff_are_identity_bound(self):
        durable = normalized(body("references/durable-runtime.md"))
        for term in (
            "A passing loop-scoped DoD must choose `LOOP_DONE`",
            "every non-success terminal requires its typed receipt",
            "canonical reference, integer revision, and content hash",
            "authenticated record says `ACCEPTED`",
            "binds that exact reference, revision, and hash",
        ):
            self.assertIn(term, durable)

    def test_memory_requires_explicit_current_request_activation(self):
        skill = normalized(body("SKILL.md"))
        memory = normalized(topic_body("memory"))
        self.assertIn(
            "Nerd Memory composes only when the current user explicitly invokes it for the current request",
            skill,
        )
        self.assertIn(
            "Installation, relevance, prior use, remembered preferences, or another skill's mention never activates it",
            memory,
        )
        self.assertIn("does not load or query Nerd Memory", memory)

    def test_identity_strings_are_canonical(self):
        durable = normalized(body("references/durable-runtime.md"))
        self.assertIn("Identity-bearing strings are canonical and nonempty", durable)
        self.assertIn("Reject whitespace-only", durable)
        self.assertIn("leading/trailing whitespace", durable)

    def test_event_wait_and_route_semantics_are_not_caller_optional(self):
        corpus = normalized(
            "\n".join(
                (
                    body("references/runtime-contract.md"),
                    body("references/durable-runtime.md"),
                    topic_body("profiles"),
                )
            )
        ).replace("`", "")
        for term in (
            "authenticated registered condition and deadline",
            "waiting consumes no active iteration budget",
            "direct is valid only when the resulting profile remains D0",
            "authenticated wake-event registration for a durable monitor or pr_delivery route",
            "Stop unauthorized or unsafe work",
            "Honor authoritative cancellation",
        ):
            self.assertIn(term, corpus)

    def test_every_mapped_route_has_one_template_and_consistent_floor(self):
        mapping = body("references/profiles/endpoint-map.md")
        template_region = body("references/profiles/routes.md")
        mapped_routes = set(re.findall(r"`([a-z_]+)/(?:D0|L1|L2|L3|L4)`", mapping))
        defined = re.findall(
            r"^### .* — `([a-z_]+)`, base (D0|L1|L2|L3|L4)",
            template_region,
            re.MULTILINE,
        )
        defined_names = [name for name, _ in defined]
        self.assertEqual(len(defined_names), len(set(defined_names)))
        self.assertTrue(mapped_routes.issubset(set(defined_names)))
        self.assertIn(("experiment", "L2"), defined)
        self.assertIn(
            "Raise to L3 when it needs managed recovery beyond a simple",
            template_region,
        )

    def test_cost_guards_prevent_reference_overinstantiation(self):
        convergence = normalized(topic_body("convergence"))
        iteration = normalized(topic_body("iteration"))
        profiles = normalized(topic_body("profiles"))
        for term in (
            "D0/L1 do not instantiate its full history model",
            "L2 uses a compact subset",
            "ordinary S1 compresses these concepts",
            "Multiple in-session iterations alone do not require durability",
            "immediate clarification or acceptance in the current interaction does not alone force L3",
            "L4 does not automatically force S3",
        ):
            self.assertTrue(term in convergence or term in iteration or term in profiles, term)

    def test_bug_finding_done_is_evidence_not_plan_activity(self):
        profiles = normalized(topic_body("profiles"))
        self.assertIn("Finishing a probe plan is activity, not proof", profiles)
        self.assertIn("declared evidence-coverage criteria pass", profiles)
        self.assertIn("required residual-risk statement is complete", profiles)

    def test_all_normative_references_share_authority_source(self):
        references = [LOOP / "references" / "durable-runtime.md"]
        for topic in ("profiles", "dod", "iteration", "convergence", "memory"):
            references.extend(sorted((LOOP / "references" / topic).glob("*.md")))
        for reference in references:
            with self.subTest(reference=reference):
                self.assertIn(
                    "runtime-contract.md",
                    reference.read_text(encoding="utf-8"),
                )

        dod = normalized(topic_body("dod"))
        memory = normalized(topic_body("memory"))
        self.assertIn("mandatory or advisory", dod)
        self.assertIn("mandatory and advisory checked-in material", memory)

    def test_no_unresolved_scaffold_claim_remains(self):
        skill = body("SKILL.md")
        self.assertNotIn("## Initial Design Boundary", skill)
        self.assertNotIn("## Design Questions", skill)
        self.assertNotIn("inspectable design scaffold", skill)
        self.assertNotIn("Do not install, publish, or enable implicit invocation", skill)
        self.assertIn(
            "Local readiness does not authorize installation",
            normalized(skill),
        )

    def test_self_refinement_has_a_convergence_dod(self):
        skill = normalized(body("SKILL.md")).casefold()
        self.assertIn("define the refinement dod before editing", skill)
        self.assertIn("no valid blocker/high finding remains open", skill)
        self.assertIn("two successive fresh reviews produce no new valid blocker/high finding", skill)
        self.assertIn("reviewer agreement alone is not proof", skill)


if __name__ == "__main__":
    unittest.main()
