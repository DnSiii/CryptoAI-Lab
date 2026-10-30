#!/usr/bin/env python3
"""AL causal online sleeve allocator; exact AK safety/settlement remains infrastructure."""
from __future__ import annotations
from collections import deque
import numpy as np

HISTORY=336
EPOCH=72
PRIORS={
    "BULL":np.array([.65,.20,.10,.05]),
    "BEAR":np.array([.15,.10,.25,.50]),
    "CHOP":np.array([.40,.25,.25,.10]),
    "STRESS":np.array([.10,.05,.05,.80]),
}
class ALAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.inventory=np.zeros((4,4),dtype=np.float64)
        self.costs=np.zeros(4,dtype=np.float64)
        self.target=np.zeros(4,dtype=np.float64)
        self.last_state="CHOP"
        self.epochs=0
    def observe(self, lr, funding, event):
        a,b,e=(np.asarray(x,dtype=np.float64) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AL_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AL_FUNDING_EVENT")
        self.history.append(self.inventory@(a-b*e)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=np.float64)
        if s.shape!=(4,4) or not np.isfinite(s).all():
            raise ValueError("AL_SLEEVE_MATRIX")
        if regime not in PRIORS:
            raise ValueError("AL_ROUTER")
        if t%EPOCH!=0 and regime==self.last_state:
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        scale=1.
        if len(self.history)==HISTORY:
            h=np.asarray(self.history)
            # Historical completed-close virtual sleeve evidence, cost-aware.
            score=1.5*(h.sum(axis=0)-.001*np.abs(s-self.inventory).sum(axis=1))
            score-=score.max()
            w*=np.exp(np.clip(score,-20.,0.))
            w/=w.sum()
            portfolio=h@w
            edge=float(portfolio.mean())
            variance=max(float(portfolio.var()),1e-5)
            scale=max(0.,1.+.25*edge/variance)
        desired=scale*(w@s)
        if not np.isfinite(desired).all():
            raise ValueError("AL_NONFINITE_TARGET")
        self.costs=.001*np.abs(s-self.inventory).sum(axis=1)
        self.inventory=s.copy()
        self.target=desired.copy()
        self.last_state=regime
        self.epochs+=1
        return desired.copy(),True

if __name__=="__main__":
    a=ALAllocator()
    s=np.eye(4)
    for t in range(400):
        a.observe(np.array([.0001,.0002,.0003,.0004]),np.zeros(4),np.zeros(4))
        x,rebal=a.decide(s,"BULL",t)
        assert np.isfinite(x).all()
    print("AL_ALLOCATOR_CAUSAL_SMOKE_PASS")
