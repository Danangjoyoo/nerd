#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ufast_tools import InspectIndex, apply_verify


SERVER_NAME = "nerd-ufast-tools"
SERVER_VERSION = "0.1.0"

TOOLS = [
    {
        "name": "inspect",
        "description": "Batch exact symbol and bounded path inspection inside one workspace.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["workspace", "queries"],
            "properties": {
                "workspace": {"type": "string"},
                "queries": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "path": {"type": "string"},
                            "start_line": {"type": "integer", "minimum": 1},
                            "end_line": {"type": "integer", "minimum": 1},
                        },
                    },
                },
                "context_lines": {"type": "integer", "minimum": 0, "maximum": 100, "default": 2},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 500, "default": 20},
                "max_bytes": {"type": "integer", "minimum": 1, "maximum": 1000000, "default": 65536},
            },
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "apply_verify",
        "description": "Apply one hash-guarded unified patch and run bounded verification without a shell.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["workspace", "patch", "expected_hashes", "checks"],
            "properties": {
                "workspace": {"type": "string"},
                "patch": {"type": "string"},
                "expected_hashes": {
                    "type": "object",
                    "additionalProperties": {"type": ["string", "null"]},
                },
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["argv"],
                        "properties": {
                            "argv": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                            "timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
                        },
                    },
                },
                "timeout_seconds": {"type": "number", "minimum": 0.01, "maximum": 300, "default": 120},
                "max_output_bytes": {"type": "integer", "minimum": 1, "maximum": 1000000, "default": 65536},
            },
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True},
    },
]


def _response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


class Server:
    def __init__(self) -> None:
        self.index = InspectIndex()

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        if request_id is None:
            return None
        if method == "initialize":
            params = request.get("params") or {}
            protocol = params.get("protocolVersion", "2025-06-18")
            return _response(
                request_id,
                {
                    "protocolVersion": protocol,
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
        try:
            if name == "inspect":
                result = self.index.inspect(**arguments)
            elif name == "apply_verify":
                result = apply_verify(**arguments)
                self.index.invalidate(arguments["workspace"])
            else:
                raise ValueError(f"unknown tool: {name}")
            return _response(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(result, sort_keys=True)}],
                    "structuredContent": result,
                    "isError": False,
                },
            )
        except Exception as error:
            return _response(
                request_id,
                {
                    "content": [{"type": "text", "text": f"{type(error).__name__}: {error}"}],
                    "isError": True,
                },
            )


def main() -> int:
    server = Server()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be an object")
            response = server.handle(request)
        except (json.JSONDecodeError, ValueError) as error:
            response = _error(None, -32700, str(error))
        if response is not None:
            print(json.dumps(response, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
