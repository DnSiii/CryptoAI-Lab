#!/usr/bin/env python3
"""V98 PE: preregistered candle-location liquidity-pressure seven-slot portfolio.
Clean-4 exposed training only; never exact event-mark PnL or live authorization.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PE_full":(0,1,2,3),"PE_core_only":(0,),
       "PE_minus_opportunity":(0,2,3),"PE_minus_RV":(0,1,3),
       "PE_minus_stress":(0,1,2)}
PRIORITY={"stress":(3,1,2),"normal":(1,2,3)}
MULT={"stress":(.5,.5,1.),"normal":(1.,1.,.5)}

def pressure(hloc, q, a, b):
    """Candle location weighted by observed quote volume, indices [a,b)."""
    v=np.asarray(q[a:b],float)
    s=np.asarray(hloc[a:b],float)
    den=np.sum(v,axis=0)
    return np.divide(np.sum(v*s,axis=0),den,out=np.zeros(4),where=den>0)

def signals(d):
    o=np.asarray(d["o"],float);h=np.asarray(d["h"],float)
    l=np.asarray(d["l"],float);c=np.asarray(d["c"],float)
    q=np.asarray(d["q"],float)
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q)):
        raise ValueError("PE_SOURCE_SHAPE")
    if not all(np.isfinite(x).all() for x in (o,h,l,c,q)):
        raise ValueError("PE_SOURCE_NONFINITE")
    if np.any(c<=0) or np.any(l<=0) or np.any(q<0) or np.any(h<l):
        raise ValueError("PE_SOURCE_GEOMETRY")
    spread=h-l
    location=np.divide(2*c-h-l,spread,out=np.zeros_like(c),where=spread>0)
    location=np.clip(location,-1.,1.)
    range_pct=np.divide(spread,c,out=np.zeros_like(c),where=c>0)
    out={}
    for t in CLOCK:
        p168=pressure(location,q,t-167,t+1)
        p24=pressure(location,q,t-23,t+1)
        p72=pressure(location,q,t-71,t+1)
        prior_q=np.mean(q[t-167:t-23],axis=0)
        recent_q=np.mean(q[t-23:t+1],axis=0)
        volratio=np.divide(recent_q,prior_q,out=np.zeros(4),where=prior_q>0)
        volratio=np.clip(volratio,0.,3.)
        recent_range=float(np.mean(range_pct[t-23:t+1]))
        prior_range=float(np.mean(range_pct[t-167:t-23]))
        stressed=recent_range>1.5*prior_range if prior_range>0 else False
        mode="stress" if stressed else "normal"
        raw=np.zeros((4,4),float)
        rank_hi=sorted(range(4),key=lambda j:(-p168[j],j))
        rank_lo=sorted(range(4),key=lambda j:(p168[j],j))
        if p168[rank_hi[1]]>.08:
            raw[0,rank_hi[0]]=.32
            raw[0,rank_hi[1]]=.20
        elif p168[rank_lo[1]]<-.08:
            raw[0,rank_lo[0]]=-.32
            raw[0,rank_lo[1]]=-.20
        absorption=(p24-p168)*volratio
        candidate=min(range(4),key=lambda j:(-abs(absorption[j]),j))
        if abs(absorption[candidate])>.20 and abs(math.log(c[t,candidate]/c[t-24,candidate]))<.06:
            raw[1,candidate]=math.copysign(.16,float(absorption[candidate]))
        high=max((1,2,3),key=lambda j:(p72[j],-j))
        low=min((1,2,3),key=lambda j:(p72[j],j))
        if high!=low and p72[high]-p72[low]>.32:
            raw[2,high]=.12;raw[2,low]=-.12
        pos=[j for j in range(4) if p24[j]>.12]
        neg=[j for j in range(4) if p24[j]<-.12]
        if stressed and (len(pos)>=3 or len(neg)>=3):
            side=1. if len(pos)>=3 else -1.
            eligible=pos if side>0 else neg
            j=min(eligible,key=lambda k:(-abs(p24[k]),k))
            raw[3,j]=side*.16
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PE_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PE_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.30,max(0.,.84-float(np.abs(held).sum())))
    for k in PRIORITY[mode]:
        if k not in active:continue
        want=float(np.abs(raw[k]).sum())
        if want>0 and room>0:
            take=min(room,want)
            held[k]=raw[k]*(take/want)
            room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.30+1e-10:
        raise ValueError("PE_GROSS")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS)[:,None];j=np.arange(4)[None,:]
    c=100*np.exp(.00002*t*(1+j/5)+.06*np.sin(t/61+j))
    h=c*(1.012+.003*np.sin(t/17+j)**2)
    l=c*(.988-.003*np.cos(t/19+j)**2)
    o=c.copy();q=1e6*(1+.3*np.cos(t/29+j)**2)
    d={"o":o,"h":h,"l":l,"c":c,"q":q}
    a=signals(d)
    modified={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c"):
        modified[k][15000:]*=np.array([1.5,.7,1.2,.8])
    modified["q"][15000:]*=3
    b=signals(modified)
    if any(a[t][1]!=b[t][1] or not np.array_equal(a[t][0],b[t][0])
           for t in CLOCK if t<15000):
        raise ValueError("PE_FUTURE_LEAK")
    books=target_books(a)
    if len(books)!=5 or any(len(v)!=157 for v in books.values()):
        raise ValueError("PE_BOOKS")
    return {"decision":"PASS_PE_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157}

def run(d):
    source=source_gate(d)
    decisions=signals(d)
    books=target_books(decisions)
    from pe_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:
        raise ValueError("PE_ORACLE_MISMATCH")
    print("PE_INDEPENDENT_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PE_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PE_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill=independent_fills(d,ledger) if audit else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            key=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(key+":physical");continue
            full=group["PE_full"]
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"]
                for slot,book in (("Opportunity","PE_minus_opportunity"),
                                  ("Relative_Value","PE_minus_RV"),("Stress_Recovery","PE_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","PE_minus_opportunity"),
                              ("Relative_Value","PE_minus_RV"),("Stress_Recovery","PE_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill is None or fill["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills")
    out={"architecture":"PE","preregistration":"pe_liquidity_pressure_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "audit":audit,"independent_decision_oracle":oracle,"independent_fill_oracle":fill,
         "gate_failures":failures,"decision":"REJECT_PE_TRAINING" if failures else "PASS_PROVISIONAL_PE_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PE_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
