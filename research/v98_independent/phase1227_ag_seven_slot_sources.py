#!/usr/bin/env python3
"""V98 Independent AG causal seven-slot sources and actual-NAV growth allocation."""
from __future__ import annotations
from collections import deque
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
START='2022-12-01 00:00:00+00:00'
PATHS=('AG_core_only','AG_full','AG_minus_opportunity',
       'AG_minus_relative_value','AG_minus_stress')
BASE_CASH=.10


def normalized(x):
    x=np.maximum(np.asarray(x,dtype=float),0.)
    s=float(x.sum())
    return x/s if s>1e-12 else np.zeros(4)


def causal_sources(close, quote):
    """Signals computed at completed close t; only executable from t+1 open."""
    c=np.asarray(close,dtype=float)
    q=np.asarray(quote,dtype=float)
    if c.ndim!=2 or c.shape[1]!=4 or q.shape!=c.shape or np.any(c<=0):
        raise ValueError('AG1227_SOURCE_SHAPE')
    n=len(c)
    growth=np.zeros((n,4))
    opportunity=np.zeros((n,4))
    rv=np.zeros((n,4))
    router=np.zeros(n)
    logc=np.log(c)
    lr=np.diff(logc,axis=0)
    for t in range(169,n):
        drift=logc[t]-logc[t-168]
        last=lr[t-72:t]
        downside=np.sqrt(np.mean(np.minimum(last,0.)**2,axis=0))
        growth[t]=normalized(np.maximum(drift,0.)/np.maximum(downside,.003))
        prior_high=np.max(c[t-72:t],axis=0)
        volume_base=np.median(q[t-24:t],axis=0)
        breakout=np.maximum(c[t]/prior_high-1.,0.)
        volume_impulse=np.maximum(q[t]/np.maximum(volume_base,1.)-1.25,0.)
        opportunity[t]=normalized(breakout*volume_impulse)
        ret48=logc[t]-logc[t-48]
        rv[t]=normalized(np.maximum(ret48-np.median(ret48),0.))
        breadth=np.mean(logc[t]-logc[t-24]>0)
        market=last.mean(axis=1)
        up=np.mean(np.maximum(market,0.)**2)
        down=np.mean(np.minimum(market,0.)**2)
        hazard=down/(down+up+1e-12)
        router[t]=float(np.clip(.55+.65*breadth-.35*hazard,.25,1.))
    return growth,opportunity,rv,router


class AGStress:
    def __init__(self):
        self.recent=deque(maxlen=48)
        self.cooldown=0
        self.active_hours=0

    def step(self,actual_nav,market_log):
        if not np.isfinite(actual_nav) or actual_nav<=0:
            raise ValueError('AG1227_NAV')
        self.recent.append(float(actual_nav))
        peak=max(self.recent)
        dd=1-float(actual_nav)/peak
        if dd>.10 or market_log<-.08:
            self.cooldown=24
        else:
            self.cooldown=max(0,self.cooldown-1)
        cash=.45 if self.cooldown else BASE_CASH
        self.active_hours+=int(cash>BASE_CASH)
        return cash


class AGAllocator:
    def __init__(self):
        self.score=np.zeros(3)
        self.previous=np.zeros((3,4))
        self.initialized=False
        self.active=np.zeros(3,dtype=int)

    def step(self,realized_asset_log,g,op,rv,router,cash_reserve,path):
        if path not in PATHS:
            raise ValueError('AG1227_PATH')
        realized=np.asarray(realized_asset_log,dtype=float)
        if realized.shape!=(4,) or not np.all(np.isfinite(realized)):
            raise ValueError('AG1227_RETURN')
        if self.initialized:
            # Causal prior paper sleeves; precommitted turnover/cost shrinkage.
            earned=self.previous@realized
            turnover=np.abs(np.vstack((g,op,rv))-self.previous).sum(axis=1)
            self.score=.988*self.score+.012*(earned-.001*turnover)
        sleeves=np.vstack((g,op,rv)).copy()
        if path=='AG_core_only':
            sleeves[1:]=0.
            cash_reserve=BASE_CASH
        if path=='AG_minus_opportunity':sleeves[1]=0.
        if path=='AG_minus_relative_value':sleeves[2]=0.
        if path=='AG_minus_stress':cash_reserve=BASE_CASH
        self.active+=(np.any(sleeves>0,axis=1)).astype(int)
        strength=np.exp(np.clip(20*.5*self.score,-5,5))
        strength*=np.array([.60,.22,.18])
        strength*=np.any(sleeves>0,axis=1)
        if strength.sum()<=0:
            mu=np.zeros(4)
        else:
            mix=(strength/strength.sum())@sleeves
            # Positive forecast only for causal active sleeves. A negative
            # baseline avoids buying assets without directional support.
            mu=.06*mix*float(router)*max(0.,1.-cash_reserve)-.002
        self.previous=np.vstack((g,op,rv)).copy()
        self.initialized=True
        return mu
