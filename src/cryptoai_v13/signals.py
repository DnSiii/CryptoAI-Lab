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
    volume_multiple: float = 1.5
    stop_loss: float = 0.05
    trailing_stop: float = 0.10
    max_holding: int = 168
    rebalance_phase: int = 0
    trend_filter_hours: int = 0
    cooldown_hours: int = 0

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


def _rebalance_and_hold(target: pd.DataFrame, every: int, phase: int = 0) -> pd.DataFrame:
    event = pd.Series(
        np.arange(len(target)) % every == phase % every, index=target.index
    )
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
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance, spec.rebalance_phase)


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
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance, spec.rebalance_phase)


def time_series_trend(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    close = data.close
    fast = close.ewm(span=spec.fast, adjust=False, min_periods=spec.fast).mean()
    slow = close.ewm(span=spec.slow, adjust=False, min_periods=spec.slow).mean()
    strength = fast.div(slow).sub(1.0)
    raw = np.sign(strength).where(strength.abs() > spec.threshold, 0.0)
    raw = raw.where(close.shift(spec.slow).notna(), 0.0)
    vol = _hourly_vol(close, spec.vol_lookback)
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance, spec.rebalance_phase)


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
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance, spec.rebalance_phase)


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
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance, spec.rebalance_phase)


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
    return _rebalance_and_hold(_risk_scale(raw, vol, spec.vol_target, spec.leverage_cap), spec.rebalance, spec.rebalance_phase)


