"""C27 variable-horizon continuation kernel. Research-only; no automatic promotion.

Consumes an independently attested state at the first prospective open. No
training-period reset, no parameter fitting and no access to future closes.
This kernel intentionally does not authenticate the state or its market source.
"""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_composed_c26 import c26_model, c26_allocator, WARMUP
from .v98_c27_two_clock_governor import planned_trim, execute_queued_units
from .v98_c27_authenticated_runner import ASSET_BUFFER, GROSS_BUFFER
from .v98_b0_causal_overlay import governor_multiplier

def continue_replay(bars, funding, scale, state):
    """State is the exact pre-open portfolio/strategy checkpoint, not a fabricated reset.

    Required: equity, peak, weights, queued, histories, decision_equity,
    decision_peak, absolute_index. The histories contain closes strictly
    preceding the first prospective open. The first open is valued against
    state['previous_open'] for each asset, and funding for that interval is
    indexed at prospective hour zero. No pending order may be silently dropped.
    """
    if scale not in (1., 2., 4., 8., 12.):
        raise ValueError("C27_CONTINUATION_UNREGISTERED_COST")
    if set(bars)!=set(ASSETS) or set(funding)!=set(ASSETS):
        raise ValueError("C27_CONTINUATION_ASSETS")
    n=len(bars[ASSETS[0]])
    if n<2 or any(len(bars[a])!=n for a in ASSETS):
        raise ValueError("C27_CONTINUATION_HOURS")
    required={"equity","peak","weights","queued","histories",
              "decision_equity","decision_peak","absolute_index","previous_open"}
    if set(state)!=required:
        raise ValueError("C27_CONTINUATION_STATE_SCHEMA")
    for k in ("weights","queued","histories","previous_open"):
        if set(state[k])!=set(ASSETS):
            raise ValueError("C27_CONTINUATION_STATE_ASSETS")
    scalar=("equity","peak","decision_equity","decision_peak")
    if any(not isinstance(state[k],(int,float)) or isinstance(state[k],bool)
           or not math.isfinite(state[k]) or state[k]<=0 for k in scalar):
        raise ValueError("C27_CONTINUATION_EQUITY")
    if state["peak"]<state["equity"] or state["decision_peak"]<state["decision_equity"]:
        raise ValueError("C27_CONTINUATION_PEAK")
    start=state["absolute_index"]
    if type(start)!=int or start<WARMUP+2:
        raise ValueError("C27_CONTINUATION_INDEX")
    weights=dict(state["weights"])
    queued=dict(state["queued"])
    histories={a:list(state["histories"][a]) for a in ASSETS}
    previous_open=dict(state["previous_open"])
    for a in ASSETS:
        if len(histories[a])!=start or any(not math.isfinite(float(x)) or x<=0 for x in histories[a]):
            raise ValueError("C27_CONTINUATION_HISTORY")
        if not math.isfinite(float(previous_open[a])) or previous_open[a]<=0:
            raise ValueError("C27_CONTINUATION_PREVIOUS_MARK")
        if any(type(x) not in (int, float) or not math.isfinite(x)
               for x in (weights[a], queued[a])):
            raise ValueError("C27_CONTINUATION_BOOK_NONFINITE")
        if not 0<=weights[a]<=ASSET_BUFFER+1e-10 or not 0<=queued[a]<=1:
            raise ValueError("C27_CONTINUATION_BOOK")
        if any(type(i)!=int or i<0 or i>=n or not math.isfinite(float(v))
               for i,v in funding[a].items()):
            raise ValueError("C27_CONTINUATION_FUNDING")
        for row in bars[a]:
            if len(row)!=5 or any(not math.isfinite(float(x)) for x in row):
                raise ValueError("C27_CONTINUATION_OHLC")
            o,h,l,c,v=map(float,row)
            if min(o,h,l,c)<=0 or l>min(o,c) or h>0 and h<max(o,c) or v<0:
                raise ValueError("C27_CONTINUATION_OHLC")
    if sum(weights.values())>GROSS_BUFFER+1e-10:
        raise ValueError("C27_CONTINUATION_GROSS")
    equity=float(state["equity"])
    peak=float(state["peak"])
    decision_equity=float(state["decision_equity"])
    decision_peak=float(state["decision_peak"])
    model,router=c26_model()
    ledger=[]
    max_dd=0.
    for t in range(n):
        i=start+t
        previous=dict(weights)
        returns={a:float(bars[a][t][0])/previous_open[a]-1 for a in ASSETS}
        gross_by_asset={a:previous[a]*returns[a] for a in ASSETS}
        funding_by_asset={a:-previous[a]*funding[a].get(t,0.) for a in ASSETS}
        gross=sum(gross_by_asset.values())
        carry=sum(funding_by_asset.values())
        factor=1+gross+carry
        if not math.isfinite(factor) or factor<=0:
            raise ValueError("C27_CONTINUATION_INSOLVENT_MARK")
        equity*=factor
        marked={a:previous[a]*(1+returns[a])/factor for a in ASSETS}
        post_queue=execute_queued_units(marked,queued)
        strategic=(i>=WARMUP+1 and (i-(WARMUP+1))%168==0)
        if strategic:
            history={a:tuple(histories[a]) for a in ASSETS}
            cached=model(history)
            router_value=router(history["BTCUSDT"])
            target=c26_allocator(cached,{a:router_value for a in ASSETS},
                                 governor_multiplier(decision_equity,decision_peak))
            target={a:max(0.,min(float(target[a]),ASSET_BUFFER)) for a in ASSETS}
            total=sum(target.values())
            if total>GROSS_BUFFER:
                target={a:target[a]*GROSS_BUFFER/total for a in ASSETS}
            order_type="strategic"
        else:
            target=post_queue
            order_type="safety" if any(queued.values()) else "hold"
        turnover=sum(abs(target[a]-marked[a]) for a in ASSETS)
        cost=turnover*.0006*scale
        if not math.isfinite(cost) or cost>=1:
            raise ValueError("C27_CONTINUATION_INSOLVENT_COST")
        peak=max(peak,equity)
        max_dd=max(max_dd,1-equity/peak)
        equity*=1-cost
        weights=dict(target)
        peak=max(peak,equity)
        max_dd=max(max_dd,1-equity/peak)
        buffered=planned_trim(weights,asset_cap=ASSET_BUFFER,gross_cap=GROSS_BUFFER)
        queued={a:0. if weights[a]<=1e-12 else max(0.,min(1.,1-buffered[a]/weights[a]))
                for a in ASSETS}
        ledger.append(dict(index=i,equity=equity,turnover=turnover,cost_return=cost,
                           gross_return=gross,funding_return=carry,order_type=order_type,
                           weights_after_fill=dict(weights),queued_next_open_sell_fractions=dict(queued)))
        decision_equity=equity
        decision_peak=peak
        for a in ASSETS:
            histories[a].append(float(bars[a][t][3]))
            previous_open[a]=float(bars[a][t][0])
    # No fabricated terminal close liquidation; final open-to-close mark is reported
    # separately, matching the training executor convention.
    final_factor=1+sum(weights[a]*(float(bars[a][-1][3])/float(bars[a][-1][0])-1) for a in ASSETS)
    if final_factor<=0 or not math.isfinite(final_factor):
        raise ValueError("C27_CONTINUATION_INSOLVENT_FINAL")
    final_equity=equity*final_factor
    max_dd=max(max_dd,1-final_equity/max(peak,final_equity))
    return dict(status="UNATTESTED_RESEARCH_REPLAY_NOT_VALIDATION",
                final_equity=final_equity,max_drawdown=max_dd,
                hours=n,scale=scale,ledger=ledger,
                carry_out=dict(equity=equity,peak=peak,weights=weights,queued=queued,
                               histories=histories,decision_equity=decision_equity,
                               decision_peak=decision_peak,absolute_index=start+n,
                               previous_open=previous_open))
