#!/usr/bin/env python3
"""V98 PT seven-slot residual/liquidity exposed training. Never a validated engine."""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PT_full":(0,1,2,3),"PT_core_only":(0,),
       "PT_minus_opportunity":(0,2,3),"PT_minus_RV":(0,1,3),
       "PT_minus_stress":(0,1,2)}
PRIORITY={"contraction":(3,2,1),"expansion":(1,2,3),"dispersion":(2,1,3)}

def signals(d):
    c=np.asarray(d["c"],float);q=np.asarray(d["q"],float)
    if c.shape!=(HOURS,4) or q.shape!=(HOURS,4) or not np.isfinite(c).all() or not np.isfinite(q).all() or np.any(c<=0) or np.any(q<0):
        raise ValueError("PT_SOURCE_GEOMETRY")
    p=np.log(c);out={}
    for t in CLOCK:
        hourly=np.diff(p[t-672:t+1],axis=0)
        centered=hourly-hourly.mean(axis=0)
        v0=float(np.mean(centered[:,0]**2))
        beta=np.zeros(4,float);beta[0]=1.
        for j in (1,2,3):
            beta[j]=np.clip(float(np.mean(centered[:,j]*centered[:,0]))/max(v0,1e-10),0.,2.)
        r={h:p[t]-p[t-h] for h in (24,72,168,672)}
        e={h:r[h]-beta*r[h][0] for h in r}
        ratio=np.sum(q[t-71:t+1],axis=0)/np.maximum(np.sum(q[t-143:t-71],axis=0),1.)
        raw=np.zeros((4,4),float)
        if r[672][0]>0:
            raw[0,0]=.30
            j=min((1,2,3),key=lambda k:(-e[168][k],k))
            if e[168][j]>0:raw[0,j]=.26
        elif r[672][0]<0:
            raw[0,0]=-.26
            j=min((1,2,3),key=lambda k:(e[168][k],k))
            if e[168][j]<0:raw[0,j]=-.24
        eligible=[j for j in (1,2,3) if ratio[j]>=1.35 and abs(e[72][j])>=.05]
        if eligible:
            j=min(eligible,key=lambda k:(-abs(e[72][k])*ratio[k],k))
            raw[1,j]=.16 if e[72][j]>0 else -.16
        hi=min((1,2,3),key=lambda k:(-e[168][k],k))
        lo=min((1,2,3),key=lambda k:(e[168][k],k))
        if hi!=lo and e[168][hi]-e[168][lo]>=.14 and e[24][hi]-e[24][lo]<0:
            raw[2,lo]=.11;raw[2,hi]=-.11
        if r[24][0]<-.06 and int(np.sum(r[24]<0))>=3 and float(np.median(ratio))>=1.15:
            raw[3,0]=-.15
        elif r[168][0]<-.10 and r[24][0]>.035 and float(np.median(ratio))>=1.15:
            raw[3,0]=.15
        mode=("contraction" if r[672][0]<0 else
              "expansion" if r[672][0]>0 and float(np.median(ratio))>=1. else "dispersion")
        out[t]=(raw,mode)
    if len(out)!=157:raise ValueError("PT_DECISION_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PT_ALLOC_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.28,max(0.,.84-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.28+1e-10:
        raise ValueError("PT_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,slots) for t,(raw,mode) in decisions.items()}
            for name,slots in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.000025*t*(1+j/7)+.08*np.sin(t/41+j)+.015*np.cos(t/13+j))
    q=np.broadcast_to(1e6*(1+.3*np.sin(t/17+j)),(HOURS,4)).copy()
    a=signals({"c":c,"q":q})
    b=c.copy();b[15000:]*=np.array([1.7,.8,1.3,.6])
    v=q.copy();v[15000:]*=3.
    mutated=signals({"c":b,"q":v})
    for k in CLOCK:
        if k>=15000:continue
        if a[k][1]!=mutated[k][1] or not np.array_equal(a[k][0],mutated[k][0]):
            raise ValueError("PT_FUTURE_LEAK")
    books=target_books(a)
    if any(len(v)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in v.values()) for v in books.values()):
        raise ValueError("PT_SYNTHETIC_GROSS")
    return {"decision":"PASS_PT_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "books":5,"future_mutation_safe":True,"pnl_computed":False}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pt_residual_liquidity_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["mismatches"]:raise ValueError("PT_INDEPENDENT_DECISION_ORACLE")
    print("PT_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PT_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PT_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PT_minus_opportunity"),("Relative_Value","PT_minus_RV"),
           ("Stress_Recovery","PT_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PT_full"]
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
    if accounting is None or accounting["cash_identity_mismatches"]:failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills_and_funding")
    out={"architecture":"PT","preregistration":"pt_residual_liquidity_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "independent_decision_oracle":oracle,"independent_accounting":accounting,
         "independent_fills":fills,"gate_failures":failures,
         "decision":"REJECT_PT_TRAINING" if failures else "PASS_PROVISIONAL_PT_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PT_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
