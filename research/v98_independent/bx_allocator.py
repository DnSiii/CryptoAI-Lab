#!/usr/bin/env python3
"""BX regime-volatility allocator: no cross-book cash transfers or PnL feedback."""
from __future__ import annotations
import numpy as np
from bx_sources import WARMUP,CORE_EPOCH,SAT_EPOCH

BUDGETS={
    "BULL":np.array([1.50,1.40,.80,0.]),
    "NEUTRAL":np.array([1.10,1.00,.80,0.]),
    "CRISIS":np.array([.40,0.,.50,1.00]),
}
class BXAllocator:
    def __init__(self):
        self.last=np.zeros((4,4))
    def decide(self,sleeves,regime,t,vol):
        s=np.asarray(sleeves,dtype=float)
        if (s.shape!=(4,4) or regime not in BUDGETS
            or not np.isfinite(s).all() or not np.isfinite(vol)
            or vol<0):
            raise ValueError("BX_ALLOCATOR_INPUT")
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return self.last.copy(),mask
        if (t-WARMUP)%SAT_EPOCH:return self.last.copy(),mask
        mask[[1,3]]=True
        if (t-WARMUP)%CORE_EPOCH==0:mask[[0,2]]=True
        scale=min(1.,.015/max(.005,float(vol)))
        for i in np.flatnonzero(mask):
            self.last[i]=np.round(BUDGETS[regime][i]*scale*s[i],12)
        return self.last.copy(),mask

def static_check():
    a=BXAllocator();p=np.zeros((4,4))
    for t in range(WARMUP):
        w,m=a.decide(p,"NEUTRAL",t,0.)
        assert not m.any() and not w.any()
    p[0,0]=1.;p[1,3]=1.;p[2,:2]=[.5,-.5]
    w,m=a.decide(p,"BULL",WARMUP,.01)
    assert m.all() and np.isclose(w[0,0],1.5)
    assert np.isclose(w[1,3],1.4)
    p[:]=0.
    w,m=a.decide(p,"NEUTRAL",WARMUP+SAT_EPOCH,.01)
    assert not m[0] and not m[2] and m[1] and m[3]
    assert np.isclose(w[0,0],1.5) and not np.any(w[1])
    w,m=a.decide(p,"NEUTRAL",WARMUP+CORE_EPOCH,.03)
    assert m.all() and not w.any()
    return True
if __name__=="__main__":
    assert static_check()
    print("BX_SEGREGATED_DYNAMIC_ALLOCATOR_PASS")
