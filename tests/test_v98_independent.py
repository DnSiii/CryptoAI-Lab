from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cryptoai_v13.data import FuturesData

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "v98_independent_baseline", PROJECT / "scripts" / "v98_independent_baseline.py"
)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def synthetic_data(hours: int = 5000) -> FuturesData:
    index = pd.date_range("2024-01-01", periods=hours, freq="h", tz="UTC")
    symbols = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT")
    rng = np.random.default_rng(42)
    close = {}
    for i, symbol in enumerate(symbols):
        returns = rng.normal(0.00002 * (i + 1), 0.006 + i * 0.0005, hours)
        close[symbol] = 100.0 * np.exp(np.cumsum(returns))
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


def test_v98_targets_are_future_invariant() -> None:
    cfg = json.loads((PROJECT / "config" / "v98_independent.json").read_text())
    data = synthetic_data()
    membership = membership_for(data)
    baseline = MOD.build_targets(data, membership, cfg)

    cut = 4300
    mutated_frames = {k: v.copy() for k, v in data.frames.items()}
    for frame in mutated_frames.values():
        frame.iloc[cut + 1 :] *= 1.75
    mutated_funding = data.funding.copy()
    mutated_funding.iloc[cut + 1 :] = 0.05
    mutated = FuturesData(mutated_frames, mutated_funding, data.symbols)
    changed = MOD.build_targets(mutated, membership_for(mutated), cfg)

    pd.testing.assert_frame_equal(baseline.iloc[: cut + 1], changed.iloc[: cut + 1])


def test_v98_respects_declared_gross_cap() -> None:
    cfg = json.loads((PROJECT / "config" / "v98_independent.json").read_text())
    data = synthetic_data()
    targets = MOD.build_targets(data, membership_for(data), cfg)
    assert float(targets.abs().sum(axis=1).max()) <= cfg["architecture"]["gross_cap"] + 1e-12


def test_v98_rebalances_only_on_fixed_events_after_warmup() -> None:
    cfg = json.loads((PROJECT / "config" / "v98_independent.json").read_text())
    data = synthetic_data()
    targets = MOD.build_targets(data, membership_for(data), cfg)
    changed = targets.diff().abs().sum(axis=1) > 1e-12
    hours = np.flatnonzero(changed.to_numpy())
    if len(hours):
        assert all(h % cfg["architecture"]["rebalance_hours"] == 0 for h in hours)
