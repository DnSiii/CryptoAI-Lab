#!/usr/bin/env python3
"""V98 PC: precommitted participation/volume-shock seven-slot complete portfolio.
Exploratory Clean-4 2022-25 only; no external benchmarks, holdout or paper.
"""
import json, math
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

BOOKS={"PC_full":(0,1,2,3),"PC_core_only":(0,),
       "PC_minus_opportunity":(0,2,3),"PC_minus_RV":(0,1,3),
       "PC_minus_stress":(0,1,2)}
PRIORITY={"expansion":(1,3,2),"calm":(2,1,3)}
MULT={"expansion":(1.,.5,1.),"calm":(.5,1.,.5)}
CLOCK=tuple(range(WARMUP,HOURS,STEP))

def signals(d):
    c=np.asarray(d["c"],float);q=np.asarray(d["q"],float)
    if c.shape!=(HOURS,4) or q.shape!=(HOURS,4) or not np.isfinite(c).all() or not np.isfinite(q).all() or np.any(c<=0) or np.any(q<0):
        raise ValueError("PC_SOURCE_SHAPE")
    p=np.log(c);result={}
    for t in CLOCK:
        r336=p[t]-p[t-336]
        r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        prev=np.diff(p[t-336:t-167,0])
        curr=np.diff(p[t-168:t+1,0])
        mode="expansion" if float(np.std(curr))>float(np.std(prev)) else "calm"
        raw=np.zeros((4,4),float)
        if r336[0]>0 and int(np.sum(r336>0))>=3:
            alt=min((1,2,3),key=lambda j:(-r336[j],j))
            raw[0,0]=.42;raw[0,alt]=.24
        elif r336[0]<0 and int(np.sum(r336<0))>=3:
            alt=min((1,2,3),key=lambda j:(r336[j],j))
            raw[0,0]=-.35;raw[0,alt]=-.22
        else:
            raw[0,0]=.22 if r336[0]>0 else (-.20 if r336[0]<0 else 0.)
        recent=np.sum(q[t-167:t+1],axis=0)
        earlier=np.sum(q[t-335:t-167],axis=0)
        ratios=np.divide(recent,earlier,out=np.zeros(4),where=earlier>0)
        long=[j for j in (1,2,3) if ratios[j]>=1.40 and r24[j]>0 and r168[j]>0]
        short=[j for j in (1,2,3) if ratios[j]>=1.40 and r24[j]<0 and r168[j]<0]
        if long:raw[1,min(long,key=lambda j:(-ratios[j],j))]=.18
        elif short:raw[1,min(short,key=lambda j:(-ratios[j],j))]=-.18
        residual=r24-r24[0]
        low=min((1,2,3),key=lambda j:(residual[j],j))
        high=min((1,2,3),key=lambda j:(-residual[j],j))
        if low!=high and residual[high]-residual[low]>.08 and r336[low]*r336[high]>0:
            raw[2,low]=.12;raw[2,high]=-.12
        if r24[0]<-.06 and r168[0]<0:raw[3,0]=-.20
        elif r168[0]<-.08 and r24[0]>.03:raw[3,0]=.20
        raw[1:]*=np.asarray(MULT[mode])[:,None]
        result[t]=(raw,mode)
    if len(result)!=157:raise ValueError("PC_WEEKLY_CLOCK")
    return result

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PC_BAD_ALLOCATION")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    room=min(.30,max(0.,.84-float(np.abs(held).sum())))
    for k in PRIORITY[mode]:
        if k not in active:continue
        gross=float(np.abs(raw[k]).sum())
        if gross>0 and room>0:
            take=min(gross,room)
            held[k]=raw[k]*(take/gross)
            room-=take
    if float(np.abs(held).sum())>.84+1e-10 or float(np.abs(held[1:]).sum())>.30+1e-10:
        raise ValueError("PC_GROSS")
    return held

def target_books(decisions):
    return {book:{t:allocate(raw,mode,active) for t,(raw,mode) in decisions.items()}
            for book,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS)[:,None];j=np.arange(4)[None,:]
    c=100*np.exp(.00002*t*(1+j/5)+.05*np.sin(t/91+j)+.025*np.cos(t/37+j))
    q=1000+100*np.sin(t/13+j)
    a=signals({"c":c,"q":q})
    c2=c.copy();c2[15000:]*=np.array([1.3,.8,1.7,.7])
    b=signals({"c":c2,"q":q})
    q2=q.copy();q2[15000:]*=2
    z=signals({"c":c,"q":q2})
    for decision in CLOCK:
        if decision<15000:
            for other in (b,z):
                if a[decision][1]!=other[decision][1] or not np.array_equal(a[decision][0],other[decision][0]):
                    raise ValueError("PC_FUTURE_LEAK")
    if len(target_books(a))!=5:raise ValueError("PC_BOOKS")
    return {"decision":"PASS_PC_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "future_price_and_volume_mutation_safe":True}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pc_independent_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["signal_and_allocation_mismatches"]:raise ValueError("PC_ORACLE_MISMATCH")
    print("PC_INDEPENDENT_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PC_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PC_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    audit=independent_accounting(d,ledger) if ledger and len(ledger)==HOURS-WARMUP-1 else None
    fill=independent_fills(d,ledger) if audit else None
    failures=[];marginals={}
    for tier in COSTS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            key=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(key+":physical");continue
            full=group["PC_full"]
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"] for slot,book in (
                ("Opportunity","PC_minus_opportunity"),("Relative_Value","PC_minus_RV"),("Stress_Recovery","PC_minus_stress"))}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1000000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in (("Opportunity","PC_minus_opportunity"),("Relative_Value","PC_minus_RV"),("Stress_Recovery","PC_minus_stress")):
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:failures.append("independent_accounting")
    if fill is None or fill["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills")
    out={"architecture":"PC","preregistration":"pc_participation_volume_prereg_20261031.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "audit":audit,"independent_decision_oracle":oracle,"independent_fill_oracle":fill,
         "gate_failures":failures,"decision":"REJECT_PC_TRAINING" if failures else "PASS_PROVISIONAL_PC_TRAINING_NOT_VALIDATED",
         "training_only":True,"year_2025_exposed":True,"exact_event_mark_attested":False,
         "holdout_accessed":False,"benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PC_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
