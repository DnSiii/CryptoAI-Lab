#!/usr/bin/env python3
"""Independent net-asset round-trip lot metrics from V98 physical hourly ledger.
Infrastructure only: no candidate selection, no future holdout, no live authorization.
"""
import math
import numpy as np

def roundtrip_metrics(d,ledger,fee_rate,slip_rate,order):
    """Reconstruct closed *net asset position* round trips; not virtual sleeve trades.

    Ledger entries: (t, nav_before, nav_after, funding_cash, fees, slip, virtual_qty, gap).
    Native funding is worst-side envelope, not exact event mark. Assumes one-way netting.
    """
    if order not in ("carried_before_fill","new_after_fill"):raise ValueError("TRADE_ORDER")
    if not math.isfinite(fee_rate+slip_rate) or min(fee_rate,slip_rate)<0:raise ValueError("TRADE_COST")
    if not ledger:raise ValueError("TRADE_EMPTY_LEDGER")
    old=np.zeros(4,float);active=[None]*4;closed=[]
    prior_nav=10000.;mismatch=0;max_error=0.;last_t=None
    def open_trade(j,qty,px,cost,t):
        return {"asset":j,"side":1 if qty>0 else -1,"start":t,
                "qty":float(qty),"entry":float(px),"pnl":-float(cost)}
    def close_trade(j,t):
        tr=active[j]
        if tr is None:raise ValueError("TRADE_CLOSE_WITHOUT_OPEN")
        closed.append({"asset":j,"side":tr["side"],"start":tr["start"],
                       "end":t,"net_pnl":float(tr["pnl"])})
        active[j]=None
    for t,before,nav,funding,fees,slippage,virtual,gap in ledger:
        if last_t is not None and t!=last_t+1:raise ValueError("TRADE_CLOCK_GAP")
        last_t=t
        new=np.asarray(virtual,float).sum(axis=0)
        px=np.asarray(d["o"][t],float)
        if new.shape!=(4,) or np.any(px<=0) or not np.isfinite(new).all():
            raise ValueError("TRADE_GEOMETRY")
        if abs(before-prior_nav)>1e-6:mismatch+=1
        delta=new-old
        est_fee=float(np.dot(np.abs(delta),px))*fee_rate
        est_slip=float(np.dot(np.abs(delta),px))*slip_rate
        err=max(abs(est_fee-fees),abs(est_slip-slippage))
        max_error=max(max_error,err)
        if err>1e-6:mismatch+=1
        if order=="carried_before_fill":
            payer=old
        else:
            payer=new
        cash_by_asset=np.zeros(4,float)
        for j in range(4):
            if bool(d["event"][t,j]):
                r=float(d["rate"][t,j]);obligation=float(payer[j]*r)
                mark=float(d["mark_upper"][t,j] if obligation>=0 else d["mark_lower"][t,j])
                cash_by_asset[j]=-obligation*mark
        err=abs(float(cash_by_asset.sum())-funding)
        max_error=max(max_error,err)
        if err>1e-6:mismatch+=1
        if order=="carried_before_fill":
            for j in range(4):
                if abs(cash_by_asset[j])>0:
                    if active[j] is None:raise ValueError("TRADE_CARRIED_FUNDING_WITHOUT_LOT")
                    active[j]["pnl"]+=cash_by_asset[j]
        for j in range(4):
            oldj=float(old[j]);newj=float(new[j]);price=float(px[j])
            if abs(oldj)<1e-12:oldj=0.
            if abs(newj)<1e-12:newj=0.
            if oldj==0. and newj==0.:continue
            if oldj==0.:
                active[j]=open_trade(j,newj,price,abs(newj)*price*(fee_rate+slip_rate),t)
            elif newj==0.:
                tr=active[j]
                if tr is None:raise ValueError("TRADE_LOT_MISSING")
                tr["pnl"]+=oldj*(price-tr["entry"])-abs(oldj)*price*(fee_rate+slip_rate)
                close_trade(j,t)
            elif oldj*newj<0:
                tr=active[j]
                if tr is None:raise ValueError("TRADE_FLIP_LOT_MISSING")
                tr["pnl"]+=oldj*(price-tr["entry"])-abs(oldj)*price*(fee_rate+slip_rate)
                close_trade(j,t)
                active[j]=open_trade(j,newj,price,abs(newj)*price*(fee_rate+slip_rate),t)
            elif abs(newj)>abs(oldj):
                tr=active[j]
                if tr is None:raise ValueError("TRADE_ADD_LOT_MISSING")
                added=abs(newj)-abs(oldj)
                tr["entry"]=(abs(oldj)*tr["entry"]+added*price)/abs(newj)
                tr["qty"]=newj
                tr["pnl"]-=added*price*(fee_rate+slip_rate)
            elif abs(newj)<abs(oldj):
                tr=active[j]
                if tr is None:raise ValueError("TRADE_PARTIAL_LOT_MISSING")
                reduced=abs(oldj)-abs(newj)
                tr["pnl"]+=math.copysign(reduced,oldj)*(price-tr["entry"])
                tr["pnl"]-=reduced*price*(fee_rate+slip_rate)
                tr["qty"]=newj
            else:
                tr=active[j]
                if tr is None:raise ValueError("TRADE_HOLD_LOT_MISSING")
                tr["qty"]=newj
        if order=="new_after_fill":
            for j in range(4):
                if abs(cash_by_asset[j])>0:
                    if active[j] is None:raise ValueError("TRADE_NEW_FUNDING_WITHOUT_LOT")
                    active[j]["pnl"]+=cash_by_asset[j]
        old=new;prior_nav=float(nav)
    last_close=np.asarray(d["c"][last_t],float)
    open_pnl=0.;open_count=0
    for j,tr in enumerate(active):
        if tr is not None:
            open_count+=1
            open_pnl+=tr["pnl"]+tr["qty"]*(float(last_close[j])-tr["entry"])
    realized=sum(x["net_pnl"] for x in closed)
    reconciled=realized+open_pnl
    nav_err=abs(reconciled-(prior_nav-10000.))
    max_error=max(max_error,nav_err)
    if nav_err>max(1e-5,1e-8*abs(prior_nav)):mismatch+=1
    wins=[x["net_pnl"] for x in closed if x["net_pnl"]>1e-10]
    losses=[-x["net_pnl"] for x in closed if x["net_pnl"]< -1e-10]
    pf=sum(wins)/sum(losses) if losses else None
    payoff=(sum(wins)/len(wins))/(sum(losses)/len(losses)) if wins and losses else None
    return {"decision":"PASS_TRADE_LOT_ACCOUNTING_ONLY_NOT_ENGINE" if not mismatch else "FAIL_TRADE_LOT_ACCOUNTING",
            "closed_net_asset_roundtrips":len(closed),"open_net_asset_roundtrips":open_count,
            "closed_wins":len(wins),"closed_losses":len(losses),
            "trade_win_rate":len(wins)/len(closed) if closed else None,
            "trade_profit_factor":pf,"trade_payoff":payoff,
            "closed_realized_pnl":realized,"open_marked_pnl":open_pnl,
            "nav_delta":prior_nav-10000.,"nav_reconciliation_error":nav_err,
            "mismatches":mismatch,"max_absolute_error":max_error,
            "native_exact_mark_attested":False,"independent_trade_fill_source_attested":False,
            "not_strategy_pnl_or_trade_execution_proof":True}

