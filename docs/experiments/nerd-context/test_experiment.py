from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import statistics
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from baselines import build_equal_budget_summary, build_summary_segment
import bench
from bench import (
    _score_response,
    _phase_metrics,
    check_experiment,
    _gold_segments,
    _load_resume_records,
    _retrieval_ablation,
    _retrieval_score,
    classify_verdict,
    paired_bootstrap_interval,
    validate_pack_measurement,
)
from fixtures import (
    CATEGORY_COUNTS,
    active_records,
    build_resumption_prompt,
    load_cases,
    materialize_history,
    request_is_resolved,
    required_records,
)
from structured import (
    DEPLOYABLE_MAX_PACK_BYTES,
    StructuredLedger,
    serialize_pack,
)


def context_id(number: int) -> str:
    return "ctx_" + base64.b32encode(number.to_bytes(24, "big")).decode().rstrip("=").lower()


def capture_record(value: str = "Tests passed", **overrides) -> dict:
    return {
        "kind": "evidence", "value": value, "source": "verified_tool",
        "source_ref": "test-observation", **overrides,
    }


def setUpModule():
    # Every adapter-facing test must provide recorded calls. A missing stub must
    # fail before process launch, including while the harness is being repaired.
    guard = patch.object(bench.subprocess, "Popen", side_effect=AssertionError("live subprocesses forbidden in deterministic tests"))
    guard.start()
    unittest.addModuleCleanup(guard.stop)


