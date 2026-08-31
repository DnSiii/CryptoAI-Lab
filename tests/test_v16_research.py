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
    CrossSectionalMomentumSpec,
    FundingCarrySpec,
    RegimeSwitchSpec,
    adaptive_equity_shield,
    adaptive_trend_targets,
    combine_convex_with_core,
    cross_sectional_momentum_targets,
    funding_carry_targets,
    performance_gated_alpha_targets,
    drawdown_regime_reentry_targets,
    protected_equity_reentry_targets,
    regime_hedged_targets,
    regime_switch_targets,
    rolling_loss_limiter_targets,
    three_regime_sleeve_targets,
    volatility_managed_targets,
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

    def test_protected_equity_reentry_is_causal_and_uses_managed_drawdown(self) -> None:
        index = pd.date_range("2026-01-01", periods=240, freq="h", tz="UTC")
        symbols = ("BTCUSDT", "ETHUSDT")
        hourly = np.zeros(len(index))
        hourly[50:70] = -0.004
        hourly[100:] = 0.001
        close = pd.DataFrame(
            {
                "BTCUSDT": 100.0 * np.cumprod(1.0 + hourly),
                "ETHUSDT": 80.0 * np.cumprod(1.0 + hourly * 0.8),
            },
            index=index,
        )
        frames = {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.002,
            "low": close * 0.998,
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
        targets = pd.DataFrame(
            {"BTCUSDT": 1.0, "ETHUSDT": 0.6}, index=index
        )
        confirmation = pd.Series(
            np.cumprod(1.0 + hourly), index=index
        )
        kwargs = dict(
            drawdown_threshold=0.05,
            minimum_multiplier=0.05,
            recovery_multiplier=0.75,
            confirmation_hours=24,
            confirmation_return=0.005,
            restore_drawdown=0.02,
            deep_drawdown=0.10,
            deep_recovery_multiplier=0.30,
            rebalance_hours=3,
            maximum_gross=1.85,
        )
        guarded, diagnostics = protected_equity_reentry_targets(
            data, targets, confirmation, **kwargs
        )
        changed_frames = {key: value.copy() for key, value in frames.items()}
        changed_frames["close"].iloc[-1, 0] *= 0.5
        changed_data = FuturesData(
            frames=changed_frames,
            funding=data.funding,
            symbols=symbols,
        )
        changed, _ = protected_equity_reentry_targets(
            changed_data, targets, confirmation, **kwargs
        )
        pd.testing.assert_frame_equal(guarded.iloc[:-1], changed.iloc[:-1])
        self.assertTrue((guarded.abs().sum(axis=1) <= 1.85 + 1e-12).all())
        self.assertTrue(diagnostics["risk_factor"].lt(1.0).any())

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

    def test_three_regime_sleeves_use_only_signal_shorts(self) -> None:
        index = pd.date_range("2025-01-01", periods=90, freq="h", tz="UTC")
        core = pd.DataFrame(
            {"BTCUSDT": 0.6, "ETHUSDT": 0.4}, index=index
        )
        attack = pd.DataFrame(
            {"BTCUSDT": 1.2, "ETHUSDT": 0.8}, index=index
        )
        raw = pd.DataFrame(
            {"BTCUSDT": -1.0, "ETHUSDT": 0.9}, index=index
        )
        regime = pd.Series("bull", index=index)
        regime.iloc[30:60] = "neutral"
        regime.iloc[60:] = "bear"
        targets, _ = three_regime_sleeve_targets(
            core,
            attack,
            raw,
            regime,
            bull_attack=1.0,
            bull_core=0.1,
            neutral_attack=0.7,
            neutral_core=0.45,
            bear_short=1.1,
            bear_core=0.0,
            maximum_gross=1.85,
        )
        self.assertLess(float(targets.loc[index[-1], "BTCUSDT"]), 0.0)
        self.assertEqual(float(targets.loc[index[-1], "ETHUSDT"]), 0.0)
        self.assertTrue((targets.abs().sum(axis=1) <= 1.85 + 1e-12).all())

    def test_volatility_manager_is_causal_and_caps_gross(self) -> None:
        index = pd.date_range("2025-01-01", periods=1200, freq="h", tz="UTC")
        returns = np.sin(np.arange(len(index)) / 20.0) * 0.003 + 0.0002
        equity = pd.Series(np.cumprod(1.0 + returns), index=index)
        regime = pd.Series("bull", index=index)
        targets = pd.DataFrame(
            {"BTCUSDT": 1.4, "ETHUSDT": 0.8}, index=index
        )
        kwargs = dict(
            volatility_hours=24 * 14,
            annual_volatility_target=0.80,
            minimum_multiplier=0.20,
            bull_maximum_multiplier=1.10,
            neutral_maximum_multiplier=0.80,
            bear_maximum_multiplier=0.40,
            one_day_shock=0.05,
            shock_multiplier=0.15,
            rebalance_hours=6,
            maximum_gross=2.00,
        )
        managed, _ = volatility_managed_targets(
            targets, equity, regime, **kwargs
        )
        changed_equity = equity.copy()
        changed_equity.iloc[-1] *= 0.5
        changed, _ = volatility_managed_targets(
            targets, changed_equity, regime, **kwargs
        )
        pd.testing.assert_frame_equal(managed.iloc[:-1], changed.iloc[:-1])
        self.assertTrue((managed.abs().sum(axis=1) <= 2.0 + 1e-12).all())

    def test_cross_sectional_momentum_is_causal_market_neutral_and_capped(self) -> None:
        index = pd.date_range("2025-01-01", periods=1200, freq="h", tz="UTC")
        base = np.arange(len(index), dtype=float)
        symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "BNBUSDT")
        close = pd.DataFrame(
            {
                symbol: 100.0 * np.exp((rank - 2.5) * 0.00008 * base)
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
        spec = CrossSectionalMomentumSpec(
            lookback_hours=72,
            volatility_hours=168,
            rebalance_hours=6,
            long_count=2,
            short_count=2,
            minimum_momentum=0.01,
        )
        targets, _ = cross_sectional_momentum_targets(data, spec)
        changed_frames = {key: value.copy() for key, value in frames.items()}
        changed_frames["close"].iloc[-1, 0] *= 0.5
        changed = FuturesData(
            frames=changed_frames,
            funding=data.funding,
            symbols=symbols,
        )
        changed_targets, _ = cross_sectional_momentum_targets(changed, spec)
        pd.testing.assert_frame_equal(targets.iloc[:-1], changed_targets.iloc[:-1])
        self.assertTrue((targets.abs().sum(axis=1) <= 1.85 + 1e-12).all())
        active = targets.abs().sum(axis=1) > 0.0
        self.assertTrue((targets.loc[active].sum(axis=1).abs() < 1e-10).all())

    def test_cross_sectional_reversal_flips_relative_selection(self) -> None:
        index = pd.date_range("2026-01-01", periods=240, freq="h", tz="UTC")
        base = np.arange(len(index), dtype=float)
        symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "BNBUSDT")
        close = pd.DataFrame(
            {
                symbol: 100.0 * np.exp((rank - 2.5) * 0.0005 * base)
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
        momentum, _ = cross_sectional_momentum_targets(
            data,
            CrossSectionalMomentumSpec(
                lookback_hours=24,
                volatility_hours=48,
                rebalance_hours=3,
                long_count=2,
                short_count=2,
                minimum_momentum=0.005,
            ),
        )
        reversal, _ = cross_sectional_momentum_targets(
            data,
            CrossSectionalMomentumSpec(
                lookback_hours=24,
                volatility_hours=48,
                rebalance_hours=3,
                long_count=2,
                short_count=2,
                minimum_momentum=0.005,
                direction="reversal",
            ),
        )
        active = momentum.abs().sum(axis=1) > 0.0
        pd.testing.assert_frame_equal(
            reversal.loc[active], -momentum.loc[active]
        )
        self.assertTrue((reversal.abs().sum(axis=1) <= 1.85 + 1e-12).all())

    def test_funding_carry_is_causal_neutral_and_receives_funding(self) -> None:
        index = pd.date_range("2026-01-01", periods=360, freq="h", tz="UTC")
        symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "BNBUSDT")
        base = np.arange(len(index), dtype=float)
        close = pd.DataFrame(
            {
                symbol: 100.0 * np.exp(0.00002 * base + 0.002 * np.sin(base / (12 + rank)))
                for rank, symbol in enumerate(symbols)
            },
            index=index,
        )
        funding = pd.DataFrame(
            {
                symbol: np.full(len(index), (rank - 2.5) * 0.00002)
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
        data = FuturesData(frames=frames, funding=funding, symbols=symbols)
        spec = FundingCarrySpec(
            funding_lookback_hours=48,
            volatility_hours=72,
            trend_hours=24,
            rebalance_hours=8,
            long_count=2,
            short_count=2,
            minimum_absolute_funding=0.0005,
        )
        targets, _ = funding_carry_targets(data, spec)
        active = targets.abs().sum(axis=1) > 0.0
        self.assertTrue((targets.loc[active].sum(axis=1).abs() < 1e-10).all())
        self.assertGreater(float(targets.loc[active, "BTCUSDT"].mean()), 0.0)
        self.assertLess(float(targets.loc[active, "BNBUSDT"].mean()), 0.0)
        pressure, _ = funding_carry_targets(
            data,
            FundingCarrySpec(
                funding_lookback_hours=48,
                volatility_hours=72,
                trend_hours=24,
                rebalance_hours=8,
                long_count=2,
                short_count=2,
                minimum_absolute_funding=0.0005,
                signal_mode="pressure_momentum",
            ),
        )
        pressure_active = pressure.abs().sum(axis=1) > 0.0
        self.assertLess(float(pressure.loc[pressure_active, "BTCUSDT"].mean()), 0.0)
        self.assertGreater(float(pressure.loc[pressure_active, "BNBUSDT"].mean()), 0.0)
        changed_funding = funding.copy()
        changed_funding.iloc[-1, 0] = 1.0
        changed = FuturesData(frames=frames, funding=changed_funding, symbols=symbols)
        changed_targets, _ = funding_carry_targets(changed, spec)
        pd.testing.assert_frame_equal(targets.iloc[:-1], changed_targets.iloc[:-1])
        self.assertTrue((targets.abs().sum(axis=1) <= spec.maximum_gross + 1e-12).all())

    def test_performance_gated_alpha_is_causal_and_capped(self) -> None:
        index = pd.date_range("2025-01-01", periods=1200, freq="h", tz="UTC")
        base = pd.DataFrame({"BTCUSDT": 1.4, "ETHUSDT": 0.4}, index=index)
        alpha = pd.DataFrame({"BTCUSDT": -0.6, "ETHUSDT": 0.6}, index=index)
        returns = np.sin(np.arange(len(index)) / 45.0) * 0.002 + 0.0001
        equity = pd.Series(np.cumprod(1.0 + returns), index=index)
        kwargs = dict(
            short_hours=24 * 7,
            long_hours=24 * 21,
            peak_hours=24 * 30,
            warning_drawdown=0.08,
            hard_drawdown=0.14,
            strong_base_multiplier=1.10,
            normal_base_multiplier=0.90,
            weak_base_multiplier=0.60,
            hard_base_multiplier=0.20,
            strong_alpha_multiplier=0.55,
            normal_alpha_multiplier=0.20,
            rebalance_hours=6,
            maximum_gross=1.95,
        )
        targets, _ = performance_gated_alpha_targets(
            base, alpha, equity, **kwargs
        )
        changed_equity = equity.copy()
        changed_equity.iloc[-1] *= 0.5
        changed, _ = performance_gated_alpha_targets(
            base, alpha, changed_equity, **kwargs
        )
        pd.testing.assert_frame_equal(targets.iloc[:-1], changed.iloc[:-1])
        self.assertTrue((targets.abs().sum(axis=1) <= 1.95 + 1e-12).all())


if __name__ == "__main__":
    unittest.main()
