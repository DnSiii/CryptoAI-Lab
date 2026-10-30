#!/usr/bin/env python3
"""V98 AE independent cash-anchored max-feasible-growth 81-corner governor."""
from __future__ import annotations
import itertools
import numpy as np

CORNERS=np.array(tuple(itertools.product(range(3),repeat=4)),dtype=np.int8)
ASSET_CAP=.30
GROSS_CAP=.95
NET_CAP=.60
EQUITY_FLOOR=.30
FEE=.002
SLIPPAGE=.0035
ORDER_SHARE=.002
ENTRY_SHARE=.001
EXIT_RESERVE_MULTIPLIER=2.5


def vec(x):
    a=np.asarray(x,dtype=np.float64)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AE1208_VECTOR')
    return a


def audit(candidate,carried,opening,equity,down,up,funding_bound,prior_quote,min_quote):
    try:
        n,old,p,d,u,f,q,qmin=map(vec,
            (candidate,carried,opening,down,up,funding_bound,prior_quote,min_quote))
    except ValueError:
        return {'feasible':False,'reason':'NONFINITE_VECTOR'}
    if (not np.isfinite(equity) or equity<=0 or np.any(p<=0) or
            np.any(d<0) or np.any(d>=1) or np.any(u<0) or np.any(f<0) or
            np.any(q<0) or np.any(qmin<0)):
        return {'feasible':False,'reason':'BAD_INPUT'}
    delta=n-old
    order=np.abs(delta)*p*(1+SLIPPAGE)
    if np.any(order>ORDER_SHARE*q+1e-9):
        return {'feasible':False,'reason':'CURRENT_ORDER_CAPACITY'}
    increase=np.abs(n)>np.abs(old)+1e-12
    entry=np.abs(n)*p*(1+u)
    if np.any(increase & (entry>ENTRY_SHARE*qmin+1e-9)):
        return {'feasible':False,'reason':'ENTRY_CAPACITY'}
    if np.any(EXIT_RESERVE_MULTIPLIER*np.abs(n)*p*(1+SLIPPAGE)>
              ORDER_SHARE*qmin+1e-9):
        return {'feasible':False,'reason':'FUTURE_EXIT_RESERVE'}
    current_cost=float(np.abs(delta)@p)*(FEE+SLIPPAGE)
    future_exit_cost=float(np.abs(n)@p)*(FEE+SLIPPAGE)
    funding_cost=float(np.abs(n*p)@f)
    prices=p*np.stack((1-d,np.ones(4),1+u))[CORNERS,np.arange(4)]
    exposure=prices*n
    stressed=equity+((prices-p)*n).sum(axis=1)-current_cost-future_exit_cost-funding_cost
    if np.any(stressed<EQUITY_FLOOR*equity-1e-9):
        return {'feasible':False,'reason':'EQUITY_FLOOR'}
    if np.any(np.abs(exposure)>ASSET_CAP*stressed[:,None]+1e-9):
        return {'feasible':False,'reason':'ASSET_CONCENTRATION'}
    if np.any(np.abs(exposure).sum(axis=1)>GROSS_CAP*stressed+1e-9):
        return {'feasible':False,'reason':'GROSS_CAP'}
    if np.any(np.abs(exposure.sum(axis=1))>NET_CAP*stressed+1e-9):
        return {'feasible':False,'reason':'NET_CAP'}
    return {'feasible':True,'reason':'PASS',
            'worst_corner_equity':float(stressed.min()),
            'current_fill_cost_reserve':current_cost,
            'future_exit_cost_reserve':future_exit_cost,
            'adverse_funding_reserve':funding_cost}


def project(desired_weights,carried,opening,equity,down,up,funding_bound,
            prior_quote,min_quote):
    w,old,p=map(vec,(desired_weights,carried,opening))
    if not np.isfinite(equity) or equity<=0 or np.any(p<=0):
        raise ValueError('AE1208_EQUITY_PRICE')
    flat=audit(np.zeros(4),old,p,equity,down,up,funding_bound,
               prior_quote,min_quote)
    if not flat['feasible']:
        raise ValueError('AE1208_UNEXECUTABLE_CARRIED_EXIT_'+flat['reason'])
    target=w*equity/p
    for k in range(100,-1,-1):
        alpha=k/100.
        candidate=alpha*target
        check=audit(candidate,old,p,equity,down,up,funding_bound,
                    prior_quote,min_quote)
        if check['feasible']:
            return {'units':candidate,'fraction':alpha,'audit':check,
                    'flatten_verified':True,
                    'historical_system_pnl_computed':False}
    raise ValueError('AE1208_NO_FEASIBLE_ANCHOR')
