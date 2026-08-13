from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.allocator import (convex_equity_overlay,
                                    multihorizon_two_sleeve_targets,
                                    trailing_stop_overlay)
from cryptoai_v13.data import FuturesData, point_in_time_liquid_view


def market(opens, closes, highs=None, lows=None, funding=None) -> FuturesData:
    index = pd.date_range("2025-01-01", periods=len(opens), freq="h", tz="UTC")
    o = pd.DataFrame({"BTCUSDT": opens}, index=index, dtype=float)
    c = pd.DataFrame({"BTCUSDT": closes}, index=index, dtype=float)
    h = pd.DataFrame({"BTCUSDT": highs if highs is not None else np.maximum(opens, closes)}, index=index, dtype=float)
    l = pd.DataFrame({"BTCUSDT": lows if lows is not None else np.minimum(opens, closes)}, index=index, dtype=float)
    zero = o * 0.0
    frames = {"open": o, "high": h, "low": l, "close": c,
              "volume": zero, "quote_volume": zero, "trades": zero}
    f = pd.DataFrame({"BTCUSDT": funding or [0.0] * len(opens)}, index=index)
    return FuturesData(frames, f, ("BTCUSDT",))


class EngineTests(unittest.TestCase):
    def test_signal_cannot_capture_next_open_gap(self):
        data = market([100, 200, 200], [100, 200, 220])
        targets = pd.DataFrame({"BTCUSDT": [1.0, 1.0, 1.0]}, index=data.close.index)
        result = exact(data, targets, cost_per_side=0.0)
        self.assertAlmostEqual(float(result.equity.iloc[1]), 1.0)
        self.assertAlmostEqual(float(result.equity.iloc[2]), 1.1)

    def test_short_position_profits_from_decline(self):
        data = market([100, 100, 100], [100, 100, 90])
        targets = pd.DataFrame({"BTCUSDT": [-1.0, -1.0, -1.0]}, index=data.close.index)
        result = exact(data, targets, cost_per_side=0.0)
        self.assertAlmostEqual(float(result.equity.iloc[-1]), 1.1)

    def test_positive_funding_is_paid_by_long(self):
        data = market([100, 100, 100, 100], [100, 100, 100, 100], funding=[0, 0, 0.01, 0])
        targets = pd.DataFrame({"BTCUSDT": [1.0, 1.0, 1.0, 1.0]}, index=data.close.index)
        result = exact(data, targets, cost_per_side=0.0)
        self.assertAlmostEqual(float(result.equity.iloc[-1]), 0.99)

    def test_intrabar_adverse_extreme_can_trigger_ruin(self):
        data = market([100, 100, 100], [100, 100, 100], highs=[100, 100, 100], lows=[100, 100, 60])
        targets = pd.DataFrame({"BTCUSDT": [3.0, 3.0, 3.0]}, index=data.close.index)
        result = exact(data, targets, cost_per_side=0.0)
        self.assertTrue(result.ruin)
        self.assertEqual(float(result.equity.iloc[-1]), 0.0)

    def test_screen_and_exact_match_without_drift_or_cost(self):
        data = market([100, 100, 100, 100], [100, 100, 110, 110])
        targets = pd.DataFrame({"BTCUSDT": [1.0, 1.0, 0.0, 0.0]}, index=data.close.index)
        fast = screen(data, targets, cost_per_side=0.0)
        rigorous = exact(data, targets, cost_per_side=0.0)
        self.assertAlmostEqual(float(fast.equity.iloc[-1]), float(rigorous.equity.iloc[-1]))

    def test_constant_target_is_not_rebalanced_every_hour(self):
        data = market([100, 100, 105, 110], [100, 105, 110, 115])
        targets = pd.DataFrame({"BTCUSDT": [1.0, 1.0, 1.0, 1.0]}, index=data.close.index)
        result = exact(data, targets, cost_per_side=0.001)
        self.assertEqual(int((result.turnover > 0).sum()), 1)

    def test_allocator_does_not_use_future_returns(self):
        index = pd.date_range("2025-01-01", periods=400, freq="h", tz="UTC")
        fund_targets = pd.DataFrame({"BTCUSDT": 1.0}, index=index)
        regime_targets = pd.DataFrame({"BTCUSDT": -1.0}, index=index)
        fund_returns = pd.Series(0.001, index=index)
        regime_returns = pd.Series(0.0, index=index)
        original = multihorizon_two_sleeve_targets(
            fund_targets, regime_targets, fund_returns, regime_returns,
            windows_days=(2,), rebalance_hours=24)
        changed = fund_returns.copy()
        changed.iloc[300:] = -0.5
        perturbed = multihorizon_two_sleeve_targets(
            fund_targets, regime_targets, changed, regime_returns,
            windows_days=(2,), rebalance_hours=24)
        pd.testing.assert_frame_equal(original.iloc[:300], perturbed.iloc[:300])

    def test_liquidity_membership_does_not_use_current_or_future_volume(self):
        index = pd.date_range("2025-01-01", periods=200, freq="h", tz="UTC")
        close = pd.DataFrame({"A": 1.0, "B": 1.0}, index=index)
        frames = {
            field: close.copy()
            for field in ("open", "high", "low", "close", "volume", "trades")
        }
        frames["quote_volume"] = pd.DataFrame({"A": 100.0, "B": 10.0}, index=index)
        funding = close * 0.0
        base = FuturesData(frames, funding, ("A", "B"))
        _, before = point_in_time_liquid_view(
            base, top_n=1, lookback_hours=48, minimum_history_hours=48)
        changed_frames = dict(frames)
        changed_volume = frames["quote_volume"].copy()
        cutoff = index[120]
        changed_volume.loc[cutoff:, "B"] = 1e12
        changed_frames["quote_volume"] = changed_volume
        changed = FuturesData(changed_frames, funding, ("A", "B"))
        _, after = point_in_time_liquid_view(
            changed, top_n=1, lookback_hours=48, minimum_history_hours=48)
        pd.testing.assert_frame_equal(before.loc[:cutoff], after.loc[:cutoff])

    def test_convex_overlay_does_not_use_future_equity(self):
        index = pd.date_range("2025-01-01", periods=500, freq="h", tz="UTC")
        targets = pd.DataFrame({"BTCUSDT": 1.0}, index=index)
        equity = pd.Series(np.linspace(1.0, 2.0, len(index)), index=index)
        kwargs = dict(short_hours=48, long_hours=120, drawdown_hours=168,
                      drawdown_threshold=0.10, winner_multiplier=1.2,
                      loser_multiplier=0.5, drawdown_multiplier=0.25)
        original = convex_equity_overlay(targets, equity, **kwargs)
        changed = equity.copy()
        changed.iloc[350:] = 0.1
        perturbed = convex_equity_overlay(targets, changed, **kwargs)
        pd.testing.assert_frame_equal(original.iloc[:350], perturbed.iloc[:350])

    def test_trailing_stop_does_not_use_future_prices(self):
        index = pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC")
        targets = pd.DataFrame({"BTCUSDT": 1.0}, index=index)
        close = pd.DataFrame({"BTCUSDT": np.linspace(100.0, 120.0, 100)}, index=index)
        original = trailing_stop_overlay(targets, close, 0.08, 24)
        changed = close.copy()
        changed.iloc[70:] = 1.0
        perturbed = trailing_stop_overlay(targets, changed, 0.08, 24)
        pd.testing.assert_frame_equal(original.iloc[:70], perturbed.iloc[:70])


if __name__ == "__main__":
    unittest.main()
