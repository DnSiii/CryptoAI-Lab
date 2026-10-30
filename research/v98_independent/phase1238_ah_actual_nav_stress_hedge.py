#!/usr/bin/env python3
"""V98 AH1238 actual-NAV funded short-factor hedge intent; causal t-1."""
from __future__ import annotations
from collections import deque
import numpy as np

HEDGE=np.full(4,-.25)
HOLD=24


class AHStressHedge:
    def __init__(self):
        self.nav=deque(maxlen=48)
        self.market=deque(maxlen=24)
        self.cooldown=0
        self.active_hours=0

    def step(self,actual_nav,market_log):
        if (not np.isfinite(actual_nav) or actual_nav<=0 or
            not np.isfinite(market_log)):
            raise ValueError('AH1238_NAV_OR_RETURN')
        self.nav.append(float(actual_nav))
        self.market.append(float(market_log))
        trigger=False
        if len(self.nav)==48 and len(self.market)==24:
            peak=max(self.nav)
            dd=1-float(actual_nav)/peak
            x=np.asarray(self.market,dtype=float)
            centered=x-x.mean()
            sigma=max(float(np.sqrt(np.mean(centered**2))),1e-4)
            skew=float(np.mean((centered/sigma)**3))
            trigger=bool(dd>.10 and (float(x.sum())<-.05 or skew<-.3))
        if trigger:self.cooldown=HOLD
        active=self.cooldown>0
        if active:self.active_hours+=1
        self.cooldown=max(0,self.cooldown-1)
        return HEDGE.copy() if active else np.zeros(4)
