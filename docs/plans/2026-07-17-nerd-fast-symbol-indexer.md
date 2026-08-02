# Nerd Fast Optional Symbol Indexer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task inline. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional, persistent symbol index to `nerd-fast` that makes repeated exact-symbol navigation cheaper without making Universal Ctags a mandatory dependency or replacing source confirmation.

**Architecture:** Bundle one Python 3 script with `nerd-fast`. The script uses Universal Ctags JSON output only during explicit incremental refreshes, stores normalized symbol definitions and file fingerprints in a workspace-keyed SQLite cache outside the workspace, and serves exact lookups without rescanning or rebuilding. `nerd-fast` selects the index only when expected reuse amortizes refresh cost and otherwise falls back to exact-file reads or narrow text search.

**Tech Stack:** Python 3.12 standard library, SQLite, optional Universal Ctags with JSON support, Git file enumeration when available, `unittest`

## Global Constraints

- Keep Universal Ctags optional; never install it automatically or fail the skill when it is unavailable.
- Verify both `Universal Ctags` identity and the `json` feature before attempting index generation.
- Keep cache files outside the target workspace and key them by the canonical workspace path.
- Never rebuild or refresh the index as part of a warm `find` query.
- Refresh only added, changed, or deleted files by comparing `st_mtime_ns` and size against stored fingerprints.
- Prefer `git ls-files -co --exclude-standard -z` for ignore-aware enumeration; fall back to a bounded filesystem walk outside Git repositories.
- Treat Ctags results as definition-oriented navigation candidates, not complete semantic references; confirm source before mutation.
- Emit machine-readable JSON on stdout and actionable diagnostics on stderr.
- Do not add a persistent daemon in the MVP. Measure process startup and warm query latency before approving a daemon or interactive Ctags process.
- Do not promise a universal latency threshold. Record cold refresh, no-change refresh, warm lookup, and narrow-search comparison measurements on the active machine.
- Resolve the bundled script relative to the installed `nerd-fast/SKILL.md`; never assume the repository checkout path.

---

## File Structure

- Create `skills/nerd-fast/scripts/symbol_index.py`: cache path selection, SQLite schema, Ctags capability detection, ignore-aware file discovery, incremental refresh, exact query, and CLI.
- Create `tests/test_fast_symbol_index.py`: deterministic cache, parser, refresh, deletion, CLI, and failure-path tests that do not require Universal Ctags on CI.
- Create `benchmarks/symbol_index.py`: local cold/warm latency measurement without a CI timing gate.
- Modify `skills/nerd-fast/SKILL.md`: document optional indexed navigation, amortization, source confirmation, and fallback behavior.
- Modify `docs/superpowers/specs/2026-07-16-nerd-fast-design.md`: replace the scriptless package decision with the optional indexer boundary and benchmark acceptance rule.
- Modify `tests/test_skill_contracts.py`: enforce the runtime index-selection language and bundled-script invocation boundary.
- Modify `scripts/validate_skills.py`: require the published `nerd-fast/scripts/symbol_index.py` resource.
- Modify `tests/test_skill_structure.py`: enforce exact script ownership without adding a reference file or license.

---

### Task 1: Build the persistent cache and exact-query core

**Files:**
- Create: `tests/test_fast_symbol_index.py`
- Create: `skills/nerd-fast/scripts/symbol_index.py`

**Interfaces:**
- Produces: `default_cache_path(root: Path) -> Path`
- Produces: `connect_cache(path: Path) -> sqlite3.Connection`
- Produces: `initialize_schema(connection: sqlite3.Connection, root: Path) -> None`
- Produces: `replace_file_symbols(connection, relative_path, fingerprint, symbols) -> None`
- Produces: `find_symbol(connection, name: str, limit: int = 50) -> list[dict[str, object]]`
- Consumes later: incremental refresh writes through `replace_file_symbols`; CLI lookup calls `find_symbol` without a filesystem scan.

- [ ] **Step 1: Write failing cache and query tests**

Create `tests/test_fast_symbol_index.py` with this loader and first test class:

