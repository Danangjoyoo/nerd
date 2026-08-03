from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from benchmarks.nerdbench.runner import load_config, schedule_runs
from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.scorer import judge_tasks
from benchmarks.nerdbench.ufast_report import (
    CASE_SHA256,
    SOURCE_HASH_KEYS,
    UFAST_END,
    UFAST_START,
    current_source_hashes,
    publish_ufast_readme,
    render_ufast_readme,
    summarize_ufast,
    write_ufast_summary,
)
from benchmarks.run import build_parser


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks" / "pilots" / "ufast-vs-xfast"
CASES = ROOT / "benchmarks" / "cases" / "ufast-phase1-verification.json"
ORIGINAL_CASES = ROOT / "benchmarks" / "pilots" / "xfast-v3-five-cases" / "cases.json"
CASE_FILE = "benchmarks/cases/ufast-phase1-verification.json"
CASE_IDS = (
    "xfast-v3-discovery-edit",
)
TARGETS = {
    "Luna": ("gpt-5.6-luna-high", "gpt-5.6-luna"),
    "Terra": ("gpt-5.6-terra-high", "gpt-5.6-terra"),
}


def source_hashes() -> dict[str, str]:
    values = current_source_hashes()
    assert set(values) == set(SOURCE_HASH_KEYS)
    return values


def tool_calls(*, applied: bool = True) -> list[dict]:
    return [
        {
            "type": "ufast_tool_call",
            "tool": "ufast_project_index",
            "status": "ready",
            "runtime_version": "0.3.0",
            "operation_ms": 2,
            "cold_start_ms": 11,
            "changed_files": [],
            "checks": [],
            "rolled_back": False,
            "route": "project_index",
            "backend": "memory_project_map",
            "cache_status": "rebuilt",
        },
        {
            "type": "ufast_tool_call",
            "tool": "ufast_fast_search",
            "status": "matched",
            "runtime_version": "0.3.0",
            "operation_ms": 1,
            "cold_start_ms": 11,
            "changed_files": [],
            "checks": [],
            "rolled_back": False,
            "route": "search_project",
            "backend": "memory_project_map",
            "cache_status": "hit",
        },
        {
            "type": "ufast_tool_call",
            "tool": "ufast_safe_edit",
            "status": "applied" if applied else "verification_failed",
            "runtime_version": "0.3.0",
            "operation_ms": 8,
            "cold_start_ms": 11,
            "changed_files": ["feature.py"] if applied else [],
            "checks": [{"name": "syntax", "exit_code": 0}],
            "rolled_back": not applied,
            "route": "safe_edit",
            "backend": "workspace_transaction",
            "cache_status": None,
            **({"reason": "verification failed"} if not applied else {}),
        },
    ]


