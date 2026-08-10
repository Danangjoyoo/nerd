from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "nerd-loop" / "scripts" / "loop.py"
SPEC = importlib.util.spec_from_file_location("nerd_loop_runtime", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)


def select_route(request):
    value = {
        "admission_ref": "admission:test",
        "contract_revision": "contract:1",
        **request,
    }
    return loop.select_route(value)


def loop_context(*, state_class="S1", active_iterations=8, wake=False):
    if state_class == "S1":
        endpoint = "review"
        signals = {"multiple_probes": True}
        capabilities = ["session_state"]
    elif state_class == "S2" and wake:
        endpoint = "monitor"
        signals = {"durable_wait": True}
        capabilities = sorted(
            set(loop.STATE_CAPABILITIES["S2"]) | {"authenticated_wake_events"}
        )
    elif state_class == "S2":
        endpoint = "execute"
        signals = {"durable_checkpoint_only": True, "external_receipt": True}
        capabilities = sorted(
            set(loop.STATE_CAPABILITIES["S2"]) | {"effect_reconciliation"}
        )
    elif state_class == "S3":
        endpoint = "execute"
        signals = {"consequential_multiwriter": True}
        capabilities = list(loop.STATE_CAPABILITIES["S3"])
    else:
        raise AssertionError(state_class)
    selected = select_route(
        {
            "schema_version": loop.SCHEMA_VERSION,
            "admission_ref": f"admission:{state_class}:{'wake' if wake else 'active'}:{active_iterations}",
            "contract_revision": "contract:1",
            "endpoint": endpoint,
            "signals": signals,
            "host_capabilities": capabilities,
            "budget": {
                "active_iterations": active_iterations,
                "source": "test",
            },
        }
    )
    selected["host_budget_head"] = host_budget_head(
        selected["admission"], selected["budget_state"]
    )
    return selected


def budget_state(admission, committed=0, *, records=None):
    if records is None:
        records = [
            {
                "iteration_id": f"history-{index}",
                "attempt_id": f"history-attempt-{index}",
                "iteration_commit_ref": f"history-commit-{index}",
                "iteration_commit_hash": f"sha256:history-{index}",
                "budget_consumption_ref": f"budget-consumption:{index}",
                "authenticated": True,
            }
            for index in range(1, committed + 1)
        ]
    identity = loop._budget_identity(
        admission["admission_hash"],
        f"budget:{admission['admission_ref']}",
        admission["active_iteration_budget"],
        records,
        len(records),
    )
    return {
        **identity,
        "budget_hash": loop._canonical_hash(identity),
        "authenticated": True,
    }


def host_budget_head(admission, state, *, head_ref=None):
    if head_ref is None:
        if state["revision"]:
            head_ref = state["committed_iterations"][-1]["budget_consumption_ref"]
        else:
            head_ref = f"budget-head:{admission['admission_ref']}:0"
    return {
        "schema_version": loop.SCHEMA_VERSION,
        "head_ref": head_ref,
        "admission_ref": admission["admission_ref"],
        "admission_hash": admission["admission_hash"],
        "budget_ref": state["budget_ref"],
        "consumption_revision": state["revision"],
        "budget_state_hash": state["budget_hash"],
        "authenticated": True,
    }


def budget_precondition(head):
    return {
        "schema_version": loop.SCHEMA_VERSION,
        "head_ref": head["head_ref"],
        "admission_ref": head["admission_ref"],
        "admission_hash": head["admission_hash"],
        "budget_ref": head["budget_ref"],
        "expected_consumption_revision": head["consumption_revision"],
        "expected_budget_state_hash": head["budget_state_hash"],
    }


def rehash_admission(admission):
    value = dict(admission)
    identity = {key: item for key, item in value.items() if key != "admission_hash"}
    value["admission_hash"] = loop._canonical_hash(identity)
    return value


def dod_item(
    status="FAIL",
    *,
    item_id="DOD-1",
    dod_revision="dod:1",
    artifact_revision="artifact:1",
    verifier_id="verifier:1",
    evidence=True,
    approval_required=False,
    acceptance_owner=None,
    approval=False,
):
    evidence_record = None
    if evidence:
        evidence_record = {
            "ref": f"evidence:{item_id}",
            "criterion_id": item_id,
            "dod_revision": dod_revision,
            "dod_hash": "pending",
            "artifact_revision": artifact_revision,
            "verifier_id": verifier_id,
            "observed_status": status,
            "authenticated": True,
        }
    approval_record = None
    if approval:
        approval_record = {
            "ref": f"approval:{item_id}",
            "criterion_id": item_id,
            "dod_revision": dod_revision,
            "dod_hash": "pending",
            "artifact_revision": artifact_revision,
            "owner": acceptance_owner,
            "decision": "APPROVED",
            "authenticated": True,
        }
    return {
        "id": item_id,
        "source_ref": f"source:{item_id}",
        "required_state_ref": f"required:{item_id}",
        "scope_ref": f"scope:{item_id}",
        "verifier_id": verifier_id,
        "pass_rule_ref": f"pass-rule:{item_id}",
        "freshness_rule_ref": f"freshness:{item_id}",
        "status": status,
        "evidence": evidence_record,
        "approval_required": approval_required,
        "acceptance_owner": acceptance_owner,
        "approval": approval_record,
    }


def dod(criteria=None, integration=None, *, revision="dod:1", artifact_revision="artifact:1"):
    if criteria is None:
        criteria = [dod_item(dod_revision=revision, artifact_revision=artifact_revision)]
    if integration is None:
        integration = []
    value = {
        "revision": revision,
        "artifact_revision": artifact_revision,
        "accepted_hash": "pending",
        "mandatory_criterion_ids": sorted(item["id"] for item in criteria),
        "mandatory_integration_ids": sorted(item["id"] for item in integration),
        "criteria": sorted(criteria, key=lambda item: item["id"]),
        "integration": sorted(integration, key=lambda item: item["id"]),
    }
    value["accepted_hash"] = loop.dod_contract_hash(value)
    for item in value["criteria"] + value["integration"]:
        if item["evidence"] is not None:
            item["evidence"]["dod_hash"] = value["accepted_hash"]
        if item["approval"] is not None:
            item["approval"]["dod_hash"] = value["accepted_hash"]
    return value


def decision(**changes):
    admission = changes.pop("admission", None)
    default_head = None
    if admission is None:
        context = loop_context(state_class="S1", active_iterations=2)
        admission = context["admission"]
        default_head = context["host_budget_head"]
    remaining = changes.pop("budget_remaining", None)
    supplied_budget = changes.pop("budget_state", None)
    if supplied_budget is None:
        committed = 0 if remaining is None else admission["active_iteration_budget"] - remaining
        supplied_budget = budget_state(admission, committed)
    supplied_head = changes.pop("host_budget_head", None)
    if supplied_head is None:
        if (
            default_head is not None
            and supplied_budget["budget_hash"]
            == default_head["budget_state_hash"]
        ):
            supplied_head = default_head
        else:
            supplied_head = host_budget_head(admission, supplied_budget)
    value = {
        "schema_version": loop.SCHEMA_VERSION,
        "admission": admission,
        "dod": dod(),
        "verifier_integrity": "VALID",
        "budget_state": supplied_budget,
        "host_budget_head": supplied_head,
        "dynamics": "NOT_ASSESSED",
        "dynamics_window_valid": False,
        "dynamics_evidence_ref": None,
        "ready_focus_ids": ["work-1"],
        "wake": None,
        "value_assessment": {"positive": True, "evidence_ref": "value:1"},
    }
    value.update(changes)
    return value


def chain():
    return [
        {
            "agent": "codex",
            "skills": ["nerd-surgery"],
            "tools": ["shell"],
            "mcp_servers": [],
        },
        {
            "agent": "reviewer",
            "skills": ["nerd-patrol"],
            "tools": [],
            "mcp_servers": ["github"],
        },
    ]


def registry():
    return {
        "codex": {
            "skills": ["nerd-surgery"],
            "tools": ["shell"],
            "mcp_servers": [],
            "skill_metadata": {
                "nerd-surgery": {"role": "primary", "incompatible_with": []}
            },
        },
        "reviewer": {
            "skills": ["nerd-patrol"],
            "tools": [],
            "mcp_servers": ["github"],
            "skill_metadata": {
                "nerd-patrol": {"role": "primary", "incompatible_with": []}
            },
        },
    }


def authority():
    return {
        agent: {
            key: list(values[key])
            for key in ("skills", "tools", "mcp_servers")
        }
        for agent, values in registry().items()
    }


def routing_context():
    return loop_context(state_class="S2", active_iterations=8)


ROUTING_BUDGET_STATES = {}


def bind_route(route_chain=None, route_registry=None, route_authority=None):
    context = routing_context()
    return loop.routing_transition(
        {
            "schema_version": loop.SCHEMA_VERSION,
            "admission": context["admission"],
            "budget_state": context["budget_state"],
            "host_budget_head": context["host_budget_head"],
            "operation": "bind",
            "proposal_ref": "proposal:1",
            "chain": route_chain or chain(),
            "registry": route_registry or registry(),
            "authority": route_authority or authority(),
        }
    )


def routing_request(operation, cursor, **changes):
    context = routing_context()
    supplied_budget = changes.pop("budget_state", None)
    if supplied_budget is None:
        consumes_active = operation in {"repeat", "satisfy"}
        supplied_budget = routing_budget_state(
            cursor,
            include_active=consumes_active,
            outcome=(
                changes.get("outcome_receipt") or changes.get("completion_receipt") or {}
            ).get("outcome", "DISPROVED"),
        )
    supplied_head = changes.pop("host_budget_head", None)
    if supplied_head is None:
        supplied_head = host_budget_head(context["admission"], supplied_budget)
    ROUTING_BUDGET_STATES[supplied_budget["budget_hash"]] = supplied_budget
    value = {
        "schema_version": loop.SCHEMA_VERSION,
        "admission": context["admission"],
        "budget_state": supplied_budget,
        "host_budget_head": supplied_head,
        "operation": operation,
        "proposal_ref": "proposal:1",
        "chain": chain(),
        "registry": registry(),
        "authority": authority(),
        "cursor": cursor,
        "expected_revision": cursor["revision"],
    }
    value.update(changes)
    return value


