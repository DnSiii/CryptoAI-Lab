"""C8 preregistered execution-policy counterfactual, training only.

Hypothesis: avoid intraday drift rebalancing while retaining immediate risk
reductions. Same causal signals, prices, funding, fees and slippage as baseline.
No holdout, no parameter search, no promotion from this comparison.
"""
import math
from .v98_b0_causal_overlay import regime_multiplier, governor_multiplier, compose_weights
from .v98_b0_stream_integration import ASSETS

def replay_c8_daily_risk(bars, funding, sleeve_fn, *, initial_equity=10000.,
                         fee_rate=.0004, slippage_rate=.0002, cost_scale=1.):
    if set(bars)!=set(ASSETS) or set(funding)!=set(ASSETS):
        raise ValueError("INVALID_CLEAN4_ASSETS")
    n=len(bars[ASSETS[0]])
    if n<3 or any(len(bars[a])!=n for a in ASSETS):
        raise ValueError("INVALID_CLEAN4_LENGTH")
    if not all(math.isfinite(float(v)) for v in (initial_equity,fee_rate,slippage_rate,cost_scale)) or not (initial_equity>0 and fee_rate>=0 and slippage_rate>=0 and cost_scale>=0):
        raise ValueError("INVALID_ACCOUNT")
    # Fail closed on corrupt candles before calculating system PnL.
    for asset in ASSETS:
        for bar in bars[asset]:
            if len(bar) != 5 or any(not math.isfinite(float(v)) for v in bar):
                raise ValueError("INVALID_CLEAN4_OHLC")
            o, h, l, c, volume = map(float, bar)
            if min(o, h, l, c) <= 0 or volume < 0 or l > min(o, c) or h < max(o, c) or l > h:
                raise ValueError("INVALID_CLEAN4_OHLC")
    if any(not math.isfinite(float(v)) for a in ASSETS for v in funding[a].values()):
        raise ValueError("INVALID_NATIVE_FUNDING")
    equity=peak=float(initial_equity)
    weights={a:0. for a in ASSETS}
    histories={a:[] for a in ASSETS}
    entries=[]
    max_drawdown=0.
    for i in range(n):
        # Snapshot known before open i: never use the opening mark to decide
        # a governor order filled at that same opening price.
        causal_governor = governor_multiplier(equity, peak)
        gross=carry=0.
        gross_by_asset={a:0. for a in ASSETS}
        funding_by_asset={a:0. for a in ASSETS}
        if i:
            returns={a:bars[a][i][0]/bars[a][i-1][0]-1 for a in ASSETS}
            gross_by_asset={a:weights[a]*returns[a] for a in ASSETS}
            funding_by_asset={a:-weights[a]*funding[a].get(i,0.) for a in ASSETS}
            gross=sum(gross_by_asset.values())
            carry=sum(funding_by_asset.values())
            factor=1+gross+carry
            if not math.isfinite(factor) or factor<=0:
                raise ValueError("INSOLVENT_MARK")
            equity*=factor
            peak=max(peak,equity)
            max_drawdown=max(max_drawdown,1-equity/peak)
            weights={a:weights[a]*(1+returns[a])/factor for a in ASSETS}
        if i:
            sleeves=sleeve_fn({a:tuple(histories[a]) for a in ASSETS})
            routers={a:regime_multiplier(histories[a]) for a in ASSETS}
            governor=causal_governor
            target=compose_weights(sleeves,routers,governor)
            if i%24:
                # No risk increases between decisions. Apply asset-specific
                # exposure cuts immediately; leave all other holdings untouched.
                target={a:min(weights[a],target[a]) for a in ASSETS}
            turnover=sum(abs(target[a]-weights[a]) for a in ASSETS)
            cost=turnover*(fee_rate+slippage_rate)*cost_scale
            if not math.isfinite(cost) or cost>=1:
                raise ValueError("INSOLVENT_COST")
            pre_fill_equity=equity
            previous_weights=dict(weights)
            equity*=(1-cost)
            weights=dict(target)
            peak=max(peak,equity)
            drawdown=1-equity/peak
            max_drawdown=max(max_drawdown,drawdown)
            entries.append(dict(index=i,equity=equity,pre_fill_equity=pre_fill_equity,
                weights_before_fill=previous_weights,weights_after_fill=dict(weights),
                turnover=turnover,cost_return=cost,drawdown=drawdown,
                gross_return=gross,funding_return=carry,
                gross_by_asset=gross_by_asset,funding_by_asset=funding_by_asset))
        for a in ASSETS:
            histories[a].append(bars[a][i][3])
    final_factor=1+sum(weights[a]*(bars[a][-1][3]/bars[a][-1][0]-1) for a in ASSETS)
    if not math.isfinite(final_factor) or final_factor<=0:
        raise ValueError("INSOLVENT_FINAL_MARK")
    equity*=final_factor
    peak=max(peak,equity)
    max_drawdown=max(max_drawdown,1-equity/peak)
    return dict(final_equity=equity,max_drawdown=max_drawdown,
        total_turnover=sum(e["turnover"] for e in entries),
        funding_return_sum=sum(e["funding_return"] for e in entries),
        hours=n,execution="C8_DAILY_WITH_INTRADAY_RISK_CUTS_TRAINING_ONLY"),entries
