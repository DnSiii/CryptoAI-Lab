#!/usr/bin/env python3
"""BR preregistered frozen-event friction-budget allocator; no fitted PnL."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=840
BUDGETS={"BULL":np.array([.90,.32,.22,0.]),
         "NEUTRAL":np.array([.70,.20,.22,.20]),
         "CRISIS":np.array([.25,0.,.10,.38])}
class BRAllocator:
    def __init__(self):
        self.last_events=np.zeros((3,4))
        self.active_budgets=np.zeros(4)
        self.authorized_events=0;self.rejected_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost,prices,rate,event):
        s=np.asarray(sleeves,dtype=float)
        edge=np.asarray(edge,dtype=float)
        carry=np.asarray(carry_cost,dtype=float)
        p=np.asarray(prices,dtype=float);r=np.asarray(rate,dtype=float)
        e=np.asarray(event,dtype=float)
        if (s.shape!=(4,4) or edge.shape!=(4,) or carry.shape!=(4,)
            or p.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,)
            or regime not in BUDGETS or np.any(p<=0) or
            any(not np.isfinite(x).all() for x in (s,edge,carry,p,r,e))):
            raise ValueError("BR_ALLOCATOR_INPUT")
        s=np.round(s,12)
        changed=~np.all(s[1:]==self.last_events,axis=1)
        self.last_events=s[1:].copy()
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return np.zeros((4,4)),mask
        if (t-WARMUP)%EPOCH==0:
            self.active_budgets[0]=BUDGETS[regime][0]
            mask[0]=True
        for i in range(1,4):
            if not changed[i-1]:continue
            mask[i]=True;self.active_budgets[i]=0.
            if np.any(s[i]) and BUDGETS[regime][i]>0:
                estimate=(edge[i]-.012 if i==2 else
                          edge[i]-max(0.,carry[i])-.012)
                confidence=float(np.clip(estimate/(.04 if i==2 else .06),.35,1.))
                self.active_budgets[i]=BUDGETS[regime][i]*confidence
                self.authorized_events+=1
            elif np.any(s[i]):self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BRAllocator();s=np.zeros((4,4));p=np.full(4,100.)
    for t in range(WARMUP):
        w,m=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4),p,
                     np.zeros(4),np.zeros(4))
        assert not m.any() and not w.any()
    s[0,0]=1.
    w,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4),p,
                 np.zeros(4),np.zeros(4))
    assert m[0] and np.isclose(w[0,0],.9)
    s[1,2]=1.
    w,m=a.decide(s,"BULL",WARMUP+1,np.array([0,.1,0,0]),
                 np.zeros(4),p,np.zeros(4),np.zeros(4))
    assert m[1] and np.isclose(w[1,2],.32)
    s[2,0]=.5;s[2,1]=-.5
    w,m=a.decide(s,"NEUTRAL",WARMUP+2,np.array([0,.1,.1,0]),
                 np.zeros(4),p,np.zeros(4),np.zeros(4))
    assert m[2] and np.isclose(w[2,0],.11)
    return True
if __name__=="__main__":
    assert static_check()
    print("BR_EVENT_ALLOCATOR_PASS")
