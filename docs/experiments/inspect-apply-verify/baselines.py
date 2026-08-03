from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from tools import _match, _root, apply_patch_only, verify_only


def inspect(
    workspace: str,
    symbol: str,
    context_lines: int,
    max_results: int,
) -> dict:
    root = _root(workspace)
    rg = shutil.which("rg")
    if rg is None:
        raise RuntimeError("rg is required for the baseline")
    completed = subprocess.run(
        [rg, "-n", "-F", "--glob", "*.py", symbol, str(root)],
        capture_output=True,
        text=True,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(completed.stderr.strip())
    occurrences: list[tuple[str, int]] = []
    for line in completed.stdout.splitlines():
        path_value, line_value, _ = line.split(":", 2)
        relative = Path(path_value).resolve().relative_to(root).as_posix()
        occurrences.append((relative, int(line_value)))
    occurrences.sort()
    return {
        "matches": [
            _match(root, relative, line_number, context_lines)
            for relative, line_number in occurrences[:max_results]
        ],
        "cache_hit": False,
        "process_count": 1,
    }


def apply_patch(
    workspace: str,
    patch: str,
    expected_hashes: dict[str, str],
) -> dict:
    return apply_patch_only(workspace, patch, expected_hashes)


def verify(
    workspace: str,
    changed_paths: list[str],
    checks: list[list[str]],
) -> dict:
    return verify_only(workspace, changed_paths, checks)

