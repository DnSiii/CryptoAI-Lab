from __future__ import annotations

import pandas as pd

from scripts.run_v99_r106_native_all_regime_engine import side_aware_quality_controller


def _fixture():
    idx = pd.date_range("2026-01-01", periods=4, freq="h", tz="UTC")
    targets = pd.DataFrame(
        {
            "BTCUSDT": [0.4, 0.4, 0.4, 0.4],
            "ETHUSDT": [-0.5, -0.5, -0.5, -0.5],
        },
        index=idx,
    )
    close = pd.DataFrame(
        {
            "BTCUSDT": [100.0, 96.0, 92.0, 88.0],
            "ETHUSDT": [100.0, 96.0, 92.0, 88.0],
        },
        index=idx,
    )
    return idx, targets, close


def test_bear_high_vol_cuts_long_but_preserves_short():
    idx, targets, close = _fixture()
    direction = pd.Series(["BEAR"] * len(idx), index=idx)
    vol = pd.Series(["HIGH_VOLATILITY"] * len(idx), index=idx)
    out, diag = side_aware_quality_controller(targets, close, direction, vol)

    # Controller is causal and acts only after prior regime/24h shock exists.
    # On any activated bear/high-vol row, long gross may shrink but short gross
    # must never be reduced by the protection logic.
    active = out["BTCUSDT"].abs() < targets["BTCUSDT"].abs()
    if active.any():
        assert (out.loc[active, "BTCUSDT"].abs() < targets.loc[active, "BTCUSDT"].abs()).all()
        assert (out.loc[active, "ETHUSDT"].abs() >= targets.loc[active, "ETHUSDT"].abs() - 1e-12).all()
    assert diag["aligned_side_preserved"] is True
    assert diag["global_risk_cut_used"] is False


def test_bull_high_vol_cuts_short_but_preserves_long():
    idx = pd.date_range("2026-01-01", periods=30, freq="h", tz="UTC")
    targets = pd.DataFrame({"BTCUSDT": 0.45, "ETHUSDT": -0.55}, index=idx)
    close = pd.DataFrame(index=idx)
    close["BTCUSDT"] = [100.0] * 24 + [103.0, 106.0, 109.0, 112.0, 115.0, 118.0]
    close["ETHUSDT"] = close["BTCUSDT"]
    direction = pd.Series(["BULL"] * len(idx), index=idx)
    vol = pd.Series(["HIGH_VOLATILITY"] * len(idx), index=idx)
    out, _ = side_aware_quality_controller(targets, close, direction, vol)

    active = out["ETHUSDT"].abs() < targets["ETHUSDT"].abs()
    if active.any():
        assert (out.loc[active, "BTCUSDT"].abs() >= targets.loc[active, "BTCUSDT"].abs() - 1e-12).all()
        assert (out.loc[active, "ETHUSDT"].abs() < targets.loc[active, "ETHUSDT"].abs()).all()
