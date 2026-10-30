from __future__ import annotations

import numpy as np
import pandas as pd
import pandas.testing as pdt

from cryptoai_v13.data import FuturesData
from cryptoai_v13.v99 import V99AsymmetricSpec
from cryptoai_v13.v99_r3 import V99R3ControlSpec, asymmetric_v99_targets_r3


def futures(close: pd.DataFrame) -> FuturesData:
    return FuturesData(
        frames={"close": close},
        funding=pd.DataFrame(0.0, index=close.index, columns=close.columns),
        symbols=tuple(close.columns),
    )


def run(close: pd.DataFrame, targets: pd.DataFrame):
    proxy = pd.Series(1.0, index=close.index)
    return asymmetric_v99_targets_r3(
        futures(close),
        targets,
        proxy,
        V99AsymmetricSpec(clean_trend_boost=1.10),
        V99R3ControlSpec(),
    )


def broad_market(index: pd.DatetimeIndex, final_multiplier: float) -> pd.DataFrame:
    base = np.full(len(index), 100.0)
    base[-25:] = np.linspace(100.0, 100.0 * final_multiplier, 25)
    return pd.DataFrame(
        {
            "BTCUSDT": base,
            "ETHUSDT": base * 1.01,
            "SOLUSDT": base * 0.99,
            "ADAUSDT": base * 1.02,
        },
        index=index,
    )


def test_r3_crash_cuts_longs_but_preserves_winning_shorts() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    close = broad_market(index, 0.88)
    targets = pd.DataFrame(0.0, index=index, columns=close.columns)
    targets["BTCUSDT"] = 0.45
    targets["ETHUSDT"] = 0.35
    targets["SOLUSDT"] = -0.35
    targets["ADAUSDT"] = -0.25

    transformed, diagnostics = run(close, targets)
    last = diagnostics.iloc[-1]

    assert float(last["long_stress_factor"]) < 1.0
    assert float(last["short_stress_factor"]) == 1.0
    assert float(transformed.iloc[-1]["BTCUSDT"]) < float(targets.iloc[-1]["BTCUSDT"])
    assert float(transformed.iloc[-1]["ETHUSDT"]) < float(targets.iloc[-1]["ETHUSDT"])
    assert abs(float(transformed.iloc[-1]["SOLUSDT"])) >= abs(float(targets.iloc[-1]["SOLUSDT"])) - 1e-9


def test_r3_upside_squeeze_cuts_shorts_but_preserves_winning_longs() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    close = broad_market(index, 1.12)
    targets = pd.DataFrame(0.0, index=index, columns=close.columns)
    targets["BTCUSDT"] = 0.40
    targets["ETHUSDT"] = 0.30
    targets["SOLUSDT"] = -0.40
    targets["ADAUSDT"] = -0.30

    transformed, diagnostics = run(close, targets)
    last = diagnostics.iloc[-1]

    assert float(last["short_stress_factor"]) < 1.0
    assert float(last["long_stress_factor"]) == 1.0
    assert abs(float(transformed.iloc[-1]["SOLUSDT"])) < abs(float(targets.iloc[-1]["SOLUSDT"]))
    assert float(transformed.iloc[-1]["BTCUSDT"]) >= float(targets.iloc[-1]["BTCUSDT"]) - 1e-9


def test_r3_side_shock_brakes_failing_book_without_btc_stress() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    btc = np.full(len(index), 100.0)
    alt = np.full(len(index), 100.0)
    alt[-4:] = [100.0, 98.5, 97.0, 95.0]
    close = pd.DataFrame(
        {
            "BTCUSDT": btc,
            "ETHUSDT": alt,
            "SOLUSDT": alt * 0.99,
            "ADAUSDT": alt * 1.01,
        },
        index=index,
    )
    targets = pd.DataFrame(0.0, index=index, columns=close.columns)
    targets["ETHUSDT"] = 0.35
    targets["SOLUSDT"] = 0.35
    targets["ADAUSDT"] = 0.35

    transformed, diagnostics = run(close, targets)
    last = diagnostics.iloc[-1]

    assert float(last["long_stress_factor"]) == 1.0
    assert float(last["long_damage_factor"]) < 1.0
    assert float(last["short_damage_factor"]) == 1.0
    assert float(transformed.iloc[-1].clip(lower=0.0).sum()) < float(targets.iloc[-1].clip(lower=0.0).sum())


def test_r3_is_causal_under_future_price_perturbation() -> None:
    index = pd.date_range("2026-01-01", periods=500, freq="h", tz="UTC")
    t = np.arange(len(index), dtype=float)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 * np.exp(0.0002 * t),
            "ETHUSDT": 90.0 * np.exp(0.00025 * t),
            "SOLUSDT": 80.0 * np.exp(-0.0001 * t),
        },
        index=index,
    )
    targets = pd.DataFrame(
        {"BTCUSDT": 0.4, "ETHUSDT": 0.3, "SOLUSDT": -0.25},
        index=index,
    )
    cutoff = index[400]

    baseline, _ = run(close, targets)
    perturbed = close.copy()
    perturbed.loc[perturbed.index > cutoff, "BTCUSDT"] *= 2.0
    perturbed.loc[perturbed.index > cutoff, "ETHUSDT"] *= 0.3
    changed, _ = run(perturbed, targets)

    pdt.assert_frame_equal(baseline.loc[:cutoff], changed.loc[:cutoff])


def test_r3_respects_maximum_gross() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    t = np.arange(len(index), dtype=float)
    trend = np.exp(0.0015 * t)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 * trend,
            "ETHUSDT": 90.0 * trend,
            "SOLUSDT": 80.0 * trend,
        },
        index=index,
    )
    targets = pd.DataFrame(0.8, index=index, columns=close.columns)
    spec = V99AsymmetricSpec(clean_trend_boost=1.20, maximum_gross=1.50)
    transformed, _ = asymmetric_v99_targets_r3(
        futures(close),
        targets,
        pd.Series(1.0, index=index),
        spec,
        V99R3ControlSpec(),
    )

    assert float(transformed.abs().sum(axis=1).max()) <= 1.50 + 1e-9
