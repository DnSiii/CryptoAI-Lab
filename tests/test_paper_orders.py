from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v13 import build_ledger


class PaperOrderTests(unittest.TestCase):
    def test_exact_fast_records_the_order_that_really_executed(self) -> None:
        index = pd.date_range("2025-01-01", periods=5, freq="h", tz="UTC")
        opened = pd.DataFrame({"BTCUSDT": [100, 100, 110, 110, 110]}, index=index)
        closed = pd.DataFrame({"BTCUSDT": [100, 110, 110, 110, 110]}, index=index)
        zero = opened * 0.0
        data = FuturesData(
            {
                "open": opened,
                "high": np.maximum(opened, closed),
                "low": np.minimum(opened, closed),
                "close": closed,
                "volume": zero,
                "quote_volume": zero,
                "trades": zero,
            },
            zero,
            ("BTCUSDT",),
        )
        targets = pd.DataFrame(
            {"BTCUSDT": [-1.0, -1.0, -0.5, -0.5, -0.5]}, index=index
        )
        cost = 0.001
        result = exact_fast(data, targets, cost_per_side=cost)

        self.assertIsNotNone(result.asset_orders)
        self.assertIsNotNone(result.asset_order_notional)
        self.assertIsNotNone(result.asset_fees)
        assert result.asset_orders is not None
        assert result.asset_order_notional is not None
        assert result.asset_fees is not None
        self.assertLess(float(result.asset_orders.iloc[1, 0]), 0.0)
        self.assertGreater(float(result.asset_orders.iloc[3, 0]), 0.0)
        pd.testing.assert_series_equal(
            result.asset_fees.sum(axis=1),
            result.asset_order_notional.abs().sum(axis=1) * cost,
            check_names=False,
        )

    def test_ledger_reports_every_asset_that_was_traded(self) -> None:
        index = pd.date_range("2025-01-01", periods=5, freq="h", tz="UTC")
        opened = pd.DataFrame(
            {
                "BTCUSDT": [100, 101, 102, 103, 104],
                "ETHUSDT": [50, 51, 52, 53, 54],
                "BCHUSDT": [20, 20, 21, 22, 23],
            },
            index=index,
            dtype=float,
        )
        closed = opened * 1.001
        zero = opened * 0.0
        data = FuturesData(
            {
                "open": opened,
                "high": np.maximum(opened, closed),
                "low": np.minimum(opened, closed),
                "close": closed,
                "volume": zero,
                "quote_volume": zero,
                "trades": zero,
            },
            zero,
            tuple(opened.columns),
        )
        targets = pd.DataFrame(
            {
                "BTCUSDT": [0.2] * len(index),
                "ETHUSDT": [0.3] * len(index),
                "BCHUSDT": [0.4] * len(index),
            },
            index=index,
        )
        result = exact_fast(data, targets, cost_per_side=0.0007)
        ledger = build_ledger(data, targets, result, index[0], "test")

        self.assertEqual(ledger["schema_version"], 4)
        self.assertEqual(set(ledger["assets"]), set(opened.columns))
        self.assertEqual(set(ledger["candles"]), set(opened.columns))
        self.assertAlmostEqual(
            sum(item["net_result_brl"] for item in ledger["assets"].values()),
            ledger["summary"]["net_result_brl"],
            places=2,
        )


if __name__ == "__main__":
    unittest.main()