def outcome_receipt(cursor, *, outcome="DISPROVED", iteration_id=None):
    index = cursor["profile_index"]
    current_iteration_id = iteration_id or cursor["active_iteration_id"]
    identity = loop._iteration_commit_identity(
        iteration_commit_ref=f"iteration-commit:{current_iteration_id}",
        iteration_commit_event_id=f"event-commit:{current_iteration_id}",
        iteration_commit_revision=4,
        iteration_id=current_iteration_id,
        attempt_id=f"attempt:{current_iteration_id}",
        outcome=outcome,
        admission_hash=cursor["admission_hash"],
        budget_head_ref_before=cursor["budget_head_ref"],
        budget_state_hash_before=cursor["budget_state_hash"],
        budget_consumption_ref=f"budget-consumption:{current_iteration_id}",
        budget_revision_after=cursor["budget_revision"] + 1,
        proposal_ref=cursor["proposal_ref"],
        chain_hash=cursor["chain_hash"],
        profile_index=index,
        profile_hash=loop._canonical_hash(chain()[index]),
    )
    return {
        "ref": f"outcome:{current_iteration_id}",
        "admission_hash": cursor["admission_hash"],
        "proposal_ref": cursor["proposal_ref"],
        "iteration_id": current_iteration_id,
        "attempt_id": identity["attempt_id"],
        "chain_hash": cursor["chain_hash"],
        "profile_index": index,
        "profile_hash": loop._canonical_hash(chain()[index]),
        "outcome": outcome,
        "iteration_commit_ref": identity["iteration_commit_ref"],
        "iteration_commit_event_id": identity["iteration_commit_event_id"],
        "iteration_commit_revision": identity["iteration_commit_revision"],
        "iteration_commit_hash": loop._canonical_hash(identity),
        "budget_head_ref_before": identity["budget_head_ref_before"],
        "budget_state_hash_before": identity["budget_state_hash_before"],
        "budget_consumption_ref": identity["budget_consumption_ref"],
        "budget_revision_after": identity["budget_revision_after"],
        "authenticated": True,
    }


def completion_receipt(cursor, *, iteration_id=None):
    value = outcome_receipt(
        cursor,
        outcome="VERIFIED",
        iteration_id=iteration_id,
    )
    value["guard_ref"] = "guard:passed"
    value["ref"] = f"completion:{value['iteration_id']}"
    return value


def routing_budget_state(cursor, *, include_active=False, outcome="DISPROVED"):
    admission = routing_context()["admission"]
    known = ROUTING_BUDGET_STATES.get(cursor["budget_state_hash"])
    if known is not None:
        records = [dict(record) for record in known["committed_iterations"]]
    else:
        records = [
            {
                "iteration_id": f"history-{index}",
                "attempt_id": f"history-attempt-{index}",
                "iteration_commit_ref": f"history-commit-{index}",
                "iteration_commit_hash": f"sha256:history-{index}",
                "budget_consumption_ref": f"history-consumption-{index}",
                "authenticated": True,
            }
            for index in range(1, cursor["budget_revision"] + 1)
        ]
    if include_active:
        receipt = outcome_receipt(cursor, outcome=outcome)
        records.append(
            {
                "iteration_id": receipt["iteration_id"],
                "attempt_id": receipt["attempt_id"],
                "iteration_commit_ref": receipt["iteration_commit_ref"],
                "iteration_commit_hash": receipt["iteration_commit_hash"],
                "budget_consumption_ref": receipt["budget_consumption_ref"],
                "authenticated": True,
            }
        )
    state = budget_state(admission, records=records)
    ROUTING_BUDGET_STATES[state["budget_hash"]] = state
    return state


def effect_request(
    events,
    *,
    state_class="S2",
    start_revision=0,
    context=None,
):
    if context is None:
        context = loop_context(state_class=state_class, active_iterations=8)
    return {
        "schema_version": loop.SCHEMA_VERSION,
        "admission": context["admission"],
        "budget_state": context["budget_state"],
        "host_budget_head": context["host_budget_head"],
        "start_revision": start_revision,
        "events": events,
    }


class RouteReducerTests(unittest.TestCase):
    def test_direct_path_has_no_loop_state_and_safe_default_is_finite(self):
        result = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {},
                "host_capabilities": [],
            }
        )
        self.assertEqual(result["profile"], "D0")
        self.assertEqual(result["route"], "direct")
        self.assertEqual(result["state_class"], "S0")
        self.assertEqual(result["active_iteration_budget"], 1)
        self.assertEqual(result["budget_source"], "safe_default")
        self.assertTrue(result["admitted"])
        self.assertTrue(result["admission"]["authenticated"])

    def test_admission_rejects_authentication_and_derived_floor_tampering(self):
        selected = loop_context(state_class="S3", active_iterations=2)

        unauthenticated = dict(selected["admission"])
        unauthenticated["authenticated"] = False
        unauthenticated = rehash_admission(unauthenticated)
        with self.assertRaisesRegex(loop.ContractError, "host-authenticated"):
            loop._admission_contract(unauthenticated)

        downgraded = dict(selected["admission"])
        downgraded["state_class"] = "S2"
        downgraded["required_host_capabilities"] = list(
            loop.STATE_CAPABILITIES["S2"]
        )
        downgraded = rehash_admission(downgraded)
        with self.assertRaisesRegex(loop.ContractError, "derived floor"):
            loop._admission_contract(downgraded)

        high_impact = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {"high_impact": True},
                "host_capabilities": list(loop.STATE_CAPABILITIES["S2"]),
            }
        )["admission"]
        high_impact["profile"] = "L3"
        high_impact = rehash_admission(high_impact)
        with self.assertRaisesRegex(loop.ContractError, "derived hard floor"):
            loop._admission_contract(high_impact)

        direct = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {},
                "host_capabilities": [],
            }
        )["admission"]
        direct.update(
            {
                "profile": "L1",
                "state_class": "S1",
                "hard_floor_signals": ["multiple_probes"],
                "host_capabilities": ["session_state"],
                "required_host_capabilities": ["session_state"],
            }
        )
        direct = rehash_admission(direct)
        with self.assertRaisesRegex(loop.ContractError, "direct.*D0"):
            loop._admission_contract(direct)

        explore = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "explore",
                "signals": {"multiple_probes": True},
                "host_capabilities": ["session_state"],
            }
        )["admission"]
        explore.update(
            {
                "profile": "L2",
                "hard_floor_signals": ["local_experiment"],
            }
        )
        explore = rehash_admission(explore)
        with self.assertRaisesRegex(loop.ContractError, "Explore admission"):
            loop._admission_contract(explore)

    def test_maximum_true_floor_wins_and_selects_complex_route(self):
        result = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {
                    "multiple_probes": True,
                    "local_correction_cycle": True,
                    "external_receipt": True,
                    "hard_to_reverse": True,
                },
                "host_capabilities": list(loop.STATE_CAPABILITIES["S3"]),
                "budget": {"active_iterations": 8, "source": "user"},
            }
        )
        self.assertEqual(result["profile"], "L4")
        self.assertEqual(result["route"], "adaptive_program")
        self.assertEqual(result["state_class"], "S2")
        self.assertEqual(result["active_iteration_budget"], 8)
        self.assertTrue(result["admitted"])

    def test_each_l3_and_l4_predicate_enforces_its_floor(self):
        l3_signals = (
            "managed_resumption",
            "durable_wait",
            "formal_human_wait",
            "ci_or_review",
            "external_receipt",
            "independent_child",
            "shared_resource",
        )
        for signal in l3_signals:
            capabilities = list(
                loop.STATE_CAPABILITIES["S3" if signal == "shared_resource" else "S2"]
            )
            if signal in {"durable_wait", "formal_human_wait", "ci_or_review"}:
                capabilities.append("authenticated_wake_events")
            if signal in {"ci_or_review", "external_receipt"}:
                capabilities.append("effect_reconciliation")
            with self.subTest(signal=signal):
                result = select_route(
                    {
                        "schema_version": loop.SCHEMA_VERSION,
                        "endpoint": "execute",
                        "signals": {signal: True},
                        "host_capabilities": capabilities,
                    }
                )
                self.assertEqual(result["profile"], "L3")
                expected_state = "S3" if signal == "shared_resource" else "S2"
                self.assertEqual(result["state_class"], expected_state)
                self.assertTrue(result["admitted"])

        l4_signals = (
            "coupled_contracts",
            "consequential_multiwriter",
            "high_consequence",
            "high_impact",
            "hard_to_reverse",
            "staged_rollout",
            "ambiguous_success",
        )
        for signal in l4_signals:
            with self.subTest(signal=signal):
                result = select_route(
                    {
                        "schema_version": loop.SCHEMA_VERSION,
                        "endpoint": "execute",
                        "signals": {signal: True},
                        "host_capabilities": list(loop.STATE_CAPABILITIES["S3"]),
                    }
                )
                self.assertEqual(result["profile"], "L4")
                expected_state = "S3" if signal == "consequential_multiwriter" else "S2"
                self.assertEqual(result["state_class"], expected_state)
                self.assertTrue(result["admitted"])

    def test_simple_durable_checkpoint_raises_state_not_profile_to_l3(self):
        result = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {
                    "local_correction_cycle": True,
                    "durable_checkpoint_only": True,
                },
                "host_capabilities": list(loop.STATE_CAPABILITIES["S2"]),
            }
        )
        self.assertEqual(result["profile"], "L2")
        self.assertEqual(result["state_class"], "S2")
        self.assertTrue(result["admitted"])
        self.assertNotIn(
            "effect_reconciliation", result["required_host_capabilities"]
        )

    def test_missing_s2_or_s3_capability_fails_closed(self):
        result = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {"external_receipt": True},
                "host_capabilities": ["session_state"],
            }
        )
        self.assertEqual(result["profile"], "L3")
        self.assertFalse(result["admitted"])
        self.assertEqual(result["terminal"]["outcome"], "BLOCKED")
        self.assertIn("durable_store", result["terminal"]["reason"])

    def test_every_required_s2_capability_fails_closed_independently(self):
        complete = set(loop.STATE_CAPABILITIES["S2"]) | {"effect_reconciliation"}
        for missing in sorted(complete):
            with self.subTest(missing=missing):
                result = select_route(
                    {
                        "schema_version": loop.SCHEMA_VERSION,
                        "endpoint": "execute",
                        "signals": {"external_receipt": True},
                        "host_capabilities": sorted(complete - {missing}),
                    }
                )
                self.assertFalse(result["admitted"])
                self.assertEqual(result["missing_host_capabilities"], [missing])

    def test_every_required_s3_capability_fails_closed_independently(self):
        complete = set(loop.STATE_CAPABILITIES["S3"])
        for missing in sorted(complete):
            with self.subTest(missing=missing):
                result = select_route(
                    {
                        "schema_version": loop.SCHEMA_VERSION,
                        "endpoint": "execute",
                        "signals": {"consequential_multiwriter": True},
                        "host_capabilities": sorted(complete - {missing}),
                    }
                )
                self.assertFalse(result["admitted"])
                self.assertEqual(result["missing_host_capabilities"], [missing])

    def test_missing_s1_packet_is_blocked_never_paused(self):
        result = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "review",
                "signals": {"multiple_probes": True},
                "host_capabilities": [],
            }
        )
        self.assertFalse(result["admitted"])
        self.assertEqual(result["terminal"]["outcome"], "BLOCKED")
        self.assertNotIn("PAUSED", json.dumps(result))

    def test_specify_cannot_select_implementation_route(self):
        normal = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "specify",
                "signals": {"adaptive_read_only": True},
                "host_capabilities": ["session_state"],
            }
        )
        self.assertEqual(normal["route"], "draft_validate")
        with self.assertRaisesRegex(loop.ContractError, "incompatible"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "endpoint": "specify",
                    "signals": {"local_correction_cycle": True},
                    "route": "spec_delivery",
                    "host_capabilities": ["session_state"],
                }
            )

    def test_route_floor_cannot_be_lowered_by_signal_omission(self):
        result = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "route": "pr_delivery",
                "signals": {},
                "host_capabilities": list(loop.STATE_CAPABILITIES["S2"])
                + ["authenticated_wake_events", "effect_reconciliation"],
            }
        )
        self.assertEqual(result["profile"], "L3")
        self.assertEqual(result["state_class"], "S2")

    def test_route_implied_wake_capability_and_direct_invariant_fail_closed(self):
        for endpoint, route in (("execute", "pr_delivery"), ("monitor", "monitor")):
            with self.subTest(route=route):
                result = select_route(
                    {
                        "schema_version": loop.SCHEMA_VERSION,
                        "endpoint": endpoint,
                        "route": route,
                        "signals": {},
                        "host_capabilities": list(loop.STATE_CAPABILITIES["S2"]),
                    }
                )
                self.assertFalse(result["admitted"])
                expected = ["authenticated_wake_events"]
                if route == "pr_delivery":
                    expected.append("effect_reconciliation")
                self.assertEqual(result["missing_host_capabilities"], expected)

        with self.assertRaisesRegex(loop.ContractError, "direct.*D0"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "endpoint": "execute",
                    "route": "direct",
                    "signals": {"managed_resumption": True},
                    "host_capabilities": list(loop.STATE_CAPABILITIES["S2"]),
                }
            )

    def test_execute_l3_defaults_to_pr_only_for_ci_and_explore_never_mutates(self):
        resumed = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "endpoint": "execute",
                "signals": {"managed_resumption": True},
                "host_capabilities": list(loop.STATE_CAPABILITIES["S2"]),
            }
        )
        self.assertEqual((resumed["profile"], resumed["route"]), ("L3", "piv"))
        with self.assertRaisesRegex(loop.ContractError, "Explore endpoint"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "endpoint": "explore",
                    "route": "experiment",
                    "signals": {"local_experiment": True},
                    "host_capabilities": ["session_state"],
                }
            )
        with self.assertRaisesRegex(loop.ContractError, "Explore endpoint"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "endpoint": "explore",
                    "signals": {"local_experiment": True},
                    "host_capabilities": ["session_state"],
                }
            )

    def test_unknown_signal_and_unbounded_budget_shapes_are_rejected(self):
        with self.assertRaisesRegex(loop.ContractError, "unknown fields"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "admission_ref": "admission:cli",
                    "contract_revision": "contract:1",
                    "endpoint": "review",
                    "signals": {"looks_complex": True},
                }
            )

    def test_schema_is_required_and_selection_is_byte_deterministic(self):
        request = {
            "schema_version": loop.SCHEMA_VERSION,
            "endpoint": "review",
            "signals": {"multiple_probes": True},
            "host_capabilities": ["session_state"],
        }
        first = json.dumps(select_route(request), sort_keys=True, separators=(",", ":"))
        second = json.dumps(select_route(request), sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)
        missing_schema = dict(request)
        missing_schema.pop("schema_version")
        with self.assertRaisesRegex(loop.ContractError, "schema_version"):
            select_route(missing_schema)
        with self.assertRaisesRegex(loop.ContractError, "integer >= 1"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "endpoint": "review",
                    "signals": {},
                    "host_capabilities": ["session_state"],
                    "budget": {"active_iterations": 0},
                }
            )
        with self.assertRaisesRegex(loop.ContractError, "host_capabilities"):
            select_route(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "endpoint": "review",
                    "signals": {},
                }
            )


