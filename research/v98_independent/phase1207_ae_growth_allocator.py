#!/usr/bin/env python3
"""V98 AE causal fractional-Kelly shrinkage allocator, source-only."""
from __future__ import annotations
from collections import deque
import numpy as np

PRIOR = np.array([.65,.12,.10,.13],dtype=np.float64)
ROUTE = np.array([[.60,.60,1.10,1.50],
                  [1.,1.,1.,1.],
                  [1.30,1.25,.90,.60]],dtype=np.float64)
HISTORY = 336
VIRTUAL_FEE = .0012
KELLY_FRACTION = .5
SHRINKAGE = .0004
STRENGTH_MIN = .25
STRENGTH_MAX = 3.


def valid_sleeves(x):
    a=np.asarray(x,dtype=np.float64)
    if a.shape!=(4,4) or not np.isfinite(a).all():
        raise ValueError('AE1207_SLEEVE_SHAPE')
    if (np.abs(a[0]).sum()>.65+1e-9 or
            np.abs(a[1]).sum()>.12+1e-9 or
            np.abs(a[2]).sum()>.20+1e-9 or
            abs(a[2].sum())>1e-9 or
            np.any(a[3]>0) or
            np.abs(a[3]).sum()>.24+1e-9 or
            np.max(a[3])-np.min(a[3])>1e-9):
        raise ValueError('AE1207_SLEEVE_BUDGET')
    return a


class AEAllocator:
    def __init__(self):
        self.prev=np.zeros((4,4),dtype=np.float64)
        self.prev_turnover=np.zeros(4,dtype=np.float64)
        self.history=deque(maxlen=HISTORY)
        self.hours=0
        self.last_realized=np.zeros(4,dtype=np.float64)

    def step(self, completed_returns, funding_rate, funding_event,
             next_sleeves, completed_regime):
        ret=np.asarray(completed_returns,dtype=np.float64)
        rate=np.asarray(funding_rate,dtype=np.float64)
        event=np.asarray(funding_event,dtype=np.float64)
        sleeves=valid_sleeves(next_sleeves)
        regime=np.asarray(completed_regime,dtype=np.float64)
        if (ret.shape!=(4,) or rate.shape!=(4,) or event.shape!=(4,) or
                regime.shape!=(3,) or
                not all(np.isfinite(x).all() for x in (ret,rate,event,regime)) or
                np.any(ret<=-1) or np.any((event!=0)&(event!=1)) or
                np.any(rate[event==0]!=0) or
                np.any((regime!=0)&(regime!=1)) or regime.sum()!=1):
            raise ValueError('AE1207_COMPLETED_INPUT')
        # Mark prior t-1 virtual sleeve inventory with fully completed t returns.
        realized=self.prev@(ret-rate*event)-VIRTUAL_FEE*self.prev_turnover
        if not np.isfinite(realized).all() or np.any(1+realized<=0):
            raise ValueError('AE1207_VIRTUAL_INSOLVENCY')
        self.history.append(realized.copy())
        self.last_realized=realized.copy()
        strength=np.ones(4,dtype=np.float64)
        if len(self.history)==HISTORY:
            data=np.stack(self.history)
            mu=data.mean(axis=0)
            variance=data.var(axis=0)
            score=np.clip(KELLY_FRACTION*mu/(variance+SHRINKAGE),-1.,2.)
            strength=np.clip(1+score,STRENGTH_MIN,STRENGTH_MAX)
        factor=ROUTE[int(np.argmax(regime))]
        raw=PRIOR*strength*factor
        budget=raw/raw.sum()
        desired=budget@sleeves
        self.prev_turnover=np.abs(sleeves-self.prev).sum(axis=1)
        self.prev=sleeves.copy()
        self.hours+=1
        if not np.isfinite(desired).all() or np.abs(desired).sum()>.65+1e-9:
            raise ValueError('AE1207_DESIRED_EXPOSURE')
        return desired,budget.copy()

    def diagnostic(self):
        return {'phase':1207,'completed_hours':self.hours,
                'window_hours':len(self.history),
                'historical_system_pnl_computed':False,
                'validation_2025_read':False,
                'external_benchmarks_used':False}
