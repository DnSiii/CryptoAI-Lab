#!/usr/bin/env python3
"""V98 OD preregistered native OI/price seven-slot source; training only."""
import csv,datetime as dt,hashlib,json
from pathlib import Path
import numpy as np
from v98_oi_full_history_v2_independent_audit_20261027 import run as audit_oi
HOURS=18288;WARMUP=744;STEP=168;CORE_STEP=672
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
BOOKS={"OD_full":(0,1,2,3),"OD_core_only":(0,),
       "OD_minus_opportunity":(0,2,3),"OD_minus_RV":(0,1,3),
       "OD_minus_stress":(0,1,2)}
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
PINNED_SHA="68ecdb3827b1540f94fb50ee053adf4af356a27260fd930853fadf0d942c7c6e"
def load_oi(root):
    audit=audit_oi(root)
    if not audit["decision"].startswith("PASS_OI_ARTIFACT_INTEGRITY"):
        raise ValueError("OD_OI_SOURCE_AUDIT_REJECT")
    files=list(Path(root).rglob("v98_oi_full_history_v2_verified_hourly_20261027.csv"))
    if len(files)!=1:raise ValueError("OD_OI_SOURCE_INVENTORY")
    if hashlib.sha256(files[0].read_bytes()).hexdigest()!=PINNED_SHA:
        raise ValueError("OD_OI_SOURCE_SHA_MISMATCH")
    oi=np.full((HOURS,4),np.nan);seen=np.zeros((HOURS,4),bool)
    with files[0].open(newline="") as f:
        for row in csv.DictReader(f):
            ts=dt.datetime.fromisoformat(row["bar_open_utc"])
            delta=(ts-START).total_seconds()
            if ts.utcoffset()!=dt.timedelta(0) or delta%3600 or not 0<=delta//3600<HOURS:
                raise ValueError("OD_OI_TIMESTAMP_OR_RANGE")
            if row["asset"] not in ASSETS:raise ValueError("OD_OI_ASSET")
            t=int(delta//3600);j=ASSETS.index(row["asset"])
            if seen[t,j]:raise ValueError("OD_OI_DUPLICATE")
            val=float(row["oi_contracts"])
            if not np.isfinite(val) or val<=0:raise ValueError("OD_OI_INVALID")
            oi[t,j]=val;seen[t,j]=True
    if int(seen.sum())!=72264 or int((~seen).sum())!=888:
        raise ValueError("OD_OI_COVERAGE_CHANGED")
    return oi,{"decision":audit["decision"],"verified_hourly_asset_rows":int(seen.sum()),
               "quarantined_hourly_asset_rows":int((~seen).sum()),
               "source_sha256":PINNED_SHA}
def bundle(o,h,l,c,q,rate,event,oi):
    o,h,l,c,q,rate,event,oi=[np.asarray(x) for x in (o,h,l,c,q,rate,event,oi)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event,oi)):
        raise ValueError("OD_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("OD_PRICE_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("OD_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("OD_FUNDING_CALENDAR")
    p=np.log(c);raw=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);held=np.zeros((4,4))
    mask=np.isfinite(oi)&(oi>0);eligible=np.zeros(HOURS,bool)
    for t in range(WARMUP,HOURS,STEP):
        eligible[t]=bool(mask[t-167:t+1].all())
        r672=p[t]-p[t-672];r336=p[t]-p[t-336]
        r168=p[t]-p[t-168];r24=p[t]-p[t-24]
        if (t-WARMUP)%CORE_STEP==0:
            held[0]=0.
            choices=[j for j in range(4) if r672[j]>0 and r168[j]>0]
            choices.sort(key=lambda j:(-r672[j],j))
            if choices:
                held[0,choices[0]]=.54
                if len(choices)>1:held[0,choices[1]]=.18
            elif r168[0]<0 and np.count_nonzero(r168<0)>=3:
                held[0,0]=-.30
            updates[t,0]=True
        held[1:]=0.
        if eligible[t]:
            oi24=np.log(oi[t]/oi[t-24]);oi168=np.log(oi[t]/oi[t-167])
            choices=[j for j in range(4) if r24[j]>.025 and oi24[j]>.02 and oi168[j]>0]
            if choices:
                j=min(choices,key=lambda k:(-r24[k]*oi24[k],k))
                held[1,j]=.18
            score=r168-oi168
            j=min((1,2,3),key=lambda k:(-score[k],k))
            if score[j]-score[0]>.08 and r168[j]>0:
                held[2,j]=.10;held[2,0]=-.10
            if np.count_nonzero(r24<-.035)>=3 and np.count_nonzero(oi24<-.025)>=3:
                held[3,0]=-.16
            elif r168[0]<-.10 and r24[0]>.025 and np.count_nonzero(r24[1:]>0)>=2:
                held[3,0]=.14
            risk_on=bool(r336[0]>0 and np.count_nonzero(r168>0)>=3)
            held[1:]*=np.array([1.,.75,.50] if risk_on else [.75,1.,1.])[:,None]
        updates[t,1:]=True
        active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        raw[t]=held
        if t+1<HOURS:raw[t+1:]=held
    return raw,updates,active,eligible
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j));h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6;rate=np.zeros_like(c)
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    oi=np.exp(7+.00001*t*(1+j/5)+.08*np.sin(t/38+j))
    a=bundle(o,h,l,c,q,rate,event,oi)
    oi2=oi.copy();oi2[14000:]*=3
    c2=c.copy();c2[14000:]*=1.4
    o2=o.copy();o2[14000:]*=1.4
    h2=np.maximum(o2,c2)*1.005;l2=np.minimum(o2,c2)*.995
    b=bundle(o2,h2,l2,c2,q,rate,event,oi2)
    if not np.array_equal(a[0][:14000],b[0][:14000]):raise ValueError("OD_FUTURE_LEAK")
    oi3=oi.copy();oi3[900,2]=np.nan
    z=bundle(o,h,l,c,q,rate,event,oi3)
    if z[3][WARMUP+168] or np.any(z[0][WARMUP+168,1:]):
        raise ValueError("OD_QUARANTINE_LEAK")
    if int(a[1][:,0].sum())!=27 or int(a[1][:,1].sum())!=105:
        raise ValueError("OD_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OD_SYNTHETIC_CAUSAL_SOURCE_PASS_NOT_PNL")