class TransitionReducerTests(unittest.TestCase):
    def test_unsafe_beats_cancellation_and_apparent_completion(self):
        result = loop.decide_transition(
            decision(
                unsafe_ref="safety:1",
                cancel_ref="cancel:1",
                dod=dod([dod_item("PASS")]),
            )
        )
        self.assertEqual((result["kind"], result["outcome"]), ("terminal", "UNSAFE"))
        self.assertEqual(result["evidence_ref"], "safety:1")

    def test_ambiguous_effect_and_contract_revision_precede_done(self):
        ambiguous = loop.decide_transition(
            decision(
                ambiguous_effect_ref="effect:unknown",
                dod=dod([dod_item("PASS")]),
            )
        )
        self.assertEqual(ambiguous["action"], "RECONCILE")
        revised = loop.decide_transition(
            decision(
                contract_revision_ref="contract:new",
                dod=dod([dod_item("PASS")]),
            )
        )
        self.assertEqual(revised["action"], "REVISE_CONTRACT")

    def test_verifier_error_cannot_be_done(self):
        result = loop.decide_transition(
            decision(dod=dod([dod_item("PASS")]), verifier_integrity="INVALID")
        )
        self.assertEqual(result["action"], "REPAIR_VERIFIER")

    def test_done_is_bound_to_complete_accepted_dod_evidence_and_approval(self):
        accepted = dod(
            [dod_item("PASS", item_id="DOD-1")],
            [
                dod_item(
                    "PASS",
                    item_id="INT-1",
                    approval_required=True,
                    acceptance_owner="alice",
                    approval=True,
                )
            ],
        )
        result = loop.decide_transition(
            decision(
                dod=accepted,
                budget_remaining=0,
                hard_terminal={
                    "outcome": "EXHAUSTED",
                    "evidence_ref": "budget:1",
                },
            )
        )
        self.assertEqual(result["outcome"], "DONE")
        self.assertEqual(result["dod_hash"], accepted["accepted_hash"])
        self.assertEqual(result["artifact_revision"], "artifact:1")
        self.assertEqual(result["approval_refs"], ["approval:INT-1"])

    def test_dod_omission_and_hash_tampering_are_rejected(self):
        accepted = dod(
            [dod_item("PASS", item_id="DOD-1"), dod_item("PASS", item_id="DOD-2")]
        )
        accepted["criteria"].pop()
        with self.assertRaisesRegex(loop.ContractError, "accepted_hash|exactly match"):
            loop.decide_transition(decision(dod=accepted))

        accepted = dod([dod_item("PASS")])
        accepted["accepted_hash"] = "sha256:forged"
        with self.assertRaisesRegex(loop.ContractError, "accepted_hash|dod_hash"):
            loop.decide_transition(decision(dod=accepted))

    def test_forged_stale_or_wrong_owner_records_are_rejected(self):
        forged = dod([dod_item("PASS")])
        forged["criteria"][0]["evidence"] = "anything"
        with self.assertRaisesRegex(loop.ContractError, "evidence must be an object"):
            loop.decide_transition(decision(dod=forged))

        stale = dod([dod_item("PASS")])
        stale["criteria"][0]["evidence"]["artifact_revision"] = "artifact:old"
        with self.assertRaisesRegex(loop.ContractError, "accepted DoD"):
            loop.decide_transition(decision(dod=stale))

        wrong_owner = dod(
            [
                dod_item(
                    "PASS",
                    approval_required=True,
                    acceptance_owner="alice",
                    approval=True,
                )
            ]
        )
        wrong_owner["criteria"][0]["approval"]["owner"] = "mallory"
        with self.assertRaisesRegex(loop.ContractError, "acceptance owner"):
            loop.decide_transition(decision(dod=wrong_owner))

    def test_status_and_approval_are_derived_from_authenticated_records(self):
        flipped = dod([dod_item("FAIL")])
        flipped["criteria"][0]["status"] = "PASS"
        with self.assertRaisesRegex(loop.ContractError, "authenticated evidence verdict"):
            loop.decide_transition(decision(dod=flipped))

        changed_rule = dod([dod_item("PASS")])
        changed_rule["criteria"][0]["pass_rule_ref"] = "pass-rule:changed"
        changed_rule["accepted_hash"] = loop.dod_contract_hash(changed_rule)
        with self.assertRaisesRegex(loop.ContractError, "dod_hash"):
            loop.decide_transition(decision(dod=changed_rule))

        rejected = dod(
            [
                dod_item(
                    "PASS",
                    approval_required=True,
                    acceptance_owner="alice",
                    approval=True,
                )
            ]
        )
        rejected["criteria"][0]["approval"]["decision"] = "REJECTED"
        result = loop.decide_transition(decision(dod=rejected))
        self.assertNotEqual(result.get("outcome"), "DONE")

    def test_priority_staging_ignores_malformed_lower_priority_payloads(self):
        unsafe = decision(
            unsafe_ref="unsafe:1",
            dod="corrupt",
            dynamics="corrupt",
            value_assessment=None,
        )
        self.assertEqual(loop.decide_transition(unsafe)["outcome"], "UNSAFE")

        cancelled = decision(
            cancel_ref="cancel:1",
            dod="corrupt",
            dynamics="corrupt",
        )
        self.assertEqual(loop.decide_transition(cancelled)["outcome"], "CANCELLED")

        reconcile = decision(
            ambiguous_effect_ref="effect:unknown",
            dod="corrupt",
            wake="corrupt",
        )
        self.assertEqual(loop.decide_transition(reconcile)["action"], "RECONCILE")

        revised = decision(
            contract_revision_ref="contract:new",
            dod="corrupt",
            value_assessment=None,
        )
        self.assertEqual(loop.decide_transition(revised)["action"], "REVISE_CONTRACT")

        done = decision(
            dod=dod([dod_item("PASS")]),
            dynamics="corrupt",
            value_assessment=None,
        )
        self.assertEqual(loop.decide_transition(done)["outcome"], "DONE")

    def test_hard_terminal_and_budget_precede_economic_stop(self):
        impossible = loop.decide_transition(
            decision(
                hard_terminal={
                    "outcome": "IMPOSSIBLE",
                    "evidence_ref": "proof:no-authorized-route",
                },
                budget_remaining=0,
                dynamics="PLATEAUED",
                dynamics_window_valid=True,
                dynamics_evidence_ref="trace:1",
                value_assessment={"positive": False, "evidence_ref": "value:none"},
            )
        )
        self.assertEqual(impossible["outcome"], "IMPOSSIBLE")
        exhausted = loop.decide_transition(
            decision(
                budget_remaining=0,
                dynamics="PLATEAUED",
                dynamics_window_valid=True,
                dynamics_evidence_ref="trace:1",
                value_assessment={"positive": False, "evidence_ref": "value:none"},
            )
        )
        self.assertEqual(exhausted["outcome"], "EXHAUSTED")

    def test_budget_is_admission_bound_and_cannot_reset_per_decision(self):
        context = loop_context(state_class="S1", active_iterations=1)
        selected = loop.decide_transition(
            decision(
                admission=context["admission"],
                budget_state=context["budget_state"],
            )
        )
        self.assertEqual(selected["action"], "SELECT_READY_FOCUS")

        consumed = budget_state(context["admission"], committed=1)
        consumed_head = host_budget_head(context["admission"], consumed)
        exhausted = loop.decide_transition(
            decision(
                admission=context["admission"],
                budget_state=consumed,
                host_budget_head=consumed_head,
            )
        )
        self.assertEqual(exhausted["outcome"], "EXHAUSTED")

        with self.assertRaisesRegex(loop.ContractError, "revision|state hash"):
            loop.decide_transition(
                decision(
                    admission=context["admission"],
                    budget_state=context["budget_state"],
                    host_budget_head=consumed_head,
                )
            )

        missing = decision(admission=context["admission"])
        missing.pop("budget_state")
        with self.assertRaisesRegex(loop.ContractError, "budget_state"):
            loop.decide_transition(missing)

        missing_head = decision(
            admission=context["admission"],
            budget_state=context["budget_state"],
        )
        missing_head.pop("host_budget_head")
        with self.assertRaisesRegex(loop.ContractError, "host_budget_head"):
            loop.decide_transition(missing_head)

    def test_budget_history_rejects_duplicate_attempt_and_consumption_ids(self):
        context = loop_context(state_class="S1", active_iterations=3)
        base_records = [
            {
                "iteration_id": "iteration:1",
                "attempt_id": "attempt:shared",
                "iteration_commit_ref": "commit:1",
                "iteration_commit_hash": "sha256:commit:1",
                "budget_consumption_ref": "consumption:shared",
                "authenticated": True,
            },
            {
                "iteration_id": "iteration:2",
                "attempt_id": "attempt:shared",
                "iteration_commit_ref": "commit:2",
                "iteration_commit_hash": "sha256:commit:2",
                "budget_consumption_ref": "consumption:2",
                "authenticated": True,
            },
        ]
        duplicate_attempt = budget_state(
            context["admission"], records=base_records
        )
        with self.assertRaisesRegex(loop.ContractError, "attempt IDs"):
            loop._budget_state_contract(duplicate_attempt, context["admission"])

        base_records[1]["attempt_id"] = "attempt:2"
        base_records[1]["budget_consumption_ref"] = "consumption:shared"
        duplicate_consumption = budget_state(
            context["admission"], records=base_records
        )
        with self.assertRaisesRegex(loop.ContractError, "consumption references"):
            loop._budget_state_contract(
                duplicate_consumption, context["admission"]
            )

    def test_handoff_requires_recipient_accepted_versioned_packet(self):
        handoff = {
            "outcome": "HANDOFF",
            "evidence_ref": "handoff:reason",
            "packet": {"ref": "packet:1", "revision": 1, "hash": "sha256:packet"},
            "acceptance": {
                "ref": "acceptance:1",
                "packet_ref": "packet:1",
                "packet_revision": 1,
                "packet_hash": "sha256:packet",
                "recipient_id": "agent:next",
                "decision": "ACCEPTED",
                "authenticated": True,
            },
        }
        result = loop.decide_transition(decision(hard_terminal=handoff))
        self.assertEqual(result["outcome"], "HANDOFF")
        self.assertEqual(result["recipient_id"], "agent:next")

        handoff["acceptance"]["packet_hash"] = "sha256:other"
        with self.assertRaisesRegex(loop.ContractError, "packet_hash mismatch"):
            loop.decide_transition(decision(hard_terminal=handoff))

    def test_low_priority_terminal_cannot_encode_unsafe_or_cancelled(self):
        for outcome in ("UNSAFE", "CANCELLED"):
            with self.subTest(outcome=outcome):
                with self.assertRaisesRegex(loop.ContractError, "hard_terminal.outcome"):
                    loop.decide_transition(
                        decision(
                            hard_terminal={
                                "outcome": outcome,
                                "evidence_ref": "invalid:priority",
                            }
                        )
                    )

    def test_unknown_or_failed_parent_integration_cannot_be_done(self):
        unknown = loop.decide_transition(
            decision(
                dod=dod(
                    [dod_item("PASS")],
                    [dod_item("UNKNOWN", item_id="INT-1")],
                ),
                ready_focus_ids=[],
            )
        )
        self.assertNotEqual(unknown.get("outcome"), "DONE")
        failed = loop.decide_transition(
            decision(
                dod=dod(
                    [dod_item("PASS")],
                    [dod_item("FAIL", item_id="INT-1")],
                ),
            )
        )
        self.assertNotEqual(failed.get("outcome"), "DONE")

    def test_pass_without_evidence_is_invalid_and_pending_approval_is_not_done(self):
        with self.assertRaisesRegex(loop.ContractError, "authenticated verdict evidence"):
            loop.decide_transition(
                decision(dod=dod([dod_item("PASS", evidence=False)]))
            )

        pending = loop.decide_transition(
            decision(
                dod=dod(
                    [
                        dod_item(
                            "PASS",
                            approval_required=True,
                            acceptance_owner="alice",
                            approval=False,
                        )
                    ]
                )
            )
        )
        self.assertNotEqual(pending.get("outcome"), "DONE")

    def test_plateau_and_inconclusive_no_value_have_precise_stopped_results(self):
        plateau = loop.decide_transition(
            decision(
                dynamics="PLATEAUED",
                dynamics_window_valid=True,
                dynamics_evidence_ref="trace:plateau",
                value_assessment={"positive": False, "evidence_ref": "value:none"},
            )
        )
        self.assertEqual((plateau["outcome"], plateau["reason"]), ("STOPPED", "PLATEAU"))
        inconclusive = loop.decide_transition(
            decision(
                dynamics="INCONCLUSIVE",
                dynamics_window_valid=True,
                dynamics_evidence_ref="trace:inconclusive",
                value_assessment={"positive": False, "evidence_ref": "value:none"},
            )
        )
        self.assertEqual(
            (inconclusive["outcome"], inconclusive["reason"]),
            ("STOPPED", "INCONCLUSIVE_TRACE"),
        )

    def test_dynamic_diagnosis_requires_a_comparable_evidence_window(self):
        with self.assertRaisesRegex(loop.ContractError, "valid comparable window"):
            loop.decide_transition(decision(dynamics="PLATEAUED"))

    def test_pathology_with_positive_value_changes_strategy(self):
        result = loop.decide_transition(
            decision(
                dynamics="OSCILLATING",
                dynamics_window_valid=True,
                dynamics_evidence_ref="trace:oscillation",
            )
        )
        self.assertEqual(result["action"], "CHANGE_STRATEGY")

    def test_registered_wait_pauses_without_an_active_positive_value_action(self):
        context = loop_context(state_class="S2", active_iterations=2, wake=True)
        result = loop.decide_transition(
            decision(
                admission=context["admission"],
                budget_state=context["budget_state"],
                ready_focus_ids=[],
                wake={
                    "condition_ref": "wake:ci",
                    "deadline_ref": "deadline:1",
                    "registration_ref": "registration:1",
                    "admission_hash": context["admission_hash"],
                    "authenticated": True,
                },
                value_assessment={"positive": False, "evidence_ref": "value:wait"},
            )
        )
        self.assertEqual(result["action"], "PAUSE")

        s1 = loop_context(state_class="S1", active_iterations=2)
        with self.assertRaisesRegex(loop.ContractError, "not admitted"):
            loop.decide_transition(
                decision(
                    admission=s1["admission"],
                    budget_state=s1["budget_state"],
                    ready_focus_ids=[],
                    wake={
                        "condition_ref": "wake:fake",
                        "deadline_ref": "deadline:1",
                        "registration_ref": "registration:fake",
                        "admission_hash": s1["admission_hash"],
                        "authenticated": True,
                    },
                )
            )

    def test_no_ready_or_wake_stops_and_ready_selection_is_deterministic(self):
        stopped = loop.decide_transition(
            decision(
                ready_focus_ids=[],
                value_assessment={"positive": False, "evidence_ref": "value:none"},
            )
        )
        self.assertEqual((stopped["outcome"], stopped["reason"]), ("STOPPED", "NO_READY_WORK"))
        selected = loop.decide_transition(
            decision(ready_focus_ids=["work-a", "work-b"])
        )
        self.assertEqual(selected["focus_id"], "work-a")

    def test_invalid_status_is_rejected_not_coerced(self):
        with self.assertRaisesRegex(loop.ContractError, "criteria.*status"):
            loop.decide_transition(decision(dod=dod([dod_item("SKIPPED")])))


