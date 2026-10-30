#!/usr/bin/env python3
"""V98 BI fixed-unit sparse event allocator; causal severe friction admission."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008
SEVERE_HURDLE=.020
BUDGETS={
    "BULL":np.array([1.10,.25,.12,.20]),
    "NEUTRAL":np.array([.80,.12,.15,.20]),
    "CRISIS":np.array([.25,.00,.05,.35]),
}
class BIAllocator:
    def __init__(self):
        self.last_events=np.zeros((3,4))
        self.active_budgets=np.zeros(4)
        self.authorized_events=0
        self.rejected_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost):
        s=np.asarray(sleeves,dtype=float)
        edge=np.asarray(edge,dtype=float)
        carry=np.asarray(carry_cost,dtype=float)
        if (s.shape!=(4,4) or edge.shape!=(4,) or carry.shape!=(4,)
            or regime not in BUDGETS or
            any(not np.isfinite(x).all() for x in (s,edge,carry))):
            raise ValueError("BI_ALLOCATOR_INPUT")
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
            self.active_budgets[i]=0.
            if np.any(s[i]):
                expected_net=float(edge[i]-max(carry[i],0.)-SEVERE_HURDLE)
                if expected_net>0:
                    self.active_budgets[i]=BUDGETS[regime][i]
                    self.authorized_events+=1
                else:self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BIAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        _,mask=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4))
        assert not mask.any()
    s[0,0]=1.
    x,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4))
    assert m[0] and x[0,0]==1.10
    s[1,1]=1.
    x,m=a.decide(s,"BULL",WARMUP+1,np.array([0.,.04,0.,0.]),np.zeros(4))
    assert m[1] and x[1,1]==.25
    x,m=a.decide(s,"CRISIS",WARMUP+2,np.zeros(4),np.ones(4))
    assert not m.any() and x[1,1]==.25
    s[1,1]=0.
    x,m=a.decide(s,"BULL",WARMUP+3,np.zeros(4),np.zeros(4))
    assert m[1] and x[1,1]==0.
    s[1,1]=1.
    x,m=a.decide(s,"BULL",WARMUP+4,np.array([0.,.01,0.,0.]),np.zeros(4))
    assert m[1] and x[1,1]==0. and a.rejected_events==1
    return True
if __name__=="__main__":
    assert static_check()
    print("BI_CAUSAL_EVENT_BUDGET_PASS")
