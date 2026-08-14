from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData


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


if __name__ == "__main__":
    unittest.main()
