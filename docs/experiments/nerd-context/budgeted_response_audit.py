"""Offline source-bound capacity evidence, preserving failed required recall."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request

from budgeted_response import CLIENT_VERSION, MAX_DURATION_TEXT, recall_from_ledger, verify_native_output
from fixtures import active_records, load_cases, required_records
from response_wire_probe import HERE, ROOT, sha, write_json
from structured import StructuredLedger


UPSTREAM = {
    "context.rs": ("codex-rs/core/src/tools/context.rs", "e9bc2f7d5a749fc5cf49989fd7a4e1dfe171c723e12c50c723d34f8ebefeff54"),
    "models.rs": ("codex-rs/protocol/src/models.rs", "22c4496e666cb3078abb8f82ce623c21695bd639cf38f7a33f93fb6d8d280190"),
    "output-truncation.rs": ("codex-rs/utils/output-truncation/src/lib.rs", "5fc339793e2d2bb680b8627b0632329b98145c66a5ad58ef70f83c2c0e4720fe"),
}
RUST_PROOF = '''fn main() {
    for d in [std::time::Duration::ZERO, std::time::Duration::MAX] {
        let w = d.as_secs_f64();
        let h = format!("Wall time: {w:.4} seconds\\nOutput:\\n");
        println!("{} {:?}", h.len(), h);
    }
}
'''


def run(output):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    names = ("budgeted_response.py", "test_budgeted_response.py", "budgeted_response_audit.py", "deployable_response.py",
             "structured.py", "fixtures.py", "cases.json", "response_wire_probe.py")
    sources = {name: sha((HERE / name).read_bytes()) for name in names}
    for name in sources:
        target = output / "source-snapshot" / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(HERE / name, target)
    provenance = {}
    for name, (path, expected) in UPSTREAM.items():
        url = "https://raw.githubusercontent.com/openai/codex/rust-v0.153.4/" + path
        content = urllib.request.urlopen(url, timeout=20).read()
        if sha(content) != expected:
            raise ValueError("pinned upstream source changed")
        (output / name).write_bytes(content)
        provenance[name] = {"url": url, "sha256": expected}
    (output / "duration-proof.rs").write_text(RUST_PROOF)
    with tempfile.TemporaryDirectory(prefix="context-duration-bound-") as temporary:
        executable = Path(temporary) / "duration-proof"
        subprocess.run(["rustc", str(output / "duration-proof.rs"), "-o", str(executable)], check=True, capture_output=True)
        rust = subprocess.run([str(executable)], check=True, capture_output=True, text=True).stdout
    if not rust.startswith('34 "Wall time: 0.0000') or '\n53 "Wall time: 18446744073709551616.0000' not in rust:
        raise ValueError("Duration-domain prefix bound did not replay")
    version = subprocess.run(["codex", "--version"], check=True, capture_output=True, text=True).stdout.strip()
    if version != CLIENT_VERSION:
        raise ValueError("unsupported installed native client")
    launcher = Path(shutil.which("codex")).resolve()
    native_candidates = list(launcher.parent.parent.glob("node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex"))
    if len(native_candidates) != 1:
        raise ValueError("native binary identity not established for this audit host")
    proof = {"client_version": version, "launcher_path": str(launcher), "launcher_sha256": sha(launcher.read_bytes()),
             "native_binary_path": str(native_candidates[0]), "native_binary_sha256": sha(native_candidates[0].read_bytes()),
             "upstream_sources": provenance, "rust_proof_stdout": rust,
             "rustc_version": subprocess.run(["rustc", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
             "source_to_binary_reproducible_build": "not_established", "max_wrapper_bytes": 53}
    rows = []
    for case in load_cases(HERE / "cases.json"):
        if case["category"] == "short_control":
            continue
        modes = []
        records = active_records(case)
        required = {item["id"] for item in required_records(case)}
        mandatory = {item["id"] for item in records if item["active"] and item["kind"] in {"goal", "boundary", "decision"}}
        for mode in ("normalized_scan", "fts5"):
            with StructuredLedger(records, index_mode=mode) as ledger:
                result = recall_from_ledger(ledger, context_id=case["context_id"], query=case["request"])
            response = result.response
            # Model-free domain-bound rendering, explicitly not a native MCP run.
            maximum_text = "Wall time: " + MAX_DURATION_TEXT + " seconds\nOutput:\n" + json.dumps(response.payload, ensure_ascii=False, separators=(",", ":"))
            measures = verify_native_output(response, maximum_text)
            rows.append({"case_id": case["id"], "index_mode": mode, "record_ids": list(result.record_ids),
                         "payload": response.payload, "payload_sha256": sha(response.payload_json),
                         "required_recall": len(required & set(result.record_ids)) / len(required),
                         "mandatory_recall": len(mandatory & set(result.record_ids)) / len(mandatory),
                         "domain_bound_rendering": measures, "actual_native_run": False})
            modes.append(response.payload_json)
        if modes[0] != modes[1]:
            raise ValueError("canonical payload mode parity failed")
    selected_rows = rows[::2]
    summary = {"cases": len(selected_rows), "mode_rows": len(rows), "canonical_payload_mode_parity": True,
               "required_recall_mean": sum(row["required_recall"] for row in selected_rows) / len(selected_rows),
               "required_recall_min": min(row["required_recall"] for row in selected_rows),
               "complete_cases": sum(row["required_recall"] == 1 for row in selected_rows),
               "mandatory_recall_min": min(row["mandatory_recall"] for row in rows),
               "reserved_native_output_bytes": [min(row["domain_bound_rendering"]["budgeted_output_bytes"] for row in rows),
                                                max(row["domain_bound_rendering"]["budgeted_output_bytes"] for row in rows)],
               "required_recall_gate_pass": False, "full_experiment_verdict": "not_run", "live_model_requests": 0,
               "limitations": ["Domain-bound rendering is model-free, not actual native delivery of these new full responses.",
                                "Prior native success/error observations plus pinned source establish the projection mechanism.",
                                "Before sampling pin effective client truncation byte budget >=2048 and reject changed/truncated actual output.",
                                "No measured tokens, latency, lifecycle economics, fairness, generated capture or production gate claim."]}
    write_json(output / "proof.json", proof)
    write_json(output / "rows.json", rows)
    write_json(output / "summary.json", summary)
    if sources != {name: sha((HERE / name).read_bytes()) for name in names}:
        raise ValueError("private source changed during audit")
    manifest = {"protocol": "budgeted-full-context-capacity-v1", "sources": sources, "live_model_requests": 0,
                "files": {str(path.relative_to(output)): sha(path.read_bytes()) for path in output.rglob("*") if path.is_file()}}
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"output": str(output), "manifest_sha256": sha((output / "manifest.json").read_bytes()), "summary": summary}))


if __name__ == "__main__":
    run(ROOT / "benchmarks/results/nerd-context" / ("budgeted-response-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")))
