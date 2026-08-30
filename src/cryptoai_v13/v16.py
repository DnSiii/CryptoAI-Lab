from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import FuturesData
from .signals import StrategySpec, build_targets


@dataclass(frozen=True)
class ConvexCaptureSpec:
    """Causal multi-speed directional capture for the V16 research gate.

    V16 deliberately does not inherit the permanent BTC/ETH concentration of
    V14/V15.  It blends two independently stopped impulse horizons with a
    slower trend sleeve, then scales direction from BTC *and* market breadth.
    Every input is known at close t and can execute only at open t+1.
    """

    fast_lookback: int = 24
    slow_lookback: int = 72
    rebalance_hours: int = 3
    top_n: int = 2
    fast_threshold: float = 0.0125
    slow_threshold: float = 0.025
    fast_volume_multiple: float = 1.5
    slow_volume_multiple: float = 1.25
    volume_fast_hours: int = 12
    volume_baseline_hours: int = 168
    volatility_lookback_hours: int = 168
    signal_volatility_target: float = 0.90
    sleeve_leverage_cap: float = 1.25
    trend_fast_hours: int = 24
    trend_slow_hours: int = 336
    trend_threshold: float = 0.004
    stop_loss: float = 0.03
    trailing_stop: float = 0.14
    fast_max_holding_hours: int = 96
    slow_max_holding_hours: int = 240
    cooldown_hours: int = 12
    fast_weight: float = 0.45
    slow_weight: float = 0.35
    trend_weight: float = 0.20
    breadth_lookback_hours: int = 72
    bull_breadth: float = 0.58
    bear_breadth: float = 0.42
    aligned_multiplier: float = 1.35
    countertrend_multiplier: float = 0.35
    neutral_multiplier: float = 0.70
    minimum_conviction: float = 0.55
    maximum_conviction: float = 1.45

    def __post_init__(self) -> None:
        if self.fast_lookback <= 1 or self.slow_lookback <= self.fast_lookback:
            raise ValueError("slow_lookback must exceed fast_lookback")
        if self.top_n <= 0 or self.rebalance_hours <= 0:
            raise ValueError("top_n and rebalance_hours must be positive")
        if not np.isclose(
            self.fast_weight + self.slow_weight + self.trend_weight, 1.0
        ):
            raise ValueError("V16 sleeve weights must sum to one")
        if not 0.0 < self.bear_breadth < self.bull_breadth < 1.0:
            raise ValueError("invalid breadth boundaries")
        if not 0.0 <= self.countertrend_multiplier <= self.aligned_multiplier:
            raise ValueError("invalid direction multipliers")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cap_gross(targets: pd.DataFrame, maximum_gross: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (
        maximum_gross / gross.replace(0.0, np.nan)
    ).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0).fillna(0.0)


def _impulse_spec(spec: ConvexCaptureSpec, *, slow: bool) -> StrategySpec:
    return StrategySpec(
        family="impulse",
        lookback=spec.slow_lookback if slow else spec.fast_lookback,
        rebalance=spec.rebalance_hours,
        top_n=spec.top_n,
        fast=spec.volume_fast_hours,
        slow=spec.volume_baseline_hours,
        vol_lookback=spec.volatility_lookback_hours,
        vol_target=spec.signal_volatility_target,
        leverage_cap=spec.sleeve_leverage_cap,
        long_short_balance=0.5,
        threshold=spec.slow_threshold if slow else spec.fast_threshold,
        volume_multiple=(
            spec.slow_volume_multiple if slow else spec.fast_volume_multiple
        ),
        stop_loss=spec.stop_loss,
        trailing_stop=spec.trailing_stop,
        max_holding=(
            spec.slow_max_holding_hours if slow else spec.fast_max_holding_hours
        ),
        trend_filter_hours=spec.trend_slow_hours,
        cooldown_hours=spec.cooldown_hours,
    )


