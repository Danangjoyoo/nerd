"""Boundary proof for the prospective contract, independent of POC ranking."""
import copy
import json
from pathlib import Path
import unittest

import deployable_response as response
from fixtures import active_records, load_cases


CTX = "ctx_" + "a" * 39
OTHER = "ctx_" + "b" * 38 + "a"


def record(index=1, **changes):
    return {"id": f"record-{index}", "context_id": CTX, "active": True,
            "kind": "boundary", "source": "direct_user", "source_ref": f"source-{index}",
            "value": 'Read only: preserve "日本語" and \\ paths.', **changes}


def serialize(records, **kwargs):
    return response.serialize_recall(context_id=CTX, records=records,
                                    project=response.transport_json_projection,
                                    projection_name="diagnostic-transport-json", **kwargs)


class ResponseTests(unittest.TestCase):
    def test_complete_self_counted_envelope_and_text_structured_equality(self):
        result = serialize([record(anchors=[{"path": "src/main.py", "symbol": "main", "sha256": "c" * 64}])])
        payload = result.payload
        self.assertEqual(payload["serialized_bytes"], len(result.model_visible_bytes))
        self.assertEqual(payload["estimated_tokens"], (len(result.model_visible_bytes) + 3) // 4)
        self.assertEqual(json.loads(result.mcp_result["content"][0]["text"]), payload)
        self.assertEqual(result.mcp_result["structuredContent"], payload)
        self.assertEqual(payload["records"][0]["authority"], "untrusted_context")
        self.assertEqual(payload["records"][0]["anchors"][0]["path"], "src/main.py")
        self.assertEqual(payload["records"][0]["value"], record()["value"])
        self.assertEqual(result.token_measurement, "not_established")
        self.assertGreater(len(result.model_visible_bytes), 2 * len(payload["records"][0]["value"].encode()))

    def test_exact_lower_boundary_and_overflow_never_partially_hydrates(self):
        records = [record()]
        exact = serialize(records)
        self.assertEqual(serialize(records, max_bytes=len(exact.model_visible_bytes)).payload["status"], "ok")
        failed = serialize(records, max_bytes=len(exact.model_visible_bytes) - 1)
        self.assertEqual(failed.payload["status"], "overflow")
        self.assertEqual(failed.payload["records"], [])
        self.assertTrue(failed.mcp_result["isError"])
        self.assertEqual(failed.payload["context_id"], CTX)
        self.assertEqual(failed.attempted_bytes, len(exact.model_visible_bytes))

    def test_large_mandatory_fact_is_not_clipped(self):
        result = serialize([record(value="x" * 1800)])
        self.assertTrue(result.payload["overflow"])
        self.assertEqual(result.payload["records"], [])
        self.assertGreater(result.attempted_bytes, 2048)
        self.assertLessEqual(len(result.model_visible_bytes), 2048)

    def test_control_too_small_is_explicit_and_budgets_cannot_expand(self):
        for budget in (0, 2049, True):
            with self.subTest(budget=budget), self.assertRaises(response.ContractError):
                serialize([], max_bytes=budget)
        with self.assertRaises(response.BudgetTooSmall):
            serialize([], max_bytes=10)

    def test_identity_active_duplicate_and_creation_guards(self):
        for records in ([record(context_id=OTHER)], [record(active=False)], [record(), record()]):
            with self.subTest(records=records), self.assertRaises(response.ContractError):
                serialize(records)
        with self.assertRaises(response.ContractError):
            serialize([record()], created=True)
        created = serialize([], created=True)
        self.assertTrue(created.payload["created"])
        unknown = serialize([], status="not_found", retrieval_path="none")
        self.assertFalse(unknown.payload["created"])
        self.assertEqual(unknown.payload["records"], [])
        for kwargs in ({"status": []}, {"retrieval_path": []}, {"status": "not_found", "created": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(response.ContractError):
                serialize([], **kwargs)

    def test_conflicts_keep_same_context_record_identifiers(self):
        result = serialize([record()], unresolved_conflicts=[{"record_ids": ["record-1", "record-2"]}],
                           known_record_contexts={"record-1": CTX, "record-2": CTX})
        self.assertEqual(result.payload["conflicts"], [{"record_ids": ["record-1", "record-2"]}])
        for bad in (["record-1", "record-1"], ["record-1", "foreign"]):
            with self.assertRaises(response.ContractError):
                serialize([record()], unresolved_conflicts=[{"record_ids": bad}],
                          known_record_contexts={"record-1": CTX, "foreign": OTHER})

    def test_projection_is_required_and_counts_outer_wrapper(self):
        project = lambda result: b"OUTER" + response.json_bytes(result) + b"END"
        rendered = response.serialize_recall(context_id=CTX, records=[], project=project, projection_name="test-wrapper")
        self.assertEqual(rendered.payload["serialized_bytes"], len(rendered.model_visible_bytes))
        self.assertTrue(rendered.model_visible_bytes.startswith(b"OUTER"))
        with self.assertRaises(response.ContractError):
            response.serialize_recall(context_id=CTX, records=[], project=lambda _: "not bytes", projection_name="bad")

    def test_observed_native_projection_preserves_payload_once_and_complete_wrapper(self):
        project = response.observed_codex_http_projection(call_id="call_fixture", output_id="fco_fixture", wall_seconds="0.0042")
        rendered = response.serialize_recall(context_id=CTX, records=[record()], project=project,
                                             projection_name="observed-codex-http-template")
        item = json.loads(rendered.model_visible_bytes)
        self.assertEqual(item["call_id"], "call_fixture")
        self.assertEqual(item["id"], "fco_fixture")
        prefix, payload = item["output"].split("\nOutput:\n")
        self.assertEqual(prefix, "Wall time: 0.0042 seconds")
        self.assertEqual(json.loads(payload), rendered.payload)
        self.assertEqual(item["output"].count("source-1"), 1)
        self.assertEqual(rendered.payload["serialized_bytes"], len(rendered.model_visible_bytes))
        bad = copy.deepcopy(rendered.mcp_result)
        bad["content"][0]["text"] = "different"
        with self.assertRaises(response.ContractError):
            project(bad)

    def test_native_overflow_receipt_is_bounded_without_stored_values(self):
        project = response.observed_codex_http_projection(call_id="call_fixture", output_id="fco_fixture", wall_seconds="0.0051")
        rendered = response.serialize_recall(context_id=CTX, records=[record(value="x" * 2000)], project=project,
                                             projection_name="observed-codex-http-template")
        self.assertEqual(rendered.payload["status"], "overflow")
        self.assertEqual(rendered.payload["records"], [])
        self.assertLessEqual(len(rendered.model_visible_bytes), 2048)
        self.assertTrue(rendered.mcp_result["isError"])

    def test_fixture_values_and_labels_are_not_rewritten_for_capacity(self):
        cases = load_cases(Path(__file__).with_name("cases.json"))
        originals = copy.deepcopy(cases)
        long_cases = [case for case in cases if case["category"] != "short_control"]
        self.assertEqual(len(long_cases), 48)
        for case in long_cases:
            records = [item for item in active_records(case) if item["active"] and item["context_id"] == case["context_id"]]
            result = response.serialize_recall(context_id=case["context_id"], records=records,
                                               project=response.transport_json_projection, projection_name="diagnostic-transport-json")
            self.assertTrue(result.payload["overflow"])
            self.assertEqual(result.payload["records"], [])
        self.assertEqual(cases, originals)


class CaptureTests(unittest.TestCase):
    def request(self, count=1):
        return {"context_id": CTX, "capture_ref": "checkpoint-1", "records": [
            {key: value for key, value in record(index).items() if key in {"kind", "value", "source", "source_ref"}}
            for index in range(count)]}

    def validate(self, request, **kwargs):
        return response.validate_capture_request(request, existing_record_contexts={"old": CTX, "foreign": OTHER},
                                                 max_capture_bytes=kwargs.get("max_capture_bytes", 65536))

    def test_twenty_accepted_twenty_one_rejected_without_input_mutation(self):
        self.assertEqual(len(self.validate(self.request(20))["records"]), 20)
        request = self.request(21)
        before = copy.deepcopy(request)
        with self.assertRaises(response.ContractError):
            self.validate(request)
        self.assertEqual(request, before)

    def test_aggregate_exact_boundary_and_explicit_limit(self):
        request = self.request()
        size = len(response.json_bytes(request))
        self.assertEqual(self.validate(request, max_capture_bytes=size), request)
        for limit in (size - 1, None, True):
            with self.assertRaises(response.ContractError):
                self.validate(request, max_capture_bytes=limit)

    def test_all_items_validated_before_any_caller_can_persist(self):
        request = self.request(2)
        request["records"][1]["kind"] = "permission"
        stored = []
        with self.assertRaises(response.ContractError):
            accepted = self.validate(request)
            stored.extend(accepted["records"])
        self.assertEqual(stored, [])

    def test_same_context_supersession_and_no_duplicate_target(self):
        request = self.request()
        request["records"][0]["supersedes_id"] = "old"
        self.assertEqual(self.validate(request), request)
        for target in ("foreign", "missing"):
            request["records"][0]["supersedes_id"] = target
            with self.assertRaises(response.ContractError):
                self.validate(request)
        request = self.request(2)
        for item in request["records"]:
            item["supersedes_id"] = "old"
        with self.assertRaises(response.ContractError):
            self.validate(request)

    def test_anchors_preserved_and_unsafe_paths_rejected(self):
        request = self.request()
        request["records"][0]["anchors"] = [{"path": "src/main.py", "symbol": "main", "sha256": "a" * 64}]
        self.assertEqual(self.validate(request), request)
        for path in ("../secret", "/absolute", "a/../b", "a//b", "a\\b", "C:thing", "./a", "~/a", "a\nb"):
            request["records"][0]["anchors"] = [{"path": path}]
            with self.subTest(path=path), self.assertRaises(response.ContractError):
                self.validate(request)


if __name__ == "__main__":
    unittest.main()
