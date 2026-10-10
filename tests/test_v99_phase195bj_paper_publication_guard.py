"""Adversarial offline tests for the V99 Phase195-BJ fail-closed paper gate."""
import copy
import unittest
from scripts.v99_phase195bj_paper_publication_guard import audit, strict_json, NAMES

B = "2026-09-16T13:00:00+00:00"
H = "2026-09-16T14:00:00+00:00"
N = "2026-09-16T15:00:00+00:00"
P = "2026-09-15T00:00:00+00:00"


def fixture():
    return {
        "mode": "PAPER_ONLY", "real_orders_enabled": False,
        "same_boundary_for_all_variants": True,
        "paper_start_after_timestamp": B, "latest_data_timestamp": H,
        "variants": {k: {
            "paper_start_after_timestamp": B, "real_orders_enabled": False,
            "equity_curve": [{"timestamp": B, "capital_brl": 10000},
                             {"timestamp": H, "capital_brl": 10010}],
            "operations": [{"timestamp": H, "symbol": "BTCUSDT", "action": "buy"}],
        } for k in NAMES},
        "backtest_reference": {k: {"curve": [
            {"timestamp": P, "equity_multiple": 1.0}
        ]} for k in NAMES},
    }


def extended():
    a = fixture()
    a["latest_data_timestamp"] = N
    for name in NAMES:
        a["variants"][name]["equity_curve"].append(
            {"timestamp": N, "capital_brl": 10011})
    return a


class TestPhase195BJ(unittest.TestCase):
    def test_append_only_not_promotion(self):
        r = audit(fixture(), extended())
        self.assertTrue(r["publication_authorized"])
        self.assertFalse(r["promotion_authorized"])

    def test_paper_rewrite(self):
        b = extended()
        b["variants"]["f3"]["equity_curve"][1]["capital_brl"] = 9999
        self.assertEqual(audit(fixture(), b)["status"], "DATA_ONLY_HOLD")

    def test_paper_gap(self):
        b = extended()
        b["variants"]["f3"]["equity_curve"].pop(1)
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_backtest_contamination(self):
        b = extended()
        b["backtest_reference"]["r98"]["curve"].append(
            {"timestamp": B, "equity_multiple": 1.1})
        self.assertEqual(audit(fixture(), b)["status"], "DATA_ONLY_HOLD")

    def test_preexisting_backtest_contamination(self):
        a = fixture()
        a["backtest_reference"]["r98"]["curve"].append(
            {"timestamp": B, "equity_multiple": 1.1})
        self.assertEqual(audit(a, extended())["status"], "DATA_ONLY_HOLD")

    def test_historical_rewrite(self):
        b = extended()
        b["backtest_reference"]["f1"]["curve"][0]["equity_multiple"] = 2
        self.assertIn("historical_backtest_or_metrics_changed",
                      audit(fixture(), b)["variants"]["f1"])

    def test_historical_roi_metadata_tamper(self):
        a, b = fixture(), extended()
        a["backtest_reference"]["f3"]["historicalRoiPct"] = 123
        b["backtest_reference"]["f3"]["historicalRoiPct"] = 999999
        self.assertIn("historical_backtest_or_metrics_changed",
                      audit(a, b)["variants"]["f3"])

    def test_rejected_status_relabel_tamper(self):
        a, b = fixture(), extended()
        a["variants"]["f1"]["status"] = "research_rejected"
        b["variants"]["f1"]["status"] = "champion"
        self.assertIn("variant_identity_or_status_changed",
                      audit(a, b)["variants"]["f1"])

    def test_operations_rewrite(self):
        b = extended()
        b["variants"]["f3"]["operations"][0]["action"] = "sell"
        self.assertIn("operations_prefix_rewritten",
                      audit(fixture(), b)["variants"]["f3"])

    def test_capped_operations(self):
        a, b = fixture(), extended()
        for item in (a, b):
            item["variants"]["f1"]["operations"] = [
                {"timestamp": H, "symbol": f"X{i:04d}"} for i in range(1500)]
        self.assertIn("operations_capped_unverifiable",
                      audit(a, b)["variants"]["f1"])

    def test_duplicate_operations(self):
        b = extended()
        b["variants"]["f1"]["operations"].append(
            copy.deepcopy(b["variants"]["f1"]["operations"][0]))
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_boundary_move(self):
        b = extended()
        b["paper_start_after_timestamp"] = H
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_real_orders(self):
        b = extended()
        b["real_orders_enabled"] = True
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_missing_variant(self):
        b = extended()
        del b["variants"]["f12"]
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_non_utc(self):
        b = extended()
        b["variants"]["f12"]["equity_curve"][1]["timestamp"] = "2026-09-16T14:00:00-03:00"
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_nonfinite_constant(self):
        with self.assertRaises(ValueError):
            strict_json('{"bad":NaN}')

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            strict_json('{"paper_start_after_timestamp":"valid","paper_start_after_timestamp":"altered"}')

    def test_nonfinite_exponent(self):
        with self.assertRaises(ValueError):
            strict_json('{"bad":1e999}')

    def test_stale_latest(self):
        b = extended()
        b["latest_data_timestamp"] = B
        with self.assertRaises(ValueError):
            audit(fixture(), b)

    def test_unordered_operations(self):
        b = extended()
        b["variants"]["f1"]["operations"].insert(0,
            {"timestamp": N, "symbol": "ETHUSDT"})
        with self.assertRaises(ValueError):
            audit(fixture(), b)


if __name__ == "__main__":
    unittest.main()
