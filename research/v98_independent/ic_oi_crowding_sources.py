#!/usr/bin/env python3
"""IC preregistered OI-crowding seven-slot causal source, native Clean4 only."""
from __future__ import annotations
import csv,datetime as dt,hashlib,json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
WARMUP=744
CLOCK=336
HOURS=18288
GROSS={"TREND":.72,"TRANSITION":.68,"STRESS":.58}
PRIOR={"TREND":np.array([.52,.20,.14,.14]),
       "TRANSITION":np.array([.60,.16,.12,.12]),
       "STRESS":np.array([.64,.10,.10,.16])}
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)

def load_oi():
    p=HERE/"v98_oi_full_history_v2_verified_hourly_20261027.csv"
    m=HERE/"v98_oi_full_history_source_v2_report_20261027.json"
    if not p.is_file() or not m.is_file():raise ValueError("IC_MISSING_INDEPENDENTLY_AUDITED_OI_ARTIFACT")
    manifest=json.loads(m.read_text())
    if (manifest.get("files_expected")!=3048 or manifest.get("files_verified_complete")!=3011
        or manifest.get("files_quarantined")!=37 or manifest.get("verified_hourly_rows")!=72264
        or manifest.get("holdout_2025_read") is not False
        or hashlib.sha256(p.read_bytes()).hexdigest()!=manifest["hourly_csv_sha256"]):
        raise ValueError("IC_OI_PIN_OR_INTEGRITY_MISMATCH")
    oi=np.full((HOURS,4),np.nan,dtype=float)
    seen=set()
    with p.open(newline="") as f:
        for row in csv.DictReader(f):
            t=dt.datetime.fromisoformat(row["bar_open_utc"])
            hours=(t-START).total_seconds()/3600.
            if hours!=int(hours) or not 0<=int(hours)<HOURS:
                raise ValueError("IC_OI_TIMESTAMP_OUTSIDE_TRAINING")
            ix=int(hours);asset=row["asset"]
            if asset not in ASSETS or (ix,asset) in seen:
                raise ValueError("IC_OI_DUPLICATE_OR_WRONG_ASSET")
            seen.add((ix,asset))
            oi[ix,ASSETS.index(asset)]=float(row["oi_contracts"])
    if (len(seen)!=72264 or np.any(oi[np.isfinite(oi)]<=0) or
        np.count_nonzero(np.isnan(oi))!=3048*24-72264):
        raise ValueError("IC_OI_MISSING_MASK_OR_VALUES")
    return oi,manifest["hourly_csv_sha256"]

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("IC_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.75).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.75)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("IC_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote,oi):
    o,h,l,c,r,e,q,v=[np.asarray(x,dtype=float) for x in
                     (opening,high,low,close,rate,event,quote,oi)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,v)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(v[np.isfinite(v)]<=0)):
        raise ValueError("IC_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n72=net(t,72);n168=net(t,168)
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        growth=np.exp(np.clip(n168,-2.,2.))/semi
        signals[t,0]=growth/growth.sum()
        stress=bool(n72[0]<-.05 or np.median(n72)<-.035)
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n168>0)>=3 else "TRANSITION"
        regimes[t]=regime
        valid=bool(np.isfinite(v[t-168:t+1]).all())
        validity[t,1:]=valid
        if valid:
            oig72=np.log(v[t]/v[t-72])
            oig168=np.log(v[t]/v[t-168])
            candidate=(oig72>0)&(n72>0)
            if np.any(candidate):
                ix=int(np.argmax(np.where(candidate,oig72*n72,-np.inf)))
                signals[t,1,ix]=1.
            crowd=oig168-.5*n168
            rank=np.argsort(crowd,kind="stable")
            signals[t,2,int(rank[0])]=.5
            signals[t,2,int(rank[-1])]=-.5
            if stress:
                signals[t,3,0]=-1. if oig72[0]>0 else 1.
            elif np.any(candidate):
                ix=int(np.argmax(np.where(candidate,oig72*n72,-np.inf)))
                signals[t,3,ix]=1.
        risk=np.maximum(np.abs(signals[t])@semi,.002)
        risk=np.where(np.abs(signals[t]).sum(axis=1)>0,risk,.02)
        budgets[t]=capped_simplex(PRIOR[regime]/risk)
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or np.any(budgets[t]<.05-1e-12) or np.any(budgets[t]>.75+1e-12)
            or not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12))
            or not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("IC_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    v=1e5*np.exp(t[:,None]*np.array([[.00001,.00002,.00003,.00004]])+
                 .1*np.sin(t[:,None]/79.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,v)
    c2,o2,h2,l2,q2,r2,v2=[x.copy() for x in (c,o,h,l,q,r,v)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.;v2[3200:]*=2.
    b=bundle(o2,h2,l2,c2,r2,e,q2,v2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IC_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IC_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IC_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IC_CORE_GROSS_CONSERVATION")
    return True

if __name__=="__main__":
    assert static_check()
    print("IC_OI_CAUSAL_SOURCE_PASS")
