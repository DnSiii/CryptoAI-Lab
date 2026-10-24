#!/usr/bin/env python3
"""AZ causal 672h native funding-carry quality allocator with independently frozen sleeve units."""
from __future__ import annotations
from collections import deque
import numpy as np
WARMUP=2160
EPOCH=672
HISTORY=672
BASE=np.array([.62,.12,.16,.10])
MULT={
 "TREND":np.array([1.2,1.2,1.3,.7]),
 "DEFENSE":np.array([.45,.35,.7,1.4]),
 "CARRY":np.array([.8,.7,1.2,1.0]),
}
class AZAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.shadow=np.zeros((4,4))
        self.costs=np.zeros(4)
        self.last_events=np.zeros((3,4))
        self.budgets=np.zeros(4)
        self.epochs=0
    def observe(self,lr,rate,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,rate,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AZ_SHADOW_INPUT")
        if not np.isin(e,(0.,1.)).all():raise ValueError("AZ_FUNDING_EVENT")
        gross=self.shadow@(a-b*e)
        if np.any(gross<=-1.):raise ValueError("AZ_SHADOW_INSOLVENCY")
        self.history.append(np.log1p(gross)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in MULT:
            raise ValueError("AZ_DECISION_INPUT")
        s=np.round(s,12)
        current=s[1:4]
        changed=~np.all(current==self.last_events,axis=1)
        self.last_events=current.copy()
        self.costs=.0015*np.abs(s-self.shadow).sum(axis=1)
        self.shadow=s.copy()
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return np.zeros((4,4)),mask
        if (t-WARMUP)%EPOCH==0:
            confidence=np.ones(4)
            if len(self.history)==HISTORY:
                wealth=np.asarray(self.history).sum(axis=0)
                confidence=np.clip(np.exp(np.clip(1.0*wealth,-20.,20.)),.6,1.4)
            self.budgets=BASE*MULT[regime]*confidence
            mask[:]=True
        else:
            mask[1:4]=changed
        if mask.any():self.epochs+=1
        return np.round(self.budgets[:,None]*s,12),mask

def static_check():
    a=AZAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        _,mask=a.decide(s,"CARRY",t)
        assert not mask.any()
    s[0,0]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x,m=a.decide(s,"TREND",WARMUP)
    assert m.all() and x[0,0]>0
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x2,m=a.decide(s,"TREND",WARMUP+1)
    assert not m.any() and np.array_equal(x,x2)
    s[1,1]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x3,m=a.decide(s,"TREND",WARMUP+2)
    assert np.array_equal(m,np.array([False,True,False,False]))
    assert x3[1,1]>0
    return True
if __name__=="__main__":
    assert static_check()
    print("AZ_COMPONENT_FREEZE_ALLOCATOR_PASS")
