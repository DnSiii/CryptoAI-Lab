#!/usr/bin/env python3
"""V98 AS causal portfolio marginal-gradient allocator with event clocks."""
from __future__ import annotations
from collections import deque
import numpy as np
FIRST=2160
EPOCH=168
HISTORY=720
FRICTION=.0015
PRIORS={
 "EXPANSION":np.array([.70,.15,.10,.05]),
 "CONTRACTION":np.array([.75,.05,.10,.10]),
 "RECOVERY":np.array([.60,.10,.05,.25]),
 "CHOP":np.array([.75,.10,.10,.05]),
}
class ASAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.inventory=np.zeros((4,4))
        self.prev_events=np.zeros((2,4))
        self.costs=np.zeros(4)
        self.target=np.zeros(4)
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AS_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AS_EVENT")
        raw=self.inventory@(a-b*e)
        if np.any(raw<=-1.):
            raise ValueError("AS_SHADOW_INSOLVENCY")
        self.history.append(np.log1p(raw)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AS_DECISION")
        self.costs=FRICTION*np.abs(s-self.inventory).sum(axis=1)
        self.inventory=s.copy()
        events=s[[1,3]]
        event_changed=not np.array_equal(events,self.prev_events)
        self.prev_events=events.copy()
        if t<FIRST or ((t-FIRST)%EPOCH and not event_changed):
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        if len(self.history)==HISTORY:
            h=np.asarray(self.history)
            differences=h[:,1:]-h[:,[0]]
            gradient=differences.mean(axis=0)-.5*differences.var(axis=0)
            w[1:]*=np.maximum(.2,1.+50.*gradient)
            w/=w.sum()
        active=np.abs(s).sum(axis=1)>0.
        w[1:]=np.where(active[1:],w[1:],0.)
        w[0]=1.-float(w[1:].sum())
        if w[0]<.5:
            w[1:]*=.5/max(float(w[1:].sum()),1e-12)
            w[0]=.5
        target=w@s
        if not np.isfinite(target).all():
            raise ValueError("AS_TARGET")
        self.target=target.copy()
        self.epochs+=1
        return target.copy(),True

def static_check():
    a=ASAllocator()
    for t in range(3500):
        a.observe(np.array([.0003,.0002,.0001,.0004]),
                  np.zeros(4),np.zeros(4))
        target,changed=a.decide(np.eye(4),"RECOVERY" if t%2 else "EXPANSION",t)
        assert np.isfinite(target).all()
        assert np.abs(target).sum()<=1.+1e-12
    assert a.epochs==8,a.epochs
    # A 72h event must change next-open targets even between weekly epochs.
    b=ASAllocator()
    b.decide(np.zeros((4,4)),"CHOP",2160)
    s=np.eye(4)
    _,changed=b.decide(s,"CHOP",2161)
    assert changed
    _,changed=b.decide(s,"CHOP",2162)
    assert not changed
    s[3]=0.
    _,changed=b.decide(s,"CHOP",2163)
    assert changed
    return True
if __name__=="__main__":
    assert static_check()
    print("AS_PORTFOLIO_GRADIENT_EVENT_CAUSAL_PASS")
