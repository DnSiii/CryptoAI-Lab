#!/usr/bin/env python3
"""V98 WF preregistered range-volatility state-transition seven-slot targets. No PnL."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WF_full":(0,1,2,3),"WF_core_only":(0,),
       "WF_minus_opportunity":(0,2,3),"WF_minus_RV":(0,1,3),
       "WF_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],float))
    hi=np.log(np.asarray(d["h"],float))
    lo=np.log(np.asarray(d["l"],float))
    ranges=hi-lo
    if np.any(ranges<0):raise ValueError("WF_NEGATIVE_RANGE")
    out={}
    for t in CLOCK:
        intensity_today=np.sum(ranges[t-23:t+1],axis=0)
        # 28 nonoverlapping completed daily windows strictly BEFORE current 24h.
        baseline=np.median(np.array([
            np.sum(ranges[t-23-24*k:t+1-24*k],axis=0)
            for k in range(1,29)]),axis=0)
        intensity=intensity_today/np.maximum(baseline,1e-8)
        r72=p[t]-p[t-72]
        efficiency=np.abs(r72)/np.maximum(
            np.sum(np.abs(np.diff(p[t-72:t+1],axis=0)),axis=0),1e-8)
        if np.any(efficiency>1+1e-8):raise ValueError("WF_EFFICIENCY_RANGE")
        signed=np.sign(r72)*efficiency
        shock=float(np.mean(intensity))>1.10
        raw=np.zeros((4,4),float)
        order=sorted(range(4),key=lambda j:(-signed[j],j))
        for j in order[:2]:raw[0,j]=.09 if shock else .18
        for j in order[2:]:raw[0,j]=-.06 if shock else -.12
        candidates=[j for j in range(4) if intensity[j]>=1.20]
        if candidates:
            j=min(candidates,key=lambda k:(-intensity[k],k))
            raw[1,j]=.12 if p[t,j]>=p[t-24,j] else -.12
        strongest=min(range(4),key=lambda j:(-efficiency[j],j))
        weakest=min(range(4),key=lambda j:(efficiency[j],j))
        if strongest!=weakest:
            raw[2,strongest]=.07
            raw[2,weakest]=-.07
        if shock:
            j=min(range(4),key=lambda k:(-intensity_today[k],k))
            raw[3,j]=-.10
        else:
            j=min(range(4),key=lambda k:(intensity_today[k],k))
            raw[3,j]=+.07
        selected=raw.copy()
        remaining=max(0.,.90-float(np.abs(selected[0]).sum()))
        for slot in (1,2,3):
            gross=float(np.abs(selected[slot]).sum())
            if gross>remaining and gross>0:selected[slot]*=remaining/gross
            remaining=max(0.,remaining-float(np.abs(selected[slot]).sum()))
        if np.abs(selected).sum()>.90+1e-9:raise ValueError("WF_GROSS")
        out[t]={"weights":selected,"regime":"range_shock" if shock else "range_normal"}
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
    for t in CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WF_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books(d))!=5:raise ValueError("WF_CLOCK_BOOKS")
    return {"decision":"PASS_WF_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,
            "2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
