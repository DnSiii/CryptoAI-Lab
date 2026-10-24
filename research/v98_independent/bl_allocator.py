#!/usr/bin/env python3
"""BL sparse completed-bar regime budget, fixed units, no continuous rebalancing."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=672
BUDGETS={
    "BULL":np.array([1.15,.30,.00,.00]),
    "NEUTRAL":np.array([.70,.00,.18,.00]),
    "CRISIS":np.array([.15,.00,.00,.00]),
    "RECOVERY":np.array([.60,.00,.00,.35]),
}
class BLAllocator:
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
            raise ValueError("BL_ALLOCATOR_INPUT")
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
                approved=(i==1 and edge[i]>.04 and regime=="BULL") or (
                    i==2 and edge[i]>.024 and carry[i]<=0 and regime=="NEUTRAL") or (
                    i==3 and edge[i]>.025 and regime=="RECOVERY")
                if approved:
                    self.active_budgets[i]=BUDGETS[regime][i]
                    self.authorized_events+=1
                else:self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BLAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        _,mask=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4))
        assert not mask.any()
    s[0,0]=1.
    x,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4))
    assert m[0] and x[0,0]==1.15
    s[1,1]=1.
    x,m=a.decide(s,"BULL",WARMUP+1,np.array([0.,.05,0.,0.]),np.zeros(4))
    assert m[1] and x[1,1]==.30
    s[1,1]=0.
    a.decide(s,"BULL",WARMUP+2,np.zeros(4),np.zeros(4))
    s[2,0]=.5;s[2,1]=-.5
    x,m=a.decide(s,"NEUTRAL",WARMUP+3,np.array([0.,0.,.03,0.]),np.array([0.,0.,-.01,0.]))
    assert m[2] and np.isclose(x[2,0],.09)
    s[2]=0.
    a.decide(s,"NEUTRAL",WARMUP+4,np.zeros(4),np.zeros(4))
    s[3,3]=1.
    x,m=a.decide(s,"RECOVERY",WARMUP+5,np.array([0.,0.,0.,.04]),np.zeros(4))
    assert m[3] and x[3,3]==.35
    return True
if __name__=="__main__":
    assert static_check()
    print("BL_CAUSAL_EVENT_BUDGET_PASS")
