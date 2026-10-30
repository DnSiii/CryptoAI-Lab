#!/usr/bin/env python3
"""AM multiplicative virtual-expert wealth allocator, causal and cost-aware."""
from __future__ import annotations
from collections import deque
import numpy as np

HISTORY=504
EPOCH=168
PRIORS={
    "BULL":np.array([.60,.20,.15,.05]),
    "BEAR":np.array([.50,.10,.25,.15]),
    "CHOP":np.array([.35,.15,.45,.05]),
    "STRESS":np.array([.25,.05,.20,.50]),
}
class AMAllocator:
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
            raise ValueError("AM_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AM_FUNDING_EVENT")
        self.history.append(self.inventory@(a-b*e)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AM_DECISION_INPUT")
        if t%EPOCH!=0 and regime==self.last_state:
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        scale=1.
        if len(self.history)==HISTORY:
            h=np.asarray(self.history)
            logwealth=np.sum(h,axis=0)-.001*np.abs(s-self.inventory).sum(axis=1)
            # Causal exponential-wealth experts; no current/future trade PnL.
            logwealth-=logwealth.max()
            w*=np.exp(np.clip(logwealth,-30.,0.))
            w/=w.sum()
            p=h@w
            edge=float(p.mean())
            var=max(float(p.var()),1e-5)
            scale=max(0.,1.+.35*edge/var)
        desired=scale*(w@s)
        if not np.isfinite(desired).all():
            raise ValueError("AM_NONFINITE_TARGET")
        self.costs=.001*np.abs(s-self.inventory).sum(axis=1)
        self.inventory=s.copy()
        self.target=desired.copy()
        self.last_state=regime
        self.epochs+=1
        return desired.copy(),True

if __name__=="__main__":
    a=AMAllocator()
    for t in range(600):
        a.observe(np.array([.0001,.0002,.0003,.0004]),np.zeros(4),np.zeros(4))
        x,_=a.decide(np.eye(4),"BULL",t)
        assert np.isfinite(x).all()
    print("AM_CAUSAL_ALLOCATOR_PASS")
