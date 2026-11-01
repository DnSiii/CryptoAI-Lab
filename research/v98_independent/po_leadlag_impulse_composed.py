#!/usr/bin/env python3
"""PO pre-registered BTC-to-alt lagged impulse seven-slot physical exposed training."""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PO_full":(0,1,2,3),"PO_core_only":(0,),
       "PO_minus_opportunity":(0,2,3),"PO_minus_RV":(0,1,3),
       "PO_minus_stress":(0,1,2)}
PRIORITY={"impulse":(3,1,2),"diffusion":(1,2,3),"quiet":(2,1,3)}

def signals(d):
    c=np.asarray(d["c"],dtype=float)
    if c.shape!=(HOURS,4) or not np.isfinite(c).all() or np.any(c<=0):
        raise ValueError("PO_PRICE_SOURCE_GEOMETRY")
    p=np.log(c)
    out={}
    for t in CLOCK:
        r24=p[t]-p[t-24]
        r168=p[t]-p[t-168]
        r336=p[t]-p[t-336]
        hour=np.diff(p[t-168:t+1],axis=0)
        vol=np.maximum(np.std(hour,axis=0)*math.sqrt(168),.04)
        lag=np.diff(p[t-337:t+1],axis=0)
        btc_lag=lag[:-1,0]
        bx=btc_lag-btc_lag.mean()
        bvar=float(np.mean(bx*bx))
        corr=np.zeros(4);beta=np.zeros(4);residual=np.zeros(4)
        for j in (1,2,3):
            y=lag[1:,j]
            yc=y-y.mean()
            cov=float(np.mean(bx*yc))
            vy=float(np.mean(yc*yc))
            corr[j]=cov/math.sqrt(max(bvar,1e-16)*max(vy,1e-16))
            beta[j]=min(2.,max(0.,cov/max(bvar,1e-16)))
            residual[j]=beta[j]*r24[0]-r24[j]
        raw=np.zeros((4,4),float)
        if float(np.median(r168))>=0:
            core=sorted((j for j in range(4) if r336[j]>0),
                        key=lambda j:(-r336[j]/vol[j],j))
            for j,w in zip(core[:2],(.34,.18)):raw[0,j]=w
        else:
            core=sorted((j for j in range(4) if r336[j]<0),
                        key=lambda j:(r336[j]/vol[j],j))
            for j,w in zip(core[:2],(-.30,-.16)):raw[0,j]=w
        linked=[j for j in (1,2,3) if corr[j]>=.10]
        opportunities=[j for j in linked if abs(residual[j])>=.025
                       and residual[j]*r24[0]>0]
        chosen=None
        if opportunities:
            chosen=min(opportunities,key=lambda j:(-abs(residual[j]),j))
            raw[1,chosen]=math.copysign(.18,residual[chosen])
        if len(linked)>=2:
            high=min(linked,key=lambda j:(-residual[j],j))
            low=min(linked,key=lambda j:(residual[j],j))
            if high!=low and residual[high]-residual[low]>=.05 and residual[low]<0<residual[high]:
                raw[2,low]=.11;raw[2,high]=-.11
        shock=abs(float(r24[0]))/max(float(vol[0])/math.sqrt(7),.02)
        if shock>=1.75 and len(linked)>=2:
            lagger=min(linked,key=lambda j:(-abs(residual[j]),j))
            if lagger==chosen:
                if r24[0]!=0:raw[3,0]=-math.copysign(.12,r24[0])
            elif residual[lagger]!=0:
                raw[3,lagger]=math.copysign(.15,residual[lagger])
        mode="impulse" if shock>=1.75 else ("diffusion" if len(linked)>=2 else "quiet")
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PO_DECISION_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PO_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    if float(np.abs(held[0]).sum())>.52+1e-10:raise ValueError("PO_CORE_GROSS")
    room=min(.32,max(0.,.84-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.32+1e-10:
        raise ValueError("PO_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,slots) for t,(raw,mode) in decisions.items()}
            for name,slots in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.000025*t*(1+j/7)+.08*np.sin(t/41+j)+.015*np.cos(t/13+j))
    d={"c":c}
    original=signals(d)
    future=c.copy();future[15000:]*=np.array([1.7,.8,1.3,.6])
    mutated=signals({"c":future})
    for k in CLOCK:
        if k>=15000:continue
        a,b=original[k],mutated[k]
        if a[1]!=b[1] or not np.array_equal(a[0],b[0]):
            raise ValueError("PO_FUTURE_LEAK")
    books=target_books(original)
    if any(len(v)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in v.values())
           for v in books.values()):raise ValueError("PO_SYNTHETIC_GROSS")
    # Source-only perturbation must not change decisions: funding never used as signal.
    return {"decision":"PASS_PO_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "books":5,"future_mutation_safe":True,"pnl_computed":False}

def run(d):
    source=source_gate(d)
    decisions=signals(d)
    books=target_books(decisions)
    from po_leadlag_impulse_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["mismatches"]:raise ValueError("PO_INDEPENDENT_DECISION_ORACLE")
    print("PO_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PO_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PO_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PO_minus_opportunity"),("Relative_Value","PO_minus_RV"),
           ("Stress_Recovery","PO_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PO_full"]
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
    out={"architecture":"PO","preregistration":"po_leadlag_impulse_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PO_TRAINING" if failures else "PASS_PROVISIONAL_PO_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PO_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
