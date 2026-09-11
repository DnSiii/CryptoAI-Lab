from __future__ import annotations

import numpy as np
import pandas as pd

from cryptoai_v13.v99_r65 import (
    V99R65Spec,
    all_regime_targets,
    causal_regimes,
    lateral_mean_reversion_sleeve,
)


def _index(hours: int = 2400) -> pd.DatetimeIndex:
    return pd.date_range("2025-01-01", periods=hours, freq="h", tz="UTC")


def _trend_close(sign: float, hours: int = 2400) -> pd.DataFrame:
    idx = _index(hours)
    assets = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    data = {}
    for j, symbol in enumerate(assets):
        step = sign * (0.0008 + j * 0.00005)
        data[symbol] = 100.0 * np.exp(np.arange(hours) * step)
    return pd.DataFrame(data, index=idx)


def test_bull_regime_boosts_aligned_long_and_adds_market_overlay():
    close = _trend_close(1.0)
    targets = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    targets["ETHUSDT"] = 0.40
    targets["SOLUSDT"] = -0.20
    spec = V99R65Spec(maximum_gross=3.0, aligned_trend_boost=1.20, bull_market_overlay=0.15)
    transformed, diag = all_regime_targets(close, targets, spec)
    bull_rows = diag.index[diag["bull"]]
    assert len(bull_rows) > 24
    row = bull_rows[-1]
    assert transformed.loc[row, "ETHUSDT"] > targets.loc[row, "ETHUSDT"]
    assert transformed.loc[row, "SOLUSDT"] == targets.loc[row, "SOLUSDT"]
    assert transformed.loc[row, "BTCUSDT"] > 0.0


def test_bear_regime_boosts_aligned_short_and_adds_short_market_overlay():
    close = _trend_close(-1.0)
    targets = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    targets["ETHUSDT"] = -0.40
    targets["SOLUSDT"] = 0.20
    spec = V99R65Spec(maximum_gross=3.0, aligned_trend_boost=1.20, bear_market_overlay=0.20)
    transformed, diag = all_regime_targets(close, targets, spec)
    bear_rows = diag.index[diag["bear"]]
    assert len(bear_rows) > 24
    row = bear_rows[-1]
    assert transformed.loc[row, "ETHUSDT"] < targets.loc[row, "ETHUSDT"]
    assert transformed.loc[row, "SOLUSDT"] == targets.loc[row, "SOLUSDT"]
    assert transformed.loc[row, "BTCUSDT"] < 0.0


def test_lateral_sleeve_is_market_neutral_and_respects_budget():
    idx = _index(120)
    x = np.arange(len(idx), dtype=float)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 + 0.5 * np.sin(x / 3.0),
            "ETHUSDT": 100.0 + 2.0 * np.sin(x / 4.0),
            "SOLUSDT": 100.0 - 2.2 * np.sin(x / 4.0),
            "BNBUSDT": 100.0 + 1.4 * np.cos(x / 5.0),
        },
        index=idx,
    )
    regime = pd.DataFrame(
        {
            "lateral": True,
        },
        index=idx,
    )
    spec = V99R65Spec(lateral_gross=0.30, lateral_min_dispersion=0.0001)
    sleeve = lateral_mean_reversion_sleeve(close, regime, spec)
    active = sleeve.abs().sum(axis=1) > 1e-9
    assert active.any()
    assert (sleeve.loc[active].sum(axis=1).abs() < 1e-10).all()
    assert (sleeve.loc[active].abs().sum(axis=1) <= 0.3000000001).all()


def test_r65_never_exceeds_maximum_gross():
    close = _trend_close(1.0)
    targets = pd.DataFrame(0.70, index=close.index, columns=close.columns)
    spec = V99R65Spec(maximum_gross=1.90, aligned_trend_boost=1.40, bull_market_overlay=0.30)
    transformed, _ = all_regime_targets(close, targets, spec)
    assert transformed.abs().sum(axis=1).max() <= 1.9000000001


def test_regime_and_targets_are_causal_with_respect_to_future_prices():
    rng = np.random.default_rng(99)
    idx = _index(1800)
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    returns = rng.normal(0.0, 0.002, size=(len(idx), len(symbols)))
    close = pd.DataFrame(100.0 * np.exp(np.cumsum(returns, axis=0)), index=idx, columns=symbols)
    targets = pd.DataFrame(rng.uniform(-0.30, 0.30, size=close.shape), index=idx, columns=symbols)
    spec = V99R65Spec()

    cut = 1200
    first_targets, first_diag = all_regime_targets(close, targets, spec)
    changed = close.copy()
    changed.iloc[cut + 1 :] *= np.linspace(1.0, 3.0, len(changed) - cut - 1)[:, None]
    second_targets, second_diag = all_regime_targets(changed, targets, spec)

    pd.testing.assert_frame_equal(first_targets.iloc[: cut + 1], second_targets.iloc[: cut + 1])
    pd.testing.assert_frame_equal(first_diag.iloc[: cut + 1], second_diag.iloc[: cut + 1])


def test_causal_regimes_produce_mutually_exclusive_primary_states():
    close = _trend_close(1.0)
    diag = causal_regimes(close, V99R65Spec())
    primary = diag[["bull", "bear", "lateral"]].astype(int).sum(axis=1)
    assert primary.max() <= 1
