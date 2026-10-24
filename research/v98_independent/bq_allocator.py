#!/usr/bin/env python3
"""BQ causal prequential shadow-expert allocator, no realized strategy PnL feedback."""
from __future__ import annotations
from collections import deque
import math
import numpy as np
WARMUP=2160
EPOCH=1008
BUDGETS={"BULL":np.array([.90,.30,.12,0.]),
         "NEUTRAL":np.array([.65,.10,.18,0.]),
         "CRISIS":np.array([.20,0.,0.,.25])}
SHADOW_FEE=.005
class BQAllocator:
    def __init__(self):
        self.last_events=np.zeros((3,4))
        self.active_budgets=np.zeros(4)
        self.previous_signal=np.zeros((4,4))
        self.previous_prices=None
        self.history=[deque(maxlen=1008) for _ in range(4)]
        self.active=[deque(maxlen=1008) for _ in range(4)]
        self.authorized_events=0;self.rejected_events=0
    def decide(self,sleeves,regime,t,edge,carry_cost,prices,rate,event):
        s=np.asarray(sleeves,dtype=float)
        edge=np.asarray(edge,dtype=float);carry=np.asarray(carry_cost,dtype=float)
        p=np.asarray(prices,dtype=float);r=np.asarray(rate,dtype=float)
        e=np.asarray(event,dtype=float)
        if (s.shape!=(4,4) or edge.shape!=(4,) or carry.shape!=(4,)
            or p.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,)
            or regime not in BUDGETS or np.any(p<=0) or
            any(not np.isfinite(x).all() for x in (s,edge,carry,p,r,e))):
            raise ValueError("BQ_ALLOCATOR_INPUT")
        s=np.round(s,12)
        if self.previous_prices is not None:
            change=np.abs(s-self.previous_signal).sum(axis=1)
            price_return=p/self.previous_prices-1.
            pnl=self.previous_signal@price_return-self.previous_signal@(r*e)
            pnl=pnl-SHADOW_FEE*change
            for i in range(4):
                self.history[i].append(math.log1p(max(-.95,float(pnl[i]))))
                self.active[i].append(int(np.any(self.previous_signal[i])))
        self.previous_prices=p.copy();self.previous_signal=s.copy()
        changed=~np.all(s[1:]==self.last_events,axis=1)
        self.last_events=s[1:].copy()
        mask=np.zeros(4,dtype=bool)
        if t<WARMUP:return np.zeros((4,4)),mask
        if (t-WARMUP)%EPOCH==0:
            self.active_budgets[0]=BUDGETS[regime][0]
            mask[0]=True
        core=np.asarray(self.history[0],dtype=float)
        for i in range(1,4):
            if not changed[i-1]:continue
            mask[i]=True;self.active_budgets[i]=0.
            if np.any(s[i]):
                hist=np.asarray(self.history[i],dtype=float)
                exposed=sum(self.active[i])
                if len(hist)>=168 and exposed>=72 and len(core)==len(hist):
                    cov=float(np.mean((hist-hist.mean())*(core-core.mean())))
                    net_growth=float(hist.sum()-.5*len(hist)*max(0.,cov))
                    if net_growth>.02 and BUDGETS[regime][i]>0:
                        confidence=min(1.,net_growth/.10)
                        self.active_budgets[i]=BUDGETS[regime][i]*confidence
                        self.authorized_events+=1
                    else:self.rejected_events+=1
                else:self.rejected_events+=1
        return np.round(self.active_budgets[:,None]*s,12),mask

def static_check():
    a=BQAllocator();s=np.zeros((4,4));p=np.full(4,100.)
    for t in range(WARMUP):
        w,m=a.decide(s,"NEUTRAL",t,np.zeros(4),np.zeros(4),
                     p,np.zeros(4),np.zeros(4))
        assert not m.any() and not w.any()
    s[0,0]=1.
    w,m=a.decide(s,"BULL",WARMUP,np.zeros(4),np.zeros(4),
                 p,np.zeros(4),np.zeros(4))
    assert m[0] and np.isclose(w[0,0],.9)
    s[1,2]=1.
    w,m=a.decide(s,"BULL",WARMUP+1,np.zeros(4),np.zeros(4),
                 p,np.zeros(4),np.zeros(4))
    assert m[1] and not w[1].any() and a.rejected_events==1
    return True
if __name__=="__main__":
    assert static_check()
    print("BQ_PREQUENTIAL_SHADOW_ALLOCATOR_PASS")
