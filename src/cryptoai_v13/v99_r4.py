from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import FuturesData
from .v99 import V99AsymmetricSpec, _cap_gross, _clean_trend
from .v99_r2 import _chop_mask_r2
from .v99_r3 import _directional_stress, _side_low_churn_factor, V99R3ControlSpec


@dataclass(frozen=True)
class V99R4ControlSpec:
    """Sparse asymmetric protection.

    R4 keeps the useful R3 idea (market stress only cuts the side fighting the
    systemic move) but removes continuous portfolio intervention and extension
    chasing protection. The portfolio shock brake is intentionally rare: it
    requires a sufficiently diversified active side, a very high synchronized
    losing fraction and material side P&L damage over a short window.
    """

    extreme_breadth: float = 0.15
    neutral_recovery_hours: int = 1
    shock_hours: int = 2
    minimum_side_positions: int = 4
    shock_soft_fraction: float = 0.80
    shock_hard_fraction: float = 0.93
    shock_soft_return: float = -0.008
    shock_hard_return: float = -0.016
    shock_soft_multiplier: float = 0.78
    shock_hard_multiplier: float = 0.45

    def __post_init__(self) -> None:
        if not 0.0 < self.extreme_breadth < 0.5:
            raise ValueError("extreme breadth must be between zero and one half")
        if self.neutral_recovery_hours <= 0 or self.shock_hours <= 0:
            raise ValueError("recovery and shock windows must be positive")
        if self.minimum_side_positions < 2:
            raise ValueError("minimum side positions must be at least two")
        if not 0.5 < self.shock_soft_fraction < self.shock_hard_fraction <= 1.0:
            raise ValueError("invalid shock fractions")
        if not self.shock_hard_return < self.shock_soft_return < 0.0:
            raise ValueError("shock returns must be negative and ordered")
        if not 0.0 < self.shock_hard_multiplier <= self.shock_soft_multiplier <= 1.0:
            raise ValueError("invalid shock multipliers")


