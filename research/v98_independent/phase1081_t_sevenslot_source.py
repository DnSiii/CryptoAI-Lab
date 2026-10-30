#!/usr/bin/env python3
"""V98 Independent T preregistered seven-slot low-turnover source only.
Causal at close t; orders may execute no earlier than open t+1.
No historical PnL, 2025+, prior engine signals or external benchmarks.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('T_core_only','T_full','T_minus_opportunity','T_minus_relative_value','T_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'T_core_only':('opportunity','relative_value','stress'),'T_full':(),
         'T_minus_opportunity':('opportunity',),'T_minus_relative_value':('relative_value',),
         'T_minus_stress':('stress',)}
BUDGET=np.array([[.15,.05,.25,.55],[.55,.10,.25,.10],[.65,.15,.15,.05]])
GROSS_CAP=1.35;ASSET_CAP=.45;NET_CAP=.75

def validate(op,hi,lo,cl,quote,funding):
    frames=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in frames):
        raise ValueError('T_CLEAN4_REQUIRED')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1600 or
        idx[0].year<2022 or idx[-1].year>2024 or
        not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or
        any(not x.index.equals(idx) for x in frames)):
        raise ValueError('T_CHRONOLOGICAL_TRAINING_ONLY')
    if any(not np.isfinite(x.to_numpy(float)).all() for x in frames):
        raise ValueError('T_NONFINITE_SOURCE')
    if ((op<=0).any().any() or (lo<=0).any().any() or (quote<0).any().any() or
        (hi<np.maximum(op,cl)).any().any() or (lo>np.minimum(op,cl)).any().any()):
        raise ValueError('T_INVALID_OHLC')

def normalize(a):
    x=np.nan_to_num(np.asarray(a,dtype=float),nan=0.,posinf=0.,neginf=0.)
    d=np.abs(x).sum(axis=1,keepdims=True)
    return np.divide(x,d,out=np.zeros_like(x),where=d>1e-12)

def governor(raw):
    w=np.nan_to_num(np.asarray(raw,float),nan=0.,posinf=0.,neginf=0.)
    gross=np.abs(w).sum(axis=1);asset=np.abs(w).max(axis=1);net=np.abs(w.sum(axis=1))
    scale=np.minimum.reduce([np.ones(len(w)),
        (GROSS_CAP-2e-5)/np.maximum(gross,1e-12),
        (ASSET_CAP-2e-5)/np.maximum(asset,1e-12),
        (NET_CAP-2e-5)/np.maximum(net,1e-12)])
    out=np.round(w*scale[:,None],6)
    if (not np.isfinite(out).all() or np.abs(out).sum(axis=1).max()>GROSS_CAP+1e-10 or
        np.abs(out).max()>ASSET_CAP+1e-10 or np.abs(out.sum(axis=1)).max()>NET_CAP+1e-10):
        raise AssertionError('T_POST_SERIALIZATION_CAP_FAILURE')
    return out

def persistence(signal,confirm=72):
    x=np.asarray(signal,bool);out=np.zeros_like(x);count=np.zeros(x.shape[1],int)
    for t in range(len(x)):
        count=np.where(x[t],count+1,0)
        out[t]=count>=confirm
    return out

def event_latch(raw,events,hold=48,cooldown=96):
    raw=np.asarray(raw,float);events=np.asarray(events,bool)
    n,k=raw.shape;out=np.zeros((n,k));ttl=np.zeros(k,int);block=np.zeros(k,int);last=np.zeros(k)
    for t in range(n):
        fired=events[t] & (block==0) & (raw[t]!=0)
        last[fired]=raw[t,fired];ttl[fired]=hold;block[fired]=cooldown
        out[t]=np.where(ttl>0,last,0.)
        ttl=np.maximum(0,ttl-1);block=np.maximum(0,block-1)
    return out

def regime(market,vol):
    trend=market.rolling(720,min_periods=720).sum()
    prior=vol.shift(1).rolling(720,min_periods=720).median()
    defensive=(trend<0)&(vol>1.20*prior)
    expansion=(trend>0)&(vol<1.10*prior)
    desired=np.where(defensive,0,np.where(expansion,2,1))
    states=np.ones(len(desired),np.int8);last=1;streak=0;state=1
    for i,d in enumerate(desired):
        d=int(d);streak=streak+1 if d==last else 1;last=d
        if streak>=72:state=d
        states[i]=state
    return states

def compose_t(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx);log=np.log(cl);ret=log.diff().fillna(0)
    market=ret.mean(axis=1);mvol=market.rolling(168,min_periods=168).std(ddof=0)
    states=regime(market,mvol)
    long720=(log-log.shift(720))>0
    long168=(log-log.shift(168))>0
    valid=persistence((long720&long168).to_numpy(bool),72)
    vol336=ret.rolling(336,min_periods=336).std(ddof=0).to_numpy(float)
    growth=normalize(np.where(valid,1/np.maximum(vol336,1e-5),0.))
    prior_q=funding.shift(1).rolling(1440,min_periods=720).quantile(.10)
    funding72=funding.rolling(72,min_periods=72).mean()
    event=((funding72<prior_q)&((log-log.shift(48))>0)).to_numpy(bool)
    opportunity=normalize(event_latch(np.ones((n,4)),event,48,96))
    score=(log-log.shift(336))-40*funding72
    scores=score.to_numpy(float);rv=np.zeros((n,4))
    for t in range(336,n):
        row=scores[t]
        if not np.isfinite(row).all():continue
        top=int(np.argmax(row));bottom=int(np.argmin(row))
        if row[top]-row[bottom]>.05:
            rv[t,top]=.5;rv[t,bottom]=-.5
    m168=market.rolling(168,min_periods=168).sum()
    baseline=mvol.shift(1).rolling(720,min_periods=720).median()
    stressed=((m168<0)&(mvol>1.2*baseline)).fillna(False).to_numpy(bool)
    r168=ret.rolling(168,min_periods=168).std(ddof=0).to_numpy(float)
    m48=market.rolling(48,min_periods=48).sum().to_numpy(float)
    hedge=np.zeros((n,4))
    for t in range(720,n):
        if not stressed[t]:continue
        if m48[t]>0:hedge[t]=.25
        else:
            ranks=np.argsort(r168[t],kind='stable')[-2:]
            hedge[t,ranks]=-.5
    stress=np.zeros_like(hedge);active=np.zeros(4,int);last=np.zeros(4)
    for t in range(n):
        if t%24==0:
            for j in range(4):
                if active[j]==0 or np.sign(last[j])!=np.sign(hedge[t,j]):
                    last[j]=hedge[t,j];active[j]=72 if hedge[t,j]!=0 else 0
        stress[t]=np.where(active>0,last,0.)
        active=np.maximum(active-1,0)
    sleeves={'growth':growth,'opportunity':opportunity,'relative_value':rv,'stress':stress}
    funding_headroom=(1-np.minimum(.4,100*funding.abs().rolling(72,min_periods=1).mean().mean(axis=1))).to_numpy(float)
    result={}
    for name in PATHS:
        weights=np.zeros((n,4));last_target=np.zeros(4)
        for t in range(n):
            if idx[t].hour==0:
                raw=np.zeros(4)
                for j,sleeve in enumerate(SLEEVES):
                    if sleeve not in EXCLUDE[name] and np.abs(sleeves[sleeve][t]).sum()>1e-12:
                        raw+=BUDGET[states[t],j]*funding_headroom[t]*sleeves[sleeve][t]
                last_target=governor(raw[None,:])[0]
            weights[t]=last_target
        result[name]=pd.DataFrame(weights,index=idx,columns=ASSETS)
    if diagnostics:
        return result,{'regime_hours':{str(s):int((states==s).sum()) for s in range(3)},
                       'active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
                       'historical_pnl_computed':False,'validation_2025_read':False,
                       'holdout_accessed':False,'external_benchmarks_used':False}
    return result
