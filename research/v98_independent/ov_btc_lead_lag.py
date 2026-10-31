#!/usr/bin/env python3
"""V98 OV BTC-led propagation complete seven-slot exploratory 2022-25 TRAINING.
Binding prereg ov_btc_lead_lag_prereg_20261031.md; no future/benchmarks/paper.
Uses only V98 OT mechanical physical settlement, never OT strategy signals.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BOOKS={"OV_full":(0,1,2,3),"OV_core_only":(0,),
       "OV_minus_opportunity":(0,2,3),"OV_minus_RV":(0,1,3),
       "OV_minus_stress":(0,1,2)}
PRIORITY={"panic":(3,1,2),"propagation":(1,2,3),"transition":(2,3,1)}
MULT={"panic":(.5,.5,1.),"propagation":(1.,.75,.5),"transition":(.75,1.,.75)}

def signals(d):
    close=np.asarray(d["c"],float)
    if close.shape!=(HOURS,4) or np.any(close<=0) or not np.isfinite(close).all():
        raise ValueError("OV_CLOSE_SOURCE")
    p=np.log(close)
    out={}
    for t in range(WARMUP,HOURS,STEP):
        r504=p[t]-p[t-504];r336=p[t]-p[t-336]
        r168=p[t]-p[t-168];r72=p[t]-p[t-72]
        r24=p[t]-p[t-24];r12=p[t]-p[t-12]
        leader_up=r504[0]>0 and r168[0]>0
        leader_down=r504[0]<0 and r168[0]<0
        state="panic" if r72[0]<-.10 else ("propagation" if leader_up or leader_down else "transition")
        raw=np.zeros((4,4),float)
        if leader_up:
            rank=sorted((j for j in range(4) if r168[j]>0),key=lambda j:(-r504[j],j))
            for j,w in zip(rank[:2],(.40,.22)):raw[0,j]=w
        elif leader_down:
            rank=sorted((j for j in range(4) if r168[j]<0),key=lambda j:(r504[j],j))
            for j,w in zip(rank[:2],(-.35,-.20)):raw[0,j]=w
        if r24[0]>.025 and r72[0]>.045:
            lag=[j for j in (1,2,3) if r72[0]-r72[j]>=.04 and r24[j]>0]
            if lag:
                j=min(lag,key=lambda k:(r72[k],k));raw[1,j]=.16
        elif r24[0]<-.025 and r72[0]<-.045:
            lag=[j for j in (1,2,3) if r72[j]-r72[0]>=.04 and r24[j]<0]
            if lag:
                j=min(lag,key=lambda k:(-r72[k],k));raw[1,j]=-.16
        hi=min((1,2,3),key=lambda k:(-r336[k],k))
        lo=min((1,2,3),key=lambda k:(r336[k],k))
        if r336[hi]-r336[lo]>.14:
            if r336[0]>0:raw[2,hi]=.10;raw[2,lo]=-.10
            elif r336[0]<0:raw[2,hi]=-.10;raw[2,lo]=.10
        if r72[0]<-.10 and r12[0]>.025 and int(np.sum(r12[1:]>0))>=2:
            raw[3,0]=.16
        elif r72[0]<-.10 and r12[0]<-.025 and int(np.sum(r12[1:]<0))>=2:
            raw[3,0]=-.16
        raw[1:]*=np.asarray(MULT[state])[:,None]
        out[t]=(raw,state)
    if len(out)!=157:raise ValueError("OV_WEEKLY_CLOCK")
    return out

def allocate(raw,state,active):
    if raw.shape!=(4,4) or state not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OV_ALLOCATION_INPUT")
    w=np.zeros((4,4))
    if 0 in active:w[0]=raw[0]
    room=min(.24,max(0.,.84-float(np.abs(w).sum())))
    for slot in PRIORITY[state]:
        if slot not in active:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross>0 and room>0:
            use=min(room,gross)
            w[slot]=raw[slot]*(use/gross)
            room-=use
    if np.abs(w).sum()>.84+1e-10 or np.abs(w[1:]).sum()>.24+1e-10:
        raise ValueError("OV_GROSS_BREACH")
    return w

def target_books(decisions):
    return {book:{t:allocate(raw,state,active) for t,(raw,state) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    time=np.arange(HOURS)[:,None];idx=np.arange(4)[None,:]
    close=100*np.exp(.00005*time*(1+idx/10)+.06*np.sin(time/57+idx))
    a={"c":close}
    x=signals(a)
    b={"c":close.copy()}
    b["c"][15000:]*=1.7
    y=signals(b)
    for t in x:
        if t<15000 and (x[t][1]!=y[t][1] or not np.array_equal(x[t][0],y[t][0])):
            raise ValueError("OV_CAUSAL_FUTURE_LEAK")
    for book,targets in target_books(x).items():
        if len(targets)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in targets.values()):
            raise ValueError("OV_SYNTHETIC_ALLOC_"+book)
    return {"decision":"PASS_OV_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":len(x)}

def run(d):
    source=source_gate(d)
    decisions=signals(d)
    books=target_books(decisions)
    from ov_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("OV_INDEPENDENT_DECISION_MISMATCH")
    print("OV_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="OV_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OV_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),"FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            g={row["book"]:row for row in cells if row["tier"]==tier and row["order"]==order}
            if not all(row["passed"] for row in g.values()):
                failures.append(tier+"/"+order+":physical")
                continue
            full=g["OV_full"]
            key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-g[book]["log_growth"]
                 for slot,book in (("Opportunity","OV_minus_opportunity"),
                                   ("Relative_Value","OV_minus_RV"),
                                   ("Stress_Recovery","OV_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","OV_minus_opportunity"),
                              ("Relative_Value","OV_minus_RV"),
                              ("Stress_Recovery","OV_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(g[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"OV","preregistration":"ov_btc_lead_lag_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_OV_TRAINING" if failures else "PASS_PROVISIONAL_OV_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OV_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
