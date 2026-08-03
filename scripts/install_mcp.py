#!/usr/bin/env python3
"""Install and register the dependency-free UFast MCP server."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


SUPPORTED_AGENTS = ("claude-code", "codex", "cursor")
SERVER_NAME = "nerd-ufast-tools"
RUNTIME_DIRECTORY = Path(".nerd/mcp/nerd-ufast")
STATE_PATH = Path(".nerd/mcp/registrations.json")
RUNTIME_FILES = ("mcp_server.py", "ufast_tools.py")


def _install_home() -> Path:
    override = os.environ.get("NERD_INSTALL_HOME")
    return Path(override).expanduser() if override else Path.home()


def _source_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / "nerd-ufast" / "scripts"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"expected a JSON object in {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(body)
        temporary = Path(handle.name)
    temporary.replace(path)


def _copy_runtime(home: Path) -> Path:
    source = _source_directory()
    destination = home / RUNTIME_DIRECTORY
    destination.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME_FILES:
        source_path = source / name
        if not source_path.is_file():
            raise RuntimeError(f"missing bundled MCP runtime: {source_path}")
        shutil.copy2(source_path, destination / name)
    return destination


def _health_check(server: Path) -> None:
    requests = (
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "nerd-installer", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    completed = subprocess.run(
        [sys.executable, "-B", str(server)],
        input="".join(json.dumps(item) + "\n" for item in requests),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"UFast MCP health check failed: {completed.stderr.strip()}")
    try:
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        tools = responses[1]["result"]["tools"]
        names = {tool["name"] for tool in tools}
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("UFast MCP health check returned invalid output") from error
    if names != {"inspect", "apply_verify"}:
        raise RuntimeError(f"UFast MCP health check returned unexpected tools: {names}")


def _command_environment(home: Path, environment: dict[str, str]) -> dict[str, str]:
    result = dict(environment)
    result["HOME"] = str(home)
    if "NERD_INSTALL_HOME" in result:
        result["CODEX_HOME"] = str(home / ".codex")
    return result


def _cli(agent: str) -> str:
    return "claude" if agent == "claude-code" else agent


def _run(
    argv: list[str],
    environment: dict[str, str],
    *,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"MCP registration command failed: {' '.join(argv)}: {detail}")
    return completed


def _owned_text(value: str, server: Path) -> bool:
    normalized = value.replace("\\", "/")
    return str(server).replace("\\", "/") in normalized or ".nerd/mcp/nerd-ufast" in normalized


def _cursor_config(home: Path) -> dict[str, Any]:
    path = home / ".cursor" / "mcp.json"
    return _load_json(path) if path.exists() else {}


def _existing_registration(
    agent: str,
    server: Path,
    home: Path,
    environment: dict[str, str],
    recorded: dict[str, Any] | None,
) -> str:
    if agent == "codex":
        completed = _run(
            ["codex", "mcp", "get", SERVER_NAME, "--json"],
            environment,
            check=False,
        )
        if completed.returncode:
            return "missing"
        return "owned" if _owned_text(completed.stdout, server) else "conflict"
    if agent == "claude-code":
        completed = _run(
            ["claude", "mcp", "get", SERVER_NAME],
            environment,
            check=False,
        )
        if completed.returncode:
            return "missing"
        output = completed.stdout + completed.stderr
        return "owned" if _owned_text(output, server) else "conflict"

    completed = _run(
        ["cursor", "agent", "mcp", "list"],
        environment,
        check=False,
    )
    listed = completed.returncode == 0 and SERVER_NAME in completed.stdout
    config = _cursor_config(home)
    entry = config.get("mcpServers", {}).get(SERVER_NAME)
    if isinstance(entry, dict):
        return "owned" if _owned_text(json.dumps(entry), server) else "conflict"
    if listed:
        return "owned" if recorded and _owned_text(json.dumps(recorded), server) else "conflict"
    return "missing"


def _remove_registration(
    agent: str,
    environment: dict[str, str],
) -> None:
    if agent == "codex":
        command = ["codex", "mcp", "remove", SERVER_NAME]
    elif agent == "claude-code":
        command = ["claude", "mcp", "remove", "--scope", "user", SERVER_NAME]
    else:
        return
    _run(command, environment, check=True)


def _add_registration(
    agent: str,
    server: Path,
    environment: dict[str, str],
) -> None:
    if agent == "codex":
        command = [
            "codex",
            "mcp",
            "add",
            SERVER_NAME,
            "--",
            "python3",
            str(server),
        ]
        _run(command, environment, check=True)
        return
    if agent == "claude-code":
        command = [
            "claude",
            "mcp",
            "add",
            "--scope",
            "user",
            SERVER_NAME,
            "--",
            "python3",
            str(server),
        ]
        _run(command, environment, check=True)
        return
    definition = json.dumps(
        {
            "name": SERVER_NAME,
            "command": "python3",
            "args": [str(server)],
        },
        separators=(",", ":"),
    )
    _run(["cursor", "--add-mcp", definition], environment, check=True)
    _run(
        ["cursor", "agent", "mcp", "enable", SERVER_NAME],
        environment,
        check=True,
    )


def install(
    agents: tuple[str, ...],
    *,
    home: Path | None = None,
    environment: dict[str, str] | None = None,
) -> Path:
    selected = tuple(dict.fromkeys(agents))
    unknown = set(selected) - set(SUPPORTED_AGENTS)
    if unknown:
        raise RuntimeError(f"unsupported agents: {', '.join(sorted(unknown))}")
    home = (home or _install_home()).expanduser().resolve()
    environment = _command_environment(home, environment or os.environ.copy())
    runtime = _copy_runtime(home)
    server = runtime / "mcp_server.py"
    _health_check(server)

    state_path = home / STATE_PATH
    state = _load_json(state_path)
    registrations = state.setdefault("agents", {})
    if not isinstance(registrations, dict):
        raise RuntimeError(f"expected agents object in {state_path}")

    for agent in selected:
        cli = _cli(agent)
        if shutil.which(cli, path=environment.get("PATH")) is None:
            raise RuntimeError(f"{cli} CLI is required to register UFast MCP tools")
        recorded = registrations.get(agent)
        if isinstance(recorded, dict) and recorded.get("server") == str(server):
            continue
        existing = _existing_registration(
            agent,
            server,
            home,
            environment,
            recorded if isinstance(recorded, dict) else None,
        )
        if existing == "conflict":
            raise RuntimeError(
                f"conflicting MCP registration named {SERVER_NAME} for {agent}"
            )
        if existing == "owned":
            _remove_registration(agent, environment)
        _add_registration(agent, server, environment)
        registrations[agent] = {"server": str(server)}
        _write_json(state_path, state)
    return runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("agents", nargs="+", choices=SUPPORTED_AGENTS)
    args = parser.parse_args(argv)
    try:
        runtime = install(tuple(args.agents))
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for agent in dict.fromkeys(args.agents):
        print(f"Configured {SERVER_NAME} for {agent}: {runtime / 'mcp_server.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
