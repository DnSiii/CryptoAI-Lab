#!/usr/bin/env python3
"""WN native premium-index seven-slot causal strategy, no PnL."""
from __future__ import annotations
import csv,datetime as dt,hashlib,json
from pathlib import Path
import numpy as np
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate,ASSETS
PIN="c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4"
SLOTS=("Growth_Core","Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"WN_full":(0,1,2,3),"WN_core_only":(0,),
       "WN_minus_opportunity":(0,2,3),"WN_minus_RV":(0,1,3),
       "WN_minus_stress":(0,1,2)}
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
def read_premium(path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=PIN:
        raise ValueError("WN_PREMIUM_SOURCE_SHA")
    x=np.full((HOURS,4),np.nan)
    seen=np.zeros((HOURS,4),bool)
    with path.open(newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames!=["asset","bar_open_utc","premium_open","premium_high",
                          "premium_low","premium_close","source_zip_sha256"]:
            raise ValueError("WN_PREMIUM_SCHEMA")
        for row in rd:
            if row["asset"] not in ASSETS:raise ValueError("WN_PREMIUM_ASSET")
            stamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            if stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0):
                raise ValueError("WN_PREMIUM_UTC")
            delta=(stamp-START).total_seconds()
            if delta<0 or delta>=HOURS*3600 or delta%3600:
                raise ValueError("WN_PREMIUM_TIME_SCOPE")
            t=int(delta//3600);j=ASSETS.index(row["asset"])
            if seen[t,j]:raise ValueError("WN_PREMIUM_DUPLICATE")
            o,h,l,c=(float(row[k]) for k in
                      ("premium_open","premium_high","premium_low","premium_close"))
            if not np.isfinite([o,h,l,c]).all() or max(abs(o),abs(h),abs(l),abs(c))>=1:
                raise ValueError("WN_PREMIUM_NONFINITE")
            if l>min(o,c)+1e-10 or h<max(o,c)-1e-10:
                raise ValueError("WN_PREMIUM_OHLC")
            x[t,j]=c;seen[t,j]=True
    if not seen.all() or int(seen.sum())!=HOURS*4:
        raise ValueError("WN_PREMIUM_MISSING_HOUR")
    return x

def targets(d,premium):
    source_gate(d)
    v=np.asarray(premium,float)
    if v.shape!=(HOURS,4) or not np.isfinite(v).all():
        raise ValueError("WN_PREMIUM_GEOMETRY")
    p=np.log(np.asarray(d["c"],float))
    out={}
    for t in CLOCK:
        r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        low=min(range(4),key=lambda j:(v[t,j],j))
        high=min(range(4),key=lambda j:(-v[t,j],j))
        raw=np.zeros((4,4),float)
        if low!=high and r168[low]>0:raw[0,low]=+.28
        if low!=high and r168[high]<0:raw[0,high]=-.28
        change=v[t]-v[t-24]
        j=min(range(4),key=lambda k:(-abs(change[k]),k))
        median=np.median(v[t-504:t],axis=0)
        if v[t,j]>median[j] and change[j]>0:raw[1,j]=-.12
        elif v[t,j]<median[j] and change[j]<0:raw[1,j]=+.12
        if low!=high and v[t,high]-v[t,low]>.00015:
            raw[2,low]=+.10;raw[2,high]=-.10
        market=float(np.mean(r24));prem=float(np.mean(v[t]))
        if market<-.04 and prem<0:raw[3,0]=+.12
        elif market>.04 and prem>0:raw[3,0]=-.12
        regime="btc_fast" if abs(r168[0])>.08 else "btc_normal"
        if regime=="btc_fast":raw[1]*=.60;raw[2]*=.60
        gross=float(np.abs(raw).sum())
        if gross>.70:raw*=.70/gross
        if not np.isfinite(raw).all() or np.abs(raw).sum()>.70+1e-10:
            raise ValueError("WN_GROSS")
        out[t]={"weights":raw,"regime":regime}
    return out

def books_from_decisions(dec):
    return {name:{t:np.sum(x["weights"][list(slots)],axis=0)
                  for t,x in dec.items()} for name,slots in BOOKS.items()}

def incidence(dec):
    return {slot:int(sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()))
            for i,slot in enumerate(SLOTS)}

def synthetic_test():
    h=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    cl=100*np.exp(.00004*h*(1+j/9)+.10*np.sin(h/180+j))
    d={"o":cl.copy(),"h":cl*1.01,"l":cl*.99,"c":cl.copy(),
       "q":np.full((HOURS,4),1e6),"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":cl*.99,"mark_upper":cl*1.01}
    d["event"][::8]=True;d["rate"][::8]=[.0001,-.00005,.00002,.0002]
    premium=np.broadcast_to(.0003*np.sin(h/130+j), (HOURS,4)).copy()
    a=targets(d,premium)
    b={k:v.copy() for k,v in d.items()}
    w=premium.copy()
    for k in ("o","h","l","c","mark_lower","mark_upper"):
        b[k][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2.;b["rate"][14000:]*=2.
    w[14000:]*=-5.
    c=targets(b,w)
    for t in CLOCK:
        if t>=14000:break
        if a[t]["regime"]!=c[t]["regime"] or not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WN_FUTURE_LEAK")
    if len(a)!=len(CLOCK) or len(books_from_decisions(a))!=5:
        raise ValueError("WN_BOOKS")
    return {"decision":"PASS_WN_SYNTHETIC_CAUSAL_NOT_PNL","decisions":len(a),
            "future_mutation_safe":True,"2026_accessed":False}
if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
