from __future__ import annotations

import pandas as pd

from scripts import run_v99_r106_phase9_sideaware_hedge_component as p9


def _params():
    return {
        "min_net": 0.10,
        "hedge_size": 0.20,
        "gross_cap": 1.90,
    }


def _always_active(monkeypatch, index):
    monkeypatch.setattr(
        p9.r37,
        "r30_stress_mask",
        lambda shadow, btc, p: pd.Series(True, index=index),
    )


def test_profitable_short_book_suppresses_only_additive_long_hedge(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=8, freq="h", tz="UTC")
    raw = pd.DataFrame({"BTCUSDT": 0.05, "ETHUSDT": -0.55}, index=idx)
    close = pd.DataFrame({"BTCUSDT": [100.0] * 8, "ETHUSDT": [100, 99, 98, 97, 96, 95, 94, 93]}, index=idx)
    shadow = pd.Series(range(8), index=idx, dtype=float)
    _always_active(monkeypatch, idx)

    out, _, diag = p9.sideaware_r30_targets(raw, shadow, close, _params())

    # Once the short book has observed positive signed return, the extra +0.20
    # BTC hedge is suppressed, but the +0.05 base BTC alpha remains intact.
    suppressed = out["BTCUSDT"].sub(0.05).abs() < 1e-12
    assert suppressed.iloc[2:].all()
    assert (out.loc[suppressed, "ETHUSDT"] == -0.55).all()
    assert diag["long_hedge_suppressed_fraction"] > 0.0


def test_losing_short_book_keeps_additive_long_hedge(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=8, freq="h", tz="UTC")
    raw = pd.DataFrame({"BTCUSDT": 0.05, "ETHUSDT": -0.55}, index=idx)
    close = pd.DataFrame({"BTCUSDT": [100.0] * 8, "ETHUSDT": [100, 101, 102, 103, 104, 105, 106, 107]}, index=idx)
    shadow = pd.Series(range(8), index=idx, dtype=float)
    _always_active(monkeypatch, idx)

    out, _, diag = p9.sideaware_r30_targets(raw, shadow, close, _params())

    assert (out.loc[idx[2]:, "BTCUSDT"] > 0.05).all()
    assert diag["long_hedge_suppressed_fraction"] == 0.0


def test_profitable_long_book_suppresses_only_additive_short_hedge(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=8, freq="h", tz="UTC")
    raw = pd.DataFrame({"BTCUSDT": -0.05, "ETHUSDT": 0.55}, index=idx)
    close = pd.DataFrame({"BTCUSDT": [100.0] * 8, "ETHUSDT": [100, 101, 102, 103, 104, 105, 106, 107]}, index=idx)
    shadow = pd.Series(range(8), index=idx, dtype=float)
    _always_active(monkeypatch, idx)

    out, _, diag = p9.sideaware_r30_targets(raw, shadow, close, _params())

    suppressed = out["BTCUSDT"].add(0.05).abs() < 1e-12
    assert suppressed.iloc[2:].all()
    assert (out.loc[suppressed, "ETHUSDT"] == 0.55).all()
    assert diag["short_hedge_suppressed_fraction"] > 0.0


def test_losing_long_book_keeps_additive_short_hedge(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=8, freq="h", tz="UTC")
    raw = pd.DataFrame({"BTCUSDT": -0.05, "ETHUSDT": 0.55}, index=idx)
    close = pd.DataFrame({"BTCUSDT": [100.0] * 8, "ETHUSDT": [100, 99, 98, 97, 96, 95, 94, 93]}, index=idx)
    shadow = pd.Series(range(8), index=idx, dtype=float)
    _always_active(monkeypatch, idx)

    out, _, diag = p9.sideaware_r30_targets(raw, shadow, close, _params())

    assert (out.loc[idx[2]:, "BTCUSDT"] < -0.05).all()
    assert diag["short_hedge_suppressed_fraction"] == 0.0
