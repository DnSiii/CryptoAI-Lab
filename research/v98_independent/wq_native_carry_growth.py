#!/usr/bin/env python3
"""V98 WQ native funding receiver seven-slot strategy. No market PnL here."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,source_gate

CLOCK=tuple(range(743,HOURS-1,24))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WQ_full":(0,1,2,3),"WQ_core_only":(0,),
       "WQ_minus_opportunity":(0,2,3),"WQ_minus_RV":(0,1,3),
       "WQ_minus_stress":(0,1,2)}

def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],float))
    rates=np.asarray(d["rate"],float)
    volume=np.asarray(d["q"],float)
    result={}
    for t in CLOCK:
        r24=p[t]-p[t-24]
        r168=p[t]-p[t-168]
        r672=p[t]-p[t-672]
        e=t-t%8
        mean_rate=np.mean(rates[e-160:e+1:8],axis=0)
        vol168=np.std(np.diff(p[t-168:t+1],axis=0),axis=0)
        raw=np.zeros((4,4),dtype=float)
        eligible=[j for j in range(4) if
                  (r168[j]>0 and mean_rate[j]<0) or
                  (r168[j]<0 and mean_rate[j]>0)]
        eligible.sort(key=lambda j:(-abs(mean_rate[j])/max(vol168[j],1e-9),j))
        for j in eligible[:2]:
            raw[0,j]=.30 if r168[j]>0 else -.30
        hi72=np.max(p[t-72:t],axis=0)
        lo72=np.min(p[t-72:t],axis=0)
        vol_latest=np.sum(volume[t-23:t+1],axis=0)
        vol_prev=np.sum(volume[t-47:t-23],axis=0)
        up=[j for j in range(4) if p[t,j]>hi72[j] and vol_latest[j]>vol_prev[j]]
        down=[j for j in range(4) if p[t,j]<lo72[j] and vol_latest[j]>vol_prev[j]]
        if up or down:
            ranked=[(abs(r24[j]),-j,j,1) for j in up]+[(abs(r24[j]),-j,j,-1) for j in down]
            _,_,j,sign=max(ranked)
            raw[1,j]=.12*sign
        lowest=min(range(4),key=lambda j:(mean_rate[j],j))
        highest=min(range(4),key=lambda j:(-mean_rate[j],j))
        if lowest!=highest and mean_rate[highest]-mean_rate[lowest]>.00008:
            raw[2,lowest]=.08
            raw[2,highest]=-.08
        market24=float(np.mean(r24))
        market_prev24=float(np.mean(p[t-24]-p[t-48]))
        if market_prev24<-.04 and market24>.02:
            j=min(range(4),key=lambda k:(-r24[k],k))
            raw[3,j]=.12
        elif market24<-.04:
            j=min(range(4),key=lambda k:(r24[k],k))
            raw[3,j]=-.12
        regime="negative_market" if float(np.mean(r672))<0 else "positive_market"
        if regime=="negative_market":
            raw[:2]=np.where(raw[:2]>0,raw[:2]*.50,raw[:2])
        gross=float(np.abs(raw).sum())
        if gross>.70:
            raw*=.70/gross
        if not np.isfinite(raw).all() or float(np.abs(raw).sum())>.70+1e-10:
            raise ValueError("WQ_GROSS_OR_NONFINITE")
        result[t]={"weights":raw,"regime":regime}
    return result

def books_from_decisions(dec):
    return {name:{t:np.sum(x["weights"][list(slots)],axis=0)
                  for t,x in dec.items()} for name,slots in BOOKS.items()}

def incidence(dec):
    return {slot:int(sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()))
            for i,slot in enumerate(SLOTS)}

def synthetic_test():
    h=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    close=100*np.exp(.00004*h*(1+j/8)+.09*np.sin(h/120+j))
    volume=np.broadcast_to(1e6*(1+.2*np.sin(h/35+j)),(HOURS,4)).copy()
    d={"o":close.copy(),"h":close*1.01,"l":close*.99,"c":close.copy(),
       "q":volume,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":close*.99,"mark_upper":close*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([-.00012,.0001,-.00008,.00015])
    a=targets(d)
    b={k:v.copy() for k,v in d.items()}
    for key in ("o","h","l","c","mark_lower","mark_upper"):
        b[key][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2
    b["rate"][14000:]*=2
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if a[t]["regime"]!=c[t]["regime"] or not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WQ_FUTURE_MUTATION_LEAK")
    if len(a)!=1096 or len(books_from_decisions(a))!=5:
        raise ValueError("WQ_CLOCK_OR_BOOKS")
    return {"decision":"PASS_WQ_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a),"incidence":incidence(a),
            "future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
