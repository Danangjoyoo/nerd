#!/usr/bin/env python3
"""Deterministic, dependency-free operations for the Nerd UFast MCP server."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import tomllib
from typing import Any


VERSION = "0.3.0"
MAX_FILES = 12
MAX_TOTAL_BYTES = 128 * 1024
MAX_OUTPUT_CHARS = 4_000
CHECK_TIMEOUT_SECONDS = 20
SUPPORT_FILES = frozenset({"lint_check.py", "verify_behavior.py"})
EXCLUDED_DIRECTORIES = frozenset(
    {"__pycache__", "node_modules", "vendor", "dist", "build"}
)
STRUCTURED_SUFFIXES = frozenset({".py", ".json", ".toml"})

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1_000))


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _result(
    status: str,
    started: float,
    **values: Any,
) -> dict[str, Any]:
    return {
        "status": status,
        "runtime_version": VERSION,
        "operation_ms": _elapsed_ms(started),
        **values,
    }


def _workspace_files(root: Path) -> tuple[list[Path], str | None]:
    files: list[Path] = []
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if not directory.startswith(".")
            and directory not in EXCLUDED_DIRECTORIES
        )
        for name in sorted(names):
            if (
                name.startswith(".")
                or name in SUPPORT_FILES
                or Path(name).suffix in {".pyc", ".pyo"}
            ):
                continue
            path = current_path / name
            if path.is_symlink():
                return [], f"symlink targets are unsupported: {path.relative_to(root)}"
            if not path.is_file():
                return [], f"Non-regular files are unsupported: {path.relative_to(root)}"
            body = path.read_bytes()
            if b"\x00" in body:
                continue
            try:
                body.decode("utf-8")
            except UnicodeDecodeError:
                continue
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix()), None


def _detected_checks(root: Path, editable_files: Sequence[Path]) -> list[str]:
    checks = []
    if any(path.suffix in STRUCTURED_SUFFIXES for path in editable_files):
        checks.append("syntax")
    lint_path = root / "lint_check.py"
    if lint_path.is_file() and not lint_path.is_symlink():
        checks.append("fixture_lint")
    if any(path.name.startswith("test") for path in editable_files):
        checks.append("changed_tests")
    behavior_path = root / "verify_behavior.py"
    if behavior_path.is_file() and not behavior_path.is_symlink():
        checks.append("verify_behavior")
    return checks


def prepare_workspace_change(root: Path | str) -> dict[str, Any]:
    """Return a bounded snapshot of editable UTF-8 workspace files."""

    started = time.perf_counter()
    workspace = Path(root).expanduser().resolve()
    if not workspace.is_dir():
        return _result(
            "unsupported",
            started,
            reason="The configured workspace is not a directory",
            files=[],
            checks=[],
        )

    files, rejection = _workspace_files(workspace)
    if rejection is not None:
        return _result(
            "unsupported",
            started,
            reason=rejection,
            files=[],
            checks=[],
        )
    if not files:
        return _result(
            "unsupported",
            started,
            reason="No editable UTF-8 workspace files were found",
            files=[],
            checks=[],
        )
    if len(files) > MAX_FILES:
        return _result(
            "unsupported",
            started,
            reason=f"Context exceeds the {MAX_FILES}-file limit",
            files=[],
            checks=[],
        )

    snapshots: list[dict[str, str]] = []
    total_bytes = 0
    for path in files:
        body = path.read_bytes()
        total_bytes += len(body)
        if total_bytes > MAX_TOTAL_BYTES:
            return _result(
                "unsupported",
                started,
                reason=f"Context exceeds the {MAX_TOTAL_BYTES}-byte limit",
                files=[],
                checks=[],
            )
        try:
            content = body.decode("utf-8")
        except UnicodeDecodeError:
            return _result(
                "unsupported",
                started,
                reason=f"Workspace file is not UTF-8: {path.relative_to(workspace)}",
                files=[],
                checks=[],
            )
        snapshots.append(
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": _digest(body),
                "content": content,
            }
        )

    return _result(
        "ready",
        started,
        files=snapshots,
        checks=_detected_checks(workspace, files),
        limits={"max_files": MAX_FILES, "max_total_bytes": MAX_TOTAL_BYTES},
    )


def _resolve_editable_path(workspace: Path, raw_path: Any) -> tuple[Path, str]:
    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
        raise ValueError("Each change path must be a non-empty string")
    if "\\" in raw_path:
        raise ValueError(f"Only normalized POSIX paths are accepted: {raw_path!r}")

    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise ValueError(f"Path traversal is not allowed: {raw_path!r}")
    if any(
        part.startswith(".") or part in EXCLUDED_DIRECTORIES
        for part in relative.parts
    ):
        raise ValueError(f"Hidden and cache paths are not editable: {raw_path!r}")
    if relative.name in SUPPORT_FILES or relative.suffix in {".pyc", ".pyo"}:
        raise ValueError(f"Runtime support and generated files are not editable: {raw_path!r}")

    target = workspace.joinpath(*relative.parts)
    if target.is_symlink():
        raise ValueError(f"Symlink targets are not editable: {raw_path!r}")
    if not target.is_file():
        raise ValueError(f"The target must be an existing regular file: {raw_path!r}")
    try:
        target.resolve(strict=True).relative_to(workspace)
    except (OSError, ValueError) as error:
        raise ValueError(f"Target escapes the workspace: {raw_path!r}") from error
    original = target.read_bytes()
    if b"\x00" in original:
        raise ValueError(f"Binary targets are not editable: {raw_path!r}")
    try:
        original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"Only UTF-8 text targets are editable: {raw_path!r}") from error
    return target, relative.as_posix()


def _validate_structured_content(relative: str, content: str) -> bool:
    suffix = PurePosixPath(relative).suffix
    if "\x00" in content:
        raise ValueError(f"NUL bytes are not accepted in text content: {relative!r}")
    if suffix == ".py":
        compile(content, relative, "exec")
        return True
    if suffix == ".json":
        json.loads(content)
        return True
    if suffix == ".toml":
        tomllib.loads(content)
        return True
    return False


def _write_temporary(target: Path, body: bytes, mode: int) -> Path:
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f".{target.name}.ufast-",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(raw_path)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _restore(replaced: Sequence[tuple[Path, bytes, int]]) -> None:
    failures: list[str] = []
    for target, body, mode in reversed(replaced):
        temporary: Path | None = None
        try:
            temporary = _write_temporary(target, body, mode)
            os.replace(temporary, target)
        except OSError as error:
            failures.append(f"{target}: {error}")
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    if failures:
        raise OSError("Rollback failed: " + "; ".join(failures))


def _trim_output(output: str) -> str:
    if len(output) <= MAX_OUTPUT_CHARS:
        return output
    return output[:MAX_OUTPUT_CHARS] + "\n...[truncated]"


def _run_check(
    name: str,
    command: Sequence[str],
    workspace: Path,
    environment: dict[str, str],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            list(command),
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
            check=False,
        )
        output = completed.stdout + completed.stderr
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr
        output = (stdout or "") + (stderr or "") + "\nCheck timed out"
        exit_code = 124
    return {
        "name": name,
        "exit_code": exit_code,
        "duration_ms": _elapsed_ms(started),
        "output": _trim_output(output),
    }


def _verification_commands(
    workspace: Path,
    changed_paths: Sequence[str],
) -> list[tuple[str, list[str] | None]]:
    python_paths = [path for path in changed_paths if PurePosixPath(path).suffix == ".py"]
    structured_paths = [
        path
        for path in changed_paths
        if PurePosixPath(path).suffix in STRUCTURED_SUFFIXES
    ]
    commands: list[tuple[str, list[str] | None]] = []
    if python_paths:
        commands.append(
            ("syntax", [sys.executable, "-m", "py_compile", *python_paths])
        )
    elif structured_paths:
        commands.append(("syntax", None))
    lint_path = workspace / "lint_check.py"
    if lint_path.is_file() and not lint_path.is_symlink():
        commands.append(
            (
                "fixture_lint",
                [sys.executable, "lint_check.py", *changed_paths],
            )
        )

    editable_files, _ = _workspace_files(workspace)
    test_paths = [
        path.relative_to(workspace).as_posix()
        for path in editable_files
        if path.name.startswith("test")
    ]
    if python_paths and test_paths:
        commands.append(
            (
                "changed_tests",
                [sys.executable, "-m", "unittest", *test_paths, "-v"],
            )
        )

    behavior_path = workspace / "verify_behavior.py"
    if python_paths and behavior_path.is_file() and not behavior_path.is_symlink():
        commands.append(
            (
                "verify_behavior",
                [sys.executable, "-m", "unittest", "verify_behavior", "-v"],
            )
        )
    return commands


def apply_workspace_change(
    root: Path | str,
    changes: Any,
    *,
    verify: bool = True,
    selected_checks: Sequence[str] | None = None,
    replace: Callable[[os.PathLike[str], os.PathLike[str]], Any] = os.replace,
) -> dict[str, Any]:
    """Atomically apply a bounded UTF-8 text batch and roll back failed checks."""

    started = time.perf_counter()
    workspace = Path(root).expanduser().resolve()
    if not workspace.is_dir():
        return _result(
            "rejected",
            started,
            reason="The configured workspace is not a directory",
            changed_files=[],
            checks=[],
            rolled_back=False,
        )
    if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_FILES:
        return _result(
            "rejected",
            started,
            reason=f"changes must contain between 1 and {MAX_FILES} items",
            changed_files=[],
            checks=[],
            rolled_back=False,
        )

    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_bytes = 0
    try:
        for change in changes:
            if not isinstance(change, dict):
                raise ValueError("Each change must be an object")
            target, relative = _resolve_editable_path(workspace, change.get("path"))
            if relative in seen:
                raise ValueError(f"Duplicate change path: {relative!r}")
            seen.add(relative)
            expected = change.get("expected_sha256")
            if (
                not isinstance(expected, str)
                or len(expected) != 64
                or any(character not in "0123456789abcdef" for character in expected)
            ):
                raise ValueError(f"Invalid expected_sha256 for {relative!r}")
            content = change.get("content")
            if not isinstance(content, str):
                raise ValueError(f"content must be a string for {relative!r}")
            body = content.encode("utf-8")
            total_bytes += len(body)
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError(f"Changes exceed the {MAX_TOTAL_BYTES}-byte limit")
            original = target.read_bytes()
            validated.append(
                {
                    "target": target,
                    "relative": relative,
                    "expected": expected,
                    "body": body,
                    "original": original,
                    "mode": target.stat().st_mode & 0o777,
                }
            )
    except (OSError, UnicodeError, ValueError) as error:
        return _result(
            "rejected",
            started,
            reason=str(error),
            changed_files=[],
            checks=[],
            rolled_back=False,
        )

    stale = [
        item["relative"]
        for item in validated
        if _digest(item["original"]) != item["expected"]
    ]
    if stale:
        return _result(
            "stale",
            started,
            reason="One or more source hashes changed after preparation",
            stale_files=stale,
            changed_files=[],
            checks=[],
            rolled_back=False,
        )

    try:
        for item in validated:
            _validate_structured_content(
                item["relative"],
                item["body"].decode("utf-8"),
            )
    except (SyntaxError, UnicodeDecodeError, ValueError) as error:
        return _result(
            "verification_failed",
            started,
            reason=f"Syntax validation failed before writing: {error}",
            changed_files=[],
            checks=[
                {
                    "name": "syntax",
                    "exit_code": 1,
                    "duration_ms": 0,
                    "output": _trim_output(str(error)),
                }
            ],
            rolled_back=False,
        )

    temporary_files: list[Path] = []
    replaced: list[tuple[Path, bytes, int]] = []
    try:
        for item in validated:
            temporary_files.append(
                _write_temporary(item["target"], item["body"], item["mode"])
            )
        for item, temporary in zip(validated, temporary_files, strict=True):
            replace(temporary, item["target"])
            replaced.append((item["target"], item["original"], item["mode"]))
    except OSError as error:
        for temporary in temporary_files:
            temporary.unlink(missing_ok=True)
        rollback_error: OSError | None = None
        try:
            _restore(replaced)
        except OSError as restore_error:
            rollback_error = restore_error
        reason = f"Atomic replacement failed: {error}"
        if rollback_error is not None:
            reason += f"; {rollback_error}"
        return _result(
            "failed",
            started,
            reason=reason,
            changed_files=[],
            checks=[],
            rolled_back=bool(replaced) and rollback_error is None,
        )
    finally:
        for temporary in temporary_files:
            temporary.unlink(missing_ok=True)

    changed_paths = [item["relative"] for item in validated]
    checks: list[dict[str, Any]] = []
    if any(PurePosixPath(path).suffix in STRUCTURED_SUFFIXES for path in changed_paths):
        checks.append(
            {
                "name": "structural_validation",
                "backend": "stdlib_parser",
                "exit_code": 0,
                "duration_ms": 0,
                "output": "Structured text validated before atomic write",
            }
        )
    verification_status = "not_requested"
    if verify:
        from ufast_verify import run_test_plan

        verification = run_test_plan(workspace, changed_paths, selected_checks)
        verification_status = verification["status"]
        checks.extend(verification.get("checks", []))
        if verification_status in {"failed", "rejected"}:
            rollback_error = None
            try:
                _restore(replaced)
            except OSError as error:
                rollback_error = error
            reason = verification.get("reason") or "Repository verification failed"
            if rollback_error is not None:
                reason += f"; {rollback_error}"
            return _result(
                "verification_failed",
                started,
                reason=reason,
                changed_files=[],
                checks=checks,
                rolled_back=rollback_error is None,
                verification_status=verification_status,
            )

    return _result(
        "applied",
        started,
        changed_files=changed_paths,
        checks=checks,
        rolled_back=False,
        verification_status=verification_status,
    )


def safe_edit(
    root: Path | str,
    changes: Any,
    *,
    verify: bool = True,
    selected_checks: Sequence[str] | None = None,
    replace: Callable[[os.PathLike[str], os.PathLike[str]], Any] = os.replace,
) -> dict[str, Any]:
    """Materialize exact replacements, then use the atomic transaction backend."""

    started = time.perf_counter()
    workspace = Path(root).expanduser().resolve()
    if not isinstance(verify, bool):
        return _result(
            "rejected",
            started,
            reason="verify must be a boolean",
            changed_files=[],
            checks=[],
            rolled_back=False,
        )
    if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_FILES:
        return _result(
            "rejected",
            started,
            reason=f"changes must contain between 1 and {MAX_FILES} items",
            changed_files=[],
            checks=[],
            rolled_back=False,
        )

    materialized: list[dict[str, str]] = []
    modes: set[str] = set()
    try:
        for change in changes:
            if not isinstance(change, dict):
                raise ValueError("Each change must be an object")
            target, relative = _resolve_editable_path(workspace, change.get("path"))
            expected = change.get("expected_sha256")
            content_present = "content" in change
            replacements_present = "replacements" in change
            if content_present == replacements_present:
                raise ValueError(
                    f"Exactly one of content or replacements is required for {relative!r}"
                )
            if content_present:
                content = change.get("content")
                if not isinstance(content, str):
                    raise ValueError(f"content must be a string for {relative!r}")
                modes.add("complete_contents")
            else:
                replacements = change.get("replacements")
                if (
                    not isinstance(replacements, list)
                    or not 1 <= len(replacements) <= 50
                ):
                    raise ValueError(
                        f"replacements must contain between 1 and 50 items for {relative!r}"
                    )
                content = target.read_text(encoding="utf-8")
                for replacement in replacements:
                    if not isinstance(replacement, dict):
                        raise ValueError("Each replacement must be an object")
                    old = replacement.get("old_text")
                    new = replacement.get("new_text")
                    occurrences = replacement.get("expected_occurrences")
                    if not isinstance(old, str) or not old:
                        raise ValueError("old_text must be a non-empty string")
                    if not isinstance(new, str):
                        raise ValueError("new_text must be a string")
                    if (
                        not isinstance(occurrences, int)
                        or isinstance(occurrences, bool)
                        or occurrences < 1
                    ):
                        raise ValueError("expected_occurrences must be a positive integer")
                    actual = content.count(old)
                    if actual != occurrences:
                        raise ValueError(
                            f"Expected {occurrences} occurrence(s) of exact text in "
                            f"{relative!r}, found {actual}"
                        )
                    content = content.replace(old, new, occurrences)
                modes.add("exact_replacements")
            materialized.append(
                {
                    "path": relative,
                    "expected_sha256": expected,
                    "content": content,
                }
            )
    except (OSError, UnicodeError, ValueError) as error:
        return _result(
            "rejected",
            started,
            reason=str(error),
            changed_files=[],
            checks=[],
            rolled_back=False,
        )

    result = apply_workspace_change(
        workspace,
        materialized,
        verify=verify,
        selected_checks=selected_checks,
        replace=replace,
    )
    mode = next(iter(modes)) if len(modes) == 1 else "mixed"
    resulting_files = []
    if result.get("status") == "applied":
        for path in result.get("changed_files", []):
            target = workspace / path
            body = target.read_bytes()
            resulting_files.append(
                {
                    "path": path,
                    "sha256": _digest(body),
                    "bytes": len(body),
                }
            )
    return {
        **result,
        "edit_mode": mode,
        "resulting_files": resulting_files,
    }