```python
from __future__ import annotations

from pathlib import Path
import importlib.util
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "nerd-fast" / "scripts" / "symbol_index.py"


def load_indexer():
    spec = importlib.util.spec_from_file_location("nerd_fast_symbol_index", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CacheContractTests(unittest.TestCase):
    def test_cache_is_outside_workspace_and_stable_for_canonical_root(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            first = indexer.default_cache_path(root)
            second = indexer.default_cache_path(root / ".")
            self.assertEqual(first, second)
            self.assertFalse(first.is_relative_to(root))
            self.assertEqual(first.name, "index.sqlite3")

    def test_replace_is_idempotent_and_find_is_exact(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "index.sqlite3"
            connection = indexer.connect_cache(cache)
            indexer.initialize_schema(connection, Path(directory))
            symbols = [
                {
                    "name": "Widget",
                    "path": "src/widget.py",
                    "line": 7,
                    "kind": "class",
                    "scope": None,
                    "language": "Python",
                    "signature": None,
                }
            ]
            indexer.replace_file_symbols(
                connection,
                "src/widget.py",
                indexer.FileFingerprint(mtime_ns=10, size=20),
                symbols,
            )
            indexer.replace_file_symbols(
                connection,
                "src/widget.py",
                indexer.FileFingerprint(mtime_ns=10, size=20),
                symbols,
            )
            self.assertEqual(indexer.find_symbol(connection, "Widget"), symbols)
            self.assertEqual(indexer.find_symbol(connection, "Wid"), [])
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.CacheContractTests -v
```

Expected: `ERROR` because `skills/nerd-fast/scripts/symbol_index.py` does not exist.

- [ ] **Step 3: Implement cache paths, schema, replacement, and exact lookup**

Create `skills/nerd-fast/scripts/symbol_index.py` with these definitions:

```python
#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import hashlib
import json
import os
import sqlite3
import sys


SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class FileFingerprint:
    mtime_ns: int
    size: int


def _cache_base() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"])
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches"
    if os.environ.get("XDG_CACHE_HOME"):
        return Path(os.environ["XDG_CACHE_HOME"])
    return Path.home() / ".cache"


def default_cache_path(root: Path) -> Path:
    canonical = root.resolve()
    key = hashlib.sha256(os.fsencode(canonical)).hexdigest()[:20]
    return _cache_base() / "nerd" / "symbol-index" / key / "index.sqlite3"


def connect_cache(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


def initialize_schema(connection: sqlite3.Connection, root: Path) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            mtime_ns INTEGER NOT NULL,
            size INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS symbols (
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            line INTEGER NOT NULL,
            kind TEXT,
            scope TEXT,
            language TEXT,
            signature TEXT,
            FOREIGN KEY(path) REFERENCES files(path) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS symbols_name_idx ON symbols(name);
        CREATE INDEX IF NOT EXISTS symbols_path_idx ON symbols(path);
        """
    )
    expected = {
        "schema_version": SCHEMA_VERSION,
        "root": str(root.resolve()),
    }
    existing = dict(connection.execute("SELECT key, value FROM metadata"))
    if existing and existing != expected:
        raise RuntimeError("symbol index metadata does not match this workspace")
    connection.executemany(
        "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
        expected.items(),
    )
    connection.commit()


def replace_file_symbols(
    connection: sqlite3.Connection,
    relative_path: str,
    fingerprint: FileFingerprint,
    symbols: Iterable[Mapping[str, object]],
) -> None:
    rows = [dict(symbol) for symbol in symbols]
    with connection:
        connection.execute("DELETE FROM symbols WHERE path = ?", (relative_path,))
        connection.execute(
            "INSERT OR REPLACE INTO files(path, mtime_ns, size) VALUES (?, ?, ?)",
            (relative_path, fingerprint.mtime_ns, fingerprint.size),
        )
        connection.executemany(
            """
            INSERT INTO symbols(name, path, line, kind, scope, language, signature)
            VALUES (:name, :path, :line, :kind, :scope, :language, :signature)
            """,
            rows,
        )


def find_symbol(
    connection: sqlite3.Connection,
    name: str,
    limit: int = 50,
) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT name, path, line, kind, scope, language, signature
        FROM symbols
        WHERE name = ?
        ORDER BY path, line
        LIMIT ?
        """,
        (name, limit),
    )
    return [dict(row) for row in rows]
```

