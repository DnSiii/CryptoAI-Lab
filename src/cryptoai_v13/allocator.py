from __future__ import annotations

import numpy as np
import pandas as pd


def multihorizon_two_sleeve_targets(
    funding_targets: pd.DataFrame,
    regime_targets: pd.DataFrame,
    funding_returns: pd.Series,
    regime_returns: pd.Series,
    windows_days: tuple[int, ...] = (60, 90, 120, 150),
    funding_weight_when_leading: float = 0.85,
    funding_weight_when_lagging: float = 0.35,
    rebalance_hours: int = 24,
    phase: int = 0,
) -> pd.DataFrame:
    """Allocate between carry and directional regime using only closed returns.

    Each horizon votes independently. Averaging the votes removes dependence on
    one sharp lookback boundary while keeping a persistent carry allocation.
    """
    funding_weights = []
    for days in windows_days:
        lookback = days * 24
        min_periods = lookback // 2
        fund_mean = funding_returns.rolling(lookback, min_periods=min_periods).mean()
        fund_std = funding_returns.rolling(lookback, min_periods=min_periods).std().replace(0.0, np.nan)
        regime_mean = regime_returns.rolling(lookback, min_periods=min_periods).mean()
        regime_std = regime_returns.rolling(lookback, min_periods=min_periods).std().replace(0.0, np.nan)
        fund_score = fund_mean.div(fund_std)
        regime_score = regime_mean.div(regime_std)
        weights = pd.Series(
            np.where(fund_score > regime_score,
                     funding_weight_when_leading, funding_weight_when_lagging),
            index=funding_targets.index,
            dtype=float,
        )
        event = pd.Series(
            (np.arange(len(weights)) - phase) % rebalance_hours == 0,
            index=weights.index,
        )
        funding_weights.append(weights.where(event, np.nan).ffill().fillna(0.5))
    funding_weight = sum(funding_weights) / len(funding_weights)
    return funding_targets.mul(funding_weight, axis=0).add(
        regime_targets.mul(1.0 - funding_weight, axis=0), fill_value=0.0)


def convex_equity_overlay(targets: pd.DataFrame, proxy_equity: pd.Series,
                          short_hours: int, long_hours: int,
                          drawdown_hours: int, drawdown_threshold: float,
                          winner_multiplier: float, loser_multiplier: float,
                          drawdown_multiplier: float, rebalance_hours: int = 24,
                          phase: int = 0, maximum_gross: float = 1.5) -> pd.DataFrame:
    """Causal risk-on/risk-off overlay based on a sleeve's own equity curve.

    State observed at close ``t`` affects the target decided at ``t`` and thus
    executes no earlier than the next open in the replay. Winners can be
    pyramided while weak or underwater states cut exposure.
    """
    short_return = proxy_equity.div(proxy_equity.shift(short_hours)).sub(1.0)
    long_return = proxy_equity.div(proxy_equity.shift(long_hours)).sub(1.0)
    rolling_peak = proxy_equity.rolling(
        drawdown_hours, min_periods=max(24 * 7, drawdown_hours // 3)).max()
    drawdown = proxy_equity.div(rolling_peak).sub(1.0)
    factor = pd.Series(1.0, index=targets.index)
    factor.loc[(short_return > 0.0) & (long_return > 0.0)] = winner_multiplier
    factor.loc[(short_return < 0.0) & (long_return < 0.0)] = loser_multiplier
    underwater = drawdown <= -abs(drawdown_threshold)
    factor.loc[underwater] = np.minimum(factor.loc[underwater], drawdown_multiplier)
    event = pd.Series((np.arange(len(factor)) - phase) % rebalance_hours == 0,
                      index=factor.index)
    factor = factor.where(event, np.nan).ffill().fillna(0.0)
    overlaid = targets.mul(factor, axis=0)
    gross = overlaid.abs().sum(axis=1)
    cap = (maximum_gross / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return overlaid.mul(cap, axis=0)


def trailing_stop_overlay(targets: pd.DataFrame, close: pd.DataFrame,
                          stop_fraction: float, cooldown_hours: int) -> pd.DataFrame:
    """Apply close-confirmed per-asset trailing stops without future data.

    A stopped target becomes zero at close ``t`` and is executed by the engine
    at the next open. Re-entry requires the configured cooldown or a reversal
    of the underlying signal. This deliberately avoids assuming an ideal
    intrabar stop fill from OHLC data.
    """
    targets = targets.reindex(index=close.index, columns=close.columns).fillna(0.0)
    output = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    for column in targets.columns:
        prices = close[column].to_numpy(dtype=float)
        desired = targets[column].to_numpy(dtype=float)
        actual = np.zeros(len(targets), dtype=float)
        active_sign = 0.0
        extreme = np.nan
        blocked_until = -1
        blocked_sign = 0.0
        for i, (price, weight) in enumerate(zip(prices, desired)):
            sign = float(np.sign(weight))
            if not np.isfinite(price) or sign == 0.0:
                active_sign = 0.0
                extreme = np.nan
                if sign == 0.0:
                    blocked_until = -1
                    blocked_sign = 0.0
                continue
            if blocked_until >= i and sign == blocked_sign:
                continue
            if sign != blocked_sign:
                blocked_until = -1
                blocked_sign = 0.0
            if active_sign != sign:
                active_sign = sign
                extreme = price
            if sign > 0:
                extreme = max(extreme, price)
                stopped = price <= extreme * (1.0 - stop_fraction)
            else:
                extreme = min(extreme, price)
                stopped = price >= extreme * (1.0 + stop_fraction)
            if stopped:
                blocked_until = i + cooldown_hours
                blocked_sign = sign
                active_sign = 0.0
                extreme = np.nan
                continue
            actual[i] = weight
        output[column] = actual
    return output