def _sparse_side_shock(
    close: pd.DataFrame,
    targets: pd.DataFrame,
    control: V99R4ControlSpec,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    held = targets.shift(1).fillna(0.0)
    hourly = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    def side(which: str):
        if which == "long":
            weight = held.clip(lower=0.0)
            signed = hourly
            losing = hourly.lt(0.0)
        else:
            weight = -held.clip(upper=0.0)
            signed = -hourly
            losing = hourly.gt(0.0)
        active = weight.gt(0.0)
        count = active.sum(axis=1)
        eligible = count.ge(control.minimum_side_positions)
        denom_count = count.replace(0, np.nan)
        loss_fraction = losing.where(active, False).sum(axis=1).div(denom_count).fillna(0.0)
        gross = weight.sum(axis=1).replace(0.0, np.nan)
        weighted_return = signed.mul(weight).sum(axis=1).div(gross).fillna(0.0)
        loss_smooth = loss_fraction.rolling(control.shock_hours, min_periods=control.shock_hours).mean()
        recent = weighted_return.rolling(control.shock_hours, min_periods=control.shock_hours).sum()
        eligible_window = eligible.rolling(control.shock_hours, min_periods=control.shock_hours).min().fillna(0).astype(bool)
        hard = eligible_window & loss_smooth.ge(control.shock_hard_fraction) & recent.le(control.shock_hard_return)
        soft = eligible_window & loss_smooth.ge(control.shock_soft_fraction) & recent.le(control.shock_soft_return) & ~hard
        factor = pd.Series(1.0, index=targets.index)
        factor.loc[soft] = control.shock_soft_multiplier
        factor.loc[hard] = control.shock_hard_multiplier
        state = pd.Series("normal", index=targets.index, dtype="object")
        state.loc[soft] = "soft"
        state.loc[hard] = "hard"
        return factor, state, count, loss_smooth.fillna(0.0), recent.fillna(0.0)

    long_factor, long_state, long_count, long_loss, long_ret = side("long")
    short_factor, short_state, short_count, short_loss, short_ret = side("short")
    damage_factor = pd.concat([long_factor, short_factor], axis=1).min(axis=1)
    damage_state = np.where(
        long_state.eq("hard") | short_state.eq("hard"),
        "hard",
        np.where(long_state.eq("soft") | short_state.eq("soft"), "soft", "normal"),
    )
    diag = pd.DataFrame(
        {
            "long_active_positions": long_count,
            "short_active_positions": short_count,
            "long_loss_fraction": long_loss,
            "short_loss_fraction": short_loss,
            "smoothed_loss_fraction": pd.concat([long_loss, short_loss], axis=1).max(axis=1),
            "long_shock_return": long_ret,
            "short_shock_return": short_ret,
            "long_damage_state": long_state,
            "short_damage_state": short_state,
            "long_damage_factor": long_factor,
            "short_damage_factor": short_factor,
            "damage_factor": damage_factor,
            "damage_state": damage_state,
        },
        index=targets.index,
    )
    return long_factor, short_factor, diag


def _block_new_entries_in_chop(
    targets: pd.DataFrame,
    chop: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    raw = targets.fillna(0.0)
    guarded = raw.copy()
    previous = pd.Series(0.0, index=raw.columns)
    counts = np.zeros(len(raw), dtype=int)
    for row in range(len(raw)):
        requested = raw.iloc[row].copy()
        if bool(chop.iloc[row]):
            previous_active = previous.abs().gt(1e-12)
            same_side = np.sign(previous) == np.sign(requested)
            allowed = previous_active & same_side
            blocked = requested.abs().gt(1e-12) & ~allowed
            if blocked.any():
                requested.loc[blocked] = 0.0
                counts[row] = int(blocked.sum())
        guarded.iloc[row] = requested
        previous = requested
    return guarded, pd.Series(counts, index=raw.index, name="chop_blocked_count")


def asymmetric_v99_targets_r4(
    data: FuturesData,
    targets: pd.DataFrame,
    proxy_equity: pd.Series,
    spec: V99AsymmetricSpec,
    control: V99R4ControlSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _ = proxy_equity
    raw = targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    close = data.close.reindex_like(raw)
    if spec.market_symbol not in close.columns:
        raise ValueError(f"V99 market symbol {spec.market_symbol} is unavailable")
    market = close[spec.market_symbol]

    bridge = V99R3ControlSpec(
        extreme_breadth=control.extreme_breadth,
        neutral_recovery_hours=control.neutral_recovery_hours,
        shock_hours=3,
        shock_soft_fraction=0.66,
        shock_hard_fraction=0.82,
        shock_soft_return=-0.004,
        shock_hard_return=-0.010,
        shock_soft_multiplier=0.72,
        shock_hard_multiplier=0.42,
    )
    long_stress, short_stress, stress_diag = _directional_stress(market, close, spec, bridge)
    long_damage, short_damage, damage_diag = _sparse_side_shock(close, raw, control)
    chop, chop_diag = _chop_mask_r2(market, close, spec)
    clean_up, clean_down, trend_diag = _clean_trend(market, close, spec)

    guarded, chop_blocked = _block_new_entries_in_chop(raw, chop)

    long_desired = pd.concat([long_stress, long_damage], axis=1).min(axis=1)
    short_desired = pd.concat([short_stress, short_damage], axis=1).min(axis=1)
    long_factor = _side_low_churn_factor(long_desired, clean_up.fillna(False), control.neutral_recovery_hours).rename("long_risk_factor")
    short_factor = _side_low_churn_factor(short_desired, clean_down.fillna(False), control.neutral_recovery_hours).rename("short_risk_factor")

    transformed = guarded.clip(lower=0.0).mul(long_factor, axis=0) + guarded.clip(upper=0.0).mul(short_factor, axis=0)
    long_boost = clean_up.fillna(False) & long_factor.ge(0.999)
    short_boost = clean_down.fillna(False) & short_factor.ge(0.999)
    if long_boost.any():
        part = transformed.loc[long_boost]
        transformed.loc[long_boost] = part.where(part.le(0.0), part * spec.clean_trend_boost)
    if short_boost.any():
        part = transformed.loc[short_boost]
        transformed.loc[short_boost] = part.where(part.ge(0.0), part * spec.clean_trend_boost)
    transformed = _cap_gross(transformed, spec.maximum_gross)

    long_desired = long_desired.rename("long_desired_risk_factor")
    short_desired = short_desired.rename("short_desired_risk_factor")
    risk_factor = pd.concat([long_factor, short_factor], axis=1).min(axis=1).rename("risk_factor")
    desired = pd.concat([long_desired, short_desired], axis=1).min(axis=1).rename("desired_risk_factor")
    boost_ready = (long_boost | short_boost).rename("boost_ready")
    extension_blocked = pd.Series(0, index=raw.index, name="extension_blocked_count", dtype="int64")

    diagnostics = pd.concat(
        [
            stress_diag,
            chop_diag,
            damage_diag,
            trend_diag,
            chop_blocked,
            extension_blocked,
            desired,
            long_factor,
            short_factor,
            risk_factor,
            long_boost.rename("long_boost_ready"),
            short_boost.rename("short_boost_ready"),
            boost_ready,
            transformed.abs().sum(axis=1).rename("gross"),
        ],
        axis=1,
    )
    return transformed, diagnostics
