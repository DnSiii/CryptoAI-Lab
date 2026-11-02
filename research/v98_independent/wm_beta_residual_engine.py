#!/usr/bin/env python3
"""WM: preregistered beta-hedged residual seven-slot signals. No market PnL."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS, CLOCK, source_gate
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WM_full":(0,1,2,3),"WM_core_only":(0,),
       "WM_minus_opportunity":(0,2,3),"WM_minus_RV":(0,1,3),
       "WM_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],dtype=float))
    ret=np.diff(p,axis=0)
    out={}
    for t in CLOCK:
        # 504 past one-hour returns ending at completed close t.
        past=ret[t-504:t,:]
        bvar=float(np.mean((past[:,0]-past[:,0].mean())**2))
        if bvar<1e-14: beta=np.zeros(3)
        else:
            centered=past[:,0]-past[:,0].mean()
            beta=np.array([np.mean(centered*(past[:,j]-past[:,j].mean()))/bvar
                           for j in (1,2,3)])
        beta=np.clip(beta,0.,3.)
        r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        residual168=r168[1:]-beta*r168[0]
        residual24=r24[1:]-beta*r24[0]
        raw=np.zeros((4,4),float)
        def hedged(slot,alt,weight):
            raw[slot,alt]+=weight
            raw[slot,0]-=weight*beta[alt-1]
        positive=[j for j in (1,2,3) if residual168[j-1]>0]
        if positive:
            j=min(positive,key=lambda k:(-residual168[k-1],k))
            hedged(0,j,.28)
        # Seven strictly prior completed daily windows; current 24h is excluded.
        prior=np.array([p[t-24*k,1:]-p[t-24*(k+1),1:]
                        -beta*(p[t-24*k,0]-p[t-24*(k+1),0])
                        for k in range(1,8)])
        opportunities=[j for j in (1,2,3) if residual24[j-1]>.03
                       and residual24[j-1]>float(np.max(prior[:,j-1]))]
        if opportunities:
            j=min(opportunities,key=lambda k:(-residual24[k-1],k))
            hedged(1,j,.12)
        hist=np.array([p[t-24*k,1:]-p[t-24*(k+1),1:]
                       -beta*(p[t-24*k,0]-p[t-24*(k+1),0])
                       for k in range(1,22)])
        med=np.median(hist,axis=0)
        mad=np.median(np.abs(hist-med),axis=0)
        z=(residual168-med*7.)/np.maximum(1.4826*mad*np.sqrt(7.),.01)
        choices=[j for j in (1,2,3) if abs(z[j-1])>1.5]
        if choices:
            j=min(choices,key=lambda k:(-abs(z[k-1]),k))
            hedged(2,j,-.10*np.sign(z[j-1]))
        if r168[0]<-.08 and r24[0]>.01:raw[3,0]=+.14
        elif r168[0]>.08 and r24[0]<-.02:raw[3,0]=-.10
        regime="btc_down" if r168[0]<0 else "btc_up"
        if regime=="btc_down":raw[0]*=.60;raw[1]*=.60
        gross=float(np.abs(raw).sum())
        if gross>.70:raw*=.70/gross
        if not np.isfinite(raw).all() or np.abs(raw).sum()>.70+1e-10:
            raise ValueError("WM_GROSS_OR_NONFINITE")
        out[t]={"weights":raw,"regime":regime}
    return out

def books_from_decisions(dec):
    return {name:{t:np.sum(v["weights"][list(slots)],axis=0)
                  for t,v in dec.items()} for name,slots in BOOKS.items()}

def incidence(dec):
    return {slot:int(sum(np.abs(v["weights"][i]).sum()>1e-12 for v in dec.values()))
            for i,slot in enumerate(SLOTS)}

def synthetic_test():
    h=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    cl=100*np.exp(.00005*h*(1+j/8)+.12*np.sin(h/180+j))
    d={"o":cl.copy(),"h":cl*1.01,"l":cl*.99,"c":cl.copy(),
       "q":np.full((HOURS,4),1e6),"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":cl*.99,"mark_upper":cl*1.01}
    d["event"][::8]=True
    d["rate"][::8]=[.0001,-.00005,.00002,.0002]
    a=targets(d)
    b={k:v.copy() for k,v in d.items()}
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2.;b["rate"][14000:]*=2.
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if a[t]["regime"]!=c[t]["regime"] or not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WM_FUTURE_LEAK")
    if len(a)!=len(CLOCK) or len(books_from_decisions(a))!=5:
        raise ValueError("WM_BOOK_GEOMETRY")
    return {"decision":"PASS_WM_CAUSAL_SYNTHETIC_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,
            "2026_accessed":False,"holdout_accessed":False}

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