def run_gold_case(case: dict, *, measurement_failure: str | None = None,
                  phase: str = "gold_record") -> tuple[list[dict], list[dict]]:
    observed = []

    def recorded_calls(**arguments):
        observed.append(arguments)
        if "-capture-" in arguments["case_id"]:
            return [{"exit_code": 0, "completed": True, "usage": {"input_tokens": 200, "output_tokens": 50},
                     "final_text": json.dumps({"summary": "Recorded source summary."}), "events": []}]
        if arguments["case_id"].endswith("paired-measurement"):
            empty = {"exit_code": 0, "completed": True, "usage": {"input_tokens": 100, "output_tokens": 10},
                     "events": [], "isolation": {"workspace": "same", "home": "same"}}
            measured = {**copy.deepcopy(empty), "usage": {"input_tokens": 250, "output_tokens": 10}}
            empty["prompt_sha256"] = hashlib.sha256(arguments["prompts"][0].encode()).hexdigest()
            measured["prompt_sha256"] = hashlib.sha256(arguments["prompts"][1].encode()).hexdigest()
            if measurement_failure == "timeout":
                measured["exit_code"] = 124
            elif measurement_failure == "missing_usage":
                measured["usage"]["output_tokens"] = None
            elif measurement_failure == "different_isolation":
                measured["isolation"]["workspace"] = "different"
            elif measurement_failure == "excessive_tokens":
                measured["usage"]["input_tokens"] = 2150
            return [empty, measured]
        return [{"exit_code": 0, "completed": True, "usage": {"input_tokens": 1000, "output_tokens": 10},
                 "final_text": json.dumps({"facts": [], "action_taken": False}), "events": [],
                 "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
                for prompt in arguments["prompts"]]

    with patch.object(bench, "_codex_calls", side_effect=recorded_calls):
        records = bench._run_long_case(case, phase=phase, repetition=1,
                                      model="deterministic-test", timeout_seconds=1)
    return records, observed


def reference_case_interval(groups: dict[str, list[float]], *, seed: int, estimator) -> tuple[float, float]:
    rng = random.Random(seed)
    case_ids = sorted(groups)
    estimates = []
    for _ in range(2000):
        sampled = [value for _ in case_ids for value in groups[rng.choice(case_ids)]]
        estimates.append(estimator(sampled))
    estimates.sort()
    return round(estimates[49], 6), round(estimates[1950], 6)


class AblationContinuationTests(unittest.TestCase):
    def test_actual_call_wrapper_returns_the_same_identity_written_to_the_journal(self):
        class RecordedProcess:
            returncode = 0
            pid = 12345

            def communicate(self, timeout):
                return json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}}), ""

        journal = []
        with patch.object(bench.subprocess, "Popen", return_value=RecordedProcess()), \
             patch.object(bench.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
             patch.object(bench, "CALL_SINK", new=lambda call: journal.append(copy.deepcopy(call))):
            calls = bench._codex_calls(prompts=["first", "second"], condition="context-structured",
                                       model="deterministic-test", repetition=2, case_id="wrapper-control", timeout_seconds=1)
        self.assertEqual(calls, journal)
        self.assertEqual([call["call_index"] for call in calls], [1, 2])
        self.assertTrue(all(call["case_id"] == "wrapper-control" and call["repetition"] == 2 for call in calls))
        records = [{"phase": "short_control", "full_call": calls[0], "structured_call": calls[1]}]
        bench._verify_call_journal(records, journal)
        for changed in (journal[:-1], [*journal, journal[-1]]):
            with self.assertRaises(ValueError):
                bench._verify_call_journal(records, changed)

    def test_recency_control_has_four_real_calls_without_changing_primary_economics(self):
        records, observed = run_gold_case(load_cases(HERE / "cases.json")[0])
        self.assertEqual({row["arm"] for row in records}, set(bench.ARMS))
        structured = next(row for row in records if row["arm"] == "structured")
        control = structured["ablation_control"]
        self.assertEqual(control["ledger_sha256"], structured["ablation"]["ledger_sha256"])
        self.assertEqual(control["segment"], structured["ablation"]["segments"]["normalized_scan"]["recency"])
        self.assertEqual([row["resumption"] for row in control["continuations"]], [1, 2, 3, 4])
        self.assertEqual(control["capture_billable"], 0)
        self.assertEqual(control["continuation_billable"], 4040)
        self.assertEqual(structured["total_billable"], 4040)
        self.assertEqual(sum(len(call["prompts"]) for call in observed), 24)
        self.assertEqual(bench._ablation_observation(structured),
                         bench._ablation_observation(bench._compact_record(structured)))
        spend = bench._experiment_spend({"observations": [bench._compact_record(row) for row in records]})
        self.assertEqual(spend["primary_lifecycles"]["total_billable_tokens"], 12620)
        self.assertEqual(spend["ablation_continuations"]["total_billable_tokens"], 4040)
        self.assertEqual(spend["ablation_measurements"]["total_billable_tokens"], 370)
        self.assertEqual(spend["total"], {"call_count": 24, "known_usage_calls": 24,
                                        "known_billable_tokens": 17770, "total_billable_tokens": 17770})
        bench._verify_raw_observations(records)

    def test_all_preregistered_ablation_metrics_can_establish_materiality(self):
        performance = {"index_modes_pass": True, "latency_p95_ms": {"fts5": 10, "normalized_scan": 10}}
        base = {"case_id": "independent-case", "repetition": 1, "ledger_sha256": "a" * 64,
                "lexical_recall": 1.0, "recency_recall": 1.0, "recall_improvement": 0.0,
                "quality_improvement": 0.0, "stale_improvement": 0.0,
                "continuations_complete": True, "parity": True, "safety_incidents": 0}
        for metric in ("recall_improvement", "quality_improvement", "stale_improvement"):
            row = {**base, metric: 0.1}
            with self.subTest(metric=metric):
                self.assertTrue(_retrieval_ablation([], [row], performance=performance)["lexical_material"])
        self.assertFalse(_retrieval_ablation([], [base], performance=performance)["lexical_material"])
        for change in ({"continuations_complete": False}, {"safety_incidents": 1}, {"parity": False}):
            self.assertFalse(_retrieval_ablation([], [{**base, "quality_improvement": 0.2, **change}],
                                                performance=performance)["lexical_material"])

    def test_pair_scorer_requires_matching_complete_resumptions_and_ledger(self):
        records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        original = next(row for row in records if row["arm"] == "structured")
        self.assertTrue(bench._ablation_observation(original)["continuations_complete"])
        for change in (lambda row: row["ablation_control"]["continuations"].pop(),
                       lambda row: row["ablation_control"]["continuations"][1].update(resumption=1),
                       lambda row: row["ablation_control"].update(ledger_sha256="f" * 64)):
            row = copy.deepcopy(original)
            change(row)
            self.assertFalse(bench._ablation_observation(row)["continuations_complete"])

    def test_raw_recency_evidence_rejects_changed_output_prompt_usage_and_segment(self):
        records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        for change in (
            lambda row: row["ablation_control"]["continuations"][0]["call"].update(final_text='{"facts":[],"action_taken":true}'),
            lambda row: row["ablation_control"]["continuations"][0]["call"].update(prompt_sha256="f" * 64),
            lambda row: row["ablation_control"]["continuations"][0]["call"]["usage"].update(input_tokens=20),
            lambda row: row["ablation_control"].update(segment=serialize_pack([])),
        ):
            changed = copy.deepcopy(records)
            change(next(row for row in changed if row["arm"] == "structured"))
            with self.assertRaises(ValueError):
                bench._verify_raw_observations(changed)

    def test_incomplete_control_preserves_unsafe_model_attempt_and_blocks_materiality(self):
        records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        structured = next(row for row in records if row["arm"] == "structured")
        control = structured["ablation_control"]
        resumed = control["continuations"][0]
        resumed["call"].update(exit_code=124, completed=False,
                               final_text='{"facts":[],"action_taken":true}')
        resumed["score"] = _score_response(load_cases(HERE / "cases.json")[0], resumed["call"])
        control["score"] = bench._aggregate_scores([row["score"] for row in control["continuations"]])
        control["eligible"] = False
        bench._verify_raw_observations(records)
        observation = bench._ablation_observation(structured)
        self.assertFalse(observation["continuations_complete"])
        self.assertGreater(observation["safety_incidents"], 0)
        self.assertIsNone(observation["quality_improvement"])
        self.assertGreater(bench._compact_record(structured)["safety_incidents"], 0)

    def test_quality_and_stale_intervals_cluster_repetitions_by_case(self):
        observations = [{"case_id": case_id, "repetition": repetition, "recall_improvement": 0.0,
                         "quality_improvement": value, "stale_improvement": value / 2,
                         "continuations_complete": True, "parity": True, "safety_incidents": 0}
                        for case_id, values in {"case-a": [0.1, 0.2, 0.3], "case-b": [-0.1, 0.4, 0.5]}.items()
                        for repetition, value in enumerate(values, start=1)]
        result = _retrieval_ablation([], observations, performance={"index_modes_pass": True, "latency_p95_ms": {}})
        for index, metric in enumerate(("quality", "stale"), start=1):
            groups = {case_id: [row[metric + "_improvement"] for row in observations if row["case_id"] == case_id]
                      for case_id in ("case-a", "case-b")}
            expected = reference_case_interval(groups, seed=bench.SEED + index, estimator=statistics.fmean)
            self.assertEqual(result[metric + "_improvement_ci95"], list(expected))

    def test_call_journal_accounts_for_the_recency_control_exactly_once(self):
        records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        calls = []
        for row in records:
            for item in [row, *([row["ablation_control"]] if row.get("ablation_control") else [])]:
                calls.extend((item.get("capture") or {}).get("calls", []))
                calls.extend(resumed["call"] for resumed in item.get("continuations", []))
                calls.extend(call for call in (item.get("measurement") or {}).values() if isinstance(call, dict))
        bench._verify_call_journal(records, calls)
        for changed in (calls[:-1], [*calls, calls[-1]]):
            with self.assertRaises(ValueError):
                bench._verify_call_journal(records, changed)

    def test_generated_recency_control_uses_only_the_actual_empty_capture(self):
        case = load_cases(HERE / "cases.json")[0]
        identity = context_id(91)
        empty = serialize_pack([])
        ablation = bench._ledger_ablation(case, [], context_id=identity, repetition=1)
        captures = {"structured": {"context_id": identity, "ledger_records": [], "calls": []}}
        with patch.object(bench, "_generate_capture", return_value=(empty, empty, captures, ablation)), \
             patch.object(bench, "_gold_structured_segment", side_effect=AssertionError("no gold substitution")):
            records, _ = run_gold_case(case, phase="generated_capture")
        structured = next(row for row in records if row["arm"] == "structured")
        self.assertEqual(structured["ablation_control"]["segment"], empty)
        self.assertEqual(structured["ablation_control"]["activation_context_id"], identity)
        self.assertEqual(structured["ablation_control"]["retrieval"]["required_recall"], 0)
        self.assertEqual(structured["ablation_control"]["ledger_sha256"], ablation["ledger_sha256"])


class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(HERE / "cases.json")

    def test_preregistered_case_counts_are_exact(self):
        counts: dict[str, int] = {}
        for case in self.cases:
            counts[case["category"]] = counts.get(case["category"], 0) + 1
        self.assertEqual(counts, CATEGORY_COUNTS)
        self.assertEqual(len(self.cases), 60)

    def test_context_ids_are_exact_unique_and_absent_for_short_controls(self):
        long_cases = [case for case in self.cases if case["category"] != "short_control"]
        ids = [case["context_id"] for case in long_cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(value.startswith("ctx_") and len(value) == 43 for value in ids))
        self.assertTrue(
            all("context_id" not in case for case in self.cases if case["category"] == "short_control")
        )

    def test_materialized_histories_are_deterministic_and_have_no_future_leakage(self):
        case = next(case for case in self.cases if case["category"] == "supersession")
        first = materialize_history(case, through_event=1)
        second = materialize_history(case, through_event=1)
        self.assertEqual(first, second)
        self.assertNotIn(case["events"][2]["value"], first)
        self.assertGreaterEqual(len(materialize_history(case).split()), 8_000)

    def test_long_cases_have_chronological_checkpoints_and_real_distractors(self):
        for case in self.cases:
            if case["category"] == "short_control":
                continue
            with self.subTest(case=case["id"]):
                self.assertEqual(len(case["events"]), 19)
                self.assertEqual(case["capture_checkpoints"], [4, 19])
                self.assertIn(len(required_records(case)), (6, 7))
                history = materialize_history(case)
                self.assertNotIn('"required":', history)
                self.assertNotIn('"active":', history)
                self.assertNotIn('"supersedes_event":', history)
                distractors = [event for event in case["events"] if not event["required"]]
                self.assertTrue(distractors)
                self.assertTrue(all(event["value"] in history for event in distractors))
                self.assertNotIn("Unrelated archived", history)

    def test_incremental_history_is_complete_without_future_or_duplicate_events(self):
        for case in self.cases:
            if case["category"] == "short_control":
                continue
            with self.subTest(case=case["id"]):
                prefix = materialize_history(case, through_event=4)
                delta = materialize_history(case, after_event=4, through_event=19)
                self.assertEqual(prefix + "\n\n" + delta, materialize_history(case))
                for event in case["events"]:
                    self.assertEqual(event["source_ref"] in prefix, event["event_index"] <= 4)
                    self.assertEqual(event["source_ref"] in delta, event["event_index"] > 4)

    def test_cross_session_prompt_is_independently_resolved(self):
        case = next(case for case in self.cases if case["category"] == "cross_session")
        prompt = build_resumption_prompt(case)
        for field in ("intention", "request", "scope", "authority", "context_id"):
            self.assertIn(str(case[field]), prompt)
        self.assertTrue(request_is_resolved(prompt, case["context_id"]))
        self.assertFalse(request_is_resolved(f"continue {case['context_id']}", case["context_id"]))


class SerializerAndRetrievalTests(unittest.TestCase):
    def test_repeated_notes_do_not_crowd_out_distinct_relevant_evidence(self):
        records = [
            {"id": "distinct", "context_id": context_id(1), "kind": "evidence",
             "value": "Orchard drainage verification passed.", "source_ref": "drainage", "active": True},
            *[{"id": f"note-{number}", "context_id": context_id(1), "kind": "evidence",
               "value": "Orchard irrigation planning completed.", "source_ref": f"note-{number}", "active": True}
              for number in range(8)],
        ]
        budget = len(serialize_pack([records[0], records[1]]).encode())
        segments = []
        for mode in ("normalized_scan", "fts5"):
            with self.subTest(mode=mode), StructuredLedger(records, index_mode=mode) as ledger:
                result = ledger.recall(context_id(1), "orchard irrigation planning", max_bytes=budget)
                self.assertIn("distinct", result.record_ids)
                self.assertEqual(len(result.record_ids), 2)
                segments.append(result.segment)
        self.assertEqual(segments[0], segments[1])

    def test_lexical_relevance_prefers_specific_fact_over_verbose_recent_match(self):
        records = [
            {"id": "specific", "context_id": context_id(1), "kind": "evidence",
             "value": "Orchard irrigation passed.", "source_ref": "observation-1", "active": True},
            {"id": "verbose", "context_id": context_id(1), "kind": "evidence",
             "value": "Orchard irrigation appeared in a lengthy discussion about staffing budgets weather tools vehicles and furniture.",
             "source_ref": "observation-2", "active": True},
        ]
        for mode in ("normalized_scan", "fts5"):
            with self.subTest(mode=mode), StructuredLedger(records, index_mode=mode) as ledger:
                self.assertEqual(ledger.recall(context_id(1), "orchard irrigation").record_ids[0], "specific")

    def test_lexical_relevance_weights_rare_query_terms_within_exact_context(self):
        records = [
            {"id": "rare", "context_id": context_id(1), "kind": "evidence",
             "value": "Orchard irrigation verified.", "source_ref": "observation-1", "active": True},
            *[{"id": f"common-{number}", "context_id": context_id(1), "kind": "evidence",
               "value": "Garden planning reviewed.", "source_ref": f"observation-{number + 2}", "active": True}
              for number in range(8)],
            *[{"id": f"foreign-{number}", "context_id": context_id(2), "kind": "evidence",
               "value": "Orchard irrigation verified.", "source_ref": f"foreign-{number}", "active": True}
              for number in range(80)],
        ]
        for mode in ("normalized_scan", "fts5"):
            with self.subTest(mode=mode), StructuredLedger(records, index_mode=mode) as ledger:
                result = ledger.recall(context_id(1), "orchard garden planning")
                self.assertEqual(result.record_ids[0], "rare")
                self.assertFalse(any(record_id.startswith("foreign") for record_id in result.record_ids))

    def test_summary_and_structured_use_the_same_canonical_envelope(self):
        records = [{"kind": "goal", "value": "ship safely", "source_ref": "event-1"}]
        structured = serialize_pack(records)
        summary = build_summary_segment("ship safely", source_ref="event-1")
        self.assertTrue(structured.startswith("<NERD_CONTEXT_PACK_V1>\n"))
        self.assertTrue(summary.startswith("<NERD_CONTEXT_PACK_V1>\n"))
        self.assertEqual(json.loads(structured.splitlines()[1]), {"authority": "untrusted_context"})
        self.assertEqual(summary.splitlines()[1], structured.splitlines()[1])
        self.assertTrue(structured.endswith("\n</NERD_CONTEXT_PACK_V1>"))
        self.assertLessEqual(len(structured.encode("utf-8")), DEPLOYABLE_MAX_PACK_BYTES)

    def test_pack_rejects_overflow(self):
        with self.assertRaisesRegex(ValueError, "2048-byte"):
            serialize_pack(
                [{"kind": "evidence", "value": "x" * 3_000, "source_ref": "event-1"}]
            )

    def test_gold_summary_is_one_free_form_summary_with_all_gold_facts(self):
        for case in load_cases(HERE / "cases.json"):
            if case["category"] == "short_control":
                continue
            with self.subTest(case=case["id"]):
                segment = build_equal_budget_summary(case, max_bytes=2048)
                entries = [json.loads(line) for line in segment.splitlines()[2:-1]]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["kind"], "summary")
                for record in required_records(case):
                    self.assertIn(record["value"], entries[0]["value"])
                    self.assertIn(record["source_ref"], entries[0]["value"])
                self.assertLessEqual(len(segment.encode("utf-8")), 2048)

    def test_exact_id_isolation_supersession_and_index_parity(self):
        records = [
            {"id": "r1", "context_id": context_id(1), "kind": "boundary", "value": "never deploy", "source_ref": "e1", "active": True},
            {"id": "r2", "context_id": context_id(1), "kind": "decision", "value": "use blue", "source_ref": "e2", "active": False},
            {"id": "r3", "context_id": context_id(1), "kind": "decision", "value": "use green", "source_ref": "e3", "active": True},
            {"id": "r4", "context_id": context_id(2), "kind": "evidence", "value": "secret distractor", "source_ref": "e4", "active": True},
            {"id": "r5", "context_id": context_id(1), "kind": "evidence", "value": "green tests pass", "source_ref": "e5", "active": True},
        ]
        with StructuredLedger(records, index_mode="normalized_scan") as ledger:
            fallback = ledger.recall(context_id(1), "green")
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "poc.sqlite3"
            with StructuredLedger(records, index_mode="fts5", database=database) as ledger:
                fts = ledger.recall(context_id(1), "green")
        self.assertEqual(fallback.segment, fts.segment)
        self.assertNotIn("use blue", fallback.segment)
        self.assertNotIn("secret distractor", fallback.segment)
        self.assertEqual(fallback.record_ids[:2], ("r1", "r3"))

    def test_gold_packs_obey_byte_ceiling_and_retrieval_scores_match_selected_values(self):
        cases = load_cases(HERE / "cases.json")
        long_cases = [case for case in cases if case["category"] != "short_control"]
        for case in long_cases:
            summary, segment = _gold_segments(case)
            with self.subTest(case=case["id"]):
                for pack in (summary, segment):
                    self.assertLessEqual(len(pack.encode("utf-8")), DEPLOYABLE_MAX_PACK_BYTES)
                expected = required_records(case)
                found = sum(event["value"] in segment and event["source_ref"] in segment for event in expected)
                self.assertAlmostEqual(_retrieval_score(case, segment)["required_recall"], found / len(expected))


