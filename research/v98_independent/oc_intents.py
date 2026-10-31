#!/usr/bin/env python3
"""V98 OC causal multi-sleeve breadth/volatility budget; no historical-PnL selection."""
import numpy as np
from oc_sources import HOURS,WARMUP,STEP
CAP=.84
def allocate(raw,sigma):
    raw=np.asarray(raw,float)
    if raw.shape!=(4,4) or not np.isfinite(raw).all() or not np.isfinite(sigma) or sigma<0:
        raise ValueError("OC_ALLOC_INPUT")
    held=np.zeros((4,4));held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>CAP+1e-10:raise ValueError("OC_CORE_CAP")
    budget=min(.28,max(0.,CAP-core))
    if sigma>.05:budget*=.5
    optional=float(np.abs(raw[1:]).sum())
    if optional>0:held[1:]=raw[1:]*min(1.,budget/optional)
    gross=float(np.abs(held).sum())
    if gross>CAP+1e-10 or np.abs(held.sum(axis=0)).sum()>gross+1e-10:
        raise ValueError("OC_HIDDEN_LEVERAGE")
    return held,{"core_gross":core,"optional_budget":budget,"gross":gross}
def build(d,raw,updates):
    if raw.shape!=(HOURS,4,4) or updates.shape!=(HOURS,4):
        raise ValueError("OC_INTENTS_SHAPE")
    result=np.zeros_like(raw);held=np.zeros((4,4))
    counts={"Opportunity":0,"Relative_Value":0,"Stress_Recovery":0}
    decisions=core_decisions=0
    p=np.log(d["c"]);r=np.diff(p[:,0],prepend=p[0,0])
    for t in range(WARMUP,HOURS):
        if updates[t,1]:
            if not updates[t,1:].all() or t%8 or not np.all(d["event"][t]):
                raise ValueError("OC_INTENTS_CALENDAR")
            sigma=float(np.std(r[t-167:t+1]))
            proposed,_=allocate(raw[t],sigma)
            if updates[t,0]:
                held[0]=proposed[0];core_decisions+=1
            held[1:]=proposed[1:]
            for i,name in enumerate(counts):
                if np.abs(held[i+1]).sum()>1e-12:counts[name]+=1
            decisions+=1
        result[t]=held
    if decisions!=105 or core_decisions!=27:raise ValueError("OC_INTENTS_DECISION_COUNT")
    return {"weights":result,"allocation_decisions":decisions,
            "core_decisions":core_decisions,"activated_period_counts":counts,
            "causal_t_minus_one":True,"funding_future_used":False,
            "training_or_holdout_read_by_allocator":False}
def synthetic_tests():
    from oc_sources import synthetic_causality,bundle
    synthetic_causality()
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j));h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6;rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    d={"o":o,"h":h,"l":l,"c":c,"q":q,"rate":rate,"event":event}
    raw,updates,_=bundle(o,h,l,c,q,rate,event);a=build(d,raw,updates)
    changed={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c"):changed[k][14000:]*=1.7
    changed["rate"][14000:]*=-1.
    raw2,upd2,_=bundle(*(changed[k] for k in ("o","h","l","c","q","rate","event")))
    b=build(changed,raw2,upd2)
    if not np.array_equal(a["weights"][:14000],b["weights"][:14000]):
        raise ValueError("OC_INTENTS_FUTURE_LEAK")
    trial=np.zeros((4,4));trial[0,0]=.52;trial[1,1]=.12;trial[2,2]=-.075;trial[2,0]=.075;trial[3,0]=-.14
    out,diag=allocate(trial,.01)
    assert np.abs(out[1:]).sum()<=.28+1e-12 and diag["gross"]<=.84
    out2,_=allocate(trial,.07)
    assert np.abs(out2[1:]).sum()<=.14+1e-12
    return True
if __name__=="__main__":
    assert synthetic_tests()
    print("OC_CAUSAL_ALLOCATOR_PASS_NOT_PNL")
