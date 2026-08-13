from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import FuturesData


@dataclass(frozen=True)
class StrategySpec:
    family: str
    lookback: int
    rebalance: int
    top_n: int = 2
    fast: int = 24
    slow: int = 168
    vol_lookback: int = 168
    vol_target: float = 0.8
    leverage_cap: float = 2.0
    trend_lookback: int = 168
    long_short_balance: float = 0.5
    threshold: float = 0.0
    exit_lookback: int = 24

    def to_dict(self) -> dict:
        return asdict(self)


def _hourly_vol(close: pd.DataFrame, lookback: int) -> pd.DataFrame:
    return close.pct_change(fill_method=None).rolling(
        lookback, min_periods=max(24, lookback // 2)).std() * np.sqrt(365.25 * 24)


def _risk_scale(raw: pd.DataFrame, vol: pd.DataFrame, target: float, cap: float) -> pd.DataFrame:
    inv = raw.div(vol.replace(0.0, np.nan))
    gross = inv.abs().sum(axis=1).replace(0.0, np.nan)
    normalized = inv.div(gross, axis=0)
    # Diagonal covariance approximation is deliberately conservative for the
    # first screen; exact finalists receive realized portfolio-vol overlays.
    estimated = np.sqrt(((normalized * vol) ** 2).sum(axis=1)).replace(0.0, np.nan)
    leverage = (target / estimated).clip(upper=cap).fillna(0.0)
    return normalized.mul(leverage, axis=0).fillna(0.0)


def _rebalance_and_hold(target: pd.DataFrame, every: int) -> pd.DataFrame:
    event = pd.Series(np.arange(len(target)) % every == 0, index=target.index)
    return target.where(event, np.nan).ffill().fillna(0.0)


def cross_sectional_momentum(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    close = data.close
    score = close.div(close.shift(spec.lookback)).sub(1.0)
    trend = close.div(close.ewm(span=spec.trend_lookback, adjust=False, min_periods=spec.trend_lookback).mean()).sub(1.0)
    available = close.notna() & close.shift(max(spec.lookback, spec.trend_lookback)).notna()
    long_rank = score.rank(axis=1, ascending=False, method="first")
    short_rank = score.rank(axis=1, ascending=True, method="first")
    longs = available & (long_rank <= spec.top_n) & (trend > spec.threshold)
    shorts = available & (short_rank <= spec.top_n) & (trend < -spec.threshold)
    long_weight = spec.long_short_balance
    short_weight = 1.0 - spec.long_short_balance
    raw = longs.astype(float).mul(long_weight).sub(shorts.astype(float).mul(short_weight))
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance)


def regime_momentum(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    """Cross-sectional momentum with directional exposure chosen by BTC regime."""
    close = data.close
    score = close.div(close.shift(spec.lookback)).sub(1.0)
    asset_trend = close.div(close.ewm(span=spec.trend_lookback, adjust=False,
                                     min_periods=spec.trend_lookback).mean()).sub(1.0)
    btc_slow = close["BTCUSDT"].ewm(span=spec.slow, adjust=False,
                                    min_periods=spec.slow).mean()
    btc_regime = close["BTCUSDT"].div(btc_slow).sub(1.0)
    available = close.notna() & close.shift(max(spec.lookback, spec.trend_lookback)).notna()
    long_rank = score.rank(axis=1, ascending=False, method="first")
    short_rank = score.rank(axis=1, ascending=True, method="first")
    longs = available & (long_rank <= spec.top_n) & (asset_trend > 0.0)
    shorts = available & (short_rank <= spec.top_n) & (asset_trend < 0.0)
    bull = btc_regime > spec.threshold
    bear = btc_regime < -spec.threshold
    neutral = ~(bull | bear)
    defensive_fraction = 1.0 - spec.long_short_balance
    long_factor = bull.astype(float) + bear.astype(float) * defensive_fraction + neutral.astype(float) * 0.5
    short_factor = bear.astype(float) + bull.astype(float) * defensive_fraction + neutral.astype(float) * 0.5
    raw = longs.astype(float).mul(long_factor, axis=0).sub(
        shorts.astype(float).mul(short_factor, axis=0))
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance)


def time_series_trend(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    close = data.close
    fast = close.ewm(span=spec.fast, adjust=False, min_periods=spec.fast).mean()
    slow = close.ewm(span=spec.slow, adjust=False, min_periods=spec.slow).mean()
    strength = fast.div(slow).sub(1.0)
    raw = np.sign(strength).where(strength.abs() > spec.threshold, 0.0)
    raw = raw.where(close.shift(spec.slow).notna(), 0.0)
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance)


def funding_carry(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    close = data.close
    known = data.funding.replace(0.0, np.nan).ffill().shift(1)
    avg = known.rolling(spec.lookback, min_periods=max(8, spec.lookback // 3)).mean()
    long_rank = avg.rank(axis=1, ascending=True, method="first")
    short_rank = avg.rank(axis=1, ascending=False, method="first")
    trend = close.div(close.ewm(span=spec.trend_lookback, adjust=False,
                                min_periods=spec.trend_lookback).mean()).sub(1.0)
    longs = (long_rank <= spec.top_n) & (avg < -spec.threshold) & (trend > -0.05)
    shorts = (short_rank <= spec.top_n) & (avg > spec.threshold) & (trend < 0.05)
    raw = longs.astype(float).mul(spec.long_short_balance).sub(
        shorts.astype(float).mul(1.0 - spec.long_short_balance))
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance)


def breakout(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    close, high, low = data.close, data.frames["high"], data.frames["low"]
    upper = high.shift(1).rolling(spec.lookback, min_periods=spec.lookback).max()
    lower = low.shift(1).rolling(spec.lookback, min_periods=spec.lookback).min()
    exit_high = high.shift(1).rolling(spec.exit_lookback, min_periods=spec.exit_lookback).max()
    exit_low = low.shift(1).rolling(spec.exit_lookback, min_periods=spec.exit_lookback).min()
    raw = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    for column in close:
        state = 0.0
        values = np.zeros(len(close))
        c = close[column].to_numpy()
        u, l = upper[column].to_numpy(), lower[column].to_numpy()
        eh, el = exit_high[column].to_numpy(), exit_low[column].to_numpy()
        for i in range(len(close)):
            if not np.isfinite(c[i]):
                state = 0.0
            elif state == 0 and np.isfinite(u[i]) and c[i] > u[i]:
                state = 1.0
            elif state == 0 and np.isfinite(l[i]) and c[i] < l[i]:
                state = -1.0
            elif state > 0 and np.isfinite(el[i]) and c[i] < el[i]:
                state = 0.0
            elif state < 0 and np.isfinite(eh[i]) and c[i] > eh[i]:
                state = 0.0
            values[i] = state
        raw[column] = values
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance)


def mean_reversion(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    close = data.close
    log_price = np.log(close)
    center = log_price.rolling(spec.lookback, min_periods=spec.lookback).mean()
    width = log_price.rolling(spec.lookback, min_periods=spec.lookback).std().replace(0.0, np.nan)
    zscore = log_price.sub(center).div(width)
    btc_move = close["BTCUSDT"].pct_change(spec.trend_lookback, fill_method=None).abs()
    # Mean reversion is enabled only when the market leader is not in a strong
    # directional move. The threshold is known at the prior close.
    sideways = btc_move < 0.12
    raw = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    exit_threshold = max(0.15, min(0.6, spec.threshold / 3.0))
    for column in close:
        state = 0.0
        values = np.zeros(len(close))
        z = zscore[column].to_numpy()
        enabled = sideways.to_numpy()
        for i in range(len(close)):
            if not enabled[i] or not np.isfinite(z[i]):
                state = 0.0
            elif state == 0.0 and z[i] >= spec.threshold:
                state = -1.0
            elif state == 0.0 and z[i] <= -spec.threshold:
                state = 1.0
            elif state > 0.0 and z[i] >= -exit_threshold:
                state = 0.0
            elif state < 0.0 and z[i] <= exit_threshold:
                state = 0.0
            values[i] = state
        raw[column] = values
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance)


def build_targets(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    if spec.family == "xmom":
        return cross_sectional_momentum(data, spec)
    if spec.family == "trend":
        return time_series_trend(data, spec)
    if spec.family == "regime":
        return regime_momentum(data, spec)
    if spec.family == "funding":
        return funding_carry(data, spec)
    if spec.family == "breakout":
        return breakout(data, spec)
    if spec.family == "meanrev":
        return mean_reversion(data, spec)
    raise ValueError(f"família desconhecida: {spec.family}")
