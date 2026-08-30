import copy
import unittest

from poc.model import canonical_digest
from poc.verify import (
    RUNTIME_POLICY,
    compare_verifications,
    deterministic_projection,
)


def verification_fixture(median_ms: float, p95_ms: float) -> dict:
    result = {
        "schema_version": "behavioral-memory-verification/v2",
        "artifact_digest": "sha256:artifact",
        "criterion_vector": {"C1": "PASS", "C10": "PASS"},
        "unit_tests": {"exit_code": 0, "passed": True, "summary": "OK"},
        "determinism": {"passed": True, "comparisons": []},
        "safety_probes": {"safe": True},
        "cross_agent_evidence": {
            "canonical_digest": "sha256:cross-agent",
            "passed": True,
        },
        "paired_agent_evidence": {
            "canonical_digest": "sha256:paired-agent",
            "passed": True,
        },
        "manifest": {"artifact": True},
        "runtime": {
            "measurements": {
                "sample_count": 500.0,
                "median_prediction_ms": median_ms,
                "p95_prediction_ms": p95_ms,
            },
            "policy": copy.deepcopy(RUNTIME_POLICY),
            "within_bounds": median_ms < 5.0 and p95_ms < 10.0,
        },
        "terminal": "DONE",
    }
    result["deterministic_evidence_digest"] = canonical_digest(
        deterministic_projection(result)
    )
    return result


class VerifierContractTests(unittest.TestCase):
    def test_timing_difference_preserved_but_deterministic_evidence_is_exact(self):
        first = verification_fixture(0.016625, 0.016791)
        second = verification_fixture(0.016750, 0.016958)

        comparison = compare_verifications(first, second)

        self.assertNotEqual(first["runtime"]["measurements"], second["runtime"]["measurements"])
        self.assertEqual(deterministic_projection(first), deterministic_projection(second))
        self.assertTrue(comparison["deterministic_evidence_exact"])
        self.assertTrue(comparison["runtime_evidence"]["within_declared_policy"])
        self.assertTrue(comparison["passed"])

    def test_runtime_bound_failure_cannot_be_hidden_by_tolerance(self):
        first = verification_fixture(0.02, 0.03)
        second = verification_fixture(5.50, 6.00)

        comparison = compare_verifications(first, second)

        self.assertFalse(comparison["runtime_evidence"]["both_runs_within_bounds"])
        self.assertFalse(comparison["passed"])

    def test_large_timing_drift_fails_even_when_both_runs_are_under_bounds(self):
        first = verification_fixture(0.01, 0.02)
        second = verification_fixture(0.20, 0.30)

        comparison = compare_verifications(first, second)

        self.assertFalse(comparison["runtime_evidence"]["within_repeat_tolerance"])
        self.assertFalse(comparison["passed"])

    def test_functional_difference_fails_exact_projection(self):
        first = verification_fixture(0.02, 0.03)
        second = verification_fixture(0.02, 0.03)
        second["safety_probes"]["safe"] = False
        second["deterministic_evidence_digest"] = canonical_digest(
            deterministic_projection(second)
        )

        comparison = compare_verifications(first, second)

        self.assertFalse(comparison["deterministic_evidence_exact"])
        self.assertFalse(comparison["passed"])

    def test_cross_agent_evidence_difference_fails_exact_projection(self):
        first = verification_fixture(0.02, 0.03)
        second = verification_fixture(0.02, 0.03)
        second["cross_agent_evidence"]["canonical_digest"] = "sha256:different"
        second["deterministic_evidence_digest"] = canonical_digest(
            deterministic_projection(second)
        )

        comparison = compare_verifications(first, second)

        self.assertFalse(comparison["deterministic_evidence_exact"])
        self.assertFalse(comparison["passed"])

    def test_paired_agent_evidence_difference_fails_exact_projection(self):
        first = verification_fixture(0.02, 0.03)
        second = verification_fixture(0.02, 0.03)
        second["paired_agent_evidence"]["canonical_digest"] = "sha256:different"
        second["deterministic_evidence_digest"] = canonical_digest(
            deterministic_projection(second)
        )

        comparison = compare_verifications(first, second)

        self.assertFalse(comparison["deterministic_evidence_exact"])
        self.assertFalse(comparison["passed"])


if __name__ == "__main__":
    unittest.main()
