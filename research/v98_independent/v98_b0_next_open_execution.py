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
    if set(bars) != set(ASSETS) or set(funding) != set(ASSETS):
        raise ValueError("INVALID_CLEAN4_ASSETS")
    n = len(bars[ASSETS[0]])
    if n < 3 or any(len(bars[a]) != n for a in ASSETS):
        raise ValueError("INVALID_CLEAN4_LENGTH")
    if not all(math.isfinite(float(v)) for v in (initial_equity, fee_rate, slippage_rate, cost_scale)) or not (initial_equity > 0 and fee_rate >= 0 and slippage_rate >= 0 and cost_scale >= 0):
        raise ValueError("INVALID_ACCOUNT")
    if any(not math.isfinite(float(rate)) for a in ASSETS for rate in funding[a].values()):
        raise ValueError("INVALID_NATIVE_FUNDING")
    equity = peak = float(initial_equity)
    weights = {a:0. for a in ASSETS}
    histories = {a:[] for a in ASSETS}
    entries = []
    max_drawdown = 0.
    # Bar i open: mark holdings from open i-1, then apply funding, then fill
    # target based ONLY on close i-1. No current-bar close is accessible.
    for i in range(n):
        if i:
            returns = {a: bars[a][i][0]/bars[a][i-1][0]-1 for a in ASSETS}
            gross_by_asset = {a:weights[a]*returns[a] for a in ASSETS}
            funding_by_asset = {a:-weights[a]*funding[a].get(i,0.) for a in ASSETS}
            gross = sum(gross_by_asset.values())
            carry = sum(funding_by_asset.values())
            factor = 1+gross+carry
            if not math.isfinite(factor) or factor <= 0:
                raise ValueError("INSOLVENT_MARK")
            equity *= factor
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, 1-equity/peak)
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
            pre_fill_equity = equity
            previous_weights = dict(weights)
            equity *= (1-cost)
            weights = dict(target)
            peak = max(peak,equity)
            drawdown = 1-equity/peak
            max_drawdown = max(max_drawdown, drawdown)
            entries.append(dict(index=i, equity=equity, pre_fill_equity=pre_fill_equity,
                                weights_before_fill=previous_weights, weights_after_fill=dict(weights),
                                turnover=turnover, cost_return=cost, drawdown=drawdown,
                                gross_return=gross, funding_return=carry,
                                gross_by_asset=gross_by_asset,
                                funding_by_asset=funding_by_asset))
        for a in ASSETS:
            histories[a].append(bars[a][i][3])
    # Final open-to-close mark; do not fill after the sample ends.
    final_return = {a:bars[a][-1][3]/bars[a][-1][0]-1 for a in ASSETS}
    final_factor = 1+sum(weights[a]*final_return[a] for a in ASSETS)
    if not math.isfinite(final_factor) or final_factor <= 0:
        raise ValueError("INSOLVENT_FINAL_MARK")
    equity *= final_factor
    peak = max(peak,equity)
    max_drawdown = max(max_drawdown, 1-equity/peak)
    return dict(final_equity=equity, max_drawdown=max_drawdown,
        total_turnover=sum(e["turnover"] for e in entries),
        funding_return_sum=sum(e["funding_return"] for e in entries),
        hours=n, execution="NEXT_OPEN_CAUSAL_RESEARCH"), entries
