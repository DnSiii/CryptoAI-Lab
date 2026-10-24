#!/usr/bin/env python3
"""CA fixed ex-ante regime budgets and event-frozen four-book allocator."""
from __future__ import annotations
import numpy as np
from ca_sources import WARMUP,CORE_EPOCH
BUDGETS={
    "BULL":np.array([1.35,.90,.80,0.]),
    "NEUTRAL":np.array([1.10,.65,.80,.40]),
    "CRISIS":np.array([.35,0.,.80,1.00]),
}
class CAAllocator:
    def __init__(self):
        self.last=np.zeros((4,4))
        self.prev_sat=np.zeros((3,4))
    def decide(self,sleeves,regime,t,vol):
        s=np.asarray(sleeves,dtype=float)
        if (s.shape!=(4,4) or regime not in BUDGETS or
            not np.isfinite(s).all() or not np.isfinite(vol) or vol<0 or
            np.any(s[:,2:])):
            raise ValueError("CA_ALLOCATOR_INPUT")
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return self.last.copy(),mask
        mask[0]=(t-WARMUP)%CORE_EPOCH==0
        mask[1:]=np.any(np.round(s[1:],12)!=self.prev_sat,axis=1)
        self.prev_sat=np.round(s[1:],12).copy()
        for i in np.flatnonzero(mask):
            self.last[i]=np.round(BUDGETS[regime][i]*s[i],12)
        return self.last.copy(),mask

def static_check():
    a=CAAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        w,m=a.decide(s,"NEUTRAL",t,0.)
        assert not m.any() and not w.any()
    s[0,:2]=[.5,.5];s[1,1]=1.
    w,m=a.decide(s,"BULL",WARMUP,.01)
    assert m[0] and m[1] and not m[2] and not m[3]
    assert np.isclose(w[0,0],.675) and np.isclose(w[1,1],.90)
    s[0]=0.
    w,m=a.decide(s,"NEUTRAL",WARMUP+1,.01)
    assert not m.any() and np.isclose(w[0,0],.675)
    s[1]=0.
    w,m=a.decide(s,"CRISIS",WARMUP+2,.01)
    assert m[1] and not w[1].any() and np.isclose(w[0,0],.675)
    w,m=a.decide(s,"CRISIS",WARMUP+CORE_EPOCH,.01)
    assert m[0] and not w[0].any()
    return True

if __name__=="__main__":
    assert static_check()
    print("CA_FROZEN_REGIME_EVENT_ALLOCATOR_PASS")
