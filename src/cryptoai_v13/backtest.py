from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import FuturesData


@dataclass(frozen=True)
class BacktestResult:
    equity: pd.Series
    positions: pd.DataFrame
    turnover: pd.Series
    fees: pd.Series
    funding: pd.Series
    gross_exposure: pd.Series
    ruin: bool


def screen(data: FuturesData, targets: pd.DataFrame, cost_per_side: float = 0.0007) -> BacktestResult:
    """Fast approximation used only to rank candidates.

    A target computed at close t executes at open t+1. Funding at that open is
    charged to the older position, preventing same-timestamp funding capture.
    """
    targets = targets.reindex(index=data.close.index, columns=data.symbols).fillna(0.0)
    at_open = targets.shift(1).fillna(0.0)
    overnight_pos = targets.shift(2).fillna(0.0)
    overnight_return = data.frames["open"].div(data.close.shift(1)).sub(1.0).fillna(0.0)
    intraday_return = data.close.div(data.frames["open"]).sub(1.0).fillna(0.0)
    gross = (overnight_pos * overnight_return).sum(axis=1) + (at_open * intraday_return).sum(axis=1)
    turnover = at_open.sub(overnight_pos).abs().sum(axis=1)
    fees = turnover * cost_per_side
    funding = (overnight_pos * data.funding).sum(axis=1)
    net = gross - fees - funding
    factors = 1.0 + net
    ruin = bool((factors <= 0).any())
    if ruin:
        first = np.flatnonzero((factors <= 0).to_numpy())[0]
        factors.iloc[first:] = 0.0
    equity = factors.cumprod()
    if len(equity):
        equity.iloc[0] = 1.0
    return BacktestResult(equity, at_open, turnover, fees, funding,
                          at_open.abs().sum(axis=1), ruin)


