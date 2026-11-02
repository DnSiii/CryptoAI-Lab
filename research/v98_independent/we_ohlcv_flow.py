#!/usr/bin/env python3
"""V98 WE seven-slot signed OHLCV close-location flow targets; no economic result here."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WE_full":(0,1,2,3),"WE_core_only":(0,),
       "WE_minus_opportunity":(0,2,3),"WE_minus_RV":(0,1,3),
       "WE_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    c=np.asarray(d["c"],float);h=np.asarray(d["h"],float);l=np.asarray(d["l"],float)
    q=np.asarray(d["q"],float)
    width=h-l
    pressure=np.divide(2*c-h-l,width,out=np.zeros_like(c),where=width>0)
    if np.any(np.abs(pressure)>1+1e-9):raise ValueError("WE_CANDLE_PRESSURE")
    signed=pressure*q
    # Causal cumulative sums: window [a,b] = csum[b+1]-csum[a].
    sc=np.vstack((np.zeros((1,4)),np.cumsum(signed,axis=0)))
    qc=np.vstack((np.zeros((1,4)),np.cumsum(q,axis=0)))
    def flow(t,n):
        return (sc[t+1]-sc[t+1-n])/np.maximum(qc[t+1]-qc[t+1-n],1.)
    out={}
    for t in CLOCK:
        f168=flow(t,168);f72=flow(t,72);f24=flow(t,24)
        negative=float(np.mean(f168))<0.
        ranked=sorted(range(4),key=lambda j:(-f168[j],j))
        raw=np.zeros((4,4),float)
        for j in ranked[:2]:raw[0,j]=.075 if negative else .15
        for j in ranked[2:]:raw[0,j]=-.075 if negative else -.15
        recent=qc[t+1]-qc[t-23]
        previous=qc[t-23]-qc[t-47]
        volume_ratio=recent/np.maximum(previous,1.)
        eligible=[j for j in range(4) if abs(f24[j])>=.25 and volume_ratio[j]>=1.20]
        if eligible:
            j=min(eligible,key=lambda k:(-abs(f24[k]),k))
            raw[1,j]=.10 if f24[j]>=0 else -.10
        acceleration=f24-f168
        high=min(range(4),key=lambda j:(-acceleration[j],j))
        low=min(range(4),key=lambda j:(acceleration[j],j))
        if high!=low:raw[2,high]=.06;raw[2,low]=-.06
        if negative:
            j=min(range(4),key=lambda k:(f72[k],k))
            raw[3,j]=-.10
        else:
            j=min(range(4),key=lambda k:(-f72[k],k))
            raw[3,j]=+.07
        selected=raw.copy()
        room=max(0.,.90-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.90+1e-9:raise ValueError("WE_GROSS")
        out[t]={"weights":selected,"regime":"negative_flow" if negative else "positive_flow"}
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
    close=100*np.exp(.00004*t*(1+j/8)+.08*np.sin(t/95+j))
    op=close*(1+.004*np.sin(t/7+j))
    hi=np.maximum(op,close)*1.002
    lo=np.minimum(op,close)*.998
    q=np.broadcast_to(1e6*(1+.2*np.sin(t/19+j)),(HOURS,4)).copy()
    d={"o":op,"h":hi,"l":lo,"c":close,"q":q,
       "rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool),
       "mark_lower":close*.99,"mark_upper":close*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.0001,-.00002,.00005,.0002])
    a=targets(d);b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2.;b["rate"][14000:]*=2.
    c=targets(b)
    for k in CLOCK:
        if k>=14000:break
        if not np.array_equal(a[k]["weights"],c[k]["weights"]):
            raise ValueError("WE_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books(d))!=5:raise ValueError("WE_CLOCK_BOOKS")
    return {"decision":"PASS_WE_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
