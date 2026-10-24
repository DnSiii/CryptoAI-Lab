#!/usr/bin/env python3
"""V98 AT causal daily/entry-exit allocator, fixed median confidence rule."""
from __future__ import annotations
from collections import deque
import numpy as np
FIRST=2160
HISTORY=168
EPOCH=24
FRICTION=.0015
PRIORS={
    "RISK_ON":np.array([.60,.20,.10,.10]),
    "DEFENSIVE":np.array([.50,.05,.10,.35]),
    "NEUTRAL":np.array([.60,.10,.20,.10]),
}
class ATAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.inventory=np.zeros((4,4))
        self.costs=np.zeros(4)
        self.target=np.zeros(4)
        self.events=np.zeros((2,4))
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AT_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AT_FUNDING_EVENT")
        raw=self.inventory@(a-b*e)
        if np.any(raw<=-1.):
            raise ValueError("AT_SHADOW_INSOLVENCY")
        self.history.append(np.log1p(raw)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AT_DECISION")
        self.costs=FRICTION*np.abs(s-self.inventory).sum(axis=1)
        self.inventory=s.copy()
        events=s[[1,3]]
        changed=not np.array_equal(events,self.events)
        self.events=events.copy()
        if t<FIRST or ((t-FIRST)%EPOCH and not changed):
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        if len(self.history)==HISTORY:
            h=np.asarray(self.history)
            confidence=np.clip(1.+20.*np.median(h,axis=0),.5,1.5)
            w*=confidence
            w/=w.sum()
        active=np.abs(s).sum(axis=1)>0.
        w[1:]=np.where(active[1:],w[1:],0.)
        w[0]=1.-float(w[1:].sum())
        if w[0]<.45:
            w[1:]*=.55/max(float(w[1:].sum()),1e-12)
            w[0]=.45
        target=w@s
        if not np.isfinite(target).all():
            raise ValueError("AT_TARGET")
        self.target=target.copy()
        self.epochs+=1
        return target.copy(),True

def static_check():
    a=ATAllocator()
    for t in range(2600):
        a.observe(np.array([.0002,.0001,.0003,.0004]),
                  np.zeros(4),np.zeros(4))
        x,_=a.decide(np.eye(4),"RISK_ON",t)
        assert np.isfinite(x).all()
        assert np.abs(x).sum()<=1.+1e-12
    b=ATAllocator()
    b.decide(np.zeros((4,4)),"NEUTRAL",2160)
    x,changed=b.decide(np.eye(4),"NEUTRAL",2161)
    assert changed
    _,changed=b.decide(np.eye(4),"NEUTRAL",2162)
    assert not changed
    return True
if __name__=="__main__":
    assert static_check()
    print("AT_ALLOCATOR_CAUSAL_PASS")
