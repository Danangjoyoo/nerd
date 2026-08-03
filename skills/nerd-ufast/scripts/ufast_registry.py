#!/usr/bin/env python3
"""Operation registry and intent router for Nerd UFast."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


Handler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class OperationRoute:
    name: str
    intent: str
    backend: str
    definition: dict[str, Any]
    handler: Handler


class OperationRegistry:
    def __init__(self) -> None:
        self._by_name: dict[str, OperationRoute] = {}
        self._by_intent: dict[str, OperationRoute] = {}

    def register(self, route: OperationRoute) -> None:
        if route.name in self._by_name or route.intent in self._by_intent:
            raise ValueError(f"Duplicate UFast operation route: {route.name}")
        self._by_name[route.name] = route
        self._by_intent[route.intent] = route

    def tool_definitions(self) -> list[dict[str, Any]]:
        return [route.definition for route in self._by_name.values()]

    def route_for_intent(self, intent: str) -> OperationRoute | None:
        return self._by_intent.get(intent)

    def dispatch(self, name: object, arguments: object) -> dict[str, Any]:
        route = self._by_name.get(name) if isinstance(name, str) else None
        if route is None:
            return {
                "status": "rejected",
                "runtime_version": "0.3.0",
                "operation_ms": 0,
                "reason": f"Unknown UFast operation: {name!r}",
            }
        if not isinstance(arguments, dict):
            return {
                "status": "rejected",
                "runtime_version": "0.3.0",
                "operation_ms": 0,
                "route": route.intent,
                "backend": route.backend,
                "reason": "Tool arguments must be an object",
            }
        try:
            result = route.handler(arguments)
        except Exception as error:  # transport boundary must return a stable envelope
            result = {
                "status": "failed",
                "runtime_version": "0.3.0",
                "operation_ms": 0,
                "reason": f"Operation backend failed: {error}",
            }
        return {
            **result,
            "route": route.intent,
            "backend": result.get("backend", route.backend),
        }


def _definition(
    name: str,
    title: str,
    description: str,
    schema: dict[str, Any],
    *,
    read_only: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "title": title,
        "description": description,
        "inputSchema": schema,
        "annotations": {
            "readOnlyHint": read_only,
            "destructiveHint": False,
            "idempotentHint": read_only,
            "openWorldHint": False,
        },
    }


def phase_one_registry(
    *,
    project_index: Handler,
    fast_search: Handler,
    safe_edit: Handler,
    test_runner: Handler,
) -> OperationRegistry:
    """Build the four-route Phase 1 registry; later adapters register here."""

    registry = OperationRegistry()
    registry.register(
        OperationRoute(
            "ufast_project_index",
            "project_index",
            "memory_project_map",
            _definition(
                "ufast_project_index",
                "Build or reuse the project index",
                "Return a bounded generic project map with hashes and cache state, without file bodies.",
                {
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "boolean", "default": False},
                        "max_entries": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "default": 200,
                        },
                    },
                    "additionalProperties": False,
                },
                read_only=True,
            ),
            project_index,
        )
    )
    registry.register(
        OperationRoute(
            "ufast_fast_search",
            "search_project",
            "memory_project_map",
            _definition(
                "ufast_fast_search",
                "Search indexed project text",
                "Search the reusable project index and return bounded context with exact file hashes.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "minLength": 1, "maxLength": 500},
                        "queries": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 10,
                            "uniqueItems": True,
                            "items": {"type": "string", "minLength": 1, "maxLength": 500},
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["literal", "regex"],
                            "default": "literal",
                        },
                        "case_sensitive": {"type": "boolean", "default": False},
                        "paths": {
                            "type": "array",
                            "maxItems": 200,
                            "items": {"type": "string"},
                        },
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 20,
                        },
                        "context_lines": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 5,
                            "default": 2,
                        },
                    },
                    "oneOf": [
                        {"required": ["query"]},
                        {"required": ["queries"]},
                    ],
                    "additionalProperties": False,
                },
                read_only=True,
            ),
            fast_search,
        )
    )
    registry.register(
        OperationRoute(
            "ufast_safe_edit",
            "safe_edit",
            "workspace_transaction",
            _definition(
                "ufast_safe_edit",
                "Apply an atomic verified workspace edit",
                "Apply exact-text replacements or complete UTF-8 contents against hashes and roll back failed verification.",
                {
                    "type": "object",
                    "properties": {
                        "changes": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 50,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "sha256": {
                                        "type": "string",
                                        "pattern": "^[0-9a-f]{64}$",
                                    },
                                    "content": {"type": "string"},
                                    "old_text": {"type": "string", "minLength": 1},
                                    "new_text": {"type": "string"},
                                    "expected_occurrences": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "default": 1,
                                    },
                                },
                                "required": ["path", "sha256"],
                                "oneOf": [
                                    {"required": ["content"]},
                                    {"required": ["old_text", "new_text"]},
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "verify": {"type": "boolean", "default": True},
                        "checks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "uniqueItems": True,
                        },
                    },
                    "required": ["changes"],
                    "additionalProperties": False,
                },
                read_only=False,
            ),
            safe_edit,
        )
    )
    registry.register(
        OperationRoute(
            "ufast_test_runner",
            "test_runner",
            "verification_registry",
            _definition(
                "ufast_test_runner",
                "Run detected repository verification",
                "Detect and execute allowlisted repository checks; arbitrary command input is not accepted.",
                {
                    "type": "object",
                    "properties": {
                        "changed_paths": {
                            "type": "array",
                            "maxItems": 200,
                            "items": {"type": "string"},
                        },
                        "checks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "uniqueItems": True,
                        },
                    },
                    "additionalProperties": False,
                },
                read_only=False,
            ),
            test_runner,
        )
    )
    return registry