- [ ] **Step 4: Run the cache tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.CacheContractTests -v
```

Expected: both tests pass; the second replacement does not duplicate `Widget`.

- [ ] **Step 5: Commit the persistent cache core**

```bash
git add skills/nerd-fast/scripts/symbol_index.py tests/test_fast_symbol_index.py
git commit -m "feat: add nerd fast symbol cache"
```

---

### Task 2: Add strict Universal Ctags capability detection and JSON parsing

**Files:**
- Modify: `tests/test_fast_symbol_index.py`
- Modify: `skills/nerd-fast/scripts/symbol_index.py`

**Interfaces:**
- Produces: `require_universal_ctags(binary: str) -> None`
- Produces: `parse_ctags_json(lines: Iterable[str], root: Path) -> list[dict[str, object]]`
- Produces: `generate_tags(binary: str, root: Path, paths: list[str]) -> list[dict[str, object]]`
- Consumes: Universal Ctags JSON Lines fields `name`, `path`, `line`, `kind`, `scope`, `language`, and `signature`.

- [ ] **Step 1: Add failing capability and parser tests**

Append this class to `tests/test_fast_symbol_index.py`:

```python
class CtagsContractTests(unittest.TestCase):
    def test_rejects_non_universal_or_non_json_ctags(self):
        indexer = load_indexer()

        def bsd_runner(*args, **kwargs):
            return indexer.subprocess.CompletedProcess(
                args[0], 0, stdout="Exuberant Ctags 5.8\n", stderr=""
            )

        with self.assertRaisesRegex(RuntimeError, "Universal Ctags"):
            indexer.require_universal_ctags("ctags", runner=bsd_runner)

        calls = iter(
            (
                indexer.subprocess.CompletedProcess(
                    ["ctags", "--version"],
                    0,
                    stdout="Universal Ctags 6.2.0\n",
                    stderr="",
                ),
                indexer.subprocess.CompletedProcess(
                    ["ctags", "--list-features"],
                    0,
                    stdout="wildcards\n",
                    stderr="",
                ),
            )
        )
        with self.assertRaisesRegex(RuntimeError, "JSON"):
            indexer.require_universal_ctags(
                "ctags", runner=lambda *args, **kwargs: next(calls)
            )

    def test_parses_only_tag_records_and_normalizes_paths(self):
        indexer = load_indexer()
        lines = [
            '{"_type":"ptag","name":"JSON_OUTPUT_VERSION","path":"1.0"}\n',
            '{"_type":"tag","name":"Widget","path":"src/widget.py",'
            '"line":7,"kind":"class","language":"Python"}\n',
        ]
        parsed = indexer.parse_ctags_json(lines, Path("/workspace"))
        self.assertEqual(
            parsed,
            [
                {
                    "name": "Widget",
                    "path": "src/widget.py",
                    "line": 7,
                    "kind": "class",
                    "scope": None,
                    "language": "Python",
                    "signature": None,
                }
            ],
        )
```

- [ ] **Step 2: Run the Ctags tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.CtagsContractTests -v
```

Expected: `ERROR` because the capability and parser functions do not exist.

- [ ] **Step 3: Implement capability detection and safe JSON parsing**

Add these imports and definitions to `symbol_index.py`:

