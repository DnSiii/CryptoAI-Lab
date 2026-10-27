#!/usr/bin/env python3
"""IE independent native taker-flow absorption and price-response seven-slot source.
Authenticated Binance Vision 5m->hourly source; completed t to next open t+1.
"""
from __future__ import annotations
import csv,datetime as dt,hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
WARMUP=744
CLOCK=336
HOURS=18288
GROSS={"BULL":.76,"MIXED":.72,"BEAR":.60}
PRIOR={"BULL":np.array([.56,.20,.12,.12]),
       "MIXED":np.array([.62,.16,.12,.10]),
       "BEAR":np.array([.64,.12,.10,.14])}

def load_taker():
    p=HERE/"v98_oi_full_history_v2_verified_hourly_20261027.csv"
    m=HERE/"v98_oi_full_history_source_v2_report_20261027.json"
    if not p.is_file() or not m.is_file():
        raise ValueError("IE_MISSING_AUTHENTICATED_NATIVE_TAKER_ARTIFACT")
    manifest=json.loads(m.read_text())
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    if (manifest.get("files_expected")!=3048 or manifest.get("files_verified_complete")!=3011
        or manifest.get("files_quarantined")!=37 or manifest.get("verified_hourly_rows")!=72264
        or manifest.get("holdout_2025_read") is not False or sha!=manifest["hourly_csv_sha256"]):
        raise ValueError("IE_NATIVE_TAKER_SOURCE_SHA_OR_MASK")
    taker=np.full((HOURS,4),np.nan,dtype=float)
    seen=set();zeros=0
    with p.open(newline="") as f:
        for row in csv.DictReader(f):
            stamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            hours=(stamp-START).total_seconds()/3600.
            if hours!=int(hours) or not 0<=int(hours)<HOURS:
                raise ValueError("IE_TAKER_TIMESTAMP_OUTSIDE_TRAINING")
            ix=int(hours);asset=row["asset"]
            if asset not in ASSETS or (ix,asset) in seen:
                raise ValueError("IE_TAKER_DUPLICATE_OR_WRONG_ASSET")
            seen.add((ix,asset))
            val=float(row["taker_ratio"])
            if not np.isfinite(val) or val<0:
                raise ValueError("IE_TAKER_NONFINITE_OR_NEGATIVE")
            if val==0:
                zeros+=1
            else:
                taker[ix,ASSETS.index(asset)]=val
    if (len(seen)!=72264 or zeros!=1 or np.count_nonzero(np.isfinite(taker))!=72263
        or np.any(taker[np.isfinite(taker)]<=0)):
        raise ValueError("IE_TAKER_GAP_OR_ZERO_MASK_MISMATCH")
    return taker,sha

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("IE_ALLOCATOR_INVALID")
    x=x/x.sum();lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.75).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.75)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("IE_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote,taker):
    o,h,l,c,r,e,q,v=[np.asarray(x,dtype=float) for x in
                     (opening,high,low,close,rate,event,quote,taker)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,v)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(v[np.isfinite(v)]<=0)):
        raise ValueError("IE_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n24=net(t,24);n72=net(t,72);n336=net(t,336)
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        core=np.exp(np.clip(n336/(np.sqrt(336.)*semi),-2.,2.))
        signals[t,0]=core/core.sum()
        valid=bool(np.isfinite(v[t-168:t+1]).all())
        validity[t,1:]=valid
        regime="MIXED"
        if valid:
            log_ratio=np.clip(np.log(v[t-168:t+1]),-np.log(10.),np.log(10.))
            pressure24=log_ratio[-24:].mean(axis=0)
            pressure72=log_ratio[-72:].mean(axis=0)
            bull=bool(np.count_nonzero(pressure24>0)>=3 and np.median(n72)>0)
            bear=bool(np.count_nonzero(pressure24<0)>=3 and np.median(n72)<0)
            regime="BULL" if bull else "BEAR" if bear else "MIXED"
            # Buy-side aggression with weak realized price response: absorption.
            score=pressure24-4.*n24
            signals[t,1,int(np.argmax(score))]=1.
            # Cross-sectional price response per aggressive flow.
            response=pressure72-2.*n72
            rank=np.argsort(response,kind="stable")
            signals[t,2,int(rank[-1])]=.5
            signals[t,2,int(rank[0])]=-.5
            # Directional fragility only in broad selling + declining market.
            ix=int(np.argmin(pressure24)) if bear else int(np.argmax(pressure24))
            signals[t,3,ix]=-1. if bear else 1.
        regimes[t]=regime
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
            raise ValueError("IE_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    v=np.exp(.25*np.sin(t[:,None]/79.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,v)
    c2,o2,h2,l2,q2,r2,v2=[x.copy() for x in (c,o,h,l,q,r,v)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.;v2[3200:]*=2.
    b=bundle(o2,h2,l2,c2,r2,e,q2,v2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IE_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IE_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IE_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IE_CORE_GROSS_CONSERVATION")
    vgap=v.copy();vgap[700:711,2]=np.nan
    g=bundle(o,h,l,c,r,e,q,vgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IE_MISSING_TAKER_GAP_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IE_NATIVE_TAKER_CAUSAL_AND_GAP_QUARANTINE_PASS")
