#!/usr/bin/env python3
"""V98 AQ causal paired counterfactual marginal wealth allocator.

Each virtual sleeve competes against the contemporaneous CORE, not cash.
"""
from __future__ import annotations
from collections import deque
import numpy as np
FIRST=2160
EPOCH=336
HISTORY=720
PRIORS={
 "RISK_ON":np.array([.70,.12,.08,.10]),
 "RISK_OFF":np.array([.75,.05,.05,.15]),
 "NEUTRAL":np.array([.75,.10,.10,.05]),
 "PANIC":np.array([.60,.05,.05,.30]),
}
class AQAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.core_history=deque(maxlen=HISTORY)
        self.prev_s=np.zeros((4,4))
        self.costs=np.zeros(3)
        self.target=np.zeros(4)
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AQ_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AQ_EVENT")
        net=a-b*e
        core=float(self.prev_s[0]@net)
        if core<=-1:
            raise ValueError("AQ_CORE_INSOLVENCY")
        margins=np.zeros(3)
        for j in range(1,4):
            alt=.90*self.prev_s[0]+.10*self.prev_s[j]
            value=float(alt@net)
            if value<=-1:
                raise ValueError("AQ_SHADOW_INSOLVENCY")
            margins[j-1]=np.log1p(value)-np.log1p(core)-self.costs[j-1]
        self.history.append(margins)
        self.core_history.append(core)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AQ_DECISION")
        old=self.prev_s
        for j in range(1,4):
            prev_alt=.90*old[0]+.10*old[j]
            new_alt=.90*s[0]+.10*s[j]
            self.costs[j-1]=.001*(np.abs(new_alt-prev_alt).sum()-
                                  np.abs(s[0]-old[0]).sum())
        self.prev_s=s.copy()
        if t<FIRST or (t-FIRST)%EPOCH:
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        active=np.abs(s).sum(axis=1)>0
        active[0]=True
        if t>=FIRST+HISTORY and len(self.history)==HISTORY:
            h=np.asarray(self.history)
            active[1:]&=(h[:360].sum(axis=0)>0)&(h[360:].sum(axis=0)>0)
        w[1:]=np.where(active[1:],w[1:],0.)
        w[0]=1.-float(w[1:].sum())
        if len(self.core_history)==HISTORY:
            h=np.asarray(self.core_history)
            edge=float(h.mean())
            variance=max(float(h.var()),1e-5)
            scale=1.+max(0.,.10*edge/variance)
        else:
            scale=1.
        desired=scale*(w@s)
        if not np.isfinite(desired).all():
            raise ValueError("AQ_TARGET")
        self.target=desired.copy()
        self.epochs+=1
        return desired.copy(),True

def static_check():
    a=AQAllocator()
    for t in range(3500):
        a.observe(np.array([.0003,.0002,.0001,.0004]),
                  np.zeros(4),np.zeros(4))
        x,changed=a.decide(np.eye(4),"PANIC" if t%2 else "RISK_ON",t)
        assert np.isfinite(x).all()
    assert a.epochs==4,a.epochs
    return True
if __name__=="__main__":
    assert static_check()
    print("AQ_PAIRED_MARGINAL_CAUSAL_PASS")
