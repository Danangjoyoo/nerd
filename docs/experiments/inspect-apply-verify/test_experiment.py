from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import baselines
from bench import RpcClient
from fixtures import (
    checks_for,
    expected_hashes,
    materialize,
    patch_for,
    tree_hash,
)
from tools import InspectIndex, apply_verify, canonical_apply


class ExperimentContractTests(unittest.TestCase):
    def test_fixtures_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            for case_id in (
                "inspect-small",
                "inspect-large",
                "apply-small",
                "apply-large",
            ):
                materialize(case_id, first)
                materialize(case_id, second)
                self.assertEqual(tree_hash(first), tree_hash(second))

    def test_inspect_matches_batched_rg_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fixture"
            materialize("inspect-large", root)
            baseline = baselines.inspect(str(root), "target_large", 2, 3)
            index = InspectIndex()
            candidate = index.inspect(str(root), "target_large", 2, 3)
            self.assertEqual(baseline["matches"], candidate["matches"])
            self.assertFalse(candidate["cache_hit"])
            self.assertTrue(index.inspect(str(root), "target_large", 2, 3)["cache_hit"])

    def test_apply_verify_matches_two_request_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            baseline_root = Path(temporary) / "baseline"
            candidate_root = Path(temporary) / "candidate"
            materialize("apply-large", baseline_root)
            materialize("apply-large", candidate_root)
            patch = patch_for("apply-large")
            checks = checks_for("apply-large")
            baseline_applied = baselines.apply_patch(
                str(baseline_root),
                patch,
                expected_hashes("apply-large", baseline_root),
            )
            baseline_checked = baselines.verify(
                str(baseline_root), baseline_applied["changed_paths"], checks
            )
            baseline = {
                "patch_status": baseline_applied["patch_status"],
                "changed_paths": baseline_applied["changed_paths"],
                "diff_sha256": baseline_checked["diff_sha256"],
                "checks": baseline_checked["checks"],
                "exit_codes": baseline_checked["exit_codes"],
                "rolled_back": False,
            }
            candidate = apply_verify(
                str(candidate_root),
                patch,
                expected_hashes("apply-large", candidate_root),
                checks,
            )
            self.assertEqual(canonical_apply(baseline), canonical_apply(candidate))

    def test_stale_hash_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fixture"
            materialize("apply-small", root)
            before = tree_hash(root)
            hashes = expected_hashes("apply-small", root)
            hashes["feature.py"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "stale starting hash"):
                apply_verify(
                    str(root),
                    patch_for("apply-small"),
                    hashes,
                    checks_for("apply-small"),
                )
            self.assertEqual(before, tree_hash(root))

    def test_failed_verification_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fixture"
            materialize("apply-small", root)
            before = tree_hash(root)
            result = apply_verify(
                str(root),
                patch_for("apply-small"),
                expected_hashes("apply-small", root),
                [["python3", "-c", "raise SystemExit(1)"]],
            )
            self.assertEqual("verification_failed", result["patch_status"])
            self.assertTrue(result["rolled_back"])
            self.assertEqual(before, tree_hash(root))

    def test_rpc_server_dispatches_candidate_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fixture"
            materialize("inspect-small", root)
            with RpcClient() as client:
                response = client.call(
                    "candidate.inspect",
                    {
                        "workspace": str(root),
                        "symbol": "target_small",
                        "context_lines": 2,
                        "max_results": 1,
                    },
                )
            self.assertEqual(1, len(response["result"]["matches"]))
            self.assertGreater(response["observed_ns"], 0)


if __name__ == "__main__":
    unittest.main()
