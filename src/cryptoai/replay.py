from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .binance_data import load_funding, load_klines
from .metrics import performance, yearly_returns, decisions_per_month


@dataclass(frozen=True)
class CandidateSpec:
    horizons_days: tuple[int, ...] = (60, 90, 120, 150)
    carry_base_allocation: float = 0.35
    carry_dominant_allocation: float = 0.85
    carry_names_each_side: int = 3
    target_volatility: float = 0.55
    max_gross_leverage: float = 2.25
    max_single_weight: float = 0.55
    rebalance_hour: int = 0
    execution_delay_hours: int = 0
    one_way_cost_bps: float = 15.0
    severe_cost_multiplier: float = 3.0
    vol_lookback_days: int = 30
    allocation_compare_days: int = 45
    min_history_days: int = 180


@dataclass
class ReplayData:
    close: pd.DataFrame
    funding: pd.DataFrame


def load_universe(symbols: Iterable[str], start: str, end: str, cache_dir: Path) -> ReplayData:
    closes: dict[str, pd.Series] = {}
    funding: dict[str, pd.Series] = {}
    for symbol in symbols:
        k = load_klines(symbol, start, end, cache_dir)
        if not k.empty:
            closes[symbol] = k["close"].rename(symbol)
            funding[symbol] = load_funding(symbol, start, end, cache_dir)
    close = pd.concat(closes.values(), axis=1).sort_index() if closes else pd.DataFrame()
    fund = pd.concat(funding.values(), axis=1).sort_index() if funding else pd.DataFrame()
    if not close.empty:
        full_index = pd.date_range(close.index.min(), close.index.max(), freq="1h", tz="UTC")
        close = close.reindex(full_index)
        close = close.ffill(limit=4)
        fund = fund.reindex(full_index).fillna(0.0)
    return ReplayData(close=close, funding=fund)


def _daily_hold(signal: pd.DataFrame, hour: int, close: pd.DataFrame) -> pd.DataFrame:
    """Sample a full weight matrix once per UTC day, then hold until next sample."""
    sampled = signal.copy()
    sampled.loc[sampled.index.hour != hour, :] = np.nan
    held = sampled.ffill().fillna(0.0)
    return held.where(close.notna(), 0.0)