def write_result_fixture(
    root: Path,
    label: str,
    target_id: str,
    model: str,
    *,
    ufast_seconds: float = 6.0,
    xfast_seconds: float = 10.0,
    ufast_tokens: int | None = 500,
    xfast_tokens: int | None = 1000,
    applied: bool = True,
) -> Path:
    result = root / label.casefold()
    result.mkdir()
    manifest = {
        "run_id": f"ufast-{label.casefold()}",
        "created_at": "2026-08-03T00:00:00+00:00",
        "smoke": False,
        "publication_state": "pending-score",
        "planned_runs": 2,
        "nerd_commit": "deadbeef",
        "agent_versions": {"codex": "codex-cli test"},
        "source_hashes": source_hashes(),
        "config": {
            "agents": ["codex"],
            "models": {"codex": model},
            "target": {
                "id": target_id,
                "display_name": f"GPT 5.6 {label} · high · UFast vs XFast",
                "reasoning_effort": "high",
            },
            "case_files": [CASE_FILE],
            "conditions": {"xfast": ["nerd-xfast", "nerd-ufast"]},
            "repetitions": 1,
            "parallelism": 1,
            "seed": 8032026,
        },
    }
    raw = []
    scores = []
    for case_id in CASE_IDS:
        for condition in ("nerd-xfast", "nerd-ufast"):
            treatment = condition == "nerd-ufast"
            run_id = f"{target_id}-{case_id}-{condition}"
            calls = tool_calls(applied=applied) if treatment else []
            raw.append(
                {
                    "run_id": run_id,
                    "case_id": case_id,
                    "condition": condition,
                    "agent": "codex",
                    "model": model,
                    "target_id": target_id,
                    "reasoning_effort": "high",
                    "repetition": 1,
                    "exit_code": 0,
                    "elapsed_seconds": ufast_seconds if treatment else xfast_seconds,
                    "output_tokens": ufast_tokens if treatment else xfast_tokens,
                    "events": calls,
                    "changed_files": ["feature.py"],
                    "command_results": {"python3 -m unittest verify_behavior -v": 0},
                    "ufast_evidence": {
                        "runtime_present": treatment,
                        "config_present": treatment,
                        "user_config_ignored": not treatment,
                        "tool_calls": calls,
                    },
                }
            )
            scores.append(
                {
                    "run_id": run_id,
                    "score": 90.0 if treatment else 100.0,
                    "passed": True,
                    "hard_gate_failures": [],
                    "criterion_results": {},
                    "judge_valid": True,
                }
            )
    (result / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (result / "raw.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in raw),
        encoding="utf-8",
    )
    (result / "scores.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in scores),
        encoding="utf-8",
    )
    return result


def write_matrix(root: Path, **overrides) -> list[Path]:
    return [
        write_result_fixture(root, label, target_id, model, **overrides)
        for label, (target_id, model) in TARGETS.items()
    ]


class UFastScheduleTests(unittest.TestCase):
    def test_blinded_judge_uses_the_configured_ufast_xfast_pair(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = write_result_fixture(
                Path(temporary),
                "Luna",
                "gpt-5.6-luna-high",
                "gpt-5.6-luna",
            )
            records = [
                json.loads(line)
                for line in (result / "raw.jsonl").read_text().splitlines()
            ]
        cases = {case.id: case for case in load_cases(CASES)}
        tasks = judge_tasks(
            records,
            cases,
            8032026,
            pair_conditions={"xfast": ("nerd-xfast", "nerd-ufast")},
        )
        self.assertEqual(len(tasks), 1)
        self.assertEqual({task["case_id"] for task in tasks}, set(CASE_IDS))

    def test_uses_one_immutable_case_and_plans_four_runs(self):
        self.assertEqual(hashlib.sha256(CASES.read_bytes()).hexdigest(), CASE_SHA256)
        copied = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        original = json.loads(ORIGINAL_CASES.read_text(encoding="utf-8"))["cases"]
        expected = [case for case in original if case["id"] == CASE_IDS[0]]
        self.assertEqual(copied, expected)
        all_ids = set()
        for label, (target_id, model) in TARGETS.items():
            config = load_config(PILOT / f"{target_id}.json")
            self.assertEqual(config["models"], {"codex": model})
            self.assertEqual(config["case_files"], [CASE_FILE])
            self.assertEqual(config["target"]["reasoning_effort"], "high")
            self.assertEqual(config["repetitions"], 1)
            self.assertEqual(config["parallelism"], 1)
            self.assertEqual(
                config["conditions"],
                {"xfast": ["nerd-xfast", "nerd-ufast"]},
            )
            runs = schedule_runs(config, ROOT / "benchmarks" / "work" / label)
            self.assertEqual(len(runs), 2)
            self.assertEqual({run.condition for run in runs}, {"nerd-xfast", "nerd-ufast"})
            self.assertTrue(all(run.run_id not in all_ids for run in runs))
            all_ids.update(run.run_id for run in runs)
        self.assertEqual(len(all_ids), 4)


class UFastReportTests(unittest.TestCase):
    def test_summarizes_two_pairs_with_tool_and_timing_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_ufast(write_matrix(Path(temporary)))
        self.assertEqual(summary["aggregate"]["pairs"], 2)
        self.assertEqual(summary["models"]["Luna"]["pairs"], 1)
        self.assertEqual(summary["models"]["Luna"]["delta"]["accuracy_points"], -10.0)
        self.assertEqual(summary["models"]["Luna"]["delta"]["speed_percent"], 40.0)
        self.assertEqual(summary["models"]["Luna"]["delta"]["token_change_percent"], -50.0)
        tools = summary["models"]["Luna"]["ufast_tools"]
        self.assertEqual(tools["hit_rate_percent"], 100.0)
        self.assertEqual(tools["fallback_runs"], 0)
        self.assertEqual(tools["median_cold_start_ms"], 11.0)
        self.assertEqual(tools["median_operation_ms"], 11.0)
        self.assertEqual(tools["project_index_runs"], 1)
        self.assertEqual(tools["fast_search_runs"], 1)
        self.assertEqual(summary["controls"]["workload_runs"], 4)
        self.assertEqual(summary["controls"]["pairs"], 2)
        self.assertEqual(summary["controls"]["verified_host"], "Codex")

    def test_missing_tokens_are_unavailable_and_negative_results_are_honest(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = summarize_ufast(
                write_matrix(Path(temporary), ufast_tokens=None)
            )
        self.assertIsNone(missing["aggregate"]["delta"]["token_change_percent"])
        self.assertIn("Unavailable", render_ufast_readme(missing))

        with tempfile.TemporaryDirectory() as temporary:
            slower = summarize_ufast(
                write_matrix(
                    Path(temporary),
                    ufast_seconds=12.0,
                    ufast_tokens=1200,
                )
            )
        rendered = render_ufast_readme(slower)
        self.assertIn("20.00% slower", rendered)
        self.assertIn("20.00% more", rendered)

    def test_counts_fallbacks_but_requires_every_ufast_run_to_call_a_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            summary = summarize_ufast(write_matrix(base, applied=False))
            self.assertEqual(summary["aggregate"]["ufast_tools"]["fallback_runs"], 2)

        with tempfile.TemporaryDirectory() as temporary:
            paths = write_matrix(Path(temporary))
            raw_path = paths[0] / "raw.jsonl"
            records = [json.loads(line) for line in raw_path.read_text().splitlines()]
            treatment = next(item for item in records if item["condition"] == "nerd-ufast")
            treatment["events"] = []
            treatment["ufast_evidence"]["tool_calls"] = []
            raw_path.write_text(
                "".join(json.dumps(item) + "\n" for item in records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "tool call"):
                summarize_ufast(paths)

    def test_rejects_xfast_leaks_and_incomplete_or_drifted_evidence(self):
        mutations = ("xfast leak", "missing run", "source drift", "failed score")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                paths = write_matrix(Path(temporary))
                if mutation == "source drift":
                    manifest_path = paths[0] / "manifest.json"
                    manifest = json.loads(manifest_path.read_text())
                    manifest["source_hashes"]["ufast_skill"] = "b" * 64
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                elif mutation == "failed score":
                    scores_path = paths[0] / "scores.jsonl"
                    scores = [json.loads(line) for line in scores_path.read_text().splitlines()]
                    scores[0]["passed"] = False
                    scores[0]["hard_gate_failures"] = ["behavior"]
                    scores_path.write_text(
                        "".join(json.dumps(item) + "\n" for item in scores),
                        encoding="utf-8",
                    )
                else:
                    raw_path = paths[0] / "raw.jsonl"
                    records = [json.loads(line) for line in raw_path.read_text().splitlines()]
                    if mutation == "missing run":
                        records.pop()
                    else:
                        control = next(item for item in records if item["condition"] == "nerd-xfast")
                        control["ufast_evidence"]["runtime_present"] = True
                    raw_path.write_text(
                        "".join(json.dumps(item) + "\n" for item in records),
                        encoding="utf-8",
                    )
                with self.assertRaises(ValueError):
                    summarize_ufast(paths)

    def test_writes_and_checks_one_deterministic_readme_region(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            paths = write_matrix(base)
            output = base / "result.json"
            summary = write_ufast_summary(paths, output)
            self.assertEqual(json.loads(output.read_text()), summary)
            readme = base / "README.md"
            readme.write_text("# Demo\n", encoding="utf-8")
            publish_ufast_readme(summary, readme)
            body = readme.read_text(encoding="utf-8")
            self.assertEqual(body.count(UFAST_START), 1)
            self.assertEqual(body.count(UFAST_END), 1)
            self.assertIn("one Python discovery/edit verification case", body)
            self.assertIn("one repetition", body)
            self.assertIn("4 fresh Codex processes", body)
            publish_ufast_readme(summary, readme, check=True)
            readme.write_text(body.replace("40.00% faster", "39.00% faster", 1))
            with self.assertRaisesRegex(ValueError, "out of date"):
                publish_ufast_readme(summary, readme, check=True)

    def test_cli_requires_two_results_and_explicit_summary(self):
        parser = build_parser()
        report = parser.parse_args(
            [
                "ufast-report",
                "--results",
                "luna",
                "terra",
                "--output",
                "result.json",
            ]
        )
        self.assertEqual(report.results, ["luna", "terra"])
        publish = parser.parse_args(
            [
                "ufast-publish",
                "--summary",
                "result.json",
                "--readme",
                "README.md",
                "--check",
            ]
        )
        self.assertTrue(publish.check)


if __name__ == "__main__":
    unittest.main()
