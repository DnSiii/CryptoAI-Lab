#!/usr/bin/env python3
"""V98 AR stateful causal multiplicative net log-wealth portfolio allocator."""
from __future__ import annotations
from collections import deque
import numpy as np

FIRST=2160
EPOCH=336
HISTORY=720
FRICTION=.0015
PRIORS={
    "RISK_ON":np.array([.75,.10,.10,.05]),
    "DRAWDOWN":np.array([.70,.05,.10,.15]),
    "SIDEWAYS":np.array([.70,.10,.15,.05]),
    "PANIC":np.array([.60,.05,.05,.30]),
}
class ARAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.inventory=np.zeros((4,4))
        self.costs=np.zeros(4)
        self.target=np.zeros(4)
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AR_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AR_EVENT")
        raw=self.inventory@(a-b*e)
        if np.any(raw<=-1.):
            raise ValueError("AR_SHADOW_INSOLVENCY")
        net=np.log1p(raw)-self.costs
        self.history.append(net)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AR_DECISION")
        self.costs=FRICTION*np.abs(s-self.inventory).sum(axis=1)
        self.inventory=s.copy()
        if t<FIRST or (t-FIRST)%EPOCH:
            return self.target.copy(),False
        prior=PRIORS[regime].copy()
        if len(self.history)==HISTORY:
            hist=np.asarray(self.history)
            scores=3.*hist.sum(axis=0)
            scores-=scores.max()
            prior*=np.exp(np.clip(scores,-30.,0.))
            prior/=prior.sum()
        active=np.abs(s).sum(axis=1)>0.
        active[0]=True
        prior[1:]=np.where(active[1:],prior[1:],0.)
        prior[0]=1.-float(prior[1:].sum())
        if prior[0]<.5:
            prior[1:]*=.5/max(float(prior[1:].sum()),1e-12)
            prior[0]=.5
        target=prior@s
        if not np.isfinite(target).all():
            raise ValueError("AR_TARGET")
        self.target=target.copy()
        self.epochs+=1
        return target.copy(),True

def static_check():
    a=ARAllocator()
    for t in range(3500):
        a.observe(np.array([.0003,.0002,.0001,.0004]),
                  np.zeros(4),np.zeros(4))
        target,changed=a.decide(np.eye(4),"PANIC" if t%2 else "RISK_ON",t)
        assert np.isfinite(target).all()
        assert np.abs(target).sum()<=1.+1e-12
    assert a.epochs==4,a.epochs
    return True

if __name__=="__main__":
    assert static_check()
    print("AR_CAUSAL_MULTIPLICATIVE_ALLOCATOR_PASS")
