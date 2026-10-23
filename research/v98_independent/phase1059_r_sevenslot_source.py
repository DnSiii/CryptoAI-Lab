#!/usr/bin/env python3
"""V98 Independent R preregistered seven-slot, source-only signed targets.

No historical PnL, external benchmark, 2025+, or future holdout access.
Signals at completed bar t can only be executed at t+1 or later.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ASSETS = ('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS = ('R_core_only','R_full','R_minus_opportunity','R_minus_relative_value','R_minus_recovery')
SLEEVES = ('growth','opportunity','relative_value','recovery')
EXCLUDED = {'R_core_only':('opportunity','relative_value','recovery'),
            'R_full':(), 'R_minus_opportunity':('opportunity',),
            'R_minus_relative_value':('relative_value',),
            'R_minus_recovery':('recovery',)}
BUDGET = np.array([[.25,.10,.50,.15],[.60,.20,.15,.05],[.75,.20,.03,.02]])
GROSS = np.array([.40,.85,1.20])
ASSET_CAP, NET_CAP, GROSS_CAP = .45,.70,1.20


def validate(op,hi,lo,cl,quote,funding):
    f=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in f):
        raise ValueError('R_CLEAN4_COLUMNS_REQUIRED')
    idx=cl.index
    if not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1600 or idx[0].year<2022 or idx[-1].year>2024 or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or any(not x.index.equals(idx) for x in f):
        raise ValueError('R_TRAINING_CHRONOLOGY_ONLY')
    if any(not np.isfinite(x.to_numpy(float)).all() for x in f):
        raise ValueError('R_NONFINITE_SOURCE')
    if (op<=0).any().any() or (lo<=0).any().any() or (quote<0).any().any() or (hi<np.maximum(op,cl)).any().any() or (lo>np.minimum(op,cl)).any().any():
        raise ValueError('R_INVALID_OHLC_VOLUME')


def unit(a):
    x=np.nan_to_num(np.asarray(a,float),nan=0.,posinf=0.,neginf=0.)
    den=np.abs(x).sum(axis=1,keepdims=True)
    return np.divide(x,den,out=np.zeros_like(x),where=den>1e-12)


def persist(raw,trigger,hours=12):
    x=np.zeros_like(raw,dtype=float);last=np.zeros(raw.shape[1]);ttl=np.zeros(raw.shape[1],int)
    for t in range(len(raw)):
        event=np.asarray(trigger[t],bool)&np.isfinite(raw[t])&(raw[t]!=0)
        last[event]=raw[t,event];ttl[event]=hours
        x[t]=np.where(ttl>0,last,0.)
        ttl=np.maximum(ttl-1,0)
    return x


def regime(market):
    ret48=market.rolling(48,min_periods=48).sum()
    down=market.clip(upper=0).pow(2).rolling(168,min_periods=168).mean()
    up=market.clip(lower=0).pow(2).rolling(168,min_periods=168).mean()
    defensive=(ret48<0)&(down>1.3*up)
    expansion=(ret48>0)&(up>1.1*down)
    desired=np.where(defensive,0,np.where(expansion,2,1))
    out=np.ones(len(desired),np.int8);state=1;last=1;streak=0
    for t,v in enumerate(desired):
        v=int(v);streak=streak+1 if v==last else 1;last=v
        if streak>=24:state=v
        out[t]=state
    return out


def governor(w,states):
    out=np.zeros_like(w)
    for t,row in enumerate(w):
        v=np.nan_to_num(row,nan=0.,posinf=0.,neginf=0.)
        gross=float(np.abs(v).sum());asset=float(np.abs(v).max());net=float(abs(v.sum()))
        if gross<=1e-12:continue
        scale=min(1.,(GROSS[int(states[t])]-1e-7)/gross,
                  (GROSS_CAP-1e-7)/gross,
                  (ASSET_CAP-1e-7)/max(asset,1e-12),
                  (NET_CAP-1e-7)/max(net,1e-12))
        # Toward-zero canonical serialization; safety margin covers signed cancellation.
        v=np.trunc(v*scale*1e8)/1e8
        if not np.isfinite(v).all() or np.abs(v).max()>ASSET_CAP+1e-10 or np.abs(v).sum()>min(GROSS_CAP,GROSS[int(states[t])])+1e-10 or abs(v.sum())>NET_CAP+1e-10:
            raise ValueError('R_POST_SERIALIZATION_GOVERNOR_FAILURE')
        out[t]=v
    return out


def compose_r(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx)
    log=np.log(cl);r=log.diff();market=r.mean(axis=1)
    m48=log-log.shift(48);m336=log-log.shift(336)
    vol=r.rolling(168,min_periods=168).std(ddof=0)
    # Long-biased multi-horizon trend; no forced short core.
    growth=(m48.clip(lower=0)*m336.clip(lower=0)).pow(.5).div(vol.where(vol>1e-12)).to_numpy(float)
    # Prior channel only; current completed bar supplies breakout and volume evidence.
    upper=hi.shift(1).rolling(24,min_periods=24).max()
    lower=lo.shift(1).rolling(24,min_periods=24).min()
    q6=quote.rolling(6,min_periods=6).median()
    q168=quote.shift(6).rolling(168,min_periods=168).median()
    active=(q6/q168.where(q168>0)>=1.5)
    breakout=np.where((cl>upper)&active,1.,np.where((cl<lower)&active,-1.,0.))
    opp=persist(breakout,np.abs(breakout)>0,12)
    # Native funding event series; cross-sectional carry only, never price-derived.
    f72=funding.rolling(72,min_periods=72).sum()
    carry=-(f72.sub(f72.mean(axis=1),axis=0)).to_numpy(float)
    # Breadth-confirmed rebound after a downshock; not a generic shock fade.
    m6=market.rolling(6,min_periods=6).sum()
    sigma6=m6.shift(1).rolling(336,min_periods=336).std(ddof=0)
    breadth=(r>0).sum(axis=1)>=3
    location=((cl-lo)/(hi-lo).where(hi>lo)-.5).mean(axis=1)
    recovery=((m6<-2*sigma6)&(sigma6>0)&breadth&(location>0)).to_numpy(bool)
    rec=persist(np.ones((n,4)),np.repeat(recovery[:,None],4,axis=1),12)
    sleeves={'growth':unit(growth),'opportunity':unit(opp),
             'relative_value':unit(carry),'recovery':unit(rec)}
    states=regime(market)
    result={}
    for path in PATHS:
        raw=np.zeros((n,4))
        for k,s in sleeves.items():
            if k not in EXCLUDED[path]:raw+=BUDGET[states,SLEEVES.index(k),None]*s
        # No renormalization when sleeves are inactive: retain unused cash.
        result[path]=pd.DataFrame(governor(raw,states),index=idx,columns=ASSETS)
    if diagnostics:
        return result,{'regime_hours':{str(k):int((states==k).sum()) for k in range(3)},
                       'active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
                       'historical_pnl_computed':False,'validation_2025_read':False,
                       'external_benchmarks_used':False}
    return result
