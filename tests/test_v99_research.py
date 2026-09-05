from __future__ import annotations

import numpy as np
import pandas as pd

from cryptoai_v13.data import FuturesData
from cryptoai_v13.v99 import V99AsymmetricSpec, asymmetric_v99_targets


def futures(close: pd.DataFrame) -> FuturesData:
    return FuturesData(
        frames={"close": close},
        funding=pd.DataFrame(0.0, index=close.index, columns=close.columns),
        symbols=tuple(close.columns),
    )


def flat_targets(close: pd.DataFrame, gross: float = 1.2) -> pd.DataFrame:
    weight = gross / len(close.columns)
    return pd.DataFrame(weight, index=close.index, columns=close.columns)


def test_v99_cuts_broad_market_stress_quickly() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    base = np.full(len(index), 100.0)
    crash = np.linspace(100.0, 88.0, 25)
    base[-25:] = crash
    close = pd.DataFrame(
        {
            "BTCUSDT": base,
            "ETHUSDT": base * 1.01,
            "SOLUSDT": base * 0.99,
        },
        index=index,
    )
    targets = flat_targets(close)
    proxy = pd.Series(1.0, index=index)

    transformed, diagnostics = asymmetric_v99_targets(
        futures(close), targets, proxy, V99AsymmetricSpec()
    )

    assert int(diagnostics.iloc[-1]["stress_score"]) >= 2
    assert float(diagnostics.iloc[-1]["risk_factor"]) < 1.0
    assert float(transformed.iloc[-1].abs().sum()) < float(targets.iloc[-1].abs().sum())


def test_v99_detects_directionless_chop_without_a_crash() -> None:
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
    targets = flat_targets(close)
    proxy = pd.Series(1.0, index=index)

    _, diagnostics = asymmetric_v99_targets(
        futures(close), targets, proxy, V99AsymmetricSpec()
    )

    recent = diagnostics.tail(48)
    assert bool(recent["chop_active"].any())
    assert float(recent.loc[recent["chop_active"], "risk_factor"].min()) <= 0.65


def test_v99_blocks_only_growth_into_an_exhausted_move() -> None:
    index = pd.date_range("2026-01-01", periods=420, freq="h", tz="UTC")
    btc = np.full(len(index), 100.0)
    alt_returns = np.zeros(len(index))
    alt_returns[-48:] = 0.008 + 0.0004 * np.sin(np.arange(48))
    alt = 100.0 * np.cumprod(1.0 + alt_returns)
    close = pd.DataFrame({"BTCUSDT": btc, "ALTUSDT": alt}, index=index)
    targets = pd.DataFrame(0.0, index=index, columns=close.columns)
    targets["ALTUSDT"] = 0.20
    targets.iloc[-1, targets.columns.get_loc("ALTUSDT")] = 0.80
    proxy = pd.Series(1.0, index=index)

    transformed, diagnostics = asymmetric_v99_targets(
        futures(close), targets, proxy, V99AsymmetricSpec()
    )

    assert int(diagnostics.iloc[-1]["extension_blocked_count"]) >= 1
    assert abs(float(transformed.iloc[-1]["ALTUSDT"])) <= 0.20 + 1e-9
    assert abs(float(transformed.iloc[-2]["ALTUSDT"])) > 0.0


def test_v99_reaccelerates_in_a_clean_broad_trend() -> None:
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
    targets = flat_targets(close, gross=1.0)
    proxy = pd.Series(np.exp(0.0005 * t), index=index)

    transformed, diagnostics = asymmetric_v99_targets(
        futures(close), targets, proxy, V99AsymmetricSpec()
    )

    assert bool(diagnostics.iloc[-1]["clean_trend"])
    assert float(diagnostics.iloc[-1]["risk_factor"]) == 1.0
    assert float(diagnostics.iloc[-1]["opportunity_factor"]) > 1.0
    assert float(transformed.iloc[-1].abs().sum()) > float(targets.iloc[-1].abs().sum())
