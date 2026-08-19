#!/usr/bin/env python3
"""Install and register a dependency-free Nerd stdio MCP server.

This is the server-agnostic form of the parked UFast experiment installer
(`docs/experiments/nerd-ufast/install_mcp.py`). Every server-specific constant
is an argument of :func:`install_server`, and registration state nests by
server name so one state file can hold several servers.
"""

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
STATE_PATH = Path(".nerd/mcp/registrations.json")
LEGACY_STATE_KEY = "agents"

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# Registry of installable servers, keyed by registered server name.
SERVERS: dict[str, dict[str, Any]] = {
    "nerd-memory-tools": {
        "runtime_directory": Path(".nerd/mcp/nerd-memory"),
        "source_directory": REPOSITORY_ROOT / "skills" / "nerd-memory" / "scripts",
        "runtime_files": ("mcp_server.py", "memory.py"),
        "expected_tools": {
            "memory_recall",
            "memory_settle",
            "memory_learn",
            "memory_inspect",
        },
    },
}


def _install_home() -> Path:
    override = os.environ.get("NERD_INSTALL_HOME")
    return Path(override).expanduser() if override else Path.home()


def _interpreter() -> str:
    """Interpreter registered as the server command.

    The experiment installer hardcoded ``python3``. A bare ``python3`` on the
    PATH is not necessarily the interpreter this repository runs under, so a
    hardcoded name can register a server that never starts while the health
    check (which runs under the current interpreter) still passes.
    """

    return sys.executable


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


def _copy_runtime(
    home: Path,
    *,
    source_directory: Path,
    runtime_directory: Path,
    runtime_files: tuple[str, ...],
) -> Path:
    destination = home / runtime_directory
    destination.mkdir(parents=True, exist_ok=True)
    for name in runtime_files:
        source_path = source_directory / name
        if not source_path.is_file():
            raise RuntimeError(f"missing bundled MCP runtime: {source_path}")
        shutil.copy2(source_path, destination / name)
    return destination


def _health_check(server: Path, *, server_name: str, expected_tools: set[str]) -> None:
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
        [_interpreter(), "-B", str(server)],
        input="".join(json.dumps(item) + "\n" for item in requests),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"{server_name} MCP health check failed: {completed.stderr.strip()}"
        )
    try:
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        tools = responses[1]["result"]["tools"]
        names = {tool["name"] for tool in tools}
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"{server_name} MCP health check returned invalid output"
        ) from error
    if names != set(expected_tools):
        raise RuntimeError(
            f"{server_name} MCP health check returned unexpected tools: {names}"
        )


def _command_environment(home: Path, environment: dict[str, str]) -> dict[str, str]:
    result = dict(environment)
    result["HOME"] = str(home)
    if "NERD_INSTALL_HOME" in result and "CODEX_HOME" not in result:
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


def _owned_text(value: str, server: Path, runtime_directory: Path) -> bool:
    normalized = value.replace("\\", "/")
    server_text = str(server).replace("\\", "/")
    runtime_text = str(runtime_directory).replace("\\", "/")
    return server_text in normalized or runtime_text in normalized


def _cursor_config(home: Path) -> dict[str, Any]:
    path = home / ".cursor" / "mcp.json"
    return _load_json(path) if path.exists() else {}


def _existing_registration(
    agent: str,
    server: Path,
    home: Path,
    environment: dict[str, str],
    recorded: dict[str, Any] | None,
    *,
    server_name: str,
    runtime_directory: Path,
) -> str:
    if agent == "codex":
        completed = _run(
            ["codex", "mcp", "get", server_name, "--json"],
            environment,
            check=False,
        )
        if completed.returncode:
            return "missing"
        owned = _owned_text(completed.stdout, server, runtime_directory)
        return "owned" if owned else "conflict"
    if agent == "claude-code":
        completed = _run(
            ["claude", "mcp", "get", server_name],
            environment,
            check=False,
        )
        if completed.returncode:
            return "missing"
        output = completed.stdout + completed.stderr
        return "owned" if _owned_text(output, server, runtime_directory) else "conflict"

    completed = _run(
        ["cursor", "agent", "mcp", "list"],
        environment,
        check=False,
    )
    listed = completed.returncode == 0 and server_name in completed.stdout
    config = _cursor_config(home)
    entry = config.get("mcpServers", {}).get(server_name)
    if isinstance(entry, dict):
        owned = _owned_text(json.dumps(entry), server, runtime_directory)
        return "owned" if owned else "conflict"
    if listed:
        owned = bool(recorded) and _owned_text(
            json.dumps(recorded), server, runtime_directory
        )
        return "owned" if owned else "conflict"
    return "missing"