def convex_capture_targets(
    data: FuturesData,
    spec: ConvexCaptureSpec,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Return V16 opportunity targets, regime labels and diagnostics."""

    fast = build_targets(data, _impulse_spec(spec, slow=False))
    slow = build_targets(data, _impulse_spec(spec, slow=True))
    trend = build_targets(
        data,
        StrategySpec(
            family="trend",
            lookback=spec.slow_lookback,
            rebalance=max(3, spec.rebalance_hours),
            fast=spec.trend_fast_hours,
            slow=spec.trend_slow_hours,
            vol_lookback=spec.volatility_lookback_hours,
            vol_target=spec.signal_volatility_target,
            leverage_cap=spec.sleeve_leverage_cap,
            threshold=spec.trend_threshold,
        ),
    )
    blended = (
        fast * spec.fast_weight
        + slow * spec.slow_weight
        + trend * spec.trend_weight
    )

    close = data.close
    btc = close["BTCUSDT"]
    btc_fast = btc.ewm(
        span=spec.trend_fast_hours,
        adjust=False,
        min_periods=spec.trend_fast_hours,
    ).mean()
    btc_slow = btc.ewm(
        span=spec.trend_slow_hours,
        adjust=False,
        min_periods=spec.trend_slow_hours,
    ).mean()
    asset_return = close.div(close.shift(spec.breadth_lookback_hours)).sub(1.0)
    breadth = (asset_return > 0.0).where(close.notna()).mean(axis=1)
    bull = (btc_fast > btc_slow) & (breadth >= spec.bull_breadth)
    bear = (btc_fast < btc_slow) & (breadth <= spec.bear_breadth)
    regime = pd.Series("neutral", index=close.index, dtype="object")
    regime.loc[bull] = "bull"
    regime.loc[bear] = "bear"

    long_factor = pd.Series(spec.neutral_multiplier, index=close.index)
    short_factor = pd.Series(spec.neutral_multiplier, index=close.index)
    long_factor.loc[bull] = spec.aligned_multiplier
    short_factor.loc[bull] = spec.countertrend_multiplier
    long_factor.loc[bear] = spec.countertrend_multiplier
    short_factor.loc[bear] = spec.aligned_multiplier

    market_strength = btc_fast.div(btc_slow).sub(1.0).abs()
    breadth_strength = breadth.sub(0.5).abs().mul(2.0)
    conviction = (
        0.55
        + market_strength.div(0.08).clip(0.0, 1.0) * 0.50
        + breadth_strength.clip(0.0, 1.0) * 0.40
    ).clip(spec.minimum_conviction, spec.maximum_conviction)
    directed = (
        blended.clip(lower=0.0).mul(long_factor, axis=0)
        + blended.clip(upper=0.0).mul(short_factor, axis=0)
    ).mul(conviction, axis=0)
    targets = _cap_gross(directed, spec.sleeve_leverage_cap)
    diagnostics = pd.DataFrame(
        {
            "breadth": breadth,
            "market_strength": market_strength,
            "conviction": conviction,
            "opportunity_gross": targets.abs().sum(axis=1),
        },
        index=close.index,
    )
    return targets, regime, diagnostics


def combine_convex_with_core(
    core_targets: pd.DataFrame,
    opportunity_targets: pd.DataFrame,
    *,
    core_fraction: float,
    maximum_portfolio_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Allocate V16 without forcing the old core to dominate every regime."""

    if not 0.0 <= core_fraction <= 1.0:
        raise ValueError("core_fraction must be between zero and one")
    if maximum_portfolio_gross <= 0.0:
        raise ValueError("maximum_portfolio_gross must be positive")
    core = core_targets.mul(core_fraction).fillna(0.0)
    opportunity = opportunity_targets.reindex_like(core).fillna(0.0)
    core_gross = core.abs().sum(axis=1)
    if bool((core_gross > maximum_portfolio_gross + 1e-12).any()):
        raise ValueError("scaled core exceeds the V16 gross limit")
    spare = (maximum_portfolio_gross - core_gross).clip(lower=0.0)
    requested = opportunity.abs().sum(axis=1)
    scale = (spare / requested.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    allocated = opportunity.mul(scale, axis=0)
    combined = core.add(allocated, fill_value=0.0)
    if bool((combined.abs().sum(axis=1) > maximum_portfolio_gross + 1e-10).any()):
        raise AssertionError("V16 exceeded maximum_portfolio_gross")
    return combined, allocated
