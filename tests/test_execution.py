import numpy as np
import pandas as pd

from cryptoai.execution import scheduled_hold


def test_scheduled_hold_supports_12h_rebalance():
    idx = pd.date_range("2024-01-01", periods=48, freq="1h", tz="UTC")
    target = pd.DataFrame({"BTCUSDT": np.arange(48.0)}, index=idx)
    close = pd.DataFrame(1.0, index=idx, columns=target.columns)
    held = scheduled_hold(target, close, interval_hours=12, anchor_hour=0, l1_band=0.0)
    assert held.loc["2024-01-01 11:00", "BTCUSDT"] == 0.0
    assert held.loc["2024-01-01 12:00", "BTCUSDT"] == 12.0
    assert held.loc["2024-01-01 23:00", "BTCUSDT"] == 12.0
    assert held.loc["2024-01-02 00:00", "BTCUSDT"] == 24.0


def test_hysteresis_ignores_small_changes_but_accepts_large_change():
    idx = pd.date_range("2024-01-01", periods=72, freq="1h", tz="UTC")
    target = pd.DataFrame(0.0, index=idx, columns=["BTCUSDT", "ETHUSDT"])
    target.loc["2024-01-01 00:00":, "BTCUSDT"] = 0.50
    target.loc["2024-01-01 00:00":, "ETHUSDT"] = 0.50
    target.loc["2024-01-01 12:00":, "BTCUSDT"] = 0.53
    target.loc["2024-01-01 12:00":, "ETHUSDT"] = 0.47
    target.loc["2024-01-02 00:00":, "BTCUSDT"] = 0.75
    target.loc["2024-01-02 00:00":, "ETHUSDT"] = 0.25
    close = pd.DataFrame(1.0, index=idx, columns=target.columns)

    held = scheduled_hold(target, close, interval_hours=12, anchor_hour=0, l1_band=0.10)
    assert np.isclose(held.loc["2024-01-01 12:00", "BTCUSDT"], 0.50)
    assert np.isclose(held.loc["2024-01-01 12:00", "ETHUSDT"], 0.50)
    assert np.isclose(held.loc["2024-01-02 00:00", "BTCUSDT"], 0.75)
    assert np.isclose(held.loc["2024-01-02 00:00", "ETHUSDT"], 0.25)
