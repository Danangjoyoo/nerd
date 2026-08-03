#!/usr/bin/env python3
"""Reusable project map and bounded text search for Nerd UFast."""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath
import hashlib
import os
import re
import time
from typing import Any


VERSION = "0.3.0"
MAX_INDEX_FILES = 5_000
MAX_INDEX_BYTES = 16 * 1024 * 1024
MAX_RETURNED_ENTRIES = 1_000
MAX_QUERY_CHARS = 500
MAX_RESULTS = 50
MAX_PREVIEW_CHARS = 2_000
PROTECTED_FILES = frozenset({"lint_check.py", "verify_behavior.py"})
EXCLUDED_DIRECTORIES = frozenset(
    {
        ".agents",
        ".claude",
        ".codex",
        ".cursor",
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "target",
    }
)


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1_000))


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _normalized_paths(value: object) -> set[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) > 200:
        raise ValueError("paths must be an array of at most 200 normalized paths")
    normalized: set[str] = set()
    for raw in value:
        if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
            raise ValueError("paths must contain normalized non-empty strings")
        path = PurePosixPath(raw)
        if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
            raise ValueError(f"Path traversal is not allowed: {raw!r}")
        normalized.add(path.as_posix())
    return normalized


class ProjectIndex:
    """Cache generic UTF-8 project content for map and search operations."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser().resolve()
        self._signature: tuple[tuple[str, int, int], ...] | None = None
        self._records: dict[str, dict[str, Any]] = {}
        self._index_id = ""
        self._total_bytes = 0
        self._skipped_files = 0

    def _candidates(self) -> tuple[list[Path], tuple[tuple[str, int, int], ...], int]:
        paths: list[Path] = []
        signature: list[tuple[str, int, int]] = []
        skipped = 0
        for current, directories, names in os.walk(self.root, followlinks=False):
            current_path = Path(current)
            directories[:] = sorted(
                directory
                for directory in directories
                if directory not in EXCLUDED_DIRECTORIES
                and (not directory.startswith(".") or directory == ".github")
            )
            for name in sorted(names):
                if (
                    name.startswith(".")
                    or name in PROTECTED_FILES
                    or Path(name).suffix in {".pyc", ".pyo"}
                ):
                    skipped += 1
                    continue
                path = current_path / name
                if path.is_symlink() or not path.is_file():
                    skipped += 1
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    skipped += 1
                    continue
                relative = path.relative_to(self.root).as_posix()
                paths.append(path)
                signature.append((relative, stat.st_mtime_ns, stat.st_size))
        return paths, tuple(signature), skipped

    def _refresh(self, *, refresh: bool = False) -> tuple[str, str | None]:
        if not self.root.is_dir():
            return "rebuilt", "The configured workspace is not a directory"
        paths, signature, skipped = self._candidates()
        if not refresh and self._signature == signature and self._records:
            return "hit", None
        if len(paths) > MAX_INDEX_FILES:
            return "rebuilt", f"Project exceeds the {MAX_INDEX_FILES}-file index limit"
        if sum(size for _, _, size in signature) > MAX_INDEX_BYTES:
            return "rebuilt", f"Project exceeds the {MAX_INDEX_BYTES}-byte index limit"

        records: dict[str, dict[str, Any]] = {}
        total_bytes = 0
        for path in paths:
            try:
                body = path.read_bytes()
            except OSError:
                skipped += 1
                continue
            if b"\x00" in body:
                skipped += 1
                continue
            try:
                content = body.decode("utf-8")
            except UnicodeDecodeError:
                skipped += 1
                continue
            relative = path.relative_to(self.root).as_posix()
            total_bytes += len(body)
            records[relative] = {
                "path": relative,
                "sha256": _digest(body),
                "bytes": len(body),
                "lines": len(content.splitlines()),
                "suffix": path.suffix.casefold() or "[none]",
                "content": content,
            }
        self._signature = signature
        self._records = records
        self._total_bytes = total_bytes
        self._skipped_files = skipped
        identity = "\n".join(
            f"{path}:{record['sha256']}" for path, record in sorted(records.items())
        )
        self._index_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        return "rebuilt", None

    def project_index(
        self,
        *,
        refresh: bool = False,
        max_entries: int = 200,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        if not isinstance(max_entries, int) or isinstance(max_entries, bool):
            max_entries = 200
        max_entries = min(MAX_RETURNED_ENTRIES, max(1, max_entries))
        cache_status, error = self._refresh(refresh=refresh)
        if error is not None:
            return {
                "status": "unsupported",
                "runtime_version": VERSION,
                "operation_ms": _elapsed_ms(started),
                "reason": error,
                "cache_status": cache_status,
                "files": [],
            }
        ordered = [self._records[path] for path in sorted(self._records)]
        files = [
            {key: value for key, value in record.items() if key != "content"}
            for record in ordered[:max_entries]
        ]
        return {
            "status": "ready",
            "runtime_version": VERSION,
            "operation_ms": _elapsed_ms(started),
            "backend": "memory_project_map",
            "cache_status": cache_status,
            "index_id": self._index_id,
            "total_files": len(ordered),
            "total_bytes": self._total_bytes,
            "skipped_files": self._skipped_files,
            "file_types": dict(sorted(Counter(item["suffix"] for item in ordered).items())),
            "files": files,
            "truncated": len(ordered) > len(files),
        }

    def fast_search(
        self,
        query: object = None,
        *,
        queries: object = None,
        mode: object = "literal",
        case_sensitive: object = False,
        paths: object = None,
        max_results: object = 20,
        context_lines: object = 2,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            if (query is None) == (queries is None):
                raise ValueError("Exactly one of query or queries is required")
            if query is not None:
                raw_queries = [query]
            else:
                if not isinstance(queries, list) or not 1 <= len(queries) <= 10:
                    raise ValueError("queries must contain between 1 and 10 strings")
                raw_queries = queries
            if any(
                not isinstance(value, str)
                or not value
                or len(value) > MAX_QUERY_CHARS
                for value in raw_queries
            ):
                raise ValueError(
                    f"Each query must be a non-empty string of at most {MAX_QUERY_CHARS} characters"
                )
            if len(set(raw_queries)) != len(raw_queries):
                raise ValueError("queries must not contain duplicates")
            if mode not in {"literal", "regex"}:
                raise ValueError("mode must be 'literal' or 'regex'")
            if not isinstance(case_sensitive, bool):
                raise ValueError("case_sensitive must be a boolean")
            selected_paths = _normalized_paths(paths)
            if not isinstance(max_results, int) or isinstance(max_results, bool):
                raise ValueError("max_results must be an integer")
            max_results = min(MAX_RESULTS, max(1, max_results))
            if not isinstance(context_lines, int) or isinstance(context_lines, bool):
                raise ValueError("context_lines must be an integer")
            context_lines = min(5, max(0, context_lines))
            flags = 0 if case_sensitive else re.IGNORECASE
            patterns = [
                (
                    value,
                    re.compile(re.escape(value) if mode == "literal" else value, flags),
                )
                for value in raw_queries
            ]
        except re.error as error:
            return {
                "status": "rejected",
                "runtime_version": VERSION,
                "operation_ms": _elapsed_ms(started),
                "reason": f"Invalid regular expression: {error}",
                "matches": [],
            }
        except ValueError as error:
            return {
                "status": "rejected",
                "runtime_version": VERSION,
                "operation_ms": _elapsed_ms(started),
                "reason": str(error),
                "matches": [],
            }

        cache_status, error = self._refresh()
        if error is not None:
            return {
                "status": "unsupported",
                "runtime_version": VERSION,
                "operation_ms": _elapsed_ms(started),
                "reason": error,
                "cache_status": cache_status,
                "matches": [],
            }

        matches: list[dict[str, Any]] = []
        total_matches = 0
        query_counts = {value: 0 for value in raw_queries}
        for path, record in sorted(self._records.items()):
            if selected_paths is not None and path not in selected_paths:
                continue
            lines = record["content"].splitlines()
            for line_number, line in enumerate(lines, 1):
                for query_value, pattern in patterns:
                    found = pattern.search(line)
                    if found is None:
                        continue
                    total_matches += 1
                    query_counts[query_value] += 1
                    if len(matches) >= max_results:
                        continue
                    start = max(0, line_number - 1 - context_lines)
                    end = min(len(lines), line_number + context_lines)
                    preview = "\n".join(lines[start:end])[:MAX_PREVIEW_CHARS]
                    matches.append(
                        {
                            "query": query_value,
                            "path": path,
                            "line": line_number,
                            "column": found.start() + 1,
                            "preview": preview,
                            "sha256": record["sha256"],
                        }
                    )
        return {
            "status": "matched" if matches else "no_match",
            "runtime_version": VERSION,
            "operation_ms": _elapsed_ms(started),
            "backend": "memory_project_map",
            "cache_status": cache_status,
            "index_id": self._index_id,
            "queries": raw_queries,
            "query_counts": query_counts,
            "match_count": total_matches,
            "matches": matches,
            "truncated": total_matches > len(matches),
        }
