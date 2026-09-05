from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import FuturesData


@dataclass(frozen=True)
class V99AsymmetricSpec:
    """Causal asymmetric risk/opportunity overlay for the V99 research track.

    The design targets the failure modes observed across V13/V14/V15 without
    turning every adverse move into a permanent low-risk state:

    * market stress cuts gross exposure when broad damage accelerates;
    * chop detection reduces trading when price travels but makes no progress;
    * portfolio damage control reacts when many active positions fail together;
    * extension guard blocks *new/increased* exposure into exhausted moves;
    * clean-trend confirmation restores risk quickly and may modestly boost
      aligned exposure while the market remains broad and directional.

    Every input is derived from data closed at timestamp t. The returned target
    at t therefore remains eligible only for the existing close-t/open-t+1
    execution convention used by the replay engine.
    """

    market_symbol: str = "BTCUSDT"

    stress_short_hours: int = 6
    stress_medium_hours: int = 24
    stress_breadth_hours: int = 12
    stress_short_return: float = -0.03
    stress_medium_return: float = -0.06
    stress_breadth: float = 0.30
    volatility_short_hours: int = 24
    volatility_long_hours: int = 24 * 14
    volatility_spike_ratio: float = 1.75
    stress_one_multiplier: float = 0.72
    stress_two_multiplier: float = 0.45
    stress_three_multiplier: float = 0.22

    chop_hours: int = 24
    chop_efficiency_threshold: float = 0.20
    chop_absolute_return: float = 0.02
    chop_breadth_low: float = 0.42
    chop_breadth_high: float = 0.58
    chop_multiplier: float = 0.65

    damage_smoothing_hours: int = 3
    damage_return_hours: int = 6
    damage_soft_fraction: float = 0.60
    damage_hard_fraction: float = 0.75
    damage_soft_return: float = -0.01
    damage_hard_return: float = -0.02
    damage_soft_multiplier: float = 0.65
    damage_hard_multiplier: float = 0.35
    active_weight_floor: float = 0.01

    extension_hours: int = 24
    extension_volatility_hours: int = 24 * 7
    extension_sigma: float = 2.75

    confirmation_hours: int = 24
    confirmation_return: float = 0.025
    confirmation_efficiency: float = 0.45
    confirmation_breadth: float = 0.62
    clean_trend_boost: float = 1.10

    recovery_step: float = 0.20
    confirmed_reentry_step: float = 0.50
    maximum_gross: float = 1.85

    def __post_init__(self) -> None:
        positive_ints = (
            self.stress_short_hours,
            self.stress_medium_hours,
            self.stress_breadth_hours,
            self.volatility_short_hours,
            self.volatility_long_hours,
            self.chop_hours,
            self.damage_smoothing_hours,
            self.damage_return_hours,
            self.extension_hours,
            self.extension_volatility_hours,
            self.confirmation_hours,
        )
        if min(positive_ints) <= 0:
            raise ValueError("V99 lookbacks must be positive")
        if self.stress_short_hours >= self.stress_medium_hours:
            raise ValueError("stress short horizon must be below medium horizon")
        if self.volatility_short_hours >= self.volatility_long_hours:
            raise ValueError("volatility short horizon must be below long horizon")
        if not 0.0 < self.stress_breadth < 0.5:
            raise ValueError("stress breadth must be below one half")
        if not 0.0 < self.chop_breadth_low < self.chop_breadth_high < 1.0:
            raise ValueError("invalid chop breadth band")
        if not 0.5 <= self.damage_soft_fraction < self.damage_hard_fraction <= 1.0:
            raise ValueError("invalid damage fractions")
        if not 0.5 < self.confirmation_breadth < 1.0:
            raise ValueError("confirmation breadth must exceed one half")
        multipliers = (
            self.stress_one_multiplier,
            self.stress_two_multiplier,
            self.stress_three_multiplier,
            self.chop_multiplier,
            self.damage_soft_multiplier,
            self.damage_hard_multiplier,
        )
        if any(not 0.0 <= value <= 1.0 for value in multipliers):
            raise ValueError("defensive multipliers must be within zero and one")
        if not (
            self.stress_three_multiplier
            <= self.stress_two_multiplier
            <= self.stress_one_multiplier
            <= 1.0
        ):
            raise ValueError("stress multipliers must become more defensive")
        if not 1.0 <= self.clean_trend_boost <= 1.25:
            raise ValueError("clean trend boost must be between one and 1.25")
        if not 0.0 < self.recovery_step <= 1.0:
            raise ValueError("recovery step must be within zero and one")
        if not self.recovery_step <= self.confirmed_reentry_step <= 1.0:
            raise ValueError("confirmed re-entry must be at least as fast as recovery")
        if self.maximum_gross <= 0.0 or self.extension_sigma <= 0.0:
            raise ValueError("gross and extension sigma must be positive")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cap_gross(targets: pd.DataFrame, maximum_gross: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (
        maximum_gross / gross.replace(0.0, np.nan)
    ).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0).fillna(0.0)


