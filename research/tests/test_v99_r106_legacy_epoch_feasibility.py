"""Proof that the legacy R106 paper guard is unsatisfiable with capped old data."""
import copy
import json
import unittest

from research.tools.v99_r106_legacy_epoch_feasibility import prove
from scripts.v99_phase195bj_paper_publication_guard import NAMES

B="2026-09-16T13:00:00+00:00"
H="2026-09-16T14:00:00+00:00"
PRE="2024-01-01T00:00:00+00:00"

def fixture():
    return {
      "mode":"PAPER_ONLY","real_orders_enabled":False,
      "same_boundary_for_all_variants":True,
      "paper_start_after_timestamp":B,"latest_data_timestamp":H,
      "variants":{k:{"paper_start_after_timestamp":B,
                       "real_orders_enabled":False,
                       "equity_curve":[{"timestamp":B,"capital_brl":10000},
                                       {"timestamp":H,"capital_brl":10001}],
                       "operations":[{"timestamp":H,"symbol":"BTCUSDT"}]}
                  for k in NAMES},
      "backtest_reference":{k:{"curve":[{"timestamp":PRE,"equity_multiple":1}]}
                            for k in NAMES},
    }

def inspect(item):
    return prove(json.dumps(item,sort_keys=True).encode())


class TestFeasibility(unittest.TestCase):
    def test_clean_old_prefix_not_structurally_impossible(self):
        r=inspect(fixture())
        self.assertEqual(r["status"],"OLD_PREFIX_NOT_STRUCTURALLY_IMPOSSIBLE")
        self.assertIsNone(r["current_epoch_guard_can_pass_any_candidate"])
        self.assertFalse(r["publication_authorized"])

    def test_one_published_cap_makes_any_candidate_impossible(self):
        a=fixture()
        a["variants"]["f1"]["operations"]=[
            {"timestamp":H,"symbol":f"A{i:04d}"} for i in range(1500)]
        r=inspect(a)
        self.assertEqual(r["status"],"NEW_VERSIONED_EPOCH_REQUIRED")
        self.assertFalse(r["current_epoch_guard_can_pass_any_candidate"])
        self.assertTrue(r["variants"]["f1"]["old_ops_cap_guarantees_guard_failure"])
        self.assertIn("operations_capped_unverifiable",r["variants"]["f1"]["unchanged_candidate_guard_flags"])

    def test_published_reference_overlap_alone_makes_epoch_impossible(self):
        a=fixture()
        a["backtest_reference"]["f3"]["curve"].append(
            {"timestamp":B,"equity_multiple":1.2})
        r=inspect(a)
        self.assertEqual(r["status"],"NEW_VERSIONED_EPOCH_REQUIRED")
        self.assertEqual(r["variants"]["f3"]["historical_reference_points_after_paper"],1)
        self.assertTrue(r["variants"]["f3"]["backtest_paper_leak_guarantees_guard_failure"])

    def test_2024_train_overrun_without_paper_overlap_is_separately_reported(self):
        a=fixture()
        a["backtest_reference"]["r98"]["curve"].append(
            {"timestamp":"2025-01-01T00:00:00Z","equity_multiple":1.1})
        r=inspect(a)
        self.assertEqual(r["variants"]["r98"]["historical_reference_points_after_train"],1)
        self.assertEqual(r["variants"]["r98"]["historical_reference_points_after_paper"],0)
        self.assertEqual(r["status"],"OLD_PREFIX_NOT_STRUCTURALLY_IMPOSSIBLE")

    def test_exact_cap_trigger_is_at_1500(self):
        a=fixture()
        a["variants"]["f3"]["operations"]=[
            {"timestamp":H,"symbol":f"X{i:04d}"} for i in range(1499)]
        self.assertEqual(inspect(a)["status"],"OLD_PREFIX_NOT_STRUCTURALLY_IMPOSSIBLE")
        a["variants"]["f3"]["operations"].append({"timestamp":H,"symbol":"X1499"})
        self.assertEqual(inspect(a)["status"],"NEW_VERSIONED_EPOCH_REQUIRED")

    def test_original_object_is_not_mutated(self):
        a=fixture()
        before=copy.deepcopy(a)
        inspect(a)
        self.assertEqual(a,before)

    def test_invariant_never_opens_holdout_or_trades(self):
        r=inspect(fixture())
        self.assertFalse(r["old_epoch_can_be_mutated"])
        self.assertFalse(r["new_epoch_source_receipts_authenticated"])
        self.assertFalse(r["holdout_accessed"])
        self.assertEqual(r["economic_trials"],0)

    def test_duplicate_json_key_fails(self):
        with self.assertRaises(ValueError):
            prove(b'{"mode":"PAPER_ONLY","mode":"PAPER_ONLY"}')

    def test_nonfinite_json_constant_fails(self):
        with self.assertRaises(ValueError):
            prove(b'{"n":NaN}')


if __name__=="__main__":
    unittest.main()
