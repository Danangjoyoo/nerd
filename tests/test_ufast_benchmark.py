from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from benchmarks.nerdbench.cases import load_cases
from benchmarks.nerdbench.runner import load_config, schedule_runs
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
CASE_IDS = ("xfast-v3-discovery-edit",)
TARGETS = {
    "Luna": ("gpt-5.6-luna-high", "gpt-5.6-luna"),
    "Terra": ("gpt-5.6-terra-high", "gpt-5.6-terra"),
}


def source_hashes() -> dict[str, str]:
    values = current_source_hashes()
    assert set(values) == set(SOURCE_HASH_KEYS)
    return values


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
) -> Path:
    result = root / label.casefold()
    result.mkdir()
    manifest = {
        "run_id": f"ufast-{label.casefold()}",
        "created_at": "2026-08-03T00:00:00+00:00",
        "smoke": False,
        "publication_state": "pending-score",
        "planned_runs": 2,
        "config": {
            "schema_version": 1,
            "agents": ["codex"],
            "models": {"codex": model},
            "target": {
                "id": target_id,
                "display_name": label,
                "reasoning_effort": "high",
            },
            "judge": {
                "agent": "codex",
                "model": "gpt-5.6-terra",
                "reasoning_effort": "xhigh",
                "timeout_seconds": 120,
            },
            "case_files": [CASE_FILE],
            "conditions": {"xfast": ["nerd-xfast", "nerd-ufast"]},
            "repetitions": 1,
            "parallelism": 1,
            "seed": 8032026,
        },
        "nerd_commit": "a" * 40,
        "source_hashes": source_hashes(),
        "agent_versions": {"codex": "codex-cli test"},
    }
    raw = []
    scores = []
    for condition in ("nerd-xfast", "nerd-ufast"):
        treatment = condition == "nerd-ufast"
        run_id = f"{target_id}-{condition}"
        raw.append(
            {
                "run_id": run_id,
                "case_id": CASE_IDS[0],
                "condition": condition,
                "agent": "codex",
                "model": model,
                "target_id": target_id,
                "reasoning_effort": "high",
                "repetition": 1,
                "exit_code": 0,
                "elapsed_seconds": ufast_seconds if treatment else xfast_seconds,
                "output_tokens": ufast_tokens if treatment else xfast_tokens,
                "events": [],
                "changed_files": [
                    "normalizers.py",
                    "registry.py",
                    "test_normalizers.py",
                ],
                "command_results": {"python3 -m unittest verify_behavior -v": 0},
                "diff_sha256": "b" * 64,
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
    def test_blinded_judge_uses_the_configured_prompt_pair(self):
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
        self.assertEqual(tasks[0]["case_id"], CASE_IDS[0])

    def test_uses_one_immutable_case_and_plans_four_runs(self):
        self.assertEqual(hashlib.sha256(CASES.read_bytes()).hexdigest(), CASE_SHA256)
        copied = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        original = json.loads(ORIGINAL_CASES.read_text(encoding="utf-8"))["cases"]
        self.assertEqual(copied, [case for case in original if case["id"] == CASE_IDS[0]])
        planned = []
        for config_path in sorted(PILOT.glob("gpt-5.6-*-high.json")):
            config = load_config(config_path)
            specs = schedule_runs(config, Path("/tmp/ufast-plan"))
            self.assertEqual(len(specs), 2)
            self.assertEqual({spec.condition for spec in specs}, {"nerd-xfast", "nerd-ufast"})
            planned.extend(specs)
        self.assertEqual(len(planned), 4)


class UFastReportTests(unittest.TestCase):
    def test_aggregates_prompt_only_matrix_and_renders_honestly(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary = summarize_ufast(write_matrix(Path(temporary)))
        self.assertTrue(summary["controls"]["prompt_only"])
        self.assertEqual(summary["controls"]["workload_runs"], 4)
        self.assertEqual(summary["aggregate"]["pairs"], 2)
        self.assertEqual(summary["aggregate"]["xfast"]["mean_score"], 100.0)
        self.assertEqual(summary["aggregate"]["ufast"]["mean_score"], 90.0)
        self.assertEqual(summary["aggregate"]["delta"]["speed_percent"], 40.0)
        self.assertEqual(summary["aggregate"]["delta"]["token_change_percent"], -50.0)
        rendered = render_ufast_readme(summary)
        self.assertIn("prompt-only three-wave execution", rendered)
        self.assertIn("no bundled scripts, MCP server, registry", rendered)
        self.assertIn("40.00% faster", rendered)
        self.assertIn("50.00% fewer", rendered)

    def test_missing_tokens_are_unavailable_and_negative_results_are_honest(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = summarize_ufast(write_matrix(Path(temporary), ufast_tokens=None))
        self.assertIsNone(missing["aggregate"]["delta"]["token_change_percent"])
        self.assertIn("Unavailable", render_ufast_readme(missing))

        with tempfile.TemporaryDirectory() as temporary:
            slower = summarize_ufast(
                write_matrix(Path(temporary), ufast_seconds=12.0, ufast_tokens=1200)
            )
        rendered = render_ufast_readme(slower)
        self.assertIn("20.00% slower", rendered)
        self.assertIn("20.00% more", rendered)

    def test_rejects_runtime_evidence_and_tool_telemetry(self):
        for mutation in ("runtime evidence", "tool telemetry"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                paths = write_matrix(Path(temporary))
                raw_path = paths[0] / "raw.jsonl"
                records = [json.loads(line) for line in raw_path.read_text().splitlines()]
                treatment = next(item for item in records if item["condition"] == "nerd-ufast")
                if mutation == "runtime evidence":
                    treatment["ufast_evidence"] = {"runtime_present": True}
                else:
                    treatment["events"] = [{"type": "ufast_tool_call"}]
                raw_path.write_text(
                    "".join(json.dumps(item) + "\n" for item in records),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "prompt-only"):
                    summarize_ufast(paths)

    def test_rejects_incomplete_drifted_or_failed_evidence(self):
        mutations = ("missing run", "source drift", "failed score")
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
                    raw_path.write_text(
                        "".join(json.dumps(item) + "\n" for item in records[:-1]),
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
            self.assertIn("4 fresh isolated Codex processes", body)
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
