import numpy as np
import pandas as pd

from cryptoai.relative import relative_momentum_signal


def test_relative_momentum_longs_eth_when_eth_outperforms_btc():
    periods = 240
    idx = pd.date_range("2024-01-01", periods=periods, freq="1h", tz="UTC")
    t = np.arange(periods, dtype=float)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 * np.exp(0.0002 * t),
            "ETHUSDT": 80.0 * np.exp(0.0007 * t),
        },
        index=idx,
    )
    weights = relative_momentum_signal(close, (2, 5), rebalance_hour=0)
    last = weights.iloc[-1]
    assert last["ETHUSDT"] > 0
    assert last["BTCUSDT"] < 0
    assert np.isclose(last.abs().sum(), 1.0)
    assert np.isclose(last.sum(), 0.0)


def test_relative_momentum_flips_when_eth_underperforms_btc():
    periods = 240
    idx = pd.date_range("2024-01-01", periods=periods, freq="1h", tz="UTC")
    t = np.arange(periods, dtype=float)
    close = pd.DataFrame(
        {
            "BTCUSDT": 100.0 * np.exp(0.0007 * t),
            "ETHUSDT": 80.0 * np.exp(0.0002 * t),
        },
        index=idx,
    )
    weights = relative_momentum_signal(close, (2, 5), rebalance_hour=0)
    last = weights.iloc[-1]
    assert last["ETHUSDT"] < 0
    assert last["BTCUSDT"] > 0
    assert np.isclose(last.abs().sum(), 1.0)
    assert np.isclose(last.sum(), 0.0)