```python
import subprocess
import tempfile


def require_universal_ctags(binary: str, runner=subprocess.run) -> None:
    try:
        version = runner(
            [binary, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise RuntimeError(
            f"Universal Ctags executable is unavailable: {binary}"
        ) from error
    if version.returncode != 0 or "Universal Ctags" not in version.stdout:
        raise RuntimeError("Universal Ctags is required for indexed refresh")
    features = runner(
        [binary, "--list-features"],
        capture_output=True,
        text=True,
        check=False,
    )
    available = {line.strip().casefold() for line in features.stdout.splitlines()}
    if features.returncode != 0 or "json" not in available:
        raise RuntimeError("Universal Ctags JSON support is required for indexed refresh")


def parse_ctags_json(lines: Iterable[str], root: Path) -> list[dict[str, object]]:
    parsed: list[dict[str, object]] = []
    for line in lines:
        if not line.strip():
            continue
        value = json.loads(line)
        if value.get("_type") != "tag" or not value.get("name"):
            continue
        path = Path(str(value["path"]))
        if path.is_absolute():
            path = path.resolve().relative_to(root.resolve())
        parsed.append(
            {
                "name": str(value["name"]),
                "path": path.as_posix(),
                "line": int(value["line"]),
                "kind": value.get("kind"),
                "scope": value.get("scope"),
                "language": value.get("language"),
                "signature": value.get("signature"),
            }
        )
    return parsed


def _ctags_operand(path: str) -> str:
    return path if os.path.isabs(path) else f"./{path}"


def _line_list_safe(path: str) -> bool:
    return "\n" not in path and "\r" not in path and not path[-1:].isspace()


def _generate_tag_batch(
    binary: str,
    root: Path,
    paths: list[str],
) -> list[dict[str, object]]:
    command = [
        binary,
        "--output-format=json",
        "--fields=+nsS-P",
        "--sort=no",
        *(_ctags_operand(path) for path in paths),
    ]
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as errors:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=errors,
            text=True,
            bufsize=1,
        )
        if process.stdout is None:
            raise RuntimeError("Universal Ctags stdout pipe was not created")
        try:
            parsed = parse_ctags_json(process.stdout, root)
        finally:
            process.stdout.close()
        returncode = process.wait()
        if returncode != 0:
            errors.seek(0)
            detail = errors.read().strip()
            raise RuntimeError(f"Universal Ctags failed ({returncode}): {detail}")
    return parsed


def _generate_tag_list(
    binary: str,
    root: Path,
    paths: list[str],
) -> list[dict[str, object]]:
    command = [
        binary,
        "--output-format=json",
        "--fields=+nsS-P",
        "--sort=no",
        "-L",
        "-",
    ]
    with (
        tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as inputs,
        tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as errors,
    ):
        inputs.writelines(f"{_ctags_operand(path)}\n" for path in paths)
        inputs.seek(0)
        process = subprocess.Popen(
            command,
            cwd=root,
            stdin=inputs,
            stdout=subprocess.PIPE,
            stderr=errors,
            text=True,
            bufsize=1,
        )
        if process.stdout is None:
            raise RuntimeError("Universal Ctags stdout pipe was not created")
        try:
            parsed = parse_ctags_json(process.stdout, root)
        finally:
            process.stdout.close()
        returncode = process.wait()
        if returncode != 0:
            errors.seek(0)
            detail = errors.read().strip()
            raise RuntimeError(f"Universal Ctags failed ({returncode}): {detail}")
    return parsed


def generate_tags(binary: str, root: Path, paths: list[str]) -> list[dict[str, object]]:
    if len(paths) > 200 and all(_line_list_safe(path) for path in paths):
        return _generate_tag_list(binary, root, paths)
    parsed: list[dict[str, object]] = []
    for start in range(0, len(paths), 200):
        parsed.extend(_generate_tag_batch(binary, root, paths[start : start + 200]))
    return parsed
```

