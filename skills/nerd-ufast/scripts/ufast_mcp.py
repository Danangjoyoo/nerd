#!/usr/bin/env python3
"""A minimal stdio MCP server for Nerd UFast's bounded workspace transaction."""

from __future__ import annotations

import time
SERVER_STARTED = time.perf_counter()

from pathlib import Path
import json
import os
import sys
from typing import Any


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from ufast_core import (  # noqa: E402
    VERSION,
    apply_workspace_change,
    prepare_workspace_change,
)


COLD_START_MS: int | None = None
PROTOCOL_VERSION = "2025-11-25"


TOOLS: list[dict[str, Any]] = [
    {
        "name": "ufast_prepare_workspace_change",
        "title": "Prepare a bounded workspace change",
        "description": (
            "Read bounded editable UTF-8 workspace files once, capture SHA-256 "
            "preconditions, and report available verification adapters."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "ufast_apply_workspace_change",
        "title": "Apply and verify a bounded workspace change",
        "description": (
            "Atomically replace existing UTF-8 text files when their hashes match, "
            "run available fixed verification adapters, and restore originals on failure."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "changes": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 12,
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "expected_sha256": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "content": {"type": "string"},
                        },
                        "required": ["path", "expected_sha256", "content"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["changes"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
]


def _workspace() -> Path | str:
    return os.environ.get("NERD_UFAST_WORKSPACE", "")


def _record_telemetry(tool: str, result: dict[str, Any]) -> None:
    raw_path = os.environ.get("NERD_UFAST_LOG")
    if not raw_path:
        return
    event = {
        "tool": tool,
        "status": result.get("status", "unknown"),
        "runtime_version": result.get("runtime_version", VERSION),
        "operation_ms": result.get("operation_ms"),
        "cold_start_ms": result.get("cold_start_ms", 0),
        "changed_files": result.get("changed_files", []),
        "checks": [
            {
                "name": check.get("name"),
                "exit_code": check.get("exit_code"),
            }
            for check in result.get("checks", [])
            if isinstance(check, dict)
        ],
        "rolled_back": result.get("rolled_back", False),
    }
    if isinstance(result.get("reason"), str):
        event["reason"] = result["reason"][:500]
    try:
        log_path = Path(raw_path).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError as error:
        print(f"nerd-ufast telemetry warning: {error}", file=sys.stderr, flush=True)


def _tool_result(name: Any, arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        result = {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": "Tool arguments must be an object",
        }
    elif name == "ufast_prepare_workspace_change":
        result = prepare_workspace_change(_workspace())
    elif name == "ufast_apply_workspace_change":
        result = apply_workspace_change(_workspace(), arguments.get("changes"))
    else:
        result = {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": f"Unknown tool: {name!r}",
        }
    result["cold_start_ms"] = COLD_START_MS if COLD_START_MS is not None else 0
    _record_telemetry(str(name), result)
    is_error = result.get("status") not in {"ready", "applied"}
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, sort_keys=True, separators=(",", ":")),
            }
        ],
        "structuredContent": result,
        "isError": is_error,
    }


def _response(request: dict[str, Any]) -> dict[str, Any] | None:
    global COLD_START_MS

    request_id = request.get("id")
    method = request.get("method")
    if request_id is None:
        return None
    if method == "initialize":
        if COLD_START_MS is None:
            COLD_START_MS = max(
                0,
                round((time.perf_counter() - SERVER_STARTED) * 1_000),
            )
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        requested_version = params.get("protocolVersion")
        protocol_version = (
            requested_version if isinstance(requested_version, str) else PROTOCOL_VERSION
        )
        result: dict[str, Any] = {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "nerd-ufast", "version": VERSION},
            "instructions": (
                "Prepare once, submit one complete hash-guarded Python batch, "
                "and use the normal agent workflow when the operation is unsupported."
            ),
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        result = _tool_result(params.get("name"), params.get("arguments", {}))
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method!r}"},
        }
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> int:
    for raw_line in sys.stdin:
        try:
            request = json.loads(raw_line)
            if not isinstance(request, dict):
                raise ValueError("JSON-RPC request must be an object")
            response = _response(request)
        except (json.JSONDecodeError, ValueError) as error:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(error)},
            }
        except Exception as error:  # Keep transport failures visible to the client.
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if isinstance(request, dict) else None,
                "error": {"code": -32603, "message": f"Internal error: {error}"},
            }
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
