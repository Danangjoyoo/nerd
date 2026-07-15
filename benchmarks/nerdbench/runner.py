"""Deterministic scheduling and immutable execution of benchmark runs."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import shlex
import subprocess
import time

from .adapters import get_adapter
from .cases import load_cases
from .materialize import materialize_run
from .models import BenchmarkCase, RunResult, RunSpec


ROOT = Path(__file__).resolve().parents[2]
CONDITION_SKILLS = {
    "nerd-smart": "nerd-smart",
    "superpowers-brainstorming": "brainstorming",
    "nerd-surgery": "nerd-surgery",
    "superpowers-systematic-debugging": "systematic-debugging",
    "nerd-execute": "nerd-execute",
    "superpowers-executing-plans": "executing-plans",
    "regular": "nerd-smart",
    "nerd-silent": "nerd-silent",
    "nerd-patrol": "nerd-patrol",
}
SMOKE_CASES = {
    "smart": "smart-ambiguous-focus",
    "surgery": "surgery-trace-source",
    "execute": "execute-blocker",
    "silent": "silent-final-only",
    "patrol": "patrol-auth-pr",
}


def load_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "upstream",
        "agents",
        "models",
        "target",
        "judge",
        "case_files",
        "conditions",
        "repetitions",
        "parallelism",
        "seed",
    }
    if set(payload) != required:
        raise ValueError("benchmark config keys do not match schema")
    if payload["repetitions"] <= 0 or payload["parallelism"] <= 0:
        raise ValueError("repetitions and parallelism must be positive")
    if set(payload["target"]) != {"id", "display_name", "reasoning_effort"}:
        raise ValueError("target keys do not match schema")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", payload["target"]["id"]):
        raise ValueError("target id must use safe lowercase characters")
    efforts = {
        None,
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    }
    if payload["target"]["reasoning_effort"] not in efforts:
        raise ValueError("unsupported target reasoning effort")
    if set(payload["judge"]) != {
        "agent",
        "model",
        "reasoning_effort",
        "timeout_seconds",
    }:
        raise ValueError("judge keys do not match schema")
    if payload["judge"].get("agent") != "codex":
        raise ValueError("the blinded judge agent must be codex")
    if payload["judge"].get("timeout_seconds", 0) <= 0:
        raise ValueError("judge timeout must be positive")
    if payload["judge"].get("reasoning_effort") not in efforts:
        raise ValueError("unsupported judge reasoning effort")
    resolved = path.resolve()
    try:
        payload["_root"] = next(
            parent
            for parent in resolved.parents
            if (parent / "benchmarks").is_dir() and (parent / "skills").is_dir()
        )
    except StopIteration as error:
        raise ValueError("benchmark config is outside a Nerd repository") from error
    return payload


def _cases(config: dict) -> tuple[BenchmarkCase, ...]:
    root = config["_root"]
    loaded = []
    for relative in config["case_files"]:
        loaded.extend(load_cases(root / relative))
    return tuple(loaded)


def pair_key(spec: RunSpec) -> tuple:
    return (
        spec.target_id,
        spec.case_id,
        spec.agent,
        spec.model,
        spec.reasoning_effort,
        spec.repetition,
    )


def schedule_runs(config: dict, workspace_root: Path) -> tuple[RunSpec, ...]:
    rng = random.Random(config["seed"])
    scheduled: list[RunSpec] = []
    target = config["target"]
    for case in _cases(config):
        try:
            conditions = tuple(config["conditions"][case.comparison])
        except KeyError as error:
            raise ValueError(f"missing conditions for {case.comparison}") from error
        for agent in config["agents"]:
            model = config["models"].get(agent)
            for repetition in range(1, config["repetitions"] + 1):
                ordered = list(conditions)
                rng.shuffle(ordered)
                for condition in ordered:
                    run_id = (
                        f"{case.comparison}--{case.id}--{target['id']}--{agent}--"
                        f"r{repetition}--{condition}"
                    )
                    scheduled.append(
                        RunSpec(
                            run_id=run_id,
                            case_id=case.id,
                            condition=condition,
                            agent=agent,
                            model=model,
                            repetition=repetition,
                            workspace=workspace_root / run_id,
                            target_id=target["id"],
                            reasoning_effort=target["reasoning_effort"],
                        )
                    )
    return tuple(scheduled)


def create_run_directory(results_root: Path, run_id: str) -> Path:
    destination = results_root / run_id
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise FileExistsError(f"refusing to overwrite existing run: {run_id}") from error
    return destination


def condition_prompt(condition: str, prompt: str) -> str:
    try:
        skill = CONDITION_SKILLS[condition]
    except KeyError as error:
        raise ValueError(f"unknown benchmark condition: {condition}") from error
    return f"Use ${skill}.\n\n{prompt}"


def _git_output(args: list[str], cwd: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _proof_commands(case: BenchmarkCase) -> tuple[str, ...]:
    commands = []
    for criterion in case.criteria:
        if criterion.evaluator != "command":
            continue
        command, separator, _ = criterion.expected.rpartition("::")
        commands.append(command if separator else criterion.expected)
    return tuple(dict.fromkeys(commands))


def _changed_files(workspace: Path) -> tuple[str, ...]:
    output = subprocess.run(
        ["git", "status", "--short"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return tuple(
        line[3:].strip()
        for line in output.splitlines()
        if len(line) >= 4 and line[3:].strip()
    )


def _diff_hash(workspace: Path) -> str:
    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD"],
        cwd=workspace,
        check=True,
        capture_output=True,
    ).stdout
    return hashlib.sha256(diff).hexdigest()


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def execute_run(case: BenchmarkCase, spec: RunSpec) -> tuple[RunResult, str]:
    materialize_run(case, spec.condition, spec.agent, spec.workspace)
    prompt = condition_prompt(spec.condition, case.prompt)
    adapter = get_adapter(spec.agent)
    command = adapter.build_command(spec, prompt)

    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            cwd=spec.workspace,
            capture_output=True,
            text=True,
            timeout=case.timeout_seconds,
            env=os.environ.copy(),
        )
        exit_code = process.returncode
        stdout = process.stdout
        stderr = process.stderr
    except subprocess.TimeoutExpired as error:
        exit_code = 124
        stdout = _timeout_text(error.stdout)
        stderr = _timeout_text(error.stderr) + "\nbenchmark timeout"
    elapsed = time.monotonic() - started
    final, tokens, events = adapter.parse(stdout, stderr)

    command_results = {}
    for proof in _proof_commands(case):
        result = subprocess.run(
            shlex.split(proof),
            cwd=spec.workspace,
            capture_output=True,
            text=True,
        )
        command_results[proof] = result.returncode

    result = RunResult(
        spec=spec,
        exit_code=exit_code,
        elapsed_seconds=elapsed,
        final_text=final,
        output_tokens=tokens,
        events=events,
        changed_files=_changed_files(spec.workspace),
        command_results=command_results,
    )
    return result, _diff_hash(spec.workspace)


def result_record(result: RunResult, diff_hash: str) -> dict:
    spec = result.spec
    return {
        "run_id": spec.run_id,
        "case_id": spec.case_id,
        "condition": spec.condition,
        "agent": spec.agent,
        "model": spec.model,
        "target_id": spec.target_id,
        "reasoning_effort": spec.reasoning_effort,
        "repetition": spec.repetition,
        "exit_code": result.exit_code,
        "elapsed_seconds": result.elapsed_seconds,
        "final_text": result.final_text,
        "output_tokens": result.output_tokens,
        "events": list(result.events),
        "changed_files": list(result.changed_files),
        "command_results": result.command_results,
        "diff_sha256": diff_hash,
    }


def _run_id(config: dict) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = _git_output(["rev-parse", "--short=7", "HEAD"])
    return f"{timestamp}-{commit}-{config['target']['id']}"


def _public_config(config: dict) -> dict:
    return {key: value for key, value in config.items() if not key.startswith("_")}


def _version(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"unavailable: {error}"
    return (result.stdout or result.stderr).strip()


def _manifest(config: dict, run_id: str, planned: int, smoke: bool) -> dict:
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "smoke": smoke,
        "publication_state": "smoke" if smoke else "pending-score",
        "planned_runs": planned,
        "config": _public_config(config),
        "nerd_commit": _git_output(["rev-parse", "HEAD"]),
        "upstream_commit": config["upstream"]["commit"],
        "upstream_tag_object": config["upstream"]["tag_object"],
        "platform": platform.platform(),
        "python": platform.python_version(),
        "agent_versions": {
            "codex": _version(["codex", "--version"]),
            "claude": _version(["claude", "--version"]),
            "cursor": _version(["cursor", "agent", "--version"]),
        },
    }


def _case_index(config: dict) -> dict[str, BenchmarkCase]:
    return {case.id: case for case in _cases(config)}


def _smoke_specs(specs: tuple[RunSpec, ...]) -> tuple[RunSpec, ...]:
    if not specs:
        return ()
    smoke_agent = specs[0].agent
    chosen = []
    for spec in specs:
        comparison = spec.run_id.split("--", 1)[0]
        if spec.agent != smoke_agent or spec.repetition != 1:
            continue
        if spec.case_id != SMOKE_CASES[comparison]:
            continue
        chosen.append(spec)
    return tuple(chosen)


def run_matrix(
    config: dict,
    results_root: Path,
    *,
    smoke: bool = False,
    resume: str | None = None,
) -> Path:
    if resume:
        result_dir = results_root / resume
        if not result_dir.is_dir():
            raise FileNotFoundError(f"unknown result run: {resume}")
        run_id = resume
        manifest = json.loads((result_dir / "manifest.json").read_text())
        if manifest.get("config") != _public_config(config):
            raise ValueError("resume config differs from original manifest")
        smoke = bool(manifest["smoke"])
    else:
        run_id = _run_id(config)
        result_dir = create_run_directory(results_root, run_id)

    workspace_root = ROOT / "benchmarks" / "work" / run_id
    specs = schedule_runs(config, workspace_root)
    if smoke:
        specs = _smoke_specs(specs)

    if not resume:
        manifest = _manifest(config, run_id, len(specs), smoke)
        (result_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    raw_path = result_dir / "raw.jsonl"
    completed = set()
    if raw_path.is_file():
        for line in raw_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                completed.add(json.loads(line)["run_id"])

    cases = _case_index(config)
    with raw_path.open("a", encoding="utf-8") as output:
        for spec in specs:
            if spec.run_id in completed:
                continue
            try:
                result, diff_hash = execute_run(cases[spec.case_id], spec)
                record = result_record(result, diff_hash)
            except Exception as error:
                record = {
                    "run_id": spec.run_id,
                    "case_id": spec.case_id,
                    "condition": spec.condition,
                    "agent": spec.agent,
                    "model": spec.model,
                    "target_id": spec.target_id,
                    "reasoning_effort": spec.reasoning_effort,
                    "repetition": spec.repetition,
                    "exit_code": -1,
                    "elapsed_seconds": 0.0,
                    "final_text": "",
                    "output_tokens": None,
                    "events": [{"type": "harness_error", "message": str(error)}],
                    "changed_files": [],
                    "command_results": {},
                    "diff_sha256": None,
                }
            output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()

    (results_root / "LATEST").write_text(run_id + "\n", encoding="utf-8")
    return result_dir
