from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cryptoai_v13.data import FuturesData

PROJECT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT / path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BASE = load_module("v98_independent_baseline", "scripts/v98_independent_baseline.py")
P003 = load_module("v98_independent_phase003", "scripts/v98_independent_phase003_dispersion_neutral.py")


def synthetic_data(hours: int = 6500) -> FuturesData:
    index = pd.date_range("2024-01-01", periods=hours, freq="h", tz="UTC")
    symbols = (
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
        "LINKUSDT", "LTCUSDT", "DOGEUSDT", "SOLUSDT", "AVAXUSDT",
    )
    rng = np.random.default_rng(42)
    btc_r = rng.normal(0.00002, 0.007, hours)
    close = {"BTCUSDT": 100.0 * np.exp(np.cumsum(btc_r))}
    for i, symbol in enumerate(symbols[1:], start=1):
        idio = rng.normal(0.00001 * ((i % 3) - 1), 0.0045 + i * 0.0002, hours)
        r = (0.65 + 0.03 * i) * btc_r + idio
        close[symbol] = 100.0 * np.exp(np.cumsum(r))
    close_df = pd.DataFrame(close, index=index)
    opened = close_df.shift(1).fillna(close_df.iloc[0])
    frames = {
        "open": opened,
        "high": pd.DataFrame(np.maximum(opened, close_df) * 1.002, index=index, columns=symbols),
        "low": pd.DataFrame(np.minimum(opened, close_df) * 0.998, index=index, columns=symbols),
        "close": close_df,
        "volume": pd.DataFrame(1000.0, index=index, columns=symbols),
        "quote_volume": pd.DataFrame(
            {symbol: 1_000_000.0 * (len(symbols) - i) for i, symbol in enumerate(symbols)}, index=index
        ),
        "trades": pd.DataFrame(1000.0, index=index, columns=symbols),
    }
    funding = pd.DataFrame(0.0, index=index, columns=symbols)
    return FuturesData(frames=frames, funding=funding, symbols=symbols)


def membership_for(data: FuturesData) -> pd.DataFrame:
    return data.close.notna()


def test_v98_baseline_targets_are_future_invariant() -> None:
    cfg = json.loads((PROJECT / "config" / "v98_independent.json").read_text())
    data = synthetic_data()
    baseline = BASE.build_targets(data, membership_for(data), cfg)
    cut = 5600
    mutated_frames = {k: v.copy() for k, v in data.frames.items()}
    for frame in mutated_frames.values():
        frame.iloc[cut + 1 :] *= 1.75
    mutated_funding = data.funding.copy()
    mutated_funding.iloc[cut + 1 :] = 0.05
    mutated = FuturesData(mutated_frames, mutated_funding, data.symbols)
    changed = BASE.build_targets(mutated, membership_for(mutated), cfg)
    pd.testing.assert_frame_equal(baseline.iloc[: cut + 1], changed.iloc[: cut + 1])


def test_v98_phase003_targets_are_future_invariant() -> None:
    data = synthetic_data()
    baseline = P003.build_targets(data, membership_for(data))
    cut = 5600
    mutated_frames = {k: v.copy() for k, v in data.frames.items()}
    for frame in mutated_frames.values():
        frame.iloc[cut + 1 :] *= 1.75
    mutated = FuturesData(mutated_frames, data.funding.copy(), data.symbols)
    changed = P003.build_targets(mutated, membership_for(mutated))
    pd.testing.assert_frame_equal(baseline.iloc[: cut + 1], changed.iloc[: cut + 1])


def test_v98_phase003_respects_gross_and_rebalance_constraints() -> None:
    data = synthetic_data()
    targets = P003.build_targets(data, membership_for(data))
    assert float(targets.abs().sum(axis=1).max()) <= P003.PHASE["gross_cap"] + 1e-12
    changed = targets.diff().abs().sum(axis=1) > 1e-12
    hours = np.flatnonzero(changed.to_numpy())
    if len(hours):
        assert all(h % P003.PHASE["rebalance_hours"] == 0 for h in hours)


def test_v98_phase003_is_nearly_dollar_neutral_at_rebalances() -> None:
    data = synthetic_data()
    targets = P003.build_targets(data, membership_for(data))
    active = targets.abs().sum(axis=1) > 1e-8
    if active.any():
        assert float(targets.loc[active].sum(axis=1).abs().max()) < 1e-8
