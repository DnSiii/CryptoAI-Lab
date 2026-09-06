from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import FuturesData
from .v99 import V99AsymmetricSpec, _breadth, _cap_gross, _clean_trend
from .v99_r2 import _block_growth_when, _chop_mask_r2, _extension_growth_guard_r2


@dataclass(frozen=True)
class V99R3ControlSpec:
    """Directional stress + side-aware portfolio shock controls.

    R3 fixes the main R2 failure: systemic stress must not reduce the side that
    is profiting from the move. A crash therefore de-risks longs only; an upside
    squeeze de-risks shorts only. A separate side-aware portfolio shock brake
    reacts when many held positions on one side fail together even if BTC itself
    has not crossed a market-stress threshold.
    """

    extreme_breadth: float = 0.15
    neutral_recovery_hours: int = 2
    shock_hours: int = 3
    shock_soft_fraction: float = 0.66
    shock_hard_fraction: float = 0.82
    shock_soft_return: float = -0.004
    shock_hard_return: float = -0.010
    shock_soft_multiplier: float = 0.72
    shock_hard_multiplier: float = 0.42

    def __post_init__(self) -> None:
        if not 0.0 < self.extreme_breadth < 0.5:
            raise ValueError("extreme breadth must be between zero and one half")
        if self.neutral_recovery_hours <= 0 or self.shock_hours <= 0:
            raise ValueError("recovery and shock windows must be positive")
        if not 0.5 <= self.shock_soft_fraction < self.shock_hard_fraction <= 1.0:
            raise ValueError("invalid shock fractions")
        if not self.shock_hard_return < self.shock_soft_return < 0.0:
            raise ValueError("shock returns must be negative and ordered")
        if not 0.0 < self.shock_hard_multiplier <= self.shock_soft_multiplier <= 1.0:
            raise ValueError("invalid shock multipliers")


