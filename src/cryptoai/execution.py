from __future__ import annotations

import numpy as np
import pandas as pd


def scheduled_hold(
    target: pd.DataFrame,
    close: pd.DataFrame,
    *,
    interval_hours: int = 24,
    anchor_hour: int = 0,
    l1_band: float = 0.0,
) -> pd.DataFrame:
    """Causally sample target weights on a fixed UTC schedule with L1 hysteresis.

    A scheduled target is accepted only when its L1 distance from the last accepted
    portfolio is at least ``l1_band``. This suppresses small rebalances without
    looking ahead. Missing prices force the affected weight to zero in the output.
    """
    if interval_hours not in {1, 2, 3, 4, 6, 8, 12, 24}:
        raise ValueError("interval_hours must divide a UTC day")
    if not 0 <= anchor_hour <= 23:
        raise ValueError("anchor_hour must be between 0 and 23")
    if l1_band < 0.0:
        raise ValueError("l1_band must be non-negative")
    if target.empty:
        return target.copy()

    target = target.reindex(index=close.index, columns=close.columns).fillna(0.0)
    schedule_mask = ((target.index.hour - anchor_hour) % interval_hours) == 0
    scheduled_index = target.index[schedule_mask]

    sampled = pd.DataFrame(np.nan, index=target.index, columns=target.columns)
    last = pd.Series(0.0, index=target.columns)
    initialized = False

    for ts in scheduled_index:
        candidate = target.loc[ts].where(close.loc[ts].notna(), 0.0).fillna(0.0)
        delta = float((candidate - last).abs().sum())
        if (not initialized) or delta >= l1_band:
            last = candidate
            initialized = True
        sampled.loc[ts] = last

    held = sampled.ffill().fillna(0.0)
    return held.where(close.notna(), 0.0)
