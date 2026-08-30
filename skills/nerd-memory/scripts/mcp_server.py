#!/usr/bin/env python3
"""Dependency-free stdio MCP adapter for global behavioral memory."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import memory as engine  # noqa: E402


SERVER_NAME = "nerd-memory-tools"
SERVER_VERSION = "2.0.0"
PROTOCOL_VERSION = "2025-06-18"

_STRING = {"type": "string"}
_STRING_ARRAY = {"type": "array", "items": {"type": "string"}}
_CURRENT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {"type": ["string", "null"]},
        "tools": _STRING_ARRAY,
        "steps": _STRING_ARRAY,
        "skills": _STRING_ARRAY,
    },
}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "memory_recall",
        "description": (
            "Return audited contextual behavioral advice. Current action, tools, "
            "steps, and skills remain authoritative."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "event_id",
                "raw_input",
                "repository",
                "language",
                "surface",
                "project_kind",
                "current",
                "output_signals",
                "consumer_agent",
            ],
            "properties": {
                "event_id": _STRING,
                "raw_input": _STRING,
                "repository": _STRING,
                "language": _STRING,
                "surface": _STRING,
                "project_kind": _STRING,
                "current": _CURRENT,
                "output_signals": _STRING_ARRAY,
                "consumer_agent": _STRING,
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
    {
        "name": "memory_record",
        "description": (
            "Record one verified behavioral episode. Raw input is transient and "
            "only sanitized command cues are persisted."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "episode_id",
                "repository",
                "language",
                "surface",
                "project_kind",
                "raw_input",
                "action",
                "tools",
                "steps",
                "skills",
                "output_signals",
                "output_valid",
                "output_severity",
                "verified",
                "verifier",
                "feedback",
                "source_kind",
                "source_agent",
                "evidence_ref",
            ],
            "properties": {
                "episode_id": _STRING,
                "repository": _STRING,
                "language": _STRING,
                "surface": _STRING,
                "project_kind": _STRING,
                "raw_input": _STRING,
                "action": _STRING,
                "tools": _STRING_ARRAY,
                "steps": _STRING_ARRAY,
                "skills": _STRING_ARRAY,
                "output_signals": _STRING_ARRAY,
                "output_valid": {"type": "boolean"},
                "output_severity": {
                    "type": "string",
                    "enum": sorted(engine.SEVERITY_VALUES),
                },
                "verified": {"type": "boolean"},
                "verifier": _STRING,
                "feedback": {
                    "type": "string",
                    "enum": sorted(engine.FEEDBACK_VALUES),
                },
                "corrected_tools": _STRING_ARRAY,
                "corrected_steps": _STRING_ARRAY,
                "corrected_skills": _STRING_ARRAY,
                "source_kind": {
                    "type": "string",
                    "enum": sorted(engine.SOURCE_KINDS),
                },
                "source_agent": _STRING,
                "evidence_ref": _STRING,
                "observed_at": _STRING,
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
    {
        "name": "memory_inspect",
        "description": "Read bounded sanitized episode and audit summaries.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [],
            "properties": {},
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
    for error_type, code, _exit_code in engine.ERROR_CODES:
        if isinstance(error, error_type):
            return code
    return "internal_error"


def _tool_result(payload: Any, *, is_error: bool = False) -> dict[str, Any]:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
        "isError": is_error,
    }


def _domain_payload(error: BaseException) -> dict[str, Any]:
    code = _error_code(error)
    return {
        "ok": False,
        "error": {
            "code": code,
            "type": type(error).__name__,
            "message": (
                "unexpected memory engine failure"
                if code == "internal_error"
                else str(error)
            ),
        },
    }


class Server:
    """Own one lazy store and permanently fence schema-incompatible sessions."""

    def __init__(self, database: Path | None = None) -> None:
        self._database = database
        self._store: engine.BehaviorMemoryStore | None = None
        self._restart_required = False

    def _open(self) -> engine.BehaviorMemoryStore:
        if self._store is None:
            path = self._database or engine.default_database_path()
            self._store = engine.BehaviorMemoryStore(path)
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
    def _schema(name: str) -> dict[str, Any]:
        for tool in TOOLS:
            if tool["name"] == name:
                return tool["inputSchema"]
        raise UnknownToolError(f"unknown tool: {name}")

    @classmethod
    def _validated(cls, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        schema = cls._schema(name)
        allowed = set(schema["properties"])
        unknown = sorted(set(arguments) - allowed)
        if unknown:
            raise engine.MemoryInputError(
                "unrecognized arguments: " + ", ".join(unknown)
            )
        missing = sorted(set(schema["required"]) - set(arguments))
        if missing:
            raise engine.MemoryInputError(
                "the following arguments are required: " + ", ".join(missing)
            )
        return arguments

    def _dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        validated = self._validated(name, arguments)
        store = self._open()
        if name == "memory_recall":
            return store.recall(**validated)
        if name == "memory_record":
            return store.record(**validated)
        if name == "memory_inspect":
            return store.inspect()
        raise UnknownToolError(f"unknown tool: {name}")

    @staticmethod
    def _restart_payload() -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": "restart_required",
                "type": "MemorySchemaError",
                "message": (
                    "behavioral memory schema changed; restart this MCP server "
                    "before retrying"
                ),
            },
        }

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._restart_required:
            return _tool_result(self._restart_payload(), is_error=True)
        try:
            return _tool_result(self._dispatch(name, arguments))
        except Exception as error:
            if isinstance(error, engine.MemorySchemaError):
                self._restart_required = True
                self._drop_store()
            else:
                code = _error_code(error)
                if code in {"storage_error", "internal_error"}:
                    self._drop_store()
            return _tool_result(_domain_payload(error), is_error=True)

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        if request_id is None:
            return None
        if method == "initialize":
            return _response(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            )
        if method == "ping":
            return _response(request_id, {})
        if method == "tools/list":
            return _response(request_id, {"tools": TOOLS})
        if method != "tools/call":
            return _error(request_id, -32601, f"method not found: {method}")

        params = request.get("params", {})
        if not isinstance(params, dict):
            return _error(request_id, -32602, "params must be a JSON object")
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            error = engine.MemoryInputError("arguments must be a JSON object")
            return _response(
                request_id,
                _tool_result(_domain_payload(error), is_error=True),
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
                print(
                    json.dumps(response, ensure_ascii=False, separators=(",", ":")),
                    flush=True,
                )
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
