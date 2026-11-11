"""V98-only causal hourly accounting kernel for B0 integration.

Weights decided after bar t close are held over t->t+1. Funding is signed
(long pays positive funding; short receives it). No future prices in decisions.
This is an accounting component, not a validated strategy or trading system.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class LedgerState:
    equity: float
    peak: float
    weights: dict

def _finite(value, label):
    if not math.isfinite(float(value)):
        raise ValueError(label)
    return float(value)

def transition(state, next_returns, next_funding, target_weights,
               *, fee_rate, slippage_rate, funding_scale=1.0):
    """Execute precommitted weights during next bar, then rebalance at its close.

    Returns (new_state, audit). All return/funding inputs belong to the
    completed bar. Target weights must have been computed without those inputs.
    Trading costs apply to the close rebalance; next bar earns target exposure.
    """
    if state.equity <= 0 or state.peak < state.equity:
        raise ValueError("INVALID_STATE")
    keys = set(state.weights)
    if not keys or keys != set(next_returns) or keys != set(next_funding) or keys != set(target_weights):
        raise ValueError("ASSET_GRID_MISMATCH")
    for key in keys:
        for val in (state.weights[key], next_returns[key], next_funding[key], target_weights[key]):
            _finite(val, "NONFINITE_INPUT")
    fee = _finite(fee_rate, "NONFINITE_FEE")
    slip = _finite(slippage_rate, "NONFINITE_SLIPPAGE")
    scale = _finite(funding_scale, "NONFINITE_SCALE")
    if min(fee, slip, scale) < 0:
        raise ValueError("NEGATIVE_COST")
    # Drifted weights must be compared against targets at bar close; turnover
    # computed on previous notional would misstate transaction costs.
    gross_return = sum(state.weights[k] * next_returns[k] for k in keys)
    funding_return = -scale * sum(state.weights[k] * next_funding[k] for k in keys)
    pretrade_factor = 1 + gross_return + funding_return
    if pretrade_factor <= 0:
        raise ValueError("INSOLVENT_BAR")
    drifted = {k: state.weights[k] * (1 + next_returns[k]) / pretrade_factor for k in keys}
    turnover = sum(abs(target_weights[k] - drifted[k]) for k in keys)
    cost_return = turnover * (fee + slip)
    if cost_return >= 1:
        raise ValueError("INSOLVENT_COST")
    equity = state.equity * pretrade_factor * (1 - cost_return)
    peak = max(state.peak, equity)
    audit = dict(gross_return=gross_return, funding_return=funding_return,
                 turnover=turnover, cost_return=cost_return,
                 equity_before=state.equity, equity_after=equity,
                 drawdown=1-equity/peak)
    return LedgerState(equity, peak, dict(target_weights)), audit
