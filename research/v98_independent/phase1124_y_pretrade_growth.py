#!/usr/bin/env python3
"""Y t-1 81-state signed portfolio max-growth pretrade scale; no PnL.

Separate from Y hourly reduce-only controller: 12h target entries include
costs, prior quote capacity, signed funding reserve and basket exit proof.
"""
from __future__ import annotations
import numpy as np
from phase1123_y_continuous_feedback import STATES
N=4;FEE=.002;SLIP=.002;ASSET=.45;NET=.75;GROSS=1.35
FLOOR=.25;FUNDING_EVENTS=6;CAPACITY=.01;ITERATIONS=32;QUANTUM=1e-6

def inputs(raw,prior,down,up,funding,quote,capital):
    w,p,d,h,f,q=[np.asarray(x,float) for x in
                 (raw,prior,down,up,funding,quote)]
    if (any(x.shape!=(4,) or not np.isfinite(x).all() for x in (w,p,d,h,f,q))
        or (p<=0).any() or (d<0).any() or (d>=1).any()
        or (h<0).any() or (f<0).any() or (q<0).any()
        or not np.isfinite(capital) or capital<=0):
        raise ValueError('Y_PRETRADE_BAD_PRIOR')
    return w,p,d,h,f,q

def feasible(w,prior,down,up,funding,quote,capital):
    w,p,d,h,f,q=inputs(w,prior,down,up,funding,quote,capital)
    cap_ok=np.all(np.abs(w)*capital*(1+np.maximum(h,d))*(1+SLIP)
                  <=CAPACITY*q+1e-8)
    factors=np.stack((1-d,np.ones(4),1+h),axis=0)
    marked=w[None,:]*factors[STATES,np.arange(4)]
    reserve=FUNDING_EVENTS*np.sum(np.abs(w)*f*(1+h))
    cash=1.-w.sum()-(FEE+SLIP)*np.abs(w).sum()
    equity=cash+marked.sum(axis=1)-reserve
    gross=np.abs(marked).sum(axis=1)
    net=np.abs(marked.sum(axis=1))
    asset=np.abs(marked).max(axis=1)
    adverse=np.where(w>=0,1-d,1+h)
    basket_cash=cash+np.sum(w*adverse*(1-np.sign(w)*SLIP)
                    -FEE*np.abs(w)*adverse*(1+SLIP))-reserve
    return bool(cap_ok and np.isfinite(equity).all()
        and np.all(equity>=FLOOR-1e-12) and basket_cash>=FLOOR-1e-12
        and np.all(asset<=ASSET*equity+1e-12)
        and np.all(gross<=GROSS*equity+1e-12)
        and np.all(net<=NET*equity+1e-12))

def maximize(raw,prior,down,up,funding,quote,capital):
    w,p,d,h,f,q=inputs(raw,prior,down,up,funding,quote,capital)
    if not np.any(w):return np.zeros(4)
    lo,hi=0.,1.
    for _ in range(ITERATIONS):
        mid=(lo+hi)/2
        proposal=np.trunc(w*mid/QUANTUM)*QUANTUM
        if feasible(proposal,p,d,h,f,q,capital):lo=mid
        else:hi=mid
    out=np.trunc(w*lo/QUANTUM)*QUANTUM
    if not feasible(out,p,d,h,f,q,capital):
        raise AssertionError('Y_PRETRADE_SERIALIZATION')
    return out
