from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DirectionAllocatorSpec:
    market_symbol: str = "BTCUSDT"
    trend_ema_hours: int = 336
    confirmation_return_hours: int = 168
    bull_long_multiplier: float = 1.6
    bull_short_multiplier: float = 0.4
    bear_long_multiplier: float = 0.4
    bear_short_multiplier: float = 1.6
    neutral_long_multiplier: float = 1.0
    neutral_short_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.trend_ema_hours <= 1 or self.confirmation_return_hours <= 0:
            raise ValueError("direction lookbacks must be positive")
        values = (
            self.bull_long_multiplier,
            self.bull_short_multiplier,
            self.bear_long_multiplier,
            self.bear_short_multiplier,
            self.neutral_long_multiplier,
            self.neutral_short_multiplier,
        )
        if any(value < 0.0 or value > 2.0 for value in values):
            raise ValueError("direction multipliers must stay between zero and two")


def adaptive_directional_targets(
    targets: pd.DataFrame,
    market_close: pd.Series,
    spec: DirectionAllocatorSpec,
) -> tuple[pd.DataFrame, pd.Series]:
    """Scale long and short opportunity targets with a causal market regime.

    The close at hour ``t`` may only change a target executed at the following
    open by the backtest engine. No future price or centered window is used.
    """

    market_close = market_close.reindex(targets.index)
    center = market_close.ewm(
        span=spec.trend_ema_hours,
        adjust=False,
        min_periods=spec.trend_ema_hours,
    ).mean()
    confirmation = market_close.div(
        market_close.shift(spec.confirmation_return_hours)
    ).sub(1.0)
    bull = (market_close > center) & (confirmation > 0.0)
    bear = (market_close < center) & (confirmation < 0.0)
    regime = pd.Series("neutral", index=targets.index, dtype="object")
    regime.loc[bull] = "bull"
    regime.loc[bear] = "bear"

    long_multiplier = pd.Series(spec.neutral_long_multiplier, index=targets.index)
    short_multiplier = pd.Series(spec.neutral_short_multiplier, index=targets.index)
    long_multiplier.loc[bull] = spec.bull_long_multiplier
    short_multiplier.loc[bull] = spec.bull_short_multiplier
    long_multiplier.loc[bear] = spec.bear_long_multiplier
    short_multiplier.loc[bear] = spec.bear_short_multiplier

    longs = targets.clip(lower=0.0).mul(long_multiplier, axis=0)
    shorts = targets.clip(upper=0.0).mul(short_multiplier, axis=0)
    return longs.add(shorts, fill_value=0.0), regime


def apply_eligibility_boundaries(
    targets: pd.DataFrame,
    eligible_after: dict[str, pd.Timestamp | str],
) -> pd.DataFrame:
    """Prevent a newly discovered contract from changing earlier decisions."""

    safe = targets.copy()
    for symbol, boundary in eligible_after.items():
        if symbol not in safe.columns:
            continue
        timestamp = pd.Timestamp(boundary)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        safe.loc[safe.index < timestamp, symbol] = 0.0
    return safe
