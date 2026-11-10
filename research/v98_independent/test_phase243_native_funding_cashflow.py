"""V98 funding ledger deterministic contract tests (no PnL claims)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase243_native_funding_cashflow import settle, load_funding, validate_complete_inventory

class NativeFundingCashflowTests(unittest.TestCase):
    def test_subsecond_exchange_stamps_and_duplicate_rejection(self):
        import csv
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "BTCUSDT_native_funding.csv"
            def write(times):
                with p.open("w", newline="") as out:
                    w = csv.DictWriter(out, fieldnames=["funding_time_ms", "funding_rate"])
                    w.writeheader()
                    w.writerows({"funding_time_ms": t, "funding_rate": "0.0001"} for t in times)
            base = 1669852800000
            write([base + 1, base + 8 * 3600000 + 6, base + 16 * 3600000 + 999])
            self.assertEqual(list(load_funding(p)), [base, base + 8 * 3600000, base + 16 * 3600000])
            write([base, base + 999])
            with self.assertRaisesRegex(ValueError, "duplicate_normalized_settlement"):
                load_funding(p)
            write([base + 1000])
            with self.assertRaisesRegex(ValueError, "non_hour_boundary"):
                load_funding(p)

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


    def test_complete_inventory_and_missing_hour(self):
        assets = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
        rows = [{"asset": a, "hour_open_ms": t, "signed_notional_usd_before_hour": 0}
                for a in assets for t in (0, 3600000, 7200000)]
        funding = {a: {3600000: 0.0001} for a in assets}
        self.assertEqual(validate_complete_inventory(rows, funding)["hours_per_asset"], 3)
        with self.assertRaisesRegex(ValueError, "MISSING_POSITION_HOUR"):
            validate_complete_inventory([r for r in rows
                if not (r["asset"] == "BTCUSDT" and r["hour_open_ms"] == 3600000)], funding)

    def test_settlement_outside_inventory_rejected(self):
        assets = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
        rows = [{"asset": a, "hour_open_ms": t, "signed_notional_usd_before_hour": 0}
                for a in assets for t in (0, 3600000, 7200000)]
        funding = {a: {3600000: 0.0001} for a in assets}
        funding["BTCUSDT"][10800000] = 0.0001
        with self.assertRaisesRegex(ValueError, "SETTLEMENT_OUTSIDE_INVENTORY"):
            validate_complete_inventory(rows, funding)

    def test_asset_misalignment_and_future_rejected(self):
        assets = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
        funding = {a: {} for a in assets}
        rows = [{"asset": a, "hour_open_ms": 0, "signed_notional_usd_before_hour": 0}
                for a in assets]
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_CLEAN4_INVENTORY"):
            validate_complete_inventory(rows[:-1], funding)
        future = [{**r, "hour_open_ms": 1767225600000} for r in rows]
        with self.assertRaisesRegex(ValueError, "TRAINING_BOUNDARY_VIOLATION"):
            validate_complete_inventory(future, funding)

if __name__ == "__main__":
    unittest.main()
