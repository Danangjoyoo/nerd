#!/usr/bin/env python3
"""Repository-aware allowlisted verification adapters for Nerd UFast."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import json
import shutil
import subprocess
import sys
import time
from typing import Any, Sequence


VERSION = "0.3.0"
CHECK_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 4_000
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


@dataclass(frozen=True)
class CheckSpec:
    name: str
    backend: str
    command: tuple[str, ...]


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1_000))


def _trim(value: str) -> str:
    return value[-MAX_OUTPUT_CHARS:]


def _as_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _is_relevant(
    changed: Sequence[str],
    *,
    suffixes: frozenset[str],
    marker_names: frozenset[str] = frozenset(),
) -> bool:
    if not changed:
        return True
    return any(
        PurePosixPath(path).suffix.casefold() in suffixes
        or PurePosixPath(path).name in marker_names
        for path in changed
    )


def _normalized_changed_paths(root: Path, values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, (list, tuple)) or len(values) > 200:
        raise ValueError("changed_paths must contain at most 200 paths")
    normalized: list[str] = []
    for raw in values:
        if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
            raise ValueError("changed_paths must contain normalized strings")
        path = PurePosixPath(raw)
        if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
            raise ValueError(f"Path traversal is not allowed: {raw!r}")
        candidate = root / path
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError(f"Changed path is not a regular workspace file: {raw!r}")
        normalized.append(path.as_posix())
    return normalized


def detect_test_plan(
    root: Path | str,
    changed_paths: Sequence[str] | None = None,
) -> list[CheckSpec]:
    """Return a deterministic plan selected only from known repository markers."""

    workspace = Path(root).expanduser().resolve()
    if not workspace.is_dir():
        return []
    try:
        changed = _normalized_changed_paths(workspace, changed_paths)
    except ValueError:
        return []
    plan: list[CheckSpec] = []

    python_paths = [path for path in changed if PurePosixPath(path).suffix == ".py"]
    python_relevant = _is_relevant(
        changed,
        suffixes=frozenset({".py", ".pyi"}),
        marker_names=frozenset({"pyproject.toml", "setup.cfg", "setup.py"}),
    )
    python_files = sorted(
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*.py")
        if path.is_file()
        and not path.is_symlink()
        and not any(
            part.startswith(".") or part in EXCLUDED_DIRECTORIES
            for part in path.relative_to(workspace).parts
        )
    )
    if python_paths:
        plan.append(
            CheckSpec(
                "python_syntax",
                "python_stdlib",
                (sys.executable, "-m", "py_compile", *python_paths),
            )
        )
    lint = workspace / "lint_check.py"
    if python_paths and lint.is_file() and not lint.is_symlink():
        plan.append(
            CheckSpec(
                "fixture_lint",
                "python_fixture",
                (sys.executable, "lint_check.py", *changed),
            )
        )
    tests = [
        path
        for path in python_files
        if PurePosixPath(path).name.startswith("test")
        and path not in {"lint_check.py", "verify_behavior.py"}
    ]
    if python_relevant and python_files and tests:
        plan.append(
            CheckSpec(
                "python_tests",
                "python_unittest",
                (sys.executable, "-m", "unittest", *tests, "-v"),
            )
        )
    behavior = workspace / "verify_behavior.py"
    if python_relevant and python_files and behavior.is_file() and not behavior.is_symlink():
        plan.append(
            CheckSpec(
                "verify_behavior",
                "python_fixture",
                (sys.executable, "-m", "unittest", "verify_behavior", "-v"),
            )
        )

    package = workspace / "package.json"
    node_relevant = _is_relevant(
        changed,
        suffixes=frozenset({".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}),
        marker_names=frozenset({"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}),
    )
    if node_relevant and package.is_file() and not package.is_symlink():
        try:
            payload = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            payload = {}
        scripts = payload.get("scripts") if isinstance(payload, dict) else None
        if isinstance(scripts, dict) and isinstance(scripts.get("test"), str):
            plan.append(CheckSpec("node_test", "npm", ("npm", "test", "--silent")))
    go_relevant = _is_relevant(
        changed,
        suffixes=frozenset({".go"}),
        marker_names=frozenset({"go.mod", "go.sum"}),
    )
    if go_relevant and (workspace / "go.mod").is_file():
        plan.append(CheckSpec("go_test", "go", ("go", "test", "./...")))
    rust_relevant = _is_relevant(
        changed,
        suffixes=frozenset({".rs"}),
        marker_names=frozenset({"Cargo.toml", "Cargo.lock"}),
    )
    if rust_relevant and (workspace / "Cargo.toml").is_file():
        plan.append(CheckSpec("cargo_test", "cargo", ("cargo", "test", "--quiet")))
    jvm_relevant = _is_relevant(
        changed,
        suffixes=frozenset({".java", ".kt", ".kts", ".groovy", ".scala"}),
        marker_names=frozenset(
            {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"}
        ),
    )
    if jvm_relevant and (workspace / "pom.xml").is_file():
        plan.append(CheckSpec("maven_test", "maven", ("mvn", "test", "-q")))
    gradle = workspace / "gradlew"
    if jvm_relevant and gradle.is_file() and not gradle.is_symlink():
        plan.append(CheckSpec("gradle_test", "gradle", (str(gradle), "test", "--quiet")))
    return plan


def _run_check(workspace: Path, check: CheckSpec) -> dict[str, Any]:
    started = time.perf_counter()
    executable = check.command[0]
    if not Path(executable).is_absolute() and shutil.which(executable) is None:
        return {
            "name": check.name,
            "backend": check.backend,
            "exit_code": 127,
            "duration_ms": _elapsed_ms(started),
            "output": f"Required executable is unavailable: {executable}",
        }
    try:
        completed = subprocess.run(
            list(check.command),
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return {
            "name": check.name,
            "backend": check.backend,
            "exit_code": completed.returncode,
            "duration_ms": _elapsed_ms(started),
            "output": _trim(output),
        }
    except subprocess.TimeoutExpired as error:
        output = _as_text(error.stdout) + _as_text(error.stderr)
        return {
            "name": check.name,
            "backend": check.backend,
            "exit_code": 124,
            "duration_ms": _elapsed_ms(started),
            "output": _trim(output + "\nCheck timed out"),
        }
    except OSError as error:
        return {
            "name": check.name,
            "backend": check.backend,
            "exit_code": 126,
            "duration_ms": _elapsed_ms(started),
            "output": _trim(str(error)),
        }


def run_test_plan(
    root: Path | str,
    changed_paths: Sequence[str] | None = None,
    selected_checks: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Run only checks selected from detected adapters; accept no command input."""

    started = time.perf_counter()
    workspace = Path(root).expanduser().resolve()
    plan = detect_test_plan(workspace, changed_paths)
    available = [check.name for check in plan]
    if selected_checks is not None:
        if (
            not isinstance(selected_checks, (list, tuple))
            or not all(isinstance(name, str) for name in selected_checks)
            or len(set(selected_checks)) != len(selected_checks)
        ):
            return {
                "status": "rejected",
                "runtime_version": VERSION,
                "operation_ms": _elapsed_ms(started),
                "reason": "checks must contain unique detected check names",
                "available_checks": available,
                "checks": [],
            }
        unknown = sorted(set(selected_checks) - set(available))
        if unknown:
            return {
                "status": "rejected",
                "runtime_version": VERSION,
                "operation_ms": _elapsed_ms(started),
                "reason": f"Unknown or unavailable checks: {', '.join(unknown)}",
                "available_checks": available,
                "checks": [],
            }
        selected = set(selected_checks)
        plan = [check for check in plan if check.name in selected]
    if not plan:
        return {
            "status": "unsupported",
            "runtime_version": VERSION,
            "operation_ms": _elapsed_ms(started),
            "reason": "No supported repository verification adapter was detected",
            "available_checks": available,
            "checks": [],
        }
    with ThreadPoolExecutor(max_workers=min(4, len(plan))) as executor:
        results = list(executor.map(lambda check: _run_check(workspace, check), plan))
    return {
        "status": "passed" if all(check["exit_code"] == 0 for check in results) else "failed",
        "runtime_version": VERSION,
        "operation_ms": _elapsed_ms(started),
        "backend": "verification_registry",
        "available_checks": available,
        "checks": results,
    }
