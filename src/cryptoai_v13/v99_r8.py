from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .v99 import _cap_gross


@dataclass(frozen=True)
class GrowthConfirmationSpec:
    """Causal fast-down / slow-up exposure confirmation.

    Risk reductions and closes follow the raw target immediately. New exposure,
    flips and increases are allowed only up to a trailing target average. This
    avoids making risk exits slower while filtering one-hour target spikes.
    Clean aligned trend states can bypass the growth limiter on the winning side
    so the mechanism does not intentionally suppress the large trend days that
    pay for the strategy's convexity.
    """

    window_hours: int = 3
    maximum_gross: float = 1.95
    clean_trend_bypass: bool = True

    def __post_init__(self) -> None:
        if self.window_hours <= 0:
            raise ValueError("confirmation window must be positive")
        if self.maximum_gross <= 0.0:
            raise ValueError("maximum gross must be positive")


def confirm_growth_targets(
    targets: pd.DataFrame,
    diagnostics: pd.DataFrame,
    spec: GrowthConfirmationSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = targets.fillna(0.0)
    if spec.window_hours == 1:
        out = _cap_gross(raw, spec.maximum_gross)
        diag = pd.DataFrame(index=raw.index)
        diag["confirmation_window_hours"] = 1
        diag["confirmation_limited_count"] = 0
        diag["confirmation_limited_gross"] = 0.0
        diag["confirmed_gross"] = out.abs().sum(axis=1)
        return out, diag

    average = raw.rolling(spec.window_hours, min_periods=1).mean()
    raw_sign = np.sign(raw)
    avg_sign = np.sign(average)
    same_sign = raw_sign.eq(avg_sign) & raw_sign.ne(0.0)

    # When a new direction has not persisted long enough for the trailing
    # average to agree, close the old risk immediately but do not open the new
    # side yet. When direction agrees, the average becomes the maximum allowed
    # growth magnitude.
    confirmed = average.where(same_sign, 0.0)

    # Reductions are never delayed: if the raw requested magnitude is already
    # below the confirmation envelope in the same direction, use it now.
    immediate_reduction = same_sign & raw.abs().le(confirmed.abs())
    confirmed = confirmed.where(~immediate_reduction, raw)
    confirmed = confirmed.where(raw.ne(0.0), 0.0)

    if spec.clean_trend_bypass:
        long_ready = diagnostics.get(
            "long_boost_ready",
            pd.Series(False, index=raw.index),
        ).reindex(raw.index).fillna(False).astype(bool)
        short_ready = diagnostics.get(
            "short_boost_ready",
            pd.Series(False, index=raw.index),
        ).reindex(raw.index).fillna(False).astype(bool)
        if long_ready.any():
            part = confirmed.loc[long_ready]
            requested = raw.loc[long_ready]
            confirmed.loc[long_ready] = part.where(requested.le(0.0), requested)
        if short_ready.any():
            part = confirmed.loc[short_ready]
            requested = raw.loc[short_ready]
            confirmed.loc[short_ready] = part.where(requested.ge(0.0), requested)

    confirmed = _cap_gross(confirmed, spec.maximum_gross)
    limited = raw.abs().sub(confirmed.abs()).clip(lower=0.0)
    diag = pd.DataFrame(index=raw.index)
    diag["confirmation_window_hours"] = spec.window_hours
    diag["confirmation_limited_count"] = limited.gt(1e-12).sum(axis=1)
    diag["confirmation_limited_gross"] = limited.sum(axis=1)
    diag["confirmed_gross"] = confirmed.abs().sum(axis=1)
    return confirmed, diag
