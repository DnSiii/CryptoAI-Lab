from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .v99 import _cap_gross


@dataclass(frozen=True)
class LagEnvelopeSpec:
    """Fast-down / lag-confirmed-up target envelope.

    Reductions and closes are immediate. New directions and increases are
    capped by the same requested target observed ``confirm_hours`` earlier.
    This tests whether the broad R7 timing plateau came from avoiding premature
    risk rather than from delaying all execution. Clean aligned trend states may
    bypass confirmation to preserve convex trend capture.
    """

    confirm_hours: int = 3
    maximum_gross: float = 1.95
    clean_trend_bypass: bool = True

    def __post_init__(self) -> None:
        if self.confirm_hours <= 0:
            raise ValueError("confirmation horizon must be positive")
        if self.maximum_gross <= 0.0:
            raise ValueError("maximum gross must be positive")


def lag_confirm_growth(
    targets: pd.DataFrame,
    diagnostics: pd.DataFrame,
    spec: LagEnvelopeSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = targets.fillna(0.0)
    lagged = raw.shift(spec.confirm_hours).fillna(0.0)
    same_sign = np.sign(raw).eq(np.sign(lagged)) & raw.ne(0.0) & lagged.ne(0.0)

    # No confirmed same-side request yet: risk may close immediately but cannot
    # open the new direction before persistence is observed.
    envelope = lagged.where(same_sign, 0.0)

    # Never delay reductions. Where current requested magnitude is below the
    # lagged same-side magnitude, use current raw request immediately.
    reduction = same_sign & raw.abs().le(envelope.abs())
    confirmed = envelope.where(~reduction, raw)
    confirmed = confirmed.where(raw.ne(0.0), 0.0)

    if spec.clean_trend_bypass:
        long_ready = diagnostics.get(
            "long_boost_ready", pd.Series(False, index=raw.index)
        ).reindex(raw.index).fillna(False).astype(bool)
        short_ready = diagnostics.get(
            "short_boost_ready", pd.Series(False, index=raw.index)
        ).reindex(raw.index).fillna(False).astype(bool)
        if long_ready.any():
            requested = raw.loc[long_ready]
            part = confirmed.loc[long_ready]
            confirmed.loc[long_ready] = part.where(requested.le(0.0), requested)
        if short_ready.any():
            requested = raw.loc[short_ready]
            part = confirmed.loc[short_ready]
            confirmed.loc[short_ready] = part.where(requested.ge(0.0), requested)

    confirmed = _cap_gross(confirmed, spec.maximum_gross)
    limited = raw.abs().sub(confirmed.abs()).clip(lower=0.0)
    diag = pd.DataFrame(index=raw.index)
    diag["confirm_hours"] = spec.confirm_hours
    diag["limited_count"] = limited.gt(1e-12).sum(axis=1)
    diag["limited_gross"] = limited.sum(axis=1)
    diag["confirmed_gross"] = confirmed.abs().sum(axis=1)
    return confirmed, diag
