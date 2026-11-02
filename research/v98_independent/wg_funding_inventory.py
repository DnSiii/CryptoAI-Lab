#!/usr/bin/env python3
"""V98 WG preregistered weekly funding-inventory and volume-anchor seven-slot targets; no PnL."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,source_gate
WEEKLY_CLOCK=tuple(range(743,HOURS-1,168))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WG_full":(0,1,2,3),"WG_core_only":(0,),
       "WG_minus_opportunity":(0,2,3),"WG_minus_RV":(0,1,3),
       "WG_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    if len(WEEKLY_CLOCK)!=157:raise ValueError("WG_WEEKLY_CLOCK")
    close=np.asarray(d["c"],float)
    volume=np.asarray(d["q"],float)
    rate=np.asarray(d["rate"],float)
    p=np.log(close)
    out={}
    for t in WEEKLY_CLOCK:
        # Volume anchor uses only completed source hours [t-671,t].
        v=volume[t-671:t+1]
        vtot=v.sum(axis=0)
        if np.any(vtot<=0):raise ValueError("WG_ZERO_ANCHOR_VOLUME")
        anchor=(close[t-671:t+1]*v).sum(axis=0)/vtot
        premium=np.log(close[t]/anchor)
        if not np.isfinite(premium).all():raise ValueError("WG_ANCHOR_NONFINITE")
        ret168=p[t]-p[t-168]
        breadth=int(np.sum(ret168>0))
        e=t-(t%8)
        past=rate[e-328:e+1:8]
        recent=rate[e-16:e+1:8]
        if past.shape!=(42,4) or recent.shape!=(3,4):
            raise ValueError("WG_FUNDING_HISTORY")
        mean42=past.mean(axis=0)
        dislocation=recent.mean(axis=0)-mean42
        raw=np.zeros((4,4),float)
        # Growth Core: directional price discovery anchored to traded quote volume.
        if np.any(premium>0):
            j=min(range(4),key=lambda k:(-premium[k],k))
            raw[0,j]=+.52
        else:
            j=min(range(4),key=lambda k:(premium[k],k))
            raw[0,j]=-.52
        if breadth<3:raw[0]*=.65
        # Opportunity: funding dislocation direction is contrarian.
        j=min(range(4),key=lambda k:(-abs(dislocation[k]),k))
        if abs(dislocation[j])>1e-12:raw[1,j]=-.12 if dislocation[j]>0 else +.12
        # Relative value: long low-cost funding / short high-cost funding.
        lo=min(range(4),key=lambda k:(mean42[k],k))
        hi=min(range(4),key=lambda k:(-mean42[k],k))
        if lo!=hi:raw[2,lo]=+.09;raw[2,hi]=-.09
        # Stress: bearish breadth downside / calm lowest realized-vol exposure.
        if float(np.mean(ret168))<-.04:
            worst=min(range(4),key=lambda k:(ret168[k],k))
            raw[3,worst]=-.12
        else:
            rv=np.std(np.diff(p[t-168:t+1],axis=0),axis=0)
            calm=min(range(4),key=lambda k:(rv[k],k))
            raw[3,calm]=+.08
        selected=raw.copy()
        remaining=max(0.,.90-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>remaining and gross>0:selected[i]*=remaining/gross
            remaining=max(0.,remaining-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.90+1e-9:raise ValueError("WG_GROSS")
        out[t]={"weights":selected,"regime":"breadth_on" if breadth>=3 else "breadth_defensive"}
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
    close=100*np.exp(.00003*t*(1+j/8)+.07*np.sin(t/81+j))
    op=close*(1+.003*np.sin(t/7+j))
    hi=np.maximum(op,close)*1.003
    lo=np.minimum(op,close)*.997
    q=np.broadcast_to(1e6*(1+.2*np.sin(t/19+j)),(HOURS,4)).copy()
    d={"o":op,"h":hi,"l":lo,"c":close,"q":q,
       "rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool),
       "mark_lower":close*.99,"mark_upper":close*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.0001,-.00002,.00005,.0002])
    a=targets(d)
    b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2.
    b["rate"][14000:]*=2.
    c=targets(b)
    for t in WEEKLY_CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WG_FUTURE_MUTATION_LEAK")
    if len(a)!=157 or len(books(d))!=5:raise ValueError("WG_CLOCK_BOOKS")
    return {"decision":"PASS_WG_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,
            "2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
