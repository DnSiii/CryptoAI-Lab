#!/usr/bin/env python3
"""V98 AF independent robust blockwise net-log-growth allocator, source-only."""
from __future__ import annotations
from collections import deque
import numpy as np

PRIOR=np.array([.70,.20,.10])
ROUTE=np.array([[.60,.50,.70],[1.,1.,1.],[1.30,1.20,1.]])
WINDOW=336
BLOCKS=4
BLOCK_SIZE=84
FEE=.0012
SCORE_MULTIPLIER=500.
UNCERTAINTY_PENALTY=.5
ROW_CAPS=np.array([.75,.20,.15])


def validated_sleeves(sleeves):
    a=np.asarray(sleeves,dtype=float)
    if (a.shape!=(3,4) or not np.isfinite(a).all() or
            np.any(a<0) or np.any(a.sum(axis=1)>ROW_CAPS+1e-9)):
        raise ValueError('AF1219_LONG_ONLY_SLEEVES')
    return a


class AFGrowthAllocator:
    def __init__(self):
        self.prev=np.zeros((3,4))
        self.prev_turnover=np.zeros(3)
        self.history=deque(maxlen=WINDOW)
        self.last_realized=np.zeros(3)
        self.completed_hours=0

    def step(self,completed_returns,funding_rate,funding_event,
             next_sleeves,regime,cash_reserve):
        ret=np.asarray(completed_returns,dtype=float)
        rate=np.asarray(funding_rate,dtype=float)
        event=np.asarray(funding_event,dtype=float)
        sleeves=validated_sleeves(next_sleeves)
        route=np.asarray(regime,dtype=float)
        if (ret.shape!=(4,) or rate.shape!=(4,) or event.shape!=(4,) or
                route.shape!=(3,) or
                not all(np.isfinite(x).all() for x in (ret,rate,event,route)) or
                np.any(ret<=-1) or np.any((event!=0)&(event!=1)) or
                np.any(rate[event==0]!=0) or
                np.any((route!=0)&(route!=1)) or route.sum()!=1 or
                cash_reserve not in (.10,.55)):
            raise ValueError('AF1219_COMPLETED_INPUT')
        realized=self.prev@(ret-rate*event)-FEE*self.prev_turnover
        if not np.isfinite(realized).all() or np.any(1+realized<=0):
            raise ValueError('AF1219_VIRTUAL_INSOLVENCY')
        self.last_realized=realized.copy()
        self.history.append(np.log1p(realized))
        multiplier=np.ones(3)
        if len(self.history)==WINDOW:
            blocks=np.stack(self.history).reshape(BLOCKS,BLOCK_SIZE,3)
            means=blocks.mean(axis=1)
            score=(np.median(means,axis=0)-
                   UNCERTAINTY_PENALTY*means.std(axis=0,ddof=0))
            multiplier=1+SCORE_MULTIPLIER*np.maximum(score,0)
        raw=PRIOR*multiplier*ROUTE[int(np.argmax(route))]
        budget=raw/raw.sum()
        desired=budget@sleeves
        cap=1-float(cash_reserve)
        if desired.sum()>cap:
            desired*=cap/desired.sum()
        self.prev_turnover=np.abs(sleeves-self.prev).sum(axis=1)
        self.prev=sleeves.copy()
        self.completed_hours+=1
        if (not np.isfinite(desired).all() or np.any(desired<0) or
                desired.sum()>cap+1e-9):
            raise ValueError('AF1219_CASH_COLLATERAL')
        return desired,budget.copy()

    def diagnostic(self):
        return {'phase':1219,'completed_hours':self.completed_hours,
                'window_hours':len(self.history),
                'historical_system_pnl_computed':False,
                'validation_2025_read':False,
                'external_benchmarks_used':False}
