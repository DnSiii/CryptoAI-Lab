#!/usr/bin/env python3
"""BT causal event-only allocation with explicit leverage and native-carry friction gate."""
from __future__ import annotations
from collections import deque
import numpy as np
WARMUP=2160
EPOCH=1008
BUDGETS={"BULL":np.array([1.05,.30,.15,0.]),
         "NEUTRAL":np.array([.90,.15,.20,.15]),
         "CRISIS":np.array([.60,0.,.20,.45])}
class BTAllocator:
    def __init__(self):
        self.prices=deque(maxlen=337)
        self.last_events=np.zeros((3,4))
        self.last_weights=np.zeros((4,4))
        self.authorized_events=0;self.rejected_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost,prices,rate,event):
        s=np.asarray(sleeves,dtype=float)
        ed=np.asarray(edge,dtype=float);carry=np.asarray(carry_cost,dtype=float)
        p=np.asarray(prices,dtype=float);r=np.asarray(rate,dtype=float)
        e=np.asarray(event,dtype=float)
        if (s.shape!=(4,4) or ed.shape!=(4,) or carry.shape!=(4,)
            or p.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,)
            or regime not in BUDGETS or np.any(p<=0) or
            any(not np.isfinite(x).all() for x in (s,ed,carry,p,r,e))):
            raise ValueError("BT_ALLOCATOR_INPUT")
        self.prices.append(np.log(p))
        s=np.round(s,12)
        changed=~np.all(s[1:]==self.last_events,axis=1)
        self.last_events=s[1:].copy()
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return np.zeros((4,4)),mask
        mask[0]=(t-WARMUP)%EPOCH==0
        mask[1:]=changed
        if not mask.any():return self.last_weights.copy(),mask
        if len(self.prices)<337:raise ValueError("BT_VOL_WARMUP")
        change=np.diff(np.asarray(self.prices),axis=0)
        sig=np.sqrt(np.mean(change*change,axis=0))
        scale=float(np.clip(.010/max(float(np.median(sig)),.0001),.7,1.10))
        for i in range(4):
            if not mask[i]:continue
            self.last_weights[i]=0.
            if i==0 or (np.any(s[i]) and
                        ed[i]-max(0.,carry[i])>.012):
                self.last_weights[i]=BUDGETS[regime][i]*scale*s[i]
                if i and np.any(self.last_weights[i]):self.authorized_events+=1
            elif np.any(s[i]):self.rejected_events+=1
        self.last_weights=np.round(self.last_weights,12)
        return self.last_weights.copy(),mask

def static_check():
    a=BTAllocator();s=np.zeros((4,4));p=np.full(4,100.)
    for t in range(WARMUP):
        w,m=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4),
                     p,np.zeros(4),np.zeros(4))
        assert not m.any() and not w.any()
    s[0]=.25
    w,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4),
                 p,np.zeros(4),np.zeros(4))
    assert m[0] and np.isclose(w[0].sum(),1.155)
    s[1,2]=1.
    w,m=a.decide(s,"BULL",WARMUP+1,np.array([0,.1,0,0]),
                 np.zeros(4),p,np.zeros(4),np.zeros(4))
    assert m[1] and np.isclose(w[1,2],.33)
    return True
if __name__=="__main__":
    assert static_check()
    print("BT_EVENT_ALLOCATOR_PASS")
