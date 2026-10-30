#!/usr/bin/env python3
"""V98 AO causal 336h portfolio allocator, shadow net-funding experts.

No access to future data; virtual sleeve experts are marked every hour.
"""
from __future__ import annotations
from collections import deque
import numpy as np

FIRST=2160
EPOCH=336
HISTORY=720
PRIORS={
 "BULL":np.array([.70,.18,.08,.04]),
 "BEAR":np.array([.55,.08,.20,.17]),
 "CHOP":np.array([.65,.13,.17,.05]),
 "STRESS":np.array([.40,.05,.15,.40]),
}
class AOAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.virtual_inventory=np.zeros((4,4),dtype=float)
        self.virtual_costs=np.zeros(4,dtype=float)
        self.target=np.zeros(4,dtype=float)
        self.epochs=0
    def observe(self,lr,funding,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,funding,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AO_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():
            raise ValueError("AO_FUNDING_EVENT")
        net=self.virtual_inventory@(a-b*e)-self.virtual_costs
        self.history.append(net)
        self.virtual_costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in PRIORS:
            raise ValueError("AO_DECISION_INPUT")
        # Mark virtual sleeves every hour; do NOT change real inventory hourly.
        self.virtual_costs=.001*np.abs(s-self.virtual_inventory).sum(axis=1)
        self.virtual_inventory=s.copy()
        if t<FIRST or (t-FIRST)%EPOCH:
            return self.target.copy(),False
        prior=PRIORS[regime].copy()
        active=np.abs(s).sum(axis=1)>0.
        if t>=FIRST+HISTORY and len(self.history)==HISTORY:
            evidence=np.asarray(self.history).sum(axis=0)
            active&=(evidence>0.)
        # Inactive non-core sleeve budget returns to active growth core.
        w=np.where(active,prior,0.)
        if active[0]:
            w[0]=1.-float(w[1:].sum())
        if len(self.history)==HISTORY and w.sum()>0:
            h=np.asarray(self.history)
            portfolio=h@w
            edge=float(portfolio.mean())
            variance=max(float(portfolio.var()),1e-5)
            scale=1.+max(0.,.15*edge/variance)
        else:
            scale=1.
        desired=scale*(w@s)
        if not np.isfinite(desired).all():
            raise ValueError("AO_NONFINITE_TARGET")
        self.target=desired.copy()
        self.epochs+=1
        return desired.copy(),True

def static_check():
    a=AOAllocator()
    s=np.eye(4)
    trades=0
    for t in range(3500):
        a.observe(np.array([.0003,.0002,.0001,.0004]),
                  np.zeros(4),np.zeros(4))
        _,changed=a.decide(s,"STRESS" if t%2 else "BULL",t)
        trades+=int(changed)
    assert trades==4,trades
    assert np.isfinite(a.target).all()
    return True

if __name__=="__main__":
    assert static_check()
    print("AO_CAUSAL_336H_ALLOCATOR_PASS")
