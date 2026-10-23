#!/usr/bin/env python3
"""AN hard 720h inventory lock, causal expert wealth, no router-transition trades."""
from __future__ import annotations
from collections import deque
import numpy as np

HISTORY=720
FIRST=2160
EPOCH=720
PRIORS={
    "BULL":np.array([.80,.10,.05,.05]),
    "BEAR":np.array([.50,.10,.20,.20]),
    "CHOP":np.array([.65,.15,.15,.05]),
    "STRESS":np.array([.40,.05,.10,.45]),
}
class ANAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.inventory=np.zeros((4,4),dtype=float)
        self.costs=np.zeros(4,dtype=float)
        self.target=np.zeros(4,dtype=float)
        self.last_state="CHOP"
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AN_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AN_FUNDING_EVENT")
        self.history.append(self.inventory@(a-b*e)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AN_DECISION_INPUT")
        # HARD trade budget: no alpha reallocation on regime transitions.
        if t<FIRST or (t-FIRST)%EPOCH!=0:
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        scale=1.
        if len(self.history)==HISTORY:
            h=np.asarray(self.history)
            evidence=h.sum(axis=0)-.001*np.abs(s-self.inventory).sum(axis=1)
            evidence-=evidence.max()
            w*=np.exp(np.clip(evidence,-30.,0.))
            w/=w.sum()
            portfolio=h@w
            edge=float(portfolio.mean())
            var=max(float(portfolio.var()),1e-5)
            scale=max(0.,1.+.50*edge/var)
        desired=scale*(w@s)
        if not np.isfinite(desired).all():
            raise ValueError("AN_NONFINITE_TARGET")
        self.costs=.001*np.abs(s-self.inventory).sum(axis=1)
        self.inventory=s.copy()
        self.target=desired.copy()
        self.last_state=regime
        self.epochs+=1
        return desired.copy(),True

if __name__=="__main__":
    a=ANAllocator()
    count=0
    for t in range(4000):
        a.observe(np.array([.0001,.0002,.0003,.0004]),np.zeros(4),np.zeros(4))
        x,changed=a.decide(np.eye(4),"BULL" if t%3 else "STRESS",t)
        count+=changed
        assert np.isfinite(x).all()
    assert count==3,count
    print("AN_HARD_BUDGET_EPOCHS",count,"PASS")
