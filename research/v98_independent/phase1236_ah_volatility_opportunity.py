#!/usr/bin/env python3
"""V98 AH1236 causal signed 12h volatility impulse / 24h range opportunity."""
from __future__ import annotations
import numpy as np

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
HOLD=12


def ah_opportunity_source(close,high,low):
    c,h,l=map(lambda x:np.asarray(x,dtype=float),(close,high,low))
    if (c.ndim!=2 or c.shape[1]!=4 or h.shape!=c.shape or l.shape!=c.shape
        or not np.isfinite(c).all() or not np.isfinite(h).all()
        or not np.isfinite(l).all() or np.any(l<=0) or
        np.any(l>c) or np.any(h<c) or np.any(h<l)):
        raise ValueError('AH1236_SOURCE_GEOMETRY')
    n=len(c)
    out=np.zeros((n,4),dtype=float)
    sign=np.zeros(4)
    ttl=np.zeros(4,dtype=int)
    lr=np.diff(np.log(c),axis=0)
    for t in range(120,n):
        rms12=np.sqrt(np.mean(lr[t-12:t]**2,axis=0))
        rms96=np.sqrt(np.mean(lr[t-96:t]**2,axis=0))
        impulse=rms12>1.4*np.maximum(rms96,1e-8)
        up=c[t]>np.max(h[t-24:t],axis=0)
        down=c[t]<np.min(l[t-24:t],axis=0)
        events=np.where(impulse & up,1.,np.where(impulse & down,-1.,0.))
        fresh=events!=0
        sign[fresh]=events[fresh]
        ttl[fresh]=HOLD
        active=np.where(ttl>0,sign,0.)
        gross=float(np.abs(active).sum())
        if gross>0:out[t]=active/gross
        ttl=np.maximum(ttl-1,0)
    return out