class EffectReducerTests(unittest.TestCase):
    def intent(
        self,
        *,
        fence_token=None,
        dod_contract=None,
        routing_binding=None,
        state_class="S2",
        dod_scope="ITERATION",
        context=None,
    ):
        if context is None:
            context = loop_context(state_class=state_class, active_iterations=8)
        if dod_contract is None:
            dod_contract = dod([dod_item("UNKNOWN", evidence=False)])
        if routing_binding is None:
            routing_binding = {
                "admission_hash": context["admission_hash"],
                "proposal_ref": "proposal:1",
                "chain_hash": loop._canonical_hash(chain()),
                "profile_index": 0,
                "profile_hash": loop._canonical_hash(chain()[0]),
            }
        return {
            "type": "INTENT_COMMITTED",
            "event_id": "event-intent",
            "expected_revision": 0,
            "commit_id": "commit-1",
            "contract_revision": "contract:1",
            "plan_revision": "plan:1",
            "base_revision": "base:1",
            "iteration_id": "iteration-1",
            "attempt_id": "attempt-1",
            "focus_id": "work-1",
            "owner_id": "owner-1",
            "owner_epoch": 1,
            "resource_scope": ["resource:a"],
            "operation_id": "operation-1",
            "idempotency_key": "idempotency-1",
            "expected_result_ref": "expected:1",
            "verifier_id": "verifier:1",
            "abort_rule_ref": "abort:1",
            "admission_hash": context["admission_hash"],
            "budget_revision": context["budget_state"]["revision"],
            "budget_precondition": budget_precondition(
                context["host_budget_head"]
            ),
            "dod_scope": dod_scope,
            "dod_contract": dod_contract,
            "routing_binding": routing_binding,
            "fence_token": fence_token,
        }

    def observed(self, *, outcome="RECEIPT", revision=1, fence_token=None):
        return {
            "type": "ACTION_OBSERVED",
            "event_id": f"event-observed-{revision}",
            "expected_revision": revision,
            "iteration_id": "iteration-1",
            "attempt_id": "attempt-1",
            "operation_id": "operation-1",
            "idempotency_key": "idempotency-1",
            "outcome": outcome,
            "observation_ref": "observation:1",
            "cost_ref": "cost:1",
            "invalidations_ref": "invalidations:none",
            "discoveries_ref": "discoveries:none",
            "best_state_ref": "best:1",
            "ownership_release_ref": "ownership:released",
            "fence_token": fence_token,
        }

    def reconciled(self, *, resolution="APPLIED", revision=2, fence_token=None):
        return {
            "type": "ACTION_RECONCILED",
            "event_id": f"event-reconciled-{revision}",
            "expected_revision": revision,
            "iteration_id": "iteration-1",
            "attempt_id": "attempt-1",
            "operation_id": "operation-1",
            "idempotency_key": "idempotency-1",
            "resolution": resolution,
            "evidence_ref": "reconcile:1",
            "fence_token": fence_token,
        }

    def verification(
        self,
        *,
        revision=2,
        observation_event_id="event-observed-1",
        dod_result=None,
        completion_verdict="FAIL",
        fence_token=None,
    ):
        if dod_result is None:
            dod_result = dod([dod_item("FAIL")])
        return {
            "type": "VERIFICATION_RECORDED",
            "event_id": f"event-verification-{revision}",
            "expected_revision": revision,
            "iteration_id": "iteration-1",
            "attempt_id": "attempt-1",
            "observation_event_id": observation_event_id,
            "dod_result": dod_result,
            "completion_verdict": completion_verdict,
            "fence_token": fence_token,
        }

    def committed(
        self,
        *,
        revision=3,
        verification_event_id="event-verification-2",
        outcome="DISPROVED",
        fence_token=None,
        context=None,
    ):
        if context is None:
            context = loop_context(
                state_class="S3" if fence_token is not None else "S2",
                active_iterations=8,
            )
        return {
            "type": "ITERATION_COMMITTED",
            "event_id": f"event-commit-{revision}",
            "expected_revision": revision,
            "iteration_id": "iteration-1",
            "attempt_id": "attempt-1",
            "outcome": outcome,
            "verification_event_id": verification_event_id,
            "commit_ref": "iteration-commit:1",
            "budget_consumption": {
                "ref": "budget-consumption:1",
                "admission_hash": context["admission_hash"],
                "expected_budget_revision": context["budget_state"]["revision"],
                "units": 1,
                "authenticated": True,
            },
            "fence_token": fence_token,
        }

    def edge(self, *, revision=4, event_type="SUCCESSOR_SELECTED", fence_token=None):
        return {
            "type": event_type,
            "event_id": f"event-edge-{revision}",
            "expected_revision": revision,
            "iteration_id": "iteration-1",
            "cause_ref": "cause:criterion-gap",
            "target_ref": "work:2",
            "fence_token": fence_token,
        }

    def test_intent_then_observation_then_evidence_then_successor(self):
        events = [
            self.intent(),
            self.observed(),
            self.verification(),
            self.committed(),
            self.edge(),
            {
                "type": "CONTEXT_CONDENSED",
                "event_id": "event-condensed",
                "expected_revision": 5,
                "iteration_id": "iteration-1",
                "source_revision": 5,
                "summary_ref": "summary:1",
                "fence_token": None,
            },
        ]
        result = loop.reduce_effect_events(effect_request(events))
        self.assertEqual(result["effect_state"], "CONDENSED")
        self.assertEqual(result["outcome"], "RECEIPT")
        self.assertEqual(result["current_revision"], 6)
        self.assertEqual(
            result["post_commit_events"],
            ["SUCCESSOR_SELECTED", "CONTEXT_CONDENSED"],
        )

    def test_crash_after_intent_has_exact_resume_requirement(self):
        result = loop.reduce_effect_events(effect_request([self.intent()]))
        self.assertEqual(result["effect_state"], "INTENT_COMMITTED")
        self.assertEqual(result["next_required_event"], "ACTION_OBSERVED")
        self.assertEqual(result["requires_committed_revision"], 1)

    def test_intent_requires_complete_versioned_effect_metadata(self):
        old_minimal = {
            "type": "INTENT_COMMITTED",
            "event_id": "event-intent",
            "expected_revision": 0,
            "operation_id": "operation-1",
        }
        with self.assertRaisesRegex(loop.ContractError, "missing required fields"):
            loop.reduce_effect_events(effect_request([old_minimal]))

    def test_unknown_effect_requires_same_operation_reconciliation(self):
        unknown = [self.intent(), self.observed(outcome="OUTCOME_UNKNOWN")]
        result = loop.reduce_effect_events(effect_request(unknown))
        self.assertEqual(result["effect_state"], "RECONCILE_REQUIRED")
        with self.assertRaisesRegex(loop.ContractError, "must be reconciled"):
            loop.reduce_effect_events(
                effect_request(unknown + [self.verification()])
            )
        reconciled = unknown + [
            self.reconciled(),
            self.verification(
                revision=3,
                observation_event_id="event-reconciled-2",
            ),
            self.committed(
                revision=4,
                verification_event_id="event-verification-3",
            ),
        ]
        self.assertEqual(
            loop.reduce_effect_events(effect_request(reconciled))["effect_state"],
            "COMMITTED",
        )

        wrong_key = self.reconciled()
        wrong_key["operation_id"] = "operation-new"
        with self.assertRaisesRegex(loop.ContractError, "operation_id"):
            loop.reduce_effect_events(effect_request(unknown + [wrong_key]))

    def test_not_applied_retries_with_same_attempt_and_idempotency_key(self):
        events = [
            self.intent(),
            self.observed(outcome="OUTCOME_UNKNOWN"),
            self.reconciled(resolution="NOT_APPLIED"),
            self.observed(revision=3),
        ]
        result = loop.reduce_effect_events(effect_request(events))
        self.assertEqual((result["effect_state"], result["outcome"]), ("OBSERVED", "RECEIPT"))

    def test_receipt_before_intent_and_successor_before_commit_are_rejected(self):
        with self.assertRaisesRegex(loop.ContractError, "first effect event"):
            loop.reduce_effect_events(effect_request([self.observed(revision=0)]))
        with self.assertRaisesRegex(loop.ContractError, "verification"):
            loop.reduce_effect_events(
                effect_request([self.intent(), self.observed(), self.edge(revision=2)])
            )

    def test_receipt_verification_and_commit_identity_are_cross_bound(self):
        wrong_observation = self.verification(observation_event_id="event:forged")
        with self.assertRaisesRegex(loop.ContractError, "observation event"):
            loop.reduce_effect_events(
                effect_request([self.intent(), self.observed(), wrong_observation])
            )

        wrong_commit = self.committed(verification_event_id="event:forged")
        with self.assertRaisesRegex(loop.ContractError, "verification event"):
            loop.reduce_effect_events(
                effect_request(
                    [self.intent(), self.observed(), self.verification(), wrong_commit]
                )
            )

    def test_verification_is_bound_to_the_intent_dod_and_completion_verdict(self):
        changed_artifact = self.verification(
            dod_result=dod(
                [dod_item("PASS", artifact_revision="artifact:other")],
                artifact_revision="artifact:other",
            )
        )
        with self.assertRaisesRegex(loop.ContractError, "artifact_revision"):
            loop.reduce_effect_events(
                effect_request([self.intent(), self.observed(), changed_artifact])
            )

        unauthenticated_result = dod([dod_item("PASS")])
        unauthenticated_result["criteria"][0]["evidence"]["authenticated"] = False
        unauthenticated = self.verification(dod_result=unauthenticated_result)
        with self.assertRaisesRegex(loop.ContractError, "authenticated"):
            loop.reduce_effect_events(
                effect_request([self.intent(), self.observed(), unauthenticated])
            )

        wrong_verdict = self.verification(
            dod_result=dod([dod_item("PASS")]),
            completion_verdict="FAIL",
        )
        with self.assertRaisesRegex(loop.ContractError, "completion_verdict"):
            loop.reduce_effect_events(
                effect_request([self.intent(), self.observed(), wrong_verdict])
            )

        failed_result = self.verification(
            dod_result=dod([dod_item("FAIL")]),
            completion_verdict="FAIL",
        )
        with self.assertRaisesRegex(loop.ContractError, "VERIFIED iteration"):
            loop.reduce_effect_events(
                effect_request(
                    [
                        self.intent(),
                        self.observed(),
                        failed_result,
                        self.committed(outcome="VERIFIED"),
                    ]
                )
            )

    def test_effect_commit_identity_is_accepted_by_the_bound_routing_profile(self):
        committed = loop.reduce_effect_events(
            effect_request(
                [
                    self.intent(),
                    self.observed(),
                    self.verification(
                        dod_result=dod([dod_item("PASS")]),
                        completion_verdict="PASS",
                    ),
                    self.committed(outcome="VERIFIED"),
                ]
            )
        )
        commit = committed["iteration_commit"]
        self.assertTrue(committed["verification_complete"])
        self.assertEqual(commit["proposal_ref"], "proposal:1")

        active = loop.routing_transition(
            routing_request(
                "activate",
                bind_route()["cursor"],
                iteration_id="iteration-1",
            )
        )["cursor"]
        receipt = {
            key: value
            for key, value in commit.items()
            if key != "schema_version"
        }
        receipt.update(
            {
                "ref": "completion:iteration-1",
                "guard_ref": "guard:passed",
                "authenticated": True,
            }
        )
        result = loop.routing_transition(
            routing_request(
                "satisfy",
                active,
                iteration_id="iteration-1",
                completion_receipt=receipt,
                budget_state=committed["budget_state"],
            )
        )
        self.assertEqual(result["action"], "ADVANCED_ONE_INDEX")

    def test_effect_state_and_budget_are_bound_to_admission(self):
        s3 = loop_context(state_class="S3", active_iterations=2)
        with self.assertRaisesRegex(loop.ContractError, "fence_token"):
            loop.reduce_effect_events(
                effect_request(
                    [self.intent(state_class="S3", context=s3)],
                    context=s3,
                )
            )

        downgraded = effect_request(
            [self.intent(state_class="S3", context=s3, fence_token="fence:1")],
            context=s3,
        )
        downgraded["state_class"] = "S2"
        with self.assertRaisesRegex(loop.ContractError, "unknown fields"):
            loop.reduce_effect_events(downgraded)

        one = loop_context(state_class="S2", active_iterations=1)
        events = [
            self.intent(context=one),
            self.observed(),
            self.verification(),
            self.committed(context=one),
        ]
        committed = loop.reduce_effect_events(
            effect_request(events, context=one)
        )
        self.assertEqual(committed["budget_state"]["revision"], 1)
        exhausted = loop.decide_transition(
            decision(
                admission=one["admission"],
                budget_state=committed["budget_state"],
            )
        )
        self.assertEqual(exhausted["outcome"], "EXHAUSTED")

    def test_loop_done_is_a_bound_terminal_edge(self):
        context = loop_context(state_class="S2", active_iterations=2)
        events = [
            self.intent(context=context, dod_scope="LOOP"),
            self.observed(),
            self.verification(
                dod_result=dod([dod_item("PASS")]),
                completion_verdict="PASS",
            ),
            self.committed(outcome="VERIFIED", context=context),
        ]
        committed = loop.reduce_effect_events(
            effect_request(events, context=context)
        )
        self.assertEqual(committed["next_required_event"], "LOOP_DONE")
        receipt = {
            "ref": "terminal:done:1",
            "outcome": "DONE",
            "admission_hash": context["admission_hash"],
            "iteration_commit_hash": committed["iteration_commit"][
                "iteration_commit_hash"
            ],
            "budget_hash": committed["budget_state"]["budget_hash"],
            "dod_revision": "dod:1",
            "dod_hash": dod([dod_item("PASS")])["accepted_hash"],
            "artifact_revision": "artifact:1",
            "authenticated": True,
        }
        done_event = {
            "type": "LOOP_DONE",
            "event_id": "event-loop-done",
            "expected_revision": 4,
            "iteration_id": "iteration-1",
            "terminal_receipt": receipt,
            "fence_token": None,
        }
        result = loop.reduce_effect_events(
            effect_request(events + [done_event], context=context)
        )
        self.assertEqual(result["terminal_outcome"], "DONE")
        self.assertEqual(result["effect_state"], "EDGED")

        local_events = list(events)
        local_events[0] = self.intent(context=context, dod_scope="ITERATION")
        with self.assertRaisesRegex(loop.ContractError, "loop-scoped"):
            loop.reduce_effect_events(
                effect_request(local_events + [done_event], context=context)
            )

    def test_budget_head_cas_is_idempotent_and_rejects_partial_replay(self):
        context = loop_context(state_class="S2", active_iterations=1)
        events = [
            self.intent(context=context),
            self.observed(),
            self.verification(),
            self.committed(context=context),
        ]
        first = loop.reduce_effect_events(effect_request(events, context=context))
        self.assertEqual(first["budget_head_status"], "UPDATE_REQUIRED")
        self.assertTrue(first["budget_head_update"]["set"]["authenticated"])

        advanced_head = dict(first["budget_head_update"]["set"])
        replay_request = effect_request(events, context=context)
        replay_request["host_budget_head"] = advanced_head
        replayed = loop.reduce_effect_events(replay_request)
        self.assertEqual(replayed["budget_head_status"], "ALREADY_APPLIED")
        self.assertEqual(replayed["budget_state"], first["budget_state"])

        partial_request = effect_request(events[:-1], context=context)
        partial_request["host_budget_head"] = advanced_head
        with self.assertRaisesRegex(loop.ContractError, "journal extension"):
            loop.reduce_effect_events(partial_request)

        with self.assertRaisesRegex(loop.ContractError, "revision|state hash"):
            loop.decide_transition(
                decision(
                    admission=context["admission"],
                    budget_state=context["budget_state"],
                    host_budget_head=advanced_head,
                )
            )
        exhausted = loop.decide_transition(
            decision(
                admission=context["admission"],
                budget_state=first["budget_state"],
                host_budget_head=advanced_head,
            )
        )
        self.assertEqual(exhausted["outcome"], "EXHAUSTED")

    def test_handoff_terminal_edge_is_typed_and_commit_bound(self):
        context = loop_context(state_class="S2", active_iterations=2)
        events = [
            self.intent(context=context),
            self.observed(),
            self.verification(),
            self.committed(context=context),
        ]
        committed = loop.reduce_effect_events(effect_request(events, context=context))
        packet = {"ref": "packet:1", "revision": 1, "hash": "sha256:packet"}
        acceptance = {
            "ref": "acceptance:1",
            "packet_ref": packet["ref"],
            "packet_revision": packet["revision"],
            "packet_hash": packet["hash"],
            "recipient_id": "agent:next",
            "decision": "ACCEPTED",
            "authenticated": True,
        }
        receipt = {
            "ref": "handoff-receipt:1",
            "outcome": "HANDOFF",
            "admission_hash": context["admission_hash"],
            "iteration_commit_hash": committed["iteration_commit"][
                "iteration_commit_hash"
            ],
            "budget_hash": committed["budget_state"]["budget_hash"],
            "packet_ref": packet["ref"],
            "packet_revision": packet["revision"],
            "packet_hash": packet["hash"],
            "recipient_id": acceptance["recipient_id"],
            "acceptance_ref": acceptance["ref"],
            "authenticated": True,
        }
        handoff_event = {
            "type": "HANDOFF_COMMITTED",
            "event_id": "event-handoff",
            "expected_revision": 4,
            "iteration_id": "iteration-1",
            "cause_ref": "cause:accepted-handoff",
            "packet": packet,
            "acceptance": acceptance,
            "handoff_receipt": receipt,
            "fence_token": None,
        }
        result = loop.reduce_effect_events(
            effect_request(events + [handoff_event], context=context)
        )
        self.assertEqual(result["terminal_outcome"], "HANDOFF")
        self.assertEqual(result["terminal_reason"], "cause:accepted-handoff")
        self.assertEqual(result["terminal_details"]["recipient_id"], "agent:next")

        wrong_admission = dict(handoff_event)
        wrong_admission["handoff_receipt"] = dict(receipt)
        wrong_admission["handoff_receipt"]["admission_hash"] = "sha256:forged"
        with self.assertRaisesRegex(loop.ContractError, "admission_hash mismatch"):
            loop.reduce_effect_events(
                effect_request(events + [wrong_admission], context=context)
            )

        boolean_revision = dict(handoff_event)
        boolean_revision["handoff_receipt"] = dict(receipt)
        boolean_revision["handoff_receipt"]["packet_revision"] = True
        with self.assertRaisesRegex(loop.ContractError, "integer"):
            loop.reduce_effect_events(
                effect_request(events + [boolean_revision], context=context)
            )

    def test_typed_loop_termination_requires_valid_reason_and_real_exhaustion(self):
        context = loop_context(state_class="S2", active_iterations=2)
        events = [
            self.intent(context=context),
            self.observed(),
            self.verification(),
            self.committed(context=context),
        ]
        committed = loop.reduce_effect_events(effect_request(events, context=context))

        def terminal_event(outcome, reason):
            return {
                "type": "LOOP_TERMINATED",
                "event_id": f"event-terminal:{outcome}:{reason}",
                "expected_revision": 4,
                "iteration_id": "iteration-1",
                "terminal_receipt": {
                    "ref": f"terminal:{outcome}:{reason}",
                    "outcome": outcome,
                    "reason": reason,
                    "evidence_ref": "evidence:terminal",
                    "admission_hash": context["admission_hash"],
                    "iteration_commit_hash": committed["iteration_commit"][
                        "iteration_commit_hash"
                    ],
                    "budget_hash": committed["budget_state"]["budget_hash"],
                    "authenticated": True,
                },
                "fence_token": None,
            }

        stopped = loop.reduce_effect_events(
            effect_request(events + [terminal_event("STOPPED", "PLATEAU")], context=context)
        )
        self.assertEqual(
            (stopped["terminal_outcome"], stopped["terminal_reason"]),
            ("STOPPED", "PLATEAU"),
        )
        with self.assertRaisesRegex(loop.ContractError, "reason"):
            loop.reduce_effect_events(
                effect_request(
                    events + [terminal_event("STOPPED", "MADE_UP")],
                    context=context,
                )
            )
        with self.assertRaisesRegex(loop.ContractError, "fully consumed"):
            loop.reduce_effect_events(
                effect_request(
                    events + [terminal_event("EXHAUSTED", "BUDGET")],
                    context=context,
                )
            )

        exhausted_context = loop_context(state_class="S2", active_iterations=1)
        exhausted_events = [
            self.intent(context=exhausted_context),
            self.observed(),
            self.verification(),
            self.committed(context=exhausted_context),
        ]
        exhausted_commit = loop.reduce_effect_events(
            effect_request(exhausted_events, context=exhausted_context)
        )
        exhausted_receipt = terminal_event("EXHAUSTED", "BUDGET")
        exhausted_receipt["terminal_receipt"].update(
            {
                "admission_hash": exhausted_context["admission_hash"],
                "iteration_commit_hash": exhausted_commit["iteration_commit"][
                    "iteration_commit_hash"
                ],
                "budget_hash": exhausted_commit["budget_state"]["budget_hash"],
            }
        )
        exhausted = loop.reduce_effect_events(
            effect_request(
                exhausted_events + [exhausted_receipt],
                context=exhausted_context,
            )
        )
        self.assertEqual(exhausted["terminal_outcome"], "EXHAUSTED")

    def test_effect_integer_fields_reject_booleans(self):
        intent = self.intent()
        intent["budget_revision"] = False
        with self.assertRaisesRegex(loop.ContractError, "integer"):
            loop.reduce_effect_events(effect_request([intent]))

        intent = self.intent()
        intent["budget_precondition"] = dict(intent["budget_precondition"])
        intent["budget_precondition"]["expected_consumption_revision"] = False
        with self.assertRaisesRegex(loop.ContractError, "integer"):
            loop.reduce_effect_events(effect_request([intent]))

        commit = self.committed()
        commit["budget_consumption"] = dict(commit["budget_consumption"])
        commit["budget_consumption"]["units"] = True
        with self.assertRaisesRegex(loop.ContractError, "integer"):
            loop.reduce_effect_events(
                effect_request(
                    [self.intent(), self.observed(), self.verification(), commit]
                )
            )

    def test_effect_append_rejects_reused_budget_identities(self):
        cases = (
            ("attempt", "attempt-1", "attempt already consumed"),
            ("commit", "iteration-commit:1", "commit reference"),
            ("consumption", "budget-consumption:1", "consumption reference"),
        )
        for kind, reused, error in cases:
            with self.subTest(kind=kind):
                context = loop_context(state_class="S2", active_iterations=3)
                prior = {
                    "iteration_id": "history-iteration",
                    "attempt_id": reused if kind == "attempt" else "history-attempt",
                    "iteration_commit_ref": reused if kind == "commit" else "history-commit",
                    "iteration_commit_hash": "sha256:history",
                    "budget_consumption_ref": (
                        reused if kind == "consumption" else "history-consumption"
                    ),
                    "authenticated": True,
                }
                context["budget_state"] = budget_state(
                    context["admission"], records=[prior]
                )
                context["host_budget_head"] = host_budget_head(
                    context["admission"], context["budget_state"]
                )
                events = [
                    self.intent(context=context),
                    self.observed(),
                    self.verification(),
                    self.committed(context=context),
                ]
                with self.assertRaisesRegex(loop.ContractError, error):
                    loop.reduce_effect_events(effect_request(events, context=context))

    def test_whitespace_resource_scope_is_rejected(self):
        intent = self.intent()
        intent["resource_scope"] = [" "]
        with self.assertRaisesRegex(loop.ContractError, "canonical non-empty"):
            loop.reduce_effect_events(effect_request([intent]))

    def test_stale_writer_fence_and_duplicate_event_payload_are_rejected(self):
        stale = self.observed(revision=0)
        with self.assertRaisesRegex(loop.ContractError, "expected_revision is stale"):
            loop.reduce_effect_events(effect_request([self.intent(), stale]))

        with self.assertRaisesRegex(loop.ContractError, "fence_token"):
            loop.reduce_effect_events(
                effect_request(
                    [
                        self.intent(fence_token="fence:1", state_class="S3"),
                        self.observed(fence_token="fence:2"),
                    ],
                    state_class="S3",
                )
            )

        changed_duplicate = self.intent()
        changed_duplicate["focus_id"] = "work:changed"
        with self.assertRaisesRegex(loop.ContractError, "different payload"):
            loop.reduce_effect_events(
                effect_request([self.intent(), changed_duplicate])
            )

        duplicate = self.intent()
        replayed = loop.reduce_effect_events(effect_request([self.intent(), duplicate]))
        self.assertEqual(replayed["current_revision"], 1)

    def test_one_next_edge_precedes_optional_condensation(self):
        committed = [
            self.intent(),
            self.observed(),
            self.verification(),
            self.committed(),
        ]
        condensed = {
            "type": "CONTEXT_CONDENSED",
            "event_id": "event-condensed",
            "expected_revision": 4,
            "iteration_id": "iteration-1",
            "source_revision": 4,
            "summary_ref": "summary:1",
            "fence_token": None,
        }
        with self.assertRaisesRegex(loop.ContractError, "successor, pause, handoff"):
            loop.reduce_effect_events(effect_request(committed + [condensed]))
        with self.assertRaisesRegex(loop.ContractError, "only optional"):
            loop.reduce_effect_events(
                effect_request(
                    committed
                    + [self.edge(), self.edge(revision=5, event_type="LOOP_PAUSED")]
                )
            )


