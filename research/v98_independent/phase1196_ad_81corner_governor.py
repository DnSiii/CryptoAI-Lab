#!/usr/bin/env python3
"""AD executable 81-corner survival constraints, no assumed stop/exit fills."""
from __future__ import annotations
import itertools
import numpy as np

CORNERS=np.asarray(tuple(itertools.product(range(3),repeat=4)),dtype=np.int8)
ASSET_CAP=.35
GROSS_CAP=1.15
NET_CAP=.65
EQUITY_FLOOR=.35
FEE=.002
SLIPPAGE=.003
ORDER_SHARE=.003
ENTRY_SHARE=.0015
EXIT_RESERVE_MULTIPLIER=2.


def vector(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AD1196_VECTOR')
    return a


def feasible(candidate,carried,price,equity,down,up,funding_bound,prior_quote,min_quote):
    try:
        n,old,p,d,u,f,q,qmin=map(vector,
            (candidate,carried,price,down,up,funding_bound,prior_quote,min_quote))
    except ValueError:
        return False
    if (not np.isfinite(equity) or equity<=0 or np.any(p<=0) or
            np.any((d<0)|(d>=1)) or np.any(u<0) or np.any(f<0) or
            np.any(q<0) or np.any(qmin<0)):
        return False
    order=np.abs(n-old)*p*(1+SLIPPAGE)
    if np.any(order>ORDER_SHARE*q+1e-9):
        return False
    increase=np.abs(n)>np.abs(old)+1e-12
    stressed_entry=np.abs(n)*p*(1+u)
    if np.any(increase & (stressed_entry>ENTRY_SHARE*qmin+1e-9)):
        return False
    if np.any(increase & (EXIT_RESERVE_MULTIPLIER*stressed_entry>ORDER_SHARE*qmin+1e-9)):
        return False
    prices=p*np.stack((1-d,np.ones(4),1+u))[CORNERS,np.arange(4)]
    exposures=prices*n
    costs=(FEE+SLIPPAGE)*np.sum(np.abs(n-old)*p)
    adverse_funding=np.sum(np.abs(n*p)*f)
    stressed_equity=equity+((prices-p)*n).sum(axis=1)-costs-adverse_funding
    if np.any(stressed_equity<EQUITY_FLOOR*equity-1e-9):
        return False
    if np.any(np.abs(exposures)>ASSET_CAP*stressed_equity[:,None]+1e-9):
        return False
    if np.any(np.abs(exposures).sum(axis=1)>GROSS_CAP*stressed_equity+1e-9):
        return False
    if np.any(np.abs(exposures.sum(axis=1))>NET_CAP*stressed_equity+1e-9):
        return False
    return True


def propose(desired_weights,carried,price,equity,down,up,funding_bound,prior_quote,min_quote):
    w=vector(desired_weights)
    old=vector(carried)
    p=vector(price)
    if not np.isfinite(equity) or equity<=0 or np.any(p<=0):
        raise ValueError('AD1196_EQUITY_PRICE')
    target=w*equity/p
    for k in range(100,-1,-1):
        alpha=k/100.
        candidate=old+alpha*(target-old)
        if feasible(candidate,old,p,equity,down,up,funding_bound,prior_quote,min_quote):
            return candidate,alpha
    raise ValueError('AD1196_UNEXECUTABLE_CARRIED_INVENTORY')
