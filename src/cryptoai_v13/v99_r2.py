from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import FuturesData
from .v99 import (
    V99AsymmetricSpec,
    _breadth,
    _cap_gross,
    _clean_trend,
    _efficiency_ratio,
)


@dataclass(frozen=True)
class V99R2ControlSpec:
    """Structural corrections derived from the first V99 failure analysis.

    R2 deliberately separates *risk reduction* from *entry suppression*:
    broad/choppy conditions alone may stop new risk from being added, but an
    existing winner is not repeatedly resized. Gross risk is cut only when
    market price damage is confirmed by breadth/volatility or when the active
    portfolio is failing together.
    """

    extreme_breadth: float = 0.15
    neutral_recovery_hours: int = 3

    def __post_init__(self) -> None:
        if not 0.0 < self.extreme_breadth < 0.5:
            raise ValueError("extreme breadth must be between zero and one half")
        if self.neutral_recovery_hours <= 0:
            raise ValueError("neutral recovery hours must be positive")


def _stress_factor_r2(
    market: pd.Series,
    close: pd.DataFrame,
    spec: V99AsymmetricSpec,
    control: V99R2ControlSpec,
) -> tuple[pd.Series, pd.DataFrame]:
    """Require actual price damage before breadth/volatility can cut gross risk.

    R1 treated weak breadth by itself as stress. On the historical replay that
    fired in roughly two fifths of all hours and created excessive resizing.
    R2 uses breadth and volatility as *confirmation* of falling market price,
    never as a standalone reason to slash existing exposure.
    """

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

    short_down = short_return.le(spec.stress_short_return)
    medium_down = medium_return.le(spec.stress_medium_return)
    breadth_weak = breadth.le(spec.stress_breadth)
    breadth_extreme = breadth.le(control.extreme_breadth)
    volatility_spike = volatility_ratio.ge(spec.volatility_spike_ratio)
    price_damage = short_down | medium_down

    confirmed = price_damage & (breadth_weak | volatility_spike)
    severe = (
        (short_down & medium_down & (breadth_weak | volatility_spike))
        | (price_damage & breadth_extreme & volatility_spike)
    )
    crisis = short_down & medium_down & breadth_extreme & volatility_spike

    factor = pd.Series(1.0, index=market.index)
    factor.loc[confirmed] = spec.stress_one_multiplier
    factor.loc[severe] = spec.stress_two_multiplier
    factor.loc[crisis] = spec.stress_three_multiplier

    severity = pd.Series(0, index=market.index, dtype="int64")
    severity.loc[confirmed] = 1
    severity.loc[severe] = 2
    severity.loc[crisis] = 3

    diagnostics = pd.DataFrame(
        {
            "stress_short_return": short_return,
            "stress_medium_return": medium_return,
            "stress_breadth": breadth,
            "volatility_ratio": volatility_ratio,
            "stress_short_down": short_down,
            "stress_medium_down": medium_down,
            "stress_breadth_weak": breadth_weak,
            "stress_breadth_extreme": breadth_extreme,
            "stress_volatility_spike": volatility_spike,
            "stress_confirmed": confirmed,
            "stress_score": severity,
            "stress_factor": factor,
        },
        index=market.index,
    )
    return factor, diagnostics


