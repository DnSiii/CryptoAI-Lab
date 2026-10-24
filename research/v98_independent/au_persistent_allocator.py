#!/usr/bin/env python3
"""AU causal 720h shadow-net-wealth allocator. No rejected-engine signals."""
from __future__ import annotations
from collections import deque
import numpy as np
MONTH=720
WARMUP=2160
BASE=np.array([.95,.25,.20,.25],dtype=float)
MULT={
    "EXPANSION":np.array([1.,1.2,.8,.5]),
    "CONTRACTION":np.array([.5,.5,1.2,1.3]),
    "TRANSITION":np.array([.8,.8,1.,1.]),
}
SHADOW_FRICTION=.0015

class AUAllocator:
    def __init__(self):
        self.history=deque(maxlen=MONTH)
        self.shadow=np.zeros((4,4))
        self.pending_shadow_cost=np.zeros(4)
        self.target=np.zeros(4)
        self.last_events=np.zeros((2,4))
        self.epochs=0
    def observe(self,lr,rate,event):
        x,r,e=(np.asarray(a,dtype=float) for a in (lr,rate,event))
        if any(a.shape!=(4,) or not np.isfinite(a).all() for a in (x,r,e)):
            raise ValueError("AU_SHADOW_OBSERVATION")
        if not np.isin(e,(0.,1.)).all():raise ValueError("AU_SHADOW_EVENT")
        gross=self.shadow@(x-r*e)
        if np.any(gross<=-1.):raise ValueError("AU_SHADOW_INSOLVENT")
        self.history.append(np.log1p(gross)-self.pending_shadow_cost)
        self.pending_shadow_cost[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in MULT:
            raise ValueError("AU_ALLOCATOR_INPUT")
        s=np.round(s,12)
        event=s[[1,3]]
        changed=not np.array_equal(event,self.last_events)
        self.last_events=event.copy()
        self.pending_shadow_cost=SHADOW_FRICTION*np.sum(np.abs(s-self.shadow),axis=1)
        self.shadow=s.copy()
        if t<WARMUP or (((t-WARMUP)%MONTH)!=0 and not changed):
            return self.target.copy(),False
        confidence=np.ones(4)
        if len(self.history)==MONTH:
            h=np.asarray(self.history,dtype=float)
            logwealth=np.sum(h,axis=0)
            confidence=np.clip(np.exp(np.clip(2.*logwealth,-20.,20.)),.5,1.5)
        budget=BASE*MULT[regime]*confidence
        desired=budget@s
        if not np.isfinite(desired).all():raise ValueError("AU_ALLOCATOR_TARGET")
        self.target=np.round(desired,12)
        self.epochs+=1
        return self.target.copy(),True

def static_check():
    a=AUAllocator();s=np.zeros((4,4))
    for t in range(2160):
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        x,flag=a.decide(s,"TRANSITION",t)
        assert not flag and not np.any(x)
    s[0,0]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x,flag=a.decide(s,"EXPANSION",2160)
    assert flag and x[0]>0
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x2,flag=a.decide(s,"EXPANSION",2161)
    assert not flag and np.array_equal(x,x2)
    s[1,1]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x3,flag=a.decide(s,"EXPANSION",2162)
    assert flag and x3[1]>0
    return True

if __name__=="__main__":
    assert static_check()
    print("AU_ALLOCATOR_NO_HOURLY_REBALANCE_PASS")