def impulse_breakout(data: FuturesData, spec: StrategySpec) -> pd.DataFrame:
    """Fast price/volume impulse with bounded losers and trailing winners.

    A signal uses the close and completed volume of hour ``t`` and therefore
    can only execute at the next hourly open in the replay. Entries require a
    fresh channel breakout, a minimum price impulse and unusually high recent
    quote volume. A close-based fixed stop limits failed attempts while the
    trailing stop and maximum holding period govern winners. Finalists require
    exact replay and harsher costs; this function does not claim intrabar stop
    execution from hourly bars.
    """
    close = data.close
    quote_volume = data.frames["quote_volume"]
    returns = close.div(close.shift(spec.lookback)).sub(1.0)
    upper = data.frames["high"].shift(1).rolling(
        spec.lookback, min_periods=spec.lookback
    ).max()
    lower = data.frames["low"].shift(1).rolling(
        spec.lookback, min_periods=spec.lookback
    ).min()
    recent_volume = quote_volume.rolling(
        spec.fast, min_periods=max(1, spec.fast // 2)
    ).mean()
    baseline_volume = quote_volume.shift(spec.fast).rolling(
        spec.slow, min_periods=max(24, spec.slow // 2)
    ).median()
    volume_ratio = recent_volume.div(baseline_volume.replace(0.0, np.nan))
    available = (
        close.notna()
        & close.shift(max(spec.lookback, spec.slow + spec.fast)).notna()
    )
    long_entry = (
        available
        & (close > upper)
        & (returns >= spec.threshold)
        & (volume_ratio >= spec.volume_multiple)
    )
    short_entry = (
        available
        & (close < lower)
        & (returns <= -spec.threshold)
        & (volume_ratio >= spec.volume_multiple)
    )
    if spec.trend_filter_hours > 0:
        directional_center = close.ewm(
            span=spec.trend_filter_hours,
            adjust=False,
            min_periods=spec.trend_filter_hours,
        ).mean()
        long_entry &= close > directional_center
        short_entry &= close < directional_center
    strength = returns.abs().mul(np.log1p(volume_ratio.clip(lower=0.0)))
    raw_values = np.zeros(close.shape, dtype=float)
    change_events = np.zeros(len(close), dtype=bool)
    price_values = close.to_numpy(dtype=float, copy=False)
    open_values = data.frames["open"].to_numpy(dtype=float, copy=False)
    high_values = data.frames["high"].to_numpy(dtype=float, copy=False)
    low_values = data.frames["low"].to_numpy(dtype=float, copy=False)
    long_values = long_entry.to_numpy(dtype=bool, copy=False)
    short_values = short_entry.to_numpy(dtype=bool, copy=False)
    strength_values = strength.to_numpy(dtype=float, copy=False)
    state = np.zeros(close.shape[1], dtype=np.int8)
    entry_price = np.full(close.shape[1], np.nan)
    extreme = np.full(close.shape[1], np.nan)
    age = np.zeros(close.shape[1], dtype=np.int32)
    pending_entry = np.zeros(close.shape[1], dtype=bool)
    blocked = np.zeros(close.shape[1], dtype=bool)
    cooldown_until = np.zeros(close.shape[1], dtype=np.int64)

    for i in range(len(close)):
        prices = price_values[i]
        changed = False
        blocked &= long_values[i] | short_values[i]
        for asset in np.flatnonzero(state != 0):
            price = prices[asset]
            if pending_entry[asset]:
                opened = open_values[i, asset]
                if not np.isfinite(opened):
                    state[asset] = 0
                    pending_entry[asset] = False
                    blocked[asset] = True
                    changed = True
                    continue
                entry_price[asset] = opened
                extreme[asset] = opened
                pending_entry[asset] = False
            if not np.isfinite(price) or not np.isfinite(entry_price[asset]):
                state[asset] = 0
                blocked[asset] = True
                changed = True
                continue
            age[asset] += 1
            high = high_values[i, asset]
            low = low_values[i, asset]
            if not np.isfinite(high):
                high = price
            if not np.isfinite(low):
                low = price
            if state[asset] > 0:
                stopped = low <= entry_price[asset] * (1.0 - spec.stop_loss)
                trailed = low <= extreme[asset] * (1.0 - spec.trailing_stop)
            else:
                stopped = high >= entry_price[asset] * (1.0 + spec.stop_loss)
                trailed = high >= extreme[asset] * (1.0 + spec.trailing_stop)
            if stopped or trailed or age[asset] >= spec.max_holding:
                state[asset] = 0
                entry_price[asset] = np.nan
                extreme[asset] = np.nan
                age[asset] = 0
                blocked[asset] = True
                cooldown_until[asset] = i + spec.cooldown_hours
                changed = True
            elif state[asset] > 0:
                extreme[asset] = max(extreme[asset], high)
            else:
                extreme[asset] = min(extreme[asset], low)

        entry_event = i % spec.rebalance == spec.rebalance_phase % spec.rebalance
        if entry_event:
            long_slots = max(0, spec.top_n - int((state > 0).sum()))
            if long_slots:
                candidates = np.flatnonzero(
                    long_values[i] & (state == 0) & ~blocked
                    & (i >= cooldown_until)
                )
                order = candidates[np.argsort(strength_values[i, candidates])[::-1]]
                for asset in order[:long_slots]:
                    state[asset] = 1
                    pending_entry[asset] = True
                    age[asset] = 0
                    changed = True
            short_slots = max(0, spec.top_n - int((state < 0).sum()))
            if short_slots:
                candidates = np.flatnonzero(
                    short_values[i] & (state == 0) & ~blocked
                    & (i >= cooldown_until)
                )
                order = candidates[np.argsort(strength_values[i, candidates])[::-1]]
                for asset in order[:short_slots]:
                    state[asset] = -1
                    pending_entry[asset] = True
                    age[asset] = 0
                    changed = True
        raw_values[i] = np.where(
            state > 0,
            spec.long_short_balance,
            np.where(state < 0, -(1.0 - spec.long_short_balance), 0.0),
        )
        change_events[i] = changed

    raw = pd.DataFrame(raw_values, index=close.index, columns=close.columns)
    vol = _hourly_vol(close, spec.vol_lookback)
    scaled = _risk_scale(raw, vol, spec.vol_target, spec.leverage_cap)
    event_mask = pd.DataFrame(
        np.broadcast_to(change_events[:, None], scaled.shape),
        index=scaled.index,
        columns=scaled.columns,
    )
    return scaled.where(event_mask).ffill().fillna(0.0)


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
    if spec.family == "impulse":
        return impulse_breakout(data, spec)
    raise ValueError(f"família desconhecida: {spec.family}")