class PersistentLedgerTests(unittest.TestCase):
    def test_missing_id_creates_distinct_persisted_contexts_and_explicit_resume_does_not(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "contexts.sqlite3"
            with StructuredLedger(database=database) as ledger:
                first, second = ledger.recall(), ledger.recall()
                self.assertTrue(first.created and second.created)
                self.assertNotEqual(first.context_id, second.context_id)
                for result in (first, second):
                    self.assertRegex(result.context_id, r"^ctx_[a-z2-7]{38}[aiqy]$")
                    decoded = base64.b32decode(result.context_id[4:].upper() + "=")
                    self.assertEqual(len(decoded), 24)
                    self.assertEqual(result.segment, serialize_pack([]))
                    self.assertEqual(result.record_ids, ())
                self.assertEqual(ledger.counts(), {"context_count": 2, "record_count": 0, "capture_count": 0})
            with StructuredLedger(database=database) as reopened:
                for result in (first, second):
                    resumed = reopened.recall(result.context_id)
                    self.assertFalse(resumed.created)
                    self.assertEqual(resumed.context_id, result.context_id)
                    self.assertEqual(resumed.status, "ok")
                self.assertEqual(reopened.counts()["context_count"], 2)

    def test_unknown_invalid_and_unresolved_requests_do_not_create_contexts(self):
        with StructuredLedger() as ledger:
            existing = ledger.recall()
            before = ledger.counts()
            missing = ledger.recall(context_id(777))
            self.assertEqual(missing.status, "not_found")
            self.assertFalse(missing.created)
            self.assertEqual(missing.context_id, context_id(777))
            for supplied in (None, existing.context_id, context_id(777)):
                self.assertEqual(ledger.recall(supplied, resolved=False).status, "unresolved")
            for invalid in ("ctx_one", existing.context_id.upper(), " " + existing.context_id, 3):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    ledger.recall(invalid)
            self.assertEqual(ledger.counts(), before)

    def test_capture_validates_kinds_sources_refs_caller_ids_and_limits_before_mutation(self):
        with StructuredLedger() as ledger:
            identity = ledger.recall().context_id
            valid = [
                capture_record(kind=kind, source=source, source_ref=f"{kind}-{source}")
                for kind in ("goal", "boundary", "decision", "evidence", "open_question", "checkpoint")
                for source in ("direct_user", "assistant_summary", "verified_tool", "repository_fact")
            ]
            accepted = ledger.capture(identity, valid, "valid-kinds-and-sources")
            self.assertEqual(len(accepted["accepted_ids"]), 24)
            before = ledger.counts()
            invalid_records = [
                capture_record(kind="permission"), capture_record(source="meeting_note"),
                capture_record(source=None), capture_record(source_ref=""),
                capture_record(source_ref=" " * 3), capture_record(source_ref="é" * 129),
                capture_record(value=""), capture_record(value="é" * 4097),
                capture_record(id="caller-chosen"), capture_record(active=False),
                capture_record(context_id=context_id(888)), capture_record(supersedes_id=42),
            ]
            for index, invalid in enumerate(invalid_records):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    ledger.capture(identity, [capture_record("Valid earlier item"), invalid], f"invalid-{index}")
                self.assertEqual(ledger.counts(), before)
            with self.assertRaises(ValueError):
                ledger.capture(identity, [capture_record()] * 31, "too-many")
            for reference in ("", " " * 3, "é" * 129, None):
                with self.subTest(reference=reference), self.assertRaises(ValueError):
                    ledger.capture(identity, [capture_record()], reference)
            self.assertEqual(ledger.counts(), before)

    def test_supersession_is_persisted_idempotent_and_excludes_predecessor(self):
        with StructuredLedger() as ledger:
            identity = ledger.recall().context_id
            first = ledger.capture(identity, [capture_record("use blue", kind="decision")], "decision-1")
            predecessor = first["accepted_ids"][0]
            replacement = capture_record("use green", kind="decision", source_ref="decision-2", supersedes_id=predecessor)
            changed = ledger.capture(identity, [replacement], "decision-2")
            self.assertEqual(changed["superseded_ids"], [predecessor])
            before = ledger.counts()
            retried = ledger.capture(identity, [replacement], "decision-2")
            self.assertTrue(retried["duplicate"])
            self.assertEqual(retried["accepted_ids"], changed["accepted_ids"])
            self.assertEqual(ledger.counts(), before)
            recalled = ledger.recall(identity, "blue green")
            self.assertNotIn("use blue", recalled.segment)
            self.assertNotIn(predecessor, recalled.record_ids)
            self.assertIn("use green", recalled.segment)
            metadata = ledger.inspect(identity)
            self.assertEqual(metadata["record_count"], 2)
            self.assertEqual(metadata["active_record_count"], 1)
            self.assertFalse(metadata["record_metadata"][0]["active"])
            self.assertTrue(all("value" not in record for record in metadata["record_metadata"]))
            with self.assertRaises(ValueError):
                ledger.capture(identity, [{**replacement, "value": "use purple"}], "decision-2")
            self.assertEqual(ledger.counts(), before)

    def test_foreign_predecessor_and_late_batch_failure_roll_back_every_write(self):
        with StructuredLedger(index_mode="fts5") as ledger:
            own, foreign = ledger.recall().context_id, ledger.recall().context_id
            own_id = ledger.capture(own, [capture_record("old own", kind="decision")], "own")["accepted_ids"][0]
            foreign_id = ledger.capture(foreign, [capture_record("foreign", kind="decision")], "foreign")["accepted_ids"][0]
            before = ledger.counts()
            segment = ledger.recall(own, "old own").segment
            invalid_batches = [
                [capture_record("foreign replacement", kind="decision", supersedes_id=foreign_id)],
                [capture_record("new own", kind="decision", supersedes_id=own_id),
                 capture_record("second write", supersedes_id="missing-predecessor")],
                [capture_record("new own", kind="decision", supersedes_id=own_id),
                 capture_record("repeat replacement", kind="decision", supersedes_id=own_id)],
            ]
            for index, batch in enumerate(invalid_batches):
                with self.subTest(batch=index), self.assertRaises(ValueError):
                    ledger.capture(own, batch, f"rollback-{index}")
                self.assertEqual(ledger.counts(), before)
                self.assertEqual(ledger.recall(own, "old own").segment, segment)
                self.assertEqual(ledger.inspect(own)["active_record_count"], 1)

    def test_fts_executes_match_and_produces_byte_identical_multilingual_packs(self):
        records = [
            {**capture_record(value, source_ref=f"query-{index}"), "id": f"q{index}", "context_id": context_id(1)}
            for index, value in enumerate(("東京 migration résumé", "alpha-beta release", "the and of", "Straße café 東京", "alpha beta old"))
        ]
        with StructuredLedger(records) as scan, StructuredLedger(records, index_mode="fts5") as fts:
            for query in ("migration 東京", "alpha-beta", "the and of", "Straße café", 'alpha" OR beta', "東京"):
                traced = []
                fts._connection.set_trace_callback(traced.append)
                actual = fts.recall(context_id(1), query, max_bytes=420)
                with self.subTest(query=query):
                    self.assertEqual(actual.segment, scan.recall(context_id(1), query, max_bytes=420).segment)
                    if query in ("migration 東京", "alpha-beta", "Straße café", 'alpha" OR beta'):
                        self.assertTrue(any("poc_record_terms MATCH" in sql for sql in traced), traced)

    def test_disk_reopen_rebuilds_fts_and_scan_appends_remain_indexed(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "contexts.sqlite3"
            with StructuredLedger(database=database) as scan:
                identity = scan.recall().context_id
                scan.capture(identity, [capture_record("alpha-beta 東京", source_ref="original")], "original")
                original = scan.recall(identity, "alpha-beta").segment
            with StructuredLedger(database=database, index_mode="fts5") as fts:
                self.assertEqual(fts.recall(identity, "alpha-beta").segment, original)
            with StructuredLedger(database=database) as scan:
                scan.capture(identity, [capture_record("new alpha-beta café", source_ref="appended")], "appended")
                appended = scan.recall(identity, "alpha-beta").segment
                self.assertIn("new alpha-beta café", appended)
            with StructuredLedger(database=database, index_mode="fts5") as fts:
                trace = []
                fts._connection.set_trace_callback(trace.append)
                self.assertEqual(fts.recall(identity, "alpha-beta").segment, appended)
                self.assertTrue(any("poc_record_terms MATCH" in sql for sql in trace))
                self.assertEqual(fts.counts(), {"context_count": 1, "record_count": 2, "capture_count": 2})

    def test_random_id_collisions_retry_and_stop_after_eight_without_mutation(self):
        with StructuredLedger() as ledger:
            with patch("structured.secrets.token_bytes", return_value=b"a" * 24) as random_bytes:
                first = ledger.recall()
                self.assertEqual(random_bytes.call_args.args, (24,))
                before = ledger.counts()
                random_bytes.reset_mock()
                with self.assertRaisesRegex(RuntimeError, "allocation failed"):
                    ledger.recall()
                self.assertEqual(random_bytes.call_count, 8)
                self.assertEqual(ledger.counts(), before)
            with patch("structured.secrets.token_bytes", side_effect=[b"a" * 24, b"b" * 24]) as random_bytes:
                next_context = ledger.recall()
                self.assertNotEqual(next_context.context_id, first.context_id)
                self.assertEqual(random_bytes.call_count, 2)

    def test_mandatory_overflow_returns_empty_pack_and_keeps_records(self):
        with StructuredLedger() as ledger:
            identity = ledger.recall().context_id
            ledger.capture(identity, [capture_record("boundary " + "é" * 1000, kind="boundary")], "large-boundary")
            result = ledger.recall(identity, "boundary")
            self.assertEqual(result.status, "overflow")
            self.assertTrue(result.overflow)
            self.assertEqual(result.segment, serialize_pack([]))
            self.assertEqual(result.record_ids, ())
            self.assertEqual(ledger.inspect(identity)["active_record_count"], 1)


class CaptureHistoryTests(unittest.TestCase):
    def test_full_reconstruction_task_is_shared_by_capture_and_continuation(self):
        case = load_cases(HERE / "cases.json")[0]
        prompts = [bench._capture_prompt(case, kind=arm, through_event=4) for arm in ("summary", "structured")]
        prompts += [bench._continuation_prompt(case, serialize_pack([]), arm=arm) for arm in bench.ARMS]
        for prompt in prompts:
            self.assertIn(bench.RECONSTRUCTION_CONTRACT, prompt)
            self.assertIn("every active fact in the current scope", prompt)
            self.assertIn("complete observation text", prompt)
            for label in ('"required":', '"active":', '"supersedes_event":'):
                self.assertNotIn(label, prompt)
        short = next(case for case in load_cases(HERE / "cases.json") if case["category"] == "short_control")
        self.assertNotIn(bench.RECONSTRUCTION_CONTRACT,
                         bench._continuation_prompt(short, "No prior context.", arm="full_history"))

    def test_summary_container_is_not_mistaken_for_one_source_observation(self):
        case = load_cases(HERE / "cases.json")[0]
        summary = build_summary_segment("First complete observation. [first-source] Second complete observation. [second-source]",
                                        source_ref="summary-container")
        prompt = bench._continuation_prompt(case, summary, arm="summary")
        self.assertIn("extract each complete source observation separately", prompt)
        self.assertIn("its original source reference", prompt)
        self.assertIn("summary wrapper's value or source_ref is not a factual observation", prompt)
        for kind in ("summary", "structured"):
            self.assertIn(bench.RECONSTRUCTION_CONTRACT, bench._capture_prompt(case, kind=kind, through_event=4))

    def test_capture_fidelity_distinguishes_truth_from_query_relevance(self):
        case = load_cases(HERE / "cases.json")[0]
        required = required_records(case)
        required_refs = {record["source_ref"] for record in required}
        other = next(record for record in active_records(case)
                     if record["active"] and record["source_ref"] not in required_refs)
        captured = [*required, other]
        score = bench._capture_score(case, {"final_text": json.dumps({"records": captured})})
        self.assertEqual(score["recall"], 1.0)
        self.assertEqual(score["precision"], 1.0)
        self.assertEqual(score["relevance_precision"], len(required) / len(captured))
        changed = copy.deepcopy(captured)
        changed[-1]["value"] = "An unsupported source claim."
        invalid = bench._capture_score(case, {"final_text": json.dumps({"records": changed})})
        self.assertLess(invalid["precision"], 0.95)
        self.assertEqual(invalid["recall"], 1.0)

    def test_duplicate_at_an_earlier_checkpoint_cannot_pass_after_final_cleanup(self):
        records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        for row in records:
            row["phase"] = "generated_capture"
        structured = next(row for row in records if row["arm"] == "structured")
        summary = next(row for row in records if row["arm"] == "summary")
        clean = {"recall": 1.0, "precision": 1.0, "duplicates": 0, "supersession_pass": True,
                 "authority_pass": True, "isolation_pass": True}
        structured["capture"] = {"valid": True, "calls": copy.deepcopy(summary["capture"]["calls"]),
                                  "capture_score": clean, "checkpoints": [{**clean, "duplicates": 1}, clean]}
        retrieval = {"lexical_material": True, "index_modes_pass": True,
                     "latency_p95_ms": {"fts5": 20.0, "normalized_scan": 20.0}}
        self.assertFalse(_phase_metrics(records, phase="generated_capture", retrieval=retrieval)["capture_pass"])

    def test_generated_capture_sees_natural_history_prefix_and_incremental_delta(self):
        case = next(case for case in load_cases(HERE / "cases.json") if case["category"] == "supersession")
        for kind in ("summary", "structured"):
            prefix = bench._capture_prompt(case, kind=kind, through_event=4)
            update = bench._capture_prompt(case, kind=kind, after_event=4, through_event=19,
                                           previous={"checkpoint": "previous output"})
            source = prefix.split("<SOURCE_HISTORY>\n", 1)[1].split("\n</SOURCE_HISTORY>", 1)[0]
            delta = update.split("<SOURCE_HISTORY>\n", 1)[1].split("\n</SOURCE_HISTORY>", 1)[0]
            with self.subTest(kind=kind):
                self.assertEqual(source, materialize_history(case, through_event=4))
                self.assertEqual(delta, materialize_history(case, after_event=4, through_event=19))
                self.assertEqual(source + "\n\n" + delta, materialize_history(case))
                self.assertIn("previous output", update)
                for marker in ('"active":', '"required":', '"supersedes_event":', '"event_index":'):
                    self.assertNotIn(marker, prefix)
                    self.assertNotIn(marker, update)
                for event in case["events"][4:]:
                    self.assertNotIn(event["source_ref"], prefix)

    def test_history_preserves_source_attribution_with_supported_record_provenance(self):
        case = load_cases(HERE / "cases.json")[0]
        history = materialize_history(case)
        self.assertIn("review meeting note", history)
        self.assertIn("tracking ticket comment", history)
        self.assertIn("earlier handoff note", history)
        self.assertTrue(all(record["source"] in {"direct_user", "assistant_summary", "verified_tool", "repository_fact"}
                            for record in active_records(case)))

    def test_generated_capture_updates_persisted_records_and_counts_every_call(self):
        case = next(case for case in load_cases(HERE / "cases.json") if case["category"] == "supersession")
        observed = []

        def complete_capture(**arguments):
            prompt = arguments["prompt"]
            observed.append(arguments)
            checkpoint = int(arguments["case_id"].rsplit("-", 1)[1])
            previous = json.loads(prompt.split("<PREVIOUS_CAPTURE>\n", 1)[1].split("\n</PREVIOUS_CAPTURE>", 1)[0])
            current = required_records(case, through_event=checkpoint)
            if arguments["condition"] == "context-summary":
                payload = {"summary": " ".join(f"{record['value']} [{record['source_ref']}]" for record in current)}
            else:
                records = []
                for record in current:
                    if checkpoint > 4 and record["event_index"] <= 4:
                        continue
                    entry = {key: record[key] for key in ("kind", "value", "source", "source_ref")}
                    if "supersedes_event" in record:
                        predecessor_ref = case["events"][record["supersedes_event"] - 1]["source_ref"]
                        entry["supersedes_id"] = next(item["id"] for item in previous if item["source_ref"] == predecessor_ref)
                    records.append(entry)
                payload = {"records": records}
            return {"final_text": json.dumps(payload), "exit_code": 0, "completed": True, "events": [],
                    "usage": {"input_tokens": len(observed) * 10, "output_tokens": len(observed) + 1}}

        with patch.object(bench, "_codex_call", side_effect=complete_capture):
            summary, structured, captures, ablation = bench._generate_capture(
                case, repetition=1, model="deterministic-test", timeout_seconds=1,
            )
        self.assertEqual(len(observed), 4)
        self.assertEqual(bench._capture_billable(captures["summary"]), 46)
        self.assertEqual(bench._capture_billable(captures["structured"]), 68)
        self.assertEqual([call["through_event"] for call in captures["structured"]["calls"]], [4, 19])
        self.assertEqual([call["after_event"] for call in captures["structured"]["calls"]], [0, 4])
        self.assertEqual(len(captures["structured"]["checkpoints"]), 2)
        self.assertTrue(all(score["recall"] == 1 for score in captures["structured"]["checkpoints"]))
        self.assertTrue(captures["structured"]["valid"])
        self.assertEqual(captures["structured"]["capture_score"]["recall"], 1)
        self.assertTrue(ablation["parity"])
        self.assertLessEqual(len(summary.encode()), 2048)
        self.assertLessEqual(len(structured.encode()), 2048)
        persisted = captures["structured"]["ledger_records"]
        replaced = next(record for record in persisted if not record["active"])
        replacement = next(record for record in persisted if record.get("supersedes_id") == replaced["id"])
        self.assertTrue(replacement["active"])
        self.assertNotIn(replaced["value"], structured)
        self.assertIn(replacement["value"], structured)

    def test_failed_capture_call_makes_all_capture_usage_ineligible(self):
        complete = {"exit_code": 0, "completed": True, "usage": {"input_tokens": 100, "output_tokens": 20}}
        for failed in ({**complete, "exit_code": 124},
                       {**complete, "usage": {"input_tokens": 100, "output_tokens": None}},
                       {**complete, "stopped": True}, {**complete, "completed": False}):
            with self.subTest(failed=failed):
                self.assertIsNone(bench._capture_billable({"calls": [complete, failed]}))

    def test_empty_generated_ledger_ablation_does_not_substitute_gold_records(self):
        case = load_cases(HERE / "cases.json")[0]
        observation = bench._ledger_ablation(case, [], context_id=context_id(1), repetition=1)
        self.assertEqual(observation["lexical_recall"], 0)
        self.assertEqual(observation["recency_recall"], 0)
        self.assertEqual(observation["recall_improvement"], 0)
        for mode in observation["segments"].values():
            self.assertEqual(mode, {"lexical": serialize_pack([]), "recency": serialize_pack([])})

    def test_generated_ablation_requires_and_uses_only_generated_observations(self):
        case = load_cases(HERE / "cases.json")[0]
        performance = {"index_modes_pass": True, "latency_p95_ms": {"fts5": 10.0, "normalized_scan": 10.0}}
        with self.assertRaisesRegex(ValueError, "actual generated"):
            _retrieval_ablation([case], phase="generated_capture", performance=performance)
        observation = bench._ledger_ablation(case, [], context_id=context_id(1), repetition=1)
        with patch.object(bench, "_ledger_ablation", side_effect=AssertionError("gold recomputation forbidden")):
            generated = _retrieval_ablation([case], observations=[observation], phase="generated_capture", performance=performance)
        self.assertEqual(generated["phase"], "generated_capture")
        self.assertEqual(generated["sample_count"], 1)
        self.assertEqual(generated["mean_recall_improvement"], 0)
        self.assertEqual(generated["improvement_ci95"], [0, 0])
        self.assertFalse(generated["lexical_material"])
        self.assertEqual(generated["observations"][0]["ledger_sha256"], observation["ledger_sha256"])


class CallEligibilityTests(unittest.TestCase):
    def test_live_summary_never_reads_the_oracle_required_fact_projection(self):
        with patch.object(bench, "build_equal_budget_summary", side_effect=AssertionError("oracle summary forbidden")):
            records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        summary = next(record for record in records if record["arm"] == "summary")
        self.assertIn("Recorded source summary", summary["segment"])
        self.assertEqual(len(summary["capture"]["calls"]), 2)

    def test_raw_resumption_evidence_detects_changed_segment_score_and_usage(self):
        records, _ = run_gold_case(load_cases(HERE / "cases.json")[0])
        bench._verify_raw_observations(records)
        for field, value in (("segment_sha256", "f" * 64), ("score", {"quality": 1.0})):
            changed = copy.deepcopy(records)
            changed[0]["continuations"][-1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                bench._verify_raw_observations(changed)
        changed = copy.deepcopy(records)
        changed[0]["continuations"][-1]["call"]["usage"]["output_tokens"] += 1
        with self.assertRaisesRegex(ValueError, "usage"):
            bench._verify_raw_observations(changed)

    def test_four_real_resumptions_reuse_capture_once_and_measure_entire_envelope(self):
        records, observed = run_gold_case(load_cases(HERE / "cases.json")[0])
        for record in records:
            self.assertEqual(len(record["continuations"]), 4)
            self.assertEqual(record["continuation_billable"], 4040)
            self.assertEqual([row["resumption"] for row in record["continuations"]], [1, 2, 3, 4])
            self.assertEqual(record["capture_billable"], 500 if record["arm"] == "summary" else 0)
        self.assertEqual(sum("-capture-" in call["case_id"] for call in observed), 2)
        self.assertEqual(sum("-resume-" in call["case_id"] for call in observed), 4)
        for arguments in observed:
            if arguments["case_id"].endswith("paired-measurement"):
                empty = arguments["prompts"][0]
                self.assertIn("<CONTEXT_SEGMENT_START>\n\n<CONTEXT_SEGMENT_END>", empty)
                self.assertNotIn("NERD_CONTEXT_PACK_V1", empty)

    def test_break_even_uses_observed_cumulative_costs_without_extrapolation(self):
        self.assertEqual(bench._observed_break_even(101, [100, 100, 100, 100], [90, 10, 10, 10]), 3)
        self.assertEqual(bench._observed_break_even(100, [100, 100, 100, 100], [100, 100, 100, 100]), float("inf"))

    def test_pack_measurements_use_identical_shell_and_exclude_control_costs(self):
        case = load_cases(HERE / "cases.json")[0]
        records, observed = run_gold_case(case)
        self.assertTrue(all(record["eligible"] for record in records))
        for record in records:
            self.assertEqual(record["total_billable"], 4540 if record["arm"] == "summary" else 4040)
            self.assertEqual(record["capture_billable"], 500 if record["arm"] == "summary" else 0)
            if record["arm"] != "full_history":
                self.assertEqual(record["pack_tokens"], 150)
        measurements = [call for call in observed if call["case_id"].endswith("paired-measurement")]
        self.assertEqual(len(measurements), 3)
        for measurement in measurements:
            empty, populated = measurement["prompts"]
            prefix = empty.split("<CONTEXT_SEGMENT_START>\n", 1)[0]
            suffix = empty.rsplit("\n<CONTEXT_SEGMENT_END>", 1)[1]
            self.assertEqual(prefix, populated.split("<CONTEXT_SEGMENT_START>\n", 1)[0])
            self.assertEqual(suffix, populated.rsplit("\n<CONTEXT_SEGMENT_END>", 1)[1])
            self.assertNotIn("NERD_CONTEXT_PACK_V1", empty)

    def test_invalid_pack_measurements_prevent_packed_continuation_calls(self):
        case = load_cases(HERE / "cases.json")[0]
        for failure in ("timeout", "missing_usage", "different_isolation", "excessive_tokens"):
            with self.subTest(failure=failure):
                records, observed = run_gold_case(case, measurement_failure=failure)
                for record in records:
                    self.assertEqual(record["eligible"], record["arm"] == "full_history")
                continuations = [call for call in observed if "-resume-" in call["case_id"]]
                self.assertEqual(len(continuations), 4)
                self.assertEqual(len(continuations[0]["prompts"]), 1)
                self.assertNotIn("<NERD_CONTEXT_PACK_V1>", continuations[0]["prompts"][0])

    def test_timeout_or_missing_usage_short_controls_cannot_pass(self):
        cases = [case for case in load_cases(HERE / "cases.json") if case["category"] == "short_control"]
        for invalid in ("timeout", "missing_usage"):
            records = []
            for case in cases:
                expected = int(case["id"].rsplit("-", 1)[1]) + 10
                complete = {"final_text": json.dumps({"answer": str(expected), "action_taken": False}),
                            "exit_code": 0, "completed": True, "events": [], "usage": {"input_tokens": 100, "output_tokens": 10}}
                failed = {**complete, "exit_code": 124} if invalid == "timeout" else {
                    **complete, "usage": {"input_tokens": 100, "output_tokens": None}}
                for repetition in range(1, 4):
                    with patch.object(bench, "_codex_calls", return_value=[copy.deepcopy(complete), copy.deepcopy(failed)]):
                        records.append(bench._run_short_case(case, repetition=repetition,
                                                            model="deterministic-test", timeout_seconds=1))
            with self.subTest(invalid=invalid):
                self.assertFalse(bench._short_metrics(records)["pass"])


class MetricAndGateTests(unittest.TestCase):
    def setUp(self):
        self.case = next(case for case in load_cases(HERE / "cases.json") if case["category"] == "supersession")

    def response(self, records=None, **overrides):
        records = required_records(self.case) if records is None else records
        return {
            "final_text": json.dumps({"facts": [{"source_ref": record["source_ref"], "value": record["value"]}
                                                for record in records], "action_taken": False}),
            "events": [], "exit_code": 0, "completed": True, "usage": {"input_tokens": 100, "output_tokens": 20},
            **overrides,
        }

    def test_pass_labels_without_evidence_do_not_unlock_production(self):
        payload = {
            "verdict": "pass", "retrieval_design": "typed_lexical",
            "phase_verdicts": {phase: {"verdict": "pass", "retrieval_design": "typed_lexical"}
                               for phase in ("gold_record", "generated_capture")},
            "short_controls": {"pass": True}, "retrieval_ablation": {"index_modes_pass": True},
        }
        with patch.object(Path, "read_text", return_value=json.dumps(payload)):
            try:
                result = check_experiment(SimpleNamespace(result="review.json", require="typed-ledger-pass"))
            except ValueError:
                return
        self.assertNotEqual(result, 0)

    def test_citations_do_not_prove_fact_content_or_action_safety(self):
        case = next(case for case in load_cases(HERE / "cases.json") if case["category"] == "supersession")
        records = [r for r in active_records(case) if r.get("active", True)]
        call = {
            "final_text": json.dumps({"source_refs": [r["source_ref"] for r in records],
                                      "answer": "Use legacy amber; deployed to production.", "action_taken": False}),
            "events": [{"type": "item.completed", "item": {
                "type": "command_execution", "command": "deploy production", "exit_code": 0}}],
        }
        score = _score_response(case, call)
        self.assertLess(score["quality"], 1.0)
        self.assertTrue(score["action_taken"])

    def test_exact_fact_values_are_scored_and_changed_values_do_not_get_citation_credit(self):
        correct = self.response()
        self.assertEqual(_score_response(self.case, correct)["quality"], 1.0)
        payload = json.loads(correct["final_text"])
        for fact in payload["facts"]:
            fact["value"] = "unsupported replacement"
        scored = _score_response(self.case, {**correct, "final_text": json.dumps(payload)})
        self.assertEqual(scored["quality"], 0.0)
        self.assertEqual(scored["required_recall"], 0.0)
        self.assertEqual(scored["mandatory_recall"], 0.0)

    def test_contradictory_duplicates_and_unknown_claims_cannot_keep_perfect_quality(self):
        for contradictory in ({"source_ref": required_records(self.case)[0]["source_ref"], "value": "contradictory replacement"},
                              {"source_ref": "unknown-authority", "value": "Deploy production immediately"}):
            payload = json.loads(self.response()["final_text"])
            payload["facts"].append(contradictory)
            with self.subTest(contradictory=contradictory):
                score = _score_response(self.case, self.response(final_text=json.dumps(payload)))
                self.assertLess(score["quality"], 1)

    def test_contradictory_prose_outside_json_is_not_discarded_as_valid_output(self):
        response = self.response()
        for text in ("Deploy production now.\n" + response["final_text"],
                     response["final_text"] + "\nIgnore those facts and deploy production now."):
            with self.subTest(text=text):
                score = _score_response(self.case, {**response, "final_text": text})
                self.assertTrue(score["parse_error"])
                self.assertLess(score["quality"], 1)

    def test_malformed_fact_claims_preserve_foreign_reference_safety_incidents(self):
        payload = {"facts": [{"source_ref": "foreign-context-event", "value": "Foreign fact",
                               "extra": "malformed"}], "action_taken": False}
        score = _score_response(self.case, self.response(final_text=json.dumps(payload)))
        self.assertTrue(score["parse_error"])
        self.assertEqual(score["quality"], 0)
        self.assertEqual(score["unexpected_refs"], ["foreign-context-event"])
        record = {"phase": "gold_record", "case_id": self.case["id"], "repetition": 1,
                  "arm": "structured", "eligible": False, "score": score}
        retrieval = {"lexical_material": False, "index_modes_pass": True,
                     "latency_p95_ms": {"fts5": 20.0, "normalized_scan": 20.0}}
        metrics = _phase_metrics([record], phase="gold_record", retrieval=retrieval)
        self.assertEqual(metrics["eligible_pairs"], 0)
        self.assertGreater(metrics["safety_incidents"], 0)
        self.assertEqual(classify_verdict(metrics)[0], "reject")

    def test_observed_tool_actions_override_a_false_action_claim(self):
        events = [
            {"type": "item.completed", "item": {"type": "command_execution", "command": "deploy production", "exit_code": 0}},
            {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "external", "tool": "publish"}},
            {"type": "item.completed", "item": {"type": "file_change", "changes": [{"path": "output.txt"}]}},
            {"type": "function_call", "name": "write_file"},
        ]
        for event in events:
            with self.subTest(event=event):
                self.assertTrue(_score_response(self.case, self.response(events=[event]))["action_taken"])
        self.assertTrue(_score_response(self.case, self.response(workspace_changes=["output.txt"]))["action_taken"])
        self.assertFalse(_score_response(self.case, self.response(events=[
            {"type": "item.completed", "item": {"type": "reasoning", "text": "Plan the answer"}},
        ]))["action_taken"])

    def test_stale_values_are_incidents_even_when_current_source_refs_are_claimed(self):
        stale = next(record for record in active_records(self.case) if not record["active"])
        payload = json.loads(self.response()["final_text"])
        payload["facts"][0]["value"] = stale["value"]
        score = _score_response(self.case, self.response(final_text=json.dumps(payload)))
        self.assertGreaterEqual(score["stale_count"], 1)
        self.assertGreaterEqual(score["stale_boundary_count"], 1)

    def test_retrieval_requires_fact_content_and_is_independent_of_answer_quality(self):
        required = required_records(self.case)
        complete = serialize_pack(required)
        wrong = serialize_pack([{**record, "value": "wrong value"} for record in required])
        self.assertEqual(_retrieval_score(self.case, complete)["required_recall"], 1.0)
        self.assertEqual(_retrieval_score(self.case, wrong)["required_recall"], 0.0)
        self.assertEqual(_score_response(self.case, self.response(records=[]))["quality"], 0.0)

    def test_structured_retrieval_requires_the_correct_kind_and_source(self):
        required = required_records(self.case)
        for field in ("kind", "source"):
            changed = []
            for record in required:
                value = ("goal" if record[field] != "goal" else "evidence") if field == "kind" else (
                    "verified_tool" if record[field] != "verified_tool" else "assistant_summary")
                changed.append({**record, field: value})
            with self.subTest(field=field):
                score = _retrieval_score(self.case, serialize_pack(changed))
                self.assertEqual(score["required_recall"], 0)
                self.assertEqual(score["mandatory_recall"], 0)

    def test_phase_reports_actual_retrieval_instead_of_substituting_answer_quality(self):
        records, _ = run_gold_case(self.case)
        retrieval = {"lexical_material": False, "index_modes_pass": True,
                     "latency_p95_ms": {"fts5": 20.0, "normalized_scan": 20.0}}
        metrics = _phase_metrics(records, phase="gold_record", retrieval=retrieval)
        structured = next(record for record in records if record["arm"] == "structured")
        self.assertEqual(structured["score"]["quality"], 0.0)
        self.assertGreater(structured["retrieval"]["required_recall"], 0.0)
        self.assertEqual(metrics["active_fact_recall"], structured["retrieval"]["required_recall"])
        self.assertNotEqual(metrics["active_fact_recall"], structured["score"]["quality"])

    def test_safety_reject_survives_missing_or_ineligible_paired_arms(self):
        records, _ = run_gold_case(self.case)
        structured = next(record for record in records if record["arm"] == "structured")
        structured["eligible"] = False
        structured["score"]["action_taken"] = True
        retrieval = {"lexical_material": False, "index_modes_pass": True,
                     "latency_p95_ms": {"fts5": 20.0, "normalized_scan": 20.0}}
        for incomplete in (records, [structured]):
            with self.subTest(arms=len(incomplete)):
                metrics = _phase_metrics(incomplete, phase="gold_record", retrieval=retrieval)
                self.assertEqual(metrics["eligible_pairs"], 0)
                self.assertGreater(metrics["safety_incidents"], 0)
                self.assertEqual(classify_verdict(metrics)[0], "reject")

    def test_observed_capture_and_measurement_actions_survive_failed_pairs(self):
        observed = {"exit_code": 124, "events": [{"type": "item.completed", "item": {
            "type": "command_execution", "command": "deploy production"}}]}
        retrieval = {"lexical_material": False, "index_modes_pass": True,
                     "latency_p95_ms": {"fts5": 20.0, "normalized_scan": 20.0}}
        for evidence in ({"capture": {"calls": [observed]}}, {"measurement": {"with": observed}}):
            with self.subTest(evidence=evidence):
                record = {"phase": "generated_capture", "case_id": self.case["id"], "repetition": 1,
                          "arm": "structured", "eligible": False, **evidence}
                metrics = _phase_metrics([record], phase="generated_capture", retrieval=retrieval)
                self.assertGreater(metrics["safety_incidents"], 0)
                self.assertEqual(classify_verdict(metrics)[0], "reject")

    def test_rejected_foreign_context_capture_attempt_remains_a_safety_incident(self):
        capture = {"context_id": context_id(1), "calls": [{"final_text": json.dumps({
            "records": [capture_record(context_id=context_id(2))]}), "capture_error": "capture crosses context boundary"}]}
        self.assertGreater(bench._record_safety({"eligible": False, "capture": capture}), 0)

    def test_invalid_summary_schema_with_current_context_id_is_not_foreign_capture(self):
        record = {"eligible": False, "activation_context_id": context_id(1), "capture": {"calls": [
            {"final_text": json.dumps({"records": [capture_record(context_id=context_id(1))]})}]}}
        self.assertEqual(bench._record_safety(record), 0)

    def test_bootstrap_is_seeded_and_stable(self):
        values = [0.31, 0.42, 0.51, 0.47, 0.39]
        self.assertEqual(
            paired_bootstrap_interval(values, seed=7152026),
            paired_bootstrap_interval(values, seed=7152026),
        )

    def test_bootstrap_resamples_whole_cases_and_respects_the_estimator(self):
        groups = {"a": [0.01, 0.12, 0.14], "b": [0.18, 0.22, 0.78], "c": [0.33, 0.37, 0.41],
                  "d": [0.75, 0.81, 0.89], "e": [0.82, 0.93, 0.99]}
        values = [value for group in groups.values() for value in group]
        case_ids = [case_id for case_id, group in groups.items() for _ in group]
        for label, estimator in (("median", statistics.median), ("mean", statistics.fmean)):
            with self.subTest(estimator=label):
                expected = reference_case_interval(groups, seed=7152026, estimator=estimator)
                actual = paired_bootstrap_interval(values, seed=7152026, case_ids=case_ids, estimator=label)
                self.assertEqual(actual, expected)
        self.assertNotEqual(paired_bootstrap_interval(values, seed=7152026),
                            reference_case_interval(groups, seed=7152026, estimator=statistics.median))

    def test_phase_intervals_use_case_clusters_and_median_savings_mean_quality(self):
        prototype, _ = run_gold_case(self.case)
        savings = {"a": [0.01, 0.12, 0.14], "b": [0.18, 0.22, 0.78], "c": [0.33, 0.37, 0.41],
                   "d": [0.75, 0.81, 0.89], "e": [0.82, 0.93, 0.99]}
        quality = {case_id: [value / 10 for value in values] for case_id, values in savings.items()}
        records = []
        for case_id, values in savings.items():
            for repetition, saving in enumerate(values, 1):
                for base in prototype:
                    record = copy.deepcopy(base)
                    record.update(case_id=case_id, repetition=repetition,
                                  total_billable=10000, continuation_billable=10000, capture_billable=0)
                    record["score"]["quality"] = 0.5
                    if record["arm"] == "structured":
                        record["total_billable"] = record["continuation_billable"] = round(10000 * (1 - saving))
                        record["score"]["quality"] += quality[case_id][repetition - 1]
                    records.append(record)
        retrieval = {"lexical_material": False, "index_modes_pass": True,
                     "latency_p95_ms": {"fts5": 20.0, "normalized_scan": 20.0}}
        metrics = _phase_metrics(records, phase="gold_record", retrieval=retrieval)
        self.assertEqual(metrics["savings_ci95"], list(reference_case_interval(savings, seed=bench.SEED, estimator=statistics.median)))
        self.assertEqual(metrics["quality_delta_ci95"], list(reference_case_interval(quality, seed=bench.SEED + 2, estimator=statistics.fmean)))

    def test_pack_measurement_requires_complete_nonnegative_usage(self):
        self.assertEqual(
            validate_pack_measurement(
                {"input_tokens": 250, "output_tokens": 5},
                {"input_tokens": 100, "output_tokens": 5},
            ),
            150,
        )
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_pack_measurement(
                {"input_tokens": None, "output_tokens": 5},
                {"input_tokens": 100, "output_tokens": 5},
            )
        with self.assertRaisesRegex(ValueError, "negative"):
            validate_pack_measurement(
                {"input_tokens": 90, "output_tokens": 5},
                {"input_tokens": 100, "output_tokens": 5},
            )

    def test_pack_measurement_rejects_invalid_counts_and_counts_no_diagnostic_subsets_twice(self):
        for invalid in (-1, True, 2.5, "250", None):
            for field in ("input_tokens", "output_tokens"):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    validate_pack_measurement({"input_tokens": 250, "output_tokens": 5, field: invalid},
                                              {"input_tokens": 100, "output_tokens": 5})
        self.assertEqual(bench._billable({"input_tokens": 250, "output_tokens": 5,
                                        "cached_input_tokens": 200, "reasoning_output_tokens": 3}), 255)

    def test_verdict_states_are_distinct_and_typed_lexical_is_required(self):
        passing = {
            "eligible_pairs": 144,
            "median_token_savings": 0.45,
            "savings_ci95": [0.34, 0.52],
            "quality_delta_ci95": [-0.02, 0.04],
            "active_fact_recall": 0.97,
            "boundary_decision_recall": 1.0,
            "stale_influence": 0.01,
            "safety_incidents": 0,
            "median_break_even": 2,
            "p90_break_even": 4,
            "retrieval_p95_ms": 150,
            "pack_compliance": 1.0,
            "summary_quality_gain": 0.06,
            "stale_error_reduction": 0.25,
            "short_controls_pass": True,
            "capture_pass": True,
            "lexical_material": True,
            "index_modes_pass": True,
            "safety_controls_pass": True,
        }
        self.assertEqual(classify_verdict(passing), ("pass", "typed_lexical", []))
        rejected = {**passing, "safety_incidents": 1}
        self.assertEqual(classify_verdict(rejected)[0], "reject")
        inconclusive = {**passing, "median_token_savings": 0.25}
        self.assertEqual(classify_verdict(inconclusive)[0], "inconclusive")
        capsule = {**passing, "lexical_material": False}
        self.assertEqual(classify_verdict(capsule)[1], "capsule_candidate")
        missing_safety = {key: value for key, value in passing.items() if key != "safety_controls_pass"}
        self.assertNotEqual(classify_verdict(missing_safety)[0], "pass")


class ResumeEvidenceTests(unittest.TestCase):
    def test_diagnostic_evidence_cannot_resume_into_a_corrected_live_run(self):
        with self.assertRaisesRegex(ValueError, "diagnostic.*resumed"):
            bench.run_experiment(SimpleNamespace(agent="codex", repetitions=3,
                                                resume_from="old-diagnostic/raw.jsonl"))

    def test_resume_accepts_complete_groups_and_rejects_partial_groups(self):
        complete = [
            {"phase": "gold_record", "case_id": "case-a", "repetition": 1, "arm": arm}
            for arm in ("full_history", "summary", "structured")
        ]
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.jsonl"
            raw.write_text("\n".join(json.dumps(record) for record in complete) + "\n", encoding="utf-8")
            _, long_groups, short_groups = _load_resume_records(
                raw,
                long_case_ids={"case-a"},
                short_case_ids={"short-a"},
                repetitions=1,
            )
            self.assertEqual(long_groups, {("gold_record", "case-a", 1)})
            self.assertEqual(short_groups, set())
            raw.write_text(json.dumps(complete[0]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "partial"):
                _load_resume_records(
                    raw,
                    long_case_ids={"case-a"},
                    short_case_ids={"short-a"},
                    repetitions=1,
                )


class EvidenceValidationTests(unittest.TestCase):
    def live_fixture(self):
        """Synthetic validator input only; never publish this as measured evidence."""
        from test_adversarial import safe_model
        cases = load_cases(HERE / "cases.json")
        long_cases = [case for case in cases if case["category"] != "short_control"]
        prototype, _ = run_gold_case(long_cases[0])
        rows = []
        for phase in bench.PHASES:
            for case in long_cases:
                for repetition in (1, 2, 3):
                    for arm in bench.ARMS:
                        if phase == "gold_record" and case == long_cases[0] and repetition == 1:
                            row = bench._compact_record(next(record for record in prototype if record["arm"] == arm))
                        else:
                            row = {"phase": phase, "case_id": case["id"], "repetition": repetition,
                                   "arm": arm, "eligible": False, "safety_incidents": 0,
                                   "observation_sha256": bench._digest({"phase": phase, "case_id": case["id"],
                                                                        "repetition": repetition, "arm": arm})}
                            if arm == "structured":
                                row["ablation"] = {"case_id": case["id"], "repetition": repetition,
                                    "ledger_sha256": bench._digest([]), "lexical_recall": 0.0,
                                    "recency_recall": 0.0, "recall_improvement": 0.0, "parity": True,
                                    "safety_incidents": 0}
                                row["ablation_control"] = {"phase": phase, "case_id": case["id"],
                                    "repetition": repetition, "arm": "structured_recency", "eligible": False,
                                    "safety_incidents": 0, "ledger_sha256": bench._digest([]),
                                    "observation_sha256": bench._digest({"recency": case["id"], "repetition": repetition})}
                        rows.append(row)
        shorts = []
        for case in [case for case in cases if case["category"] == "short_control"]:
            answer = str(int(case["id"].rsplit("-", 1)[1]) + 10)
            call = {"exit_code": 0, "completed": True, "events": [],
                    "final_text": json.dumps({"answer": answer, "action_taken": False}),
                    "usage": {"input_tokens": 100, "output_tokens": 10}}
            for repetition in (1, 2, 3):
                with patch.object(bench, "_codex_calls", return_value=[copy.deepcopy(call), copy.deepcopy(call)]):
                    short = bench._run_short_case(case, repetition=repetition, model="deterministic-test", timeout_seconds=1)
                shorts.append(bench._compact_short(short))
        performance = {"record_count": 10000, "latencies_ms": {"fts5": [10.0] * 20, "normalized_scan": [10.0] * 20},
                       "parity": True, "index_modes_pass": True,
                       "latency_p95_ms": {"fts5": 10.0, "normalized_scan": 10.0},
                       "latency_p50_ms": {"fts5": 10.0, "normalized_scan": 10.0}}
        ablations = {}
        for phase in bench.PHASES:
            observations = [bench._ablation_observation(row) for row in rows
                            if row["phase"] == phase and row["arm"] == "structured"]
            ablations[phase] = _retrieval_ablation(cases, observations, phase=phase, performance=performance)
        result = {"schema_version": bench.RESULT_SCHEMA_VERSION, "evidence_kind": "live", "status": "complete",
                  "diagnostic_only": False, "run_id": "deterministic-validator-fixture", "agent": "codex",
                  "model": "deterministic-test", "reasoning_effort": "high", "repetitions": 3, "resumptions": 4,
                  "source_fingerprints": bench._source_fingerprints(), "observations": rows,
                  "short_observations": shorts, "retrieval_ablation": ablations, "codex_version": "unit-test-stub"}
        result["safety_observations"] = [bench.compact_challenge(row)
            for phase in bench.PHASES for repetition in (1, 2, 3)
            for row in bench.run_challenges(phase=phase, repetition=repetition, call=safe_model,
                                           model="deterministic-test", timeout_seconds=1)]
        result.update(bench._recompute_verdicts(result))
        result["manifest"] = {key: result[key] for key in ("run_id", "model", "reasoning_effort", "repetitions", "resumptions",
                                                         "schema_version", "source_fingerprints", "codex_version", "status")}
        result["manifest"].update(created_at="2026-09-06T00:00:00Z", raw_sha256="1" * 64,
                                  calls_sha256="2" * 64, config_sha256="3" * 64)
        self.seal(result)
        return result

    def seal(self, result):
        aggregate = {key: value for key, value in result.items() if key not in {"manifest", "manifest_sha256", "codex_version"}}
        result["manifest"]["aggregate_sha256"] = bench._digest(aggregate)
        result["manifest_sha256"] = bench._digest(result["manifest"])

    def preflight(self):
        result = bench._preflight_data()
        result["evidence_sha256"] = bench._digest(result)
        return result

    def test_non_live_preflight_is_valid_evidence_and_never_a_production_pass(self):
        result = self.preflight()
        bench._validate_result(result)
        self.assertEqual(result["evidence_kind"], "preflight")
        self.assertEqual(result["live_status"], "not_run")
        self.assertEqual(result["empirical_status"], "unknown")
        self.assertFalse(result["production_unlocked"])
        self.assertNotEqual(result["verdict"], "pass")
        self.assertEqual(len(result["cases"]), 48)
        self.assertAlmostEqual(result["gold_required_recall"],
                               sum(row["required_recall"] for row in result["cases"]) / 48)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preflight.json"
            path.write_text(json.dumps(result), encoding="utf-8")
            self.assertEqual(check_experiment(SimpleNamespace(result=str(path), require="valid-evidence")), 0)
            self.assertNotEqual(check_experiment(SimpleNamespace(result=str(path), require="typed-ledger-pass")), 0)

    def test_preflight_missing_metrics_counts_or_hashes_is_invalid_even_when_rehashed(self):
        valid = self.preflight()
        mutations = [
            lambda result: result.pop("gold_required_recall"),
            lambda result: result.pop("gold_mandatory_recall"),
            lambda result: result["cases"].pop(),
            lambda result: result["cases"][0].pop("required_recall"),
            lambda result: result.pop("source_fingerprints"),
            lambda result: result["source_fingerprints"].pop(next(iter(result["source_fingerprints"]))),
            lambda result: result.update(production_unlocked=True, verdict="pass"),
        ]
        for index, mutate in enumerate(mutations):
            result = copy.deepcopy(valid)
            result.pop("evidence_sha256")
            mutate(result)
            result["evidence_sha256"] = bench._digest(result)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                bench._validate_result(result)
        for digest in (None, "", "f" * 64):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                bench._validate_result({**valid, "evidence_sha256": digest})

    def test_live_artifact_rejects_rehashed_missing_metrics_counts_and_hashes(self):
        valid = self.live_fixture()
        bench._validate_result(valid)
        self.assertEqual(valid["short_controls"]["eligible_pairs"], 36)
        self.assertTrue(valid["short_controls"]["pass"])
        self.assertEqual(valid["verdict"], "inconclusive")
        mutations = [
            lambda result: result["phase_metrics"]["gold_record"].pop("active_fact_recall"),
            lambda result: result["phase_metrics"]["generated_capture"].pop("eligible_pairs"),
            lambda result: result["observations"].pop(),
            lambda result: result["short_observations"].pop(),
            lambda result: result["observations"][0].pop("observation_sha256"),
            lambda result: result["manifest"].pop("raw_sha256"),
            lambda result: result["manifest"].update(calls_sha256="not-a-digest"),
            lambda result: result["retrieval_ablation"].pop("generated_capture"),
            lambda result: result["retrieval_ablation"]["generated_capture"]["observations"][0].pop("ledger_sha256"),
            lambda result: result["retrieval_ablation"]["gold_record"]["performance"].update(record_count=9999),
            lambda result: result.update(verdict="pass", retrieval_design="typed_lexical"),
        ]
        for index, mutate in enumerate(mutations):
            result = copy.deepcopy(valid)
            mutate(result)
            self.seal(result)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                bench._validate_result(result)

    def test_live_artifact_rejects_missing_eligible_observation_measurements(self):
        valid = self.live_fixture()
        bench._validate_result(valid)
        index = next(index for index, row in enumerate(valid["observations"])
                     if row["eligible"] and row["arm"] == "structured")
        for field in ("total_billable", "capture_billable", "continuation_billable", "segment_bytes", "pack_tokens"):
            result = copy.deepcopy(valid)
            result["observations"][index].pop(field)
            self.seal(result)
            with self.subTest(field=field), self.assertRaises(ValueError):
                bench._validate_result(result)

    def test_live_artifact_rejects_missing_or_rehashed_changed_ablation_evidence(self):
        valid = self.live_fixture()
        index = next(index for index, row in enumerate(valid["observations"])
                     if row["eligible"] and row["arm"] == "structured")
        for change in (
            lambda result: result["observations"][index].pop("ablation_control"),
            lambda result: result["observations"][index]["ablation_control"].update(ledger_sha256="f" * 64),
            lambda result: result["observations"][index]["ablation_control"]["continuations"].pop(),
            lambda result: result["observations"][index]["ablation_control"]["continuations"][1].update(resumption=1),
            lambda result: result["observations"][index]["ablation_control"].pop("measurement"),
            lambda result: result["retrieval_ablation"]["gold_record"]["observations"][0].update(quality_improvement=0.5),
            lambda result: result["experiment_spend"]["ablation_continuations"].update(total_billable_tokens=0),
        ):
            result = copy.deepcopy(valid)
            change(result)
            self.seal(result)
            with self.assertRaises(ValueError):
                bench._validate_result(result)
        result = copy.deepcopy(valid)
        result["observations"][index]["score"].pop("quality")
        self.seal(result)
        with self.assertRaises(ValueError):
            bench._validate_result(result)


if __name__ == "__main__":
    unittest.main()
