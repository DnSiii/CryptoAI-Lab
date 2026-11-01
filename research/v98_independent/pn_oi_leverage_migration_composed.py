#!/usr/bin/env python3
"""PN preregistered OI leverage migration seven-slot V98 exposed training; not live."""
import json,math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PN_full":(0,1,2,3),"PN_core_only":(0,),
       "PN_minus_opportunity":(0,2,3),"PN_minus_RV":(0,1,3),
       "PN_minus_stress":(0,1,2)}
PRIORITY={"expansion":(1,2,3),"defense":(3,2,1),"transition":(2,1,3)}

def signals(d,bridge):
    c=np.asarray(d["c"],float)
    oi=np.asarray(bridge["oi"],float)
    mask=np.asarray(bridge["observed"],bool)
    eligible=bridge["eligible"]
    if c.shape!=(HOURS,4) or oi.shape!=(HOURS,4) or mask.shape!=(HOURS,4):
        raise ValueError("PN_SOURCE_GEOMETRY")
    if not np.isfinite(c).all() or np.any(c<=0) or not np.array_equal(np.isfinite(oi),mask):
        raise ValueError("PN_SOURCE_VALUES")
    if len(eligible)!=len(CLOCK) or sum(bool(v) for v in eligible.values())!=143:
        raise ValueError("PN_OI_SOURCE_ELIGIBILITY")
    logp=np.log(c)
    out={}
    for t in CLOCK:
        r168=logp[t]-logp[t-168]
        r336=logp[t]-logp[t-336]
        r72=logp[t]-logp[t-72]
        v=np.std(np.diff(logp[t-168:t+1],axis=0),axis=0)*math.sqrt(168)
        breadth=int(np.sum(r168>0))
        raw=np.zeros((4,4),float)
        if breadth>=2:
            ranked=sorted((j for j in range(4) if r336[j]>0 and r168[j]>0),
                          key=lambda j:(-r336[j]/max(v[j],.06),j))
            for j,w in zip(ranked[:2],(.40,.22)):raw[0,j]=w
        is_eligible=bool(eligible[t])
        if is_eligible:
            if not mask[t-167:t+1].all():
                raise ValueError("PN_OI_CAUSAL_MASK_FALSE_PASS")
            g=np.log(oi[t]/oi[t-167])
            s=int(np.sum(g>0))
            choices=[j for j in range(4) if g[j]>.035 and r72[j]>0 and r168[j]>0]
            if choices:
                j=min(choices,key=lambda k:(-(r72[k]+.5*g[k]),k))
                raw[1,j]=.16
            divergence=g-r168
            hi=min(range(4),key=lambda j:(-divergence[j],j))
            lo=min(range(4),key=lambda j:(divergence[j],j))
            if (hi!=lo and divergence[hi]-divergence[lo]>.09 and
                r72[hi]>0 and r72[lo]<0):
                raw[2,hi]=.09;raw[2,lo]=-.09
            if s<=1 and breadth<=1 and r168[0]<-.08:
                raw[3,0]=-.14
            elif s<=1 and breadth>=3 and r72[0]>.025:
                raw[3,0]=.14
            mode="expansion" if breadth>=3 and s>=2 else (
                "defense" if breadth<=1 or s<=1 else "transition")
        else:
            if mask[t-167:t+1].all():
                raise ValueError("PN_OI_ELIGIBLE_FALSE_REJECTION")
            g=None
            mode="expansion" if breadth>=3 else ("defense" if breadth<=1 else "transition")
        out[t]=(raw,mode,is_eligible)
    if len(out)!=157 or sum(v[2] for v in out.values())!=143:
        raise ValueError("PN_DECISION_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PN_ALLOCATION_INPUT")
    held=np.zeros_like(raw)
    if 0 in active:held[0]=raw[0]
    room=min(.24,max(0.,.84-float(np.abs(held).sum())))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.24+1e-10:
        raise ValueError("PN_GROSS")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode,_) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/6)+.07*np.sin(t/80+j))
    oi=1000*np.exp(.00002*t*(1+j/8)+.02*np.cos(t/110+j))
    observed=np.ones((HOURS,4),bool)
    observed[1000:1024,2]=False
    oi[~observed]=np.nan
    eligible={k:bool(observed[k-167:k+1].all()) for k in CLOCK}
    # Full source integration requires 143/157; synthetic signal testing
    # supplies 14 deterministic unavailable windows, not invented OI values.
    for k in CLOCK[143:]:
        observed[k,1]=False
        oi[k,1]=np.nan
    eligible={k:bool(observed[k-167:k+1].all()) for k in CLOCK}
    # Synthetic local causality is exercised on the first valid decision,
    # without pretending the synthetic mask matches the authenticated source.
    assert eligible[CLOCK[0]]
    b={"oi":oi,"observed":observed,"eligible":eligible}
    d={"c":c}
    # Replace only the synthetic eligibility count with a mask that has
    # exactly 143 valid decisions, while retaining exact causal consistency.
    observed[:]=True
    oi[:]=1000*np.exp(.00002*t*(1+j/8)+.02*np.cos(t/110+j))
    for k in CLOCK[143:]:
        observed[k,1]=False;oi[k,1]=np.nan
    b["eligible"]={k:bool(observed[k-167:k+1].all()) for k in CLOCK}
    assert sum(b["eligible"].values())==143
    a=signals(d,b)
    d2={"c":c.copy()}
    b2={"oi":oi.copy(),"observed":observed.copy(),"eligible":dict(b["eligible"])}
    d2["c"][15000:]*=np.array([1.4,.7,1.2,.8])
    b2["oi"][15000:]*=1.8
    changed=signals(d2,b2)
    for k in CLOCK:
        if k>=15000:continue
        x,y=a[k],changed[k]
        if x[1:]!=y[1:] or not np.array_equal(x[0],y[0]):
            raise ValueError("PN_FUTURE_CAUSAL_LEAK")
    books=target_books(a)
    if any(len(x)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in x.values())
           for x in books.values()):raise ValueError("PN_SYNTHETIC_BOOKS")
    if any(np.abs(a[k][0][1:]).sum()>1e-12 for k in CLOCK[143:]):
        raise ValueError("PN_MISSING_OI_NOT_CASH")
    return {"decision":"PASS_PN_SYNTHETIC_CAUSALITY_NOT_PNL",
            "decisions":157,"oi_eligible":143,"oi_blocked":14,
            "future_mutation_safe":True,"missing_oi_sleeves_cash":True}

