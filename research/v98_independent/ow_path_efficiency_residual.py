#!/usr/bin/env python3
"""V98 OW pre-registered 2022-25 EXPOSED TRAINING seven-slot physical composition.
Uses OT source-independent physical execution mechanics, NEVER OT trading signals.
No benchmarks, 2026+, XRP, contaminated holdout, Frozen or paper/live.
"""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BOOKS={"OW_full":(0,1,2,3),"OW_core_only":(0,),
       "OW_minus_opportunity":(0,2,3),"OW_minus_RV":(0,1,3),
       "OW_minus_stress":(0,1,2)}
PRIORITY={"positive":(1,2,3),"negative":(3,2,1),"mixed":(2,1,3)}
MULT={"positive":(1.,.75,.5),"negative":(.5,1.,1.),"mixed":(.75,1.,.75)}

def signals(d):
    close=np.asarray(d["c"],float)
    if close.shape!=(HOURS,4) or not np.isfinite(close).all() or np.any(close<=0):
        raise ValueError("OW_SOURCE_CLOSE")
    p=np.log(close);out={}
    for t in range(WARMUP,HOURS,STEP):
        r504=p[t]-p[t-504];r168=p[t]-p[t-168]
        r72=p[t]-p[t-72];r24=p[t]-p[t-24];r12=p[t]-p[t-12]
        hr=np.diff(p[t-504:t+1],axis=0)
        path=np.sum(np.abs(hr),axis=0)
        eff=np.abs(r504)/np.maximum(path,1e-12)
        up=int(np.sum(r504>0));down=int(np.sum(r504<0))
        mode="positive" if up>=3 else ("negative" if down>=3 else "mixed")
        raw=np.zeros((4,4),float)
        if mode=="positive":
            eligible=[j for j in range(4) if r504[j]>0 and r168[j]>0]
            for j,w in zip(sorted(eligible,key=lambda k:(-eff[k],k))[:2],(.42,.22)):
                raw[0,j]=w
        elif mode=="negative":
            eligible=[j for j in range(4) if r504[j]<0 and r168[j]<0]
            for j,w in zip(sorted(eligible,key=lambda k:(-eff[k],k))[:2],(-.38,-.20)):
                raw[0,j]=w
        elif r504[0]>0 and r168[0]>0:raw[0,0]=.28
        elif r504[0]<0 and r168[0]<0:raw[0,0]=-.28
        rebound=[j for j in range(4) if r24[j]<-.065 and r12[j]>.022]
        exhaustion=[j for j in range(4) if r24[j]>.065 and r12[j]<-.022]
        if rebound:
            j=min(rebound,key=lambda k:(-r12[k],k));raw[1,j]=.16
        elif exhaustion:
            j=min(exhaustion,key=lambda k:(r12[k],k));raw[1,j]=-.16
        btc=hr[:,0];xb=btc-btc.mean()
        variance=float(np.dot(xb,xb))
        beta=np.zeros(3)
        for j in (1,2,3):
            xj=hr[:,j]-float(hr[:,j].mean())
            beta[j-1]=float(np.clip(np.dot(xb,xj)/max(variance,1e-15),.2,2.5))
        residual=r168[1:]-beta*r168[0]
        hi=min(range(3),key=lambda k:(-residual[k],k))
        lo=min(range(3),key=lambda k:(residual[k],k))
        if residual[hi]-residual[lo]>.10:
            raw[2,hi+1]=.11;raw[2,lo+1]=-.11
        if int(np.sum(r72<-.09))>=3 and int(np.sum(r24<-.035))>=3:
            raw[3,0]=-.16
        elif int(np.sum(r72<-.09))>=3 and int(np.sum(r24>.020))>=3:
            raw[3,0]=.16
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("OW_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OW_ALLOC_INPUT")
    w=np.zeros((4,4))
    if 0 in active:w[0]=raw[0]
    room=min(.26,max(0.,.84-float(np.abs(w).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross>0 and room>0:
            use=min(gross,room)
            w[slot]=raw[slot]*(use/gross)
            room-=use
    if np.abs(w).sum()>.84+1e-10 or np.abs(w[1:]).sum()>.26+1e-10:
        raise ValueError("OW_GROSS_BREACH")
    return w

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    tt=np.arange(HOURS)[:,None];jj=np.arange(4)[None,:]
    close=100*np.exp(.00005*tt*(1+jj/10)+.06*np.sin(tt/57+jj))
    d={"c":close}
    x=signals(d)
    altered={"c":close.copy()}
    altered["c"][15000:]*=1.7
    y=signals(altered)
    for t in x:
        if t<15000 and (x[t][1]!=y[t][1] or not np.allclose(x[t][0],y[t][0],rtol=0,atol=1e-12)):
            raise ValueError("OW_CAUSAL_FUTURE_LEAK")
    for book,targets in target_books(x).items():
        if len(targets)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in targets.values()):
            raise ValueError("OW_SYNTHETIC_ALLOC_"+book)
    return {"decision":"PASS_OW_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":len(x)}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from ow_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("OW_INDEPENDENT_DECISION_MISMATCH")
    print("OW_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="OW_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OW_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),"FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            g={row["book"]:row for row in cells if row["tier"]==tier and row["order"]==order}
            if not all(row["passed"] for row in g.values()):
                failures.append(tier+"/"+order+":physical");continue
            full=g["OW_full"];key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-g[book]["log_growth"]
                for slot,book in (("Opportunity","OW_minus_opportunity"),
                                  ("Relative_Value","OW_minus_RV"),
                                  ("Stress_Recovery","OW_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<= (.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","OW_minus_opportunity"),
                              ("Relative_Value","OW_minus_RV"),
                              ("Stress_Recovery","OW_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(g[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"OW","preregistration":"ow_path_efficiency_residual_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_OW_TRAINING" if failures else "PASS_PROVISIONAL_OW_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OW_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
