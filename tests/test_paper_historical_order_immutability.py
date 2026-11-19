"""Adversarial historical paper immutability tests; no exchange orders."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paper_once_v13 import assert_historical_orders_unchanged


def ledger(value=7.71, raw=7.7148819, timestamp="2026-11-04T19:00:00+00:00"):
    return {"decisions": [{"timestamp": timestamp, "adjustments": [{
        "symbol": "ETHUSDT", "order_side": "buy", "action_code": "increase_long",
        "order_value_brl": value, "order_value_brl_unrounded": raw,
        "previous_weight": 0.1, "new_weight": 0.2, "execution_price": 3000.0
    }]}]}


class HistoricalOrderTests(unittest.TestCase):
    def test_identical(self):
        assert_historical_orders_unchanged(ledger(), ledger())

    def test_append_only(self):
        new = ledger()
        new["decisions"].append(ledger(timestamp="2026-11-04T20:00:00+00:00")["decisions"][0])
        assert_historical_orders_unchanged(ledger(), new)

    def test_reject_changed_displayed_notional(self):
        with self.assertRaisesRegex(RuntimeError, "historical order drift"):
            assert_historical_orders_unchanged(ledger(), ledger(value=7.72))

    def test_reject_changed_raw_notional(self):
        with self.assertRaisesRegex(RuntimeError, "historical raw notional drift"):
            assert_historical_orders_unchanged(ledger(), ledger(raw=7.7148818))

    def test_reject_deleted_order(self):
        with self.assertRaisesRegex(RuntimeError, "disappeared"):
            assert_historical_orders_unchanged(ledger(), {"decisions": []})

    def test_allow_legacy_missing_raw_without_fabrication(self):
        old = ledger()
        del old["decisions"][0]["adjustments"][0]["order_value_brl_unrounded"]
        assert_historical_orders_unchanged(old, ledger())

    def test_reject_duplicate_orders(self):
        new = ledger()
        new["decisions"].append(new["decisions"][0].copy())
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            assert_historical_orders_unchanged(ledger(), new)


if __name__ == "__main__":
    unittest.main()
