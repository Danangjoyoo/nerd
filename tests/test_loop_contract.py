from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "skills" / "nerd-loop"


def body(relative: str) -> str:
    return (LOOP / relative).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class LoopContractTests(unittest.TestCase):
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
            "definition-of-done.md",
            "convergence.md",
            "iteration.md",
            "behavioral-memory.md",
            "loop-profiles.md",
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
            "## Nerd Memory Routing Compilation", 1
        )[0]
        ordered = (
            "stop unauthorized or unsafe work",
            "honor an authoritative cancellation",
            "reconcile an ambiguous effect",
            "apply current user or higher-authority revisions",
            "validate verifier integrity",
            "if the completion expression passes, return `DONE`",
            "apply an already-reached hard terminal condition",
            "derive the ready set",
            "enter `PAUSED`",
            "diagnose dynamics",
            "select the lexicographically first eligible ready focus",
        )
        offsets = [transition.index(term) for term in ordered]
        self.assertEqual(offsets, sorted(offsets))

        self.assertIn("`DONE` is reachable only through the DoD decision", contract)
        self.assertIn("only the completion expression can return `DONE`", contract)

    def test_durable_effects_use_two_phase_commit_order(self):
        contract = body("references/runtime-contract.md")
        protocol = contract.split("## Iteration and Two-Phase Effect Protocol", 1)[
            1
        ].split("## Transition Priority", 1)[0]
        ordered = (
            "**Intent commit:**",
            "`INTENT_COMMITTED`",
            "**Execute:**",
            "**Outcome commit:**",
            "`ACTION_OBSERVED`",
            "`VERIFICATION_RECORDED`",
            "`ITERATION_COMMITTED`",
            "Exactly one cause-labelled successor",
        )
        offsets = [protocol.index(term) for term in ordered]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn("Never require a receipt before its action", protocol)
        iteration = body("references/iteration.md")
        self.assertNotIn("ACTION_PLANNED", iteration)
        self.assertNotIn("ITERATION_SELECTED and ACTION_INTENT", iteration)

    def test_memory_integration_uses_seven_fields_and_atomic_routing(self):
        skill = normalized(body("SKILL.md"))
        memory = normalized(body("references/behavioral-memory.md"))
        contract = normalized(body("references/runtime-contract.md"))
        for text in (skill, memory, contract):
            self.assertNotIn("six-field", text.casefold())
            self.assertNotIn("six pattern", text.casefold())

        for term in (
            "`goal`, `task`, `action`, `result`, `boundary`, `verification`, and `routing`",
            "Preserve a remembered `routing` chain atomically",
            "authenticated registry",
            "fail closed",
            "lowering a profile floor",
        ):
            self.assertTrue(term in skill or term in memory or term in contract, term)

        self.assertIn("## Mapping the Seven Pattern Types", body("references/behavioral-memory.md"))
        self.assertIn("| `routing` |", body("references/behavioral-memory.md"))
        self.assertIn("all seven pattern types compile", memory)

    def test_runtime_claims_are_bound_to_evidence_authority_and_revisions(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "Freeze the sorted complete mandatory criterion and integration ID sets",
            "hash that immutable definition with its DoD revision",
            "host-authenticated record bound to the criterion ID",
            "wrong verifier, wrong owner",
            "Every event carries the next expected revision",
            "same ID with different payload",
            "every profile",
            "explicit agent-bound allowed-authority map",
            "Reject corrupt or unreachable combinations before returning a resume directive",
            "authenticated completion receipt",
            "`ROUTING_BOUND` is exactly pending/index-zero/revision-zero",
            "hashed identity of the corresponding `ITERATION_COMMITTED`",
            "receipt from another proposal or iteration commit is invalid",
            "exact accepted DoD contract",
            "structured authenticated evidence-bound committed outcome",
        ):
            self.assertIn(term, contract)

    def test_dod_verdicts_and_approval_decisions_are_authenticated(self):
        contract = normalized(body("references/runtime-contract.md"))
        dod = normalized(body("references/definition-of-done.md"))
        for term in (
            "exact accepted DoD hash and revision",
            "Criterion status is a checked projection of that authenticated verdict",
            "without evidence it must be `UNKNOWN`",
            "`APPROVED | REJECTED` decision",
            "Presence alone is not approval",
            "each displayed status equals its verdict",
            "explicitly `APPROVED`",
        ):
            self.assertTrue(term in contract or term in dod, term)

    def test_all_reducers_share_admission_and_cumulative_budget(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "Its `admission_hash` covers every field in that envelope",
            "Pass that exact admitted envelope to `decide`, `effect`, and `routing`",
            "one authenticated cumulative `budget_state`",
            "never accepts a free-standing `budget_remaining`",
            "Every `ITERATION_COMMITTED` consumes exactly one unit",
            "reject a stale, skipped, reset, or cross-admission budget revision",
        ):
            self.assertIn(term, contract)

    def test_transition_validation_is_staged_by_priority(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "parse only through the first matching priority stage",
            "Malformed same-stage or higher-priority data fails closed",
            "malformed lower-priority admission, DoD, budget, wake, value, or dynamics data cannot suppress a valid earlier transition",
        ):
            self.assertIn(term, contract)

    def test_profile_floor_and_routing_compatibility_are_explicit(self):
        contract = normalized(body("references/runtime-contract.md"))
        profiles = normalized(body("references/loop-profiles.md"))
        for term in (
            "`high_impact` and `high_consequence`",
            "`primary | modifier | middleware | controller`",
            "at most one primary specialty",
            "selected incompatible pair fails admission",
            "ordinary S2 checkpoint does not pay for it",
        ):
            self.assertTrue(term in contract or term in profiles, term)

    def test_terminal_receipts_and_handoff_are_identity_bound(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "A passing loop-scoped DoD must choose `LOOP_DONE`",
            "typed non-success receipt is required for `LOOP_TERMINATED`",
            "canonical packet reference, integer revision, and content hash",
            "authenticated acceptance record says `ACCEPTED`",
            "binds that exact packet reference, revision, and hash",
        ):
            self.assertIn(term, contract)

    def test_memory_requires_explicit_current_request_activation(self):
        skill = normalized(body("SKILL.md"))
        memory = normalized(body("references/behavioral-memory.md"))
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
        contract = normalized(body("references/runtime-contract.md"))
        self.assertIn("canonical nonempty string", contract)
        self.assertIn("reject whitespace-only values", contract)
        self.assertIn("leading or trailing whitespace", contract)

    def test_event_wait_and_route_semantics_are_not_caller_optional(self):
        contract = normalized(body("references/runtime-contract.md"))
        for term in (
            "registered wake condition plus deadline is a viable event-driven transition",
            "even when no active action currently has positive value",
            "direct is valid only when the resulting profile remains D0",
            "pr_delivery and durable monitor routes require authenticated wake-event capability",
            "later hard-terminal union cannot encode UNSAFE or CANCELLED",
        ):
            self.assertIn(term, contract.replace("`", ""))

    def test_every_mapped_route_has_one_template_and_consistent_floor(self):
        profiles = body("references/loop-profiles.md")
        mapping = profiles.split("## Nerd Endpoint Mapping", 1)[1].split(
            "## Route Templates", 1
        )[0]
        template_region = profiles.split("## Route Templates", 1)[1].split(
            "## Escalation and De-escalation", 1
        )[0]
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
        convergence = normalized(body("references/convergence.md"))
        iteration = normalized(body("references/iteration.md"))
        profiles = normalized(body("references/loop-profiles.md"))
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
        profiles = normalized(body("references/loop-profiles.md"))
        self.assertIn("Finishing a probe plan is activity, not proof", profiles)
        self.assertIn("declared evidence-coverage criteria pass", profiles)
        self.assertIn("required residual-risk statement is complete", profiles)

    def test_all_normative_references_share_authority_source(self):
        for reference in (
            "definition-of-done.md",
            "convergence.md",
            "iteration.md",
            "behavioral-memory.md",
            "loop-profiles.md",
        ):
            with self.subTest(reference=reference):
                self.assertIn("runtime-contract.md", body(f"references/{reference}"))

        dod = normalized(body("references/definition-of-done.md"))
        memory = normalized(body("references/behavioral-memory.md"))
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
        skill = normalized(body("SKILL.md"))
        self.assertIn("Define the refinement DoD before editing", skill)
        self.assertIn("no valid Blocker/High finding remains open", skill)
        self.assertIn("two successive fresh reviews produce no new valid Blocker/High finding", skill)
        self.assertIn("Reviewer agreement alone is not proof", skill)


if __name__ == "__main__":
    unittest.main()
