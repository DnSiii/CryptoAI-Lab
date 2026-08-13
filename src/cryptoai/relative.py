from __future__ import annotations

import numpy as np
import pandas as pd


def relative_momentum_signal(
    close: pd.DataFrame,
    horizons_days: tuple[int, ...],
    rebalance_hour: int = 0,
) -> pd.DataFrame:
    """Daily market-neutral ETH/BTC relative-momentum weights using only past prices."""
    out = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    if "BTCUSDT" not in close.columns or "ETHUSDT" not in close.columns:
        return out
    ratio = np.log(close["ETHUSDT"] / close["BTCUSDT"])
    score = pd.Series(0.0, index=close.index)
    for days in horizons_days:
        score = score.add(np.sign(ratio - ratio.shift(days * 24)).fillna(0.0), fill_value=0.0)
    direction = np.sign(score)
    out.loc[:, "ETHUSDT"] = 0.5 * direction
    out.loc[:, "BTCUSDT"] = -0.5 * direction
    sampled = out.copy()
    sampled.loc[sampled.index.hour != rebalance_hour, :] = np.nan
    held = sampled.ffill().fillna(0.0)
    return held.where(close.notna(), 0.0)
