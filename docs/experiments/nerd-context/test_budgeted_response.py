import copy
import json
from pathlib import Path
import unittest

import budgeted_response as budget
from deployable_response import ContractError, json_bytes
from fixtures import active_records, load_cases, required_records
from structured import StructuredLedger
from test_deployable_response import CTX, OTHER, record


def native_text(response, seconds=budget.MAX_DURATION_TEXT):
    return "Wall time: " + seconds + " seconds\nOutput:\n" + json.dumps(response.payload, ensure_ascii=False, separators=(",", ":"))


class BudgetTests(unittest.TestCase):
    def test_full_duration_bound_selfcount_unicode_escaping_and_native_receipt(self):
        result = budget.serialize_native_recall(context_id=CTX, records=[record()])
        observed = budget.verify_native_output(result, native_text(result))
        self.assertEqual(len("Wall time: " + budget.MAX_DURATION_TEXT + " seconds\nOutput:\n"), 53)
        self.assertEqual(result.payload["serialized_bytes"], len(result.payload_json))
        self.assertEqual(observed["actual_native_output_bytes"], result.budgeted_output_bytes)
        self.assertEqual(result.budgeted_output_bytes, len(result.payload_json) + 53)
        self.assertLess(budget.verify_native_output(result, native_text(result, "0.0000"))["actual_native_output_bytes"], result.budgeted_output_bytes)

    def test_exact_2048_and_2049_complete_output_boundary(self):
        first = budget.serialize_native_recall(context_id=CTX, records=[record(value="x")])
        padding = 2048 - first.budgeted_output_bytes
        result = budget.serialize_native_recall(context_id=CTX, records=[record(value="x" * (1 + padding))])
        # Crossing digit widths in the size fields may consume a few bytes.
        while result.payload["overflow"]:
            padding -= 1
            result = budget.serialize_native_recall(context_id=CTX, records=[record(value="x" * (1 + padding))])
        self.assertEqual(result.budgeted_output_bytes, 2048)
        self.assertEqual(len(native_text(result).encode()), 2048)
        larger = budget.serialize_native_recall(context_id=CTX, records=[record(value="x" * (2 + padding))])
        self.assertEqual(larger.attempted_budgeted_bytes, 2049)
        self.assertTrue(larger.payload["overflow"])
        self.assertEqual(larger.payload["records"], [])
        self.assertLessEqual(budget.verify_native_output(larger, native_text(larger))["actual_native_output_bytes"], 2048)

    def test_changed_missing_truncated_or_unpinned_native_content_rejected(self):
        result = budget.serialize_native_recall(context_id=CTX, records=[record()])
        good = native_text(result)
        changed = copy.deepcopy(result.payload)
        del changed["authority"]
        bad = [good[:-1], good.replace("source-1", "source-other"),
               "Wall time: 0.0000 seconds\nOutput:\n" + json.dumps(changed),
               good.replace(budget.MAX_DURATION_TEXT, "999999999999999999999.0000")]
        for value in bad:
            with self.subTest(value=value[:50]), self.assertRaises(ContractError):
                budget.verify_native_output(result, value)
        with self.assertRaises(ContractError):
            budget.verify_native_output(result, good, client_version="unverified")

    def test_canonical_mcp_wire_roundtrip_remains_valid_native_delivery(self):
        response = budget.serialize_native_recall(context_id=CTX, records=[record()])
        received = json.loads(json_bytes(response.mcp_result))["structuredContent"]
        delivered = "Wall time: 0.0000 seconds\nOutput:\n" + json.dumps(received, ensure_ascii=False, separators=(",", ":"))
        observed = budget.verify_native_output(response, delivered)
        self.assertEqual(observed["actual_native_output_bytes"], len(delivered.encode()))

    def test_mandatory_anchor_and_conflict_overflow_is_complete_abstention(self):
        records = [record(index, value="x" * 500, anchors=[{"path": f"src/{index}.py", "sha256": "a" * 64}]) for index in range(3)]
        selected = budget.select_native_response(context_id=CTX, records=records, query="x",
                                                conflict_groups=[{"record_ids": ["record-0", "record-1"]}])
        self.assertTrue(selected.response.payload["overflow"])
        self.assertEqual(selected.record_ids, ())
        self.assertEqual(selected.response.payload["records"], [])
        self.assertEqual(selected.response.payload["conflicts"], [])
        self.assertEqual(selected.response.payload["context_id"], CTX)

    def test_anchor_content_is_preserved_when_it_fits(self):
        original = record(anchors=[{"path": "src/a.py", "symbol": "A", "sha256": "a" * 64}])
        selected = budget.select_native_response(context_id=CTX, records=[original], query="a")
        self.assertEqual(selected.response.payload["records"][0]["anchors"], original["anchors"])
        with self.assertRaises(ContractError):
            budget.select_native_response(context_id=CTX, records=[original], query="a",
                                          conflict_groups=[{"record_ids": ["record-1", "missing"]}])

    def test_twenty_and_256k_canonical_capture_limits(self):
        base = {key: value for key, value in record().items() if key in {"kind", "value", "source", "source_ref"}}
        request = {"context_id": CTX, "capture_ref": "capture-1", "records": [copy.deepcopy(base) for _ in range(20)]}
        self.assertEqual(len(budget.validate_bounded_capture(request, existing_record_contexts={})["records"]), 20)
        request["records"].append(copy.deepcopy(base))
        with self.assertRaises(ContractError):
            budget.validate_bounded_capture(request, existing_record_contexts={})
        request["records"].pop()
        # Escaped control bytes exercise canonical argument size, not raw text size.
        for item in request["records"]:
            item["value"] = "\x01" * 2100
        remaining = budget.MAX_CAPTURE_ARGUMENT_BYTES - len(json_bytes(request))
        for item in request["records"]:
            added = min(remaining, 8192 - len(item["value"].encode()))
            item["value"] += "x" * added
            remaining -= added
        self.assertEqual(remaining, 0)
        self.assertLessEqual(len(request["records"][0]["value"].encode()), 8192)
        self.assertEqual(len(json_bytes(request)), 256 * 1024)
        budget.validate_bounded_capture(request, existing_record_contexts={})
        request["records"][-1]["value"] += "x"
        with self.assertRaises(ContractError):
            budget.validate_bounded_capture(request, existing_record_contexts={})
        with self.assertRaises(ContractError):
            budget.validate_bounded_capture(request, existing_record_contexts={}, max_bytes=256 * 1024 + 1)

    def test_unknown_id_never_creates_or_reuses_another_context(self):
        with StructuredLedger([record()]) as ledger:
            before = ledger._connection.execute("SELECT count(*) FROM contexts").fetchone()[0]
            result = budget.recall_from_ledger(ledger, context_id=OTHER, query="x")
            after = ledger._connection.execute("SELECT count(*) FROM contexts").fetchone()[0]
        self.assertEqual(before, after)
        self.assertEqual(result.response.payload["status"], "not_found")
        self.assertEqual(result.response.payload["context_id"], OTHER)
        self.assertEqual(result.record_ids, ())

    def test_no_pressure_ranking_matches_existing_order_without_label_dependence(self):
        records = [record(0, kind="goal", value="goal"), record(1, kind="evidence", value="rare apple"),
                   record(2, kind="evidence", value="common banana"), record(3, kind="evidence", value="common common banana")]
        with StructuredLedger(records) as ledger:
            old = ledger.recall(context_id=CTX, query="rare common")
            new = budget.recall_from_ledger(ledger, context_id=CTX, query="rare common")
        self.assertEqual(new.record_ids, old.record_ids)
        flipped = [{**item, "required": index % 2 == 0, "rubric_weight": 100 - index} for index, item in enumerate(records)]
        plain = budget.select_native_response(context_id=CTX, records=records, query="rare common")
        labelled = budget.select_native_response(context_id=CTX, records=flipped, query="rare common")
        self.assertEqual(plain.response.payload_json, labelled.response.payload_json)

    def test_current_fixtures_keep_mode_parity_mandatory_facts_and_negative_recall_evidence(self):
        recalls, complete = [], 0
        for case in load_cases(Path(__file__).with_name("cases.json")):
            if case["category"] == "short_control":
                continue
            modes = []
            for index_mode in ("normalized_scan", "fts5"):
                with StructuredLedger(active_records(case), index_mode=index_mode) as ledger:
                    selected = budget.recall_from_ledger(ledger, context_id=case["context_id"], query=case["request"])
                self.assertLessEqual(selected.response.budgeted_output_bytes, 2048)
                self.assertFalse(selected.response.payload["overflow"])
                mandatory = {item["id"] for item in active_records(case) if item["active"] and item["kind"] in {"goal", "boundary", "decision"}}
                self.assertTrue(mandatory <= set(selected.record_ids))
                modes.append(selected)
            self.assertEqual(modes[0].response.payload_json, modes[1].response.payload_json)
            required = {item["id"] for item in required_records(case)}
            recall = len(required & set(modes[0].record_ids)) / len(required)
            recalls.append(recall)
            complete += recall == 1
        self.assertEqual(len(recalls), 48)
        self.assertEqual(complete, 12)
        self.assertAlmostEqual(sum(recalls) / len(recalls), 291 / 336)


if __name__ == "__main__":
    unittest.main()
