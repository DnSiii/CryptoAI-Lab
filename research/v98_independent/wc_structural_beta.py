#!/usr/bin/env python3
"""V98 WC structural crypto beta plus liquidity, low-vol and crisis/recovery sleeves."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WC_full":(0,1,2,3),"WC_core_only":(0,),
       "WC_minus_opportunity":(0,2,3),"WC_minus_RV":(0,1,3),
       "WC_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],float))
    q=np.asarray(d["q"],float)
    out={}
    for t in CLOCK:
        market=float(np.mean(p[t]-p[t-168]))
        raw=np.zeros((4,4),float)
        raw[0]=.06 if market<0 else .12
        historical=np.arange(t-720,t-23,24)
        today=q[t-23:t+1].sum(axis=0)
        baseline=np.median(np.asarray([q[s-23:s+1].sum(axis=0) for s in historical]),axis=0)
        ratio=today/np.maximum(baseline,1.)
        best=min(range(4),key=lambda j:(-ratio[j],j))
        raw[1,best]=.12
        vol=np.std(np.diff(p[t-719:t+1],axis=0),axis=0)
        low=min(range(4),key=lambda j:(vol[j],j))
        high=min(range(4),key=lambda j:(-vol[j],j))
        if low!=high:raw[2,low]=+.08;raw[2,high]=-.08
        if market<0:raw[3,0]=-.12
        else:raw[3,3]=+.08
        selected=raw.copy()
        room=max(0.,.90-np.abs(selected[0]).sum())
        for i in (1,2,3):
            gross=np.abs(selected[i]).sum()
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-np.abs(selected[i]).sum())
        if np.abs(selected).sum()>.90+1e-9:raise ValueError("WC_GROSS")
        out[t]={"weights":selected,"regime":"stress" if market<0 else "growth"}
    return out

def books(d):
    dec=targets(d)
    return {name:{t:sum((x["weights"][i] for i in slots),np.zeros(4))
                  for t,x in dec.items()} for name,slots in BOOKS.items()}

def incidence(dec):
    return {SLOTS[i]:int(sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()))
            for i in range(4)}

def synthetic_test():
    h=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    p=100*np.exp(.00007*h*(1+j/9)+.13*np.sin(h/130+j))
    q=np.broadcast_to(1e6*(1+.3*np.sin(h/23+j)),(HOURS,4)).copy()
    d={"o":p.copy(),"h":p*1.002,"l":p*.998,"c":p.copy(),
       "q":q,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":p*.99,"mark_upper":p*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.0001,-.00002,.00005,.0002])
    a=targets(d);b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):b[k][14000:]*=1.5
    b["q"][14000:]*=2.;b["rate"][14000:]*=2.
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WC_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books(d))!=5:raise ValueError("WC_CLOCK_BOOKS")
    return {"decision":"PASS_WC_SYNTHETIC_CAUSAL_NOT_PNL","decisions":len(a),
            "future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
