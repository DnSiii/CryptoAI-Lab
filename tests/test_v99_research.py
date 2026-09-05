from __future__ import annotations

import numpy as np
import pandas as pd

from cryptoai_v13.data import FuturesData
from cryptoai_v13.v99 import V99AsymmetricSpec
from cryptoai_v13.v99_r2 import V99R2ControlSpec, asymmetric_v99_targets_r2


def futures(close: pd.DataFrame) -> FuturesData:
    return FuturesData(
        frames={"close": close},
        funding=pd.DataFrame(0.0, index=close.index, columns=close.columns),
        symbols=tuple(close.columns),
    )


def flat_targets(close: pd.DataFrame, gross: float = 1.2) -> pd.DataFrame:
    weight = gross / len(close.columns)
    return pd.DataFrame(weight, index=close.index, columns=close.columns)


def run(close: pd.DataFrame, targets: pd.DataFrame, proxy: pd.Series | None = None):
    if proxy is None:
        proxy = pd.Series(1.0, index=close.index)
    return asymmetric_v99_targets_r2(
        futures(close),
        targets,
        proxy,
        V99AsymmetricSpec(),
        V99R2ControlSpec(),
    )


def test_v99_r2_cuts_confirmed_broad_market_stress_quickly() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    base = np.full(len(index), 100.0)
    base[-25:] = np.linspace(100.0, 88.0, 25)
    close = pd.DataFrame(
        {
            "BTCUSDT": base,
            "ETHUSDT": base * 1.01,
            "SOLUSDT": base * 0.99,
        },
        index=index,
    )
    targets = flat_targets(close)

    transformed, diagnostics = run(close, targets)

    assert int(diagnostics.iloc[-1]["stress_score"]) >= 1
    assert bool(diagnostics.iloc[-1]["stress_confirmed"])
    assert float(diagnostics.iloc[-1]["risk_factor"]) < 1.0
    assert float(transformed.iloc[-1].abs().sum()) < float(targets.iloc[-1].abs().sum())


def test_v99_r2_weak_breadth_alone_does_not_cut_existing_gross() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    t = np.arange(len(index), dtype=float)
    btc = 100.0 * np.exp(0.00001 * t)
    falling = 100.0 * np.exp(-0.0005 * t)
    close = pd.DataFrame(
        {
            "BTCUSDT": btc,
            "ETHUSDT": falling,
            "SOLUSDT": falling * 0.95,
            "ADAUSDT": falling * 0.90,
        },
        index=index,
    )
    targets = flat_targets(close)

    transformed, diagnostics = run(close, targets)

    assert float(diagnostics.iloc[-1]["stress_breadth"]) <= 0.30
    assert not bool(diagnostics.iloc[-1]["stress_confirmed"])
    assert float(diagnostics.iloc[-1]["stress_factor"]) == 1.0
    assert float(diagnostics.iloc[-1]["risk_factor"]) == 1.0
    assert float(transformed.iloc[-1].abs().sum()) >= 0.99 * float(
        targets.iloc[-1].abs().sum()
    )


def test_v99_r2_chop_blocks_growth_instead_of_resizing_existing_positions() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    t = np.arange(len(index), dtype=float)
    oscillation = 1.0 + 0.012 * np.sin(2.0 * np.pi * t / 6.0)
    tiny_up = np.exp(0.00001 * t)
    tiny_down = np.exp(-0.00001 * t)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 * oscillation * tiny_up,
            "ETHUSDT": 90.0 * oscillation * tiny_up,
            "SOLUSDT": 80.0 * oscillation * tiny_down,
            "ADAUSDT": 70.0 * oscillation * tiny_down,
        },
        index=index,
    )
    targets = flat_targets(close, gross=0.8)
    targets.iloc[-1] = 0.35

    transformed, diagnostics = run(close, targets)

    recent = diagnostics.tail(48)
    assert bool(recent["chop_active"].any())
    assert float(recent.loc[recent["chop_active"], "risk_factor"].min()) == 1.0
    if bool(diagnostics.iloc[-1]["chop_active"]):
        assert int(diagnostics.iloc[-1]["chop_blocked_count"]) >= 1
        assert float(transformed.iloc[-1].abs().sum()) < float(targets.iloc[-1].abs().sum())


def test_v99_r2_blocks_only_growth_into_an_exhausted_move() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    btc = np.full(len(index), 100.0)
    alt_returns = np.zeros(len(index))
    alt_returns[-48:] = 0.008 + 0.0004 * np.sin(np.arange(48))
    alt = 100.0 * np.cumprod(1.0 + alt_returns)
    close = pd.DataFrame({"BTCUSDT": btc, "ALTUSDT": alt}, index=index)
    targets = pd.DataFrame(0.0, index=index, columns=close.columns)
    targets["ALTUSDT"] = 0.20
    targets.iloc[-1, targets.columns.get_loc("ALTUSDT")] = 0.80

    transformed, diagnostics = run(close, targets)

    assert int(diagnostics.iloc[-1]["extension_blocked_count"]) >= 1
    assert abs(float(transformed.iloc[-1]["ALTUSDT"])) <= 0.20 + 1e-9
    assert abs(float(transformed.iloc[-2]["ALTUSDT"])) > 0.0


def test_v99_r2_reaccelerates_and_boosts_only_aligned_side_in_clean_trend() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    t = np.arange(len(index), dtype=float)
    trend = np.exp(0.0015 * t)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 * trend,
            "ETHUSDT": 90.0 * trend,
            "SOLUSDT": 80.0 * trend,
            "ADAUSDT": 70.0 * trend,
        },
        index=index,
    )
    targets = pd.DataFrame(0.0, index=index, columns=close.columns)
    targets["BTCUSDT"] = 0.40
    targets["ETHUSDT"] = 0.30
    targets["SOLUSDT"] = -0.20
    proxy = pd.Series(np.exp(0.0005 * t), index=index)

    transformed, diagnostics = run(close, targets, proxy)

    assert bool(diagnostics.iloc[-1]["clean_uptrend"])
    assert float(diagnostics.iloc[-1]["risk_factor"]) == 1.0
    assert bool(diagnostics.iloc[-1]["boost_ready"])
    assert float(transformed.iloc[-1]["BTCUSDT"]) > float(targets.iloc[-1]["BTCUSDT"])
    assert float(transformed.iloc[-1]["ETHUSDT"]) > float(targets.iloc[-1]["ETHUSDT"])
    assert float(transformed.iloc[-1]["SOLUSDT"]) == float(targets.iloc[-1]["SOLUSDT"])
