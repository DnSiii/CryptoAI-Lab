#!/usr/bin/env python3
"""V98 PS preregistered daily stateful trend inventory seven-slot TRAINING, not validated."""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS
from ot_independent_oracle import independent_fills

FIRST=1008
CLOCK=tuple(range(FIRST,HOURS,24))
BOOKS={"PS_full":(0,1,2,3),"PS_core_only":(0,),
       "PS_minus_opportunity":(0,2,3),"PS_minus_RV":(0,1,3),
       "PS_minus_stress":(0,1,2)}
PRIORITY={"risk_off":(3,2,1),"risk_on":(1,2,3),"mixed":(2,1,3)}

def _sticky(eligible,prev):
    """Retain rank incumbents unless a challenger improves directional score enough."""
    selected=[]
    for rank in range(2):
        available=[(j,score) for j,score in eligible if j not in selected]
        if not available:break
        best_j,best_score=available[0]
        old_j=prev[rank] if rank<len(prev) else None
        old=next((score for j,score in available if j==old_j),None)
        if old is not None and best_j!=old_j and best_score-old<max(.02,.25*abs(old)):
            chosen=old_j
        else:chosen=best_j
        selected.append(chosen)
    return tuple(selected)

def signals(d):
    c=np.asarray(d["c"],dtype=float);q=np.asarray(d["q"],dtype=float)
    if c.shape!=(HOURS,4) or q.shape!=(HOURS,4) or not np.isfinite(c).all() or not np.isfinite(q).all() or np.any(c<=0) or np.any(q<0):
        raise ValueError("PS_SOURCE_GEOMETRY")
    p=np.log(c);out={};previous=();prev_side=None
    for t in CLOCK:
        r24=p[t]-p[t-24];r72=p[t]-p[t-72];r168=p[t]-p[t-168]
        r336=p[t]-p[t-336];r1008=p[t]-p[t-1008]
        sigma=np.maximum(np.std(np.diff(p[t-336:t+1],axis=0),axis=0)*math.sqrt(336),.05)
        breadth=int(np.sum(r336>0))
        score=(r1008+.5*r336)/sigma
        side=1 if breadth>=2 else -1
        eligible=sorted((j for j in range(4) if (r1008[j]>0 and r336[j]>0) if side==1),
                        key=lambda j:(-score[j],j)) if side==1 else sorted(
                        (j for j in range(4) if r1008[j]<0 and r336[j]<0),
                        key=lambda j:(score[j],j))
        directional=[(j,float(side*score[j])) for j in eligible]
        chosen=_sticky(directional,previous if prev_side==side else ())
        previous=chosen;prev_side=side
        raw=np.zeros((4,4),float)
        weights=(.36,.18) if side==1 else (-.32,-.18)
        for j,w in zip(chosen,weights):raw[0,j]=w
        vratio=np.sum(q[t-71:t+1],axis=0)/np.maximum(np.sum(q[t-143:t-71],axis=0),1.)
        high=np.max(c[t-407:t-71],axis=0);low=np.min(c[t-407:t-71],axis=0)
        opp=[j for j in range(4) if vratio[j]>=1.20 and
             ((c[t,j]>high[j] and r72[j]>.05) or (c[t,j]<low[j] and r72[j]<-.05))]
        if opp:
            j=min(opp,key=lambda k:(-abs(r72[k])/sigma[k],k))
            raw[1,j]=.16 if r72[j]>0 else -.16
        hi=min(range(4),key=lambda j:(-r168[j],j))
        lo=min(range(4),key=lambda j:(r168[j],j))
        if hi!=lo and r168[hi]-r168[lo]>=.22 and r24[hi]*r24[lo]<0:
            raw[2,lo]=.10;raw[2,hi]=-.10
        if breadth<=1 and int(np.sum(r24<-.045))>=3:
            j=min(range(4),key=lambda k:(r72[k],k));raw[3,j]=-.14
        elif breadth>=3 and int(np.sum(r24>.045))>=3 and float(np.median(r72))<-.04:
            j=min(range(4),key=lambda k:(-r24[k],k));raw[3,j]=.14
        mode="risk_off" if breadth<=1 else ("risk_on" if breadth>=3 else "mixed")
        out[t]=(raw,mode)
    if len(out)!=1085:raise ValueError("PS_DECISION_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PS_ALLOC_INPUT")
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
        raise ValueError("PS_GROSS")
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
    v=q.copy();v[15000:]*=3
    m=signals({"c":b,"q":v})
    for k in CLOCK:
        if k>=15000:break
        if a[k][1]!=m[k][1] or not np.array_equal(a[k][0],m[k][0]):
            raise ValueError("PS_FUTURE_LEAK")
    books=target_books(a)
    if any(len(v)!=1085 or any(np.abs(w).sum()>.84+1e-10 for w in v.values())
           for v in books.values()):raise ValueError("PS_SYNTHETIC_GROSS")
    return {"decision":"PASS_PS_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":1085,
            "books":5,"future_mutation_safe":True,"pnl_computed":False}

def run(d):
    source=source_gate(d)
    decisions=signals(d)
    books=target_books(decisions)
    from ps_daily_inventory_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["mismatches"]:raise ValueError("PS_INDEPENDENT_DECISION_ORACLE")
    print("PS_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PS_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PS_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-744-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PS_minus_opportunity"),("Relative_Value","PS_minus_RV"),
           ("Stress_Recovery","PS_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PS_full"]
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
    out={"architecture":"PS","preregistration":"ps_daily_inventory_composed_prereg_20261101.md",
         "source":source,"daily_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PS_TRAINING" if failures else "PASS_PROVISIONAL_PS_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PS_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