def exact(data: FuturesData, targets: pd.DataFrame, cost_per_side: float = 0.0007,
          maintenance_equity_fraction: float = 0.02,
          gross_guard_cap: float | None = None,
          funding_debit_multiplier: float = 1.0,
          funding_credit_multiplier: float = 1.0,
          drawdown_guard_threshold: float | None = None,
          drawdown_guard_multiplier: float = 1.0,
          drawdown_guard_recovery: float | None = None,
          drawdown_guard_cooldown_hours: int | None = None) -> BacktestResult:
    """Stateful cross-margin replay with drift and conservative intrabar ruin.

    If all held assets touch their adverse hourly extrema, the portfolio must
    retain more than ``maintenance_equity_fraction`` of equity. This is more
    conservative than assuming a favorable order among hourly high/low events.

    ``gross_guard_cap`` is an optional causal drift guard. Targets are clipped
    to the cap, and an observed close above the cap schedules a proportional
    reduction at the next hourly open. It intentionally does not claim that an
    intrabar cap can be enforced from hourly OHLC data.

    Funding stress can independently increase debits and haircut credits.
    This avoids the misleading case where multiplying all signed funding rates
    also multiplies favorable receipts.
    """
    targets = targets.reindex(index=data.close.index, columns=data.symbols).fillna(0.0)
    index = data.close.index
    columns = data.close.columns
    equity = pd.Series(np.nan, index=index, dtype=float)
    positions_out = pd.DataFrame(0.0, index=index, columns=columns)
    turnover = pd.Series(0.0, index=index)
    fees = pd.Series(0.0, index=index)
    funding_cost = pd.Series(0.0, index=index)
    current_equity = 1.0
    peak_equity = 1.0
    weights = pd.Series(0.0, index=columns)
    last_requested_target = pd.Series(0.0, index=columns)
    drawdown_guard_active = False
    drawdown_guard_until = -1
    ruined = False
    for i, timestamp in enumerate(index):
        if i == 0:
            equity.iloc[i] = current_equity
            continue
        previous = index[i - 1]
        if drawdown_guard_threshold is not None:
            if (
                drawdown_guard_cooldown_hours is not None
                and drawdown_guard_active
                and i >= drawdown_guard_until
            ):
                drawdown_guard_active = False
                peak_equity = current_equity
            recovery = (
                drawdown_guard_threshold / 2.0
                if drawdown_guard_recovery is None
                else drawdown_guard_recovery
            )
            prior_drawdown = current_equity / peak_equity - 1.0
            if (
                drawdown_guard_cooldown_hours is None
                and drawdown_guard_active
                and prior_drawdown >= -abs(recovery)
            ):
                drawdown_guard_active = False
            elif (
                not drawdown_guard_active
                and prior_drawdown <= -abs(drawdown_guard_threshold)
            ):
                drawdown_guard_active = True
                if drawdown_guard_cooldown_hours is not None:
                    drawdown_guard_until = i + drawdown_guard_cooldown_hours
        guard_factor = (
            drawdown_guard_multiplier if drawdown_guard_active else 1.0
        )
        opened = data.frames["open"].loc[timestamp]
        previous_close = data.close.loc[previous]
        ratio = opened.div(previous_close).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        overnight_factor = 1.0 + float((weights * (ratio - 1.0)).sum())
        if overnight_factor <= maintenance_equity_fraction:
            current_equity = 0.0
            ruined = True
            equity.iloc[i:] = 0.0
            break
        current_equity *= overnight_factor
        weights = (weights * ratio / overnight_factor).fillna(0.0)

        # Funding is paid/received by the position held before this open.
        funding_contribution = weights * data.funding.loc[timestamp]
        fund_fraction = float(
            funding_contribution.clip(lower=0.0).sum() * funding_debit_multiplier
            + funding_contribution.clip(upper=0.0).sum() * funding_credit_multiplier
        )
        funding_value = current_equity * fund_fraction
        current_equity -= funding_value
        funding_cost.iloc[i] = funding_value

        requested_target = targets.iloc[i - 1].copy() * guard_factor
        signal_event = float(
            (requested_target - last_requested_target).abs().sum()
        ) > 1e-12
        last_requested_target = requested_target.copy()
        tradable = opened.notna() & data.close.loc[timestamp].notna()
        forced_exit = bool((weights.abs().gt(1e-12) & ~tradable).any())
        prior_close_gross = float(positions_out.iloc[i - 1].abs().sum())
        guard_event = bool(
            gross_guard_cap is not None
            and prior_close_gross > gross_guard_cap + 1e-12
        )
        if signal_event or forced_exit or guard_event:
            target = requested_target if signal_event else weights.copy()
            target = target.where(tradable, 0.0)
            if gross_guard_cap is not None:
                target_gross = float(target.abs().sum())
                if target_gross > gross_guard_cap:
                    target *= gross_guard_cap / target_gross
            traded = float((target - weights).abs().sum())
            fee = current_equity * traded * cost_per_side
            current_equity -= fee
            turnover.iloc[i] = traded
            fees.iloc[i] = fee
            weights = target

        low_move = data.frames["low"].loc[timestamp].div(opened).sub(1.0).fillna(0.0)
        high_move = data.frames["high"].loc[timestamp].div(opened).sub(1.0).fillna(0.0)
        adverse = pd.Series(np.where(weights >= 0, low_move, high_move), index=columns)
        worst_factor = 1.0 + float((weights * adverse).sum())
        if worst_factor <= maintenance_equity_fraction:
            current_equity = 0.0
            ruined = True
            equity.iloc[i:] = 0.0
            positions_out.iloc[i:] = 0.0
            break

        close_move = data.close.loc[timestamp].div(opened).sub(1.0).fillna(0.0)
        close_factor = 1.0 + float((weights * close_move).sum())
        if close_factor <= maintenance_equity_fraction:
            current_equity = 0.0
            ruined = True
            equity.iloc[i:] = 0.0
            break
        current_equity *= close_factor
        weights = (weights * (1.0 + close_move) / close_factor).fillna(0.0)
        equity.iloc[i] = current_equity
        positions_out.iloc[i] = weights
        peak_equity = max(peak_equity, current_equity)
    return BacktestResult(equity.ffill().fillna(1.0), positions_out, turnover, fees,
                          funding_cost, positions_out.abs().sum(axis=1), ruined)


