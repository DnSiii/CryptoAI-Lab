#!/usr/bin/env python3
"""V98 OT: preregistered 2022-25 exploratory TRAINING seven-slot engine.
No benchmark, 2026+, contaminated holdout, paper/live or exact tick mark claims.
"""
import json, math
from pathlib import Path
import numpy as np
from v98_oneway_net_atomic_planner import plan_virtual, settle_virtual
from v98_mark_envelope_settlement import worst_funding

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
WARMUP=744
STEP=168
HOURS=27048
COSTS={"base":(.0004,.0002),"severe":(.001,.001),"supersevere":(.0015,.002)}
ORDERS=("carried_before_fill","new_after_fill")
BOOKS={
    "OT_full":(0,1,2,3),
    "OT_core_only":(0,),
    "OT_minus_opportunity":(0,2,3),
    "OT_minus_RV":(0,1,3),
    "OT_minus_stress":(0,1,2),
}
PRIORITY={
    "positive":(1,2,3),
    "negative":(3,2,1),
    "mixed":(2,1,3),
}
MULT={
    "positive":(1.,.75,.5),
    "negative":(.5,1.,1.),
    "mixed":(.75,1.,.75),
}
YEAREND={9503:2023,18287:2024,27047:2025}

def source_gate(d):
    required=("o","h","l","c","q","rate","event","mark_lower","mark_upper","time","execution_allowed")
    if not all(k in d for k in required): raise ValueError("OT_SOURCE_MISSING")
    if any(np.asarray(d[k]).shape!=(HOURS,4) for k in required[:-2]):
        raise ValueError("OT_SOURCE_SHAPE")
    if len(d["time"])!=HOURS or d["time"][0].year!=2022 or d["time"][-1].year!=2025:
        raise ValueError("OT_SOURCE_TIME")
    if not d["training_only"] or not d["year_2025_exposed"] or d["exact_funding_tick_mark"] or d["holdout_accessed"]:
        raise ValueError("OT_SOURCE_PROVENANCE")
    if int(d["event"].sum())!=13524 or not np.all(d["event"][::8]) or np.any(d["event"][np.arange(HOURS)%8!=0]):
        raise ValueError("OT_SOURCE_FUNDING")
    if not np.array_equal(d["execution_allowed"],d["q"]>0):
        raise ValueError("OT_SOURCE_FILL_MASK")
    for k in ("o","h","l","c","q","rate"):
        if not np.isfinite(d[k]).all(): raise ValueError("OT_SOURCE_NONFINITE_"+k)
    if np.any(d["l"]<=0) or np.any(d["h"]<np.maximum(d["o"],d["c"])) or np.any(d["l"]>np.minimum(d["o"],d["c"])):
        raise ValueError("OT_SOURCE_OHLC")
    if np.any(d["q"]<0) or not np.all(np.isfinite(d["mark_lower"][d["event"]])) or not np.all(np.isfinite(d["mark_upper"][d["event"]])):
        raise ValueError("OT_SOURCE_MARK")
    if np.any(d["mark_lower"][d["event"]]<=0) or np.any(d["mark_upper"][d["event"]]<d["mark_lower"][d["event"]]):
        raise ValueError("OT_SOURCE_MARK_GEOMETRY")
    return {"decision":"PASS_OT_SOURCE_TRAINING_ONLY","hours":HOURS,"events":13524,
            "zero_volume_hours":int(np.sum(~np.asarray(d["execution_allowed"]).all(axis=1)))}

