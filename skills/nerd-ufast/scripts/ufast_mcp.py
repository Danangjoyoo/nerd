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
    safe_edit,
)
from ufast_index import ProjectIndex  # noqa: E402
from ufast_registry import phase_one_registry  # noqa: E402
from ufast_verify import run_test_plan  # noqa: E402


COLD_START_MS: int | None = None
PROTOCOL_VERSION = "2025-11-25"


def _workspace() -> Path | str:
    return os.environ.get("NERD_UFAST_WORKSPACE", "")


PROJECT_INDEX = ProjectIndex(_workspace())


def _project_index(arguments: dict[str, Any]) -> dict[str, Any]:
    if not set(arguments) <= {"refresh", "max_entries"}:
        return {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": "Unexpected project-index argument",
        }
    return PROJECT_INDEX.project_index(
        refresh=arguments.get("refresh", False),
        max_entries=arguments.get("max_entries", 200),
    )


def _fast_search(arguments: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "query",
        "queries",
        "mode",
        "case_sensitive",
        "paths",
        "max_results",
        "context_lines",
    }
    if not set(arguments) <= allowed:
        return {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": "Unexpected fast-search argument",
            "matches": [],
        }
    return PROJECT_INDEX.fast_search(
        arguments.get("query"),
        queries=arguments.get("queries"),
        mode=arguments.get("mode", "literal"),
        case_sensitive=arguments.get("case_sensitive", False),
        paths=arguments.get("paths"),
        max_results=arguments.get("max_results", 20),
        context_lines=arguments.get("context_lines", 2),
    )


def _safe_edit(arguments: dict[str, Any]) -> dict[str, Any]:
    if not set(arguments) <= {"changes", "verify", "checks"}:
        return {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": "Unexpected safe-edit argument",
            "changed_files": [],
            "checks": [],
            "rolled_back": False,
        }
    try:
        changes = _normalize_safe_edit_changes(arguments.get("changes"))
    except ValueError as error:
        return {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": str(error),
            "changed_files": [],
            "checks": [],
            "rolled_back": False,
        }
    result = safe_edit(
        _workspace(),
        changes,
        verify=arguments.get("verify", True),
        selected_checks=arguments.get("checks"),
    )
    if result.get("status") == "applied":
        PROJECT_INDEX.project_index(refresh=True)
    return result


def _normalize_safe_edit_changes(value: object) -> list[dict[str, Any]]:
    """Group ergonomic flat edit operations into one atomic per-file batch."""

    if not isinstance(value, list) or not 1 <= len(value) <= 50:
        raise ValueError("changes must contain between 1 and 50 edit operations")
    grouped: dict[str, dict[str, Any]] = {}
    allowed = {
        "path",
        "sha256",
        "content",
        "old_text",
        "new_text",
        "expected_occurrences",
    }
    for operation in value:
        if not isinstance(operation, dict) or not set(operation) <= allowed:
            raise ValueError("Each edit operation must use only the documented fields")
        path = operation.get("path")
        digest = operation.get("sha256")
        if not isinstance(path, str) or not path:
            raise ValueError("Each edit operation requires a non-empty path")
        if not isinstance(digest, str):
            raise ValueError(f"Each edit operation requires the indexed sha256: {path!r}")
        content_present = "content" in operation
        replacement_present = "old_text" in operation or "new_text" in operation
        if content_present == replacement_present:
            raise ValueError(
                f"Exactly one of content or old_text/new_text is required: {path!r}"
            )
        existing = grouped.get(path)
        if existing is not None and existing["expected_sha256"] != digest:
            raise ValueError(f"Conflicting source hashes for {path!r}")
        if content_present:
            content = operation.get("content")
            if not isinstance(content, str):
                raise ValueError(f"content must be a string for {path!r}")
            if existing is not None:
                raise ValueError(f"Complete-content edits cannot be combined for {path!r}")
            grouped[path] = {
                "path": path,
                "expected_sha256": digest,
                "content": content,
            }
            continue
        old_text = operation.get("old_text")
        new_text = operation.get("new_text")
        occurrences = operation.get("expected_occurrences", 1)
        if not isinstance(old_text, str) or not old_text:
            raise ValueError(f"old_text must be a non-empty string for {path!r}")
        if not isinstance(new_text, str):
            raise ValueError(f"new_text must be a string for {path!r}")
        if (
            not isinstance(occurrences, int)
            or isinstance(occurrences, bool)
            or occurrences < 1
        ):
            raise ValueError(f"expected_occurrences must be positive for {path!r}")
        if existing is None:
            existing = {
                "path": path,
                "expected_sha256": digest,
                "replacements": [],
            }
            grouped[path] = existing
        if "content" in existing:
            raise ValueError(f"Replacement edits cannot follow content for {path!r}")
        existing["replacements"].append(
            {
                "old_text": old_text,
                "new_text": new_text,
                "expected_occurrences": occurrences,
            }
        )
    if len(grouped) > 12:
        raise ValueError("changes may target at most 12 files")
    return list(grouped.values())


def _test_runner(arguments: dict[str, Any]) -> dict[str, Any]:
    if not set(arguments) <= {"changed_paths", "checks"}:
        return {
            "status": "rejected",
            "runtime_version": VERSION,
            "operation_ms": 0,
            "reason": "Unexpected test-runner argument",
            "checks": [],
        }
    return run_test_plan(
        _workspace(),
        arguments.get("changed_paths"),
        arguments.get("checks"),
    )


REGISTRY = phase_one_registry(
    project_index=_project_index,
    fast_search=_fast_search,
    safe_edit=_safe_edit,
    test_runner=_test_runner,
)
TOOLS = REGISTRY.tool_definitions()


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
        "route": result.get("route"),
        "backend": result.get("backend"),
        "cache_status": result.get("cache_status"),
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
    result = REGISTRY.dispatch(name, arguments)
    result["cold_start_ms"] = COLD_START_MS if COLD_START_MS is not None else 0
    _record_telemetry(str(name), result)
    is_error = result.get("status") not in {
        "ready",
        "matched",
        "no_match",
        "applied",
        "passed",
    }
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
                "Route project mapping, indexed search, safe UTF-8 edits, and "
                "allowlisted repository checks through the registered tools; "
                "use the active workflow when an intent is unsupported."
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