- [ ] **Step 4: Run focused and cache tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.CtagsContractTests -v
python3 -m unittest tests.test_fast_symbol_index -v
```

Expected: all five tests pass without invoking the host machine's `ctags` binary.

- [ ] **Step 5: Commit capability detection and parsing**

```bash
git add skills/nerd-fast/scripts/symbol_index.py tests/test_fast_symbol_index.py
git commit -m "feat: parse universal ctags symbols"
```

---

### Task 3: Implement ignore-aware incremental refresh

**Files:**
- Modify: `tests/test_fast_symbol_index.py`
- Modify: `skills/nerd-fast/scripts/symbol_index.py`

**Interfaces:**
- Produces: `enumerate_files(root: Path) -> list[str]`
- Produces: `fingerprint(path: Path) -> FileFingerprint`
- Produces: `refresh_index(connection, root, tag_provider) -> dict[str, int]`
- Guarantees: deleted files remove their symbols; unchanged files never reach `tag_provider`; failed generation leaves prior cache rows unchanged.

- [ ] **Step 1: Add a failing changed/deleted-file test**

Append this class to `tests/test_fast_symbol_index.py`:

```python
class RefreshContractTests(unittest.TestCase):
    def test_refresh_indexes_only_changes_and_removes_deleted_files(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            source = root / "widget.py"
            source.write_text("class Widget:\n    pass\n", encoding="utf-8")
            cache = Path(directory) / "cache" / "index.sqlite3"
            connection = indexer.connect_cache(cache)
            indexer.initialize_schema(connection, root)
            calls: list[list[str]] = []

            def tags(paths: list[str]):
                calls.append(paths)
                return [
                    {
                        "name": "Widget",
                        "path": "widget.py",
                        "line": 1,
                        "kind": "class",
                        "scope": None,
                        "language": "Python",
                        "signature": None,
                    }
                ]

            first = indexer.refresh_index(
                connection,
                root,
                tags,
                files=["widget.py"],
            )
            second = indexer.refresh_index(
                connection,
                root,
                tags,
                files=["widget.py"],
            )
            source.unlink()
            third = indexer.refresh_index(connection, root, tags, files=[])

            self.assertEqual(calls, [["widget.py"]])
            self.assertEqual(first, {"changed": 1, "removed": 0})
            self.assertEqual(second, {"changed": 0, "removed": 0})
            self.assertEqual(third, {"changed": 0, "removed": 1})
            self.assertEqual(indexer.find_symbol(connection, "Widget"), [])
```

- [ ] **Step 2: Run the refresh test and verify RED**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.RefreshContractTests -v
```

Expected: `ERROR` because `refresh_index` does not exist.

- [ ] **Step 3: Implement enumeration, fingerprints, and transactional refresh**

Add these definitions to `symbol_index.py`:

```python
DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
}


def enumerate_files(root: Path) -> list[str]:
    git = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
        capture_output=True,
        check=False,
    )
    if git.returncode == 0:
        return sorted(
            os.fsdecode(value)
            for value in git.stdout.split(b"\0")
            if value
        )

    discovered: list[str] = []
    for directory, names, files in os.walk(root):
        names[:] = sorted(name for name in names if name not in DEFAULT_EXCLUDED_DIRS)
        base = Path(directory)
        for name in sorted(files):
            path = base / name
            if path.is_symlink() or not path.is_file():
                continue
            discovered.append(path.relative_to(root).as_posix())
    return discovered


def fingerprint(path: Path) -> FileFingerprint:
    stat = path.stat()
    return FileFingerprint(mtime_ns=stat.st_mtime_ns, size=stat.st_size)


def refresh_index(
    connection: sqlite3.Connection,
    root: Path,
    tag_provider,
    *,
    files: list[str] | None = None,
) -> dict[str, int]:
    current_paths = enumerate_files(root) if files is None else sorted(files)
    current = {path: fingerprint(root / path) for path in current_paths}
    stored = {
        row["path"]: FileFingerprint(row["mtime_ns"], row["size"])
        for row in connection.execute("SELECT path, mtime_ns, size FROM files")
    }
    changed = [path for path, value in current.items() if stored.get(path) != value]
    removed = sorted(set(stored) - set(current))
    generated = tag_provider(changed) if changed else []
    by_path: dict[str, list[dict[str, object]]] = {path: [] for path in changed}
    for symbol in generated:
        path = str(symbol["path"])
        if path in by_path:
            by_path[path].append(symbol)

    with connection:
        for path in removed:
            connection.execute("DELETE FROM symbols WHERE path = ?", (path,))
            connection.execute("DELETE FROM files WHERE path = ?", (path,))
        for path in changed:
            connection.execute("DELETE FROM symbols WHERE path = ?", (path,))
            connection.execute(
                "INSERT OR REPLACE INTO files(path, mtime_ns, size) VALUES (?, ?, ?)",
                (path, current[path].mtime_ns, current[path].size),
            )
            connection.executemany(
                """
                INSERT INTO symbols(name, path, line, kind, scope, language, signature)
                VALUES (:name, :path, :line, :kind, :scope, :language, :signature)
                """,
                by_path[path],
            )
    return {"changed": len(changed), "removed": len(removed)}
```

- [ ] **Step 4: Run all indexer tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index -v
```

Expected: all tests pass; the tag provider is called once across the three refreshes.

- [ ] **Step 5: Commit incremental refresh**

```bash
git add skills/nerd-fast/scripts/symbol_index.py tests/test_fast_symbol_index.py
git commit -m "feat: refresh symbol index incrementally"
```

---

### Task 4: Add the JSON CLI and optional-dependency failure path

**Files:**
- Modify: `tests/test_fast_symbol_index.py`
- Modify: `skills/nerd-fast/scripts/symbol_index.py`

**Interfaces:**
- Produces: `ensure --root PATH [--cache PATH] [--ctags BINARY]`
- Produces: `find NAME --root PATH [--cache PATH] [--limit N]`
- Produces: `status --root PATH [--cache PATH]`
- Produces: `invalidate --root PATH [--cache PATH]`
- Exit codes: `0` success, `2` invalid invocation or unavailable Ctags during refresh, `3` missing index for lookup.

- [ ] **Step 1: Add failing CLI tests for warm lookup and missing Ctags**

Append this class and import to `tests/test_fast_symbol_index.py`:

```python
import json
import subprocess


class CliContractTests(unittest.TestCase):
    def test_find_reads_existing_cache_without_refreshing(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            cache = Path(directory) / "index.sqlite3"
            connection = indexer.connect_cache(cache)
            indexer.initialize_schema(connection, root)
            indexer.replace_file_symbols(
                connection,
                "widget.py",
                indexer.FileFingerprint(1, 1),
                [
                    {
                        "name": "Widget",
                        "path": "widget.py",
                        "line": 1,
                        "kind": "class",
                        "scope": None,
                        "language": "Python",
                        "signature": None,
                    }
                ],
            )
            connection.close()
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "find",
                    "Widget",
                    "--root",
                    str(root),
                    "--cache",
                    str(cache),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(json.loads(result.stdout)["matches"][0]["line"], 1)

    def test_ensure_reports_unavailable_ctags_without_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "ensure",
                    "--root",
                    directory,
                    "--ctags",
                    "definitely-missing-universal-ctags",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Universal Ctags", result.stderr)
```

- [ ] **Step 2: Run the CLI tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.CliContractTests -v
```

Expected: `FAIL` because the script has no command-line interface.

- [ ] **Step 3: Implement CLI parsing and JSON output**

Add these imports and definitions to `symbol_index.py`, then invoke `main()` under the standard module guard:

```python
import argparse
import shutil


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent exact-symbol index")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("ensure", "find", "status", "invalidate"):
        command = subparsers.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--cache", type=Path)
    subparsers.choices["ensure"].add_argument("--ctags", default="ctags")
    subparsers.choices["find"].add_argument("name")
    subparsers.choices["find"].add_argument("--limit", type=int, default=50)
    return parser


def _resolved_cache(args) -> Path:
    return args.cache if args.cache is not None else default_cache_path(args.root)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    cache = _resolved_cache(args)
    if args.command == "invalidate":
        cache.unlink(missing_ok=True)
        print(json.dumps({"status": "invalidated", "cache": str(cache)}))
        return 0
    if args.command == "find" and not cache.is_file():
        print("symbol index is missing; run ensure or use narrow text search", file=sys.stderr)
        return 3

    connection = connect_cache(cache)
    try:
        initialize_schema(connection, root)
        if args.command == "find":
            print(
                json.dumps(
                    {"query": args.name, "matches": find_symbol(connection, args.name, args.limit)},
                    separators=(",", ":"),
                )
            )
            return 0
        if args.command == "status":
            files = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            symbols = connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            print(json.dumps({"files": files, "symbols": symbols, "cache": str(cache)}))
            return 0
        require_universal_ctags(args.ctags)
        result = refresh_index(
            connection,
            root,
            lambda paths: generate_tags(args.ctags, root, paths),
        )
        print(json.dumps({"status": "ready", **result, "cache": str(cache)}))
        return 0
    except (OSError, RuntimeError, sqlite3.Error, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI and complete indexer tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_fast_symbol_index.CliContractTests -v
python3 -m unittest tests.test_fast_symbol_index -v
```

Expected: all tests pass; the missing dependency exits `2` and does not modify the workspace.

- [ ] **Step 5: Commit the CLI**

```bash
git add skills/nerd-fast/scripts/symbol_index.py tests/test_fast_symbol_index.py
git commit -m "feat: expose optional symbol index cli"
```

---

### Task 5: Measure cold refresh and warm lookup without a CI timing gate

**Files:**
- Create: `benchmarks/symbol_index.py`

**Interfaces:**
- Consumes: the completed indexer CLI, a workspace path, an exact symbol, and a positive repetition count.
- Produces: JSON with `ensure_ms`, `warm_find_median_ms`, `warm_find_p95_ms`, and `repetitions`.

- [ ] **Step 1: Create the benchmark runner**

Create `benchmarks/symbol_index.py` with this complete runner:

```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import statistics
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
INDEXER = ROOT / "skills" / "nerd-fast" / "scripts" / "symbol_index.py"


def elapsed_ms(command: list[str]) -> float:
    started = time.perf_counter_ns()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    elapsed = (time.perf_counter_ns() - started) / 1_000_000
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return elapsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("symbol")
    parser.add_argument("--repetitions", type=int, default=30)
    args = parser.parse_args(argv)
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    common = ["--root", str(args.workspace.resolve())]
    ensure_ms = elapsed_ms([sys.executable, str(INDEXER), "ensure", *common])
    samples = [
        elapsed_ms(
            [sys.executable, str(INDEXER), "find", args.symbol, *common]
        )
        for _ in range(args.repetitions)
    ]
    ordered = sorted(samples)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    print(
        json.dumps(
            {
                "ensure_ms": ensure_ms,
                "warm_find_median_ms": statistics.median(samples),
                "warm_find_p95_ms": p95,
                "repetitions": args.repetitions,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run a syntax check and verify the benchmark CLI**

Run:

```bash
python3 -m py_compile benchmarks/symbol_index.py skills/nerd-fast/scripts/symbol_index.py
python3 benchmarks/symbol_index.py . FastContractTests --repetitions 30
```

Expected: compilation exits `0`. The benchmark either prints four JSON metrics when Universal Ctags with JSON support is installed or reports the optional dependency clearly; it never fabricates a latency result.

- [ ] **Step 3: Record the local measurement in the implementation handoff**

Record the command, Universal Ctags version, workspace file count, `ensure_ms`, warm median, and warm p95 in the final implementation response. Do not add machine-specific timings to `SKILL.md`, tests, or README.

- [ ] **Step 4: Commit the benchmark runner**

```bash
git add benchmarks/symbol_index.py
git commit -m "bench: measure symbol index latency"
```

---

### Task 6: Publish the optional indexer contract in `nerd-fast`

**Files:**
- Modify: `tests/test_skill_contracts.py`
- Modify: `skills/nerd-fast/SKILL.md`
- Modify: `docs/superpowers/specs/2026-07-16-nerd-fast-design.md`
- Modify: `scripts/validate_skills.py`
- Modify: `tests/test_skill_structure.py`

**Interfaces:**
- Produces: runtime selection rule that uses the bundled script only after reuse is expected to amortize refresh cost.
- Produces: exact installed-script invocation shape using a path resolved relative to `SKILL.md`.
- Guarantees: unavailable, missing, stale, or incomplete index state falls back to an exact-file read or narrow text search.

- [ ] **Step 1: Add failing skill and structure contracts**

Add this test to `FastContractTests` in `tests/test_skill_contracts.py`:

```python
def test_uses_optional_persistent_index_only_when_amortized(self):
    body = skill_body("nerd-fast")
    assert_terms(
        self,
        body,
        (
            "existing fresh file or symbol index",
            "expected reuse amortizes refresh cost",
            "Do not rebuild or refresh an index for a single lookup",
            "confirm source before mutation",
            "exact-file read or narrow text search",
            "scripts/symbol_index.py",
            "Universal Ctags is optional",
        ),
    )
```

Add `REQUIRED_SCRIPTS` to `scripts/validate_skills.py`:

```python
REQUIRED_SCRIPTS = {
    "nerd-smart": (),
    "nerd-surgery": (),
    "nerd-patrol": (),
    "nerd-execute": (),
    "nerd-silent": (),
    "nerd-fast": ("symbol_index.py",),
}
```

Add this assertion to `SkillStructureTests.test_reference_ownership_is_exact`:

```python
self.assertEqual(REQUIRED_SCRIPTS["nerd-fast"], ("symbol_index.py",))
```

- [ ] **Step 2: Run the contracts and verify RED**

Run:

```bash
python3 -m unittest tests.test_skill_contracts.FastContractTests.test_uses_optional_persistent_index_only_when_amortized -v
python3 -m unittest tests.test_skill_structure.SkillStructureTests -v
```

Expected: the Fast contract fails because the runtime invocation is absent; the structure contract fails until the validator imports and checks `REQUIRED_SCRIPTS`.

- [ ] **Step 3: Add the runtime rule and package design**

Add this row to the Execution Discipline rule table in `skills/nerd-fast/SKILL.md`:

```markdown
| **Indexed navigation** | Prefer an existing fresh file or symbol index when its query cost is lower than direct search and expected reuse amortizes refresh cost. Do not rebuild or refresh an index for a single lookup. When the bundled script is available, resolve `scripts/symbol_index.py` relative to this `SKILL.md`, run `ensure` once before repeated exact-symbol lookups, and use `find` without implicit refresh. Universal Ctags is optional; fall back to an exact-file read or narrow text search when the index is unavailable, stale, or incomplete. Treat matches as navigation candidates and confirm source before mutation. |
```

Replace the `Package Shape` tree in the design specification with:

```text
skills/nerd-fast/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── symbol_index.py
```

Document beside the tree that the script uses only Python standard-library modules, Universal Ctags is optional, no index file is written into the workspace, and direct search remains the required fallback.

- [ ] **Step 4: Enforce required scripts in the validator**

Import `REQUIRED_SCRIPTS` in `tests/test_skill_structure.py`. In `validate_repository`, after reference validation, add:

```python
for script in REQUIRED_SCRIPTS[name]:
    path = skill_dir / "scripts" / script
    if not path.is_file():
        violations.append(f"missing file: skills/{name}/scripts/{script}")
```

- [ ] **Step 5: Run skill, structure, and indexer verification**

Run:

```bash
python3 -m unittest tests.test_skill_contracts.FastContractTests -v
python3 -m unittest tests.test_skill_structure -v
python3 -m unittest tests.test_fast_symbol_index -v
python3 scripts/validate_skills.py
```

Expected: every command exits `0`; Fast remains a modifier, the optional script is present, and no reference ownership changes.

- [ ] **Step 6: Commit the published integration**

```bash
git add skills/nerd-fast/SKILL.md skills/nerd-fast/scripts/symbol_index.py docs/superpowers/specs/2026-07-16-nerd-fast-design.md scripts/validate_skills.py tests/test_skill_contracts.py tests/test_skill_structure.py
git commit -m "feat: integrate optional fast symbol index"
```

---

### Task 7: Run repository proof and inspect publication shape

**Files:**
- Verify: all files listed in this plan

**Interfaces:**
- Consumes: completed indexer, benchmark runner, skill contract, and validator ownership.
- Produces: final proof that the optional dependency cannot break the default skill path.

- [ ] **Step 1: Run the full repository suite**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
```

Expected: all tests and the repository skill validator pass.

- [ ] **Step 2: Exercise the fallback on a host without Universal Ctags JSON support**

Run:

```bash
python3 skills/nerd-fast/scripts/symbol_index.py ensure --root . --ctags /usr/bin/ctags
```

Expected on the current macOS host: exit `2` with a diagnostic naming Universal Ctags; no cache is created inside the repository and direct `rg` remains available.

- [ ] **Step 3: Inspect the scoped diff and package**

```bash
git diff --check
git diff --stat
find skills/nerd-fast -maxdepth 3 -type f -print | sort
git status --short
```

Expected: the skill contains `SKILL.md`, `agents/openai.yaml`, and `scripts/symbol_index.py`; no SQLite, tag, cache, or generated file appears in the repository.

- [ ] **Step 4: Commit the plan and any final verification-only corrections**

```bash
git add docs/superpowers/plans/2026-07-17-nerd-fast-symbol-indexer.md
git commit -m "docs: plan nerd fast symbol indexer"
```

## Self-Review Record

- Spec coverage: optional dependency, persistent cache, incremental refresh, deleted-file invalidation, exact lookup, fallback, source confirmation, validation, and latency measurement each map to a task.
- Placeholder scan: no deferred implementation markers remain; every code-producing step names exact content and commands.
- Type consistency: `FileFingerprint`, cache functions, `refresh_index`, CLI subcommands, and the benchmark invocation use the same names throughout.
- Scope boundary: persistent daemons, fuzzy search, semantic references, automatic dependency installation, and CI timing gates are deliberately excluded from the MVP.
