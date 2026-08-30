from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.data import FuturesData
from cryptoai_v13.v16 import (
    AdaptiveTrendSpec,
    ConvexCaptureSpec,
    RegimeSwitchSpec,
    adaptive_equity_shield,
    adaptive_trend_targets,
    combine_convex_with_core,
    drawdown_regime_reentry_targets,
    regime_hedged_targets,
    regime_switch_targets,
    rolling_loss_limiter_targets,
)


class V16ResearchTests(unittest.TestCase):
    def test_configuration_rejects_invalid_weights(self) -> None:
        with self.assertRaises(ValueError):
            ConvexCaptureSpec(fast_weight=0.8, slow_weight=0.3, trend_weight=0.2)

    def test_allocator_respects_portfolio_gross_and_does_not_mutate_core(self) -> None:
        index = pd.date_range("2026-01-01", periods=4, freq="h", tz="UTC")
        core = pd.DataFrame({"BTCUSDT": [1.0] * 4, "ETHUSDT": [0.5] * 4}, index=index)
        opportunity = pd.DataFrame({"BTCUSDT": [2.0] * 4, "ETHUSDT": [-2.0] * 4}, index=index)
        original = core.copy()
        combined, allocated = combine_convex_with_core(
            core, opportunity, core_fraction=0.3, maximum_portfolio_gross=1.6
        )
        pd.testing.assert_frame_equal(core, original)
        self.assertTrue((combined.abs().sum(axis=1) <= 1.6 + 1e-12).all())
        self.assertTrue((allocated.abs().sum(axis=1) <= 1.15 + 1e-12).all())

    def test_v16_source_is_research_only_and_has_no_order_method(self) -> None:
        source = (PROJECT / "src" / "cryptoai_v13" / "v16.py").read_text()
        runner = (PROJECT / "scripts" / "search_v16.py").read_text()
        for forbidden in ("create_order", "create_market_order", "apiKey", "secret"):
            self.assertNotIn(forbidden, source)
            self.assertNotIn(forbidden, runner)
        self.assertIn("without_best_day_return", runner)
        self.assertIn("delay_3h", runner)
        self.assertIn("severe_cost", runner)

    def test_adaptive_shield_is_causal_and_caps_gross(self) -> None:
        index = pd.date_range("2026-01-01", periods=900, freq="h", tz="UTC")
        base = pd.DataFrame(
            {"BTCUSDT": 1.2, "ETHUSDT": -0.8}, index=index
        )
        equity = pd.Series(np.linspace(1.0, 1.5, len(index)), index=index)
        kwargs = dict(
            short_hours=48,
            long_hours=24 * 21,
            peak_hours=24 * 120,
            warning_drawdown=0.06,
            hard_drawdown=0.10,
            attack_multiplier=1.45,
            neutral_multiplier=0.70,
            weak_multiplier=0.25,
            hard_multiplier=0.05,
            shock_return=0.045,
            rebalance_hours=6,
            maximum_gross=1.85,
        )
        shielded, _ = adaptive_equity_shield(base, equity, **kwargs)
        changed = equity.copy()
        changed.iloc[-1] = changed.iloc[-1] * 0.5
        changed_targets, _ = adaptive_equity_shield(base, changed, **kwargs)
        pd.testing.assert_frame_equal(shielded.iloc[:-1], changed_targets.iloc[:-1])
        self.assertTrue((shielded.abs().sum(axis=1) <= 1.85 + 1e-12).all())

    def test_adaptive_trend_uses_no_future_and_caps_gross(self) -> None:
        index = pd.date_range("2025-12-01", periods=1600, freq="h", tz="UTC")
        symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT")
        base = np.arange(len(index), dtype=float)
        close = pd.DataFrame(
            {
                symbol: 100.0 * np.exp((0.0002 - rank * 0.00008) * base)
                for rank, symbol in enumerate(symbols)
            },
            index=index,
        )
        frames = {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.004,
            "low": close * 0.996,
            "close": close,
            "volume": pd.DataFrame(1_000.0, index=index, columns=symbols),
            "quote_volume": pd.DataFrame(1_000_000.0, index=index, columns=symbols),
            "trades": pd.DataFrame(100.0, index=index, columns=symbols),
        }
        data = FuturesData(
            frames=frames,
            funding=pd.DataFrame(0.0, index=index, columns=symbols),
            symbols=symbols,
        )
        spec = AdaptiveTrendSpec(
            long_candidates=4,
            short_candidates=4,
            long_count=2,
            short_count=2,
        )
        targets, _ = adaptive_trend_targets(data, spec)
        changed_frames = {key: value.copy() for key, value in frames.items()}
        changed_frames["close"].iloc[-1, 0] *= 0.5
        changed = FuturesData(
            frames=changed_frames,
            funding=data.funding,
            symbols=symbols,
        )
        changed_targets, _ = adaptive_trend_targets(changed, spec)
        pd.testing.assert_frame_equal(targets.iloc[:-1], changed_targets.iloc[:-1])
        self.assertTrue((targets.abs().sum(axis=1) <= spec.maximum_gross + 1e-12).all())

    def test_regime_switch_is_causal_and_caps_gross(self) -> None:
        index = pd.date_range("2025-01-01", periods=3000, freq="h", tz="UTC")
        base = np.arange(len(index), dtype=float)
        close = pd.DataFrame(
            {
                "BTCUSDT": 100.0 * np.exp(0.00015 * base),
                "ETHUSDT": 80.0 * np.exp(0.00010 * base),
                "SOLUSDT": 60.0 * np.exp(0.00005 * base),
            },
            index=index,
        )
        core = pd.DataFrame(0.5, index=index, columns=close.columns)
        attack = pd.DataFrame(1.0, index=index, columns=close.columns)
        spec = RegimeSwitchSpec()
        targets, _ = regime_switch_targets(core, attack, close, spec)
        changed = close.copy()
        changed.iloc[-1, 0] *= 0.5
        changed_targets, _ = regime_switch_targets(core, attack, changed, spec)
        pd.testing.assert_frame_equal(targets.iloc[:-1], changed_targets.iloc[:-1])
        self.assertTrue((targets.abs().sum(axis=1) <= spec.maximum_gross + 1e-12).all())

    def test_regime_reentry_shield_is_causal_and_caps_gross(self) -> None:
        index = pd.date_range("2025-01-01", periods=1200, freq="h", tz="UTC")
        equity = pd.Series(np.linspace(1.0, 1.4, len(index)), index=index)
        equity.iloc[700:800] *= np.linspace(1.0, 0.85, 100)
        regime = pd.Series("bull", index=index)
        targets = pd.DataFrame(
            {"BTCUSDT": 1.4, "ETHUSDT": 0.8}, index=index
        )
        kwargs = dict(
            drawdown_threshold=0.07,
            defensive_multiplier=0.20,
            reentry_return_hours=24 * 7,
            reentry_return=0.02,
            minimum_defensive_hours=24 * 5,
            rebalance_hours=24,
            maximum_gross=1.85,
        )
        shielded, _ = drawdown_regime_reentry_targets(
            targets, equity, regime, **kwargs
        )
        changed_equity = equity.copy()
        changed_equity.iloc[-1] *= 0.5
        changed, _ = drawdown_regime_reentry_targets(
            targets, changed_equity, regime, **kwargs
        )
        pd.testing.assert_frame_equal(shielded.iloc[:-1], changed.iloc[:-1])
        self.assertTrue((shielded.abs().sum(axis=1) <= 1.85 + 1e-12).all())

    def test_rolling_loss_limiter_is_causal_and_caps_gross(self) -> None:
        index = pd.date_range("2025-01-01", periods=900, freq="h", tz="UTC")
        equity = pd.Series(np.linspace(1.0, 1.3, len(index)), index=index)
        equity.iloc[500:550] *= np.linspace(1.0, 0.90, 50)
        targets = pd.DataFrame(
            {"BTCUSDT": 1.4, "ETHUSDT": 0.8}, index=index
        )
        kwargs = dict(
            short_hours=24,
            medium_hours=24 * 7,
            short_loss=0.04,
            medium_loss=0.09,
            short_multiplier=0.15,
            medium_multiplier=0.35,
            rebalance_hours=3,
            maximum_gross=1.85,
        )
        limited, _ = rolling_loss_limiter_targets(targets, equity, **kwargs)
        changed_equity = equity.copy()
        changed_equity.iloc[-1] *= 0.5
        changed, _ = rolling_loss_limiter_targets(
            targets, changed_equity, **kwargs
        )
        pd.testing.assert_frame_equal(limited.iloc[:-1], changed.iloc[:-1])
        self.assertTrue((limited.abs().sum(axis=1) <= 1.85 + 1e-12).all())

    def test_regime_hedge_is_causal_and_caps_gross(self) -> None:
        index = pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC")
        targets = pd.DataFrame(
            {"BTCUSDT": 1.0, "ETHUSDT": 0.6, "SOLUSDT": 0.2}, index=index
        )
        regime = pd.Series("bull", index=index)
        regime.iloc[30:60] = "neutral"
        regime.iloc[60:] = "bear"
        hedged, diagnostics = regime_hedged_targets(
            targets,
            regime,
            neutral_net_cap=0.75,
            bear_net_target=-0.35,
            maximum_gross=1.85,
        )
        changed = regime.copy()
        changed.iloc[-1] = "bull"
        changed_targets, _ = regime_hedged_targets(
            targets,
            changed,
            neutral_net_cap=0.75,
            bear_net_target=-0.35,
            maximum_gross=1.85,
        )
        pd.testing.assert_frame_equal(hedged.iloc[:-1], changed_targets.iloc[:-1])
        self.assertLess(float(diagnostics.loc[index[-2], "net"]), 0.0)
        self.assertTrue((hedged.abs().sum(axis=1) <= 1.85 + 1e-12).all())


if __name__ == "__main__":
    unittest.main()
