from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import baselines

PRODUCTION_TOOLS = (
    ROOT.parents[2] / "skills" / "nerd-ufast" / "scripts" / "ufast_tools.py"
)
SPEC = importlib.util.spec_from_file_location("production_ufast_tools", PRODUCTION_TOOLS)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load production tools: {PRODUCTION_TOOLS}")
production_tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(production_tools)


def candidate_inspect(index, **params):
    result = index.inspect(
        workspace=params["workspace"],
        queries=[{"symbol": params["symbol"]}],
        context_lines=params["context_lines"],
        max_results=params["max_results"],
        max_bytes=1_000_000,
    )
    return {
        "matches": result["results"][0]["matches"],
        "cache_hit": result["cache_hit"],
        "process_count": 0,
    }


def candidate_apply_verify(**params):
    checks = [{"argv": argv} for argv in params.pop("checks")]
    result = production_tools.apply_verify(checks=checks, **params)
    result["checks"] = [
        {"command": check["argv"], "exit_code": check["exit_code"]}
        for check in result["checks"]
    ]
    result["process_count"] = 2 + len(checks)
    return result


def main() -> int:
    index = production_tools.InspectIndex()
    for line in sys.stdin:
        request = json.loads(line)
        request_id = request["id"]
        method = request["method"]
        params = request.get("params", {})
        if method == "shutdown":
            response = {
                "id": request_id,
                "result": {"ok": True, "process_count": 0},
                "operation_ns": 0,
            }
            print(json.dumps(response, sort_keys=True), flush=True)
            return 0
        started = time.perf_counter_ns()
        try:
            if method == "ping":
                result = {"ok": True, "process_count": 0}
            elif method == "candidate.inspect":
                result = candidate_inspect(index, **params)
            elif method == "baseline.inspect":
                result = baselines.inspect(**params)
            elif method == "baseline.apply_patch":
                result = baselines.apply_patch(**params)
            elif method == "baseline.verify":
                result = baselines.verify(**params)
            elif method == "candidate.apply_verify":
                result = candidate_apply_verify(**params)
            else:
                raise ValueError(f"unknown method: {method}")
            response = {
                "id": request_id,
                "result": result,
                "operation_ns": time.perf_counter_ns() - started,
            }
        except Exception as error:
            response = {
                "id": request_id,
                "error": {"type": type(error).__name__, "message": str(error)},
                "operation_ns": time.perf_counter_ns() - started,
            }
        print(json.dumps(response, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
