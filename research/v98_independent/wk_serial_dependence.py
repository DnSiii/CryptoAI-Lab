#!/usr/bin/env python3
"""V98 WK preregistered 48h serial-dependence seven-slot targets; no PnL."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,source_gate
CLOCK=tuple(range(743,HOURS-1,48))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WK_full":(0,1,2,3),"WK_core_only":(0,),
       "WK_minus_opportunity":(0,2,3),"WK_minus_RV":(0,1,3),
       "WK_minus_stress":(0,1,2)}

def acf1(x):
    x=np.asarray(x,float)
    if x.ndim!=1 or len(x)<3:raise ValueError("WK_ACF_INPUT")
    a=x[1:];b=x[:-1]
    a=a-a.mean();b=b-b.mean()
    denom=float(np.linalg.norm(a)*np.linalg.norm(b))
    return float((a@b)/denom) if denom>1e-15 else 0.

def targets(d):
    source_gate(d)
    if len(CLOCK)!=548:raise ValueError("WK_CLOCK")
    p=np.log(np.asarray(d["c"],float))
    r=np.diff(p,axis=0,prepend=p[:1])
    out={}
    for t in CLOCK:
        long=r[t-335:t+1]
        short=r[t-23:t+1]
        a336=np.array([acf1(long[:,j]) for j in range(4)])
        a24=np.array([acf1(short[:,j]) for j in range(4)])
        r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        raw=np.zeros((4,4),float)
        score=a336*r72
        j=min(range(4),key=lambda k:(-abs(score[k]),k))
        if score[j]!=0:raw[0,j]=.52*np.sign(score[j])
        regime="persistence" if float(a336.mean())>0 else "reversal"
        if regime=="reversal":raw[0]*=.75
        change=a24-a336
        j=min(range(4),key=lambda k:(-abs(change[k]),k))
        if abs(change[j])>=.10 and a24[j]*r24[j]!=0:
            raw[1,j]=.12*np.sign(a24[j]*r24[j])
        hi=min(range(4),key=lambda k:(-a336[k],k))
        lo=min(range(4),key=lambda k:(a336[k],k))
        if hi!=lo and a336[hi]-a336[lo]>=.10:
            raw[2,hi]=+.08;raw[2,lo]=-.08
        market24=float(r24.mean())
        if market24<=-.04 and float(a336.mean())>0:raw[3,0]=-.10
        elif market24>=+.04 and float(a336.mean())<0:raw[3,0]=-.08
        if float(np.std(short,axis=0).mean())>2.*max(float(np.std(long,axis=0).mean()),1e-12):
            raw*=.65
        selected=raw.copy()
        room=max(0.,.80-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.80+1e-10:raise ValueError("WK_GROSS")
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
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    cl=100*np.exp(.000025*t*(1+j/8)+.07*np.sin(t/31+j)+.01*np.sin(t/11+j*2))
    op=cl*(1+.003*np.sin(t/7+j))
    hi=np.maximum(op,cl)*1.004;lo=np.minimum(op,cl)*.996
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
            raise ValueError("WK_FUTURE_MUTATION_LEAK")
    if len(a)!=548 or len(books(d))!=5:raise ValueError("WK_BOOKS")
    return {"decision":"PASS_WK_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,"2026_accessed":False}
if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
