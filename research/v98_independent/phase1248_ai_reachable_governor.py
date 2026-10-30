#!/usr/bin/env python3
"""V98 AI1248 independent analytical 16-state forward-reachable safe set."""
from __future__ import annotations
import itertools
import numpy as np

FEES={'base':(.0005,.0005),'severe':(.002,.003),
      'supersevere':(.005,.010)}
ORDERS=('carried_before_fill','new_after_fill')
NEXT=np.asarray(tuple(itertools.product((-.01,.01),repeat=4))+
                ((0.,0.,0.,0.),),dtype=float)
ORDER_SHARE=.003
EXIT_RESERVE=2.2
FUNDING_HOURS=24
MAINTENANCE=.18
EQUITY_FLOOR=.40

def four(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AI1248_VECTOR')
    return a

def severe_safe(cash,units,opening,down,up,funding,exit_fee,initial_equity):
    n,p,d,u,f=map(four,(units,opening,down,up,funding))
    if (not np.isfinite(cash) or not np.isfinite(initial_equity) or
        cash<=0 or initial_equity<=0 or np.any(p<=0) or
        np.any(d<0) or np.any(d>=1) or np.any(u<0) or np.any(f<0)
        or exit_fee<0):
        return False,'BAD_INPUT'
    notionals=np.abs(n*p)
    loss=float(np.sum(np.where(n>=0,notionals*d,notionals*u)))
    upper=float(np.sum(notionals*(1+u)))
    reserved=float(FUNDING_HOURS*np.sum(notionals*f)+exit_fee*upper)
    stressed=cash-loss-reserved
    required=max(EQUITY_FLOOR*initial_equity,MAINTENANCE*upper)
    return (bool(stressed>=required-1e-8),
            'PASS' if stressed>=required-1e-8 else 'SEVERE_SAFE_SET')

def forward_reachable(cash,units,opening,down,up,funding,exit_fee,initial_equity):
    n,p,d,u,f=map(four,(units,opening,down,up,funding))
    ok,reason=severe_safe(cash,n,p,d,u,f,exit_fee,initial_equity)
    if not ok:return False,reason
    for shock in NEXT:
        next_p=p*(1+shock)
        next_cash=float(cash+n@(next_p-p)-np.sum(np.abs(n*next_p)*f))
        ok,_=severe_safe(next_cash,n,next_p,d,u,f,exit_fee,initial_equity)
        if not ok:return False,'NEXT_OPEN_REACHABILITY'
    return True,'PASS'

def ai_reachable_governor(cash_previous,old_units,prior_close,opening,
                          signed_target,prior_down,prior_up,funding_bound,
                          prior_quote,min_quote,fee_mode='base',
                          funding_order='carried_before_fill'):
    if fee_mode not in FEES or funding_order not in ORDERS:
        raise ValueError('AI1248_MODE')
    old,p0,p,w,d,u,f,q,qmin=map(four,
        (old_units,prior_close,opening,signed_target,prior_down,
         prior_up,funding_bound,prior_quote,min_quote))
    if (not np.isfinite(cash_previous) or cash_previous<=0 or
        np.any(p0<=0) or np.any(p<=0) or np.any(d<0) or
        np.any(d>=1) or np.any(u<0) or np.any(f<0)
        or np.any(q<0) or np.any(qmin<0)):
        raise ValueError('AI1248_INPUT')
    fee,slip=FEES[fee_mode]
    cash_open=float(cash_previous+old@(p-p0))
    if cash_open<=0:raise ValueError('AI1248_GAP_INSOLVENCY')
    ok,reason=forward_reachable(cash_open,old,p,d,u,f,fee+slip,cash_open)
    if not ok:raise ValueError('AI1248_CARRIED_'+reason)
    worst_exit=p*(1+u)
    max_abs=ORDER_SHARE*qmin/(EXIT_RESERVE*worst_exit)
    if np.any(np.abs(old)>max_abs+1e-9):
        raise ValueError('AI1248_CARRIED_EXIT_DEPTH')
    desired=w*cash_open/p
    max_delta=ORDER_SHARE*q/p
    liquid=np.clip(desired,old-max_delta,old+max_delta)
    liquid=np.clip(liquid,-max_abs,max_abs)
    def feasible(alpha):
        n=old+alpha*(liquid-old)
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if funding_order=='carried_before_fill' else n
        reserved=float(np.sum(np.abs(payer*p)*f))
        cash=cash_open-(fee+slip)*turnover-reserved
        ok,_=forward_reachable(cash,n,p,d,u,f,fee+slip,cash_open)
        return ok,n
    ok,_=feasible(0.)
    if not ok:raise ValueError('AI1248_CARRIED_FUNDING_UNSAFE')
    ok,n=feasible(1.)
    alpha=1.
    if not ok:
        lo,hi=0.,1.
        for _ in range(28):
            mid=(lo+hi)/2.
            valid,_=feasible(mid)
            if valid:lo=mid
            else:hi=mid
        alpha=lo
        _,n=feasible(alpha)
    return {'units':n.copy(),'fraction':float(alpha),
            'cash_after_gap':cash_open,'forward_reachable':True,
            'next_open_scenarios':len(NEXT),'hidden_borrow':False}
