#!/usr/bin/env python3
"""PQ preregistered asymmetric semivariance seven-slot exposed training; not validated."""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PQ_full":(0,1,2,3),"PQ_core_only":(0,),
       "PQ_minus_opportunity":(0,2,3),"PQ_minus_RV":(0,1,3),
       "PQ_minus_stress":(0,1,2)}
PRIORITY={"panic":(3,2,1),"expansion":(1,2,3),"normal":(2,1,3)}

def signals(d):
    c=np.asarray(d["c"],dtype=float)
    q=np.asarray(d["q"],dtype=float)
    if (c.shape!=(HOURS,4) or q.shape!=(HOURS,4) or
        not np.isfinite(c).all() or not np.isfinite(q).all() or
        np.any(c<=0) or np.any(q<0)):
        raise ValueError("PQ_PRICE_VOLUME_SOURCE_GEOMETRY")
    p=np.log(c)
    out={}
    for t in CLOCK:
        hourly=np.diff(p[t-504:t+1],axis=0)
        downside=np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0))
        upside=np.sqrt(np.mean(np.maximum(hourly,0.)**2,axis=0))
        asym=(downside+.0001)/(upside+.0001)
        vol=np.maximum(np.std(hourly,axis=0)*math.sqrt(504),.04)
        r24=p[t]-p[t-24];r72=p[t]-p[t-72]
        r168=p[t]-p[t-168];r504=p[t]-p[t-504]
        v=np.minimum(4.,np.sum(q[t-71:t+1],axis=0)/
                     np.maximum(np.sum(q[t-143:t-71],axis=0),1.))
        raw=np.zeros((4,4),float)
        if float(np.median(r168))>=0:
            eligible=sorted((j for j in range(4) if r504[j]>0 and asym[j]<1.25),
                            key=lambda j:(-r504[j]/vol[j],j))
            for j,w in zip(eligible[:2],(.42,.24)):raw[0,j]=w
        else:
            eligible=sorted((j for j in range(4) if r504[j]<0 and asym[j]>1.15),
                            key=lambda j:(r504[j]/vol[j],j))
            for j,w in zip(eligible[:2],(-.38,-.22)):raw[0,j]=w
        up=sorted((j for j in range(4) if r72[j]>.06 and v[j]>1.5 and asym[j]<.95),
                  key=lambda j:(-v[j],j))
        down=sorted((j for j in range(4) if r72[j]<-.08 and v[j]>1.5 and asym[j]>1.30),
                    key=lambda j:(-v[j],j))
        if up:raw[1,up[0]]=.18
        elif down:raw[1,down[0]]=-.16
        high=min((1,2,3),key=lambda j:(-asym[j],j))
        low=min((1,2,3),key=lambda j:(asym[j],j))
        if high!=low and asym[high]-asym[low]>.40 and abs(r168[high]-r168[low])<.10:
            raw[2,high]=-.12;raw[2,low]=.12
        if r72[0]<-.12 and float(np.median(asym))>1.25:
            recover=sorted((j for j in range(4) if r24[j]>0 and v[j]>1.2),
                           key=lambda j:(-r24[j],j))
            if recover:raw[3,recover[0]]=.16
            elif r24[0]<-.05:raw[3,0]=-.16
        mode=("panic" if float(np.median(asym))>1.35 else
              "expansion" if float(np.median(v))>1.20 else "normal")
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PQ_DECISION_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PQ_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    if float(np.abs(held[0]).sum())>.66+1e-10:raise ValueError("PQ_CORE_GROSS")
    room=min(.24,max(0.,.82-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if float(np.abs(held).sum())>.82+1e-10 or float(np.abs(held[1:]).sum())>.24+1e-10:
        raise ValueError("PQ_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,slots) for t,(raw,mode) in decisions.items()}
            for name,slots in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.000025*t*(1+j/7)+.08*np.sin(t/41+j)+.015*np.cos(t/13+j))
    q=np.broadcast_to(1e6*(1+.3*np.sin(t/17+j)),(HOURS,4)).copy()
    original=signals({"c":c,"q":q})
    future=c.copy();future[15000:]*=np.array([1.7,.8,1.3,.6])
    qfuture=q.copy();qfuture[15000:]*=3
    mutated=signals({"c":future,"q":qfuture})
    for k in CLOCK:
        if k>=15000:continue
        a,b=original[k],mutated[k]
        if a[1]!=b[1] or not np.array_equal(a[0],b[0]):
            raise ValueError("PQ_FUTURE_LEAK")
    books=target_books(original)
    if any(len(v)!=157 or any(np.abs(w).sum()>.82+1e-10 for w in v.values())
           for v in books.values()):raise ValueError("PQ_SYNTHETIC_GROSS")
    return {"decision":"PASS_PQ_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "books":5,"future_mutation_safe":True,"pnl_computed":False}

def run(d):
    source=source_gate(d)
    decisions=signals(d)
    books=target_books(decisions)
    from pq_asymmetric_downside_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["mismatches"]:raise ValueError("PQ_INDEPENDENT_DECISION_ORACLE")
    print("PQ_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PQ_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PQ_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PQ_minus_opportunity"),("Relative_Value","PQ_minus_RV"),
           ("Stress_Recovery","PQ_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PQ_full"]
            marginals[label]={slot:full["log_growth"]-group[book]["log_growth"]
                              for slot,book in slots}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":CAGR")
            if full["turnover"]>1000000:failures.append(label+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(label+":drawdown")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(label+":annual")
            for slot,book in slots:
                if marginals[label][slot]<=.02:failures.append(label+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(label+":"+slot+":"+year+":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:
        failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills_and_funding")
    out={"architecture":"PQ","preregistration":"pq_asymmetric_downside_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PQ_TRAINING" if failures else "PASS_PROVISIONAL_PQ_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PQ_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
