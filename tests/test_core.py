import numpy as np
import pandas as pd

from cryptoai.gates import PromotionGates
from cryptoai.metrics import max_drawdown, performance, block_bootstrap_ruin_probability
from cryptoai.replay import CandidateSpec, _carry_signal, _core_signal, _daily_hold, _trend_confirmation_multiplier
from cryptoai.splits import ResearchSplit


def test_promotion_gates_match_frozen_thresholds():
    metrics = {
        "base_cagr": 0.561,
        "max_drawdown": -0.279,
        "severe_cost_cagr": 0.371,
        "delay_3h_cagr": 0.520,
        "decisions_per_month": 12.0,
        "bootstrap_ruin_probability": 0.00582,
        "phase_min_cagr": 0.552,
        "liquidated": False,
    }
    report = PromotionGates().report(metrics)
    assert report["passed"] is True
    assert all(report["checks"].values())


def test_gate_rejects_half_valid_candidate():
    metrics = {
        "base_cagr": 0.70,
        "max_drawdown": -0.50,
        "severe_cost_cagr": 0.10,
        "delay_3h_cagr": 0.55,
        "decisions_per_month": 20,
        "bootstrap_ruin_probability": 0.03,
        "phase_min_cagr": -0.01,
        "liquidated": False,
    }
    report = PromotionGates().report(metrics)
    assert report["passed"] is False
    assert report["checks"]["drawdown"] is False
    assert report["checks"]["severe_cost_cagr"] is False
    assert report["checks"]["bootstrap_ruin"] is False
    assert report["checks"]["24_phases"] is False


def test_performance_drawdown():
    idx = pd.date_range("2024-01-01", periods=4, freq="1h", tz="UTC")
    r = pd.Series([0.10, -0.20, 0.05, 0.02], index=idx)
    p = performance(r)
    eq = (1 + r).cumprod()
    assert np.isclose(p.max_drawdown, max_drawdown(eq))
    assert p.observations == 4


def test_bootstrap_detects_obviously_ruinous_series():
    idx = pd.date_range("2024-01-01", periods=1000, freq="1h", tz="UTC")
    r = pd.Series(np.zeros(1000), index=idx)
    r.iloc[::50] = -0.25
    prob = block_bootstrap_ruin_probability(r, samples=200, block_hours=24, seed=7)
    assert prob > 0.5


def test_daily_hold_samples_matrix_at_requested_hour():
    idx = pd.date_range("2024-01-01", periods=48, freq="1h", tz="UTC")
    signal = pd.DataFrame({"BTCUSDT": np.arange(48.0), "ETHUSDT": np.arange(48.0) * -1}, index=idx)
    close = pd.DataFrame(1.0, index=idx, columns=signal.columns)
    held = _daily_hold(signal, 6, close)
    assert (held.loc["2024-01-01 06:00":"2024-01-02 05:00", "BTCUSDT"] == 6.0).all()
    assert (held.loc["2024-01-02 06:00":, "BTCUSDT"] == 30.0).all()
    assert held.loc["2024-01-01 05:00", "BTCUSDT"] == 0.0


def test_research_split_normalizes_naive_and_aware_boundaries_to_utc():
    idx = pd.date_range("2022-12-31 21:00", periods=5, freq="1h", tz="UTC")
    r = pd.Series(np.arange(5.0), index=idx)
    split = ResearchSplit(
        discovery_start="2022-12-31 22:00",
        discovery_end="2022-12-31 23:00:00+00:00",
    )
    sliced = split.discovery_slice(r)
    assert list(sliced.index) == list(pd.date_range("2022-12-31 22:00", periods=2, freq="1h", tz="UTC"))
    assert sliced.tolist() == [1.0, 2.0]


def _synthetic_close(periods: int = 800) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=periods, freq="1h", tz="UTC")
    t = np.arange(periods, dtype=float)
    noise = 0.01 * np.sin(t / 7.0)
    return pd.DataFrame(
        {
            "BTCUSDT": np.exp(4.0 + 0.0004 * t + noise),
            "ETHUSDT": np.exp(3.5 + 0.0002 * t - noise * 0.7),
            "ALTUPUSDT": np.exp(2.0 + 0.0008 * t + noise * 1.3),
            "ALTDOWNUSDT": np.exp(2.5 - 0.0005 * t + noise * 0.9),
        },
        index=idx,
    )


def test_universe_rank_momentum_has_long_and_short_cross_section():
    close = _synthetic_close()
    signal = _core_signal(close, (5,), model="rank_momentum", scope="universe", cross_section_quantile=0.25)
    last = signal.iloc[-1]
    assert last.max() > 0
    assert last.min() < 0
    assert abs(last["ALTUPUSDT"]) > 0


def test_relative_funding_carry_can_long_low_positive_and_short_high_positive():
    close = _synthetic_close(800)
    rates = {"BTCUSDT": 0.00001, "ETHUSDT": 0.00002, "ALTUPUSDT": 0.00003, "ALTDOWNUSDT": 0.00004}
    funding = pd.DataFrame({c: rates[c] for c in close.columns}, index=close.index)
    spec = CandidateSpec(
        carry_horizons_days=(7,),
        carry_names_each_side=1,
        carry_require_sign=False,
        min_history_days=7,
        vol_lookback_days=14,
    )
    weights = _carry_signal(close, funding, spec)
    last = weights.iloc[-1]
    assert (last > 0).any()
    assert (last < 0).any()


def test_trend_confirmation_cuts_risk_when_slow_and_fast_disagree():
    periods = 900
    idx = pd.date_range("2024-01-01", periods=periods, freq="1h", tz="UTC")
    t = np.arange(periods, dtype=float)
    late_drop = np.maximum(t - 820.0, 0.0)
    base = np.exp(4.0 + 0.0010 * t - 0.0030 * late_drop + 0.005 * np.sin(t / 11.0))
    close = pd.DataFrame({"BTCUSDT": base, "ETHUSDT": base * 0.7}, index=idx)
    spec = CandidateSpec(
        horizons_days=(20,),
        trend_filter_mode="agreement",
        trend_fast_horizons_days=(2,),
        trend_conflict_scale=0.25,
        carry_base_allocation=0.0,
        carry_dominant_allocation=0.0,
    )
    multiplier = _trend_confirmation_multiplier(close, spec)
    assert np.isclose(multiplier.iloc[-1]["BTCUSDT"], 0.25)
    assert np.isclose(multiplier.iloc[-1]["ETHUSDT"], 0.25)


def test_trend_confirmation_default_is_neutral():
    close = _synthetic_close()
    multiplier = _trend_confirmation_multiplier(close, CandidateSpec())
    assert (multiplier == 1.0).all().all()
