#!/usr/bin/env python3
"""BB causal online sleeve allocation; persistent frozen component units."""
from __future__ import annotations
from collections import deque
import numpy as np
WARMUP=2160
EPOCH=168
HISTORY=336
BASE=np.array([.65,.12,.13,.10])
MULT={
 "EXPANSION":np.array([1.25,1.1,.9,.3]),
 "PANIC":np.array([.35,.65,1.2,1.7]),
 "TRANSITION":np.array([.8,1.,1.2,.9]),
}
class BBAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.shadow=np.zeros((4,4))
        self.costs=np.zeros(4)
        self.last_events=np.zeros((3,4))
        self.budgets=np.zeros(4)
    def observe(self,lr,rate,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,rate,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("BB_SHADOW_INPUT")
        if not np.isin(e,(0.,1.)).all():raise ValueError("BB_FUNDING_EVENT")
        gross=self.shadow@(a-b*e)
        if np.any(gross<=-1.):raise ValueError("BB_SHADOW_INSOLVENCY")
        self.history.append(np.log1p(gross)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in MULT:
            raise ValueError("BB_DECISION_INPUT")
        s=np.round(s,12)
        changed=~np.all(s[1:]==self.last_events,axis=1)
        self.last_events=s[1:].copy()
        self.costs=.0015*np.abs(s-self.shadow).sum(axis=1)
        self.shadow=s.copy()
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return np.zeros((4,4)),mask
        if (t-WARMUP)%EPOCH==0:
            confidence=np.ones(4)
            if len(self.history)==HISTORY:
                wealth=np.asarray(self.history).sum(axis=0)
                confidence=np.clip(np.exp(np.clip(wealth,-20.,20.)),.65,1.35)
            self.budgets=BASE*MULT[regime]*confidence
            mask[:]=True
        else:
            mask[1:]=changed
        return np.round(self.budgets[:,None]*s,12),mask

def static_check():
    a=BBAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        _,mask=a.decide(s,"TRANSITION",t)
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
    print("BB_COMPONENT_ALLOCATOR_PASS")
