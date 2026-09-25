"""Replay native projection evidence and measure unchanged fixture capacity.

Required labels are used ONLY for a diagnostic necessary-facts lower bound.
The original ranker receives the original query and complete original ledger.
No result here is a new benchmark verdict, measured-token gate, or production
reservation proof. The native timing/item identifiers are one observed frame.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

from deployable_response import json_bytes, mcp_result, observed_codex_http_projection, serialize_recall
from fixtures import active_records, load_cases, required_records
from response_wire_probe import CALL_ID, ERROR_CALL_ID, PAYLOAD, ERROR_PAYLOAD, HERE, ROOT, sha, write_json
from structured import StructuredLedger


PROTOCOL = "full-context-response-capacity-diagnostic-v1"


def projections_from_archive(probe_root):
    manifest_bytes = (probe_root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("protocol") != "offline-context-response-projection-v2" or manifest.get("live_model_requests") != 0:
        raise ValueError("wrong native projection evidence protocol")
    for name, expected in manifest["files"].items():
        if sha((probe_root / name).read_bytes()) != expected:
            raise ValueError("native projection evidence digest mismatch")
    raw = json.loads((probe_root / "raw.json").read_bytes())
    if raw["exit_code"] != 0 or raw["aborted"] or raw["errors"] or raw["live_model_requests"] != 0:
        raise ValueError("native projection observation failed")
    projections = {}
    items = json.loads((probe_root / "projection.json").read_bytes())["items"]
    if len(items) != 2 or {item["call_id"] for item in items} != {CALL_ID, ERROR_CALL_ID}:
        raise ValueError("missing native success or overflow observation")
    for item in items:
        if set(item) != {"type", "call_id", "id", "output"} or item["type"] != "function_call_output":
            raise ValueError("unsupported native output shape")
        match = re.match(r"Wall time: ([0-9]+\.[0-9]{4}) seconds\nOutput:\n", item["output"])
        if match is None:
            raise ValueError("unsupported native output header")
        project = observed_codex_http_projection(call_id=item["call_id"], output_id=item["id"], wall_seconds=match[1])
        payload = PAYLOAD if item["call_id"] == CALL_ID else ERROR_PAYLOAD
        if project(mcp_result(payload)) != json_bytes(item):
            raise ValueError("native projection does not replay exactly")
        projections[item["call_id"]] = project
    return projections, sha(manifest_bytes), raw["client_version"]


def capacity_rows(project):
    rows = []
    for case in load_cases(HERE / "cases.json"):
        if case["category"] == "short_control":
            continue
        records = active_records(case)
        lookup = {item["id"]: item for item in records}
        with StructuredLedger(records) as ledger:
            original = ledger.recall(context_id=case["context_id"], query=case["request"])
        required = required_records(case)
        selected = [lookup[identifier] for identifier in original.record_ids]
        row = {"case_id": case["id"], "original_pack_bytes": len(original.segment.encode()),
               "original_required_recall": len(set(original.record_ids) & {item["id"] for item in required}) / len(required)}
        # Evaluation-only lower bounds never influence original selection.
        for name, candidate in (("original_selected", selected), ("required_only", required),
                                ("mandatory_only", [item for item in records if item["active"] and item["kind"] in {"goal", "boundary", "decision"}])):
            observations = []
            def observe(result):
                rendered = project(result)
                if result["structuredContent"]["status"] == "ok":
                    observations.append((result["structuredContent"], rendered))
                return rendered
            response = serialize_recall(context_id=case["context_id"], records=candidate, project=observe,
                                        projection_name="codex-0.153.4-http-one-observed-frame")
            attempted_payload, attempted_item = observations[-1]
            row[name] = {"record_count": len(candidate), "status": response.payload["status"],
                         "attempted_complete_bytes": response.attempted_bytes,
                         "candidate_payload_json_bytes": len(json_bytes(attempted_payload)),
                         "candidate_native_output_text_bytes": len(json.loads(attempted_item)["output"].encode()),
                         "returned_complete_bytes": len(response.model_visible_bytes)}
        rows.append(row)
    return rows


def run(probe_root, output):
    projects, probe_manifest_sha, version = projections_from_archive(probe_root)
    sources = {name: sha((HERE / name).read_bytes()) for name in (
        "deployable_response.py", "test_deployable_response.py", "response_wire_probe.py", "test_response_wire_probe.py",
        "response_contract_audit.py", "structured.py", "fixtures.py", "cases.json")}
    rows = capacity_rows(projects[CALL_ID])
    summary = {"protocol": PROTOCOL, "client_version": version, "cases": len(rows), "live_model_requests": 0,
               "native_success_and_overflow_replay": True,
               "original_required_recall_min": min(row["original_required_recall"] for row in rows),
               "original_pack_bytes": [min(row["original_pack_bytes"] for row in rows), max(row["original_pack_bytes"] for row in rows)]}
    for name in ("original_selected", "required_only", "mandatory_only"):
        summary[name] = {"fits": sum(row[name]["status"] == "ok" for row in rows),
                         "overflow": sum(row[name]["status"] == "overflow" for row in rows),
                         "attempted_complete_bytes": [min(row[name]["attempted_complete_bytes"] for row in rows),
                                                      max(row[name]["attempted_complete_bytes"] for row in rows)]}
        for field in ("candidate_payload_json_bytes", "candidate_native_output_text_bytes"):
            summary[name][field] = [min(row[name][field] for row in rows), max(row[name][field] for row in rows)]
    summary["limitations"] = ["Complete native item is counted conservatively as canonical UTF-8 JSON, including identity and escaped output.",
                              "Whole-item policy is not an observed upstream model-visible serialization/tokenization; overflows under it do not prove intrinsic schema impossibility.",
                              "Only one observed native timing/identity frame; no future metadata reservation or other-client proof.",
                              "No anchors exist in these fixtures; supplied anchors may increase bytes and are never removed.",
                              "Required-only is a diagnostic capacity lower bound, not a candidate ranking strategy.",
                              "No model token, billing, quality, latency, lifecycle, storage-fairness, or acceptance verdict."]
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name in sources:
        target = output / "source-snapshot" / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(HERE / name, target)
    write_json(output / "rows.json", rows)
    write_json(output / "summary.json", summary)
    if sources != {name: sha((HERE / name).read_bytes()) for name in sources}:
        raise ValueError("source changed during capacity audit")
    manifest = {"protocol": PROTOCOL, "probe_root": str(probe_root), "probe_manifest_sha256": probe_manifest_sha,
                "sources": sources, "live_model_requests": 0,
                "files": {str(path.relative_to(output)): sha(path.read_bytes()) for path in output.rglob("*") if path.is_file()}}
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"output": str(output), "manifest_sha256": sha((output / "manifest.json").read_bytes()), "summary": summary}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run(args.probe_root, args.output or ROOT / "benchmarks/results/nerd-context" / ("response-capacity-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")))