def signals(d):
    """Weekly causal four-sleeve signals, one row per decision, no future rates."""
    p=np.log(d["c"]); q=d["q"]
    result={}
    for t in range(WARMUP,HOURS,STEP):
        r672=p[t]-p[t-672]
        r168=p[t]-p[t-168]
        r72=p[t]-p[t-72]
        r24=p[t]-p[t-24]
        vol=np.std(np.diff(p[t-672:t+1],axis=0),axis=0)*np.sqrt(672)
        quality=(r672+.5*r168)/np.maximum(vol,.04)
        breadth=int(np.sum(r672>0))
        mode="positive" if breadth>=3 else ("negative" if breadth<=1 else "mixed")
        raw=np.zeros((4,4))
        if breadth>=2:
            rank=sorted(range(4),key=lambda j:(-quality[j],j))
            for j,w in zip(rank[:2],(.34,.22)):
                if quality[j]>0:raw[0,j]=w
        else:
            rank=sorted(range(4),key=lambda j:(quality[j],j))
            for j,w in zip(rank[:2],(-.30,-.20)):
                if quality[j]<0:raw[0,j]=w
        eligible=[j for j in range(4) if r72[j]<0 and r24[j]>0
                  and np.sum(q[t-23:t+1,j])>np.sum(q[t-47:t-23,j])]
        if eligible:
            j=sorted(eligible,key=lambda k:(-r24[k],k))[0]
            raw[1,j]=.12
        hi=sorted(range(4),key=lambda j:(-r168[j],j))[0]
        lo=sorted(range(4),key=lambda j:(r168[j],j))[0]
        if r168[hi]-r168[lo]>.16 and r24[hi]<0 and r24[lo]>0:
            raw[2,hi]=-.10;raw[2,lo]=+.10
        if int(np.sum(r24<-.06))>=3:
            j=sorted(range(4),key=lambda k:(r72[k],k))[0]
            raw[3,j]=-.14
        elif int(np.sum(r72<-.08))>=3 and int(np.sum(r24>0))>=3:
            j=sorted(range(4),key=lambda k:(-r24[k],k))[0]
            raw[3,j]=+.14
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        result[t]=(raw,mode)
    if len(result)!=157:raise ValueError("OT_DECISION_CLOCK")
    return result

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OT_ALLOC_INPUT")
    held=np.zeros_like(raw)
    held[0]=raw[0] if 0 in active else 0.
    room=min(.28,max(0.,.84-float(np.abs(held).sum())))
    for k in PRIORITY[mode]:
        if k not in active:continue
        gross=float(np.abs(raw[k]).sum())
        if gross>0 and room>0:
            use=min(gross,room)
            held[k]=raw[k]*(use/gross)
            room-=use
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.28+1e-10:
        raise ValueError("OT_ALLOC_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for name,active in BOOKS.items()}

def physical(d,targets,book,tier,order,record=False):
    fee,slip=COSTS[tier]
    qty=np.zeros((4,4),dtype=float)
    nav=10000.
    equity_path=[];hour_changes=[];ledger=[]
    turnover=fees=slippage=funding=0.
    max_intermediate=max_gross=max_concentration=0.
    min_intrabar=10000.;fills=forced=0
    annual={};annual_start={2023:10000.}
    def reject(why,t):
        return {"passed":False,"book":book,"tier":tier,"order":order,"failure":why,"hour":t,
                "training_only":True},ledger
    for t in range(WARMUP+1,HOURS):
        before=nav
        px=d["o"][t]; close=d["c"][t]; previous=d["c"][t-1]
        gap_cash=float(np.sum(qty*(px-previous)))
        nav+=gap_cash
        if not math.isfinite(nav) or nav<=0:return reject("INSOLVENT_OPEN",t)
        pre_gross=float(np.sum(np.abs(qty)*px))
        pre_net=float(np.sum(np.abs(qty.sum(axis=0))*px))
        max_gross=max(max_gross,pre_gross/nav)
        if max(pre_gross,pre_net)>nav*(1+1e-9):return reject("GAP_GROSS_ABOVE_NAV",t)
        weekly=(t-1) in targets
        event=bool(d["event"][t].any())
        guard=(pre_gross>.82*nav or (event and pre_gross>.80*nav))
        plan=None
        if weekly or guard:
            if weekly:
                weights=targets[t-1]
            else:
                weights=qty*px/nav
                gross=float(np.abs(weights).sum())
                if gross>0:weights*=((.76 if event else .78)/gross)
            try:
                plan=plan_virtual(qty,weights,px,nav,fee,slip,funding_event=event)
            except ValueError as exc:return reject("PLAN_"+str(exc),t)
            if np.any((np.abs(plan["net_delta"])>1e-12)&(~d["execution_allowed"][t])):
                return reject("ZERO_VOLUME_EXECUTION",t)
            max_intermediate=max(max_intermediate,plan["max_intermediate_net_gross_fraction"])
            if plan["turnover"]>1e-8:fills+=1
            if guard and not weekly:forced+=1
        next_qty=plan["virtual_quantity"] if plan is not None else qty
        cash=worst_funding(qty.sum(axis=0),next_qty.sum(axis=0),d["rate"][t],d["event"][t],
                           d["mark_lower"][t],d["mark_upper"][t],order) if event else 0.
        if plan is not None:
            try:nav=settle_virtual(plan,cash,order,nav,qty,px)
            except ValueError as exc:return reject("SETTLEMENT_"+str(exc),t)
            qty=next_qty
            turnover+=plan["turnover"];fees+=plan["fees"];slippage+=plan["slippage"]
        else:nav+=cash
        funding+=cash
        if nav<=0 or not math.isfinite(nav):return reject("INSOLVENT_AFTER_SETTLEMENT",t)
        gross=float(np.sum(np.abs(qty)*px))
        netgross=float(np.sum(np.abs(qty.sum(axis=0))*px))
        max_gross=max(max_gross,gross/nav)
        if max(gross,netgross)>.90*nav+1e-6:return reject("POST_FUNDING_GROSS_CAP",t)
        if gross>0:
            max_concentration=max(max_concentration,float(np.max(np.sum(np.abs(qty)*px,axis=0)))/gross)
        net=qty.sum(axis=0)
        adverse=np.where(net>=0,d["l"][t],d["h"][t])
        intra=nav+float(np.dot(net,adverse-px))
        min_intrabar=min(min_intrabar,intra)
        if intra<=0:return reject("INSOLVENT_INTRABAR",t)
        nav+=float(np.dot(net,close-px))
        if nav<=0 or not math.isfinite(nav):return reject("INSOLVENT_CLOSE",t)
        if float(np.sum(np.abs(qty)*close))>nav*(1+1e-9):
            return reject("CLOSE_VIRTUAL_GROSS_ABOVE_NAV",t)
        if record:
            ledger.append((t,before,nav,cash,float(plan["fees"] if plan else 0.),
                           float(plan["slippage"] if plan else 0.),
                           qty.copy(),gap_cash))
        equity_path.append(nav);hour_changes.append(nav-before)
        if t in YEAREND:
            y=YEAREND[t];annual[y]=nav/annual_start[y]-1
            if y<2025:annual_start[y+1]=nav
    curve=np.asarray(equity_path)
    peak=np.maximum.accumulate(np.r_[10000.,curve])
    dd=float(np.min(np.r_[10000.,curve]/peak-1))
    daily=curve[22::24]
    daily_returns=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
    changes=np.asarray(hour_changes)
    wins=changes[changes>1e-10];loss=-changes[changes< -1e-10]
    log_growth=math.log(nav/10000.)
    return {"passed":True,"book":book,"tier":tier,"order":order,
            "final_equity":float(nav),"cagr":float((nav/10000.)**(365.25/1096.)-1),
            "log_growth":log_growth,"year_returns":{str(y):float(v) for y,v in annual.items()},
            "max_dd":dd,"turnover":turnover,"fees":fees,"slippage":slippage,"funding":funding,
            "max_intermediate_gross_fraction":max_intermediate,"max_pretrade_post_gross_fraction":max_gross,
            "max_single_asset_gross_concentration":max_concentration,
            "min_intrabar_equity":min_intrabar,"physical_fills":fills,"forced_safety_fills":forced,
            "positive_days":int(np.sum(daily_returns>0)),"daily_count":len(daily_returns),
            "daily_win_rate":float(np.mean(daily_returns>0)),
            "daily_cvar_1pct":float(np.mean(np.sort(daily_returns)[:max(1,len(daily_returns)//100)])),
            "hourly_net_pf":float(wins.sum()/loss.sum()) if len(loss) else None,
            "hourly_net_payoff":float(wins.mean()/loss.mean()) if len(wins) and len(loss) else None,
            "hourly_net_win_rate":float(len(wins)/(len(wins)+len(loss))) if len(wins)+len(loss) else 0.,
            "trade_pf_payoff_win_rate_independent":False,
            "training_only":True,"exact_tick_mark":False},ledger

def independent_accounting(d,ledger):
    """Separate event-by-event cash identity, using recorded quantities, not original settlement function."""
    if len(ledger)!=HOURS-WARMUP-1:raise ValueError("OT_LEDGER_LENGTH")
    previous_nav=10000.
    previous_qty=np.zeros((4,4))
    mismatches=0; max_error=0.
    for t,before,nav,funding,fees,slip,qty,gap in ledger:
        if abs(before-previous_nav)>1e-6: mismatches+=1
        px=d["o"][t];close=d["c"][t]
        independent_gap=float(np.sum(previous_qty*(px-d["c"][t-1])))
        expected=previous_nav+independent_gap-fees-slip+funding+float(np.sum(qty*(close-px)))
        error=abs(expected-nav)
        max_error=max(max_error,error)
        if error>1e-6 or abs(gap-independent_gap)>1e-6:mismatches+=1
        previous_nav=nav;previous_qty=qty
    return {"hours_reconciled":len(ledger),"cash_identity_mismatches":mismatches,
            "max_absolute_cash_error":max_error,
            "independent_fill_reconstruction":False,
            "independent_source_reconstruction":False}

def run(d):
    gate=source_gate(d)
    decision=signals(d)
    targets=target_books(decision)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=book=="OT_full" and tier=="base" and order=="carried_before_fill"
                row,detail=physical(d,targets[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OT_CELL",tier,order,book,"PASS",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),
                      "FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            if not all(x["passed"] for x in group.values()):
                failures.append(tier+"/"+order+":physical")
                continue
            full=group["OT_full"]
            marginals[tier+"/"+order]={s:full["log_growth"]-group[book]["log_growth"] for s,book in
                (("Opportunity","OT_minus_opportunity"),("Relative_Value","OT_minus_RV"),
                 ("Stress_Recovery","OT_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(tier+"/"+order+":CAGR")
            if full["turnover"]>1000000:failures.append(tier+"/"+order+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(tier+"/"+order+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(tier+"/"+order+":annual")
            for s,b in (("Opportunity","OT_minus_opportunity"),("Relative_Value","OT_minus_RV"),
                        ("Stress_Recovery","OT_minus_stress")):
                if marginals[tier+"/"+order][s]<=.02:failures.append(tier+"/"+order+":"+s+":marginal")
                for y in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][y])-math.log1p(group[b]["year_returns"][y])
                    if diff<-.03:failures.append(tier+"/"+order+":"+s+":"+y+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:
        failures.append("independent_accounting")
    out={"architecture":"OT","preregistration":"ot_breadth_dispersion_prereg_20261031.md",
         "source":gate,"weekly_decisions":len(decision),"cells":cells,"marginals":marginals,
         "audit":audit,"gate_failures":failures,
         "decision":"REJECT_OT_TRAINING" if failures else "PASS_PROVISIONAL_OT_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "independent_source_and_fill_oracles_pending":True,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OT_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

def synthetic_test():
    # Deterministic causality on a complete synthetic calendar: changing future prices
    # cannot change signals for any earlier weekly decision.
    t=np.arange(HOURS)[:,None];j=np.arange(4)[None,:]
    c=100*np.exp(.0001*t*(1+j/10)+.08*np.sin(t/55+j))
    q=np.ones_like(c)*1e6
    a={"c":c,"q":q}
    x=signals(a)
    b={"c":c.copy(),"q":q.copy()}
    b["c"][15000:]*=1.8;b["q"][15000:]*=3
    y=signals(b)
    if any(not np.array_equal(x[k][0],y[k][0]) or x[k][1]!=y[k][1]
           for k in x if k<15000):raise ValueError("OT_FUTURE_LEAK")
    for book,targets in target_books(x).items():
        if len(targets)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in targets.values()):
            raise ValueError("OT_SYNTHETIC_ALLOC_"+book)
    return True

if __name__=="__main__":
    assert synthetic_test()
    print("OT_SYNTHETIC_CAUSALITY_PASS_NOT_PNL")
