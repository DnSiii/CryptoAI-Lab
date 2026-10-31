#!/usr/bin/env python3
"""V98 OE volatility-aware portfolio sleeve allocator, causal and PnL-independent."""
import numpy as np
from oe_sources import HOURS,WARMUP
CAP=.84
def allocate(raw,sigma):
    raw=np.asarray(raw,float);sigma=np.asarray(sigma,float)
    if raw.shape!=(4,4) or sigma.shape!=(4,) or not np.isfinite(raw).all() or not np.isfinite(sigma).all() or np.any(sigma<0):
        raise ValueError("OE_ALLOC_INPUT")
    held=np.zeros((4,4));held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>CAP+1e-10:raise ValueError("OE_CORE_CAP")
    gross=np.abs(raw[1:]).sum(axis=1)
    budget=min(.36,max(0.,CAP-core))
    total=min(float(gross.sum()),budget)
    if total>0:
        vols=np.array([max(.01,float(np.dot(np.abs(raw[k]),sigma)/gross[k-1]))
                       if gross[k-1]>0 else 1. for k in (1,2,3)])
        strengths=np.divide(gross,vols)
        for k in (1,2,3):
            if gross[k-1]>0:held[k]=raw[k]*(total*strengths[k-1]/strengths.sum()/gross[k-1])
    if np.abs(held).sum()>CAP+1e-10 or np.abs(held.sum(axis=0)).sum()>np.abs(held).sum()+1e-10:
        raise ValueError("OE_HIDDEN_GROSS")
    return held,{"core_gross":core,"optional_gross":float(np.abs(held[1:]).sum()),"budget":budget}
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):raise ValueError("OE_SHAPE")
    result=np.zeros_like(raw);held=np.zeros((4,4))
    p=np.log(d["c"]);r=np.diff(p,axis=0,prepend=p[:1])
    count=core=0;counts={"Opportunity":0,"Relative_Value":0,"Stress_Recovery":0}
    for t in range(WARMUP,HOURS):
        if updates[t,1]:
            if not updates[t,1:].all() or t%8 or not np.all(d["event"][t]):
                raise ValueError("OE_CLOCK")
            sigma=np.std(r[t-167:t+1],axis=0)
            proposed,_=allocate(raw[t],sigma)
            if updates[t,0]:held[0]=proposed[0];core+=1
            held[1:]=proposed[1:]
            for i,k in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[k]+=1
            count+=1
        result[t]=held
    if count!=105 or core!=27:raise ValueError("OE_DECISION_COUNT")
    return {"weights":result,"allocation_decisions":count,"core_decisions":core,
            "activated_period_counts":counts,"causal_t_minus_one":True,
            "funding_future_used":False,"training_or_holdout_read_by_allocator":False}
def synthetic_tests():
    trial=np.zeros((4,4));trial[0,0]=.42;trial[0,1]=.20;trial[0,2]=.10
    trial[1,2]=.20;trial[2,1]=.10;trial[2,0]=-.10;trial[3,0]=-.20
    w,diag=allocate(trial,np.array([.04,.02,.01,.08]))
    if np.abs(w).sum()>.84+1e-12 or diag["optional_gross"]>.12+1e-12:
        raise ValueError("OE_SYNTHETIC_BUDGET")
    return True
if __name__=="__main__":
    assert synthetic_tests()
    print("OE_CAUSAL_ALLOCATOR_PASS_NOT_PNL")
