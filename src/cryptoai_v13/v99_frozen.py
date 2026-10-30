from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest import BacktestResult, exact_fast, screen
from .v99 import V99AsymmetricSpec, _cap_gross
from .v99_r4 import V99R4ControlSpec, _sparse_side_shock
from .v99_r5 import asymmetric_v99_targets_r5


FAST_GUARD = {"threshold": 0.058, "multiplier": 0.55, "cooldown": 6}
VOTE_WINDOWS_DAYS = (45, 60, 90, 120, 180, 240)
FROZEN_MAX_SATELLITE = 0.10
FROZEN_REBALANCE_HOURS = 24 * 30
FROZEN_ROUTINE_PERSISTENCE_HOURS = 4


@dataclass(frozen=True)
class FrozenV99Result:
    equity: pd.Series
    positions: pd.DataFrame
    satellite_weight: pd.Series
    target_satellite_weight: pd.Series
    vote_fraction: pd.Series
    parent_result: BacktestResult
    satellite_result: BacktestResult
    transfer_cost_total: float


def persistent_engine_result(
    data,
    parent_targets: pd.DataFrame,
    execution: dict,
    spec: V99AsymmetricSpec,
    control: V99R4ControlSpec,
    cost_per_side: float,
) -> BacktestResult:
    """R10 persistent alpha sleeve with immediate side-aware protection."""
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    r5_targets, diagnostics = asymmetric_v99_targets_r5(
        data, parent_targets, proxy, spec, control
    )
    routine = r5_targets.shift(FROZEN_ROUTINE_PERSISTENCE_HOURS).fillna(0.0)
    shock_long, shock_short, _ = _sparse_side_shock(data.close, parent_targets, control)
    long_now = pd.concat(
        [diagnostics["long_risk_factor"].astype(float), shock_long], axis=1
    ).min(axis=1)
    short_now = pd.concat(
        [diagnostics["short_risk_factor"].astype(float), shock_short], axis=1
    ).min(axis=1)
    targets = _cap_gross(
        routine.clip(lower=0.0).mul(long_now, axis=0)
        + routine.clip(upper=0.0).mul(short_now, axis=0),
        spec.maximum_gross,
    )
    return exact_fast(
        data,
        targets,
        cost_per_side=cost_per_side,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=2.0,
        drawdown_guard_threshold=FAST_GUARD["threshold"],
        drawdown_guard_multiplier=FAST_GUARD["multiplier"],
        drawdown_guard_cooldown_hours=FAST_GUARD["cooldown"],
    )


def trailing_vote(
    parent_equity: pd.Series,
    satellite_equity: pd.Series,
    windows_days: tuple[int, ...] = VOTE_WINDOWS_DAYS,
) -> pd.Series:
    parent_returns = parent_equity.pct_change(fill_method=None).fillna(0.0)
    satellite_returns = satellite_equity.pct_change(fill_method=None).fillna(0.0)
    votes = []
    for days in windows_days:
        lookback = int(days) * 24
        minimum = lookback // 2
        parent_score = parent_returns.rolling(lookback, min_periods=minimum).mean().div(
            parent_returns.rolling(lookback, min_periods=minimum)
            .std()
            .replace(0.0, np.nan)
        )
        satellite_score = satellite_returns.rolling(
            lookback, min_periods=minimum
        ).mean().div(
            satellite_returns.rolling(lookback, min_periods=minimum)
            .std()
            .replace(0.0, np.nan)
        )
        votes.append(satellite_score.gt(parent_score).astype(float))
    return pd.concat(votes, axis=1).mean(axis=1).fillna(0.0)


def desired_satellite_weight(
    vote_fraction: pd.Series,
    maximum_weight: float = FROZEN_MAX_SATELLITE,
) -> pd.Series:
    # Strict majority only: 4/6 -> 1/3 cap, 5/6 -> 2/3, 6/6 -> full cap.
    conviction = ((vote_fraction - 0.5) * 2.0).clip(0.0, 1.0)
    return conviction * float(maximum_weight)


def combine_dynamic_results(
    parent_result: BacktestResult,
    satellite_result: BacktestResult,
    target_satellite: pd.Series,
    rebalance_hours: int = FROZEN_REBALANCE_HOURS,
    transfer_cost_per_side: float = 0.0,
) -> tuple[pd.Series, pd.Series, pd.DataFrame, float]:
    aligned = pd.concat(
        [
            parent_result.equity.rename("parent"),
            satellite_result.equity.rename("satellite"),
            target_satellite.rename("target_satellite"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    parent_returns = aligned["parent"].pct_change(fill_method=None).fillna(0.0)
    satellite_returns = aligned["satellite"].pct_change(fill_method=None).fillna(0.0)
    desired = aligned["target_satellite"].clip(0.0, 1.0)

    parent_capital = 1.0
    satellite_capital = 0.0
    equity = pd.Series(index=aligned.index, dtype=float)
    weight = pd.Series(0.0, index=aligned.index, dtype=float)
    equity.iloc[0] = 1.0
    transfer_cost_total = 0.0

    for i in range(1, len(aligned)):
        parent_capital *= 1.0 + float(parent_returns.iloc[i])
        satellite_capital *= 1.0 + float(satellite_returns.iloc[i])
        total = parent_capital + satellite_capital
        if total <= 0.0:
            equity.iloc[i:] = 0.0
            weight.iloc[i:] = 0.0
            break
        if i % int(rebalance_hours) == 0:
            wanted = float(desired.iloc[i])
            current = satellite_capital / total
            moved = abs(current - wanted)
            cost = total * moved * 2.0 * float(transfer_cost_per_side)
            transfer_cost_total += cost
            total = max(0.0, total - cost)
            satellite_capital = total * wanted
            parent_capital = total * (1.0 - wanted)
        equity.iloc[i] = parent_capital + satellite_capital
        weight.iloc[i] = satellite_capital / max(parent_capital + satellite_capital, 1e-12)

    equity = equity.ffill().fillna(1.0)
    weight = weight.ffill().fillna(0.0)
    columns = parent_result.positions.columns.union(satellite_result.positions.columns)
    parent_positions = parent_result.positions.reindex(index=aligned.index, columns=columns).fillna(0.0)
    satellite_positions = satellite_result.positions.reindex(index=aligned.index, columns=columns).fillna(0.0)
    positions = parent_positions.mul(1.0 - weight, axis=0).add(
        satellite_positions.mul(weight, axis=0), fill_value=0.0
    )
    return equity, weight, positions, float(transfer_cost_total)


def build_frozen_v99(
    data,
    parent_targets: pd.DataFrame,
    parent_result: BacktestResult,
    execution: dict,
    spec: V99AsymmetricSpec,
    control: V99R4ControlSpec,
    cost_per_side: float | None = None,
) -> FrozenV99Result:
    cost = (
        float(execution["base_cost_per_side"])
        if cost_per_side is None
        else float(cost_per_side)
    )
    satellite = persistent_engine_result(
        data, parent_targets, execution, spec, control, cost
    )
    vote = trailing_vote(parent_result.equity, satellite.equity)
    desired = desired_satellite_weight(vote)
    equity, realized_weight, positions, transfer_cost = combine_dynamic_results(
        parent_result,
        satellite,
        desired,
        rebalance_hours=FROZEN_REBALANCE_HOURS,
        transfer_cost_per_side=cost,
    )
    return FrozenV99Result(
        equity=equity,
        positions=positions,
        satellite_weight=realized_weight,
        target_satellite_weight=desired,
        vote_fraction=vote,
        parent_result=parent_result,
        satellite_result=satellite,
        transfer_cost_total=transfer_cost,
    )
