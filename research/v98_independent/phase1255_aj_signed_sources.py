#!/usr/bin/env python3
"""V98 Independent AJ1255: distinct deterministic four signed sleeves and router."""
from __future__ import annotations
import numpy as np

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
STATES=('TREND','RANGE','CRISIS','REBOUND')

def valid_close(close):
    c=np.asarray(close,dtype=float)
    if c.ndim!=2 or c.shape[1]!=4 or not np.isfinite(c).all() or np.any(c<=0):
        raise ValueError('AJ1255_CLOSE')
    return c

def valid_native(c,rate,event):
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    if (r.shape!=c.shape or e.shape!=c.shape or
        not np.isfinite(r).all() or not np.isfinite(e).all() or
        not np.isin(e,(0.,1.)).all()):
        raise ValueError('AJ1255_NATIVE')
    return r,e

def growth_core(close):
    c=valid_close(close)
    lr=np.diff(np.log(c),axis=0)
    out=np.zeros_like(c)
    for t in range(336,len(c)):
        fast=lr[t-96:t].sum(axis=0)
        slow=lr[t-336:t].sum(axis=0)
        agreed=(np.sign(fast)==np.sign(slow)) & (fast!=0) & (slow!=0)
        vol=np.maximum(np.sqrt(np.mean(lr[t-168:t]**2,axis=0)),.001)
        raw=np.where(agreed,np.sign(fast)/vol,0.)
        gross=float(np.abs(raw).sum())
        if gross>0:out[t]=raw/gross
    return out

def opportunity(close,high,low):
    c=valid_close(close)
    h=np.asarray(high,dtype=float)
    l=np.asarray(low,dtype=float)
    if (h.shape!=c.shape or l.shape!=c.shape or
        not np.isfinite(h).all() or not np.isfinite(l).all() or
        np.any(l<=0) or np.any(l>c) or np.any(h<c)):
        raise ValueError('AJ1255_OHLC')
    lr=np.diff(np.log(c),axis=0)
    out=np.zeros_like(c)
    ttl=np.zeros(4,dtype=int)
    direction=np.zeros(4)
    for t in range(120,len(c)):
        rms12=np.sqrt(np.mean(lr[t-12:t]**2,axis=0))
        rms120=np.sqrt(np.mean(lr[t-120:t]**2,axis=0))
        expansion=rms12>1.25*np.maximum(rms120,1e-8)
        highbreak=c[t]>np.max(h[t-72:t],axis=0)
        lowbreak=c[t]<np.min(l[t-72:t],axis=0)
        events=np.where(expansion&highbreak,1.,
                        np.where(expansion&lowbreak,-1.,0.))
        fresh=events!=0.
        direction[fresh]=events[fresh]
        ttl[fresh]=12
        active=np.where(ttl>0,direction,0.)
        gross=float(np.abs(active).sum())
        if gross>0:out[t]=active/gross
        ttl=np.maximum(0,ttl-1)
    return out

def relative_value(close,rate,event):
    c=valid_close(close)
    r,e=valid_native(c,rate,event)
    logc=np.log(c)
    out=np.zeros_like(c)
    index=np.arange(4)
    for t in range(336,len(c)):
        r48=logc[t]-logc[t-48]
        r336=logc[t]-logc[t-336]
        funding=(r[t-47:t+1]*e[t-47:t+1]).sum(axis=0)
        residual=r48-(48./336.)*r336-funding
        rank=np.lexsort((index,residual))
        out[t,rank[:2]]=.25
        out[t,rank[2:]]=-.25
    return out

def stress_recovery(close):
    c=valid_close(close)
    lr=np.diff(np.log(c),axis=0)
    market=lr.mean(axis=1)
    out=np.zeros_like(c)
    stress_ttl=0
    recovery_ttl=0
    last_crisis=-10**9
    for t in range(96,len(c)):
        market24=float(market[t-24:t].sum())
        if market24<-.06:
            last_crisis=t
            stress_ttl=24
            recovery_ttl=0
        elif market24>.05 and t-last_crisis<=72:
            recovery_ttl=12
        if stress_ttl>0:
            out[t]=np.full(4,-.25)
            stress_ttl-=1
        elif recovery_ttl>0:
            out[t]=np.full(4,.25)
            recovery_ttl-=1
    return out

def regime_router(close):
    c=valid_close(close)
    lr=np.diff(np.log(c),axis=0)
    market=lr.mean(axis=1)
    state=np.full(len(c),'RANGE',dtype='<U10')
    last_crisis=-10**9
    for t in range(336,len(c)):
        r24=float(market[t-24:t].sum())
        r168=lr[t-168:t].sum(axis=0)
        avg168=float(r168.mean())
        breadth=int(np.count_nonzero(r168>0))
        if r24<-.06:
            state[t]='CRISIS'
            last_crisis=t
        elif r24>.05 and t-last_crisis<=72:
            state[t]='REBOUND'
        elif (avg168>.05 and breadth>=3) or (avg168<-.05 and breadth<=1):
            state[t]='TREND'
    return {'state':state}

def source_bundle(close,high,low,rate,event):
    c=valid_close(close)
    return (growth_core(c),opportunity(c,high,low),
            relative_value(c,rate,event),stress_recovery(c),
            regime_router(c))
