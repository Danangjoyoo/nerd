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
        elapsed_ms([sys.executable, str(INDEXER), "find", args.symbol, *common])
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
