from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class V99R65Spec:
    """Causal all-regime alpha layer for the V99 research track.

    The module intentionally leaves the frozen V99 and its paper runner untouched.
    It transforms an already-causal parent target stream using only information
    available at close t; execution remains open t+1 in the existing replay.

    R65 has three explicit jobs instead of acting only as a defensive overlay:
    1. trend capture in both directions (bull and bear),
    2. market-direction overlay when broad evidence confirms the trend,
    3. market-neutral cross-sectional mean reversion during lateral regimes.
    """

    market_symbol: str = "BTCUSDT"
    trend_hours: int = 72
    trend_efficiency_floor: float = 0.34
    trend_sigma_floor: float = 0.90
    bull_breadth_floor: float = 0.58
    bear_breadth_ceiling: float = 0.42
    regime_confirmation_hours: int = 6

    lateral_efficiency_ceiling: float = 0.28
    lateral_sigma_ceiling: float = 0.65
    lateral_breadth_low: float = 0.38
    lateral_breadth_high: float = 0.62
    lateral_signal_hours: int = 6
    lateral_rebalance_hours: int = 6
    lateral_min_dispersion: float = 0.010

    volatility_short_hours: int = 24
    volatility_long_hours: int = 24 * 30
    high_vol_ratio: float = 1.40
    high_vol_trend_multiplier: float = 1.10

    aligned_trend_boost: float = 1.15
    bull_market_overlay: float = 0.12
    bear_market_overlay: float = 0.18
    lateral_gross: float = 0.20
    maximum_gross: float = 1.90

    def __post_init__(self) -> None:
        positive_ints = (
            self.trend_hours,
            self.regime_confirmation_hours,
            self.lateral_signal_hours,
            self.lateral_rebalance_hours,
            self.volatility_short_hours,
            self.volatility_long_hours,
        )
        if min(positive_ints) <= 0:
            raise ValueError("R65 lookbacks and cadence must be positive")
        if self.volatility_short_hours >= self.volatility_long_hours:
            raise ValueError("short volatility horizon must be below long horizon")
        if not 0.5 < self.bull_breadth_floor < 1.0:
            raise ValueError("bull breadth floor must exceed one half")
        if not 0.0 < self.bear_breadth_ceiling < 0.5:
            raise ValueError("bear breadth ceiling must be below one half")
        if not 0.0 < self.lateral_breadth_low < self.lateral_breadth_high < 1.0:
            raise ValueError("invalid lateral breadth band")
        if not 1.0 <= self.aligned_trend_boost <= 1.50:
            raise ValueError("aligned trend boost outside research safety envelope")
        if min(self.bull_market_overlay, self.bear_market_overlay, self.lateral_gross) < 0.0:
            raise ValueError("overlay sizes cannot be negative")
        if self.maximum_gross <= 0.0:
            raise ValueError("maximum gross must be positive")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cap_gross(targets: pd.DataFrame, maximum_gross: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (maximum_gross / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0).fillna(0.0)


def _breadth(close: pd.DataFrame, hours: int) -> pd.Series:
    move = close.div(close.shift(hours)).sub(1.0)
    valid = move.notna()
    denominator = valid.sum(axis=1).replace(0, np.nan)
    return move.gt(0.0).where(valid, False).sum(axis=1).div(denominator)


def _efficiency_ratio(price: pd.Series, hours: int) -> pd.Series:
    one_hour = price.pct_change(fill_method=None)
    progress = price.div(price.shift(hours)).sub(1.0).abs()
    path = one_hour.abs().rolling(hours, min_periods=max(12, hours // 3)).sum()
    return progress.div(path.replace(0.0, np.nan)).clip(lower=0.0, upper=1.0)


def causal_regimes(close: pd.DataFrame, spec: V99R65Spec) -> pd.DataFrame:
    if spec.market_symbol not in close.columns:
        raise ValueError(f"R65 market symbol {spec.market_symbol} is unavailable")
    market = close[spec.market_symbol].astype(float)
    market_return = market.div(market.shift(spec.trend_hours)).sub(1.0)
    hourly = market.pct_change(fill_method=None)
    trend_vol = hourly.rolling(
        spec.trend_hours,
        min_periods=max(24, spec.trend_hours // 3),
    ).std().mul(np.sqrt(spec.trend_hours))
    normalized_trend = market_return.div(trend_vol.replace(0.0, np.nan))
    efficiency = _efficiency_ratio(market, spec.trend_hours)
    breadth = _breadth(close, spec.trend_hours)

    bull_raw = (
        normalized_trend.ge(spec.trend_sigma_floor)
        & efficiency.ge(spec.trend_efficiency_floor)
        & breadth.ge(spec.bull_breadth_floor)
    ).fillna(False)
    bear_raw = (
        normalized_trend.le(-spec.trend_sigma_floor)
        & efficiency.ge(spec.trend_efficiency_floor)
        & breadth.le(spec.bear_breadth_ceiling)
    ).fillna(False)
    lateral_raw = (
        normalized_trend.abs().le(spec.lateral_sigma_ceiling)
        & efficiency.le(spec.lateral_efficiency_ceiling)
        & breadth.between(spec.lateral_breadth_low, spec.lateral_breadth_high)
        & ~bull_raw
        & ~bear_raw
    ).fillna(False)

    confirm = int(spec.regime_confirmation_hours)
    bull = bull_raw.astype(float).rolling(confirm, min_periods=1).mean().ge(2.0 / 3.0)
    bear = bear_raw.astype(float).rolling(confirm, min_periods=1).mean().ge(2.0 / 3.0)
    lateral = lateral_raw.astype(float).rolling(confirm, min_periods=1).mean().ge(2.0 / 3.0)
    lateral &= ~bull & ~bear

    short_vol = hourly.rolling(
        spec.volatility_short_hours,
        min_periods=max(8, spec.volatility_short_hours // 3),
    ).std()
    long_vol = hourly.rolling(
        spec.volatility_long_hours,
        min_periods=max(24 * 7, spec.volatility_long_hours // 3),
    ).std()
    volatility_ratio = short_vol.div(long_vol.replace(0.0, np.nan))
    high_vol = volatility_ratio.ge(spec.high_vol_ratio).fillna(False)

    regime = pd.Series("neutral", index=close.index, dtype="object")
    regime.loc[lateral] = "lateral"
    regime.loc[bull] = "bull"
    regime.loc[bear] = "bear"
    return pd.DataFrame(
        {
            "regime": regime,
            "bull": bull,
            "bear": bear,
            "lateral": lateral,
            "high_vol": high_vol,
            "market_return": market_return,
            "normalized_trend": normalized_trend,
            "efficiency": efficiency,
            "breadth": breadth,
            "volatility_ratio": volatility_ratio,
        },
        index=close.index,
    )


def lateral_mean_reversion_sleeve(
    close: pd.DataFrame,
    regime: pd.DataFrame,
    spec: V99R65Spec,
) -> pd.DataFrame:
    signal_return = close.pct_change(spec.lateral_signal_hours, fill_method=None)
    cross_median = signal_return.median(axis=1)
    excess = signal_return.sub(cross_median, axis=0)
    dispersion = excess.std(axis=1, ddof=0)

    ranks = excess.rank(axis=1, method="average", pct=True)
    raw = (0.5 - ranks).where(excess.notna(), 0.0)
    raw = raw.sub(raw.mean(axis=1), axis=0)
    gross = raw.abs().sum(axis=1).replace(0.0, np.nan)
    sleeve = raw.div(gross, axis=0).mul(float(spec.lateral_gross)).fillna(0.0)

    active = regime["lateral"].fillna(False) & dispersion.ge(spec.lateral_min_dispersion)
    sleeve = sleeve.where(active, 0.0)

    cadence = np.arange(len(sleeve)) % int(spec.lateral_rebalance_hours) == 0
    rebalance = pd.Series(cadence, index=sleeve.index) & active
    sleeve = sleeve.where(rebalance).ffill(limit=max(0, int(spec.lateral_rebalance_hours) - 1)).fillna(0.0)
    sleeve = sleeve.where(active, 0.0)
    return sleeve


def all_regime_targets(
    close: pd.DataFrame,
    parent_targets: pd.DataFrame,
    spec: V99R65Spec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = parent_targets.reindex(index=close.index, columns=close.columns).fillna(0.0)
    regime = causal_regimes(close, spec)
    lateral = lateral_mean_reversion_sleeve(close, regime, spec)

    out = raw.copy()
    bull = regime["bull"].fillna(False)
    bear = regime["bear"].fillna(False)
    high_vol = regime["high_vol"].fillna(False)

    bull_multiplier = pd.Series(1.0, index=out.index)
    bear_multiplier = pd.Series(1.0, index=out.index)
    bull_multiplier.loc[bull] = float(spec.aligned_trend_boost)
    bear_multiplier.loc[bear] = float(spec.aligned_trend_boost)
    hv_bull = bull & high_vol
    hv_bear = bear & high_vol
    bull_multiplier.loc[hv_bull] *= float(spec.high_vol_trend_multiplier)
    bear_multiplier.loc[hv_bear] *= float(spec.high_vol_trend_multiplier)

    positive = out.clip(lower=0.0).mul(bull_multiplier, axis=0)
    negative = out.clip(upper=0.0).mul(bear_multiplier, axis=0)
    unchanged_positive = out.clip(lower=0.0).where(~bull, 0.0)
    unchanged_negative = out.clip(upper=0.0).where(~bear, 0.0)

    transformed = out.copy()
    if bull.any():
        transformed.loc[bull] = positive.loc[bull] + out.clip(upper=0.0).loc[bull]
    if bear.any():
        transformed.loc[bear] = negative.loc[bear] + out.clip(lower=0.0).loc[bear]

    # Explicit directional market alpha. It is symmetric in concept but the
    # bear sleeve is intentionally allowed a larger budget because the audit
    # showed the historical stack was materially weaker in falling markets.
    if spec.market_symbol not in transformed.columns:
        raise ValueError(f"R65 market symbol {spec.market_symbol} missing from targets")
    transformed.loc[bull, spec.market_symbol] += float(spec.bull_market_overlay)
    transformed.loc[bear, spec.market_symbol] -= float(spec.bear_market_overlay)

    transformed = transformed.add(lateral, fill_value=0.0)
    transformed = _cap_gross(transformed, spec.maximum_gross)

    diagnostics = regime.copy()
    diagnostics["parent_gross"] = raw.abs().sum(axis=1)
    diagnostics["lateral_gross"] = lateral.abs().sum(axis=1)
    diagnostics["transformed_gross"] = transformed.abs().sum(axis=1)
    diagnostics["parent_net"] = raw.sum(axis=1)
    diagnostics["transformed_net"] = transformed.sum(axis=1)
    diagnostics["bull_overlay"] = bull.astype(float) * float(spec.bull_market_overlay)
    diagnostics["bear_overlay"] = bear.astype(float) * float(spec.bear_market_overlay)
    return transformed, diagnostics