def _directional_stress(
    market: pd.Series,
    close: pd.DataFrame,
    spec: V99AsymmetricSpec,
    control: V99R3ControlSpec,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
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
    volatility_spike = volatility_ratio.ge(spec.volatility_spike_ratio)

    down_short = short_return.le(spec.stress_short_return)
    down_medium = medium_return.le(spec.stress_medium_return)
    breadth_weak = breadth.le(spec.stress_breadth)
    breadth_extreme_low = breadth.le(control.extreme_breadth)
    down_damage = down_short | down_medium
    down_confirmed = down_damage & (breadth_weak | volatility_spike)
    down_severe = (
        down_short & down_medium & (breadth_weak | volatility_spike)
    ) | (down_damage & breadth_extreme_low & volatility_spike)
    down_crisis = down_short & down_medium & breadth_extreme_low & volatility_spike

    short_up_threshold = abs(spec.stress_short_return)
    medium_up_threshold = abs(spec.stress_medium_return)
    up_short = short_return.ge(short_up_threshold)
    up_medium = medium_return.ge(medium_up_threshold)
    breadth_strong = breadth.ge(1.0 - spec.stress_breadth)
    breadth_extreme_high = breadth.ge(1.0 - control.extreme_breadth)
    up_damage = up_short | up_medium
    up_confirmed = up_damage & (breadth_strong | volatility_spike)
    up_severe = (
        up_short & up_medium & (breadth_strong | volatility_spike)
    ) | (up_damage & breadth_extreme_high & volatility_spike)
    up_crisis = up_short & up_medium & breadth_extreme_high & volatility_spike

    long_factor = pd.Series(1.0, index=market.index)
    long_factor.loc[down_confirmed] = spec.stress_one_multiplier
    long_factor.loc[down_severe] = spec.stress_two_multiplier
    long_factor.loc[down_crisis] = spec.stress_three_multiplier

    short_factor = pd.Series(1.0, index=market.index)
    short_factor.loc[up_confirmed] = spec.stress_one_multiplier
    short_factor.loc[up_severe] = spec.stress_two_multiplier
    short_factor.loc[up_crisis] = spec.stress_three_multiplier

    down_score = pd.Series(0, index=market.index, dtype="int64")
    down_score.loc[down_confirmed] = 1
    down_score.loc[down_severe] = 2
    down_score.loc[down_crisis] = 3
    up_score = pd.Series(0, index=market.index, dtype="int64")
    up_score.loc[up_confirmed] = 1
    up_score.loc[up_severe] = 2
    up_score.loc[up_crisis] = 3

    diagnostics = pd.DataFrame(
        {
            "stress_short_return": short_return,
            "stress_medium_return": medium_return,
            "stress_breadth": breadth,
            "volatility_ratio": volatility_ratio,
            "down_stress_score": down_score,
            "up_stress_score": up_score,
            "stress_score": pd.concat([down_score, up_score], axis=1).max(axis=1),
            "long_stress_factor": long_factor,
            "short_stress_factor": short_factor,
            "stress_factor": pd.concat([long_factor, short_factor], axis=1).min(axis=1),
        },
        index=market.index,
    )
    return long_factor, short_factor, diagnostics


def _weighted_side_return(
    hourly_return: pd.DataFrame,
    held: pd.DataFrame,
    side: str,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    if side == "long":
        weight = held.clip(lower=0.0)
        signed = hourly_return
        losing = hourly_return.lt(0.0)
    elif side == "short":
        weight = (-held.clip(upper=0.0))
        signed = -hourly_return
        losing = hourly_return.gt(0.0)
    else:
        raise ValueError("side must be long or short")

    active = weight.gt(0.0)
    active_count = active.sum(axis=1).replace(0, np.nan)
    loss_fraction = losing.where(active, False).sum(axis=1).div(active_count).fillna(0.0)
    gross = weight.sum(axis=1).replace(0.0, np.nan)
    side_return = signed.mul(weight).sum(axis=1).div(gross).fillna(0.0)
    return loss_fraction, side_return, active.sum(axis=1)


def _side_shock_factors(
    close: pd.DataFrame,
    targets: pd.DataFrame,
    control: V99R3ControlSpec,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    held = targets.shift(1).fillna(0.0)
    hourly_return = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    long_loss, long_hourly, long_count = _weighted_side_return(hourly_return, held, "long")
    short_loss, short_hourly, short_count = _weighted_side_return(hourly_return, held, "short")

    long_loss_smooth = long_loss.rolling(control.shock_hours, min_periods=1).mean()
    short_loss_smooth = short_loss.rolling(control.shock_hours, min_periods=1).mean()
    long_recent = long_hourly.rolling(control.shock_hours, min_periods=1).sum()
    short_recent = short_hourly.rolling(control.shock_hours, min_periods=1).sum()

    long_hard = (
        long_loss_smooth.ge(control.shock_hard_fraction)
        & long_recent.le(control.shock_hard_return)
    )
    long_soft = (
        long_loss_smooth.ge(control.shock_soft_fraction)
        & long_recent.le(control.shock_soft_return)
        & ~long_hard
    )
    short_hard = (
        short_loss_smooth.ge(control.shock_hard_fraction)
        & short_recent.le(control.shock_hard_return)
    )
    short_soft = (
        short_loss_smooth.ge(control.shock_soft_fraction)
        & short_recent.le(control.shock_soft_return)
        & ~short_hard
    )

    long_factor = pd.Series(1.0, index=targets.index)
    long_factor.loc[long_soft] = control.shock_soft_multiplier
    long_factor.loc[long_hard] = control.shock_hard_multiplier
    short_factor = pd.Series(1.0, index=targets.index)
    short_factor.loc[short_soft] = control.shock_soft_multiplier
    short_factor.loc[short_hard] = control.shock_hard_multiplier

    long_state = pd.Series("normal", index=targets.index, dtype="object")
    long_state.loc[long_soft] = "soft"
    long_state.loc[long_hard] = "hard"
    short_state = pd.Series("normal", index=targets.index, dtype="object")
    short_state.loc[short_soft] = "soft"
    short_state.loc[short_hard] = "hard"

    diagnostics = pd.DataFrame(
        {
            "long_active_positions": long_count,
            "short_active_positions": short_count,
            "long_loss_fraction": long_loss_smooth,
            "short_loss_fraction": short_loss_smooth,
            "smoothed_loss_fraction": pd.concat([long_loss_smooth, short_loss_smooth], axis=1).max(axis=1),
            "long_shock_return": long_recent,
            "short_shock_return": short_recent,
            "long_damage_state": long_state,
            "short_damage_state": short_state,
            "long_damage_factor": long_factor,
            "short_damage_factor": short_factor,
            "damage_factor": pd.concat([long_factor, short_factor], axis=1).min(axis=1),
        },
        index=targets.index,
    )
    diagnostics["damage_state"] = np.where(
        (long_state.eq("hard") | short_state.eq("hard")),
        "hard",
        np.where((long_state.eq("soft") | short_state.eq("soft")), "soft", "normal"),
    )
    return long_factor, short_factor, diagnostics


def _side_low_churn_factor(
    desired: pd.Series,
    clean_aligned: pd.Series,
    recovery_hours: int,
) -> pd.Series:
    effective = np.ones(len(desired), dtype=float)
    previous = 1.0
    neutral_streak = 0
    for row in range(len(desired)):
        wanted = float(desired.iloc[row])
        if wanted < 1.0:
            current = wanted
            neutral_streak = 0
        elif previous < 1.0:
            if bool(clean_aligned.iloc[row]):
                current = 1.0
                neutral_streak = 0
            else:
                neutral_streak += 1
                current = 1.0 if neutral_streak >= recovery_hours else previous
        else:
            current = 1.0
            neutral_streak = 0
        effective[row] = current
        previous = current
    return pd.Series(effective, index=desired.index)


def asymmetric_v99_targets_r3(
    data: FuturesData,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
    control: V99R3ControlSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """V99 R3 directional asymmetric overlay.

    proxy_equity remains an argument for API continuity and auditability. R3's
    shock brake intentionally uses held-position returns directly instead of a
    global equity proxy so that a profitable short book is not suppressed by a
    falling market, and vice versa.
    """

    _ = proxy_equity
    raw = targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    close = data.close.reindex_like(raw)
    if spec.market_symbol not in close.columns:
        raise ValueError(f"V99 market symbol {spec.market_symbol} is unavailable")
    market = close[spec.market_symbol]

    long_stress, short_stress, stress_diag = _directional_stress(market, close, spec, control)
    long_damage, short_damage, damage_diag = _side_shock_factors(close, raw, control)
    chop_mask, chop_diag = _chop_mask_r2(market, close, spec)
    clean_up, clean_down, trend_diag = _clean_trend(market, close, spec)

    chop_guarded, chop_blocked = _block_growth_when(raw, chop_mask)
    extension_guarded, extension_blocked = _extension_growth_guard_r2(
        close,
        chop_guarded,
        clean_up,
        clean_down,
        spec,
    )

    long_desired = pd.concat([long_stress, long_damage], axis=1).min(axis=1)
    short_desired = pd.concat([short_stress, short_damage], axis=1).min(axis=1)
    long_factor = _side_low_churn_factor(
        long_desired,
        clean_up.fillna(False),
        control.neutral_recovery_hours,
    ).rename("long_risk_factor")
    short_factor = _side_low_churn_factor(
        short_desired,
        clean_down.fillna(False),
        control.neutral_recovery_hours,
    ).rename("short_risk_factor")

    transformed = extension_guarded.copy()
    positives = transformed.clip(lower=0.0).mul(long_factor, axis=0)
    negatives = transformed.clip(upper=0.0).mul(short_factor, axis=0)
    transformed = positives + negatives

    long_boost_ready = clean_up.fillna(False) & long_factor.ge(0.999)
    short_boost_ready = clean_down.fillna(False) & short_factor.ge(0.999)
    if long_boost_ready.any():
        current = transformed.loc[long_boost_ready]
        transformed.loc[long_boost_ready] = current.where(
            current.le(0.0),
            current * spec.clean_trend_boost,
        )
    if short_boost_ready.any():
        current = transformed.loc[short_boost_ready]
        transformed.loc[short_boost_ready] = current.where(
            current.ge(0.0),
            current * spec.clean_trend_boost,
        )

    transformed = _cap_gross(transformed, spec.maximum_gross)
    risk_factor = pd.concat([long_factor, short_factor], axis=1).min(axis=1).rename("risk_factor")
    desired_risk = pd.concat([long_desired, short_desired], axis=1).min(axis=1).rename("desired_risk_factor")
    boost_ready = (long_boost_ready | short_boost_ready).rename("boost_ready")

    diagnostics = pd.concat(
        [
            stress_diag,
            chop_diag,
            damage_diag,
            trend_diag,
            chop_blocked,
            extension_blocked,
            desired_risk,
            long_factor,
            short_factor,
            risk_factor,
            long_boost_ready.rename("long_boost_ready"),
            short_boost_ready.rename("short_boost_ready"),
            boost_ready,
            transformed.abs().sum(axis=1).rename("gross"),
        ],
        axis=1,
    )
    return transformed, diagnostics
