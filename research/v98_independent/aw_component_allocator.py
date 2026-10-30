#!/usr/bin/env python3
"""AW causal 672h shadow growth allocator with independently frozen sleeve units."""
from __future__ import annotations
from collections import deque
import numpy as np
WARMUP=2160
EPOCH=1344
HISTORY=672
BASE=np.array([.55,.12,.10,.15])
MULT={
 "EXPANSION":np.array([1.2,1.3,1.1,.8]),
 "RECOVERY":np.array([.7,1.1,1.2,1.4]),
 "DEFENSIVE":np.array([.5,.4,.6,.7]),
}
class AWAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.shadow=np.zeros((4,4))
        self.costs=np.zeros(4)
        self.last_events=np.zeros((2,4))
        self.budgets=np.zeros(4)
        self.epochs=0
    def observe(self,lr,rate,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,rate,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AW_SHADOW_INPUT")
        if not np.isin(e,(0.,1.)).all():raise ValueError("AW_FUNDING_EVENT")
        gross=self.shadow@(a-b*e)
        if np.any(gross<=-1.):raise ValueError("AW_SHADOW_INSOLVENCY")
        self.history.append(np.log1p(gross)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in MULT:
            raise ValueError("AW_DECISION_INPUT")
        s=np.round(s,12)
        current=s[[1,3]]
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
                confidence=np.clip(np.exp(np.clip(wealth,-20.,20.)),.6,1.4)
            self.budgets=BASE*MULT[regime]*confidence
            mask[:]=True
        else:
            mask[1]=changed[0]
            mask[3]=changed[1]
        if mask.any():self.epochs+=1
        return np.round(self.budgets[:,None]*s,12),mask

def static_check():
    a=AWAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        _,mask=a.decide(s,"DEFENSIVE",t)
        assert not mask.any()
    s[0,0]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x,m=a.decide(s,"EXPANSION",WARMUP)
    assert m.all() and x[0,0]>0
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x2,m=a.decide(s,"EXPANSION",WARMUP+1)
    assert not m.any() and np.array_equal(x,x2)
    s[1,1]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x3,m=a.decide(s,"EXPANSION",WARMUP+2)
    assert np.array_equal(m,np.array([False,True,False,False]))
    assert x3[1,1]>0
    return True
if __name__=="__main__":
    assert static_check()
    print("AW_COMPONENT_FREEZE_ALLOCATOR_PASS")
