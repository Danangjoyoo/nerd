#!/usr/bin/env python3
"""Command-line interface for Nerd's reproducible benchmark harness."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.nerdbench.report import publish_readme, write_report
from benchmarks.nerdbench.runner import load_config, run_matrix, schedule_runs
from benchmarks.nerdbench.scorer import score_result_directory


DEFAULT_CONFIG = ROOT / "benchmarks" / "config.json"
RESULTS_ROOT = ROOT / "benchmarks" / "results"


def _config(value: str) -> dict:
    return load_config((ROOT / value).resolve() if not Path(value).is_absolute() else Path(value))


def _result_dir(args) -> Path:
    if getattr(args, "latest", False):
        latest = RESULTS_ROOT / "LATEST"
        if not latest.is_file():
            raise FileNotFoundError("benchmarks/results/LATEST is missing")
        return RESULTS_ROOT / latest.read_text(encoding="utf-8").strip()
    value = getattr(args, "results", None)
    if not value:
        raise ValueError("select --latest or --results")
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _add_result_selector(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--latest", action="store_true")
    group.add_argument("--results")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="list planned runs without invoking agents")
    plan.add_argument("--config", default=str(DEFAULT_CONFIG))

    run = subparsers.add_parser("run", help="execute benchmark runs")
    run.add_argument("--config", default=str(DEFAULT_CONFIG))
    mode = run.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--release", action="store_true")
    run.add_argument("--resume")

    score = subparsers.add_parser("score", help="derive scores from raw evidence")
    score.add_argument("--config", default=str(DEFAULT_CONFIG))
    _add_result_selector(score)

    report = subparsers.add_parser("report", help="derive or check summary artifacts")
    _add_result_selector(report)
    report.add_argument("--check", action="store_true")

    publish = subparsers.add_parser("publish", help="sync release evidence to README")
    _add_result_selector(publish)
    publish.add_argument("--readme", default=str(ROOT / "README.md"))
    publish.add_argument("--check", action="store_true")
    publish.add_argument("--allow-historical", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        config = _config(args.config)
        runs = schedule_runs(config, ROOT / "benchmarks" / "work" / "planned")
        for run in runs:
            print(run.run_id)
        print(f"{len(runs)} planned agent runs")
        return 0

    if args.command == "run":
        config = _config(args.config)
        result = run_matrix(
            config,
            RESULTS_ROOT,
            smoke=args.smoke,
            resume=args.resume,
        )
        print(result.relative_to(ROOT))
        return 0

    if args.command == "score":
        config = _config(args.config)
        result = _result_dir(args)
        scores = score_result_directory(result, config)
        print(f"{len(scores)} scored agent runs")
        return 0

    if args.command == "report":
        result = _result_dir(args)
        summary = write_report(result, check=args.check)
        print(f"{summary['publication_state']} {summary['run_id']}")
        return 0

    if args.command == "publish":
        result = _result_dir(args)
        readme = Path(args.readme)
        if not readme.is_absolute():
            readme = (ROOT / readme).resolve()
        summary = publish_readme(
            result,
            readme,
            results_root=RESULTS_ROOT,
            repository_root=ROOT,
            check=args.check,
            allow_historical=args.allow_historical,
        )
        print(f"synchronized {summary['run_id']}")
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
