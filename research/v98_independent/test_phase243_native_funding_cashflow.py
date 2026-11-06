"""V98 funding ledger deterministic contract tests (no PnL claims)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase243_native_funding_cashflow import settle, load_funding

class NativeFundingCashflowTests(unittest.TestCase):
    def test_signed_settlement_and_non_event(self):
        t = 8 * 3600000
        events = {"BTCUSDT": {t: 0.0001}, "ETHUSDT": {}, "BNBUSDT": {}, "SOLUSDT": {}}
        positions = [
            {"asset": "BTCUSDT", "hour_open_ms": t, "signed_notional_usd_before_hour": 10000},
            {"asset": "BTCUSDT", "hour_open_ms": t + 3600000, "signed_notional_usd_before_hour": -10000},
            {"asset": "ETHUSDT", "hour_open_ms": t, "signed_notional_usd_before_hour": -10000},
        ]
        result = settle(positions, events)
        self.assertAlmostEqual(result[0]["funding_cashflow_usd"], -1)
        self.assertEqual(result[1]["funding_cashflow_usd"], 0)
        self.assertEqual(result[2]["funding_cashflow_usd"], 0)

    def test_short_receives_positive_funding(self):
        t = 8 * 3600000
        events = {"BTCUSDT": {t: 0.0001}}
        row = {"asset": "BTCUSDT", "hour_open_ms": t, "signed_notional_usd_before_hour": -10000}
        self.assertAlmostEqual(settle([row], events)[0]["funding_cashflow_usd"], 1)

    def test_duplicate_inventory_rejected(self):
        row = {"asset": "BTCUSDT", "hour_open_ms": 0, "signed_notional_usd_before_hour": 100}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_POSITION_HOUR"):
            settle([row, row], {"BTCUSDT": {}})

    def test_invalid_notional_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_POSITION"):
            settle([{"asset": "BTCUSDT", "hour_open_ms": 0,
                     "signed_notional_usd_before_hour": float("nan")}], {"BTCUSDT": {}})

if __name__ == "__main__":
    unittest.main()
