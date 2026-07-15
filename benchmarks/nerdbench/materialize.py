"""Create isolated benchmark workspaces and condition-specific skill sets."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from .models import BenchmarkCase


ROOT = Path(__file__).resolve().parents[2]
PINNED_SUPERPOWERS_COMMIT = "c984ea2e7aeffdcc865784fd6c5e3ab75da0209a"
SUPERPOWERS_TAG = "v6.1.1"
SUPERPOWERS_URL = "https://github.com/obra/superpowers.git"

AGENT_SKILL_PATHS = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "cursor": Path(".agents/skills"),
}

LOCAL_CONDITIONS = {
    "nerd-smart": ("nerd-smart",),
    "nerd-surgery": ("nerd-smart", "nerd-surgery"),
    "nerd-execute": ("nerd-smart", "nerd-execute"),
    "regular": ("nerd-smart",),
    "nerd-silent": ("nerd-smart", "nerd-silent"),
    "nerd-patrol": ("nerd-smart", "nerd-patrol"),
}

UPSTREAM_CONDITIONS = {
    "superpowers-brainstorming": ("brainstorming",),
    "superpowers-systematic-debugging": (
        "systematic-debugging",
        "test-driven-development",
        "verification-before-completion",
    ),
    "superpowers-executing-plans": (
        "executing-plans",
        "test-driven-development",
        "verification-before-completion",
    ),
}


def _run(command: list[str], cwd: Path) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_superpowers_checkout(path: Path) -> None:
    actual = _run(["git", "rev-parse", "HEAD"], path)
    if actual != PINNED_SUPERPOWERS_COMMIT:
        raise ValueError(
            "upstream checkout does not match pinned commit "
            f"{PINNED_SUPERPOWERS_COMMIT}: {actual}"
        )


def fetch_superpowers(cache_dir: Path) -> Path:
    checkout = cache_dir / f"superpowers-{SUPERPOWERS_TAG}"
    if checkout.exists():
        try:
            verify_superpowers_checkout(checkout)
            return checkout
        except (ValueError, subprocess.CalledProcessError):
            shutil.rmtree(checkout)

    cache_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            SUPERPOWERS_TAG,
            SUPERPOWERS_URL,
            str(checkout),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    verify_superpowers_checkout(checkout)
    return checkout


def _copy_fixture(case: BenchmarkCase, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    if case.fixture is None:
        return
    source = ROOT / "benchmarks" / "fixtures" / case.fixture
    if not source.is_dir():
        raise ValueError(f"missing fixture: {case.fixture}")
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def _install_condition(condition: str, agent: str, destination: Path) -> None:
    try:
        skill_root = destination / AGENT_SKILL_PATHS[agent]
    except KeyError as error:
        raise ValueError(f"unsupported agent: {agent}") from error
    skill_root.mkdir(parents=True, exist_ok=True)

    if condition in LOCAL_CONDITIONS:
        source_root = ROOT / "skills"
        skill_names = LOCAL_CONDITIONS[condition]
    elif condition in UPSTREAM_CONDITIONS:
        checkout = fetch_superpowers(ROOT / "benchmarks" / ".cache")
        source_root = checkout / "skills"
        skill_names = UPSTREAM_CONDITIONS[condition]
    else:
        raise ValueError(f"unknown benchmark condition: {condition}")

    for name in skill_names:
        source = source_root / name
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"condition skill is missing: {source}")
        shutil.copytree(source, skill_root / name)


def _initialize_repository(destination: Path) -> None:
    _run(["git", "init", "-q"], destination)
    _run(["git", "config", "user.email", "benchmark@nerd.invalid"], destination)
    _run(["git", "config", "user.name", "Nerd Benchmark"], destination)
    _run(["git", "add", "."], destination)
    _run(["git", "commit", "-qm", "benchmark baseline"], destination)


def materialize_run(
    case: BenchmarkCase,
    condition: str,
    agent: str,
    destination: Path,
) -> Path:
    _copy_fixture(case, destination)
    _install_condition(condition, agent, destination)
    _initialize_repository(destination)
    return destination
