#!/usr/bin/env python3
"""ON causal stateful inventory allocator, no PnL feedback."""
import numpy as np
from on_sources import HOURS,WARMUP,state
CAP=.84
PRIORITY={"positive":(1,2,3),"negative":(3,2,1),"mixed":(2,1,3)}
def allocate(raw,mode):
    raw=np.asarray(raw,float)
    if raw.shape!=(4,4) or not np.isfinite(raw).all() or mode not in PRIORITY:raise ValueError("ON_ALLOC_INPUT")
    held=np.zeros((4,4));held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>CAP+1e-10:raise ValueError("ON_CORE_CAP")
    budget=min(.32,max(0.,CAP-core));remaining=budget
    for k in PRIORITY[mode]:
        gross=float(np.abs(raw[k]).sum())
        if gross>0 and remaining>0:
            used=min(gross,remaining);held[k]=raw[k]*(used/gross);remaining-=used
    if np.abs(held).sum()>CAP+1e-10:raise ValueError("ON_HIDDEN_GROSS")
    return held,{"core_gross":core,"optional_gross":float(np.abs(held[1:]).sum()),"budget":budget,"mode":mode}
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):raise ValueError("ON_SHAPE")
    result=np.zeros_like(raw);held=np.zeros((4,4));p=np.log(d["c"])
    count=core=0;counts={"Opportunity":0,"Relative_Value":0,"Stress_Recovery":0}
    for t in range(WARMUP,HOURS):
        if updates[t,1]:
            if not updates[t,1:].all() or t%8 or not np.all(d["event"][t]):raise ValueError("ON_CLOCK")
            mode=state(p[t]-p[t-672],p[t]-p[t-168])
            proposed,_=allocate(raw[t],mode)
            if updates[t,0]:held[0]=proposed[0];core+=1
            held[1:]=proposed[1:]
            for i,k in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[k]+=1
            count+=1
        result[t]=held
    if count!=105 or core!=int(updates[:,0].sum()):raise ValueError("ON_DECISION_COUNT")
    return {"weights":result,"allocation_decisions":count,"core_decisions":core,
            "activated_period_counts":counts,"causal_t_minus_one":True,
            "funding_future_used":False,"training_or_holdout_read_by_allocator":False}
def synthetic_tests():
    raw=np.zeros((4,4));raw[0,0]=.46;raw[0,1]=.18
    raw[1,2]=.22;raw[2,1]=.12;raw[2,0]=-.12;raw[3,0]=-.22;raw[3,1]=-.10
    a,_=allocate(raw,"positive");b,_=allocate(raw,"negative")
    if np.abs(a).sum()>.84+1e-12 or np.abs(b).sum()>.84+1e-12:raise ValueError("ON_BUDGET")
    if not np.abs(a[1]).sum()>np.abs(a[3]).sum() or not np.abs(b[3]).sum()>np.abs(b[1]).sum():raise ValueError("ON_PRIORITY")
    return True
if __name__=="__main__":
    assert synthetic_tests()
    print("ON_CAUSAL_ALLOCATOR_PASS_NOT_PNL")
