#!/usr/bin/env python3
"""Deterministic decision reducer for the Nerd Loop v1 contract.

The reducer has no action authority and performs no task effect. Hosts use it
to make profile, terminal, effect-order, and remembered-routing decisions
reproducible. Durable hosts remain responsible for transactions and fencing.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "nerd-loop/v1"

ENDPOINTS = (
    "discuss",
    "ideate",
    "explore",
    "diagnose",
    "review",
    "specify",
    "document",
    "plan",
    "execute",
    "monitor",
)
PROFILES = ("D0", "L1", "L2", "L3", "L4")
STATE_CLASSES = ("S0", "S1", "S2", "S3")
CRITERION_STATUSES = ("PASS", "FAIL", "UNKNOWN", "ERROR")
DYNAMICS = (
    "NOT_ASSESSED",
    "PROGRESSING",
    "LEARNING",
    "SETTLING",
    "PLATEAUED",
    "PREMATURELY_CONVERGED",
    "STUCK",
    "OSCILLATING",
    "DIVERGING",
    "INCONCLUSIVE",
    "FALSE_CONVERGENCE",
)
TERMINAL_OUTCOMES = (
    "DONE",
    "BLOCKED",
    "CANCELLED",
    "UNSAFE",
    "IMPOSSIBLE",
    "FAILED",
    "EXHAUSTED",
    "STOPPED",
    "HANDOFF",
)
STOP_REASONS = (
    "NO_POSITIVE_VALUE",
    "PLATEAU",
    "INCONCLUSIVE_TRACE",
    "NO_READY_WORK",
)
ROUTING_STATUSES = ("PENDING", "ACTIVE", "COMPLETE", "BLOCKED")
ITERATION_OUTCOMES = (
    "VERIFIED",
    "DISPROVED",
    "BLOCKED",
    "INCONCLUSIVE",
    "FAILED",
)

PROFILE_RANK = {profile: index for index, profile in enumerate(PROFILES)}
STATE_RANK = {state: index for index, state in enumerate(STATE_CLASSES)}

ROUTE_FLOORS = {
    "direct": "D0",
    "options": "L1",
    "draft_validate": "L1",
    "plan_validate": "L1",
    "inspect": "L1",
    "piv": "L2",
    "tdd": "L2",
    "spec_delivery": "L2",
    "routine": "L2",
    "experiment": "L2",
    "pr_delivery": "L3",
    "monitor": "L3",
    "adaptive_program": "L4",
}

ENDPOINT_ROUTES = {
    "discuss": {"direct", "inspect"},
    "ideate": {"options"},
    "explore": {"inspect"},
    "diagnose": {"inspect", "experiment"},
    "review": {"inspect"},
    "specify": {"draft_validate"},
    "document": {"direct", "draft_validate"},
    "plan": {"plan_validate"},
    "execute": {
        "direct",
        "piv",
        "tdd",
        "spec_delivery",
        "routine",
        "experiment",
        "pr_delivery",
        "adaptive_program",
    },
    "monitor": {"inspect", "monitor"},
}

SIGNAL_FLOORS = {
    "adaptive_read_only": "L1",
    "multiple_probes": "L1",
    "local_correction_cycle": "L2",
    "local_experiment": "L2",
    "managed_resumption": "L3",
    "durable_wait": "L3",
    "formal_human_wait": "L3",
    "ci_or_review": "L3",
    "external_receipt": "L3",
    "independent_child": "L3",
    "shared_resource": "L3",
    "coupled_contracts": "L4",
    "consequential_multiwriter": "L4",
    "high_consequence": "L4",
    "high_impact": "L4",
    "hard_to_reverse": "L4",
    "staged_rollout": "L4",
    "ambiguous_success": "L4",
    # This raises state to S2 without adding the other L3 control mechanics.
    "durable_checkpoint_only": "L1",
}

PROFILE_DEFAULT_STATE = {
    "D0": "S0",
    "L1": "S1",
    "L2": "S1",
    "L3": "S2",
    "L4": "S2",
}

S2_CAPABILITIES = (
    "durable_store",
    "idempotency_keys",
    "resume_lookup",
    "schema_checks",
    "single_writer",
    "stable_ids",
)
STATE_CAPABILITIES = {
    "S0": (),
    "S1": ("session_state",),
    "S2": S2_CAPABILITIES,
    "S3": S2_CAPABILITIES
    + (
        "compare_and_append",
        "effect_reconciliation",
        "ledger_fencing",
        "ownership_claims",
        "resource_fencing",
    ),
}

ROUTE_CAPABILITIES = {
    "pr_delivery": ("authenticated_wake_events", "effect_reconciliation"),
    "monitor": ("authenticated_wake_events",),
}

SKILL_ROLES = ("primary", "modifier", "middleware", "controller")
FIXED_SKILL_ROLES = {
    "nerd-execute": "primary",
    "nerd-fast": "modifier",
    "nerd-loop": "controller",
    "nerd-memory": "middleware",
    "nerd-patrol": "primary",
    "nerd-silent": "modifier",
    "nerd-smart": "controller",
    "nerd-surgery": "primary",
    "nerd-xfast": "primary",
}
FIXED_INCOMPATIBILITIES = {
    "nerd-loop": {"nerd-xfast"},
    "nerd-xfast": {"nerd-loop"},
}


class ContractError(ValueError):
    """Raised when an input cannot belong to the v1 contract."""


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name} must be an object")
    return dict(value)


def _reject_unknown(value: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ContractError(f"{name} contains unknown fields: {', '.join(unknown)}")


def _require_schema(value: Mapping[str, Any], name: str) -> None:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"{name}.schema_version must be {SCHEMA_VERSION}")


def _boolean(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{name} must be boolean")
    return value


def _nonempty_string(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise ContractError(f"{name} must be a canonical non-empty string")
    return value


def _optional_string(value: Any, name: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, name)


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{name} must be an integer >= {minimum}")
    return value


def _enum(value: Any, choices: Sequence[str], name: str) -> str:
    if value not in choices:
        raise ContractError(f"{name} must be one of: {', '.join(choices)}")
    return str(value)


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _max_profile(*profiles: str) -> str:
    return max(profiles, key=PROFILE_RANK.__getitem__)


def _max_state(*states: str) -> str:
    return max(states, key=STATE_RANK.__getitem__)


def _default_route(endpoint: str, signal_floor: str, signals: Mapping[str, bool]) -> str:
    if endpoint == "discuss":
        return "direct" if signal_floor == "D0" else "inspect"
    if endpoint == "ideate":
        return "options"
    if endpoint == "explore":
        return "inspect"
    if endpoint == "diagnose":
        return "experiment" if signals["local_experiment"] else "inspect"
    if endpoint == "review":
        return "inspect"
    if endpoint == "specify":
        return "draft_validate"
    if endpoint == "document":
        return "direct" if signal_floor == "D0" else "draft_validate"
    if endpoint == "plan":
        return "plan_validate"
    if endpoint == "execute":
        if signal_floor == "D0":
            return "direct"
        if PROFILE_RANK[signal_floor] >= PROFILE_RANK["L4"]:
            return "adaptive_program"
        if signals["ci_or_review"]:
            return "pr_delivery"
        return "piv"
    if endpoint == "monitor":
        return "monitor" if PROFILE_RANK[signal_floor] >= PROFILE_RANK["L3"] else "inspect"
    raise AssertionError(endpoint)


def select_route(request: Mapping[str, Any]) -> dict[str, Any]:
    """Select the maximum hard floor and fail closed on missing state capability."""

    data = _mapping(request, "route request")
    _reject_unknown(
        data,
        {
            "schema_version",
            "admission_ref",
            "contract_revision",
            "endpoint",
            "signals",
            "route",
            "host_capabilities",
            "budget",
        },
        "route request",
    )
    _require_schema(data, "route request")
    admission_ref = _nonempty_string(data.get("admission_ref"), "admission_ref")
    contract_revision = _nonempty_string(
        data.get("contract_revision"), "contract_revision"
    )
    endpoint = _enum(data.get("endpoint"), ENDPOINTS, "endpoint")

    raw_signals = _mapping(data.get("signals", {}), "signals")
    _reject_unknown(raw_signals, set(SIGNAL_FLOORS), "signals")
    signals = {
        name: _boolean(raw_signals.get(name, False), f"signals.{name}")
        for name in SIGNAL_FLOORS
    }
    if endpoint == "explore" and (
        signals["local_correction_cycle"] or signals["local_experiment"]
    ):
        raise ContractError("Explore endpoint cannot admit mutation or experiment signals")
    true_floor_values = [
        SIGNAL_FLOORS[name] for name, enabled in signals.items() if enabled
    ]
    signal_floor = _max_profile("D0", *true_floor_values)

    route_value = data.get("route")
    route = (
        _enum(route_value, tuple(ROUTE_FLOORS), "route")
        if route_value is not None
        else _default_route(endpoint, signal_floor, signals)
    )
    if route not in ENDPOINT_ROUTES[endpoint]:
        raise ContractError(f"route {route} is incompatible with endpoint {endpoint}")

    profile = _max_profile(signal_floor, ROUTE_FLOORS[route])
    if route == "direct" and profile != "D0":
        raise ContractError("route direct is valid only for a D0 decision")
    state_class = PROFILE_DEFAULT_STATE[profile]
    if signals["durable_checkpoint_only"]:
        state_class = _max_state(state_class, "S2")
    if signals["shared_resource"] or signals["consequential_multiwriter"]:
        state_class = "S3"

    raw_capabilities = data.get("host_capabilities")
    if (
        not isinstance(raw_capabilities, list)
        or any(
            not isinstance(item, str)
            or not item.strip()
            or item != item.strip()
            for item in raw_capabilities
        )
    ):
        raise ContractError(
            "host_capabilities must be a list of canonical non-empty strings"
        )
    capabilities = sorted(set(raw_capabilities))

    budget_value = data.get("budget")
    if budget_value is None:
        active_iterations = 1
        budget_source = "safe_default"
    else:
        budget = _mapping(budget_value, "budget")
        _reject_unknown(budget, {"active_iterations", "source"}, "budget")
        active_iterations = _integer(
            budget.get("active_iterations"), "budget.active_iterations", 1
        )
        budget_source = _nonempty_string(
            budget.get("source", "caller"), "budget.source"
        )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "admission_ref": admission_ref,
        "contract_revision": contract_revision,
        "endpoint": endpoint,
        "profile": profile,
        "route": route,
        "state_class": state_class,
        "active_iteration_budget": active_iterations,
        "budget_source": budget_source,
        "hard_floor_signals": sorted(
            name for name, enabled in signals.items() if enabled
        ),
        "admitted": True,
        "terminal": None,
    }

    required = list(STATE_CAPABILITIES[state_class])
    required.extend(ROUTE_CAPABILITIES.get(route, ()))
    if (
        signals["durable_wait"]
        or signals["formal_human_wait"]
        or signals["ci_or_review"]
    ):
        required.append("authenticated_wake_events")
    if signals["external_receipt"] or signals["staged_rollout"]:
        required.append("effect_reconciliation")
    required = sorted(set(required))
    missing_capabilities = [
        capability for capability in required if capability not in capabilities
    ]
    result["required_host_capabilities"] = required
    result["missing_host_capabilities"] = missing_capabilities
    if missing_capabilities:
        result["admitted"] = False
        result["terminal"] = {
            "outcome": "BLOCKED",
            "reason": "missing_host_capability:" + ",".join(missing_capabilities),
        }
    admission_identity = {
        "schema_version": SCHEMA_VERSION,
        "admission_ref": admission_ref,
        "contract_revision": contract_revision,
        "endpoint": endpoint,
        "profile": profile,
        "route": route,
        "state_class": state_class,
        "active_iteration_budget": active_iterations,
        "budget_source": budget_source,
        "hard_floor_signals": result["hard_floor_signals"],
        "host_capabilities": capabilities,
        "required_host_capabilities": required,
        "wake_admitted": "authenticated_wake_events" in required,
        "admitted": result["admitted"],
        "terminal": result["terminal"],
        "authenticated": True,
    }
    admission = dict(admission_identity)
    admission["admission_hash"] = _canonical_hash(admission_identity)
    result["admission"] = admission
    result["admission_hash"] = admission["admission_hash"]
    result["budget_state"] = _initial_budget_state(admission)
    result["install_precondition"] = {
        "schema_version": SCHEMA_VERSION,
        "admission_ref": admission_ref,
        "contract_revision": contract_revision,
        "expected_budget_head_ref": None,
        "candidate_admission_hash": admission["admission_hash"],
        "candidate_budget_hash": result["budget_state"]["budget_hash"],
    }
    return result


def _admission_contract(value: Any) -> dict[str, Any]:
    admission = _mapping(value, "admission")
    identity_fields = {
        "schema_version",
        "admission_ref",
        "contract_revision",
        "endpoint",
        "profile",
        "route",
        "state_class",
        "active_iteration_budget",
        "budget_source",
        "hard_floor_signals",
        "host_capabilities",
        "required_host_capabilities",
        "wake_admitted",
        "admitted",
        "terminal",
        "authenticated",
    }
    fields = identity_fields | {"admission_hash"}
    _reject_unknown(admission, fields, "admission")
    if set(admission) != fields:
        raise ContractError("admission is missing required fields")
    _require_schema(admission, "admission")
    _nonempty_string(admission["admission_ref"], "admission.admission_ref")
    _nonempty_string(
        admission["contract_revision"], "admission.contract_revision"
    )
    endpoint = _enum(admission["endpoint"], ENDPOINTS, "admission.endpoint")
    profile = _enum(admission["profile"], PROFILES, "admission.profile")
    route = _enum(
        admission["route"], tuple(ROUTE_FLOORS), "admission.route"
    )
    if route not in ENDPOINT_ROUTES[endpoint]:
        raise ContractError("admission route is incompatible with its endpoint")
    hard_floor_signals = _string_list(
        admission["hard_floor_signals"], "admission.hard_floor_signals"
    )
    unknown_signals = sorted(set(hard_floor_signals) - set(SIGNAL_FLOORS))
    if unknown_signals:
        raise ContractError("admission contains unknown hard-floor signals")
    if endpoint == "explore" and set(hard_floor_signals) & {
        "local_correction_cycle",
        "local_experiment",
    }:
        raise ContractError("Explore admission cannot contain mutation signals")
    signal_floor = _max_profile(
        "D0", *(SIGNAL_FLOORS[signal] for signal in hard_floor_signals)
    )
    expected_profile = _max_profile(signal_floor, ROUTE_FLOORS[route])
    if profile != expected_profile:
        raise ContractError("admission profile does not match its derived hard floor")
    if route == "direct" and profile != "D0":
        raise ContractError("admission route direct is valid only for D0")
    state_class = _enum(
        admission["state_class"], STATE_CLASSES, "admission.state_class"
    )
    expected_state = PROFILE_DEFAULT_STATE[profile]
    if "durable_checkpoint_only" in hard_floor_signals:
        expected_state = _max_state(expected_state, "S2")
    if set(hard_floor_signals) & {
        "shared_resource",
        "consequential_multiwriter",
    }:
        expected_state = "S3"
    if state_class != expected_state:
        raise ContractError("admission state_class does not match its derived floor")
    _integer(
        admission["active_iteration_budget"],
        "admission.active_iteration_budget",
        1,
    )
    _nonempty_string(admission["budget_source"], "admission.budget_source")
    host_capabilities = _string_list(
        admission["host_capabilities"], "admission.host_capabilities"
    )
    required_capabilities = _string_list(
        admission["required_host_capabilities"],
        "admission.required_host_capabilities",
    )
    expected_required = list(STATE_CAPABILITIES[state_class])
    expected_required.extend(ROUTE_CAPABILITIES.get(route, ()))
    if set(hard_floor_signals) & {
        "durable_wait",
        "formal_human_wait",
        "ci_or_review",
    }:
        expected_required.append("authenticated_wake_events")
    if set(hard_floor_signals) & {"external_receipt", "staged_rollout"}:
        expected_required.append("effect_reconciliation")
    expected_required = sorted(set(expected_required))
    if required_capabilities != expected_required:
        raise ContractError("admission required capabilities do not match its contract")
    wake_admitted = _boolean(admission["wake_admitted"], "admission.wake_admitted")
    if wake_admitted != ("authenticated_wake_events" in expected_required):
        raise ContractError("admission wake policy does not match required capabilities")
    if wake_admitted and (
        PROFILE_RANK[profile] < PROFILE_RANK["L3"]
        or STATE_RANK[state_class] < STATE_RANK["S2"]
    ):
        raise ContractError("durable wake admission requires L3/S2 or stronger")
    admitted = _boolean(admission["admitted"], "admission.admitted")
    missing = sorted(set(required_capabilities) - set(host_capabilities))
    if admitted != (not missing):
        raise ContractError("admission status does not match host capabilities")
    terminal = admission["terminal"]
    if admitted:
        if terminal is not None:
            raise ContractError("an admitted contract cannot contain a terminal")
    else:
        terminal_record = _mapping(terminal, "admission.terminal")
        _reject_unknown(terminal_record, {"outcome", "reason"}, "admission.terminal")
        if terminal_record.get("outcome") != "BLOCKED":
            raise ContractError("a rejected admission must be BLOCKED")
        terminal_reason = _nonempty_string(
            terminal_record.get("reason"), "admission.terminal.reason"
        )
        expected_reason = "missing_host_capability:" + ",".join(missing)
        if terminal_reason != expected_reason:
            raise ContractError("admission terminal reason does not match missing capabilities")
    if not _boolean(admission["authenticated"], "admission.authenticated"):
        raise ContractError("admission must be host-authenticated")
    identity = {field: admission[field] for field in identity_fields}
    if admission["admission_hash"] != _canonical_hash(identity):
        raise ContractError("admission_hash mismatch")
    if not admitted:
        raise ContractError("a rejected admission cannot authorize a loop command")
    return admission


def _budget_identity(
    admission_hash: str,
    budget_ref: str,
    initial_active_iterations: int,
    committed_iterations: list[dict[str, Any]],
    revision: int,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "admission_hash": admission_hash,
        "budget_ref": budget_ref,
        "initial_active_iterations": initial_active_iterations,
        "committed_iterations": committed_iterations,
        "revision": revision,
    }


def _initial_budget_state(admission: Mapping[str, Any]) -> dict[str, Any]:
    identity = _budget_identity(
        admission["admission_hash"],
        f"budget:{admission['admission_ref']}",
        admission["active_iteration_budget"],
        [],
        0,
    )
    return {
        **identity,
        "budget_hash": _canonical_hash(identity),
        "authenticated": True,
    }


_DOD_DEFINITION_FIELDS = (
    "id",
    "source_ref",
    "required_state_ref",
    "scope_ref",
    "verifier_id",
    "pass_rule_ref",
    "freshness_rule_ref",
    "approval_required",
    "acceptance_owner",
)


def _dod_definition_item(value: Mapping[str, Any]) -> dict[str, Any]:
    return {field: value[field] for field in _DOD_DEFINITION_FIELDS}


def dod_contract_hash(value: Mapping[str, Any]) -> str:
    """Hash the immutable accepted DoD definition, excluding observations."""

    data = _mapping(value, "dod")
    revision = _nonempty_string(data.get("revision"), "dod.revision")
    criterion_ids = _string_list(
        data.get("mandatory_criterion_ids"), "dod.mandatory_criterion_ids"
    )
    integration_ids = _string_list(
        data.get("mandatory_integration_ids", []),
        "dod.mandatory_integration_ids",
    )
    raw_criteria = data.get("criteria")
    raw_integration = data.get("integration", [])
    if not isinstance(raw_criteria, list) or not isinstance(raw_integration, list):
        raise ContractError("dod criteria and integration must be lists")

    definitions: dict[str, list[dict[str, Any]]] = {"criteria": [], "integration": []}
    for label, raw_items in (
        ("criteria", raw_criteria),
        ("integration", raw_integration),
    ):
        for index, raw_item in enumerate(raw_items):
            item = _mapping(raw_item, f"dod.{label}[{index}]")
            missing = [field for field in _DOD_DEFINITION_FIELDS if field not in item]
            if missing:
                raise ContractError(
                    f"dod.{label}[{index}] lacks definition fields: {', '.join(missing)}"
                )
            definitions[label].append(_dod_definition_item(item))

    return _canonical_hash(
        {
            "revision": revision,
            "mandatory_criterion_ids": criterion_ids,
            "mandatory_integration_ids": integration_ids,
            "criteria": definitions["criteria"],
            "integration": definitions["integration"],
        }
    )


def _dod_items(
    value: Any,
    name: str,
    *,
    require_nonempty: bool,
    dod_revision: str,
    dod_hash: str,
    artifact_revision: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractError(f"{name} must be a list")
    if require_nonempty and not value:
        raise ContractError(f"{name} must not be empty")
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    required = {
        "id",
        "source_ref",
        "required_state_ref",
        "scope_ref",
        "verifier_id",
        "pass_rule_ref",
        "freshness_rule_ref",
        "status",
        "evidence",
        "approval_required",
        "acceptance_owner",
        "approval",
    }
    for index, raw_item in enumerate(value):
        item = _mapping(raw_item, f"{name}[{index}]")
        _reject_unknown(item, required, f"{name}[{index}]")
        if set(item) != required:
            raise ContractError(f"{name}[{index}] is missing required fields")
        item_id = _nonempty_string(item["id"], f"{name}[{index}].id")
        if item_id in seen_ids:
            raise ContractError(f"{name} criterion IDs must be unique")
        seen_ids.add(item_id)
        for field in (
            "source_ref",
            "required_state_ref",
            "scope_ref",
            "verifier_id",
            "pass_rule_ref",
            "freshness_rule_ref",
        ):
            _nonempty_string(item[field], f"{name}[{index}].{field}")
        status = _enum(item["status"], CRITERION_STATUSES, f"{name}[{index}].status")

        evidence = item["evidence"]
        evidence_ref: str | None = None
        if evidence is not None:
            evidence_record = _mapping(evidence, f"{name}[{index}].evidence")
            evidence_fields = {
                "ref",
                "criterion_id",
                "dod_revision",
                "dod_hash",
                "artifact_revision",
                "verifier_id",
                "observed_status",
                "authenticated",
            }
            _reject_unknown(
                evidence_record,
                evidence_fields,
                f"{name}[{index}].evidence",
            )
            if set(evidence_record) != evidence_fields:
                raise ContractError(f"{name}[{index}].evidence is missing required fields")
            evidence_ref = _nonempty_string(
                evidence_record["ref"], f"{name}[{index}].evidence.ref"
            )
            expected_bindings = {
                "criterion_id": item_id,
                "dod_revision": dod_revision,
                "dod_hash": dod_hash,
                "artifact_revision": artifact_revision,
                "verifier_id": item["verifier_id"],
            }
            for field, expected in expected_bindings.items():
                if evidence_record[field] != expected:
                    raise ContractError(
                        f"{name}[{index}].evidence.{field} is not bound to the accepted DoD"
                    )
            if not _boolean(
                evidence_record["authenticated"],
                f"{name}[{index}].evidence.authenticated",
            ):
                raise ContractError(f"{name}[{index}].evidence is not authenticated")
            observed_status = _enum(
                evidence_record["observed_status"],
                CRITERION_STATUSES,
                f"{name}[{index}].evidence.observed_status",
            )
            if status != observed_status:
                raise ContractError(
                    f"{name}[{index}].status must equal its authenticated evidence verdict"
                )
        elif status != "UNKNOWN":
            raise ContractError(
                f"{name}[{index}] {status} requires authenticated verdict evidence"
            )

        approval_required = _boolean(
            item["approval_required"], f"{name}[{index}].approval_required"
        )
        acceptance_owner = item["acceptance_owner"]
        if approval_required:
            acceptance_owner = _nonempty_string(
                acceptance_owner, f"{name}[{index}].acceptance_owner"
            )
        elif acceptance_owner is not None:
            raise ContractError(
                f"{name}[{index}].acceptance_owner must be null when approval is not required"
            )

        approval = item["approval"]
        approval_ref: str | None = None
        approval_decision: str | None = None
        if approval is not None:
            if not approval_required:
                raise ContractError(
                    f"{name}[{index}].approval is not allowed without an acceptance owner"
                )
            approval_record = _mapping(approval, f"{name}[{index}].approval")
            approval_fields = {
                "ref",
                "criterion_id",
                "dod_revision",
                "dod_hash",
                "artifact_revision",
                "owner",
                "decision",
                "authenticated",
            }
            _reject_unknown(
                approval_record,
                approval_fields,
                f"{name}[{index}].approval",
            )
            if set(approval_record) != approval_fields:
                raise ContractError(f"{name}[{index}].approval is missing required fields")
            approval_ref = _nonempty_string(
                approval_record["ref"], f"{name}[{index}].approval.ref"
            )
            expected_approval = {
                "criterion_id": item_id,
                "dod_revision": dod_revision,
                "dod_hash": dod_hash,
                "artifact_revision": artifact_revision,
                "owner": acceptance_owner,
            }
            for field, expected in expected_approval.items():
                if approval_record[field] != expected:
                    raise ContractError(
                        f"{name}[{index}].approval.{field} is not bound to the acceptance owner"
                    )
            if not _boolean(
                approval_record["authenticated"],
                f"{name}[{index}].approval.authenticated",
            ):
                raise ContractError(f"{name}[{index}].approval is not authenticated")
            approval_decision = _enum(
                approval_record["decision"],
                ("APPROVED", "REJECTED"),
                f"{name}[{index}].approval.decision",
            )
        items.append(
            {
                "id": item_id,
                "source_ref": item["source_ref"],
                "required_state_ref": item["required_state_ref"],
                "scope_ref": item["scope_ref"],
                "verifier_id": item["verifier_id"],
                "pass_rule_ref": item["pass_rule_ref"],
                "freshness_rule_ref": item["freshness_rule_ref"],
                "status": status,
                "evidence_ref": evidence_ref,
                "approval_required": approval_required,
                "acceptance_owner": acceptance_owner,
                "approval_ref": approval_ref,
                "approval_decision": approval_decision,
            }
        )
    return items


def _dod_contract(value: Any) -> dict[str, Any]:
    data = _mapping(value, "dod")
    required = {
        "revision",
        "artifact_revision",
        "accepted_hash",
        "mandatory_criterion_ids",
        "mandatory_integration_ids",
        "criteria",
        "integration",
    }
    _reject_unknown(data, required, "dod")
    if set(data) != required:
        raise ContractError("dod is missing required fields")
    revision = _nonempty_string(data["revision"], "dod.revision")
    artifact_revision = _nonempty_string(
        data["artifact_revision"], "dod.artifact_revision"
    )
    accepted_hash = _nonempty_string(data["accepted_hash"], "dod.accepted_hash")
    criterion_ids = _string_list(
        data["mandatory_criterion_ids"], "dod.mandatory_criterion_ids"
    )
    if not criterion_ids:
        raise ContractError("dod.mandatory_criterion_ids must not be empty")
    integration_ids = _string_list(
        data["mandatory_integration_ids"], "dod.mandatory_integration_ids"
    )
    if set(criterion_ids) & set(integration_ids):
        raise ContractError("DoD criterion and integration IDs must be disjoint")
    computed_hash = dod_contract_hash(data)
    if accepted_hash != computed_hash:
        raise ContractError("dod.accepted_hash does not match the complete DoD definition")
    criteria = _dod_items(
        data["criteria"],
        "dod.criteria",
        require_nonempty=True,
        dod_revision=revision,
        dod_hash=accepted_hash,
        artifact_revision=artifact_revision,
    )
    integration = _dod_items(
        data["integration"],
        "dod.integration",
        require_nonempty=False,
        dod_revision=revision,
        dod_hash=accepted_hash,
        artifact_revision=artifact_revision,
    )
    if [item["id"] for item in criteria] != criterion_ids:
        raise ContractError("dod.criteria must exactly match the mandatory criterion IDs")
    if [item["id"] for item in integration] != integration_ids:
        raise ContractError("dod.integration must exactly match the mandatory integration IDs")
    return {
        "revision": revision,
        "artifact_revision": artifact_revision,
        "accepted_hash": accepted_hash,
        "criteria": criteria,
        "integration": integration,
    }


def _terminal(outcome: str, reason: str, **details: Any) -> dict[str, Any]:
    _enum(outcome, TERMINAL_OUTCOMES, "terminal outcome")
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": "terminal",
        "outcome": outcome,
        "reason": reason,
    }
    result.update(details)
    return result


def _control(action: str, reason: str, **details: Any) -> dict[str, Any]:
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": "control",
        "action": action,
        "reason": reason,
    }
    result.update(details)
    return result


def _budget_state_contract(
    value: Any,
    admission: Mapping[str, Any],
) -> dict[str, Any]:
    budget = _mapping(value, "budget_state")
    fields = {
        "schema_version",
        "admission_hash",
        "budget_ref",
        "initial_active_iterations",
        "committed_iterations",
        "revision",
        "budget_hash",
        "authenticated",
    }
    _reject_unknown(budget, fields, "budget_state")
    if set(budget) != fields:
        raise ContractError("budget_state is missing required fields")
    _require_schema(budget, "budget_state")
    if budget["admission_hash"] != admission["admission_hash"]:
        raise ContractError("budget_state.admission_hash mismatch")
    budget_ref = _nonempty_string(budget["budget_ref"], "budget_state.budget_ref")
    if budget_ref != f"budget:{admission['admission_ref']}":
        raise ContractError("budget_state.budget_ref mismatch")
    initial = _integer(
        budget["initial_active_iterations"],
        "budget_state.initial_active_iterations",
        1,
    )
    if initial != admission["active_iteration_budget"]:
        raise ContractError("budget_state initial budget differs from admission")
    raw_committed = budget["committed_iterations"]
    if not isinstance(raw_committed, list):
        raise ContractError("budget_state.committed_iterations must be a list")
    committed: list[dict[str, Any]] = []
    seen_iterations: set[str] = set()
    seen_attempts: set[str] = set()
    seen_commits: set[str] = set()
    seen_consumptions: set[str] = set()
    record_fields = {
        "iteration_id",
        "attempt_id",
        "iteration_commit_ref",
        "iteration_commit_hash",
        "budget_consumption_ref",
        "authenticated",
    }
    for index, raw_record in enumerate(raw_committed):
        name = f"budget_state.committed_iterations[{index}]"
        record = _mapping(raw_record, name)
        _reject_unknown(record, record_fields, name)
        if set(record) != record_fields:
            raise ContractError(f"{name} is missing required fields")
        iteration_id = _nonempty_string(record["iteration_id"], f"{name}.iteration_id")
        attempt_id = _nonempty_string(record["attempt_id"], f"{name}.attempt_id")
        commit_ref = _nonempty_string(
            record["iteration_commit_ref"], f"{name}.iteration_commit_ref"
        )
        _nonempty_string(
            record["iteration_commit_hash"], f"{name}.iteration_commit_hash"
        )
        consumption_ref = _nonempty_string(
            record["budget_consumption_ref"], f"{name}.budget_consumption_ref"
        )
        if not _boolean(record["authenticated"], f"{name}.authenticated"):
            raise ContractError(f"{name} must be authenticated")
        if iteration_id in seen_iterations:
            raise ContractError("budget_state iteration IDs must be unique")
        if attempt_id in seen_attempts:
            raise ContractError("budget_state attempt IDs must be unique")
        if commit_ref in seen_commits:
            raise ContractError("budget_state commit references must be unique")
        if consumption_ref in seen_consumptions:
            raise ContractError("budget_state consumption references must be unique")
        seen_iterations.add(iteration_id)
        seen_attempts.add(attempt_id)
        seen_commits.add(commit_ref)
        seen_consumptions.add(consumption_ref)
        committed.append(record)
    revision = _integer(budget["revision"], "budget_state.revision", 0)
    if revision != len(committed):
        raise ContractError("budget_state.revision must equal committed consumption count")
    if len(committed) > initial:
        raise ContractError("budget_state exceeds the admitted active budget")
    identity = _budget_identity(
        budget["admission_hash"], budget_ref, initial, committed, revision
    )
    if budget["budget_hash"] != _canonical_hash(identity):
        raise ContractError("budget_state.budget_hash mismatch")
    if not _boolean(budget["authenticated"], "budget_state.authenticated"):
        raise ContractError("budget_state must be host-authenticated")
    return {
        "initial": initial,
        "committed": committed,
        "committed_iteration_ids": seen_iterations,
        "committed_attempt_ids": seen_attempts,
        "committed_commit_refs": seen_commits,
        "committed_consumption_refs": seen_consumptions,
        "revision": revision,
        "remaining": initial - len(committed),
        "budget_ref": budget_ref,
        "budget_hash": budget["budget_hash"],
    }


def _host_budget_head_contract(
    host_head_value: Any,
    admission: Mapping[str, Any],
    budget_ref: str,
) -> dict[str, Any]:
    host_head = _mapping(host_head_value, "host_budget_head")
    head_fields = {
        "schema_version",
        "head_ref",
        "admission_ref",
        "admission_hash",
        "budget_ref",
        "consumption_revision",
        "budget_state_hash",
        "authenticated",
    }
    _reject_unknown(host_head, head_fields, "host_budget_head")
    if set(host_head) != head_fields:
        raise ContractError("host_budget_head is missing required fields")
    _require_schema(host_head, "host_budget_head")
    head_ref = _nonempty_string(host_head["head_ref"], "host_budget_head.head_ref")
    if host_head["admission_ref"] != admission["admission_ref"]:
        raise ContractError("host_budget_head.admission_ref mismatch")
    if host_head["admission_hash"] != admission["admission_hash"]:
        raise ContractError("host_budget_head.admission_hash mismatch")
    if host_head["budget_ref"] != budget_ref:
        raise ContractError("host_budget_head.budget_ref mismatch")
    consumption_revision = _integer(
        host_head["consumption_revision"],
        "host_budget_head.consumption_revision",
        0,
    )
    budget_state_hash = _nonempty_string(
        host_head["budget_state_hash"], "host_budget_head.budget_state_hash"
    )
    if not _boolean(host_head["authenticated"], "host_budget_head.authenticated"):
        raise ContractError("host_budget_head must be host-authenticated")
    return {
        "head_ref": head_ref,
        "consumption_revision": consumption_revision,
        "budget_state_hash": budget_state_hash,
    }


def _budget_precondition(
    admission: Mapping[str, Any],
    budget_ref: str,
    head_ref: str,
    revision: int,
    budget_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "head_ref": head_ref,
        "admission_ref": admission["admission_ref"],
        "admission_hash": admission["admission_hash"],
        "budget_ref": budget_ref,
        "expected_consumption_revision": revision,
        "expected_budget_state_hash": budget_hash,
    }


def _budget_contract(
    value: Any,
    admission: Mapping[str, Any],
    host_head_value: Any,
) -> dict[str, Any]:
    budget = _budget_state_contract(value, admission)
    host_head = _host_budget_head_contract(
        host_head_value, admission, budget["budget_ref"]
    )
    if host_head["consumption_revision"] != budget["revision"]:
        raise ContractError("host_budget_head consumption revision mismatch")
    if host_head["budget_state_hash"] != budget["budget_hash"]:
        raise ContractError("host_budget_head budget state hash mismatch")
    if (
        budget["revision"] > 0
        and host_head["head_ref"]
        != budget["committed"][-1]["budget_consumption_ref"]
    ):
        raise ContractError("host_budget_head does not name the latest consumption")
    return {
        **budget,
        "head_ref": host_head["head_ref"],
        "precondition": _budget_precondition(
            admission,
            budget["budget_ref"],
            host_head["head_ref"],
            budget["revision"],
            budget["budget_hash"],
        ),
    }


def _handoff_binding(
    packet_value: Any,
    acceptance_value: Any,
    name: str,
) -> dict[str, Any]:
    packet = _mapping(packet_value, f"{name}.packet")
    packet_fields = {"ref", "revision", "hash"}
    _reject_unknown(packet, packet_fields, f"{name}.packet")
    if set(packet) != packet_fields:
        raise ContractError(f"{name}.packet is missing required fields")
    packet_ref = _nonempty_string(packet["ref"], f"{name}.packet.ref")
    packet_revision = _integer(
        packet["revision"], f"{name}.packet.revision", 1
    )
    packet_hash = _nonempty_string(packet["hash"], f"{name}.packet.hash")
    acceptance = _mapping(acceptance_value, f"{name}.acceptance")
    acceptance_fields = {
        "ref",
        "packet_ref",
        "packet_revision",
        "packet_hash",
        "recipient_id",
        "decision",
        "authenticated",
    }
    _reject_unknown(acceptance, acceptance_fields, f"{name}.acceptance")
    if set(acceptance) != acceptance_fields:
        raise ContractError(f"{name}.acceptance is missing required fields")
    acceptance_ref = _nonempty_string(
        acceptance["ref"], f"{name}.acceptance.ref"
    )
    recipient_id = _nonempty_string(
        acceptance["recipient_id"], f"{name}.acceptance.recipient_id"
    )
    if acceptance["packet_ref"] != packet_ref:
        raise ContractError("handoff acceptance packet_ref mismatch")
    acceptance_packet_revision = _integer(
        acceptance["packet_revision"], f"{name}.acceptance.packet_revision", 1
    )
    if acceptance_packet_revision != packet_revision:
        raise ContractError("handoff acceptance packet_revision mismatch")
    if acceptance["packet_hash"] != packet_hash:
        raise ContractError("handoff acceptance packet_hash mismatch")
    if acceptance["decision"] != "ACCEPTED":
        raise ContractError("handoff recipient must explicitly accept the packet")
    if not _boolean(
        acceptance["authenticated"], f"{name}.acceptance.authenticated"
    ):
        raise ContractError("handoff acceptance must be authenticated")
    return {
        "packet_ref": packet_ref,
        "packet_revision": packet_revision,
        "packet_hash": packet_hash,
        "recipient_id": recipient_id,
        "acceptance_ref": acceptance_ref,
    }


def _hard_terminal_contract(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    record = _mapping(value, "hard_terminal")
    outcome = _enum(
        record.get("outcome"),
        ("BLOCKED", "IMPOSSIBLE", "FAILED", "HANDOFF"),
        "hard_terminal.outcome",
    )
    if outcome != "HANDOFF":
        fields = {"outcome", "evidence_ref"}
        _reject_unknown(record, fields, "hard_terminal")
        if set(record) != fields:
            raise ContractError("hard_terminal is missing required fields")
        return {
            "outcome": outcome,
            "evidence_ref": _nonempty_string(
                record["evidence_ref"], "hard_terminal.evidence_ref"
            ),
        }

    fields = {"outcome", "evidence_ref", "packet", "acceptance"}
    _reject_unknown(record, fields, "hard_terminal")
    if set(record) != fields:
        raise ContractError("HANDOFF terminal is missing required fields")
    evidence_ref = _nonempty_string(
        record["evidence_ref"], "hard_terminal.evidence_ref"
    )
    return {
        "outcome": outcome,
        "evidence_ref": evidence_ref,
        **_handoff_binding(
            record["packet"], record["acceptance"], "hard_terminal"
        ),
    }


def _wake_contract(
    value: Any,
    admission: Mapping[str, Any],
    name: str = "wake",
) -> dict[str, Any]:
    if not admission["wake_admitted"]:
        raise ContractError("wake was not admitted by the bound route contract")
    wake = _mapping(value, name)
    fields = {
        "condition_ref",
        "deadline_ref",
        "registration_ref",
        "admission_hash",
        "authenticated",
    }
    _reject_unknown(wake, fields, name)
    if set(wake) != fields:
        raise ContractError(f"{name} is missing required fields")
    _nonempty_string(wake["condition_ref"], f"{name}.condition_ref")
    _nonempty_string(wake["deadline_ref"], f"{name}.deadline_ref")
    _nonempty_string(wake["registration_ref"], f"{name}.registration_ref")
    if wake["admission_hash"] != admission["admission_hash"]:
        raise ContractError(f"{name}.admission_hash mismatch")
    if not _boolean(wake["authenticated"], f"{name}.authenticated"):
        raise ContractError(f"{name} registration must be authenticated")
    return wake


def decide_transition(request: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the single v1 transition-priority function."""

    data = _mapping(request, "decision request")
    allowed = {
        "schema_version",
        "unsafe_ref",
        "cancel_ref",
        "ambiguous_effect_ref",
        "schema_mismatch_ref",
        "stale_owner_ref",
        "contract_revision_ref",
        "admission",
        "verifier_integrity",
        "dod",
        "hard_terminal",
        "budget_state",
        "host_budget_head",
        "dynamics",
        "dynamics_window_valid",
        "dynamics_evidence_ref",
        "ready_focus_ids",
        "wake",
        "value_assessment",
    }
    _reject_unknown(data, allowed, "decision request")
    _require_schema(data, "decision request")

    # Parse only through the first matching priority stage. Corruption in a
    # lower-priority payload must not suppress a safety or recovery transition.
    unsafe_ref = _optional_string(data.get("unsafe_ref"), "unsafe_ref")
    if unsafe_ref is not None:
        return _terminal(
            "UNSAFE", "unsafe_or_unauthorized", evidence_ref=unsafe_ref
        )

    cancel_ref = _optional_string(data.get("cancel_ref"), "cancel_ref")
    if cancel_ref is not None:
        return _terminal(
            "CANCELLED", "authoritative_cancellation", evidence_ref=cancel_ref
        )

    ambiguous_effect_ref = _optional_string(
        data.get("ambiguous_effect_ref"), "ambiguous_effect_ref"
    )
    schema_mismatch_ref = _optional_string(
        data.get("schema_mismatch_ref"), "schema_mismatch_ref"
    )
    stale_owner_ref = _optional_string(
        data.get("stale_owner_ref"), "stale_owner_ref"
    )
    reconciliation_refs = sorted(
        ref
        for ref in (
            ambiguous_effect_ref,
            schema_mismatch_ref,
            stale_owner_ref,
        )
        if ref is not None
    )
    if reconciliation_refs:
        return _control(
            "RECONCILE",
            "effect_schema_or_ownership_state",
            evidence_refs=reconciliation_refs,
        )

    contract_revision_ref = _optional_string(
        data.get("contract_revision_ref"), "contract_revision_ref"
    )
    if contract_revision_ref is not None:
        return _control(
            "REVISE_CONTRACT",
            "higher_authority_revision",
            evidence_ref=contract_revision_ref,
        )

    admission = _admission_contract(data.get("admission"))
    verifier_integrity = _enum(
        data.get("verifier_integrity", "VALID"),
        ("VALID", "INVALID", "UNKNOWN"),
        "verifier_integrity",
    )
    if verifier_integrity != "VALID":
        return _control(
            "REPAIR_VERIFIER",
            verifier_integrity.lower(),
            admission_hash=admission["admission_hash"],
        )

    dod = _dod_contract(data.get("dod"))

    done = all(
        item["status"] == "PASS"
        and bool(item["evidence_ref"])
        and (
            not item["approval_required"]
            or item["approval_decision"] == "APPROVED"
        )
        for item in dod["criteria"] + dod["integration"]
    )
    if done:
        return _terminal(
            "DONE",
            "dod_completion_expression_passed",
            admission_hash=admission["admission_hash"],
            dod_revision=dod["revision"],
            dod_hash=dod["accepted_hash"],
            artifact_revision=dod["artifact_revision"],
            evidence_refs=[
                item["evidence_ref"]
                for item in dod["criteria"] + dod["integration"]
            ],
            approval_refs=[
                item["approval_ref"]
                for item in dod["criteria"] + dod["integration"]
                if item["approval_ref"] is not None
            ],
        )
    hard_terminal = _hard_terminal_contract(data.get("hard_terminal"))
    if hard_terminal is not None:
        return _terminal(
            hard_terminal["outcome"],
            f"declared_hard_terminal:{hard_terminal['evidence_ref']}",
            admission_hash=admission["admission_hash"],
            **{
                key: value
                for key, value in hard_terminal.items()
                if key != "outcome"
            },
        )
    budget = _budget_contract(
        data.get("budget_state"), admission, data.get("host_budget_head")
    )

    if budget["remaining"] == 0:
        return _terminal(
            "EXHAUSTED",
            "active_budget_exhausted",
            admission_hash=admission["admission_hash"],
            budget_revision=budget["revision"],
            budget_precondition=budget["precondition"],
        )

    ready_focus_ids = _string_list(
        data.get("ready_focus_ids", []), "ready_focus_ids"
    )
    wake_value = data.get("wake")
    if wake_value is None:
        wake = None
    else:
        wake = _wake_contract(wake_value, admission)

    # A registered event-driven wait is itself the viable next transition. It
    # does not require a currently executable positive-value action.
    if not ready_focus_ids and wake is not None:
        return _control(
            "PAUSE",
            "declared_wake_condition",
            admission_hash=admission["admission_hash"],
            budget_precondition=budget["precondition"],
            condition_ref=wake["condition_ref"],
            deadline_ref=wake["deadline_ref"],
            registration_ref=wake["registration_ref"],
        )

    value_assessment = _mapping(data.get("value_assessment"), "value_assessment")
    value_fields = {"positive", "evidence_ref"}
    _reject_unknown(value_assessment, value_fields, "value_assessment")
    if set(value_assessment) != value_fields:
        raise ContractError("value_assessment is missing required fields")
    positive_value_action = _boolean(
        value_assessment["positive"], "value_assessment.positive"
    )
    value_evidence_ref = _nonempty_string(
        value_assessment["evidence_ref"], "value_assessment.evidence_ref"
    )
    dynamics = _enum(data.get("dynamics", "NOT_ASSESSED"), DYNAMICS, "dynamics")
    dynamics_window_valid = _boolean(
        data.get("dynamics_window_valid", False), "dynamics_window_valid"
    )
    dynamics_evidence_ref = _optional_string(
        data.get("dynamics_evidence_ref"), "dynamics_evidence_ref"
    )
    if dynamics == "NOT_ASSESSED":
        if dynamics_window_valid or dynamics_evidence_ref is not None:
            raise ContractError(
                "NOT_ASSESSED dynamics cannot claim a valid evidence window"
            )
    elif not dynamics_window_valid or dynamics_evidence_ref is None:
        raise ContractError(
            "a dynamic diagnosis requires a valid comparable window and evidence"
        )

    if not positive_value_action:
        if dynamics == "PLATEAUED":
            return _terminal(
                "STOPPED",
                "PLATEAU",
                admission_hash=admission["admission_hash"],
                budget_precondition=budget["precondition"],
                evidence_refs=[dynamics_evidence_ref, value_evidence_ref],
            )
        if dynamics == "INCONCLUSIVE":
            return _terminal(
                "STOPPED",
                "INCONCLUSIVE_TRACE",
                admission_hash=admission["admission_hash"],
                budget_precondition=budget["precondition"],
                evidence_refs=[dynamics_evidence_ref, value_evidence_ref],
            )
        if not ready_focus_ids:
            return _terminal(
                "STOPPED",
                "NO_READY_WORK",
                admission_hash=admission["admission_hash"],
                budget_precondition=budget["precondition"],
                evidence_ref=value_evidence_ref,
            )
        return _terminal(
            "STOPPED",
            "NO_POSITIVE_VALUE",
            admission_hash=admission["admission_hash"],
            budget_precondition=budget["precondition"],
            evidence_ref=value_evidence_ref,
        )

    if dynamics in {
        "PLATEAUED",
        "PREMATURELY_CONVERGED",
        "STUCK",
        "OSCILLATING",
        "DIVERGING",
        "FALSE_CONVERGENCE",
    }:
        return _control(
            "CHANGE_STRATEGY",
            dynamics.lower(),
            admission_hash=admission["admission_hash"],
            budget_precondition=budget["precondition"],
        )
    if dynamics == "INCONCLUSIVE":
        return _control(
            "REPAIR_OR_REPEAT_MEASUREMENT",
            "inconclusive_trace",
            admission_hash=admission["admission_hash"],
            budget_precondition=budget["precondition"],
        )
    if ready_focus_ids:
        return _control(
            "SELECT_READY_FOCUS",
            "eligible_positive_value_action",
            admission_hash=admission["admission_hash"],
            budget_precondition=budget["precondition"],
            focus_id=ready_focus_ids[0],
            value_evidence_ref=value_evidence_ref,
        )
    return _terminal(
        "STOPPED",
        "NO_READY_WORK",
        admission_hash=admission["admission_hash"],
        budget_precondition=budget["precondition"],
        evidence_ref=value_evidence_ref,
    )