def _breadth(close: pd.DataFrame, hours: int) -> pd.Series:
    move = close.div(close.shift(hours)).sub(1.0)
    valid = move.notna()
    denominator = valid.sum(axis=1).replace(0, np.nan)
    return move.gt(0.0).where(valid, False).sum(axis=1).div(denominator)


def _efficiency_ratio(price: pd.Series, hours: int) -> pd.Series:
    one_hour = price.pct_change()
    progress = price.div(price.shift(hours)).sub(1.0).abs()
    path = one_hour.abs().rolling(
        hours,
        min_periods=max(3, hours // 3),
    ).sum()
    return progress.div(path.replace(0.0, np.nan)).clip(lower=0.0, upper=1.0)


def _stress_factor(
    market: pd.Series,
    close: pd.DataFrame,
    spec: V99AsymmetricSpec,
) -> tuple[pd.Series, pd.DataFrame]:
    short_return = market.div(market.shift(spec.stress_short_hours)).sub(1.0)
    medium_return = market.div(market.shift(spec.stress_medium_hours)).sub(1.0)
    breadth = _breadth(close, spec.stress_breadth_hours)
    hourly_return = market.pct_change()
    short_volatility = hourly_return.rolling(
        spec.volatility_short_hours,
        min_periods=max(6, spec.volatility_short_hours // 3),
    ).std()
    long_volatility = hourly_return.rolling(
        spec.volatility_long_hours,
        min_periods=max(24, spec.volatility_long_hours // 3),
    ).std()
    volatility_ratio = short_volatility.div(long_volatility.replace(0.0, np.nan))

    score = (
        short_return.le(spec.stress_short_return).astype(int)
        + medium_return.le(spec.stress_medium_return).astype(int)
        + breadth.le(spec.stress_breadth).astype(int)
        + volatility_ratio.ge(spec.volatility_spike_ratio).astype(int)
    )
    factor = pd.Series(1.0, index=market.index)
    factor.loc[score.eq(1)] = spec.stress_one_multiplier
    factor.loc[score.eq(2)] = spec.stress_two_multiplier
    factor.loc[score.ge(3)] = spec.stress_three_multiplier
    diagnostics = pd.DataFrame(
        {
            "stress_short_return": short_return,
            "stress_medium_return": medium_return,
            "stress_breadth": breadth,
            "volatility_ratio": volatility_ratio,
            "stress_score": score,
            "stress_factor": factor,
        },
        index=market.index,
    )
    return factor, diagnostics


def _chop_factor(
    market: pd.Series,
    close: pd.DataFrame,
    spec: V99AsymmetricSpec,
) -> tuple[pd.Series, pd.DataFrame]:
    efficiency = _efficiency_ratio(market, spec.chop_hours)
    market_return = market.div(market.shift(spec.chop_hours)).sub(1.0)
    breadth = _breadth(close, spec.chop_hours)
    chop = (
        efficiency.le(spec.chop_efficiency_threshold)
        & market_return.abs().le(spec.chop_absolute_return)
        & breadth.between(spec.chop_breadth_low, spec.chop_breadth_high)
    )
    factor = pd.Series(1.0, index=market.index)
    factor.loc[chop] = spec.chop_multiplier
    diagnostics = pd.DataFrame(
        {
            "chop_efficiency": efficiency,
            "chop_market_return": market_return,
            "chop_breadth": breadth,
            "chop_active": chop,
            "chop_factor": factor,
        },
        index=market.index,
    )
    return factor, diagnostics


def _damage_factor(
    close: pd.DataFrame,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
) -> tuple[pd.Series, pd.DataFrame]:
    held = targets.shift(1).fillna(0.0)
    hourly_return = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    signed_return = hourly_return.mul(np.sign(held))
    active = held.abs().ge(spec.active_weight_floor)
    active_count = active.sum(axis=1).replace(0, np.nan)
    losing_count = signed_return.lt(0.0).where(active, False).sum(axis=1)
    loss_fraction = losing_count.div(active_count).fillna(0.0)
    smoothed_loss_fraction = loss_fraction.rolling(
        spec.damage_smoothing_hours,
        min_periods=1,
    ).mean()
    equity = proxy_equity.reindex(targets.index).ffill()
    recent_return = equity.div(equity.shift(spec.damage_return_hours)).sub(1.0)

    hard = (
        smoothed_loss_fraction.ge(spec.damage_hard_fraction)
        & recent_return.le(spec.damage_hard_return)
    )
    soft = (
        smoothed_loss_fraction.ge(spec.damage_soft_fraction)
        & recent_return.le(spec.damage_soft_return)
        & ~hard
    )
    factor = pd.Series(1.0, index=targets.index)
    factor.loc[soft] = spec.damage_soft_multiplier
    factor.loc[hard] = spec.damage_hard_multiplier
    state = pd.Series("normal", index=targets.index, dtype="object")
    state.loc[soft] = "soft"
    state.loc[hard] = "hard"
    diagnostics = pd.DataFrame(
        {
            "active_positions": active.sum(axis=1),
            "loss_fraction": loss_fraction,
            "smoothed_loss_fraction": smoothed_loss_fraction,
            "damage_recent_return": recent_return,
            "damage_state": state,
            "damage_factor": factor,
        },
        index=targets.index,
    )
    return factor, diagnostics


def _clean_trend(
    market: pd.Series,
    close: pd.DataFrame,
    spec: V99AsymmetricSpec,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    market_return = market.div(market.shift(spec.confirmation_hours)).sub(1.0)
    efficiency = _efficiency_ratio(market, spec.confirmation_hours)
    breadth = _breadth(close, spec.confirmation_hours)
    up = (
        market_return.ge(spec.confirmation_return)
        & efficiency.ge(spec.confirmation_efficiency)
        & breadth.ge(spec.confirmation_breadth)
    )
    down = (
        market_return.le(-spec.confirmation_return)
        & efficiency.ge(spec.confirmation_efficiency)
        & breadth.le(1.0 - spec.confirmation_breadth)
    )
    diagnostics = pd.DataFrame(
        {
            "confirmation_return": market_return,
            "confirmation_efficiency": efficiency,
            "confirmation_breadth": breadth,
            "clean_uptrend": up,
            "clean_downtrend": down,
            "clean_trend": up | down,
        },
        index=market.index,
    )
    return up, down, diagnostics


def _extension_guard(
    close: pd.DataFrame,
    targets: pd.DataFrame,
    clean_uptrend: pd.Series,
    clean_downtrend: pd.Series,
    spec: V99AsymmetricSpec,
) -> tuple[pd.DataFrame, pd.Series]:
    move = close.div(close.shift(spec.extension_hours)).sub(1.0)
    hourly_volatility = close.pct_change().rolling(
        spec.extension_volatility_hours,
        min_periods=max(24, spec.extension_volatility_hours // 3),
    ).std()
    horizon_volatility = hourly_volatility.mul(np.sqrt(spec.extension_hours))
    extension_score = move.div(horizon_volatility.replace(0.0, np.nan))

    raw = targets.copy().fillna(0.0)
    guarded = raw.copy()
    blocked_counts = np.zeros(len(raw), dtype=int)
    previous = pd.Series(0.0, index=raw.columns)
    for row in range(len(raw)):
        requested = raw.iloc[row].copy()
        score = extension_score.iloc[row]
        long_block = (
            requested.gt(0.0)
            & score.ge(spec.extension_sigma)
            & (not bool(clean_uptrend.iloc[row]))
        )
        short_block = (
            requested.lt(0.0)
            & score.le(-spec.extension_sigma)
            & (not bool(clean_downtrend.iloc[row]))
        )
        blocked = long_block | short_block
        same_direction = np.sign(previous) == np.sign(requested)
        previous_same_direction = previous.abs().where(same_direction, 0.0)
        growing = requested.abs().gt(previous_same_direction)
        prevent_growth = blocked & growing
        if prevent_growth.any():
            requested.loc[prevent_growth] = (
                np.sign(requested.loc[prevent_growth])
                * previous_same_direction.loc[prevent_growth]
            )
        guarded.iloc[row] = requested
        blocked_counts[row] = int(prevent_growth.sum())
        previous = requested
    return guarded, pd.Series(blocked_counts, index=raw.index, name="extension_blocked_count")


def asymmetric_v99_targets(
    data: FuturesData,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the complete V99 asymmetric overlay to an existing target stream."""

    raw = targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    close = data.close.reindex_like(raw)
    if spec.market_symbol not in close.columns:
        raise ValueError(f"V99 market symbol {spec.market_symbol} is unavailable")
    market = close[spec.market_symbol]

    stress_factor, stress_diag = _stress_factor(market, close, spec)
    chop_factor, chop_diag = _chop_factor(market, close, spec)
    damage_factor, damage_diag = _damage_factor(close, raw, proxy_equity, spec)
    clean_up, clean_down, trend_diag = _clean_trend(market, close, spec)
    extension_guarded, blocked_count = _extension_guard(
        close,
        raw,
        clean_up,
        clean_down,
        spec,
    )

    desired_factor = pd.concat(
        [stress_factor, chop_factor, damage_factor],
        axis=1,
    ).min(axis=1)
    clean = trend_diag["clean_trend"].fillna(False)
    effective = np.ones(len(raw), dtype=float)
    previous = 1.0
    for row in range(len(raw)):
        desired = float(desired_factor.iloc[row])
        if desired < previous:
            current = desired
        elif desired > previous:
            step = (
                spec.confirmed_reentry_step
                if bool(clean.iloc[row])
                else spec.recovery_step
            )
            current = min(desired, previous + step)
        else:
            current = previous
        effective[row] = current
        previous = current
    risk_factor = pd.Series(effective, index=raw.index, name="risk_factor")

    opportunity_factor = pd.Series(1.0, index=raw.index, name="opportunity_factor")
    boost_ready = clean & risk_factor.ge(0.999)
    opportunity_factor.loc[boost_ready] = spec.clean_trend_boost

    boosted = extension_guarded.copy()
    up_rows = clean_up.fillna(False) & risk_factor.ge(0.999)
    down_rows = clean_down.fillna(False) & risk_factor.ge(0.999)
    if up_rows.any():
        up_slice = boosted.loc[up_rows]
        boosted.loc[up_rows] = up_slice.where(
            up_slice.le(0.0),
            up_slice * spec.clean_trend_boost,
        )
    if down_rows.any():
        down_slice = boosted.loc[down_rows]
        boosted.loc[down_rows] = down_slice.where(
            down_slice.ge(0.0),
            down_slice * spec.clean_trend_boost,
        )

    transformed = boosted.mul(risk_factor, axis=0)
    transformed = _cap_gross(transformed, spec.maximum_gross)

    diagnostics = pd.concat(
        [
            stress_diag,
            chop_diag,
            damage_diag,
            trend_diag,
            blocked_count,
            desired_factor.rename("desired_risk_factor"),
            risk_factor,
            opportunity_factor,
            transformed.abs().sum(axis=1).rename("gross"),
        ],
        axis=1,
    )
    return transformed, diagnostics
