"""V98 B0 next-open execution research harness; no holdout or live orders.

Completed close t determines the target filled at open t+1. Funding stamped
at open t+1 is charged to the PREVIOUS exposure before the fill (conservative
boundary convention). Mark-to-market is open-to-open; fees/slippage on traded
notional. The final bar is marked to its close without a fictional next fill.
"""
import math
from .v98_b0_causal_overlay import regime_multiplier, governor_multiplier, compose_weights
from .v98_b0_stream_integration import ASSETS

def replay_next_open(bars, funding, sleeve_fn, *, initial_equity=10000.,
                     fee_rate=.0004, slippage_rate=.0002, cost_scale=1.):
    n = len(bars[ASSETS[0]])
    if n < 3 or any(len(bars[a]) != n for a in ASSETS):
        raise ValueError("INVALID_CLEAN4_LENGTH")
    if not (initial_equity > 0 and cost_scale >= 0):
        raise ValueError("INVALID_ACCOUNT")
    equity = peak = float(initial_equity)
    weights = {a:0. for a in ASSETS}
    histories = {a:[] for a in ASSETS}
    entries = []
    # Bar i open: mark holdings from open i-1, then apply funding, then fill
    # target based ONLY on close i-1. No current-bar close is accessible.
    for i in range(n):
        if i:
            returns = {a: bars[a][i][0]/bars[a][i-1][0]-1 for a in ASSETS}
            gross = sum(weights[a]*returns[a] for a in ASSETS)
            carry = -sum(weights[a]*funding[a].get(i,0.) for a in ASSETS)
            factor = 1+gross+carry
            if not math.isfinite(factor) or factor <= 0:
                raise ValueError("INSOLVENT_MARK")
            equity *= factor
            weights = {a:weights[a]*(1+returns[a])/factor for a in ASSETS}
        if i:
            sleeves = sleeve_fn({a:tuple(histories[a]) for a in ASSETS})
            routers = {a:regime_multiplier(histories[a]) for a in ASSETS}
            governor = governor_multiplier(equity, peak)
            target = compose_weights(sleeves, routers, governor)
            turnover = sum(abs(target[a]-weights[a]) for a in ASSETS)
            cost = turnover*(fee_rate+slippage_rate)*cost_scale
            if not math.isfinite(cost) or cost >= 1:
                raise ValueError("INSOLVENT_COST")
            equity *= (1-cost)
            weights = dict(target)
            peak = max(peak,equity)
            entries.append(dict(index=i, equity=equity, turnover=turnover,
                                cost_return=cost, drawdown=1-equity/peak,
                                gross_return=gross, funding_return=carry))
        for a in ASSETS:
            histories[a].append(bars[a][i][3])
    # Final open-to-close mark; do not fill after the sample ends.
    final_return = {a:bars[a][-1][3]/bars[a][-1][0]-1 for a in ASSETS}
    equity *= 1+sum(weights[a]*final_return[a] for a in ASSETS)
    peak = max(peak,equity)
    return dict(final_equity=equity, max_drawdown=max(
        [1-equity/peak]+[e["drawdown"] for e in entries]),
        total_turnover=sum(e["turnover"] for e in entries),
        funding_return_sum=sum(e["funding_return"] for e in entries),
        hours=n, execution="NEXT_OPEN_CAUSAL_RESEARCH"), entries
