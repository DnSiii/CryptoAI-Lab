#!/usr/bin/env python3
"""V98 AF independent collateralized sell-then-buy 81-corner growth governor."""
from __future__ import annotations
import itertools
import numpy as np

CORNERS=np.array(tuple(itertools.product(range(3),repeat=4)),dtype=np.int8)
ASSET_CAP=.32
GROSS_CAP=.88
EQUITY_FLOOR=.35
FEE=.002
SLIPPAGE=.003
ORDER_SHARE=.0025
ENTRY_SHARE=.0015
EXIT_RESERVE_MULTIPLIER=2.2


def vec(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AF1220_VECTOR')
    return a


def audit(candidate,cash_after,opening,open_equity,down,up,
          funding_bound,prior_quote,min_quote,buy_units):
    n,p,d,u,f,q,qmin,buy=map(vec,
        (candidate,opening,down,up,funding_bound,prior_quote,min_quote,buy_units))
    if (not np.isfinite(cash_after) or cash_after<0 or
            not np.isfinite(open_equity) or open_equity<=0 or
            np.any(n<0) or np.any(p<=0) or
            np.any(d<0) or np.any(d>=1) or np.any(u<0) or
            np.any(f<0) or np.any(q<0) or np.any(qmin<0) or np.any(buy<0)):
        return {'feasible':False,'reason':'BAD_COLLATERAL_OR_INPUT'}
    if np.any(buy*p*(1+SLIPPAGE)>ORDER_SHARE*q+1e-9):
        return {'feasible':False,'reason':'BUY_ORDER_CAPACITY'}
    if np.any(buy*p*(1+u)>ENTRY_SHARE*qmin+1e-9):
        return {'feasible':False,'reason':'ENTRY_CAPACITY'}
    if np.any(EXIT_RESERVE_MULTIPLIER*n*p*(1+SLIPPAGE)>
              ORDER_SHARE*qmin+1e-9):
        return {'feasible':False,'reason':'FUTURE_EXIT_RESERVE'}
    prices=p*np.stack((1-d,np.ones(4),1+u))[CORNERS,np.arange(4)]
    exposure=prices*n
    funding_reserve=float((n*p)@f)
    exit_cost=float((n*p).sum())*(FEE+SLIPPAGE)
    stressed=cash_after+exposure.sum(axis=1)-funding_reserve-exit_cost
    if np.any(stressed<EQUITY_FLOOR*open_equity-1e-9):
        return {'feasible':False,'reason':'EQUITY_FLOOR'}
    if np.any(exposure>ASSET_CAP*stressed[:,None]+1e-9):
        return {'feasible':False,'reason':'ASSET_CONCENTRATION'}
    if np.any(exposure.sum(axis=1)>GROSS_CAP*stressed+1e-9):
        return {'feasible':False,'reason':'GROSS_CAP'}
    return {'feasible':True,'reason':'PASS',
            'worst_corner_equity':float(stressed.min()),
            'funding_reserve':funding_reserve,
            'future_exit_cost_reserve':exit_cost}


def plan(desired_weights,carried,opening,cash,down,up,
         funding_bound,prior_quote,min_quote):
    w,old,p,d,u,f,q,qmin=map(vec,
        (desired_weights,carried,opening,down,up,
         funding_bound,prior_quote,min_quote))
    if (not np.isfinite(cash) or cash<0 or np.any(old<0) or
            np.any(w<0) or w.sum()>GROSS_CAP+1e-9 or
            np.any(p<=0) or np.any(q<0) or np.any(qmin<0)):
        raise ValueError('AF1220_COLLATERAL_OR_TARGET')
    equity=float(cash+old@p)
    if equity<=0:
        raise ValueError('AF1220_INSOLVENCY')
    if np.any(old*p*(1+SLIPPAGE)>ORDER_SHARE*q+1e-9):
        raise ValueError('AF1220_UNEXECUTABLE_CARRIED_EXIT')
    target=w*equity/p
    sell=np.maximum(old-target,0)
    kept=old-sell
    sell_notional=float(sell@p)
    after_sell_cash=float(cash+sell_notional*(1-FEE-SLIPPAGE))
    buy_target=np.maximum(target-kept,0)
    sell_only=audit(kept,after_sell_cash,p,equity,d,u,f,q,qmin,np.zeros(4))
    if not sell_only['feasible']:
        raise ValueError('AF1220_UNEXECUTABLE_POST_SELL_'+sell_only['reason'])
    for k in range(100,-1,-1):
        fraction=k/100.
        buy=fraction*buy_target
        candidate=kept+buy
        buy_notional=float(buy@p)
        free_cash=after_sell_cash-buy_notional*(1+FEE+SLIPPAGE)
        if free_cash<0:
            continue
        check=audit(candidate,free_cash,p,equity,d,u,f,q,qmin,buy)
        if check['feasible']:
            turnover=sell_notional+buy_notional
            return {'units':candidate,'cash':free_cash,
                    'fraction':fraction,'turnover':turnover,
                    'fees':turnover*FEE,'slippage':turnover*SLIPPAGE,
                    'worst_corner_equity':check['worst_corner_equity'],
                    'audit':check,'fully_collateralized':True,
                    'historical_system_pnl_computed':False}
    raise ValueError('AF1220_NO_FEASIBLE_BUY')