def exact_fast(data: FuturesData, targets: pd.DataFrame,
               cost_per_side: float = 0.0007,
               maintenance_equity_fraction: float = 0.02,
               gross_guard_cap: float | None = None,
               funding_debit_multiplier: float = 1.0,
               funding_credit_multiplier: float = 1.0,
               drawdown_guard_threshold: float | None = None,
               drawdown_guard_multiplier: float = 1.0,
               drawdown_guard_recovery: float | None = None,
               drawdown_guard_cooldown_hours: int | None = None) -> BacktestResult:
    """Array implementation of :func:`exact` with identical execution rules.

    The state transition remains sequential and causal; only repeated pandas
    row construction and indexing are removed.
    """
    targets = targets.reindex(index=data.close.index, columns=data.symbols).fillna(0.0)
    index = data.close.index
    columns = data.close.columns
    size, assets = len(index), len(columns)
    target_values = targets.to_numpy(dtype=float, copy=True)
    opened_values = data.frames["open"].to_numpy(dtype=float, copy=False)
    close_values = data.close.to_numpy(dtype=float, copy=False)
    low_values = data.frames["low"].to_numpy(dtype=float, copy=False)
    high_values = data.frames["high"].to_numpy(dtype=float, copy=False)
    funding_values = data.funding.to_numpy(dtype=float, copy=False)

    equity_values = np.full(size, np.nan, dtype=float)
    position_values = np.zeros((size, assets), dtype=float)
    turnover_values = np.zeros(size, dtype=float)
    fee_values = np.zeros(size, dtype=float)
    funding_cost_values = np.zeros(size, dtype=float)
    current_equity = 1.0
    peak_equity = 1.0
    weights = np.zeros(assets, dtype=float)
    last_requested_target = np.zeros(assets, dtype=float)
    drawdown_guard_active = False
    drawdown_guard_until = -1
    ruined = False

    if size:
        equity_values[0] = current_equity
    for i in range(1, size):
        if drawdown_guard_threshold is not None:
            if (
                drawdown_guard_cooldown_hours is not None
                and drawdown_guard_active
                and i >= drawdown_guard_until
            ):
                drawdown_guard_active = False
                peak_equity = current_equity
            recovery = (
                drawdown_guard_threshold / 2.0
                if drawdown_guard_recovery is None
                else drawdown_guard_recovery
            )
            prior_drawdown = current_equity / peak_equity - 1.0
            if (
                drawdown_guard_cooldown_hours is None
                and drawdown_guard_active
                and prior_drawdown >= -abs(recovery)
            ):
                drawdown_guard_active = False
            elif (
                not drawdown_guard_active
                and prior_drawdown <= -abs(drawdown_guard_threshold)
            ):
                drawdown_guard_active = True
                if drawdown_guard_cooldown_hours is not None:
                    drawdown_guard_until = i + drawdown_guard_cooldown_hours
        guard_factor = (
            drawdown_guard_multiplier if drawdown_guard_active else 1.0
        )
        opened = opened_values[i]
        previous_close = close_values[i - 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = opened / previous_close
        ratio = np.where(np.isfinite(ratio), ratio, 1.0)
        overnight_factor = 1.0 + float(np.sum(weights * (ratio - 1.0)))
        if overnight_factor <= maintenance_equity_fraction:
            current_equity = 0.0
            ruined = True
            equity_values[i:] = 0.0
            break
        current_equity *= overnight_factor
        weights = np.nan_to_num(weights * ratio / overnight_factor)

        funding_contribution = weights * funding_values[i]
        fund_fraction = float(
            np.clip(funding_contribution, 0.0, None).sum()
            * funding_debit_multiplier
            + np.clip(funding_contribution, None, 0.0).sum()
            * funding_credit_multiplier
        )
        funding_value = current_equity * fund_fraction
        current_equity -= funding_value
        funding_cost_values[i] = funding_value

        requested_target = target_values[i - 1].copy() * guard_factor
        signal_event = float(
            np.abs(requested_target - last_requested_target).sum()
        ) > 1e-12
        last_requested_target = requested_target.copy()
        tradable = np.isfinite(opened) & np.isfinite(close_values[i])
        forced_exit = bool(np.any((np.abs(weights) > 1e-12) & ~tradable))
        prior_close_gross = float(np.abs(position_values[i - 1]).sum())
        guard_event = bool(
            gross_guard_cap is not None
            and prior_close_gross > gross_guard_cap + 1e-12
        )
        if signal_event or forced_exit or guard_event:
            target = requested_target if signal_event else weights.copy()
            target = np.where(tradable, target, 0.0)
            if gross_guard_cap is not None:
                target_gross = float(np.abs(target).sum())
                if target_gross > gross_guard_cap:
                    target *= gross_guard_cap / target_gross
            traded = float(np.abs(target - weights).sum())
            fee = current_equity * traded * cost_per_side
            current_equity -= fee
            turnover_values[i] = traded
            fee_values[i] = fee
            weights = target

        with np.errstate(divide="ignore", invalid="ignore"):
            low_move = low_values[i] / opened - 1.0
            high_move = high_values[i] / opened - 1.0
        low_move = np.where(np.isfinite(low_move), low_move, 0.0)
        high_move = np.where(np.isfinite(high_move), high_move, 0.0)
        adverse = np.where(weights >= 0.0, low_move, high_move)
        worst_factor = 1.0 + float(np.sum(weights * adverse))
        if worst_factor <= maintenance_equity_fraction:
            current_equity = 0.0
            ruined = True
            equity_values[i:] = 0.0
            position_values[i:] = 0.0
            break

        with np.errstate(divide="ignore", invalid="ignore"):
            close_move = close_values[i] / opened - 1.0
        close_move = np.where(np.isfinite(close_move), close_move, 0.0)
        close_factor = 1.0 + float(np.sum(weights * close_move))
        if close_factor <= maintenance_equity_fraction:
            current_equity = 0.0
            ruined = True
            equity_values[i:] = 0.0
            break
        current_equity *= close_factor
        weights = np.nan_to_num(weights * (1.0 + close_move) / close_factor)
        equity_values[i] = current_equity
        position_values[i] = weights
        peak_equity = max(peak_equity, current_equity)

    equity = pd.Series(equity_values, index=index).ffill().fillna(1.0)
    positions = pd.DataFrame(position_values, index=index, columns=columns)
    turnover = pd.Series(turnover_values, index=index)
    fees = pd.Series(fee_values, index=index)
    funding_cost = pd.Series(funding_cost_values, index=index)
    gross = positions.abs().sum(axis=1)
    return BacktestResult(equity, positions, turnover, fees, funding_cost, gross, ruined)
