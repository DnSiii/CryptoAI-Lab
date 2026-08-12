import numpy as np
import pandas as pd

from cryptoai.gates import PromotionGates
from cryptoai.metrics import max_drawdown, performance, block_bootstrap_ruin_probability


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