def _chop_mask_r2(
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
    diagnostics = pd.DataFrame(
        {
            "chop_efficiency": efficiency,
            "chop_market_return": market_return,
            "chop_breadth": breadth,
            "chop_active": chop,
        },
        index=market.index,
    )
    return chop.fillna(False), diagnostics


def _damage_factor_r2(
    close: pd.DataFrame,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
) -> tuple[pd.Series, pd.DataFrame]:
    """Cut existing gross only when many held positions fail together."""

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


def _block_growth_when(
    targets: pd.DataFrame,
    row_mask: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    """Allow exits/reductions, but reject new/increased risk while a mask is on."""

    raw = targets.fillna(0.0)
    guarded = raw.copy()
    previous = pd.Series(0.0, index=raw.columns)
    blocked_counts = np.zeros(len(raw), dtype=int)

    for row in range(len(raw)):
        requested = raw.iloc[row].copy()
        if bool(row_mask.iloc[row]):
            same_direction = np.sign(previous) == np.sign(requested)
            previous_same_direction = previous.abs().where(same_direction, 0.0)
            growing = requested.abs().gt(previous_same_direction)
            if growing.any():
                requested.loc[growing] = (
                    np.sign(requested.loc[growing])
                    * previous_same_direction.loc[growing]
                )
                blocked_counts[row] = int(growing.sum())
        guarded.iloc[row] = requested
        previous = requested

    return guarded, pd.Series(
        blocked_counts,
        index=raw.index,
        name="chop_blocked_count",
    )


def _extension_growth_guard_r2(
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

    raw = targets.fillna(0.0)
    guarded = raw.copy()
    previous = pd.Series(0.0, index=raw.columns)
    blocked_counts = np.zeros(len(raw), dtype=int)

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

    return guarded, pd.Series(
        blocked_counts,
        index=raw.index,
        name="extension_blocked_count",
    )


def _low_churn_risk_factor(
    stress_factor: pd.Series,
    damage_factor: pd.Series,
    clean_trend: pd.Series,
    control: V99R2ControlSpec,
) -> tuple[pd.Series, pd.Series]:
    """Immediate defense, discrete recovery.

    R1 walked exposure up/down almost every hour. R2 immediately adopts any
    active defensive state, but once all defensive conditions disappear it
    keeps the last defensive level for a short neutral confirmation window and
    then returns to full risk in one step. A clean trend can restore full risk
    immediately.
    """

    desired = pd.concat([stress_factor, damage_factor], axis=1).min(axis=1)
    effective = np.ones(len(desired), dtype=float)
    previous = 1.0
    neutral_streak = 0

    for row in range(len(desired)):
        wanted = float(desired.iloc[row])
        if wanted < 1.0:
            current = wanted
            neutral_streak = 0
        elif previous < 1.0:
            if bool(clean_trend.iloc[row]):
                current = 1.0
                neutral_streak = 0
            else:
                neutral_streak += 1
                current = (
                    1.0
                    if neutral_streak >= control.neutral_recovery_hours
                    else previous
                )
        else:
            current = 1.0
            neutral_streak = 0
        effective[row] = current
        previous = current

    return (
        pd.Series(effective, index=desired.index, name="risk_factor"),
        desired.rename("desired_risk_factor"),
    )


def asymmetric_v99_targets_r2(
    data: FuturesData,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
    control: V99R2ControlSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """V99 R2: low-churn defense plus asymmetric opportunity preservation."""

    raw = targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    close = data.close.reindex_like(raw)
    if spec.market_symbol not in close.columns:
        raise ValueError(f"V99 market symbol {spec.market_symbol} is unavailable")
    market = close[spec.market_symbol]

    stress_factor, stress_diag = _stress_factor_r2(market, close, spec, control)
    chop_mask, chop_diag = _chop_mask_r2(market, close, spec)
    damage_factor, damage_diag = _damage_factor_r2(close, raw, proxy_equity, spec)
    clean_up, clean_down, trend_diag = _clean_trend(market, close, spec)

    # Choppy markets stop *new* conviction first; they do not resize an existing
    # winner every hour. Extension protection is applied with the same asymmetry.
    chop_guarded, chop_blocked = _block_growth_when(raw, chop_mask)
    extension_guarded, extension_blocked = _extension_growth_guard_r2(
        close,
        chop_guarded,
        clean_up,
        clean_down,
        spec,
    )

    risk_factor, desired_factor = _low_churn_risk_factor(
        stress_factor,
        damage_factor,
        trend_diag["clean_trend"].fillna(False),
        control,
    )

    boosted = extension_guarded.copy()
    boost_ready = risk_factor.ge(0.999)
    up_rows = clean_up.fillna(False) & boost_ready
    down_rows = clean_down.fillna(False) & boost_ready
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
            chop_blocked,
            extension_blocked,
            desired_factor,
            risk_factor,
            boost_ready.rename("boost_ready"),
            transformed.abs().sum(axis=1).rename("gross"),
        ],
        axis=1,
    )
    return transformed, diagnostics
