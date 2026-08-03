from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Iterable


TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
INDEX_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}
MAX_INDEX_FILE_BYTES = 2_000_000


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _workspace(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"workspace is not a directory: {value}")
    return root


def _safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"path escapes workspace: {relative}")
    return path


def _iter_index_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        try:
            relative = path.relative_to(root)
            if any(part in IGNORED_PARTS for part in relative.parts):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            stat = path.stat()
        except OSError:
            continue
        if path.suffix.casefold() not in INDEX_SUFFIXES:
            continue
        if stat.st_size > MAX_INDEX_FILE_BYTES:
            continue
        yield path


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    result = {}
    for path in _iter_index_files(root):
        try:
            stat = path.stat()
        except OSError:
            continue
        result[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return result


def _bounded_text(value: str, limit: int) -> tuple[str, bool, int]:
    encoded = value.encode("utf-8")
    if len(encoded) <= limit:
        return value, False, len(encoded)
    return encoded[:limit].decode("utf-8", errors="ignore"), True, limit


def _slice(
    root: Path,
    relative: str,
    lines: list[str],
    start_line: int,
    end_line: int,
    byte_limit: int,
) -> dict[str, Any]:
    if start_line < 1 or end_line < start_line:
        raise ValueError("line range must be positive and ordered")
    start = min(start_line, max(1, len(lines)))
    end = min(end_line, len(lines))
    content = "".join(lines[start - 1 : end]) if lines else ""
    bounded, truncated, used = _bounded_text(content, byte_limit)
    return {
        "path": relative,
        "start_line": start,
        "end_line": end,
        "content": bounded,
        "content_sha256": _sha256(content.encode("utf-8")),
        "truncated": truncated,
        "bytes": used,
    }


class InspectIndex:
    def __init__(self) -> None:
        self._roots: dict[Path, dict[str, Any]] = {}

    def invalidate(self, workspace: str) -> None:
        self._roots.pop(_workspace(workspace), None)

    def _state(self, root: Path) -> tuple[dict[str, Any], bool]:
        snapshot = _snapshot(root)
        current = self._roots.get(root)
        if current is not None and current["snapshot"] == snapshot:
            return current, True

        index: dict[str, list[tuple[str, int]]] = defaultdict(list)
        files: dict[str, list[str]] = {}
        for relative in sorted(snapshot):
            path = _safe_path(root, relative)
            try:
                lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            except (OSError, UnicodeDecodeError):
                continue
            files[relative] = lines
            for line_number, line in enumerate(lines, start=1):
                for token in set(TOKEN.findall(line)):
                    index[token].append((relative, line_number))
        state = {
            "snapshot": snapshot,
            "files": files,
            "index": dict(index),
        }
        self._roots[root] = state
        return state, False

    def inspect(
        self,
        workspace: str,
        queries: list[dict[str, Any]],
        context_lines: int = 2,
        max_results: int = 20,
        max_bytes: int = 65_536,
    ) -> dict[str, Any]:
        if not isinstance(queries, list) or not queries:
            raise ValueError("queries must be a non-empty array")
        if not 0 <= context_lines <= 100:
            raise ValueError("context_lines must be between 0 and 100")
        if not 1 <= max_results <= 500:
            raise ValueError("max_results must be between 1 and 500")
        if not 1 <= max_bytes <= 1_000_000:
            raise ValueError("max_bytes must be between 1 and 1000000")

        root = _workspace(workspace)
        state, cache_hit = self._state(root)
        remaining = max_bytes
        results = []
        for query in queries:
            if not isinstance(query, dict):
                raise ValueError("each query must be an object")
            symbol = query.get("symbol")
            path_value = query.get("path")
            if bool(symbol) == bool(path_value):
                raise ValueError("each query must contain exactly one symbol or path")
            matches = []
            if symbol:
                if not isinstance(symbol, str):
                    raise ValueError("symbol must be a string")
                occurrences = state["index"].get(symbol, ())
                for relative, line_number in occurrences[:max_results]:
                    lines = state["files"][relative]
                    match = _slice(
                        root,
                        relative,
                        lines,
                        max(1, line_number - context_lines),
                        line_number + context_lines,
                        remaining,
                    )
                    remaining -= match.pop("bytes")
                    matches.append(match)
                    if remaining <= 0:
                        break
            else:
                if not isinstance(path_value, str):
                    raise ValueError("path must be a string")
                path = _safe_path(root, path_value)
                if not path.is_file() or path.is_symlink():
                    results.append(
                        {
                            "query": query,
                            "matches": [],
                            "error": f"path is not a regular file: {path_value}",
                        }
                    )
                    continue
                try:
                    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
                except UnicodeDecodeError:
                    results.append(
                        {
                            "query": query,
                            "matches": [],
                            "error": f"path is not UTF-8 text: {path_value}",
                        }
                    )
                    continue
                start = int(query.get("start_line", 1))
                end = int(query.get("end_line", len(lines)))
                match = _slice(root, path_value, lines, start, end, remaining)
                remaining -= match.pop("bytes")
                matches.append(match)
            results.append({"query": query, "matches": matches})
            if remaining <= 0:
                break
        return {
            "results": results,
            "cache_hit": cache_hit,
            "truncated": remaining <= 0,
            "indexed_files": len(state["files"]),
        }


def _patch_label(value: str, prefix: str) -> str | None:
    label = value.split("\t", 1)[0].strip()
    if label == "/dev/null":
        return None
    if not label.startswith(prefix):
        raise ValueError(f"patch path must start with {prefix}: {label}")
    return label[len(prefix) :]


def changed_paths(patch: str) -> list[str]:
    lines = patch.splitlines()
    paths: set[str] = set()
    for index, line in enumerate(lines):
        if not line.startswith("--- "):
            continue
        if index + 1 >= len(lines) or not lines[index + 1].startswith("+++ "):
            raise ValueError("malformed unified patch headers")
        old = _patch_label(line[4:], "a/")
        new = _patch_label(lines[index + 1][4:], "b/")
        if old is None and new is None:
            raise ValueError("patch entry has no path")
        if old is not None and new is not None and old != new:
            raise ValueError("renames are not supported")
        paths.add(old or new or "")
    if not paths:
        raise ValueError("patch changes no files")
    return sorted(paths)


def _validate_hashes(
    root: Path,
    paths: Iterable[str],
    expected_hashes: dict[str, str | None],
) -> None:
    for relative in paths:
        path = _safe_path(root, relative)
        if relative not in expected_hashes:
            raise ValueError(f"missing starting hash: {relative}")
        expected = expected_hashes[relative]
        actual = _sha256(path.read_bytes()) if path.is_file() else None
        if actual != expected:
            raise ValueError(f"stale starting hash: {relative}")


def _diff_hash(root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = _safe_path(root, relative)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.is_file() else b"<deleted>")
        digest.update(b"\0")
    return digest.hexdigest()


def _restore(root: Path, backups: dict[str, bytes | None]) -> None:
    for relative, content in backups.items():
        path = _safe_path(root, relative)
        if content is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _truncate(value: str | bytes | None, limit: int) -> tuple[str, bool]:
    if value is None:
        return "", False
    if isinstance(value, bytes):
        encoded = value
    else:
        encoded = value.encode("utf-8", errors="replace")
    truncated = len(encoded) > limit
    return encoded[:limit].decode("utf-8", errors="replace"), truncated


def _run_checks(
    root: Path,
    checks: list[dict[str, Any]],
    timeout_seconds: float,
    max_output_bytes: int,
) -> list[dict[str, Any]]:
    results = []
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("each check must be an object")
        argv = check.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(item, str) or "\0" in item for item in argv)
        ):
            raise ValueError("check argv must be a non-empty string array")
        timeout = float(check.get("timeout_seconds", timeout_seconds))
        if not 0.01 <= timeout <= timeout_seconds:
            raise ValueError("check timeout exceeds the apply_verify timeout")
        started = time.perf_counter_ns()
        try:
            completed = subprocess.run(
                argv,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            stdout, stdout_truncated = _truncate(completed.stdout, max_output_bytes)
            stderr, stderr_truncated = _truncate(completed.stderr, max_output_bytes)
            result = {
                "argv": argv,
                "exit_code": completed.returncode,
                "timed_out": False,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
            }
        except subprocess.TimeoutExpired as error:
            stdout, stdout_truncated = _truncate(error.stdout, max_output_bytes)
            stderr, stderr_truncated = _truncate(error.stderr, max_output_bytes)
            result = {
                "argv": argv,
                "exit_code": None,
                "timed_out": True,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
            }
        result["elapsed_ms"] = (time.perf_counter_ns() - started) / 1_000_000
        results.append(result)
        if result["timed_out"] or result["exit_code"] != 0:
            break
    return results


def apply_verify(
    workspace: str,
    patch: str,
    expected_hashes: dict[str, str | None],
    checks: list[dict[str, Any]],
    timeout_seconds: float = 120,
    max_output_bytes: int = 65_536,
) -> dict[str, Any]:
    if not isinstance(patch, str) or not patch:
        raise ValueError("patch must be a non-empty unified diff")
    if not 0.01 <= float(timeout_seconds) <= 300:
        raise ValueError("timeout_seconds must be between 0.01 and 300")
    if not 1 <= int(max_output_bytes) <= 1_000_000:
        raise ValueError("max_output_bytes must be between 1 and 1000000")
    root = _workspace(workspace)
    paths = changed_paths(patch)
    for relative in paths:
        _safe_path(root, relative)
    _validate_hashes(root, paths, expected_hashes)
    backups = {
        relative: (
            _safe_path(root, relative).read_bytes()
            if _safe_path(root, relative).is_file()
            else None
        )
        for relative in paths
    }
    started = time.perf_counter_ns()
    check_patch = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=root,
        input=patch,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    if check_patch.returncode:
        raise ValueError(f"patch check failed: {check_patch.stderr.strip()}")
    applied = subprocess.run(
        ["git", "apply", "-"],
        cwd=root,
        input=patch,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    if applied.returncode:
        _restore(root, backups)
        raise ValueError(f"patch apply failed: {applied.stderr.strip()}")
    try:
        check_results = _run_checks(
            root,
            checks,
            float(timeout_seconds),
            int(max_output_bytes),
        )
    except Exception:
        _restore(root, backups)
        raise
    failed = any(
        result["timed_out"] or result["exit_code"] != 0
        for result in check_results
    )
    diff_sha256 = _diff_hash(root, paths)
    if failed:
        _restore(root, backups)
    return {
        "patch_status": "verification_failed" if failed else "applied",
        "changed_paths": paths,
        "diff_sha256": diff_sha256,
        "checks": check_results,
        "exit_codes": [result["exit_code"] for result in check_results],
        "rolled_back": failed,
        "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000,
    }
