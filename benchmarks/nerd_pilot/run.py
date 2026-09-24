"""Run one Nerd pilot case via a Claude Code sub-session and score it.

Wall-clock duration and token usage come from the real `claude -p
--output-format json` payload, not from self-report. Accuracy is scored
by the deterministic rubric in `rubric.py`.

Sub-session is read-only: `--permission-mode plan` prevents any mutation
of the working tree.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
IGNORED_RESULTS = REPO_ROOT / "benchmarks/results/nerd-pilot"

sys.path.insert(0, str(HERE))
from rubric import score  # noqa: E402


def run(model: str, case_path: Path, case_id: str) -> dict:
    prompt = case_path.read_text(encoding="utf-8")
    claude = shutil.which("claude")
    if claude is None:
        raise RuntimeError("claude CLI not on PATH")
    started_wall = time.perf_counter()
    # Repo-read-only + Nerd MCP writes to user-local sqlite: allow the three
    # Context tools, the three Memory tools, Skill, and Read; keep Edit/Write
    # and free-form Bash off the allowlist so the sub-session cannot mutate the
    # working tree.
    allowed_tools = " ".join((
        "Skill",
        "Read",
        "mcp__nerd-context-tools__context_recall",
        "mcp__nerd-context-tools__context_capture",
        "mcp__nerd-context-tools__context_inspect",
        "mcp__nerd-memory-tools__memory_recall",
        "mcp__nerd-memory-tools__memory_record",
        "mcp__nerd-memory-tools__memory_inspect",
    ))
    completed = subprocess.run(
        [
            claude,
            "-p",
            "--model", model,
            "--output-format", "json",
            "--input-format", "text",
            "--allowedTools", allowed_tools,
        ],
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )
    wall_seconds = time.perf_counter() - started_wall
    if completed.returncode != 0:
        return {
            "ok": False,
            "model": model,
            "wall_clock_seconds": wall_seconds,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
        }
    try:
        events = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return {
            "ok": False,
            "model": model,
            "wall_clock_seconds": wall_seconds,
            "error": f"invalid claude JSON: {error}",
            "stdout_tail": completed.stdout[-4000:],
        }
    if isinstance(events, list):
        payload = next(
            (event for event in reversed(events) if event.get("type") == "result"),
            {},
        )
    elif isinstance(events, dict):
        payload = events
    else:
        payload = {}
    result_text = payload.get("result", "")
    accuracy = score(result_text, case_id)
    usage = payload.get("usage", {})
    return {
        "ok": not payload.get("is_error", False),
        "model": payload.get("modelUsage", {}).get(model, {}).get("model", model)
                 if isinstance(payload.get("modelUsage"), dict) else model,
        "session_id": payload.get("session_id"),
        "wall_clock_seconds": round(wall_seconds, 3),
        "claude_duration_ms": payload.get("duration_ms"),
        "claude_duration_api_ms": payload.get("duration_api_ms"),
        "ttft_ms": payload.get("ttft_ms"),
        "num_turns": payload.get("num_turns"),
        "total_cost_usd": payload.get("total_cost_usd"),
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        },
        "accuracy": accuracy,
        "result_text": result_text,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("--case", default=str(HERE / "cases" / "case1.md"))
    parser.add_argument("--case-id", default="case1")
    parser.add_argument("--label", default="opus-5-default")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output = IGNORED_RESULTS / f"{stamp}-{args.label}"
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    outcome = run(args.model, Path(args.case), args.case_id)
    (output / "result.json").write_text(
        json.dumps(outcome, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = {
        "path": str(output),
        "model": outcome.get("model"),
        "ok": outcome.get("ok"),
        "wall_clock_seconds": outcome.get("wall_clock_seconds"),
        "claude_duration_ms": outcome.get("claude_duration_ms"),
        "total_cost_usd": outcome.get("total_cost_usd"),
        "usage": outcome.get("usage"),
        "accuracy_percent": (outcome.get("accuracy") or {}).get("accuracy_percent"),
        "score": (outcome.get("accuracy") or {}).get("score"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if outcome.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
