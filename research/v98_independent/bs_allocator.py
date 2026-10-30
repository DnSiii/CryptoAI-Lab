#!/usr/bin/env python3
"""BS synchronous 1008h portfolio allocation with causal 336h volatility scale."""
from __future__ import annotations
from collections import deque
import numpy as np
WARMUP=2160
EPOCH=1008
BUDGETS={"BULL":np.array([1.15,.30,.15,0.]),
         "NEUTRAL":np.array([.85,.20,.25,.25]),
         "CRISIS":np.array([.35,0.,.20,.45])}
class BSAllocator:
    def __init__(self):
        self.prices=deque(maxlen=337)
        self.authorized_events=0;self.rejected_events=0
        self.last_weights=np.zeros((4,4))
    def decide(self,sleeves,regime,t,edge,carry_cost,prices,rate,event):
        s=np.asarray(sleeves,dtype=float)
        ed=np.asarray(edge,dtype=float);carry=np.asarray(carry_cost,dtype=float)
        p=np.asarray(prices,dtype=float);r=np.asarray(rate,dtype=float)
        e=np.asarray(event,dtype=float)
        if (s.shape!=(4,4) or ed.shape!=(4,) or carry.shape!=(4,)
            or p.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,)
            or regime not in BUDGETS or np.any(p<=0) or
            any(not np.isfinite(x).all() for x in (s,ed,carry,p,r,e))):
            raise ValueError("BS_ALLOCATOR_INPUT")
        self.prices.append(np.log(p))
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP or (t-WARMUP)%EPOCH:
            return self.last_weights.copy(),mask
        if len(self.prices)<337:raise ValueError("BS_VOL_WARMUP")
        change=np.diff(np.asarray(self.prices),axis=0)
        sig=np.sqrt(np.mean(change*change,axis=0))
        scale=float(np.clip(.012/max(float(np.median(sig)),.0001),.5,1.25))
        w=np.zeros((4,4))
        for i in range(4):
            if i==0 or (np.any(s[i]) and
                        ed[i]-max(0.,carry[i])>.012):
                w[i]=BUDGETS[regime][i]*scale*s[i]
                if i and np.any(w[i]):self.authorized_events+=1
            elif np.any(s[i]):self.rejected_events+=1
        self.last_weights=np.round(w,12)
        mask[:]=True
        return self.last_weights.copy(),mask

def static_check():
    a=BSAllocator();s=np.zeros((4,4));p=np.full(4,100.)
    for t in range(WARMUP):
        w,m=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4),
                     p,np.zeros(4),np.zeros(4))
        assert not m.any() and not w.any()
    s[0,0]=1.;s[1,1]=1.
    w,m=a.decide(s,"BULL",WARMUP,np.array([0,.1,0,0]),
                 np.zeros(4),p,np.zeros(4),np.zeros(4))
    assert m.all() and np.isclose(w[0,0],1.4375) and np.isclose(w[1,1],.375)
    w,m=a.decide(s,"BULL",WARMUP+1,np.zeros(4),
                 np.zeros(4),p,np.zeros(4),np.zeros(4))
    assert not m.any() and np.isclose(w[0,0],1.4375)
    return True
if __name__=="__main__":
    assert static_check()
    print("BS_SYNC_ALLOCATOR_PASS")
