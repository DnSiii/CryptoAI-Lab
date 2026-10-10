"""Adversarial tests for V99 historical/forward partition."""
import copy
import unittest
from scripts.v99_phase195bm_historical_partition import partition, audit_references, NAMES
B = "2026-09-16T13:00:00+00:00"
def row(t, m=1.0, ret=0.0):
    return {"timestamp": t, "equity_multiple": m, "daily_return_pct": ret}
def ledger():
    return {"mode": "PAPER_ONLY", "paper_start_after_timestamp": B,
            "backtest_reference": {k: {"curve": [row("2026-09-15T02:00:00Z"),
                                                  row("2026-09-16T02:00:00Z", 1.1, 10),
                                                  row("2026-09-17T02:00:00Z", 1.2, 9.09)]}
                                   for k in NAMES}}
class TestHistoricalPartition(unittest.TestCase):
    def test_excludes_forward_without_mutating_original(self):
        src = ledger()["backtest_reference"]["f1"]["curve"]
        original = copy.deepcopy(src)
        out = partition(src, B)
        self.assertEqual(len(out["historical_curve"]), 2)
        self.assertEqual(out["quarantined_forward_rows"], 1)
        self.assertEqual(src, original)
    def test_boundary_equal_is_forward(self):
        self.assertEqual(partition([row("2026-09-15T02:00:00Z"), row(B)], B)["quarantined_forward_rows"], 1)
    def test_extension_cannot_change_historical(self):
        src = ledger()["backtest_reference"]["f1"]["curve"]
        extended = src + [row("2026-09-18T02:00:00Z", 1.4, 16.67)]
        self.assertEqual(partition(src, B)["historical_curve"], partition(extended, B)["historical_curve"])
    def test_rejects_naive_and_offset(self):
        for t in ("2026-09-15T02:00:00", "2026-09-15T02:00:00-03:00"):
            with self.assertRaises(ValueError): partition([row(t)], B)
    def test_rejects_duplicate_and_unsorted(self):
        r = row("2026-09-15T02:00:00Z")
        for rows in ([r,r], [row("2026-09-16T02:00:00Z"),r]):
            with self.assertRaises(ValueError): partition(rows, B)
    def test_rejects_nonfinite_and_boolean(self):
        for value in (float("nan"), float("inf"), True, None):
            with self.assertRaises(ValueError): partition([row("2026-09-15T02:00:00Z", value)], B)
    def test_rejects_empty_pre_boundary(self):
        with self.assertRaises(ValueError): partition([row(B)], B)
    def test_audit_detects_changed_pre_boundary_and_keeps_hold(self):
        old, new = ledger(), ledger()
        new["backtest_reference"]["f3"]["curve"][0]["equity_multiple"] = 1.5
        result = audit_references(old,new)
        self.assertEqual(result["variants"]["f3"]["historical_changed"],1)
        self.assertEqual(result["status"], "DATA_ONLY_HOLD")
        self.assertFalse(result["publication_authorized"])
    def test_audit_detects_changed_metadata(self):
        old,new=ledger(),ledger()
        new["backtest_reference"]["f3"]["historicalRoiPct"] = 99
        result=audit_references(old,new)
        self.assertTrue(result["variants"]["f3"]["historical_metadata_changed"])
    def test_audit_boundary_moved(self):
        old,new=ledger(),ledger()
        new["paper_start_after_timestamp"] = "2026-09-16T14:00:00Z"
        with self.assertRaises(ValueError): audit_references(old,new)
    def test_audit_paper_only_required(self):
        old,new=ledger(),ledger()
        new["mode"]="LIVE"
        with self.assertRaises(ValueError): audit_references(old,new)
if __name__ == "__main__": unittest.main()
