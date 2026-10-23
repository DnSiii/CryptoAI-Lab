#!/usr/bin/env python3
"""X independent 256-state whole-basket contingency growth governor, no PnL."""
from __future__ import annotations
import itertools
import numpy as np
N=4
STATES=np.asarray(tuple(itertools.product(range(4),repeat=N)),dtype=np.int8)
ASSET_CAP=.45;NET_CAP=.75;GROSS_CAP=1.35;EQUITY_FLOOR=.25
FEE=.002;SLIP=.002;FUNDING_EVENTS=6;PARTICIPATION=.01
ITERATIONS=32;QUANTUM=1e-6

def inputs(raw,price,down,up,funding,quote,capital):
    w,p,d,h,f,q=[np.asarray(x,float) for x in (raw,price,down,up,funding,quote)]
    if (any(x.shape!=(4,) or not np.isfinite(x).all() for x in (w,p,d,h,f,q))
        or (p<=0).any() or (d<0).any() or (d>=1).any()
        or (h<0).any() or (f<0).any() or (q<0).any()
        or not np.isfinite(capital) or capital<=0):
        raise ValueError('X_GOVERNOR_BAD_PRIOR')
    return w,p,d,h,f,q

def feasible(weights,price,down,up,funding,quote,capital,*,details=False):
    w,p,d,h,f,q=inputs(weights,price,down,up,funding,quote,capital)
    sign=np.sign(w)[None,:]
    adverse=np.where(w>=0,1-d,1+h)[None,:]
    favorable=np.where(w>=0,1+h,1-d)[None,:]
    liquid=np.abs(w)*capital*np.maximum(adverse[0],favorable[0])*(1+SLIP)
    capacity_ok=bool(np.all(liquid<=PARTICIPATION*q+1e-8))
    # Unlike W, ANY one stopped asset pretriggers full basket liquidation.
    basket_stop=np.any(STATES==2,axis=1)
    frac=np.where(basket_stop[:,None],1.,np.where(STATES==3,1./3.,0.))
    fill_factor=np.where(basket_stop[:,None],adverse,
                         np.where(STATES==3,favorable,1.))
    mark_factor=np.where(STATES==0,1.,adverse)
    exposure=np.where(basket_stop[:,None],0.,w[None,:]*(1-frac)*mark_factor)
    proceeds=w[None,:]*frac*fill_factor*(1-sign*SLIP)
    exit_cost=FEE*np.abs(w[None,:])*frac*fill_factor*(1+SLIP)
    entry_cost=(FEE+SLIP)*np.abs(w).sum()
    reserve=FUNDING_EVENTS*np.sum(np.abs(w)*f*(1+h))
    cash=1.-w.sum()-entry_cost+np.sum(proceeds-exit_cost,axis=1)
    equity=cash+exposure.sum(axis=1)-reserve
    asset=np.abs(exposure).max(axis=1)
    gross=np.abs(exposure).sum(axis=1)
    net=np.abs(exposure.sum(axis=1))
    ok=(capacity_ok and np.isfinite(equity).all()
        and np.all(equity>=EQUITY_FLOOR-1e-12)
        and np.all(asset<=ASSET_CAP*equity+1e-12)
        and np.all(gross<=GROSS_CAP*equity+1e-12)
        and np.all(net<=NET_CAP*equity+1e-12))
    if not details:return bool(ok)
    return {'feasible':bool(ok),'states':len(STATES),
        'basket_stop_states':int(basket_stop.sum()),
        'worst_equity':float(equity.min()),'capacity_ok':capacity_ok}

def maximize(raw,price,down,up,funding,quote,capital):
    w,p,d,h,f,q=inputs(raw,price,down,up,funding,quote,capital)
    if not np.any(w):return np.zeros(4)
    lo=0.;hi=1.
    for _ in range(ITERATIONS):
        mid=(lo+hi)/2
        proposal=np.trunc(w*mid/QUANTUM)*QUANTUM
        if feasible(proposal,p,d,h,f,q,capital):lo=mid
        else:hi=mid
    out=np.trunc(w*lo/QUANTUM)*QUANTUM
    if not feasible(out,p,d,h,f,q,capital):
        raise AssertionError('X_CONTINGENT_SERIALIZATION')
    return out
