from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Iterable


TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _root(value: str) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise ValueError(f"workspace is not a directory: {value}")
    return root


def _safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"path escapes workspace: {relative}")
    return path


def _match(root: Path, relative: str, line_number: int, context: int) -> dict:
    path = _safe_path(root, relative)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = max(1, line_number - context)
    end = min(len(lines), line_number + context)
    content = "".join(lines[start - 1 : end])
    return {
        "path": relative,
        "start_line": start,
        "end_line": end,
        "content": content,
        "content_sha256": _sha256(content.encode("utf-8")),
        "truncated": False,
    }


class InspectIndex:
    def __init__(self) -> None:
        self._roots: dict[Path, dict[str, list[tuple[str, int]]]] = {}

    def _build(self, root: Path) -> dict[str, list[tuple[str, int]]]:
        index: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for token in set(TOKEN.findall(line)):
                    index[token].append((relative, line_number))
        return dict(index)

    def inspect(
        self,
        workspace: str,
        symbol: str,
        context_lines: int,
        max_results: int,
    ) -> dict:
        root = _root(workspace)
        index = self._roots.get(root)
        cache_hit = index is not None
        if index is None:
            index = self._build(root)
            self._roots[root] = index
        occurrences = sorted(index.get(symbol, ()))[:max_results]
        return {
            "matches": [
                _match(root, relative, line_number, context_lines)
                for relative, line_number in occurrences
            ],
            "cache_hit": cache_hit,
            "process_count": 0,
        }


def changed_paths(patch: str) -> list[str]:
    paths = []
    for line in patch.splitlines():
        if not line.startswith("+++ b/"):
            continue
        relative = line[6:]
        if relative == "/dev/null" or relative in paths:
            continue
        paths.append(relative)
    if not paths:
        raise ValueError("patch changes no files")
    return sorted(paths)


def _validate_hashes(
    root: Path,
    paths: Iterable[str],
    expected_hashes: dict[str, str],
) -> None:
    for relative in paths:
        path = _safe_path(root, relative)
        expected = expected_hashes.get(relative)
        if expected is None:
            raise ValueError(f"missing starting hash: {relative}")
        actual = _sha256(path.read_bytes())
        if actual != expected:
            raise ValueError(f"stale starting hash: {relative}")


def _diff_hash(root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = _safe_path(root, relative)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _apply(
    workspace: str,
    patch: str,
    expected_hashes: dict[str, str],
) -> tuple[Path, list[str], dict[str, bytes], int]:
    root = _root(workspace)
    paths = changed_paths(patch)
    _validate_hashes(root, paths, expected_hashes)
    backups = {relative: _safe_path(root, relative).read_bytes() for relative in paths}
    check = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=root,
        input=patch,
        capture_output=True,
        text=True,
    )
    if check.returncode:
        raise ValueError(f"patch check failed: {check.stderr.strip()}")
    applied = subprocess.run(
        ["git", "apply", "-"],
        cwd=root,
        input=patch,
        capture_output=True,
        text=True,
    )
    if applied.returncode:
        raise ValueError(f"patch apply failed: {applied.stderr.strip()}")
    return root, paths, backups, 2


def apply_patch_only(
    workspace: str,
    patch: str,
    expected_hashes: dict[str, str],
) -> dict:
    root, paths, _, process_count = _apply(workspace, patch, expected_hashes)
    return {
        "patch_status": "applied",
        "changed_paths": paths,
        "diff_sha256": _diff_hash(root, paths),
        "process_count": process_count,
    }


def _run_checks(root: Path, checks: list[list[str]]) -> tuple[list[dict], int]:
    results = []
    for command in checks:
        if not command or command[0] != "python3":
            raise ValueError("experiment checks must use python3 without a shell")
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
        )
        results.append(
            {
                "command": command,
                "exit_code": completed.returncode,
            }
        )
    return results, len(checks)


def verify_only(
    workspace: str,
    changed_paths_value: list[str],
    checks: list[list[str]],
) -> dict:
    root = _root(workspace)
    paths = sorted(changed_paths_value)
    for relative in paths:
        _safe_path(root, relative)
    results, process_count = _run_checks(root, checks)
    return {
        "diff_sha256": _diff_hash(root, paths),
        "checks": results,
        "exit_codes": [item["exit_code"] for item in results],
        "process_count": process_count,
    }


def _restore(root: Path, backups: dict[str, bytes]) -> None:
    for relative, content in backups.items():
        _safe_path(root, relative).write_bytes(content)


def apply_verify(
    workspace: str,
    patch: str,
    expected_hashes: dict[str, str],
    checks: list[list[str]],
) -> dict:
    root, paths, backups, apply_processes = _apply(
        workspace, patch, expected_hashes
    )
    results, check_processes = _run_checks(root, checks)
    failed = any(item["exit_code"] != 0 for item in results)
    diff_sha256 = _diff_hash(root, paths)
    if failed:
        _restore(root, backups)
    return {
        "patch_status": "verification_failed" if failed else "applied",
        "changed_paths": paths,
        "diff_sha256": diff_sha256,
        "checks": results,
        "exit_codes": [item["exit_code"] for item in results],
        "rolled_back": failed,
        "process_count": apply_processes + check_processes,
    }


def canonical_apply(result: dict) -> dict:
    return {
        "patch_status": result["patch_status"],
        "changed_paths": result["changed_paths"],
        "diff_sha256": result["diff_sha256"],
        "checks": result["checks"],
        "exit_codes": result["exit_codes"],
        "rolled_back": result["rolled_back"],
    }