class RoutingCursorTests(unittest.TestCase):
    def test_chain_validation_is_atomic_normalized_and_order_sensitive(self):
        route_chain = chain()
        first = bind_route(route_chain=route_chain)["cursor"]["chain_hash"]
        reversed_chain = list(reversed(route_chain))
        second = bind_route(route_chain=reversed_chain)["cursor"]["chain_hash"]
        self.assertNotEqual(first, second)

        unsorted = chain()
        unsorted[0]["skills"] = ["z-skill", "a-skill"]
        with self.assertRaisesRegex(loop.ContractError, "sorted set"):
            bind_route(route_chain=unsorted)

        duplicate_agent = chain()
        duplicate_agent[1]["agent"] = "codex"
        with self.assertRaisesRegex(loop.ContractError, "agents must be unique"):
            bind_route(route_chain=duplicate_agent)

    def test_registry_is_agent_bound_not_a_global_capability_pool(self):
        wrong_agent_registry = registry()
        wrong_agent_registry["codex"]["tools"] = []
        wrong_agent_registry["reviewer"]["tools"] = ["shell"]
        wrong_agent_authority = authority()
        wrong_agent_authority["codex"]["tools"] = []
        wrong_agent_authority["reviewer"]["tools"] = ["shell"]
        result = bind_route(
            route_registry=wrong_agent_registry,
            route_authority=wrong_agent_authority,
        )
        self.assertEqual(result["action"], "BLOCKED")
        self.assertIn("registry.tools:shell", result["missing_profiles"][0]["missing"])

    def test_routing_rejects_controllers_incompatibilities_and_multiple_primaries(self):
        incompatible_chain = [
            {
                "agent": "codex",
                "skills": ["nerd-loop", "nerd-xfast"],
                "tools": [],
                "mcp_servers": [],
            }
        ]
        incompatible_registry = {
            "codex": {
                "skills": ["nerd-loop", "nerd-xfast"],
                "tools": [],
                "mcp_servers": [],
                "skill_metadata": {
                    "nerd-loop": {
                        "role": "controller",
                        "incompatible_with": ["nerd-xfast"],
                    },
                    "nerd-xfast": {
                        "role": "primary",
                        "incompatible_with": ["nerd-loop"],
                    },
                },
            }
        }
        incompatible_authority = {
            "codex": {
                "skills": ["nerd-loop", "nerd-xfast"],
                "tools": [],
                "mcp_servers": [],
            }
        }
        blocked = bind_route(
            route_chain=incompatible_chain,
            route_registry=incompatible_registry,
            route_authority=incompatible_authority,
        )
        self.assertEqual(blocked["action"], "BLOCKED")
        self.assertTrue(
            any(
                item.startswith("compatibility.")
                for item in blocked["missing_profiles"][0]["missing"]
            )
        )

        xfast_only_chain = [
            {
                "agent": "codex",
                "skills": ["nerd-xfast"],
                "tools": [],
                "mcp_servers": [],
            }
        ]
        xfast_only_registry = {
            "codex": {
                "skills": ["nerd-xfast"],
                "tools": [],
                "mcp_servers": [],
                "skill_metadata": {
                    "nerd-xfast": {
                        "role": "primary",
                        "incompatible_with": ["nerd-loop"],
                    }
                },
            }
        }
        xfast_only_authority = {
            "codex": {
                "skills": ["nerd-xfast"],
                "tools": [],
                "mcp_servers": [],
            }
        }
        blocked = bind_route(
            route_chain=xfast_only_chain,
            route_registry=xfast_only_registry,
            route_authority=xfast_only_authority,
        )
        self.assertIn(
            "compatibility.controller_incompatible:nerd-xfast:nerd-loop",
            blocked["missing_profiles"][0]["missing"],
        )

        multiple_chain = [
            {
                "agent": "codex",
                "skills": ["nerd-patrol", "nerd-surgery"],
                "tools": [],
                "mcp_servers": [],
            }
        ]
        multiple_registry = {
            "codex": {
                "skills": ["nerd-patrol", "nerd-surgery"],
                "tools": [],
                "mcp_servers": [],
                "skill_metadata": {
                    skill: {"role": "primary", "incompatible_with": []}
                    for skill in ("nerd-patrol", "nerd-surgery")
                },
            }
        }
        multiple_authority = {
            "codex": {
                "skills": ["nerd-patrol", "nerd-surgery"],
                "tools": [],
                "mcp_servers": [],
            }
        }
        blocked = bind_route(
            route_chain=multiple_chain,
            route_registry=multiple_registry,
            route_authority=multiple_authority,
        )
        self.assertIn(
            "compatibility.multiple_primary:nerd-patrol,nerd-surgery",
            blocked["missing_profiles"][0]["missing"],
        )

    def test_routing_cursor_is_bound_to_admission_and_budget_revision(self):
        active = loop.routing_transition(
            routing_request(
                "activate",
                bind_route()["cursor"],
                iteration_id="iteration-1",
            )
        )["cursor"]
        other = select_route(
            {
                "schema_version": loop.SCHEMA_VERSION,
                "admission_ref": "admission:other",
                "contract_revision": "contract:1",
                "endpoint": "execute",
                "signals": {
                    "durable_checkpoint_only": True,
                    "external_receipt": True,
                },
                "host_capabilities": sorted(
                    set(loop.STATE_CAPABILITIES["S2"])
                    | {"effect_reconciliation"}
                ),
                "budget": {"active_iterations": 8, "source": "test"},
            }
        )
        request = routing_request("recover", active, ambiguous_effect_ref=None)
        request["admission"] = other["admission"]
        request["budget_state"] = other["budget_state"]
        with self.assertRaisesRegex(loop.ContractError, "admission_ref|admission_hash"):
            loop.routing_transition(request)

        stale_budget = routing_budget_state(active, include_active=False)
        with self.assertRaisesRegex(loop.ContractError, "budget_revision_after"):
            loop.routing_transition(
                routing_request(
                    "repeat",
                    active,
                    iteration_id="iteration-2",
                    outcome_receipt=outcome_receipt(active),
                    budget_state=stale_budget,
                )
            )

    def test_whitespace_only_identifiers_fail_closed(self):
        corrupt = chain()
        corrupt[0]["skills"] = [" "]
        with self.assertRaisesRegex(loop.ContractError, "canonical non-empty"):
            bind_route(route_chain=corrupt)

        with self.assertRaisesRegex(loop.ContractError, "canonical non-empty"):
            loop.decide_transition(decision(ready_focus_ids=[" "]))

    def test_bind_validates_every_profile_and_explicit_authority_before_activation(self):
        later_missing = registry()
        later_missing["reviewer"]["mcp_servers"] = []
        later_authority = authority()
        later_authority["reviewer"]["mcp_servers"] = []
        blocked = bind_route(
            route_registry=later_missing,
            route_authority=later_authority,
        )
        self.assertEqual(blocked["action"], "BLOCKED")
        self.assertEqual(blocked["missing_profiles"][0]["profile_index"], 1)

        denied = authority()
        denied["reviewer"]["mcp_servers"] = []
        blocked = bind_route(route_authority=denied)
        self.assertEqual(blocked["action"], "BLOCKED")
        self.assertIn(
            "authority.mcp_servers:github",
            blocked["missing_profiles"][0]["missing"],
        )

    def test_bind_activate_repeat_and_recover_never_skip_index(self):
        bound = bind_route()
        self.assertEqual((bound["action"], bound["cursor"]["profile_index"]), ("BOUND", 0))
        active = loop.routing_transition(
            routing_request("activate", bound["cursor"], iteration_id="iteration-1")
        )
        self.assertEqual(active["cursor"]["status"], "ACTIVE")
        recovered = loop.routing_transition(
            routing_request("recover", active["cursor"], ambiguous_effect_ref=None)
        )
        self.assertEqual(recovered["action"], "RESUME_SAME_INDEX")
        self.assertEqual(recovered["cursor"]["profile_index"], 0)
        repeated = loop.routing_transition(
            routing_request(
                "repeat",
                active["cursor"],
                iteration_id="iteration-2",
                outcome_receipt=outcome_receipt(active["cursor"]),
            )
        )
        self.assertEqual(repeated["action"], "REPEATED_SAME_INDEX")
        self.assertEqual(repeated["cursor"]["profile_index"], 0)

    def test_satisfaction_advances_exactly_one_then_completes(self):
        cursor = bind_route()["cursor"]
        first = loop.routing_transition(
            routing_request("activate", cursor, iteration_id="iteration-1")
        )["cursor"]
        first_done = loop.routing_transition(
            routing_request(
                "satisfy",
                first,
                iteration_id="iteration-1",
                completion_receipt=completion_receipt(first),
            )
        )
        self.assertEqual(first_done["action"], "ADVANCED_ONE_INDEX")
        self.assertEqual(first_done["cursor"]["profile_index"], 1)
        second = loop.routing_transition(
            routing_request(
                "activate",
                first_done["cursor"],
                iteration_id="iteration-2",
            )
        )["cursor"]
        completed = loop.routing_transition(
            routing_request(
                "satisfy",
                second,
                iteration_id="iteration-2",
                completion_receipt=completion_receipt(second),
            )
        )
        self.assertEqual(completed["action"], "ROUTING_COMPLETE")
        self.assertEqual(completed["cursor"]["profile_index"], 2)
        self.assertEqual(completed["cursor"]["status"], "COMPLETE")

    def test_guard_cas_and_active_iteration_are_enforced(self):
        cursor = bind_route()["cursor"]
        active = loop.routing_transition(
            routing_request("activate", cursor, iteration_id="iteration-1")
        )["cursor"]
        unauthenticated = completion_receipt(active)
        unauthenticated["authenticated"] = False
        with self.assertRaisesRegex(loop.ContractError, "authenticated"):
            loop.routing_transition(
                routing_request(
                    "satisfy",
                    active,
                    iteration_id="iteration-1",
                    completion_receipt=unauthenticated,
                )
            )
        bad_revision = routing_request(
            "recover", active, ambiguous_effect_ref=None
        )
        bad_revision["expected_revision"] -= 1
        with self.assertRaisesRegex(loop.ContractError, "expected_revision"):
            loop.routing_transition(bad_revision)
        with self.assertRaisesRegex(loop.ContractError, "must match"):
            loop.routing_transition(
                routing_request(
                    "satisfy",
                    active,
                    iteration_id="wrong",
                    completion_receipt=completion_receipt(
                        active, iteration_id="wrong"
                    ),
                )
            )

    def test_missing_component_and_registry_change_fail_closed(self):
        missing_registry = registry()
        missing_registry["codex"]["tools"] = []
        missing_authority = authority()
        missing_authority["codex"]["tools"] = []
        blocked = bind_route(
            route_registry=missing_registry,
            route_authority=missing_authority,
        )
        self.assertEqual(blocked["cursor"]["status"], "BLOCKED")
        self.assertIn(
            "registry.tools:shell",
            blocked["missing_profiles"][0]["missing"],
        )

        bound = bind_route()
        changed_registry = registry()
        changed_registry["reviewer"]["mcp_servers"] = []
        request = routing_request(
            "recover", bound["cursor"], ambiguous_effect_ref=None
        )
        request["registry"] = changed_registry
        request["authority"] = {
            agent: {
                key: list(values[key])
                for key in ("skills", "tools", "mcp_servers")
            }
            for agent, values in changed_registry.items()
        }
        changed = loop.routing_transition(request)
        self.assertEqual(changed["action"], "BLOCKED")
        self.assertIn("registry_hash_mismatch", changed["reason"])
        self.assertIn("authority_hash_mismatch", changed["reason"])

        bound = bind_route()
        changed_authority = authority()
        changed_authority["reviewer"]["mcp_servers"] = []
        request = routing_request(
            "recover", bound["cursor"], ambiguous_effect_ref=None
        )
        request["authority"] = changed_authority
        changed = loop.routing_transition(request)
        self.assertEqual(changed["action"], "BLOCKED")
        self.assertEqual(changed["reason"], "authority_hash_mismatch")

    def test_ambiguous_recovery_reconciles_without_cursor_advance(self):
        cursor = bind_route()["cursor"]
        active = loop.routing_transition(
            routing_request("activate", cursor, iteration_id="iteration-1")
        )["cursor"]
        recovered = loop.routing_transition(
            routing_request(
                "recover", active, ambiguous_effect_ref="effect:unknown"
            )
        )
        self.assertEqual(recovered["action"], "RECONCILE_EFFECT")
        self.assertEqual(recovered["cursor"], active)

    def test_no_skip_operation_or_modified_chain_is_accepted(self):
        cursor = bind_route()["cursor"]
        with self.assertRaisesRegex(loop.ContractError, "operation"):
            loop.routing_transition(
                routing_request("skip", cursor, iteration_id="iteration-1")
            )
        changed_chain = chain()
        changed_chain[0]["skills"] = ["nerd-patrol"]
        request = routing_request("recover", cursor, ambiguous_effect_ref=None)
        request["chain"] = changed_chain
        with self.assertRaisesRegex(loop.ContractError, "chain_hash"):
            loop.routing_transition(request)

        request = routing_request("recover", cursor, ambiguous_effect_ref=None)
        request["proposal_ref"] = "proposal:other"
        with self.assertRaisesRegex(loop.ContractError, "proposal_ref"):
            loop.routing_transition(request)

    def test_corrupt_cursor_status_index_and_event_combinations_fail_closed(self):
        active = loop.routing_transition(
            routing_request(
                "activate",
                bind_route()["cursor"],
                iteration_id="iteration-1",
            )
        )["cursor"]
        corruptions = []
        missing_active = dict(active)
        missing_active["active_iteration_id"] = None
        corruptions.append(missing_active)
        out_of_bounds = dict(active)
        out_of_bounds["profile_index"] = 99
        corruptions.append(out_of_bounds)
        garbage_event = dict(active)
        garbage_event["last_event"] = "garbage"
        corruptions.append(garbage_event)
        incoherent_event = dict(active)
        incoherent_event["last_event"] = "ROUTING_BOUND"
        corruptions.append(incoherent_event)

        for cursor in corruptions:
            with self.subTest(cursor=cursor):
                with self.assertRaises(loop.ContractError):
                    loop.routing_transition(
                        routing_request(
                            "recover", cursor, ambiguous_effect_ref=None
                        )
                    )

        complete = dict(active)
        complete.update(
            {
                "status": "COMPLETE",
                "profile_index": 1,
                "active_iteration_id": None,
                "last_event": "ROUTING_COMPLETED",
            }
        )
        with self.assertRaisesRegex(loop.ContractError, "past the final"):
            loop.routing_transition(
                routing_request("recover", complete, ambiguous_effect_ref=None)
            )

        impossible_bound = dict(bind_route()["cursor"])
        impossible_bound["profile_index"] = 1
        with self.assertRaisesRegex(
            loop.ContractError, "reachable initial|profile progress"
        ):
            loop.routing_transition(
                routing_request(
                    "recover", impossible_bound, ambiguous_effect_ref=None
                )
            )

        impossible_satisfied = dict(bind_route()["cursor"])
        impossible_satisfied.update(
            {
                "profile_index": 1,
                "revision": 1,
                "last_event": "ROUTING_PROFILE_SATISFIED",
            }
        )
        with self.assertRaisesRegex(
            loop.ContractError,
            "unreachable revision|profile progress",
        ):
            loop.routing_transition(
                routing_request(
                    "recover", impossible_satisfied, ambiguous_effect_ref=None
                )
            )

    def test_completion_receipt_is_bound_to_chain_index_profile_and_guard(self):
        active = loop.routing_transition(
            routing_request(
                "activate",
                bind_route()["cursor"],
                iteration_id="iteration-1",
            )
        )["cursor"]
        for field, value, message in (
            ("proposal_ref", "proposal:other", "proposal_ref"),
            ("chain_hash", "sha256:wrong", "chain_hash"),
            ("profile_index", 1, "profile_index"),
            ("profile_hash", "sha256:wrong", "profile_hash"),
            ("iteration_commit_ref", "", "iteration_commit_ref"),
            ("iteration_commit_hash", "sha256:wrong", "iteration_commit_hash"),
            ("guard_ref", "", "guard_ref"),
        ):
            record = completion_receipt(active)
            record[field] = value
            with self.subTest(field=field):
                with self.assertRaisesRegex(loop.ContractError, message):
                    loop.routing_transition(
                        routing_request(
                            "satisfy",
                            active,
                            iteration_id="iteration-1",
                            completion_receipt=record,
                        )
                    )

        record = completion_receipt(active)
        unrelated_budget = routing_budget_state(active, include_active=False)
        unrelated_record = {
            "iteration_id": "unrelated-iteration",
            "attempt_id": "unrelated-attempt",
            "iteration_commit_ref": "unrelated-commit",
            "iteration_commit_hash": "sha256:unrelated",
            "budget_consumption_ref": "unrelated-consumption",
            "authenticated": True,
        }
        unrelated_budget = budget_state(
            routing_context()["admission"], records=[unrelated_record]
        )
        with self.assertRaisesRegex(
            loop.ContractError, "budget head belongs|budget consumption record"
        ):
            loop.routing_transition(
                routing_request(
                    "satisfy",
                    active,
                    iteration_id="iteration-1",
                    completion_receipt=record,
                    budget_state=unrelated_budget,
                )
            )


class LoopCliTests(unittest.TestCase):
    def test_cli_emits_one_json_result_and_structured_error(self):
        success = subprocess.run(
            [sys.executable, str(MODULE_PATH), "route"],
            input=json.dumps(
                {
                    "schema_version": loop.SCHEMA_VERSION,
                    "admission_ref": "admission:cli",
                    "contract_revision": "contract:1",
                    "endpoint": "review",
                    "signals": {"multiple_probes": True},
                    "host_capabilities": ["session_state"],
                }
            ),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(json.loads(success.stdout)["profile"], "L1")

        failure = subprocess.run(
            [sys.executable, str(MODULE_PATH), "decide"],
            input="not json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(failure.returncode, 2)
        self.assertEqual(json.loads(failure.stderr)["error"]["type"], "contract_error")


if __name__ == "__main__":
    unittest.main()
