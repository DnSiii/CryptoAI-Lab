#!/usr/bin/env python3
"""V98 OD preregistered causal optional OI allocation, no PnL optimization."""
import numpy as np
from od_sources import HOURS,WARMUP,STEP
CAP=.84
def allocate(raw,sigma):
    raw=np.asarray(raw,float)
    if raw.shape!=(4,4) or not np.isfinite(raw).all() or not np.isfinite(sigma) or sigma<0:
        raise ValueError("OD_ALLOC_INPUT")
    held=np.zeros((4,4));held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>CAP+1e-10:raise ValueError("OD_CORE_CAP")
    budget=min(.30,max(0.,CAP-core))
    if sigma>.05:budget*=.5
    optional=float(np.abs(raw[1:]).sum())
    if optional>0:held[1:]=raw[1:]*min(1.,budget/optional)
    gross=float(np.abs(held).sum())
    if gross>CAP+1e-10 or np.abs(held.sum(axis=0)).sum()>gross+1e-10:
        raise ValueError("OD_HIDDEN_LEVERAGE")
    return held,{"core_gross":core,"optional_budget":budget,"gross":gross}
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):
        raise ValueError("OD_INTENTS_SHAPE")
    result=np.zeros_like(raw);held=np.zeros((4,4))
    counts={"Opportunity":0,"Relative_Value":0,"Stress_Recovery":0}
    decisions=core_decisions=0
    p=np.log(d["c"][:,0]);r=np.diff(p,prepend=p[0])
    for t in range(WARMUP,HOURS):
        if updates[t,1]:
            if not updates[t,1:].all() or t%8 or not np.all(d["event"][t]):
                raise ValueError("OD_INTENTS_CALENDAR")
            sigma=float(np.std(r[t-167:t+1]))
            proposed,_=allocate(raw[t],sigma)
            if updates[t,0]:
                held[0]=proposed[0];core_decisions+=1
            held[1:]=proposed[1:]
            for i,name in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[name]+=1
            decisions+=1
        result[t]=held
    if decisions!=105 or core_decisions!=27:raise ValueError("OD_INTENTS_CLOCK")
    return {"weights":result,"allocation_decisions":decisions,
            "core_decisions":core_decisions,"activated_period_counts":counts,
            "causal_t_minus_one":True,"funding_future_used":False,
            "training_or_holdout_read_by_allocator":False}
def synthetic_tests():
    from od_sources import synthetic_causality
    synthetic_causality()
    trial=np.zeros((4,4));trial[0,0]=.54;trial[0,1]=.18
    trial[1,2]=.18;trial[2,3]=.10;trial[2,0]=-.10;trial[3,0]=-.16
    out,diag=allocate(trial,.01)
    assert np.abs(out[1:]).sum()<=.12+1e-12 and diag["gross"]<=.84
    out2,_=allocate(trial,.07)
    assert np.abs(out2[1:]).sum()<=.06+1e-12
    return True
if __name__=="__main__":
    assert synthetic_tests()
    print("OD_ALLOCATOR_CAUSAL_SYNTHETIC_PASS_NOT_PNL")
