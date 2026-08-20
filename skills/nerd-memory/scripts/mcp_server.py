#!/usr/bin/env python3
"""Dependency-free stdio MCP server for the Nerd Memory runtime.

Exposes the composite memory workflows over one warm process so a caller spends
one round trip where the CLI needs several. Every tool is a thin adapter over
`MemoryStore`; the engine owns all validation, policy, and gating.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import memory as engine  # noqa: E402


SERVER_NAME = "nerd-memory-tools"
SERVER_VERSION = "1.1.0"
PROTOCOL_VERSION = "2025-06-18"

# Either message means this process can no longer write safely: the store moved
# underneath a live handle, or this runtime copy is older than the store it
# opened. SKILL.md forbids retrying through such a handle.
SCHEMA_RESTART_MESSAGES = engine.SCHEMA_RESTART_MESSAGES

_ENDPOINT_OBJECT = {"type": "object"}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "memory_recall",
        "description": (
            "Check namespace consent, enable it from the current invocation event "
            "when required, and return a gated endpoint proposal. Search the "
            "supplied namespace first; accept global-search fields only when the "
            "current user explicitly requested fallback across enabled namespaces. "
            "Replaces the status, enable, and propose calls with one round trip."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "namespace",
                "episode_id",
                "input_text",
                "context",
                "baseline",
                "consent_ref",
            ],
            "properties": {
                "namespace": {"type": "string"},
                "episode_id": {"type": "string"},
                "input_text": {"type": "string"},
                "context": _ENDPOINT_OBJECT,
                "baseline": _ENDPOINT_OBJECT,
                "consent_ref": {"type": "string"},
                "baseline_source": {"type": "string", "enum": ["direct_user"]},
                "baseline_ref": {"type": "string"},
                "global_search_source": {
                    "type": "string",
                    "enum": ["direct_user"],
                },
                "global_search_ref": {"type": "string"},
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
    {
        "name": "memory_settle",
        "description": (
            "Consume one proposal, confirming first when memory influenced it. "
            "Supply the exact phrase from a fresh direct-user confirmation event; "
            "omit it only for a memory-free proposal, which has no gate."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["proposal_id", "source", "confirmation_ref"],
            "properties": {
                "proposal_id": {"type": "string"},
                "phrase": {
                    "type": "string",
                    "description": "Omit only for a memory-free proposal.",
                },
                "source": {"type": "string", "enum": ["direct_user"]},
                "confirmation_ref": {"type": "string"},
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
    {
        "name": "memory_learn",
        "description": (
            "Append one typed observation and reconsolidate the namespace. "
            "Replaces the observe and consolidate calls with one round trip."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "namespace",
                "episode_id",
                "pattern_type",
                "pattern_key",
                "value",
                "source",
                "evidence_ref",
            ],
            "properties": {
                "namespace": {"type": "string"},
                "episode_id": {"type": "string"},
                "pattern_type": {"type": "string", "enum": list(engine.PATTERN_TYPES)},
                "pattern_key": {"type": "string"},
                "value": {},
                "scope": _ENDPOINT_OBJECT,
                "triggers": {"type": "array", "items": {"type": "string"}},
                "operation": {"type": "string", "enum": sorted(engine.OPERATIONS)},
                "source": {
                    "type": "string",
                    "enum": sorted(engine.OBSERVATION_SOURCES),
                },
                "signal": {
                    "type": "string",
                    "enum": sorted(engine.BEHAVIOR_SIGNAL_THRESHOLDS),
                },
                "evidence_ref": {"type": "string"},
                "min_episodes": {"type": "integer", "minimum": 1},
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
    {
        "name": "memory_experience",
        "description": (
            "Record verified reusable workspace evidence or invalidate a stale hint. "
            "Hints are untrusted navigation evidence and never endpoint authority."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["action", "namespace"],
            "properties": {
                "action": {"type": "string", "enum": ["record", "invalidate"]},
                "namespace": {"type": "string"},
                "episode_id": {"type": "string"},
                "kind": {"type": "string", "enum": sorted(engine.EXPERIENCE_KINDS)},
                "hint_key": {"type": "string"},
                "value": {"type": "object"},
                "scope": _ENDPOINT_OBJECT,
                "tags": {"type": "array", "items": {"type": "string"}},
                "anchors": {"type": "array", "items": {"type": "object"}},
                "verification": {"type": "object"},
                "hint_id": {"type": "string"},
                "reason": {"type": "string"},
                "source": {
                    "type": "string",
                    "enum": sorted(engine.EXPERIENCE_INVALIDATION_SOURCES),
                },
                "evidence_ref": {"type": "string"},
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
    {
        "name": "memory_inspect",
        "description": (
            "Read consent, patterns, and reusable evidence for exactly one namespace."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["namespace"],
            "properties": {"namespace": {"type": "string"}},
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
]


class UnknownToolError(Exception):
    """Raised for a tool name outside the published surface."""


def _response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _error_code(error: BaseException) -> str:
    if isinstance(error, UnknownToolError):
        return "unknown_tool"
    for error_type, code, _exit_code in engine._ERROR_CODES:
        if isinstance(error, error_type):
            return code
    return "internal_error"


def _tool_result(payload: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, sort_keys=True)}],
        "structuredContent": payload,
        "isError": is_error,
    }


class Server:
    """Owns one lazily opened MemoryStore for the lifetime of the process."""

    def __init__(self, database: Path | None = None) -> None:
        self._database = database
        self._store: Any = None
        self._restart_required = False

    def _open(self) -> Any:
        if self._store is None:
            path = self._database or engine.default_store_path()
            self._store = engine.MemoryStore(path)
        return self._store

    def _drop_store(self) -> None:
        store = self._store
        self._store = None
        if store is not None:
            try:
                store.close()
            except Exception:
                pass

    @staticmethod
    def _validated(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Enforce the published schema here; never trust client-side validation.

        Raises the engine's input error so an argument mistake reports the same
        `invalid_input` code the CLI returns for a bad flag, keeping the two
        surfaces interchangeable and keeping argument errors out of the
        fallback triggers.
        """
        schema = next((tool["inputSchema"] for tool in TOOLS if tool["name"] == name), None)
        if schema is None:
            raise UnknownToolError(f"unknown tool: {name}")
        allowed = set(schema.get("properties", {}))
        unknown = sorted(set(arguments) - allowed)
        if unknown:
            raise engine.MemoryInputError(
                "unrecognized arguments: " + ", ".join(unknown)
            )
        missing = sorted(set(schema.get("required", [])) - set(arguments))
        if missing:
            raise engine.MemoryInputError(
                "the following arguments are required: " + ", ".join(missing)
            )
        return arguments

    def _dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        arguments = self._validated(name, arguments)
        store = self._open()
        if name == "memory_recall":
            return store.recall(**arguments)
        if name == "memory_settle":
            result = store.settle(
                arguments["proposal_id"],
                arguments.get("phrase"),
                source=arguments["source"],
                confirmation_ref=arguments["confirmation_ref"],
            )
            confirmation = result.get("confirmation")
            if isinstance(confirmation, dict) and "grant_token" in confirmation:
                # The grant is already spent; never echo it into model context.
                confirmation = dict(confirmation)
                confirmation["grant_token"] = None
                result = {**result, "confirmation": confirmation}
            return result
        if name == "memory_learn":
            return store.learn(**arguments)
        if name == "memory_experience":
            action = arguments["action"]
            payload = {key: value for key, value in arguments.items() if key != "action"}
            if action == "record":
                expected = {
                    "namespace", "episode_id", "kind", "hint_key", "value",
                    "scope", "tags", "anchors", "verification", "source",
                    "evidence_ref",
                }
                if set(payload) != expected:
                    raise engine.MemoryInputError(
                        "record requires exactly: " + ", ".join(sorted(expected))
                    )
                return store.record_experience(**payload)
            if action == "invalidate":
                expected = {
                    "namespace", "hint_id", "reason", "source", "evidence_ref"
                }
                if set(payload) != expected:
                    raise engine.MemoryInputError(
                        "invalidate requires exactly: " + ", ".join(sorted(expected))
                    )
                return store.invalidate_experience(**payload)
            raise engine.MemoryInputError("action must be record or invalidate")
        if name == "memory_inspect":
            namespace = arguments["namespace"]
            return {
                "consent": store.consent_status(namespace),
                "patterns": store.list_patterns(namespace),
                "evidence_hints": store.list_experience(namespace),
            }
        raise UnknownToolError(f"unknown tool: {name}")

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._restart_required:
            return _tool_result(self._restart_payload(), is_error=True)
        try:
            return _tool_result(self._dispatch(name, arguments))
        except Exception as error:
            if (
                isinstance(error, engine.MemoryInvariantError)
                and str(error) in SCHEMA_RESTART_MESSAGES
            ):
                # Fail closed and stay closed. Never reopen and never retry.
                self._restart_required = True
                self._drop_store()
                return _tool_result(self._restart_payload(), is_error=True)
            code = _error_code(error)
            if code in ("storage_error", "internal_error"):
                # Only a storage or unexpected failure may have left the handle
                # unusable. Domain errors already rolled back, so keep the warm
                # store rather than reopening the database on every refusal.
                self._drop_store()
            payload: dict[str, Any] = {
                "code": code,
                "type": type(error).__name__,
                # The CLI never reports an unexpected exception's text, which can
                # carry the database path. Match that exactly.
                "message": (
                    "unexpected memory engine failure"
                    if code == "internal_error"
                    else str(error)
                ),
            }
            details = getattr(error, "collisions", None)
            if details is not None:
                # Preserve the structured detail the CLI emits, or the caller
                # cannot satisfy the baseline attestation requirement.
                payload["details"] = {
                    "baseline_collisions": details,
                    "required_attestation": {
                        "source": "direct_user",
                        "unique_event_ref": True,
                        "effect": engine.BASELINE_ATTESTATION_EFFECT,
                    },
                }
            return _tool_result({"ok": False, "error": payload}, is_error=True)

    @staticmethod
    def _restart_payload() -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": "restart_required",
                "type": "MemoryInvariantError",
                "message": (
                    "memory runtime schema changed; restart this MCP server "
                    "before retrying"
                ),
            },
        }

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        if request_id is None:
            return None
        if method == "initialize":
            params = request.get("params") or {}
            return _response(
                request_id,
                {
                    "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            )
        if method == "ping":
            return _response(request_id, {})
        if method == "tools/list":
            return _response(request_id, {"tools": TOOLS})
        if method != "tools/call":
            return _error(request_id, -32601, f"method not found: {method}")

        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _response(
                request_id,
                _tool_result(
                    {
                        "ok": False,
                        "error": {
                            "code": "invalid_input",
                            "type": "MemoryInputError",
                            "message": "arguments must be a JSON object",
                        },
                    },
                    is_error=True,
                ),
            )
        return _response(request_id, self._call_tool(name, arguments))

    def close(self) -> None:
        self._drop_store()


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    database = Path(arguments[0]) if arguments else None
    server = Server(database)
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError("request must be a JSON object")
                response = server.handle(request)
            except (json.JSONDecodeError, ValueError) as error:
                response = _error(None, -32700, str(error))
            if response is not None:
                print(json.dumps(response, separators=(",", ":")), flush=True)
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
