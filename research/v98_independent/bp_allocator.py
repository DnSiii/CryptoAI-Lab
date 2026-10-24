#!/usr/bin/env python3
"""BP event-only confidence allocator, costs and native carry ex ante, no observed strategy PnL."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=720
BUDGETS={"BULL":np.array([.95,.30,.18,0.]),
         "NEUTRAL":np.array([.70,0.,.18,.20]),
         "CRISIS":np.array([.25,0.,0.,.25])}
ROUNDTRIP_SEVERE=.010
class BPAllocator:
    def __init__(self):
        self.last_events=np.zeros((3,4))
        self.active_budgets=np.zeros(4)
        self.authorized_events=0;self.rejected_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost):
        s=np.asarray(sleeves,dtype=float)
        edge=np.asarray(edge,dtype=float);carry=np.asarray(carry_cost,dtype=float)
        if (s.shape!=(4,4) or edge.shape!=(4,) or carry.shape!=(4,)
            or regime not in BUDGETS or
            any(not np.isfinite(x).all() for x in (s,edge,carry))):
            raise ValueError("BP_ALLOCATOR_INPUT")
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
            if np.any(s[i]):
                # Forecast is a fixed lagged-price heuristic, NOT estimated future alpha.
                # Must cover severe two-way friction, positive carry and risk buffer.
                projected=edge[i]-max(0.,carry[i])-ROUNDTRIP_SEVERE
                minimum={1:.045,2:.055,3:.025}[i]
                eligible=((i==1 and regime=="BULL") or
                          (i==2 and regime!="CRISIS") or
                          (i==3 and regime in ("CRISIS","NEUTRAL")))
                if eligible and projected>minimum:
                    # Confidence scales *at entry*, never continuous rebalancing.
                    confidence=min(1.,max(.0,projected/(3.*minimum)))
                    self.active_budgets[i]=BUDGETS[regime][i]*confidence
                    self.authorized_events+=1
                else:self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BPAllocator();s=np.zeros((4,4))
    for t in range(WARMUP):
        _,m=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4))
        assert not m.any()
    s[0,0]=.65;s[0,1]=.35
    w,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4))
    assert m[0] and np.isclose(w[0,0],.6175)
    s[1,2]=1.
    w,m=a.decide(s,"BULL",WARMUP+1,np.array([0,.2,0,0]),np.zeros(4))
    assert m[1] and np.isclose(w[1,2],.3)
    s[1]=0
    a.decide(s,"BULL",WARMUP+2,np.zeros(4),np.zeros(4))
    s[2,0]=.5;s[2,1]=-.5
    w,m=a.decide(s,"NEUTRAL",WARMUP+3,np.array([0,0,.2,0]),np.zeros(4))
    assert m[2] and np.isclose(w[2,0],.09)
    s[2]=0
    a.decide(s,"NEUTRAL",WARMUP+4,np.zeros(4),np.zeros(4))
    s[3,0]=1.
    w,m=a.decide(s,"CRISIS",WARMUP+5,np.array([0,0,0,.1]),np.zeros(4))
    assert m[3] and np.isclose(w[3,0],.25)
    return True
if __name__=="__main__":
    assert static_check()
    print("BP_EVENT_CONFIDENCE_ALLOCATOR_PASS")
