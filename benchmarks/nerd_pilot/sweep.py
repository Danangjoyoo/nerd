"""Run the full Nerd pilot sweep: 3 cases × 3 reps × 3 models = 27 runs.

Each run writes its own result.json under
`benchmarks/results/nerd-pilot/sweep-<UTC>/<model>/<case>/rep-<n>/`.
An aggregate `summary.json` is written at the sweep root and printed on
completion.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
IGNORED_RESULTS = REPO_ROOT / "benchmarks/results/nerd-pilot"

sys.path.insert(0, str(HERE))
from run import run as run_case  # noqa: E402


MODELS = (
    "claude-opus-5",
    "claude-sonnet-5",
    "claude-haiku-4-5",
)
CASES = ("case1", "case2", "case3")
REPS = 3


def _stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    sorted_values = sorted(values)
    n = len(sorted_values)
    mean = sum(sorted_values) / n
    median = (
        sorted_values[n // 2]
        if n % 2
        else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    )
    return {
        "n": n,
        "mean": round(mean, 3),
        "median": round(median, 3),
        "min": round(min(sorted_values), 3),
        "max": round(max(sorted_values), 3),
    }


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    sweep_root = IGNORED_RESULTS / f"sweep-{stamp}"
    sweep_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    runs: list[dict] = []
    started = time.perf_counter()
    for model in MODELS:
        for case_id in CASES:
            for rep in range(1, REPS + 1):
                case_file = HERE / "cases" / f"{case_id}.md"
                out_dir = sweep_root / model / case_id / f"rep-{rep}"
                out_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
                print(
                    f"[{time.strftime('%H:%M:%S')}] running {model} / {case_id} / rep-{rep} ...",
                    flush=True,
                )
                try:
                    outcome = run_case(model, case_file, case_id)
                except Exception:  # noqa: BLE001
                    outcome = {
                        "ok": False,
                        "model": model,
                        "case_id": case_id,
                        "rep": rep,
                        "exception": traceback.format_exc(),
                    }
                outcome["model"] = model
                outcome["case_id"] = case_id
                outcome["rep"] = rep
                (out_dir / "result.json").write_text(
                    json.dumps(outcome, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                runs.append(outcome)
                status = (
                    f"score={(outcome.get('accuracy') or {}).get('score')}"
                    f"/{(outcome.get('accuracy') or {}).get('maximum')} "
                    f"wall={outcome.get('wall_clock_seconds')}s "
                    f"out={((outcome.get('usage') or {}).get('output_tokens'))}tok "
                    f"${outcome.get('total_cost_usd')}"
                )
                print(f"  -> {status}", flush=True)
    total_wall = time.perf_counter() - started

    # Aggregate per-model and per-case.
    def aggregate(subset: list[dict]) -> dict:
        oks = [r for r in subset if r.get("ok") and r.get("accuracy")]
        scores = [r["accuracy"]["score"] for r in oks]
        accuracies = [r["accuracy"]["accuracy_percent"] for r in oks]
        walls = [r["wall_clock_seconds"] for r in oks if r.get("wall_clock_seconds")]
        outputs = [
            r["usage"]["output_tokens"]
            for r in oks
            if (r.get("usage") or {}).get("output_tokens")
        ]
        costs = [r["total_cost_usd"] for r in oks if r.get("total_cost_usd")]
        return {
            "runs": len(subset),
            "successful": len(oks),
            "score": _stats(scores),
            "accuracy_percent": _stats(accuracies),
            "wall_clock_seconds": _stats(walls),
            "output_tokens": _stats(outputs),
            "total_cost_usd": _stats(costs),
        }

    per_model = {model: aggregate([r for r in runs if r["model"] == model]) for model in MODELS}
    per_case_model = {
        model: {case: aggregate([r for r in runs if r["model"] == model and r["case_id"] == case])
                for case in CASES}
        for model in MODELS
    }
    summary = {
        "sweep_root": str(sweep_root),
        "models": MODELS,
        "cases": CASES,
        "reps": REPS,
        "total_runs": len(runs),
        "sweep_wall_seconds": round(total_wall, 3),
        "per_model": per_model,
        "per_model_per_case": per_case_model,
        "overall": aggregate(runs),
    }
    (sweep_root / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
