#!/usr/bin/env python3
"""V98 AH1235 signed 120h funding-adjusted residual growth source; no PnL."""
from __future__ import annotations
import numpy as np

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')


def ah_growth_source(close,native_rate,funding_event):
    c,r,e=map(lambda x:np.asarray(x,dtype=float),
              (close,native_rate,funding_event))
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or not np.isfinite(c).all() or np.any(c<=0) or
        not np.isfinite(r).all() or not np.isfinite(e).all() or
        not np.isin(e,(0.,1.)).all()):
        raise ValueError('AH1235_SOURCE_GEOMETRY')
    n=len(c)
    out=np.zeros((n,4),dtype=float)
    logc=np.log(c)
    lr=np.diff(logc,axis=0)
    excess=lr-lr.mean(axis=1,keepdims=True)
    for t in range(120,n):
        window=excess[t-120:t]
        native=np.sum(r[t-119:t+1]*e[t-119:t+1],axis=0)
        residual=np.sum(window,axis=0)-native
        confirm=np.sum(excess[t-24:t],axis=0)
        scale=max(float(np.median(np.abs(residual))),1e-4)
        score=np.clip(residual/scale,-3.,3.)
        score=np.where(residual*confirm>0,score,0.)
        market48=float(np.mean(logc[t]-logc[t-48]))
        if market48>.005:score+=.15
        elif market48<-.005:score-=.15
        gross=float(np.abs(score).sum())
        if gross>1e-12:out[t]=score/gross
    return out