def synthetic_tests():
    """Synthetic physical-like ledger: price gaps, partial closes, flips, costs and funding."""
    rng=np.random.default_rng(980111)
    n=600
    d={k:np.zeros((n,4),float) for k in ("o","c","rate","mark_lower","mark_upper")}
    d["event"]=np.zeros((n,4),bool)
    prices=np.array([100.,200.,50.,25.])
    q=np.zeros(4);nav=10000.;ledger=[]
    fee=.0004;slip=.0002
    for t in range(1,n):
        px=prices*np.exp(rng.normal(0,.004,4))
        end=px*np.exp(rng.normal(0,.004,4))
        d["o"][t]=px;d["c"][t]=end
        if t%8==0:
            d["event"][t]=True
            d["rate"][t]=rng.normal(.0001,.0001,4)
            d["mark_lower"][t]=np.minimum(px,end)*.995
            d["mark_upper"][t]=np.maximum(px,end)*1.005
        old=q.copy()
        new=np.where(rng.random(4)<.12,rng.choice([-1,0,1],4)*rng.uniform(0,2,4),old)
        gap=float(np.dot(old,px-prices))
        delta=new-old
        fees=float(np.dot(abs(delta),px))*fee
        slippage=float(np.dot(abs(delta),px))*slip
        payer=old
        funding=0.
        if t%8==0:
            for j in range(4):
                ob=payer[j]*d["rate"][t,j]
                funding-=ob*(d["mark_upper"][t,j] if ob>=0 else d["mark_lower"][t,j])
        before=nav
        nav+=gap-fees-slippage+funding+float(np.dot(new,end-px))
        v=np.zeros((4,4));v[0]=new
        ledger.append((t,before,nav,funding,fees,slippage,v,gap))
        prices=end;q=new
    out=roundtrip_metrics(d,ledger,fee,slip,"carried_before_fill")
    assert out["mismatches"]==0 and out["nav_reconciliation_error"]<1e-5,out
    assert out["closed_net_asset_roundtrips"]>0
    assert out["trade_win_rate"] is not None
    assert out["trade_profit_factor"] is not None
    # A forged NAV must fail, rather than being reported as a successful metric.
    tampered=list(ledger)
    row=list(tampered[-1]);row[2]+=10.;tampered[-1]=tuple(row)
    bad=roundtrip_metrics(d,tampered,fee,slip,"carried_before_fill")
    assert bad["mismatches"]>0
    return out

if __name__=="__main__":
    import json
    print(json.dumps(synthetic_tests(),sort_keys=True))
