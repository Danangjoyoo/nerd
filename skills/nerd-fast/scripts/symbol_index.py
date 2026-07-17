#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile


SCHEMA_VERSION = "1"
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


def enumerate_files(root: Path) -> list[str]:
    try:
        git = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
            capture_output=True,
            check=False,
        )
    except OSError:
        git = None
    if git is not None and git.returncode == 0:
        return sorted(os.fsdecode(value) for value in git.stdout.split(b"\0") if value)

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


def _resolved_cache(args: argparse.Namespace) -> Path:
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
        print(
            "symbol index is missing; run ensure or use narrow text search",
            file=sys.stderr,
        )
        return 3

    connection = connect_cache(cache)
    try:
        initialize_schema(connection, root)
        if args.command == "find":
            print(
                json.dumps(
                    {
                        "query": args.name,
                        "matches": find_symbol(connection, args.name, args.limit),
                    },
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
