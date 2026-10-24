#!/usr/bin/env python3
"""AV 672h shadow native-funded allocator, 1008h/event-only unit epochs."""
from __future__ import annotations
from collections import deque
import numpy as np
EPOCH=1008
WARMUP=2160
HISTORY=672
BASE=np.array([1.,.35,.15,.25])
MULT={
 "RISK_ON":np.array([1.,1.2,.7,.4]),
 "RISK_OFF":np.array([.5,.5,1.2,1.4]),
 "MIXED":np.array([.8,.8,1.,.8]),
}
FRICTION=.0015
class AVAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.shadow=np.zeros((4,4))
        self.costs=np.zeros(4)
        self.events=np.zeros((3,4))
        self.target=np.zeros(4)
        self.epochs=0
    def observe(self,lr,rate,event):
        a,b,e=(np.asarray(x,dtype=float) for x in (lr,rate,event))
        if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (a,b,e)):
            raise ValueError("AV_SHADOW_INPUT")
        if not np.isin(e,(0.,1.)).all():raise ValueError("AV_EVENT")
        raw=self.shadow@(a-b*e)
        if np.any(raw<=-1.):raise ValueError("AV_SHADOW_INSOLVENCY")
        self.history.append(np.log1p(raw)-self.costs)
        self.costs[:]=0.
    def decide(self,sleeves,regime,t):
        s=np.asarray(sleeves,dtype=float)
        if s.shape!=(4,4) or not np.isfinite(s).all() or regime not in MULT:
            raise ValueError("AV_DECISION")
        s=np.round(s,12)
        event=s[1:4]
        changed=not np.array_equal(event,self.events)
        self.events=event.copy()
        self.costs=FRICTION*np.abs(s-self.shadow).sum(axis=1)
        self.shadow=s.copy()
        if t<WARMUP or ((t-WARMUP)%EPOCH!=0 and not changed):
            return self.target.copy(),False
        conf=np.ones(4)
        if len(self.history)==HISTORY:
            wealth=np.asarray(self.history).sum(axis=0)
            conf=np.clip(np.exp(np.clip(1.5*wealth,-20.,20.)),.5,1.5)
        desired=(BASE*MULT[regime]*conf)@s
        if not np.isfinite(desired).all():raise ValueError("AV_TARGET")
        self.target=np.round(desired,12)
        self.epochs+=1
        return self.target.copy(),True

def static_check():
    a=AVAllocator();s=np.zeros((4,4))
    for t in range(2160):
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        _,ch=a.decide(s,"MIXED",t)
        assert not ch
    s[0,0]=1.
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    x,ch=a.decide(s,"RISK_ON",2160)
    assert ch and x[0]>0
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    y,ch=a.decide(s,"RISK_ON",2161)
    assert not ch and np.array_equal(x,y)
    s[2,1]=.5;s[2,0]=-.5
    a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
    z,ch=a.decide(s,"RISK_ON",2162)
    assert ch and np.isfinite(z).all()
    return True
if __name__=="__main__":
    assert static_check()
    print("AV_ALLOCATOR_EVENT_ONLY_PASS")
