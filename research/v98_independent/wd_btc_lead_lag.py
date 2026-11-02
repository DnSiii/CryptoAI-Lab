#!/usr/bin/env python3
"""V98 WD preregistered BTC-led propagation seven-slot targets; NO PnL in this module."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS, CLOCK, source_gate

SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WD_full":(0,1,2,3),"WD_core_only":(0,),
       "WD_minus_opportunity":(0,2,3),"WD_minus_RV":(0,1,3),
       "WD_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],float))
    out={}
    for t in CLOCK:
        # 720h beta estimated using completed hourly log returns only.
        ret=np.diff(p[t-719:t+1],axis=0)
        btc=ret[:,0]
        centered=btc-btc.mean()
        denom=float(centered@centered)
        beta=np.ones(4,float)
        if denom>1e-15:
            beta[1:]=np.clip((ret[:,1:]-ret[:,1:].mean(axis=0)).T@centered/denom,.5,2.5)
        r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        residual72=r72[1:]-beta[1:]*r72[0]
        residual24=r24[1:]-beta[1:]*r24[0]
        b72=float(r72[0]);b12=float(p[t,0]-p[t-12,0])
        raw=np.zeros((4,4),float)
        # Underreaction relative to BTC impulse, directional BTC-led growth.
        direction=1. if b72>=0 else -1.
        j=1+min(range(3),key=lambda k:(direction*residual72[k],k))
        raw[0,0]=direction*.18
        raw[0,j]=direction*.24*(.75 if p[t,0]-p[t-168,0]<0 else 1.)
        if p[t,0]-p[t-168,0]<0:raw[0,0]*=.75
        # Propagate sufficiently large BTC 12h impulse to a lagging alt.
        if abs(b12)>=.025:
            s=1. if b12>0 else -1.
            k=1+min(range(3),key=lambda i:(s*residual24[i],i))
            raw[1,k]=s*.10
        lo=1+min(range(3),key=lambda i:(residual24[i],i))
        hi=1+min(range(3),key=lambda i:(-residual24[i],i))
        if lo!=hi:raw[2,lo]=+.07;raw[2,hi]=-.07
        volnow=float(np.std(np.diff(p[t-23:t+1,0])))
        historical=[float(np.std(np.diff(p[s-23:s+1,0])))
                    for s in range(t-720,t-23,24)]
        highvol=volnow>float(np.median(historical))
        maxbeta=1+min(range(3),key=lambda i:(-beta[i+1],i))
        raw[3,maxbeta]=-.10 if highvol else +.07
        selected=raw.copy()
        room=max(0.,.90-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.90+1e-9:raise ValueError("WD_GROSS")
        out[t]={"weights":selected,"regime":"btc_highvol" if highvol else "btc_calm"}
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
    p=100*np.exp(.00004*h*(1+j/9)+.10*np.sin(h/110+j)+.025*np.sin(h/11+j))
    q=np.broadcast_to(1e6*(1+.2*np.sin(h/19+j)),(HOURS,4)).copy()
    d={"o":p.copy(),"h":p*1.002,"l":p*.998,"c":p.copy(),
       "q":q,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":p*.99,"mark_upper":p*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.0001,-.00002,.00005,.0002])
    a=targets(d);b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2.;b["rate"][14000:]*=2.
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WD_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books(d))!=5:raise ValueError("WD_CLOCK_BOOKS")
    return {"decision":"PASS_WD_SYNTHETIC_CAUSAL_NOT_PNL","decisions":len(a),
            "future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
