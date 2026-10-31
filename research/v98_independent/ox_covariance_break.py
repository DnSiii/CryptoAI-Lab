#!/usr/bin/env python3
"""V98 OX: preregistered covariance-break seven-slot complete physical engine.
Exploratory exposed 2022-25 Clean-4 training ONLY. No benchmarks, 2026+, XRP or paper.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BOOKS={"OX_full":(0,1,2,3),"OX_core_only":(0,),
       "OX_minus_opportunity":(0,2,3),"OX_minus_RV":(0,1,3),
       "OX_minus_stress":(0,1,2)}
PRIORITY={"coherent_up":(1,2,3),"coherent_down":(3,2,1),"fractured":(2,3,1)}
MULT={"coherent_up":(1.,.75,.5),"coherent_down":(.75,1.,1.),
      "fractured":(.75,1.,.75)}

def corr_btc(matrix):
    b=matrix[:,0]; b=b-float(b.mean()); norm_b=float(np.dot(b,b))
    result=[]
    for j in (1,2,3):
        a=matrix[:,j];a=a-float(a.mean())
        denom=math.sqrt(max(norm_b*float(np.dot(a,a)),0.))
        result.append(float(np.dot(b,a)/denom) if denom>1e-18 else 0.)
    return np.array(result)

def signals(d):
    close=np.asarray(d["c"],float)
    if close.shape!=(HOURS,4) or not np.isfinite(close).all() or np.any(close<=0):
        raise ValueError("OX_SOURCE_CLOSE")
    p=np.log(close);out={}
    for t in range(WARMUP,HOURS,STEP):
        r336=p[t]-p[t-336];r72=p[t]-p[t-72]
        hr=np.diff(p[t-168:t+1],axis=0)
        corr168=float(np.median(corr_btc(hr)))
        corr72=float(np.median(corr_btc(hr[-72:])))
        up=int(np.sum(r336>0));down=int(np.sum(r336<0))
        mode=("coherent_up" if corr168>=.65 and up>=3 else
              "coherent_down" if corr168>=.65 and down>=3 else "fractured")
        raw=np.zeros((4,4),float)
        if mode=="coherent_up":
            candidates=sorted([j for j in range(4) if r336[j]>0],
                              key=lambda j:(-r336[j],j))
            for j,w in zip(candidates[:2],(.38,.24)):raw[0,j]=w
        elif mode=="coherent_down":
            candidates=sorted([j for j in range(4) if r336[j]<0],
                              key=lambda j:(r336[j],j))
            for j,w in zip(candidates[:2],(-.32,-.20)):raw[0,j]=w
        else:
            hi=min(range(4),key=lambda j:(-r336[j],j))
            lo=min(range(4),key=lambda j:(r336[j],j))
            if r336[hi]>0 and r72[hi]>0:raw[0,hi]=.28
            elif r336[lo]<0 and r72[lo]<0:raw[0,lo]=-.24
        if corr72-corr168>.20:
            if int(np.sum(r72>0))>=3 and r72[0]>0:
                j=min((1,2,3),key=lambda j:(-r72[j],j))
                raw[1,j]=.14
            elif int(np.sum(r72<0))>=3 and r72[0]<0:
                j=min((1,2,3),key=lambda j:(r72[j],j))
                raw[1,j]=-.14
        btc=hr[:,0];xb=btc-float(btc.mean());den=max(float(np.dot(xb,xb)),1e-15)
        scores=[]
        for j in (1,2,3):
            alt=hr[:,j];xa=alt-float(alt.mean())
            beta=float(np.clip(float(np.dot(xa,xb))/den,.2,2.5))
            residual=alt-beta*btc
            std=float(np.std(residual))
            scores.append(float(np.sum(residual[-72:])/(max(std,1e-12)*math.sqrt(72))))
        hi=min(range(3),key=lambda j:(-scores[j],j))
        lo=min(range(3),key=lambda j:(scores[j],j))
        if hi!=lo and scores[hi]>1.5 and scores[lo]<-1.5:
            raw[2,hi+1]=-.10;raw[2,lo+1]=.10
        if corr72<.20 and r72[0]<-.05:
            raw[3,0]=-.16
        elif corr72>.65 and corr168<.35 and r72[0]>.04:
            raw[3,0]=.16
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("OX_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("OX_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.26,max(0.,.84-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active:continue
        wanted=float(np.abs(raw[slot]).sum())
        if wanted>0 and room>0:
            used=min(wanted,room)
            held[slot]=raw[slot]*(used/wanted)
            room-=used
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.26+1e-10:
        raise ValueError("OX_GROSS_BREACH")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    tt=np.arange(HOURS)[:,None];jj=np.arange(4)[None,:]
    close=100*np.exp(.000035*tt*(1+jj/10)+.06*np.sin(tt/67+jj)+.015*np.cos(tt/19+jj*2))
    a=signals({"c":close})
    future=close.copy();future[15000:]*=np.array([1.4,.7,1.2,.9])
    b=signals({"c":future})
    for t in a:
        if t<15000 and (a[t][1]!=b[t][1] or not np.allclose(a[t][0],b[t][0],atol=1e-12,rtol=0)):
            raise ValueError("OX_FUTURE_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(book)!=157 for book in books.values()):
        raise ValueError("OX_SYNTHETIC_BOOK_CLOCK")
    return {"decision":"PASS_OX_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from ox_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("OX_INDEPENDENT_DECISION_MISMATCH")
    print("OX_INDEPENDENT_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=(tier=="base" and order=="carried_before_fill" and book=="OX_full")
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("OX_CELL",tier,order,book,"PHYSICAL",row["passed"],
                      "CAGR",round(100*row.get("cagr",-1),3),"FAIL",row.get("failure",""),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill_oracle=independent_fills(d,ledger) if audit is not None else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            if not all(x["passed"] for x in group.values()):
                failures.append(tier+"/"+order+":physical");continue
            full=group["OX_full"];key=tier+"/"+order
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"]
                for slot,book in (("Opportunity","OX_minus_opportunity"),
                                  ("Relative_Value","OX_minus_RV"),
                                  ("Stress_Recovery","OX_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","OX_minus_opportunity"),
                              ("Relative_Value","OX_minus_RV"),
                              ("Stress_Recovery","OX_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    diff=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill_oracle is None or fill_oracle["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    out={"architecture":"OX","preregistration":"ox_covariance_break_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"audit":audit,"independent_decision_oracle":oracle,
         "independent_fill_oracle":fill_oracle,"gate_failures":failures,
         "decision":"REJECT_OX_TRAINING" if failures else "PASS_PROVISIONAL_OX_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("OX_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
