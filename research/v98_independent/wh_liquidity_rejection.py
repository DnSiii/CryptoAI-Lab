#!/usr/bin/env python3
"""WH preregistered OHLC liquidity-rejection seven-slot targets; exposed training only."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,source_gate
CLOCK=tuple(range(743,HOURS-1,24))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WH_full":(0,1,2,3),"WH_core_only":(0,),
       "WH_minus_opportunity":(0,2,3),"WH_minus_RV":(0,1,3),
       "WH_minus_stress":(0,1,2)}
def targets(d):
    source_gate(d)
    if len(CLOCK)!=1096:raise ValueError("WH_CLOCK")
    op=np.asarray(d["o"],float);hi=np.asarray(d["h"],float)
    lo=np.asarray(d["l"],float);cl=np.asarray(d["c"],float)
    qv=np.asarray(d["q"],float);p=np.log(cl)
    width=np.maximum(hi-lo,1e-12)
    rejection=(np.minimum(op,cl)-lo-hi+np.maximum(op,cl))/width
    out={}
    for t in CLOCK:
        window=slice(t-23,t+1)
        w=qv[window]
        weight=w.sum(axis=0)
        if np.any(weight<=0):raise ValueError("WH_ZERO_REJECTION_VOLUME")
        score=(rejection[window]*w).sum(axis=0)/weight
        r24=p[t]-p[t-24];r168=p[t]-p[t-168]
        raw=np.zeros((4,4),float)
        j=min(range(4),key=lambda k:(-abs(score[k]),k))
        raw[0,j]=.35*np.sign(score[j])
        if float(np.mean(r168))<0:raw[0]*=.65
        recent_range=((hi-lo)/np.maximum(cl,1e-12))[window].sum(axis=0)
        median_range=np.median(((hi-lo)/np.maximum(cl,1e-12))[t-167:t+1],axis=0)
        ratio=recent_range/np.maximum(median_range,1e-12)
        j=min(range(4),key=lambda k:(-ratio[k],k))
        if ratio[j]>=1.5:raw[1,j]=-.10*np.sign(r24[j])
        top=min(range(4),key=lambda k:(-score[k],k))
        bottom=min(range(4),key=lambda k:(score[k],k))
        if top!=bottom and score[top]-score[bottom]>=.10:
            raw[2,top]=+.08;raw[2,bottom]=-.08
        avg=float(np.mean(r24))
        if avg<-.035:
            j=min(range(4),key=lambda k:(r24[k],k));raw[3,j]=-.08
        elif avg>.035:
            j=min(range(4),key=lambda k:(-r24[k],k));raw[3,j]=+.08
        selected=raw.copy()
        room=max(0.,.75-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.75+1e-10:raise ValueError("WH_GROSS")
        out[t]={"weights":selected,"regime":"risk_off" if np.mean(r168)<0 else "risk_on"}
    return out
def books(d):
    dec=targets(d)
    return {name:{t:sum((x["weights"][i] for i in slots),np.zeros(4))
                  for t,x in dec.items()} for name,slots in BOOKS.items()}
def incidence(dec):
    return {SLOTS[i]:int(sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()))
            for i in range(4)}
def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    cl=100*np.exp(.00002*t*(1+j/8)+.07*np.sin(t/31+j))
    op=cl*(1+.006*np.sin(t/11+j))
    hi=np.maximum(op,cl)*1.005
    lo=np.minimum(op,cl)*.995
    d={"o":op,"h":hi,"l":lo,"c":cl,
       "q":np.broadcast_to(1e6*(1+.2*np.sin(t/17+j)),(HOURS,4)).copy(),
       "rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool),
       "mark_lower":cl*.99,"mark_upper":cl*1.01}
    d["event"][::8]=True
    d["rate"][::8]=[.0001,-.00002,.00005,.0002]
    a=targets(d);b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2;b["rate"][14000:]*=2
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WH_FUTURE_MUTATION_LEAK")
    if len(a)!=1096 or len(books(d))!=5:raise ValueError("WH_BOOKS")
    return {"decision":"PASS_WH_SYNTHETIC_CAUSAL_NOT_PNL","decisions":len(a),
            "future_mutation_safe":True,"2026_accessed":False}
if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