def _routing_binding(value: Any, name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    binding = _mapping(value, name)
    fields = {
        "admission_hash",
        "proposal_ref",
        "chain_hash",
        "profile_index",
        "profile_hash",
    }
    _reject_unknown(binding, fields, name)
    if set(binding) != fields:
        raise ContractError(f"{name} is missing required fields")
    _nonempty_string(binding["admission_hash"], f"{name}.admission_hash")
    _nonempty_string(binding["proposal_ref"], f"{name}.proposal_ref")
    _nonempty_string(binding["chain_hash"], f"{name}.chain_hash")
    _integer(binding["profile_index"], f"{name}.profile_index", 0)
    _nonempty_string(binding["profile_hash"], f"{name}.profile_hash")
    return binding


def _iteration_commit_identity(
    *,
    iteration_commit_ref: str,
    iteration_commit_event_id: str,
    iteration_commit_revision: int,
    iteration_id: str,
    attempt_id: str,
    outcome: str,
    admission_hash: str,
    budget_head_ref_before: str,
    budget_state_hash_before: str,
    budget_consumption_ref: str,
    budget_revision_after: int,
    proposal_ref: str | None,
    chain_hash: str | None,
    profile_index: int | None,
    profile_hash: str | None,
) -> dict[str, Any]:
    """Return the exact record hashed into a routing completion receipt."""

    return {
        "schema_version": SCHEMA_VERSION,
        "iteration_commit_ref": iteration_commit_ref,
        "iteration_commit_event_id": iteration_commit_event_id,
        "iteration_commit_revision": iteration_commit_revision,
        "iteration_id": iteration_id,
        "attempt_id": attempt_id,
        "outcome": outcome,
        "admission_hash": admission_hash,
        "budget_head_ref_before": budget_head_ref_before,
        "budget_state_hash_before": budget_state_hash_before,
        "budget_consumption_ref": budget_consumption_ref,
        "budget_revision_after": budget_revision_after,
        "proposal_ref": proposal_ref,
        "chain_hash": chain_hash,
        "profile_index": profile_index,
        "profile_hash": profile_hash,
    }


def reduce_effect_events(request: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a versioned effect journal and its crash/retry invariants."""

    data = _mapping(request, "effect request")
    _reject_unknown(
        data,
        {
            "schema_version",
            "admission",
            "budget_state",
            "host_budget_head",
            "start_revision",
            "events",
        },
        "effect request",
    )
    _require_schema(data, "effect request")
    admission = _admission_contract(data.get("admission"))
    state_class = admission["state_class"]
    if state_class not in {"S2", "S3"}:
        raise ContractError("effect journal requires an admitted S2 or S3 contract")
    budget = _budget_state_contract(data.get("budget_state"), admission)
    current_budget_head = _host_budget_head_contract(
        data.get("host_budget_head"), admission, budget["budget_ref"]
    )
    head_delta = current_budget_head["consumption_revision"] - budget["revision"]
    if head_delta not in {0, 1}:
        raise ContractError("effect host budget head is stale or skips a revision")
    if head_delta == 0:
        if current_budget_head["budget_state_hash"] != budget["budget_hash"]:
            raise ContractError("effect host budget head hash mismatch")
        if (
            budget["revision"] > 0
            and current_budget_head["head_ref"]
            != budget["committed"][-1]["budget_consumption_ref"]
        ):
            raise ContractError("effect host budget head is not current")
        budget["head_ref"] = current_budget_head["head_ref"]
        budget["precondition"] = _budget_precondition(
            admission,
            budget["budget_ref"],
            current_budget_head["head_ref"],
            budget["revision"],
            budget["budget_hash"],
        )
    else:
        budget["head_ref"] = None
        budget["precondition"] = None
    if budget["remaining"] == 0:
        raise ContractError("effect journal cannot start after active budget exhaustion")
    revision = _integer(data.get("start_revision"), "start_revision", 0)
    events = data.get("events")
    if not isinstance(events, list):
        raise ContractError("events must be a list")

    state = "EMPTY"
    iteration_id: str | None = None
    attempt_id: str | None = None
    operation_id: str | None = None
    idempotency_key: str | None = None
    verifier_id: str | None = None
    intent_dod: dict[str, Any] | None = None
    intent_dod_scope: str | None = None
    intent_routing: dict[str, Any] | None = None
    result_dod: dict[str, Any] | None = None
    fence_token: str | None = None
    outcome: str | None = None
    observation_event_id: str | None = None
    verification_event_id: str | None = None
    verification_complete = False
    iteration_outcome: str | None = None
    iteration_commit: dict[str, Any] | None = None
    next_budget_state: dict[str, Any] | None = None
    budget_head_update: dict[str, Any] | None = None
    terminal_outcome: str | None = None
    terminal_reason: str | None = None
    terminal_details: dict[str, Any] | None = None
    post_commit_events: list[str] = []
    seen_events: dict[str, str] = {}

    def require_fields(event: Mapping[str, Any], fields: set[str], name: str) -> None:
        _reject_unknown(event, fields, name)
        if set(event) != fields:
            missing = sorted(fields - set(event))
            raise ContractError(f"{name} is missing required fields: {', '.join(missing)}")

    def validate_fence(event: Mapping[str, Any], name: str) -> str | None:
        value = event["fence_token"]
        if state_class == "S3":
            current = _nonempty_string(value, f"{name}.fence_token")
        else:
            current = _optional_string(value, f"{name}.fence_token")
        if state != "EMPTY" and current != fence_token:
            raise ContractError("effect events must retain the committed fence_token")
        return current

    def validate_binding(event: Mapping[str, Any], name: str) -> None:
        if event["iteration_id"] != iteration_id:
            raise ContractError(f"{name}.iteration_id does not match the intent")
        if event.get("attempt_id") != attempt_id:
            raise ContractError(f"{name}.attempt_id does not match the intent")
        if event.get("operation_id") != operation_id:
            raise ContractError(f"{name}.operation_id does not match the intent")
        if event.get("idempotency_key") != idempotency_key:
            raise ContractError(f"{name}.idempotency_key does not match the intent")

    for index, raw_event in enumerate(events):
        name = f"events[{index}]"
        event = _mapping(raw_event, name)
        event_type = _nonempty_string(event.get("type"), f"{name}.type")
        event_id = _nonempty_string(event.get("event_id"), f"{name}.event_id")
        event_digest = _canonical_hash(event)
        if event_id in seen_events:
            if seen_events[event_id] != event_digest:
                raise ContractError("duplicate event_id has a different payload")
            continue
        seen_events[event_id] = event_digest

        expected_revision = _integer(
            event.get("expected_revision"), f"{name}.expected_revision", 0
        )
        if expected_revision != revision:
            raise ContractError(
                f"{name}.expected_revision is stale: expected {revision}"
            )

        if state == "EMPTY":
            if event_type != "INTENT_COMMITTED":
                raise ContractError("first effect event must be INTENT_COMMITTED")
            fields = {
                "type",
                "event_id",
                "expected_revision",
                "commit_id",
                "contract_revision",
                "plan_revision",
                "base_revision",
                "iteration_id",
                "attempt_id",
                "focus_id",
                "owner_id",
                "owner_epoch",
                "resource_scope",
                "operation_id",
                "idempotency_key",
                "expected_result_ref",
                "verifier_id",
                "abort_rule_ref",
                "admission_hash",
                "budget_revision",
                "budget_precondition",
                "dod_scope",
                "dod_contract",
                "routing_binding",
                "fence_token",
            }
            require_fields(event, fields, name)
            for field in (
                "commit_id",
                "contract_revision",
                "plan_revision",
                "base_revision",
                "iteration_id",
                "attempt_id",
                "focus_id",
                "owner_id",
                "operation_id",
                "idempotency_key",
                "expected_result_ref",
                "verifier_id",
                "abort_rule_ref",
            ):
                _nonempty_string(event[field], f"{name}.{field}")
            _integer(event["owner_epoch"], f"{name}.owner_epoch", 1)
            resource_scope = _string_list(event["resource_scope"], f"{name}.resource_scope")
            if not resource_scope:
                raise ContractError("INTENT_COMMITTED requires a non-empty resource_scope")
            iteration_id = event["iteration_id"]
            if iteration_id in budget["committed_iteration_ids"]:
                raise ContractError("iteration already consumed the admitted budget")
            attempt_id = event["attempt_id"]
            if attempt_id in budget["committed_attempt_ids"]:
                raise ContractError("attempt already consumed the admitted budget")
            operation_id = event["operation_id"]
            idempotency_key = event["idempotency_key"]
            verifier_id = event["verifier_id"]
            if event["contract_revision"] != admission["contract_revision"]:
                raise ContractError("intent contract_revision differs from admission")
            if event["admission_hash"] != admission["admission_hash"]:
                raise ContractError("intent admission_hash mismatch")
            intent_budget_revision = _integer(
                event["budget_revision"], f"{name}.budget_revision", 0
            )
            if intent_budget_revision != budget["revision"]:
                raise ContractError("intent budget_revision mismatch")
            intent_budget_precondition = _mapping(
                event["budget_precondition"], f"{name}.budget_precondition"
            )
            precondition_fields = {
                "schema_version",
                "head_ref",
                "admission_ref",
                "admission_hash",
                "budget_ref",
                "expected_consumption_revision",
                "expected_budget_state_hash",
            }
            _reject_unknown(
                intent_budget_precondition,
                precondition_fields,
                f"{name}.budget_precondition",
            )
            if set(intent_budget_precondition) != precondition_fields:
                raise ContractError("intent budget_precondition is missing required fields")
            _integer(
                intent_budget_precondition["expected_consumption_revision"],
                f"{name}.budget_precondition.expected_consumption_revision",
                0,
            )
            base_head_ref = _nonempty_string(
                intent_budget_precondition.get("head_ref"),
                f"{name}.budget_precondition.head_ref",
            )
            expected_budget_precondition = _budget_precondition(
                admission,
                budget["budget_ref"],
                base_head_ref,
                budget["revision"],
                budget["budget_hash"],
            )
            if intent_budget_precondition != expected_budget_precondition:
                raise ContractError("intent budget_precondition mismatch")
            if head_delta == 0 and intent_budget_precondition != budget["precondition"]:
                raise ContractError("intent does not bind the current host budget head")
            budget["head_ref"] = base_head_ref
            budget["precondition"] = intent_budget_precondition
            intent_dod = _dod_contract(event["dod_contract"])
            intent_dod_scope = _enum(
                event["dod_scope"], ("ITERATION", "LOOP"), f"{name}.dod_scope"
            )
            intent_routing = _routing_binding(
                event["routing_binding"], f"{name}.routing_binding"
            )
            if (
                intent_routing is not None
                and intent_routing["admission_hash"] != admission["admission_hash"]
            ):
                raise ContractError("routing binding admission_hash mismatch")
            fence_token = validate_fence(event, name)
            revision += 1
            state = "INTENT_COMMITTED"
            continue

        if state == "INTENT_COMMITTED":
            if event_type != "ACTION_OBSERVED":
                raise ContractError("ACTION_OBSERVED must follow committed intent")
            fields = {
                "type",
                "event_id",
                "expected_revision",
                "iteration_id",
                "attempt_id",
                "operation_id",
                "idempotency_key",
                "outcome",
                "observation_ref",
                "cost_ref",
                "invalidations_ref",
                "discoveries_ref",
                "best_state_ref",
                "ownership_release_ref",
                "fence_token",
            }
            require_fields(event, fields, name)
            validate_binding(event, name)
            validate_fence(event, name)
            for field in (
                "observation_ref",
                "cost_ref",
                "invalidations_ref",
                "discoveries_ref",
                "best_state_ref",
                "ownership_release_ref",
            ):
                _nonempty_string(event[field], f"{name}.{field}")
            outcome = _enum(
                event["outcome"],
                ("RECEIPT", "FAILURE", "OUTCOME_UNKNOWN"),
                f"{name}.outcome",
            )
            revision += 1
            if outcome == "OUTCOME_UNKNOWN":
                if "effect_reconciliation" not in admission["host_capabilities"]:
                    raise ContractError(
                        "OUTCOME_UNKNOWN requires admitted effect_reconciliation"
                    )
                state = "RECONCILE_REQUIRED"
            else:
                observation_event_id = event_id
                state = "OBSERVED"
            continue

        if state == "RECONCILE_REQUIRED":
            if event_type != "ACTION_RECONCILED":
                raise ContractError("unknown action outcome must be reconciled before progress")
            fields = {
                "type",
                "event_id",
                "expected_revision",
                "iteration_id",
                "attempt_id",
                "operation_id",
                "idempotency_key",
                "resolution",
                "evidence_ref",
                "fence_token",
            }
            require_fields(event, fields, name)
            validate_binding(event, name)
            validate_fence(event, name)
            _nonempty_string(event["evidence_ref"], f"{name}.evidence_ref")
            resolution = _enum(
                event["resolution"],
                ("APPLIED", "NOT_APPLIED", "FAILED", "UNRESOLVED"),
                f"{name}.resolution",
            )
            revision += 1
            if resolution == "APPLIED":
                outcome = "RECEIPT"
                observation_event_id = event_id
                state = "OBSERVED"
            elif resolution == "FAILED":
                outcome = "FAILURE"
                observation_event_id = event_id
                state = "OBSERVED"
            elif resolution == "NOT_APPLIED":
                outcome = None
                state = "INTENT_COMMITTED"
            else:
                outcome = "OUTCOME_UNKNOWN"
            continue

        if state == "OBSERVED":
            if event_type != "VERIFICATION_RECORDED":
                raise ContractError("verification must follow the observed action outcome")
            fields = {
                "type",
                "event_id",
                "expected_revision",
                "iteration_id",
                "attempt_id",
                "observation_event_id",
                "dod_result",
                "completion_verdict",
                "fence_token",
            }
            require_fields(event, fields, name)
            if event["iteration_id"] != iteration_id or event["attempt_id"] != attempt_id:
                raise ContractError("verification must bind to the active iteration and attempt")
            if event["observation_event_id"] != observation_event_id:
                raise ContractError("verification must reference the resolved observation event")
            validate_fence(event, name)
            if intent_dod is None:
                raise AssertionError("intent DoD was not initialized")
            result_dod = _dod_contract(event["dod_result"])
            for field in ("revision", "accepted_hash", "artifact_revision"):
                if result_dod[field] != intent_dod[field]:
                    raise ContractError(
                        f"verification DoD {field} does not match committed intent"
                    )
            all_results = result_dod["criteria"] + result_dod["integration"]
            if any(item["evidence_ref"] is None for item in all_results):
                raise ContractError(
                    "verification requires authenticated evidence for every DoD result"
                )
            verification_complete = all(
                item["status"] == "PASS"
                and item["evidence_ref"] is not None
                and (
                    not item["approval_required"]
                    or item["approval_decision"] == "APPROVED"
                )
                for item in all_results
            )
            declared_verdict = _enum(
                event["completion_verdict"],
                ("PASS", "FAIL"),
                f"{name}.completion_verdict",
            )
            expected_verdict = "PASS" if verification_complete else "FAIL"
            if declared_verdict != expected_verdict:
                raise ContractError(
                    "completion_verdict does not match the bound DoD results"
                )
            verification_event_id = event_id
            revision += 1
            state = "VERIFIED"
            continue

        if state == "VERIFIED":
            if event_type != "ITERATION_COMMITTED":
                raise ContractError("ITERATION_COMMITTED must follow verification")
            fields = {
                "type",
                "event_id",
                "expected_revision",
                "iteration_id",
                "attempt_id",
                "outcome",
                "verification_event_id",
                "commit_ref",
                "budget_consumption",
                "fence_token",
            }
            require_fields(event, fields, name)
            if event["iteration_id"] != iteration_id or event["attempt_id"] != attempt_id:
                raise ContractError("iteration commit must bind to the active attempt")
            if event["verification_event_id"] != verification_event_id:
                raise ContractError("iteration commit must reference its verification event")
            validate_fence(event, name)
            iteration_outcome = _enum(
                event["outcome"], ITERATION_OUTCOMES, f"{name}.outcome"
            )
            if iteration_outcome == "VERIFIED" and outcome != "RECEIPT":
                raise ContractError("VERIFIED iteration requires an applied action receipt")
            if (iteration_outcome == "VERIFIED") != verification_complete:
                raise ContractError(
                    "VERIFIED iteration must exactly match a passing DoD verdict"
                )
            commit_ref = _nonempty_string(event["commit_ref"], f"{name}.commit_ref")
            if commit_ref in budget["committed_commit_refs"]:
                raise ContractError("iteration commit_ref already consumed budget")
            consumption = _mapping(
                event["budget_consumption"], f"{name}.budget_consumption"
            )
            consumption_fields = {
                "ref",
                "admission_hash",
                "expected_budget_revision",
                "units",
                "authenticated",
            }
            require_fields(
                consumption,
                consumption_fields,
                f"{name}.budget_consumption",
            )
            consumption_ref = _nonempty_string(
                consumption["ref"], f"{name}.budget_consumption.ref"
            )
            if consumption_ref in budget["committed_consumption_refs"]:
                raise ContractError("budget consumption ref was already used")
            if consumption["admission_hash"] != admission["admission_hash"]:
                raise ContractError("budget consumption admission_hash mismatch")
            expected_budget_revision = _integer(
                consumption["expected_budget_revision"],
                f"{name}.budget_consumption.expected_budget_revision",
                0,
            )
            if expected_budget_revision != budget["revision"]:
                raise ContractError("budget consumption expected revision mismatch")
            units = _integer(
                consumption["units"], f"{name}.budget_consumption.units", 1
            )
            if units != 1:
                raise ContractError("each committed iteration must consume one budget unit")
            if not _boolean(
                consumption["authenticated"],
                f"{name}.budget_consumption.authenticated",
            ):
                raise ContractError("budget consumption must be authenticated")
            revision += 1
            routing_values = intent_routing or {
                "proposal_ref": None,
                "chain_hash": None,
                "profile_index": None,
                "profile_hash": None,
            }
            iteration_commit = _iteration_commit_identity(
                iteration_commit_ref=commit_ref,
                iteration_commit_event_id=event_id,
                iteration_commit_revision=revision,
                iteration_id=iteration_id,
                attempt_id=attempt_id,
                outcome=iteration_outcome,
                admission_hash=admission["admission_hash"],
                budget_head_ref_before=budget["head_ref"],
                budget_state_hash_before=budget["budget_hash"],
                budget_consumption_ref=consumption_ref,
                budget_revision_after=budget["revision"] + 1,
                proposal_ref=routing_values["proposal_ref"],
                chain_hash=routing_values["chain_hash"],
                profile_index=routing_values["profile_index"],
                profile_hash=routing_values["profile_hash"],
            )
            iteration_commit["iteration_commit_hash"] = _canonical_hash(
                iteration_commit
            )
            budget_record = {
                "iteration_id": iteration_id,
                "attempt_id": attempt_id,
                "iteration_commit_ref": commit_ref,
                "iteration_commit_hash": iteration_commit["iteration_commit_hash"],
                "budget_consumption_ref": consumption_ref,
                "authenticated": True,
            }
            committed_budget = budget["committed"] + [budget_record]
            budget_identity = _budget_identity(
                admission["admission_hash"],
                budget["budget_ref"],
                budget["initial"],
                committed_budget,
                budget["revision"] + 1,
            )
            next_budget_state = {
                **budget_identity,
                "budget_hash": _canonical_hash(budget_identity),
                "authenticated": True,
            }
            budget_head_update = {
                "compare": budget["precondition"],
                "set": {
                    "schema_version": SCHEMA_VERSION,
                    "head_ref": consumption_ref,
                    "admission_ref": admission["admission_ref"],
                    "admission_hash": admission["admission_hash"],
                    "budget_ref": budget["budget_ref"],
                    "consumption_revision": budget["revision"] + 1,
                    "budget_state_hash": next_budget_state["budget_hash"],
                    "authenticated": True,
                },
                "iteration_commit_hash": iteration_commit[
                    "iteration_commit_hash"
                ],
            }
            state = "COMMITTED"
            continue

        next_edges = {
            "SUCCESSOR_SELECTED",
            "LOOP_PAUSED",
            "HANDOFF_COMMITTED",
            "LOOP_DONE",
            "LOOP_TERMINATED",
        }
        if state == "COMMITTED":
            if event_type not in next_edges:
                raise ContractError(
                    "one successor, pause, handoff, or terminal edge must follow commit"
                )
            if event_type == "SUCCESSOR_SELECTED":
                fields = {
                    "type",
                    "event_id",
                    "expected_revision",
                    "iteration_id",
                    "cause_ref",
                    "target_ref",
                    "fence_token",
                }
            elif event_type == "HANDOFF_COMMITTED":
                fields = {
                    "type",
                    "event_id",
                    "expected_revision",
                    "iteration_id",
                    "cause_ref",
                    "packet",
                    "acceptance",
                    "handoff_receipt",
                    "fence_token",
                }
            elif event_type == "LOOP_PAUSED":
                fields = {
                    "type",
                    "event_id",
                    "expected_revision",
                    "iteration_id",
                    "cause_ref",
                    "wake",
                    "fence_token",
                }
            else:
                fields = {
                    "type",
                    "event_id",
                    "expected_revision",
                    "iteration_id",
                    "terminal_receipt",
                    "fence_token",
                }
            require_fields(event, fields, name)
            if event["iteration_id"] != iteration_id:
                raise ContractError("post-commit edge must bind to the committed iteration")
            validate_fence(event, name)
            if (
                intent_dod_scope == "LOOP"
                and verification_complete
                and event_type != "LOOP_DONE"
            ):
                raise ContractError("a passing loop DoD commit must transition to LOOP_DONE")
            if event_type == "LOOP_DONE" and (
                intent_dod_scope != "LOOP" or not verification_complete
            ):
                raise ContractError("LOOP_DONE requires a passing loop-scoped DoD commit")

            if event_type == "SUCCESSOR_SELECTED":
                _nonempty_string(event["cause_ref"], f"{name}.cause_ref")
                _nonempty_string(event["target_ref"], f"{name}.target_ref")
            elif event_type == "HANDOFF_COMMITTED":
                _nonempty_string(event["cause_ref"], f"{name}.cause_ref")
                handoff = _handoff_binding(
                    event["packet"], event["acceptance"], name
                )
                receipt_name = f"{name}.handoff_receipt"
                handoff_receipt = _mapping(event["handoff_receipt"], receipt_name)
                receipt_fields = {
                    "ref",
                    "outcome",
                    "admission_hash",
                    "iteration_commit_hash",
                    "budget_hash",
                    "packet_ref",
                    "packet_revision",
                    "packet_hash",
                    "recipient_id",
                    "acceptance_ref",
                    "authenticated",
                }
                _reject_unknown(handoff_receipt, receipt_fields, receipt_name)
                if set(handoff_receipt) != receipt_fields:
                    raise ContractError(f"{receipt_name} is missing required fields")
                receipt_ref = _nonempty_string(
                    handoff_receipt["ref"], f"{receipt_name}.ref"
                )
                if handoff_receipt["outcome"] != "HANDOFF":
                    raise ContractError("handoff receipt outcome must be HANDOFF")
                if handoff_receipt["admission_hash"] != admission["admission_hash"]:
                    raise ContractError("handoff receipt admission_hash mismatch")
                if iteration_commit is None or next_budget_state is None:
                    raise AssertionError("commit state was not initialized")
                if (
                    handoff_receipt["iteration_commit_hash"]
                    != iteration_commit["iteration_commit_hash"]
                ):
                    raise ContractError("handoff receipt iteration_commit_hash mismatch")
                if handoff_receipt["budget_hash"] != next_budget_state["budget_hash"]:
                    raise ContractError("handoff receipt budget_hash mismatch")
                for field in (
                    "packet_ref",
                    "packet_hash",
                    "recipient_id",
                    "acceptance_ref",
                ):
                    if handoff_receipt[field] != handoff[field]:
                        raise ContractError(f"handoff receipt {field} mismatch")
                receipt_packet_revision = _integer(
                    handoff_receipt["packet_revision"],
                    f"{receipt_name}.packet_revision",
                    1,
                )
                if receipt_packet_revision != handoff["packet_revision"]:
                    raise ContractError("handoff receipt packet_revision mismatch")
                if not _boolean(
                    handoff_receipt["authenticated"],
                    f"{receipt_name}.authenticated",
                ):
                    raise ContractError("handoff receipt must be authenticated")
                terminal_outcome = "HANDOFF"
                terminal_reason = event["cause_ref"]
                terminal_details = {
                    "receipt_ref": receipt_ref,
                    **handoff,
                }
            elif event_type == "LOOP_PAUSED":
                _nonempty_string(event["cause_ref"], f"{name}.cause_ref")
                _wake_contract(event["wake"], admission, f"{name}.wake")
            else:
                receipt_name = f"{name}.terminal_receipt"
                terminal_receipt = _mapping(event["terminal_receipt"], receipt_name)
                common_fields = {
                    "ref",
                    "outcome",
                    "admission_hash",
                    "iteration_commit_hash",
                    "budget_hash",
                    "authenticated",
                }
                terminal_fields = set(common_fields)
                if event_type == "LOOP_DONE":
                    terminal_fields.update(
                        {"dod_revision", "dod_hash", "artifact_revision"}
                    )
                else:
                    terminal_fields.update({"reason", "evidence_ref"})
                _reject_unknown(terminal_receipt, terminal_fields, receipt_name)
                if set(terminal_receipt) != terminal_fields:
                    raise ContractError(f"{receipt_name} is missing required fields")
                _nonempty_string(terminal_receipt["ref"], f"{receipt_name}.ref")
                if terminal_receipt["admission_hash"] != admission["admission_hash"]:
                    raise ContractError("terminal receipt admission_hash mismatch")
                if iteration_commit is None or next_budget_state is None:
                    raise AssertionError("commit state was not initialized")
                if (
                    terminal_receipt["iteration_commit_hash"]
                    != iteration_commit["iteration_commit_hash"]
                ):
                    raise ContractError("terminal receipt iteration_commit_hash mismatch")
                if terminal_receipt["budget_hash"] != next_budget_state["budget_hash"]:
                    raise ContractError("terminal receipt budget_hash mismatch")
                if not _boolean(
                    terminal_receipt["authenticated"],
                    f"{receipt_name}.authenticated",
                ):
                    raise ContractError("terminal receipt must be authenticated")
                if event_type == "LOOP_DONE":
                    if terminal_receipt["outcome"] != "DONE":
                        raise ContractError("LOOP_DONE receipt outcome must be DONE")
                    if result_dod is None:
                        raise AssertionError("verification DoD was not initialized")
                    expected_dod = {
                        "dod_revision": result_dod["revision"],
                        "dod_hash": result_dod["accepted_hash"],
                        "artifact_revision": result_dod["artifact_revision"],
                    }
                    for field, expected in expected_dod.items():
                        if terminal_receipt[field] != expected:
                            raise ContractError(
                                f"terminal receipt {field} does not match verification"
                            )
                    terminal_outcome = "DONE"
                    terminal_details = {"receipt_ref": terminal_receipt["ref"]}
                else:
                    terminal_outcome = _enum(
                        terminal_receipt["outcome"],
                        (
                            "BLOCKED",
                            "CANCELLED",
                            "UNSAFE",
                            "IMPOSSIBLE",
                            "FAILED",
                            "EXHAUSTED",
                            "STOPPED",
                        ),
                        f"{receipt_name}.outcome",
                    )
                    terminal_reason = _nonempty_string(
                        terminal_receipt["reason"],
                        f"{receipt_name}.reason",
                    )
                    if (
                        terminal_outcome == "EXHAUSTED"
                        and next_budget_state["revision"]
                        < next_budget_state["initial_active_iterations"]
                    ):
                        raise ContractError(
                            "EXHAUSTED terminal receipt requires a fully consumed "
                            "active iteration budget"
                        )
                    if terminal_outcome == "STOPPED":
                        _enum(
                            terminal_reason,
                            STOP_REASONS,
                            f"{receipt_name}.reason",
                        )
                    _nonempty_string(
                        terminal_receipt["evidence_ref"],
                        f"{receipt_name}.evidence_ref",
                    )
                    terminal_details = {
                        "receipt_ref": terminal_receipt["ref"],
                        "evidence_ref": terminal_receipt["evidence_ref"],
                    }
            post_commit_events.append(event_type)
            revision += 1
            state = "EDGED"
            continue

        if state == "EDGED":
            if event_type != "CONTEXT_CONDENSED":
                raise ContractError("only optional CONTEXT_CONDENSED may follow the next edge")
            fields = {
                "type",
                "event_id",
                "expected_revision",
                "iteration_id",
                "source_revision",
                "summary_ref",
                "fence_token",
            }
            require_fields(event, fields, name)
            if event["iteration_id"] != iteration_id:
                raise ContractError("condensation must bind to the committed iteration")
            validate_fence(event, name)
            source_revision = _integer(
                event["source_revision"], f"{name}.source_revision", 0
            )
            if source_revision != revision:
                raise ContractError(
                    "condensation source_revision must equal the complete next-edge revision"
                )
            _nonempty_string(event["summary_ref"], f"{name}.summary_ref")
            post_commit_events.append(event_type)
            revision += 1
            state = "CONDENSED"
            continue

        if state == "CONDENSED":
            raise ContractError("no event may follow CONTEXT_CONDENSED")

        raise AssertionError(state)

    if head_delta == 1:
        if next_budget_state is None or budget_head_update is None:
            raise ContractError(
                "advanced host budget head requires its committed journal extension"
            )
        expected_current_head = budget_head_update["set"]
        for field in (
            "head_ref",
            "consumption_revision",
            "budget_state_hash",
        ):
            if current_budget_head[field] != expected_current_head[field]:
                raise ContractError(
                    f"advanced host budget head {field} does not match the journal"
                )
        budget_head_status = "ALREADY_APPLIED"
    elif budget_head_update is not None:
        budget_head_status = "UPDATE_REQUIRED"
    else:
        budget_head_status = "CURRENT"

    next_required = {
        "EMPTY": "INTENT_COMMITTED",
        "INTENT_COMMITTED": "ACTION_OBSERVED",
        "RECONCILE_REQUIRED": "ACTION_RECONCILED",
        "OBSERVED": "VERIFICATION_RECORDED",
        "VERIFIED": "ITERATION_COMMITTED",
        "COMMITTED": "SUCCESSOR_SELECTED|LOOP_PAUSED|HANDOFF_COMMITTED|LOOP_DONE|LOOP_TERMINATED",
        "EDGED": "CONTEXT_CONDENSED_OR_END",
        "CONDENSED": "END",
    }[state]
    if state == "COMMITTED" and intent_dod_scope == "LOOP" and verification_complete:
        next_required = "LOOP_DONE"
    return {
        "schema_version": SCHEMA_VERSION,
        "state_class": state_class,
        "effect_state": state,
        "current_revision": revision,
        "iteration_id": iteration_id,
        "attempt_id": attempt_id,
        "operation_id": operation_id,
        "idempotency_key": idempotency_key,
        "outcome": outcome,
        "observation_event_id": observation_event_id,
        "verification_event_id": verification_event_id,
        "verification_complete": verification_complete,
        "iteration_outcome": iteration_outcome,
        "iteration_commit": iteration_commit,
        "budget_state": next_budget_state or dict(data["budget_state"]),
        "budget_precondition": budget["precondition"],
        "budget_head_update": budget_head_update,
        "budget_head_status": budget_head_status,
        "admission_hash": admission["admission_hash"],
        "terminal_outcome": terminal_outcome,
        "terminal_reason": terminal_reason,
        "terminal_details": terminal_details,
        "next_required_event": next_required,
        "post_commit_events": post_commit_events,
        "requires_committed_revision": revision,
    }


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ContractError(f"{name} must be a list of canonical non-empty strings")
    for index, item in enumerate(value):
        _nonempty_string(item, f"{name}[{index}]")
    if value != sorted(set(value)):
        raise ContractError(f"{name} must be a sorted set")
    return list(value)


def _validate_chain(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ContractError("chain must be a non-empty list")
    if len(value) > 8:
        raise ContractError("chain may contain at most eight profiles")
    chain: list[dict[str, Any]] = []
    agents: set[str] = set()
    for index, raw_profile in enumerate(value):
        profile = _mapping(raw_profile, f"chain[{index}]")
        _reject_unknown(
            profile,
            {"agent", "skills", "tools", "mcp_servers"},
            f"chain[{index}]",
        )
        agent = _nonempty_string(profile.get("agent"), f"chain[{index}].agent")
        if agent != agent.casefold():
            raise ContractError(f"chain[{index}].agent must be normalized lowercase")
        if agent in agents:
            raise ContractError("agents must be unique within a routing chain")
        agents.add(agent)
        normalized = {
            "agent": agent,
            "skills": _string_list(profile.get("skills", []), f"chain[{index}].skills"),
            "tools": _string_list(profile.get("tools", []), f"chain[{index}].tools"),
            "mcp_servers": _string_list(
                profile.get("mcp_servers", []), f"chain[{index}].mcp_servers"
            ),
        }
        capabilities = (
            normalized["skills"] + normalized["tools"] + normalized["mcp_servers"]
        )
        if any(len(normalized[field]) > 16 for field in ("skills", "tools", "mcp_servers")):
            raise ContractError("routing capability class may contain at most sixteen identifiers")
        if len(capabilities) > 24:
            raise ContractError("routing profile may contain at most twenty-four capabilities")
        if not capabilities:
            raise ContractError("each routing profile needs at least one capability")
        if any(item != item.casefold() for item in capabilities):
            raise ContractError("routing capability identifiers must be lowercase")
        chain.append(normalized)
    return chain


def _validate_registry(
    value: Any,
    name: str = "registry",
    *,
    require_skill_metadata: bool = True,
) -> dict[str, dict[str, Any]]:
    raw_registry = _mapping(value, name)
    if not raw_registry:
        raise ContractError(f"{name} must contain at least one agent")
    registry: dict[str, dict[str, Any]] = {}
    global_metadata: dict[str, dict[str, Any]] = {}
    for agent, raw_capabilities in sorted(raw_registry.items()):
        normalized_agent = _nonempty_string(agent, f"{name} agent")
        if normalized_agent != normalized_agent.casefold():
            raise ContractError(f"{name} agent identifiers must be lowercase")
        capabilities = _mapping(raw_capabilities, f"{name}.{agent}")
        allowed = {"skills", "tools", "mcp_servers"}
        if require_skill_metadata:
            allowed.add("skill_metadata")
        _reject_unknown(capabilities, allowed, f"{name}.{agent}")
        normalized: dict[str, Any] = {
            key: _string_list(capabilities.get(key, []), f"{name}.{agent}.{key}")
            for key in ("skills", "tools", "mcp_servers")
        }
        if require_skill_metadata:
            raw_metadata = _mapping(
                capabilities.get("skill_metadata"),
                f"{name}.{agent}.skill_metadata",
            )
            if set(raw_metadata) != set(normalized["skills"]):
                raise ContractError(
                    f"{name}.{agent}.skill_metadata must exactly cover registered skills"
                )
            metadata: dict[str, dict[str, Any]] = {}
            for skill, raw_record in sorted(raw_metadata.items()):
                record_name = f"{name}.{agent}.skill_metadata.{skill}"
                record = _mapping(raw_record, record_name)
                fields = {"role", "incompatible_with"}
                _reject_unknown(record, fields, record_name)
                if set(record) != fields:
                    raise ContractError(f"{record_name} is missing required fields")
                role = _enum(record["role"], SKILL_ROLES, f"{record_name}.role")
                incompatible = _string_list(
                    record["incompatible_with"],
                    f"{record_name}.incompatible_with",
                )
                if skill in incompatible:
                    raise ContractError("a skill cannot be incompatible with itself")
                fixed_role = FIXED_SKILL_ROLES.get(skill)
                if fixed_role is not None and role != fixed_role:
                    raise ContractError(f"{skill} has fixed role {fixed_role}")
                required_incompatible = FIXED_INCOMPATIBILITIES.get(skill, set())
                if not required_incompatible.issubset(incompatible):
                    raise ContractError(
                        f"{skill} metadata omits a fixed incompatibility"
                    )
                normalized_record = {
                    "role": role,
                    "incompatible_with": incompatible,
                }
                previous = global_metadata.get(skill)
                if previous is not None and previous != normalized_record:
                    raise ContractError(
                        f"{name} contains conflicting metadata for skill {skill}"
                    )
                global_metadata[skill] = normalized_record
                metadata[skill] = normalized_record
            normalized["skill_metadata"] = metadata
        registry[agent] = normalized
    return registry


def _missing_profile_capabilities(
    profile: Mapping[str, Any],
    registry: Mapping[str, dict[str, Any]],
    authority: Mapping[str, dict[str, Any]],
) -> list[str]:
    missing: list[str] = []
    agent_capabilities = registry.get(profile["agent"])
    if agent_capabilities is None:
        missing.append(f"registry.agent:{profile['agent']}")
    authorized_capabilities = authority.get(profile["agent"])
    if authorized_capabilities is None:
        missing.append(f"authority.agent:{profile['agent']}")
    for field in ("skills", "tools", "mcp_servers"):
        available = set(agent_capabilities[field]) if agent_capabilities else set()
        authorized = (
            set(authorized_capabilities[field]) if authorized_capabilities else set()
        )
        missing.extend(
            f"registry.{field}:{item}" for item in profile[field] if item not in available
        )
        missing.extend(
            f"authority.{field}:{item}"
            for item in profile[field]
            if item not in authorized
        )
    return missing


def _profile_compatibility_issues(
    profile: Mapping[str, Any],
    registry: Mapping[str, dict[str, Any]],
) -> list[str]:
    agent = registry.get(profile["agent"])
    if agent is None:
        return []
    metadata = agent["skill_metadata"]
    selected = set(profile["skills"])
    issues: list[str] = []
    primary = [
        skill
        for skill in profile["skills"]
        if skill in metadata and metadata[skill]["role"] == "primary"
    ]
    if len(primary) > 1:
        issues.append("compatibility.multiple_primary:" + ",".join(primary))
    for skill in profile["skills"]:
        if skill not in metadata:
            continue
        role = metadata[skill]["role"]
        if role in {"controller", "middleware"}:
            issues.append(f"compatibility.non_specialty:{skill}:{role}")
        conflicts = sorted(selected & set(metadata[skill]["incompatible_with"]))
        issues.extend(
            "compatibility.incompatible:" + ":".join(sorted((skill, conflict)))
            for conflict in conflicts
        )
        if "nerd-loop" in metadata[skill]["incompatible_with"]:
            issues.append(f"compatibility.controller_incompatible:{skill}:nerd-loop")
    return sorted(set(issues))


def _cursor(
    value: Any,
    chain_hash: str,
    proposal_ref: str,
    chain_size: int,
    admission_hash: str,
) -> dict[str, Any]:
    cursor = _mapping(value, "cursor")
    required = {
        "schema_version",
        "admission_hash",
        "proposal_ref",
        "chain_hash",
        "registry_hash",
        "authority_hash",
        "profile_index",
        "chain_size",
        "status",
        "active_iteration_id",
        "revision",
        "budget_head_ref",
        "budget_base_revision",
        "budget_revision",
        "budget_state_hash",
        "last_event",
    }
    _reject_unknown(cursor, required, "cursor")
    if set(cursor) != required:
        raise ContractError("cursor is missing required fields")
    if cursor["schema_version"] != SCHEMA_VERSION:
        raise ContractError("cursor schema_version mismatch")
    if cursor["admission_hash"] != admission_hash:
        raise ContractError("cursor admission_hash mismatch")
    if cursor["proposal_ref"] != proposal_ref:
        raise ContractError("cursor proposal_ref mismatch")
    if cursor["chain_hash"] != chain_hash:
        raise ContractError("cursor chain_hash mismatch")
    _nonempty_string(cursor["registry_hash"], "cursor.registry_hash")
    _nonempty_string(cursor["authority_hash"], "cursor.authority_hash")
    cursor_chain_size = _integer(cursor["chain_size"], "cursor.chain_size", 1)
    if cursor_chain_size != chain_size:
        raise ContractError("cursor chain_size mismatch")
    status = _enum(cursor["status"], ROUTING_STATUSES, "cursor.status")
    profile_index = _integer(cursor["profile_index"], "cursor.profile_index", 0)
    revision = _integer(cursor["revision"], "cursor.revision", 0)
    _nonempty_string(cursor["budget_head_ref"], "cursor.budget_head_ref")
    budget_base_revision = _integer(
        cursor["budget_base_revision"], "cursor.budget_base_revision", 0
    )
    budget_revision = _integer(
        cursor["budget_revision"], "cursor.budget_revision", 0
    )
    if budget_revision < budget_base_revision:
        raise ContractError("cursor budget revision predates its routing bind")
    _nonempty_string(cursor["budget_state_hash"], "cursor.budget_state_hash")
    active_iteration_id = cursor["active_iteration_id"]
    if active_iteration_id is not None:
        _nonempty_string(active_iteration_id, "cursor.active_iteration_id")
    last_event = _enum(
        cursor["last_event"],
        (
            "ROUTING_BOUND",
            "ROUTING_PROFILE_ACTIVATED",
            "ROUTING_PROFILE_REPEATED",
            "ROUTING_PROFILE_SATISFIED",
            "ROUTING_COMPLETED",
            "ROUTING_BLOCKED",
        ),
        "cursor.last_event",
    )
    allowed_events = {
        "PENDING": {"ROUTING_BOUND", "ROUTING_PROFILE_SATISFIED"},
        "ACTIVE": {"ROUTING_PROFILE_ACTIVATED", "ROUTING_PROFILE_REPEATED"},
        "COMPLETE": {"ROUTING_COMPLETED"},
        "BLOCKED": {"ROUTING_BLOCKED"},
    }
    if last_event not in allowed_events[status]:
        raise ContractError("cursor status and last_event are incoherent")
    if status == "ACTIVE" and active_iteration_id is None:
        raise ContractError("ACTIVE routing cursor requires active_iteration_id")
    if status != "ACTIVE" and active_iteration_id is not None:
        raise ContractError("only an ACTIVE routing cursor may hold active_iteration_id")
    if status == "COMPLETE":
        if profile_index != chain_size:
            raise ContractError("COMPLETE routing cursor must point past the final profile")
    elif profile_index >= chain_size:
        raise ContractError("non-complete routing cursor points beyond the routing chain")
    if budget_revision - budget_base_revision < profile_index:
        raise ContractError(
            "routing profile progress exceeds committed budget consumption since bind"
        )

    # These lower bounds and exact initial state describe every cursor reachable
    # through bind/activate/repeat/satisfy/block. Recovery must not turn a
    # syntactically plausible but impossible cursor into authority to skip work.
    if last_event == "ROUTING_BOUND" and not (
        status == "PENDING" and profile_index == 0 and revision == 0
    ):
        raise ContractError("ROUTING_BOUND cursor is not a reachable initial state")
    if last_event == "ROUTING_PROFILE_SATISFIED" and (
        profile_index == 0 or revision < 2 * profile_index
    ):
        raise ContractError("satisfied routing cursor has an unreachable revision")
    if last_event == "ROUTING_PROFILE_ACTIVATED" and revision < 2 * profile_index + 1:
        raise ContractError("activated routing cursor has an unreachable revision")
    if (
        last_event == "ROUTING_PROFILE_ACTIVATED"
        and profile_index == 0
        and revision != 1
    ):
        raise ContractError("first activated routing cursor must be at revision one")
    if last_event == "ROUTING_PROFILE_REPEATED" and revision < 2 * profile_index + 2:
        raise ContractError("repeated routing cursor has an unreachable revision")
    if last_event == "ROUTING_COMPLETED" and revision < 2 * chain_size:
        raise ContractError("completed routing cursor has an unreachable revision")
    if last_event == "ROUTING_BLOCKED":
        if revision == 0 and profile_index != 0:
            raise ContractError("initial blocked routing cursor must be at index zero")
        if revision > 0 and revision < 2 * profile_index + 1:
            raise ContractError("blocked routing cursor has an unreachable revision")
    return cursor


def _routing_result(cursor: dict[str, Any], action: str, **extra: Any) -> dict[str, Any]:
    result = {
        "schema_version": SCHEMA_VERSION,
        "action": action,
        "cursor": cursor,
    }
    result.update(extra)
    return result


def routing_transition(request: Mapping[str, Any]) -> dict[str, Any]:
    """Bind, advance, repeat, block, or recover one atomic routing cursor."""

    data = _mapping(request, "routing request")
    allowed = {
        "schema_version",
        "admission",
        "budget_state",
        "host_budget_head",
        "operation",
        "proposal_ref",
        "chain",
        "registry",
        "authority",
        "cursor",
        "expected_revision",
        "iteration_id",
        "completion_receipt",
        "outcome_receipt",
        "ambiguous_effect_ref",
        "reason",
    }
    _reject_unknown(data, allowed, "routing request")
    _require_schema(data, "routing request")
    admission = _admission_contract(data.get("admission"))
    if admission["profile"] == "D0":
        raise ContractError("D0 admission cannot activate a remembered routing chain")
    budget = _budget_contract(
        data.get("budget_state"), admission, data.get("host_budget_head")
    )
    def route_result(
        cursor_value: dict[str, Any], action: str, **extra: Any
    ) -> dict[str, Any]:
        return _routing_result(
            cursor_value,
            action,
            budget_precondition=budget["precondition"],
            **extra,
        )

    operation = _enum(
        data.get("operation"),
        ("bind", "activate", "repeat", "satisfy", "block", "recover"),
        "operation",
    )
    proposal_ref = _nonempty_string(data.get("proposal_ref"), "proposal_ref")
    chain = _validate_chain(data.get("chain"))
    registry = _validate_registry(data.get("registry"))
    authority = _validate_registry(
        data.get("authority"),
        "authority",
        require_skill_metadata=False,
    )
    for agent, authorized in authority.items():
        if agent not in registry:
            raise ContractError(f"authority agent is absent from registry: {agent}")
        for field in ("skills", "tools", "mcp_servers"):
            if not set(authorized[field]).issubset(registry[agent][field]):
                raise ContractError(
                    f"authority.{agent}.{field} must be a subset of the registry"
                )
    chain_hash = _canonical_hash(chain)
    registry_hash = _canonical_hash(registry)
    authority_hash = _canonical_hash(authority)

    def missing_profiles() -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for index, profile in enumerate(chain):
            missing = _missing_profile_capabilities(profile, registry, authority)
            missing.extend(_profile_compatibility_issues(profile, registry))
            if missing:
                result.append(
                    {"profile_index": index, "agent": profile["agent"], "missing": missing}
                )
        return result

    def receipt(
        value: Any,
        name: str,
        expected_iteration_id: str,
        expected_index: int,
        *,
        completion: bool,
        expected_budget_head_ref_before: str,
        expected_budget_state_hash_before: str,
    ) -> dict[str, Any]:
        record = _mapping(value, name)
        fields = {
            "ref",
            "admission_hash",
            "proposal_ref",
            "iteration_id",
            "attempt_id",
            "chain_hash",
            "profile_index",
            "profile_hash",
            "outcome",
            "iteration_commit_ref",
            "iteration_commit_event_id",
            "iteration_commit_revision",
            "iteration_commit_hash",
            "budget_head_ref_before",
            "budget_state_hash_before",
            "budget_consumption_ref",
            "budget_revision_after",
            "authenticated",
        }
        if completion:
            fields.add("guard_ref")
        _reject_unknown(record, fields, name)
        if set(record) != fields:
            raise ContractError(f"{name} is missing required fields")
        _nonempty_string(record["ref"], f"{name}.ref")
        if record["admission_hash"] != admission["admission_hash"]:
            raise ContractError(f"{name}.admission_hash mismatch")
        if record["proposal_ref"] != proposal_ref:
            raise ContractError(f"{name}.proposal_ref mismatch")
        if record["iteration_id"] != expected_iteration_id:
            raise ContractError(f"{name}.iteration_id does not match the active profile")
        attempt_id = _nonempty_string(record["attempt_id"], f"{name}.attempt_id")
        if record["chain_hash"] != chain_hash:
            raise ContractError(f"{name}.chain_hash mismatch")
        profile_index = _integer(record["profile_index"], f"{name}.profile_index", 0)
        if profile_index != expected_index:
            raise ContractError(f"{name}.profile_index mismatch")
        if record["profile_hash"] != _canonical_hash(chain[expected_index]):
            raise ContractError(f"{name}.profile_hash mismatch")
        commit_ref = _nonempty_string(
            record["iteration_commit_ref"], f"{name}.iteration_commit_ref"
        )
        commit_event_id = _nonempty_string(
            record["iteration_commit_event_id"],
            f"{name}.iteration_commit_event_id",
        )
        commit_revision = _integer(
            record["iteration_commit_revision"],
            f"{name}.iteration_commit_revision",
            1,
        )
        commit_hash = _nonempty_string(
            record["iteration_commit_hash"], f"{name}.iteration_commit_hash"
        )
        budget_head_ref_before = _nonempty_string(
            record["budget_head_ref_before"],
            f"{name}.budget_head_ref_before",
        )
        budget_state_hash_before = _nonempty_string(
            record["budget_state_hash_before"],
            f"{name}.budget_state_hash_before",
        )
        if budget_head_ref_before != expected_budget_head_ref_before:
            raise ContractError(f"{name}.budget_head_ref_before mismatch")
        if budget_state_hash_before != expected_budget_state_hash_before:
            raise ContractError(f"{name}.budget_state_hash_before mismatch")
        budget_consumption_ref = _nonempty_string(
            record["budget_consumption_ref"], f"{name}.budget_consumption_ref"
        )
        budget_revision_after = _integer(
            record["budget_revision_after"], f"{name}.budget_revision_after", 1
        )
        if budget_revision_after != budget["revision"]:
            raise ContractError(f"{name}.budget_revision_after mismatch")
        commit_identity = _iteration_commit_identity(
            iteration_commit_ref=commit_ref,
            iteration_commit_event_id=commit_event_id,
            iteration_commit_revision=commit_revision,
            iteration_id=record["iteration_id"],
            attempt_id=attempt_id,
            outcome=record["outcome"],
            admission_hash=record["admission_hash"],
            budget_head_ref_before=budget_head_ref_before,
            budget_state_hash_before=budget_state_hash_before,
            budget_consumption_ref=budget_consumption_ref,
            budget_revision_after=budget_revision_after,
            proposal_ref=record["proposal_ref"],
            chain_hash=record["chain_hash"],
            profile_index=profile_index,
            profile_hash=record["profile_hash"],
        )
        if commit_hash != _canonical_hash(commit_identity):
            raise ContractError(f"{name}.iteration_commit_hash mismatch")
        committed = budget["committed"][-1] if budget["committed"] else None
        if committed is None or not (
            committed["iteration_id"] == record["iteration_id"]
            and committed["attempt_id"] == attempt_id
            and committed["iteration_commit_ref"] == commit_ref
            and committed["iteration_commit_hash"] == commit_hash
            and committed["budget_consumption_ref"] == budget_consumption_ref
        ):
            raise ContractError(
                f"{name} is not bound to its authenticated budget consumption record"
            )
        if not _boolean(record["authenticated"], f"{name}.authenticated"):
            raise ContractError(f"{name} must be authenticated")
        if completion:
            if record["outcome"] != "VERIFIED":
                raise ContractError("completion_receipt outcome must be VERIFIED")
            _nonempty_string(record["guard_ref"], "completion_receipt.guard_ref")
        else:
            _enum(
                record["outcome"],
                ("DISPROVED", "BLOCKED", "INCONCLUSIVE", "FAILED"),
                "outcome_receipt.outcome",
            )
        return record

    if operation == "bind":
        if data.get("cursor") is not None:
            raise ContractError("bind must not receive an existing cursor")
        all_missing = missing_profiles()
        if budget["remaining"] < len(chain):
            all_missing.append(
                {
                    "profile_index": 0,
                    "agent": "loop-controller",
                    "missing": ["budget.remaining_below_unsatisfied_profiles"],
                }
            )
        status = "BLOCKED" if all_missing else "PENDING"
        cursor = {
            "schema_version": SCHEMA_VERSION,
            "admission_hash": admission["admission_hash"],
            "proposal_ref": proposal_ref,
            "chain_hash": chain_hash,
            "registry_hash": registry_hash,
            "authority_hash": authority_hash,
            "profile_index": 0,
            "chain_size": len(chain),
            "status": status,
            "active_iteration_id": None,
            "revision": 0,
            "budget_head_ref": budget["head_ref"],
            "budget_base_revision": budget["revision"],
            "budget_revision": budget["revision"],
            "budget_state_hash": budget["budget_hash"],
            "last_event": "ROUTING_BLOCKED" if all_missing else "ROUTING_BOUND",
        }
        action = "BLOCKED" if all_missing else "BOUND"
        return route_result(cursor, action, missing_profiles=all_missing)

    cursor = _cursor(
        data.get("cursor"),
        chain_hash,
        proposal_ref,
        len(chain),
        admission["admission_hash"],
    )
    expected_revision = _integer(
        data.get("expected_revision"), "expected_revision", 0
    )
    if expected_revision != cursor["revision"]:
        raise ContractError("routing expected_revision conflict")
    current = copy.deepcopy(cursor)

    cursor_budget_revision = current["budget_revision"]
    if current["status"] == "ACTIVE":
        allowed_budget_revisions = {cursor_budget_revision, cursor_budget_revision + 1}
    else:
        allowed_budget_revisions = {cursor_budget_revision}
    if budget["revision"] not in allowed_budget_revisions:
        raise ContractError("routing budget_state is stale or skips a revision")
    if budget["revision"] == cursor_budget_revision:
        if budget["head_ref"] != current["budget_head_ref"]:
            raise ContractError("routing budget head_ref mismatch")
        if budget["budget_hash"] != current["budget_state_hash"]:
            raise ContractError("routing budget state hash mismatch")
    else:
        if not budget["committed"]:
            raise ContractError("routing budget advance lacks a committed record")
        if budget["committed"][-1]["iteration_id"] != current["active_iteration_id"]:
            raise ContractError("routing budget head belongs to another iteration")
        prefix_records = budget["committed"][:-1]
        prefix_identity = _budget_identity(
            admission["admission_hash"],
            budget["budget_ref"],
            budget["initial"],
            prefix_records,
            cursor_budget_revision,
        )
        if _canonical_hash(prefix_identity) != current["budget_state_hash"]:
            raise ContractError("routing budget history does not extend its cursor")

    if current["status"] == "COMPLETE":
        if operation == "recover":
            return route_result(current, "ROUTING_COMPLETE")
        raise ContractError("routing cursor is terminal: COMPLETE")

    drift: list[str] = []
    if current["registry_hash"] != registry_hash:
        drift.append("registry_hash_mismatch")
    if current["authority_hash"] != authority_hash:
        drift.append("authority_hash_mismatch")
    if drift:
        current["status"] = "BLOCKED"
        current["active_iteration_id"] = None
        current["revision"] += 1
        current["budget_head_ref"] = budget["head_ref"]
        current["budget_revision"] = budget["revision"]
        current["budget_state_hash"] = budget["budget_hash"]
        current["last_event"] = "ROUTING_BLOCKED"
        return route_result(
            current,
            "BLOCKED",
            reason=",".join(drift),
            observed_registry_hash=registry_hash,
            observed_authority_hash=authority_hash,
        )

    all_missing = missing_profiles()
    if all_missing and current["status"] != "COMPLETE":
        current["status"] = "BLOCKED"
        current["active_iteration_id"] = None
        current["revision"] += 1
        current["budget_head_ref"] = budget["head_ref"]
        current["budget_revision"] = budget["revision"]
        current["budget_state_hash"] = budget["budget_hash"]
        current["last_event"] = "ROUTING_BLOCKED"
        return route_result(
            current, "BLOCKED", reason="routing_component_unavailable", missing_profiles=all_missing
        )

    if operation == "recover":
        ambiguous_effect_ref = _optional_string(
            data.get("ambiguous_effect_ref"), "ambiguous_effect_ref"
        )
        if ambiguous_effect_ref is not None:
            return route_result(
                current, "RECONCILE_EFFECT", evidence_ref=ambiguous_effect_ref
            )
        if (
            current["status"] == "ACTIVE"
            and budget["revision"] == current["budget_revision"] + 1
        ):
            return route_result(current, "AWAIT_COMMITTED_OUTCOME_RECEIPT")
        action = {
            "PENDING": "ACTIVATE_SAME_INDEX",
            "ACTIVE": "RESUME_SAME_INDEX",
            "COMPLETE": "ROUTING_COMPLETE",
            "BLOCKED": "ROUTING_BLOCKED",
        }[current["status"]]
        return route_result(current, action)

    if current["status"] in {"COMPLETE", "BLOCKED"}:
        raise ContractError(f"routing cursor is terminal: {current['status']}")

    index = current["profile_index"]

    if operation == "activate":
        if current["status"] != "PENDING":
            raise ContractError("activate requires a PENDING cursor")
        if budget["revision"] != current["budget_revision"]:
            raise ContractError("activate requires the cursor's exact budget revision")
        if budget["remaining"] == 0:
            raise ContractError("activate cannot exceed the admitted iteration budget")
        iteration_id = _nonempty_string(data.get("iteration_id"), "iteration_id")
        if iteration_id in budget["committed_iteration_ids"]:
            raise ContractError("activate cannot reuse a committed iteration_id")
        current["status"] = "ACTIVE"
        current["active_iteration_id"] = iteration_id
        current["revision"] += 1
        current["last_event"] = "ROUTING_PROFILE_ACTIVATED"
        return route_result(current, "ACTIVATED", profile=chain[index])

    if operation == "repeat":
        if current["status"] != "ACTIVE":
            raise ContractError("repeat requires an ACTIVE cursor")
        receipt(
            data.get("outcome_receipt"),
            "outcome_receipt",
            current["active_iteration_id"],
            index,
            completion=False,
            expected_budget_head_ref_before=current["budget_head_ref"],
            expected_budget_state_hash_before=current["budget_state_hash"],
        )
        if budget["revision"] != current["budget_revision"] + 1:
            raise ContractError("repeat requires one newly committed budget unit")
        if budget["remaining"] == 0:
            raise ContractError("repeat cannot exceed the admitted iteration budget")
        iteration_id = _nonempty_string(data.get("iteration_id"), "iteration_id")
        if iteration_id == current["active_iteration_id"]:
            raise ContractError("repeat requires a new iteration_id")
        if iteration_id in budget["committed_iteration_ids"]:
            raise ContractError("repeat cannot reuse a committed iteration_id")
        current["active_iteration_id"] = iteration_id
        current["revision"] += 1
        current["budget_head_ref"] = budget["head_ref"]
        current["budget_revision"] = budget["revision"]
        current["budget_state_hash"] = budget["budget_hash"]
        current["last_event"] = "ROUTING_PROFILE_REPEATED"
        return route_result(current, "REPEATED_SAME_INDEX", profile=chain[index])

    if operation == "satisfy":
        if current["status"] != "ACTIVE":
            raise ContractError("satisfy requires an ACTIVE cursor")
        iteration_id = _nonempty_string(data.get("iteration_id"), "iteration_id")
        if iteration_id != current["active_iteration_id"]:
            raise ContractError("satisfy iteration_id must match the active profile")
        completion = receipt(
            data.get("completion_receipt"),
            "completion_receipt",
            iteration_id,
            index,
            completion=True,
            expected_budget_head_ref_before=current["budget_head_ref"],
            expected_budget_state_hash_before=current["budget_state_hash"],
        )
        if budget["revision"] != current["budget_revision"] + 1:
            raise ContractError("satisfy requires one newly committed budget unit")
        current["profile_index"] += 1
        current["active_iteration_id"] = None
        current["revision"] += 1
        current["budget_head_ref"] = budget["head_ref"]
        current["budget_revision"] = budget["revision"]
        current["budget_state_hash"] = budget["budget_hash"]
        if current["profile_index"] == len(chain):
            current["status"] = "COMPLETE"
            current["last_event"] = "ROUTING_COMPLETED"
            return route_result(
                current, "ROUTING_COMPLETE", completion_ref=completion["ref"]
            )
        current["status"] = "PENDING"
        current["last_event"] = "ROUTING_PROFILE_SATISFIED"
        return route_result(
            current, "ADVANCED_ONE_INDEX", completion_ref=completion["ref"]
        )

    if operation == "block":
        reason = _nonempty_string(data.get("reason"), "reason")
        current["status"] = "BLOCKED"
        current["active_iteration_id"] = None
        current["revision"] += 1
        current["budget_head_ref"] = budget["head_ref"]
        current["budget_revision"] = budget["revision"]
        current["budget_state_hash"] = budget["budget_hash"]
        current["last_event"] = "ROUTING_BLOCKED"
        return route_result(current, "BLOCKED", reason=reason)

    raise AssertionError(operation)


COMMANDS = {
    "route": select_route,
    "decide": decide_transition,
    "effect": reduce_effect_events,
    "routing": routing_transition,
}


def _read_input(value: str) -> Any:
    raw = sys.stdin.read() if value == "-" else value
    if len(raw.encode("utf-8")) > 1024 * 1024:
        raise ContractError("input exceeds the 1 MiB limit")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise ContractError(f"input is not valid JSON: {error.msg}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=tuple(COMMANDS))
    parser.add_argument(
        "--input",
        default="-",
        help="Complete JSON object, or - to read one object from stdin",
    )
    args = parser.parse_args(argv)
    try:
        result = COMMANDS[args.command](_read_input(args.input))
    except ContractError as error:
        print(
            json.dumps(
                {"error": {"type": "contract_error", "message": str(error)}},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
