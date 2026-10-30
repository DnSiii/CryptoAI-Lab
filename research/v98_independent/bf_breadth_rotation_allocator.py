#!/usr/bin/env python3
"""BF breadth-led event-only severe-cost gate with frozen physical units."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=336
# At severe fees .002 and slippage .003 per side, round trip is .010.
# Preregistered two-times-round-trip hurdle = .020, not fitted to outcomes.
SEVERE_TWO_ROUND_TRIPS=.020
BUDGETS={
 "BREADTH":np.array([1.05,.12,.10,.05]),
 "STRESS":np.array([.20,.00,.03,.18]),
 "ROTATION":np.array([.85,.10,.12,.08]),
 "FLAT":np.array([.55,.06,.05,.06]),
}
class BFAllocator:
    def __init__(self):
        self.last_events=np.zeros((3,4))
        self.active_budgets=np.zeros(4)
        self.approved=np.zeros(4,dtype=bool)
        self.rejected_events=0
        self.authorized_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost):
        s=np.asarray(sleeves,dtype=float)
        edge=np.asarray(edge,dtype=float)
        carry=np.asarray(carry_cost,dtype=float)
        if (s.shape!=(4,4) or edge.shape!=(4,) or carry.shape!=(4,)
            or regime not in BUDGETS or
            any(not np.isfinite(x).all() for x in (s,edge,carry))):
            raise ValueError("BF_ALLOCATOR_INPUT")
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
            mask[i]=True
            self.approved[i]=False
            self.active_budgets[i]=0.
            if np.any(s[i]):
                expected_net=float(edge[i]-max(carry[i],0.)-SEVERE_TWO_ROUND_TRIPS)
                if expected_net>0:
                    self.approved[i]=True
                    self.active_budgets[i]=BUDGETS[regime][i]
                    self.authorized_events+=1
                else:
                    self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BFAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        _,mask=a.decide(s,"FLAT",t,np.zeros(4),np.zeros(4))
        assert not mask.any()
    s[0,0]=1.
    x,m=a.decide(s,"BREADTH",WARMUP,np.zeros(4),np.zeros(4))
    assert m[0] and x[0,0]==1.05
    s[1,1]=1.
    x,m=a.decide(s,"BREADTH",WARMUP+1,np.array([0.,.04,0.,0.]),np.zeros(4))
    assert m[1] and x[1,1]==.12
    x,m=a.decide(s,"BREADTH",WARMUP+2,np.zeros(4),np.ones(4))
    assert not m.any() and x[1,1]==.12
    s[1,1]=0.
    x,m=a.decide(s,"BREADTH",WARMUP+3,np.zeros(4),np.zeros(4))
    assert m[1] and x[1,1]==0.
    s[1,1]=1.
    x,m=a.decide(s,"BREADTH",WARMUP+4,np.array([0.,.01,0.,0.]),np.zeros(4))
    assert m[1] and x[1,1]==0. and a.rejected_events==1
    return True

if __name__=="__main__":
    assert static_check()
    print("BF_ALLOCATOR_SEVERE_HURDLE_PASS")
