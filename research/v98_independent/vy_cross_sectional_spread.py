#!/usr/bin/env python3
"""V98 VY: preregistered perpetual-only seven-slot cross-sectional targets. No PnL."""
from __future__ import annotations
import json,math
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=27048
WARMUP=744
STEP=24
CLOCK=tuple(range(WARMUP-1,HOURS-1,STEP))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"VY_full":(0,1,2,3),"VY_core_only":(0,),
       "VY_minus_opportunity":(0,2,3),"VY_minus_RV":(0,1,3),
       "VY_minus_stress":(0,1,2)}

def source_gate(d):
    for k in ("o","h","l","c","q","rate","event","mark_lower","mark_upper"):
        if np.asarray(d[k]).shape!=(HOURS,4):raise ValueError("VY_SOURCE_SHAPE_"+k)
    for k in ("o","h","l","c","q","rate"):
        if not np.isfinite(d[k]).all():raise ValueError("VY_NONFINITE_"+k)
    if np.any(d["o"]<=0) or np.any(d["c"]<=0) or np.any(d["l"]<=0) or np.any(d["h"]<np.maximum(d["o"],d["c"])) or np.any(d["l"]>np.minimum(d["o"],d["c"])) or np.any(d["q"]<0):
        raise ValueError("VY_BAD_OHLC")
    ev=np.asarray(d["event"])
    if ev.dtype!=bool or int(ev.sum())!=13524 or not np.all(ev[::8]) or np.any(ev[np.arange(HOURS)%8!=0]):
        raise ValueError("VY_FUNDING_CLOCK")
    if np.any(d["rate"][~ev]!=0) or np.any(np.abs(d["rate"][ev])>1):
        raise ValueError("VY_FUNDING_RATE")
    lo=np.asarray(d["mark_lower"]);hi=np.asarray(d["mark_upper"])
    if not np.isfinite(lo[ev]).all() or not np.isfinite(hi[ev]).all() or np.any(lo[ev]<=0) or np.any(hi[ev]<lo[ev]):
        raise ValueError("VY_FUNDING_MARK_ENVELOPE")
    return {"hours":HOURS,"native_funding_events":13524,
            "decision":"PASS_SOURCE_GEOMETRY_NOT_PROVENANCE_OR_PNL"}

def targets(d):
    source_gate(d)
    p=np.log(np.asarray(d["c"],float))
    rate=np.asarray(d["rate"],float)
    out={}
    for t in CLOCK:
        r672=p[t]-p[t-672];r48=p[t]-p[t-48]
        vol=np.std(np.diff(p[t-672:t+1],axis=0),axis=0)*math.sqrt(672)
        score=r672/np.maximum(vol,1e-9)
        ranked=sorted(range(4),key=lambda j:(-score[j],j))
        breadth=int(np.sum(r672>0))
        regime="risk_on" if breadth>=3 else "risk_off" if breadth<=1 else "mixed"
        raw=np.zeros((4,4),float)
        core_scale=.5 if regime=="risk_off" else 1.
        for j in ranked[:2]:raw[0,j]=+.15*core_scale
        for j in ranked[2:]:raw[0,j]=-.15*core_scale
        past=np.arange(t-671,t+1)
        historical_disp=np.std(p[past]-p[past-48],axis=1)
        if np.std(r48)>float(np.median(historical_disp)):
            top=min(range(4),key=lambda j:(-r48[j],j))
            bottom=min(range(4),key=lambda j:(r48[j],j))
            raw[1,top]=+.08;raw[1,bottom]=-.08
        e=t-(t%8)
        means=np.mean(rate[e-160:e+1:8],axis=0)
        low=min(range(4),key=lambda j:(means[j],j))
        high=min(range(4),key=lambda j:(-means[j],j))
        if low!=high and means[high]-means[low]>.00015:
            raw[2,low]=+.08;raw[2,high]=-.08
        top=min(range(4),key=lambda j:(-r48[j],j))
        bottom=min(range(4),key=lambda j:(r48[j],j))
        if np.mean(r48)<0:
            raw[3,top]=+.06;raw[3,bottom]=-.06
        else:
            raw[3,bottom]=+.06;raw[3,top]=-.06
        selected=raw.copy()
        room=max(0.,.90-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.90+1e-9 or abs(float(selected.sum()))>1e-9:
            raise ValueError("VY_GROSS_OR_NET_TARGET")
        out[t]={"regime":regime,"raw":raw,"weights":selected}
    return out

def books(d):
    dec=targets(d)
    result={}
    for name,slots in BOOKS.items():
        result[name]={t:sum((x["weights"][i] for i in slots),np.zeros(4)) for t,x in dec.items()}
    return result

def incidence(dec):
    return {SLOTS[i]:sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()) for i in range(4)}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    p=100*np.exp(.00003*t*(1+j/9)+.12*np.sin(t/190+j))
    d={"o":p.copy(),"h":p*1.01,"l":p*.99,"c":p.copy(),
       "q":np.ones((HOURS,4))*1e6,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":p*.99,"mark_upper":p*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.00002,.00010,-.00008,.00020])
    a=targets(d)
    mutated={k:v.copy() for k,v in d.items()}
    mutated["c"][12000:]*=np.array([3.,.7,1.4,.5])
    mutated["o"][12000:]*=np.array([3.,.7,1.4,.5])
    mutated["h"][12000:]*=4.;mutated["l"][12000:]*=.4
    mutated["q"][12000:]*=2.
    mutated["rate"][12000:]*=3.
    b=targets(mutated)
    for t in CLOCK:
        if t>=12000:continue
        if a[t]["regime"]!=b[t]["regime"] or not np.array_equal(a[t]["weights"],b[t]["weights"]):
            raise ValueError("VY_FUTURE_MUTATION_LEAK")
    if len(a)!=len(CLOCK) or len(books(d))!=5:raise ValueError("VY_BOOK_COUNT")
    return {"decision":"PASS_VY_CAUSAL_SYNTHETIC_NOT_ECONOMIC",
            "decisions":len(a),"future_mutation_safe":True,
            "2026_accessed":False,"pnl_computed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
