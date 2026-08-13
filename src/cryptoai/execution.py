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
    portfolio is at least ``l1_band``. The state transition remains sequential and
    causal, while NumPy arrays avoid expensive pandas indexing inside the loop.
    Missing prices force the affected weight to zero in the output.
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
    target_values = target.to_numpy(dtype=float, copy=True)
    valid_values = close.notna().to_numpy(dtype=bool, copy=False)
    hours = target.index.hour.to_numpy()
    scheduled_positions = np.flatnonzero(((hours - anchor_hour) % interval_hours) == 0)

    held_values = np.zeros_like(target_values, dtype=float)
    last = np.zeros(target_values.shape[1], dtype=float)
    initialized = False

    for i, pos in enumerate(scheduled_positions):
        candidate = np.where(valid_values[pos], target_values[pos], 0.0)
        delta = float(np.abs(candidate - last).sum())
        if (not initialized) or delta >= l1_band:
            last = candidate.copy()
            initialized = True
        end = scheduled_positions[i + 1] if i + 1 < len(scheduled_positions) else len(target_values)
        held_values[pos:end] = last

    held_values[~valid_values] = 0.0
    return pd.DataFrame(held_values, index=target.index, columns=target.columns)
