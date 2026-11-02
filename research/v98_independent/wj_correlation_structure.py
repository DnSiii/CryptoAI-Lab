#!/usr/bin/env python3
"""V98 WJ preregistered covariance-regime seven-slot targets; exposed training only."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS,source_gate
CLOCK=tuple(range(743,HOURS-1,24))
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WJ_full":(0,1,2,3),"WJ_core_only":(0,),
       "WJ_minus_opportunity":(0,2,3),"WJ_minus_RV":(0,1,3),
       "WJ_minus_stress":(0,1,2)}

def _corr(x):
    if x.shape[0]<3:return np.eye(4)
    z=np.corrcoef(x,rowvar=False)
    if not np.isfinite(z).all():raise ValueError("WJ_CORRELATION_NONFINITE")
    return z

def targets(d):
    source_gate(d)
    if len(CLOCK)!=1096:raise ValueError("WJ_CLOCK")
    p=np.log(np.asarray(d["c"],float))
    ret=np.diff(p,axis=0,prepend=p[:1])
    out={}
    for t in CLOCK:
        h=ret[t-671:t+1]
        c672=_corr(h)
        c72=_corr(ret[t-71:t+1])
        off=np.triu_indices(4,1)
        common_corr=float(np.mean(c672[off]))
        short_corr=float(np.mean(c72[off]))
        r336=p[t]-p[t-336];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        common336=float(np.mean(r336));common72=float(np.mean(r72))
        common24=float(np.mean(r24))
        raw=np.zeros((4,4),float)
        vol=np.std(h,axis=0)
        inv=1./np.maximum(vol,1e-8)
        inv/=inv.sum()
        if common336!=0:
            gross=.56 if common336*common72>0 else .28
            if common_corr<.50:gross*=.75
            raw[0]=np.sign(common336)*gross*inv
        residual=r72-common72
        j=min(range(4),key=lambda k:(-abs(residual[k]),k))
        if common_corr-short_corr>=.20 and abs(residual[j])>.02:
            raw[1,j]=np.sign(residual[j])*.12
        pairs=[(float(c672[i,j]),i,j) for i in range(4) for j in range(i+1,4)]
        _,a,b=sorted(pairs,key=lambda x:(-x[0],x[1],x[2]))[0]
        if c672[a,b]>0:
            x=h[:,a];y=h[:,b]
            xx=x-x.mean();den=float(xx@xx)
            beta=float((xx@(y-y.mean()))/den) if den>1e-15 else 0.
            residual_series=p[t-167:t+1,b]-beta*p[t-167:t+1,a]
            sigma=float(np.std(residual_series))
            z=(float(residual_series[-1])-float(np.mean(residual_series)))/max(sigma,1e-12)
            if abs(z)>=1.25:
                raw[2,b]=-.08*np.sign(z)
                raw[2,a]=+.08*np.sign(z)
        if common_corr>=.50:
            if common24<=-.05:raw[3,0]=-.12
            elif common24>=+.05:raw[3,0]=+.08
        common_hour=h.mean(axis=1)
        recent_hour=ret[t-23:t+1].mean(axis=1)
        if float(np.std(recent_hour))>2.*max(float(np.std(common_hour)),1e-12):
            raw*=.65
        selected=raw.copy()
        room=max(0.,.80-float(np.abs(selected[0]).sum()))
        for i in (1,2,3):
            gross=float(np.abs(selected[i]).sum())
            if gross>room and gross>0:selected[i]*=room/gross
            room=max(0.,room-float(np.abs(selected[i]).sum()))
        if np.abs(selected).sum()>.80+1e-10:raise ValueError("WJ_GROSS")
        out[t]={"weights":selected,"regime":"systemic" if common_corr>=.50 else "fragmented"}
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
    cl=100*np.exp(.000025*t*(1+j/8)+.06*np.sin(t/37+j)+.01*np.sin(t/11+j*2))
    op=cl*(1+.003*np.sin(t/7+j))
    hi=np.maximum(op,cl)*1.004;lo=np.minimum(op,cl)*.996
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
            raise ValueError("WJ_FUTURE_MUTATION_LEAK")
    if len(a)!=1096 or len(books(d))!=5:raise ValueError("WJ_BOOKS")
    return {"decision":"PASS_WJ_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a),"future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
