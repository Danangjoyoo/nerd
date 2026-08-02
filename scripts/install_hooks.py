#!/usr/bin/env python3
"""Install idempotent global prompt hooks for the supported coding agents."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile
from typing import Any


SUPPORTED_AGENTS = ("claude-code", "codex", "cursor")
HOOK_MARKER = ".nerd/hooks/prompt_hook.py"


def _install_home() -> Path:
    override = os.environ.get("NERD_INSTALL_HOME")
    return Path(override).expanduser() if override else Path.home()


def _load_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def _write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(body)
        temporary = Path(handle.name)
    temporary.replace(path)


def _copy_hook(home: Path) -> Path:
    source = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "nerd-smart"
        / "scripts"
        / "prompt_hook.py"
    )
    destination = home / HOOK_MARKER
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    destination.chmod(0o755)
    return destination


def _command(hook_path: Path, agent: str) -> str:
    return f"python3 {shlex.quote(str(hook_path))} --agent {agent}"


def _is_nerd_handler(value: Any) -> bool:
    return isinstance(value, dict) and HOOK_MARKER in str(value.get("command", ""))


def _hooks_object(config: dict[str, Any], path: Path) -> dict[str, Any]:
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"expected hooks to be a JSON object in {path}")
    return hooks


def _ensure_nested_handler(
    config: dict[str, Any],
    path: Path,
    event: str,
    handler: dict[str, Any],
) -> None:
    hooks = _hooks_object(config, path)
    groups = hooks.setdefault(event, [])
    if not isinstance(groups, list):
        raise ValueError(f"expected hooks.{event} to be a JSON array in {path}")

    for group in groups:
        if not isinstance(group, dict):
            continue
        handlers = group.get("hooks")
        if not isinstance(handlers, list):
            continue
        for index, existing in enumerate(handlers):
            if _is_nerd_handler(existing):
                handlers[index] = handler
                return
    groups.append({"hooks": [handler]})


def _ensure_direct_handler(
    config: dict[str, Any],
    path: Path,
    event: str,
    handler: dict[str, Any],
) -> None:
    hooks = _hooks_object(config, path)
    handlers = hooks.setdefault(event, [])
    if not isinstance(handlers, list):
        raise ValueError(f"expected hooks.{event} to be a JSON array in {path}")
    for index, existing in enumerate(handlers):
        if _is_nerd_handler(existing):
            handlers[index] = handler
            return
    handlers.append(handler)


def _configure_agent(home: Path, hook_path: Path, agent: str) -> Path:
    command = _command(hook_path, agent)
    if agent == "claude-code":
        path = home / ".claude" / "settings.json"
        config = _load_object(path)
        _ensure_nested_handler(
            config,
            path,
            "UserPromptSubmit",
            {"type": "command", "command": command, "timeout": 5},
        )
    elif agent == "codex":
        path = home / ".codex" / "hooks.json"
        config = _load_object(path)
        _ensure_nested_handler(
            config,
            path,
            "UserPromptSubmit",
            {"type": "command", "command": command, "timeout": 5},
        )
    else:
        path = home / ".cursor" / "hooks.json"
        config = _load_object(path)
        config.setdefault("version", 1)
        _ensure_direct_handler(
            config,
            path,
            "sessionStart",
            {"command": command},
        )
    _write_object(path, config)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("agents", nargs="+", choices=SUPPORTED_AGENTS)
    args = parser.parse_args()

    home = _install_home()
    hook_path = _copy_hook(home)
    for agent in dict.fromkeys(args.agents):
        path = _configure_agent(home, hook_path, agent)
        print(f"Configured nerd-smart for {agent}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
