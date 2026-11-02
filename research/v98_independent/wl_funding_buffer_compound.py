#!/usr/bin/env python3
"""WL: independent seven-slot causal signals; no PnL or benchmarks."""
from __future__ import annotations
import json, math
import numpy as np
from vy_cross_sectional_spread import HOURS, source_gate
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
CLOCK=tuple(range(743,HOURS-1,24))
BOOKS={"WL_full":(0,1,2,3),"WL_core_only":(0,),
       "WL_minus_opportunity":(0,2,3),"WL_minus_RV":(0,1,3),
       "WL_minus_stress":(0,1,2)}
def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],float))
    highs=np.asarray(d["h"],float)
    out={}
    for t in CLOCK:
        r336=p[t]-p[t-336]
        r72=p[t]-p[t-72]
        r24=p[t]-p[t-24]
        breadth=int(np.sum(r336>0))
        rank=sorted(range(4),key=lambda j:(-(r336[j]+.5*r72[j]),j))
        raw=np.zeros((4,4),dtype=float)
        positive=[j for j in rank if r336[j]>0]
        for j in positive[:2]:
            raw[0,j]=.19 if breadth>=2 else .09
        breakout=[j for j in range(4)
                  if r24[j]>.04 and d["c"][t,j]>float(np.max(highs[t-96:t,j]))]
        if breakout:
            j=sorted(breakout,key=lambda j:(-r24[j],j))[0]
            raw[1,j]=.12
        if float(np.max(r72)-np.min(r72))>.08:
            lo=int(np.argmin(r72));hi=int(np.argmax(r72))
            if lo!=hi:
                raw[2,lo]=+.05;raw[2,hi]=-.05
        normalized=np.exp(p[t-335:t+1]-p[t-336])
        market=np.mean(normalized,axis=1)
        market_dd=float(market[-1]/np.max(market)-1.)
        if market_dd<-.12 and float(np.mean(r24))>0 and breadth<=2:
            j=sorted(range(4),key=lambda j:(-r24[j],j))[0]
            raw[3,j]=.10
        regime="risk_off" if breadth<2 else "risk_on"
        if regime=="risk_off":
            raw[0]*=.60;raw[1]*=.50;raw[2]*=.50
        gross=float(np.abs(raw).sum())
        if gross>.70:
            raw*=.70/gross
        if not np.isfinite(raw).all() or float(np.abs(raw).sum())>.70+1e-10:
            raise ValueError("WL_ALLOCATOR_GROSS")
        out[t]={"weights":raw,"regime":regime,"market_drawdown":market_dd}
    return out
def books_from_decisions(dec):
    return {name:{t:np.sum(v["weights"][list(slots)],axis=0)
                  for t,v in dec.items()} for name,slots in BOOKS.items()}
def incidence(dec):
    return {slot:int(sum(bool(np.abs(v["weights"][i]).sum()>1e-12) for v in dec.values()))
            for i,slot in enumerate(SLOTS)}
def synthetic_test():
    x=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    p=100*np.exp(.00003*x*(1+j/8)+.12*np.sin(x/190+j))
    d={"o":p.copy(),"h":p*1.01,"l":p*.99,"c":p.copy(),
       "q":np.ones((HOURS,4))*1e6,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":p*.99,"mark_upper":p*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.00002,.00010,-.00008,.00020])
    a=targets(d)
    altered={k:v.copy() for k,v in d.items()}
    altered["c"][12000:]*=np.array([3.,.7,1.4,.5])
    altered["o"][12000:]*=np.array([3.,.7,1.4,.5])
    altered["h"][12000:]*=4.;altered["l"][12000:]*=.4
    altered["q"][12000:]*=2.
    altered["rate"][12000:]*=3.
    b=targets(altered)
    for t in CLOCK:
        if t>=12000:break
        if a[t]["regime"]!=b[t]["regime"] or not np.array_equal(a[t]["weights"],b[t]["weights"]):
            raise ValueError("WL_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books_from_decisions(a))!=5:
        raise ValueError("WL_CONTRACT")
    return {"decision":"PASS_WL_CAUSAL_SYNTHETIC_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,
            "2026_accessed":False,"holdout_accessed":False,"pnl_computed":False}
if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