def _core_signal(close: pd.DataFrame, horizons_days: tuple[int, ...]) -> pd.DataFrame:
    core_assets = [c for c in ("BTCUSDT", "ETHUSDT") if c in close.columns]
    if not core_assets:
        return pd.DataFrame(0.0, index=close.index, columns=close.columns)
    core = close[core_assets]
    score = pd.DataFrame(0.0, index=close.index, columns=core_assets)
    components = 0
    for d in horizons_days:
        h = d * 24
        momentum = np.sign(np.log(core / core.shift(h)))
        ema_fast = core.ewm(span=max(24, h // 4), adjust=False, min_periods=max(24, h // 4)).mean()
        ema_slow = core.ewm(span=h, adjust=False, min_periods=h).mean()
        trend = np.sign(ema_fast - ema_slow)
        mean = core.rolling(h, min_periods=h).mean()
        slope_proxy = np.sign(core - mean)
        score = score.add(momentum.fillna(0.0) + trend.fillna(0.0) + slope_proxy.fillna(0.0), fill_value=0.0)
        components += 3
    score = (score / components).clip(-1.0, 1.0)
    rv = core.pct_change(fill_method=None).rolling(30 * 24, min_periods=14 * 24).std() * np.sqrt(365.25 * 24)
    inv = 1.0 / rv.replace(0.0, np.nan)
    raw = score * inv
    denom = raw.abs().sum(axis=1).replace(0.0, np.nan)
    raw = raw.div(denom, axis=0).fillna(0.0)
    out = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    out.loc[:, core_assets] = raw
    return out


def _carry_signal(close: pd.DataFrame, funding: pd.DataFrame, spec: CandidateSpec) -> pd.DataFrame:
    avg_funding = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    for d in spec.horizons_days:
        avg_funding += funding.reindex(columns=close.columns, fill_value=0.0).rolling(d * 24, min_periods=max(7 * 24, d * 12)).sum()
    avg_funding /= len(spec.horizons_days)

    rv = close.pct_change(fill_method=None).rolling(spec.vol_lookback_days * 24, min_periods=14 * 24).std() * np.sqrt(365.25 * 24)
    history = close.notna().rolling(spec.min_history_days * 24, min_periods=1).sum() >= spec.min_history_days * 24 * 0.90
    score = avg_funding.div(rv.replace(0.0, np.nan)).where(history)

    weights = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    rebalance_mask = close.index.hour == spec.rebalance_hour
    for ts in close.index[rebalance_mask]:
        s = score.loc[ts].dropna()
        if len(s) < 4:
            continue
        n = min(spec.carry_names_each_side, max(1, len(s) // 4))
        shorts = s.nlargest(n)
        longs = s.nsmallest(n)
        selected: dict[str, float] = {}
        for sym, val in shorts.items():
            if val > 0:
                selected[sym] = -1.0
        for sym, val in longs.items():
            if val < 0:
                selected[sym] = 1.0
        if not selected:
            continue
        risk = rv.loc[ts, list(selected)].replace(0.0, np.nan)
        inv = (1.0 / risk).replace([np.inf, -np.inf], np.nan).dropna()
        if inv.empty:
            continue
        for side in (1.0, -1.0):
            names = [x for x, v in selected.items() if v == side and x in inv.index]
            if not names:
                continue
            w = inv.loc[names] / inv.loc[names].sum() * 0.5
            weights.loc[ts, names] = side * w
    return _daily_hold(weights, spec.rebalance_hour, close)


def _sleeve_return(weights: pd.DataFrame, asset_returns: pd.DataFrame, funding: pd.DataFrame, cost_bps: float) -> pd.Series:
    w = weights.shift(1).fillna(0.0)
    price_pnl = (w * asset_returns.fillna(0.0)).sum(axis=1)
    funding_pnl = (-w * funding.reindex_like(asset_returns).fillna(0.0)).sum(axis=1)
    turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(weights.abs().sum(axis=1))
    costs = turnover * (cost_bps / 10000.0)
    return price_pnl + funding_pnl - costs


def build_weights(data: ReplayData, spec: CandidateSpec) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
    close = data.close
    asset_returns = close.pct_change(fill_method=None)
    funding = data.funding.reindex_like(close).fillna(0.0)

    core_raw = _core_signal(close, spec.horizons_days)
    core = _daily_hold(core_raw, spec.rebalance_hour, close)
    carry = _carry_signal(close, funding, spec)

    core_ret = _sleeve_return(core, asset_returns, funding, spec.one_way_cost_bps)
    carry_ret = _sleeve_return(carry, asset_returns, funding, spec.one_way_cost_bps)
    look = spec.allocation_compare_days * 24
    core_growth = (1.0 + core_ret).rolling(look, min_periods=look // 2).apply(np.prod, raw=True) - 1.0
    carry_growth = (1.0 + carry_ret).rolling(look, min_periods=look // 2).apply(np.prod, raw=True) - 1.0
    carry_alloc = pd.Series(spec.carry_base_allocation, index=close.index)
    carry_alloc = carry_alloc.where(~(carry_growth > core_growth), spec.carry_dominant_allocation)
    core_alloc = 1.0 - carry_alloc
    combined = core.mul(core_alloc, axis=0).add(carry.mul(carry_alloc, axis=0), fill_value=0.0)

    raw_ret = (combined.shift(1).fillna(0.0) * asset_returns.fillna(0.0)).sum(axis=1)
    rolling_vol = raw_ret.rolling(spec.vol_lookback_days * 24, min_periods=14 * 24).std() * np.sqrt(365.25 * 24)
    scale = (spec.target_volatility / rolling_vol.replace(0.0, np.nan)).clip(upper=spec.max_gross_leverage).fillna(0.0)
    combined = combined.mul(scale, axis=0)
    gross = combined.abs().sum(axis=1)
    gross_scale = (spec.max_gross_leverage / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    combined = combined.mul(gross_scale, axis=0).clip(-spec.max_single_weight, spec.max_single_weight)
    gross = combined.abs().sum(axis=1)
    gross_scale = (spec.max_gross_leverage / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    combined = combined.mul(gross_scale, axis=0)

    combined = _daily_hold(combined, spec.rebalance_hour, close)

    if spec.execution_delay_hours:
        combined = combined.shift(spec.execution_delay_hours).fillna(0.0)
    return combined, {"core": core_ret, "carry": carry_ret, "carry_allocation": carry_alloc}


def run_replay(data: ReplayData, spec: CandidateSpec, *, cost_multiplier: float = 1.0, funding_adverse: bool = False) -> dict[str, object]:
    weights, sleeves = build_weights(data, spec)
    close = data.close
    asset_returns = close.pct_change(fill_method=None)
    funding = data.funding.reindex_like(close).fillna(0.0)
    if funding_adverse:
        held = weights.shift(1).fillna(0.0)
        signed_pnl = -held * funding
        funding_effect = signed_pnl.where(signed_pnl < 0, signed_pnl * 0.5).where(signed_pnl >= 0, signed_pnl * 1.5)
        funding_pnl = funding_effect.sum(axis=1)
        price_pnl = (held * asset_returns.fillna(0.0)).sum(axis=1)
        turnover = weights.diff().abs().sum(axis=1).fillna(weights.abs().sum(axis=1))
        returns = price_pnl + funding_pnl - turnover * (spec.one_way_cost_bps * cost_multiplier / 10000.0)
    else:
        returns = _sleeve_return(weights, asset_returns, funding, spec.one_way_cost_bps * cost_multiplier)
    perf = performance(returns)
    liquidated = bool((returns <= -1.0).any())
    carry_alloc = sleeves["carry_allocation"]
    diagnostics = {
        "core_sleeve": performance(sleeves["core"]).to_dict(),
        "carry_sleeve": performance(sleeves["carry"]).to_dict(),
        "carry_dominant_fraction": float((carry_alloc == spec.carry_dominant_allocation).mean()),
        "average_gross_exposure": float(weights.abs().sum(axis=1).mean()),
        "p95_gross_exposure": float(weights.abs().sum(axis=1).quantile(0.95)),
    }
    return {
        "performance": perf.to_dict(),
        "yearly_returns": yearly_returns(returns),
        "decisions_per_month": decisions_per_month(weights),
        "min_hourly_return": float(returns.min()) if len(returns) else 0.0,
        "liquidated": liquidated,
        "diagnostics": diagnostics,
        "returns": returns,
        "weights": weights,
        "sleeves": sleeves,
    }


def phase_sweep(data: ReplayData, spec: CandidateSpec) -> dict[str, float]:
    out: dict[str, float] = {}
    for hour in range(24):
        result = run_replay(data, replace(spec, rebalance_hour=hour))
        out[str(hour)] = float(result["performance"]["cagr"])
    return out
