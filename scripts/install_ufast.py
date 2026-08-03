#!/usr/bin/env python3
"""Install Nerd UFast's local runtime and explicit Codex MCP configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import tempfile


START_MARKER = "# >>> nerd-ufast managed MCP >>>"
END_MARKER = "# <<< nerd-ufast managed MCP <<<"
TABLE_HEADER = "[mcp_servers.nerd_ufast]"


def _install_home() -> Path:
    override = os.environ.get("NERD_INSTALL_HOME")
    return Path(override).expanduser() if override else Path.home()


def _atomic_write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as stream:
        stream.write(body)
        temporary = Path(stream.name)
    temporary.replace(path)


def _copy_runtime(home: Path) -> Path:
    source = Path(__file__).resolve().parents[1] / "skills" / "nerd-ufast" / "scripts"
    destination = home / ".nerd" / "ufast"
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("ufast_core.py", "ufast_mcp.py"):
        shutil.copyfile(source / name, destination / name)
        (destination / name).chmod(0o755)
    return destination / "ufast_mcp.py"


def _managed_block(server: Path) -> str:
    server_value = json.dumps(str(server), ensure_ascii=False)
    return "\n".join(
        (
            START_MARKER,
            TABLE_HEADER,
            'command = "python3"',
            f"args = [{server_value}]",
            "startup_timeout_sec = 5",
            "tool_timeout_sec = 30",
            END_MARKER,
        )
    )


def _configure_codex(home: Path, server: Path) -> Path:
    config = home / ".codex" / "config.toml"
    original = config.read_text(encoding="utf-8") if config.is_file() else ""
    start_count = original.count(START_MARKER)
    end_count = original.count(END_MARKER)
    if start_count != end_count or start_count > 1:
        raise ValueError(f"Malformed Nerd UFast managed block in {config}")

    block = _managed_block(server)
    if start_count == 1:
        pattern = re.compile(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            re.DOTALL,
        )
        updated = pattern.sub(block, original)
    else:
        if re.search(r"(?m)^\s*\[mcp_servers\.nerd_ufast\]\s*$", original):
            raise ValueError(
                f"Refusing to replace an unmanaged mcp_servers.nerd_ufast entry in {config}"
            )
        updated = original.rstrip()
        if updated:
            updated += "\n\n"
        updated += block + "\n"
    if not updated.endswith("\n"):
        updated += "\n"
    _atomic_write(config, updated)
    return config


def main() -> int:
    home = _install_home()
    server = _copy_runtime(home)
    config = _configure_codex(home, server)
    print(f"Configured nerd-ufast for Codex: {config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
