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
          maintenance_equity_fraction: float = 0.02) -> BacktestResult:
    """Stateful cross-margin replay with drift and conservative intrabar ruin.

    If all held assets touch their adverse hourly extrema, the portfolio must
    retain more than ``maintenance_equity_fraction`` of equity. This is more
    conservative than assuming a favorable order among hourly high/low events.
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
    weights = pd.Series(0.0, index=columns)
    ruined = False
    for i, timestamp in enumerate(index):
        if i == 0:
            equity.iloc[i] = current_equity
            continue
        previous = index[i - 1]
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
        fund_fraction = float((weights * data.funding.loc[timestamp]).sum())
        funding_value = current_equity * fund_fraction
        current_equity -= funding_value
        funding_cost.iloc[i] = funding_value

        target = targets.iloc[i - 1].copy()
        prior_target = targets.iloc[i - 2] if i >= 2 else target * 0.0
        signal_event = float((target - prior_target).abs().sum()) > 1e-12
        tradable = opened.notna() & data.close.loc[timestamp].notna()
        forced_exit = bool((weights.abs().gt(1e-12) & ~tradable).any())
        if signal_event or forced_exit:
            target = target.where(tradable, 0.0)
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
    return BacktestResult(equity.ffill().fillna(1.0), positions_out, turnover, fees,
                          funding_cost, positions_out.abs().sum(axis=1), ruined)
