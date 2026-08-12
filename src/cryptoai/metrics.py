from __future__ import annotations

import math
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

HOURS_PER_YEAR = 365.25 * 24.0


@dataclass(frozen=True)
class Performance:
    total_return: float
    cagr: float
    max_drawdown: float
    sharpe: float
    annual_volatility: float
    observations: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def equity_from_returns(returns: pd.Series, initial: float = 1.0) -> pd.Series:
    r = returns.fillna(0.0).clip(lower=-0.999999)
    return initial * (1.0 + r).cumprod()


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def performance(returns: pd.Series, periods_per_year: float = HOURS_PER_YEAR) -> Performance:
    r = returns.dropna().astype(float)
    if r.empty:
        return Performance(0.0, 0.0, 0.0, 0.0, 0.0, 0)
    eq = equity_from_returns(r)
    total = float(eq.iloc[-1] - 1.0)
    years = max(len(r) / periods_per_year, 1.0 / periods_per_year)
    cagr = float(eq.iloc[-1] ** (1.0 / years) - 1.0) if eq.iloc[-1] > 0 else -1.0
    std = float(r.std(ddof=0))
    vol = float(std * math.sqrt(periods_per_year))
    sharpe = float(r.mean() / std * math.sqrt(periods_per_year)) if std > 0 else 0.0
    return Performance(total, cagr, max_drawdown(eq), sharpe, vol, len(r))


def yearly_returns(returns: pd.Series) -> dict[str, float]:
    if returns.empty:
        return {}
    eq_growth = (1.0 + returns.fillna(0.0)).groupby(returns.index.year).prod() - 1.0
    return {str(int(year)): float(value) for year, value in eq_growth.items()}


def decisions_per_month(weights: pd.DataFrame, threshold: float = 0.05) -> float:
    if weights.empty:
        return 0.0
    delta = weights.fillna(0.0).diff().abs().sum(axis=1)
    decisions = delta.gt(threshold)
    monthly = decisions.groupby([weights.index.year, weights.index.month]).sum()
    return float(monthly.mean()) if len(monthly) else 0.0


def block_bootstrap_ruin_probability(
    hourly_returns: pd.Series,
    *,
    samples: int = 5000,
    block_hours: int = 24 * 7,
    ruin_equity: float = 0.20,
    seed: int = 20260812,
) -> float:
    """Conservative block bootstrap. Ruin means equity <= ruin_equity of initial capital."""
    values = hourly_returns.dropna().to_numpy(dtype=float)
    if len(values) < block_hours * 2:
        return 1.0
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(len(values) / block_hours)
    max_start = len(values) - block_hours
    ruined = 0
    for _ in range(samples):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        path = np.concatenate([values[s : s + block_hours] for s in starts])[: len(values)]
        log_growth = np.log1p(np.clip(path, -0.999999, None)).cumsum()
        if np.any(log_growth <= math.log(ruin_equity)):
            ruined += 1
    return ruined / samples
