#!/usr/bin/env python3
"""V98 WA: stateful per-asset 336h range breakout; seven-slot causal targets, no PnL."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WA_full":(0,1,2,3),"WA_core_only":(0,),
       "WA_minus_opportunity":(0,2,3),"WA_minus_RV":(0,1,3),
       "WA_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    close=np.asarray(d["c"],float)
    high=np.asarray(d["h"],float)
    low=np.asarray(d["l"],float)
    vol=np.asarray(d["q"],float)
    p=np.log(close)
    state=np.zeros(4,dtype=int)
    result={}
    for t in CLOCK:
        r24=p[t]-p[t-24]
        r168=p[t]-p[t-168]
        for j in range(4):
            up=close[t,j]>np.max(high[t-336:t,j])
            down=close[t,j]<np.min(low[t-336:t,j])
            if up and down:raise ValueError("WA_IMPOSSIBLE_BREAKOUT")
            if up:state[j]=1
            elif down:state[j]=-1
            elif state[j]>0 and close[t,j]<np.min(low[t-168:t,j]):state[j]=0
            elif state[j]<0 and close[t,j]>np.max(high[t-168:t,j]):state[j]=0
        raw=np.zeros((4,4),float)
        factor=.75 if int(np.sum(r168>0))<=1 else 1.
        raw[0]=state*.18*factor
        eligible=[j for j in range(4)
                  if close[t,j]>np.max(high[t-72:t,j])
                  and vol[t-23:t+1,j].sum()>1.25*vol[t-47:t-23,j].sum()]
        if eligible:
            j=min(eligible,key=lambda k:(-r24[k],k))
            raw[1,j]=.08
        hist=np.arange(t-504,t+1,24)
        past=np.std(p[hist]-p[hist-24],axis=1)
        if np.std(r24)>np.median(past):
            top=min(range(4),key=lambda k:(-r24[k],k))
            bottom=min(range(4),key=lambda k:(r24[k],k))
            raw[2,top]=.06;raw[2,bottom]=-.06
        if float(np.mean(r168))<=-.05:
            raw[3,0]=-.08;raw[3,1]=+.04
        selected=raw.copy()
        room=max(0.,.90-np.abs(selected[0]).sum())
        for i in (1,2,3):
            gross=np.abs(selected[i]).sum()
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-np.abs(selected[i]).sum())
        if np.abs(selected).sum()>.90+1e-9:
            raise ValueError("WA_GROSS_TARGET")
        result[t]={"weights":selected,"state":state.copy(),
                   "regime":"risk_off" if factor<1 else "normal"}
    return result

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
    d={"o":p.copy(),"h":p*1.002,"l":p*.998,"c":p.copy(),
       "q":np.ones((HOURS,4))*1e6,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":p*.99,"mark_upper":p*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.0001,-.00002,.00005,.0002])
    a=targets(d)
    b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):b[k][14000:]*=1.5
    b["q"][14000:]*=2.;b["rate"][14000:]*=2.
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]) or not np.array_equal(a[t]["state"],c[t]["state"]):
            raise ValueError("WA_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books(d))!=5:raise ValueError("WA_CLOCK_BOOKS")
    return {"decision":"PASS_WA_SYNTHETIC_CAUSAL_NOT_PNL","decisions":len(a),
            "future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
