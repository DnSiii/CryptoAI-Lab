#!/usr/bin/env python3
"""V98 AP fixed structural beta with causal online conditional overlay budgets."""
from __future__ import annotations
from collections import deque
import numpy as np
FIRST=2160
EPOCH=336
HISTORY=720
PRIORS={
 "RISK_ON":np.array([.70,.15,.10,.05]),
 "RISK_OFF":np.array([.75,.05,.10,.10]),
 "NEUTRAL":np.array([.75,.10,.10,.05]),
 "PANIC":np.array([.65,.05,.10,.20]),
}
class APAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.virtual_inventory=np.zeros((4,4))
        self.virtual_costs=np.zeros(4)
        self.target=np.zeros(4)
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AP_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AP_EVENT")
        self.history.append(self.virtual_inventory@(a-b*e)-self.virtual_costs)
        self.virtual_costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AP_DECISION")
        self.virtual_costs=.001*np.abs(s-self.virtual_inventory).sum(axis=1)
        self.virtual_inventory=s.copy()
        if t<FIRST or (t-FIRST)%EPOCH:
            return self.target.copy(),False
        w=PRIORS[regime].copy()
        active=np.abs(s).sum(axis=1)>0.
        active[0]=True
        if t>=FIRST+HISTORY and len(self.history)==HISTORY:
            evidence=np.asarray(self.history).sum(axis=0)
            active[1:]&=(evidence[1:]>0.)
        w[1:]=np.where(active[1:],w[1:],0.)
        w[0]=1.-float(w[1:].sum())
        if len(self.history)==HISTORY:
            h=np.asarray(self.history)
            portfolio=h@w
            edge=float(portfolio.mean())
            variance=max(float(portfolio.var()),1e-5)
            scale=1.+max(0.,.10*edge/variance)
        else:
            scale=1.
        desired=scale*(w@s)
        if not np.isfinite(desired).all():
            raise ValueError("AP_TARGET")
        self.target=desired.copy()
        self.epochs+=1
        return desired.copy(),True

def static_check():
    a=APAllocator()
    for t in range(3500):
        a.observe(np.array([.0003,.0002,.0001,.0004]),
                  np.zeros(4),np.zeros(4))
        target,changed=a.decide(np.eye(4),"PANIC" if t%2 else "RISK_ON",t)
        assert np.isfinite(target).all()
    assert a.epochs==4,a.epochs
    return True
if __name__=="__main__":
    assert static_check()
    print("AP_STRUCTURAL_ALLOCATOR_CAUSAL_PASS")