def _remove_registration(
    agent: str,
    environment: dict[str, str],
    *,
    server_name: str,
) -> None:
    if agent == "codex":
        command = ["codex", "mcp", "remove", server_name]
    elif agent == "claude-code":
        command = ["claude", "mcp", "remove", "--scope", "user", server_name]
    else:
        return
    _run(command, environment, check=True)


def _add_registration(
    agent: str,
    server: Path,
    environment: dict[str, str],
    *,
    server_name: str,
) -> None:
    interpreter = _interpreter()
    if agent == "codex":
        command = [
            "codex",
            "mcp",
            "add",
            server_name,
            "--",
            interpreter,
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
            server_name,
            "--",
            interpreter,
            str(server),
        ]
        _run(command, environment, check=True)
        return
    definition = json.dumps(
        {
            "name": server_name,
            "command": interpreter,
            "args": [str(server)],
        },
        separators=(",", ":"),
    )
    _run(["cursor", "--add-mcp", definition], environment, check=True)
    _run(
        ["cursor", "agent", "mcp", "enable", server_name],
        environment,
        check=True,
    )


def install_server(
    agents: tuple[str, ...],
    *,
    server_name: str,
    runtime_directory: Path,
    source_directory: Path,
    runtime_files: tuple[str, ...],
    expected_tools: set[str],
    home: Path | None = None,
    environment: dict[str, str] | None = None,
) -> Path:
    """Install one stdio MCP server and register it with the given agents."""

    if not server_name or server_name == LEGACY_STATE_KEY:
        raise RuntimeError(f"invalid MCP server name: {server_name!r}")
    selected = tuple(dict.fromkeys(agents))
    unknown = set(selected) - set(SUPPORTED_AGENTS)
    if unknown:
        raise RuntimeError(f"unsupported agents: {', '.join(sorted(unknown))}")
    home = (home or _install_home()).expanduser().resolve()
    environment = _command_environment(home, environment or os.environ.copy())
    runtime = _copy_runtime(
        home,
        source_directory=Path(source_directory),
        runtime_directory=Path(runtime_directory),
        runtime_files=tuple(runtime_files),
    )
    server = runtime / "mcp_server.py"
    _health_check(server, server_name=server_name, expected_tools=set(expected_tools))

    state_path = home / STATE_PATH
    state = _load_json(state_path)
    registrations = state.setdefault(server_name, {})
    if not isinstance(registrations, dict):
        raise RuntimeError(f"expected {server_name} object in {state_path}")

    # One agent must not block the others: a user with two of the three CLIs
    # installed should still get those two registered. Collect every failure and
    # report them together once the reachable agents are done.
    failures: list[str] = []
    for agent in selected:
        cli = _cli(agent)
        if shutil.which(cli, path=environment.get("PATH")) is None:
            failures.append(f"{cli} CLI is required to register {server_name}")
            continue
        recorded = registrations.get(agent)
        # Never trust the state file alone. The user may have removed the
        # registration by hand, and re-running the installer must repair it.
        existing = _existing_registration(
            agent,
            server,
            home,
            environment,
            recorded if isinstance(recorded, dict) else None,
            server_name=server_name,
            runtime_directory=Path(runtime_directory),
        )
        if existing == "conflict":
            failures.append(
                f"conflicting MCP registration named {server_name} for {agent}"
            )
            continue
        try:
            if existing == "owned":
                _remove_registration(agent, environment, server_name=server_name)
            _add_registration(agent, server, environment, server_name=server_name)
        except RuntimeError as error:
            failures.append(str(error))
            continue
        registrations[agent] = {"server": str(server)}
        _write_json(state_path, state)
    if failures:
        raise RuntimeError("; ".join(failures))
    return runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, choices=sorted(SERVERS))
    parser.add_argument("agents", nargs="+", choices=SUPPORTED_AGENTS)
    args = parser.parse_args(argv)
    definition = SERVERS[args.server]
    try:
        runtime = install_server(
            tuple(args.agents),
            server_name=args.server,
            runtime_directory=definition["runtime_directory"],
            source_directory=definition["source_directory"],
            runtime_files=definition["runtime_files"],
            expected_tools=definition["expected_tools"],
        )
    except Exception as error:
        # A health-check timeout or filesystem error must not print a traceback
        # into installer output.
        print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    for agent in dict.fromkeys(args.agents):
        print(f"Configured {args.server} for {agent}: {runtime / 'mcp_server.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
