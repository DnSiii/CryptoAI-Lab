#!/usr/bin/env python3
"""BN event-only seven-slot allocator; no strategy PnL feedback."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008
BUDGETS={
    "BULL":np.array([.95,.35,0.,0.]),
    "NEUTRAL":np.array([.65,0.,.18,0.]),
    "CRISIS":np.array([.10,0.,0.,.30]),
}
class BNAllocator:
    def __init__(self):
        self.last_events=np.zeros((3,4))
        self.active_budgets=np.zeros(4)
        self.authorized_events=0;self.rejected_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost):
        s=np.asarray(sleeves,dtype=float)
        edge=np.asarray(edge,dtype=float);carry=np.asarray(carry_cost,dtype=float)
        if (s.shape!=(4,4) or edge.shape!=(4,) or carry.shape!=(4,)
            or regime not in BUDGETS
            or any(not np.isfinite(x).all() for x in (s,edge,carry))):
            raise ValueError("BN_ALLOCATOR_INPUT")
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
                approved=(i==1 and edge[i]>.04 and carry[i]<.015 and regime=="BULL") or (
                    i==2 and edge[i]>.005 and carry[i]<.005 and regime=="NEUTRAL") or (
                    i==3 and edge[i]>.08 and carry[i]<.015 and regime=="CRISIS")
                if approved:
                    self.active_budgets[i]=BUDGETS[regime][i]
                    self.authorized_events+=1
                else:self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BNAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        _,m=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4))
        assert not m.any()
    s[0,0]=.5;s[0,1]=.5
    w,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4))
    assert m[0] and np.isclose(w[0,0],.475)
    s[1,2]=1.
    w,m=a.decide(s,"BULL",WARMUP+1,np.array([0,.1,0,0]),np.zeros(4))
    assert m[1] and np.isclose(w[1,2],.35)
    s[1]=0
    a.decide(s,"BULL",WARMUP+2,np.zeros(4),np.zeros(4))
    s[2,0]=.5;s[2,1]=-.5
    w,m=a.decide(s,"NEUTRAL",WARMUP+3,np.array([0,0,.03,0]),np.zeros(4))
    assert m[2] and np.isclose(w[2,0],.09)
    s[2]=0
    a.decide(s,"NEUTRAL",WARMUP+4,np.zeros(4),np.zeros(4))
    s[3,0]=.5;s[3,3]=-.5
    w,m=a.decide(s,"CRISIS",WARMUP+5,np.array([0,0,0,.1]),np.zeros(4))
    assert m[3] and np.isclose(w[3,3],-.15)
    return True
if __name__=="__main__":
    assert static_check()
    print("BN_EVENT_ALLOCATOR_PASS")
