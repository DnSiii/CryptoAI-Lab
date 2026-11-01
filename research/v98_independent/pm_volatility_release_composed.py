#!/usr/bin/env python3
"""V98 PM preregistered volatility-release seven-slot training; 2025 exposed, no holdout."""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills
# Source reader only: no PK alpha, parameters, decisions, allocation or PnL reused.
from pk_premium_dislocation_composed import load_premium, PREMIUM_SHA

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PM_full":(0,1,2,3),"PM_core_only":(0,),
       "PM_minus_opportunity":(0,2,3),"PM_minus_RV":(0,1,3),
       "PM_minus_stress":(0,1,2)}
PRIORITY={"expansion":(1,2,3),"defense":(3,2,1),"transition":(2,1,3)}

def signals(d,premium):
    c=np.asarray(d["c"],float)
    rate=np.asarray(d["rate"],float)
    event=np.asarray(d["event"],bool)
    if (c.shape!=(HOURS,4) or premium.shape!=(HOURS,4) or
        rate.shape!=(HOURS,4) or event.shape!=(HOURS,4) or
        np.any(c<=0) or not np.isfinite(c).all() or
        not np.isfinite(premium).all() or not np.isfinite(rate).all()):
        raise ValueError("PM_SOURCE_GEOMETRY")
    p=np.log(c)
    out={}
    for t in CLOCK:
        if not np.all(event[t-168:t:8]) or np.any(event[t-167:t:8]):
            raise ValueError("PM_FUNDING_EVENT_CAUSAL_CLOCK")
        f=np.mean(rate[t-168:t:8],axis=0)
        pr=premium[t-1].copy()  # premium bar t is not complete
        r24=p[t]-p[t-24];r72=p[t]-p[t-72]
        r168=p[t]-p[t-168];r504=p[t]-p[t-504]
        h72=np.diff(p[t-72:t+1],axis=0)
        h336=np.diff(p[t-336:t+1],axis=0)
        v72=np.std(h72,axis=0)
        v336=np.std(h336,axis=0)
        quality=r504/np.maximum(v336*math.sqrt(504),.06)
        raw=np.zeros((4,4),float)
        core=sorted((j for j in range(4) if r504[j]>0 and r168[j]>0 and
                     f[j]<.00015 and pr[j]<.004),
                    key=lambda j:(-quality[j],j))
        for j,w in zip(core[:2],(.46,.24)):raw[0,j]=w
        opportunity=sorted((j for j in range(4) if
                             v72[j]/max(v336[j],1e-6)<.80 and
                             c[t,j]>np.max(c[t-168:t,j]) and
                             r24[j]>.018 and f[j]<.00018),
                           key=lambda j:(-r24[j]/max(v72[j],.0001),j))
        if opportunity:raw[1,opportunity[0]]=.20
        b=h336[:,0];b0=b-np.mean(b);den=max(float(np.mean(b0*b0)),1e-8)
        residual=np.zeros(4,float)
        for j in (1,2,3):
            x=h336[:,j]; beta=float(np.mean((x-np.mean(x))*b0))/den
            residual[j]=r168[j]-beta*r168[0]
        high=min((1,2,3),key=lambda j:(-residual[j],j))
        low=min((1,2,3),key=lambda j:(residual[j],j))
        if high!=low and residual[high]-residual[low]>.12 and f[high]-f[low]<.00010:
            raw[2,high]=.10;raw[2,low]=-.10
        if r72[0]<-.065 and int(np.sum(r72>0))<=1 and v72[0]>1.30*v336[0]:
            raw[3,0]=-.16
        elif r72[0]>.04 and int(np.sum(r24>0))>=3 and v72[0]>1.20*v336[0]:
            raw[3,0]=.16
        breadth=int(np.sum(r168>0))
        mode="expansion" if breadth>=3 else "defense" if breadth<=1 else "transition"
        out[t]=(raw,mode,(f,pr,residual))
    if len(out)!=157:raise ValueError("PM_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PM_ALLOCATOR_INPUT")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>.70+1e-10:raise ValueError("PM_CORE_GROSS")
    room=min(.30,max(0.,.84-core))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.30+1e-10:
        raise ValueError("PM_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode,_) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/5)+.05*np.sin(t/45+j))
    prem=np.broadcast_to(.0003*np.sin(t/31+j),(HOURS,4)).copy()
    d={"c":c,"rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool)}
    d["event"][::8]=True
    d["rate"][::8]=np.broadcast_to(.00004*np.sin(np.arange(0,HOURS,8)[:,None]/81+j),
                                   (len(range(0,HOURS,8)),4))
    a=signals(d,prem)
    d2={k:v.copy() for k,v in d.items()}
    p2=prem.copy()
    d2["c"][15000:]*=np.array([1.3,.8,1.5,.7])
    d2["rate"][15000::8]=.03
    p2[15000:]+=.05
    b=signals(d2,p2)
    for k in CLOCK:
        if k>=15000:continue
        x,y=a[k],b[k]
        if x[1]!=y[1] or not np.array_equal(x[0],y[0]) or any(
                not np.array_equal(v,w) for v,w in zip(x[2],y[2])):
            raise ValueError("PM_FUTURE_LEAK")
    books=target_books(a)
    if any(len(v)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in v.values())
           for v in books.values()):raise ValueError("PM_SYNTHETIC_GROSS")
    return {"decision":"PASS_PM_CAUSAL_SYNTHETIC_ONLY_NOT_PNL",
            "decisions":157,"books":5,"future_mutation_safe":True,
            "premium_bar_t_excluded":True,"funding_event_t_excluded":True}

def run(d,premium):
    source=source_gate(d)
    decisions=signals(d,premium)
    books=target_books(decisions)
    from pm_volatility_release_independent_oracle import independent_decisions
    oracle=independent_decisions(d,premium,decisions,books)
    if oracle["mismatches"]:raise ValueError("PM_INDEPENDENT_DECISION_ORACLE")
    print("PM_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PM_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PM_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PM_minus_opportunity"),("Relative_Value","PM_minus_RV"),
           ("Stress_Recovery","PM_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PM_full"]
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
    out={"architecture":"PM","preregistration":"pm_volatility_release_prereg_20261101.md",
         "premium_source_sha256":PREMIUM_SHA,"premium_asset_hours":int(premium.size),
         "premium_last_closed_bar_at_decision":"t-1",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PM_TRAINING" if failures else "PASS_PROVISIONAL_PM_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PM_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
