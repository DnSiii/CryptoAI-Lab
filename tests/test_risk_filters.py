import numpy as np
import pandas as pd

from cryptoai.replay import CandidateSpec, _volatility_shock_multiplier


def test_volatility_shock_brake_cuts_exposure_on_recent_vol_spike():
    periods = 1200
    idx = pd.date_range("2024-01-01", periods=periods, freq="1h", tz="UTC")
    t = np.arange(periods, dtype=float)
    low = 0.0003 + 0.0005 * np.sin(t / 13.0)
    high = 0.0003 + 0.0080 * np.sin(t / 2.5)
    hourly = np.where(t >= 1100, high, low)
    btc = 100.0 * np.exp(np.cumsum(hourly))
    eth = 80.0 * np.exp(np.cumsum(hourly * 1.1))
    close = pd.DataFrame({"BTCUSDT": btc, "ETHUSDT": eth}, index=idx)
    spec = CandidateSpec(
        volatility_shock_mode="ratio",
        volatility_shock_short_days=2,
        volatility_shock_long_days=20,
        volatility_shock_threshold=1.5,
        volatility_shock_scale=0.25,
    )
    multiplier = _volatility_shock_multiplier(close, spec)
    assert np.isclose(multiplier.iloc[-1]["BTCUSDT"], 0.25)
    assert np.isclose(multiplier.iloc[-1]["ETHUSDT"], 0.25)


def test_volatility_shock_default_is_neutral():
    idx = pd.date_range("2024-01-01", periods=100, freq="1h", tz="UTC")
    close = pd.DataFrame({"BTCUSDT": np.linspace(100, 110, 100)}, index=idx)
    multiplier = _volatility_shock_multiplier(close, CandidateSpec())
    assert (multiplier == 1.0).all().all()