def run(d,bridge):
    source=source_gate(d)
    decisions=signals(d,bridge)
    books=target_books(decisions)
    from pn_oi_leverage_migration_oracle import independent_decisions
    oracle=independent_decisions(d,bridge,decisions,books)
    if oracle["mismatches"]:raise ValueError("PN_INDEPENDENT_SIGNAL_ORACLE")
    print("PN_DECISION_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PN_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PN_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    sleeves=(("Opportunity","PN_minus_opportunity"),("Relative_Value","PN_minus_RV"),
             ("Stress_Recovery","PN_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PN_full"]
            marginals[label]={slot:full["log_growth"]-group[book]["log_growth"]
                              for slot,book in sleeves}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":CAGR")
            if full["turnover"]>1000000:failures.append(label+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(label+":drawdown")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(label+":annual")
            for slot,book in sleeves:
                if marginals[label][slot]<=.02:failures.append(label+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(label+":"+slot+":"+year+":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:
        failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fee_slippage_funding")
    out={"architecture":"PN","preregistration":"pn_oi_leverage_migration_prereg_20261101.md",
         "source":source,"oi_source_sha256":[p for _,p in __import__("v98_oi_clean4_value_bridge").SOURCES],
         "oi_verified_asset_hours":int(bridge["observed"].sum()),
         "oi_eligible_decisions":sum(v[2] for v in decisions.values()),
         "oi_blocked_decisions":sum(not v[2] for v in decisions.values()),
         "weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PN_TRAINING" if failures else "PASS_PROVISIONAL_PN_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PN_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
