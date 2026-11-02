#!/usr/bin/env python3
"""WI preregistered downside/upside semivariance composed seven-slot targets; exposed training only."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,source_gate
CLOCK=tuple(range(743,HOURS-1,24))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WI_full":(0,1,2,3),"WI_core_only":(0,),
       "WI_minus_opportunity":(0,2,3),"WI_minus_RV":(0,1,3),
       "WI_minus_stress":(0,1,2)}
def targets(d):
    source_gate(d)
    if len(CLOCK)!=1096:raise ValueError("WI_CLOCK")
    p=np.log(np.asarray(d["c"],float))
    r=np.diff(p,axis=0,prepend=p[:1])
    out={}
    for t in CLOCK:
        tail=r[t-167:t+1]
        downside=np.square(np.minimum(tail,0)).sum(axis=0)
        upside=np.square(np.maximum(tail,0)).sum(axis=0)
        asym=(upside-downside)/(upside+downside+1e-12)
        r168=p[t]-p[t-168];r24=p[t]-p[t-24]
        d24=np.square(np.minimum(r[t-23:t+1],0)).sum(axis=0)
        history=np.square(np.minimum(r[t-695:t-23],0)).reshape(28,24,4).sum(axis=1)
        baseline=np.median(history,axis=0)
        shock=d24/np.maximum(baseline,1e-12)
        raw=np.zeros((4,4),float)
        hi=min(range(4),key=lambda k:(-asym[k],k))
        lo=min(range(4),key=lambda k:(asym[k],k))
        if asym[hi]>0 and r168[hi]>0:raw[0,hi]=+.48
        elif asym[lo]<0 and r168[lo]<0:raw[0,lo]=-.30
        eligible=[j for j in range(4) if shock[j]>=2. and r24[j]>0]
        if eligible:
            j=min(eligible,key=lambda k:(-shock[k],k));raw[1,j]=+.12
        if hi!=lo and asym[hi]-asym[lo]>=.25:
            raw[2,hi]=+.08;raw[2,lo]=-.08
        mean24=float(np.mean(r24))
        if mean24<=-.04:
            j=min(range(4),key=lambda k:(-d24[k],k));raw[3,j]=-.10
        elif mean24>=+.04:
            j=min(range(4),key=lambda k:(d24[k],k));raw[3,j]=+.08
        regime="risk_off" if float(np.mean(r168))<0 else "risk_on"
        if regime=="risk_off":raw[0]*=.65
        selected=raw.copy()
        room=max(0.,.72-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.72+1e-10:raise ValueError("WI_GROSS")
        out[t]={"weights":selected,"regime":regime}
    return out
def books(d):
    dec=targets(d)
    return {name:{t:sum((x["weights"][i] for i in slots),np.zeros(4))
                  for t,x in dec.items()} for name,slots in BOOKS.items()}
def incidence(dec):
    return {SLOTS[i]:int(sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()))
            for i in range(4)}
def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    cl=100*np.exp(.000025*t*(1+j/8)+.09*np.sin(t/51+j))
    op=cl*(1+.004*np.sin(t/11+j))
    hi=np.maximum(op,cl)*1.006;lo=np.minimum(op,cl)*.994
    d={"o":op,"h":hi,"l":lo,"c":cl,
       "q":np.broadcast_to(1e6*(1+.2*np.sin(t/17+j)),(HOURS,4)).copy(),
       "rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool),
       "mark_lower":cl*.99,"mark_upper":cl*1.01}
    d["event"][::8]=True;d["rate"][::8]=[.0001,-.00002,.00005,.0002]
    a=targets(d);b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2;b["rate"][14000:]*=2
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WI_FUTURE_MUTATION_LEAK")
    if len(a)!=1096 or len(books(d))!=5:raise ValueError("WI_BOOKS")
    return {"decision":"PASS_WI_SYNTHETIC_CAUSAL_NOT_PNL","decisions":len(a),
            "future_mutation_safe":True,"2026_accessed":False}
if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
