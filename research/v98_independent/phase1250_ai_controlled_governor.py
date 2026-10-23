#!/usr/bin/env python3
"""V98 AI1250 actual-open controlled viability with funded executable reduction."""
from __future__ import annotations
import numpy as np

FEES={'base':(.0005,.0005),'severe':(.002,.003),
      'supersevere':(.005,.010)}
ORDERS=('carried_before_fill','new_after_fill')
ORDER_SHARE=.003
EXIT_RESERVE=2.2
MAINTENANCE=.18
OPEN_FLOOR=.35
FUTURE_FLOOR=.40
FUNDING_HOURS=24
CONTINUATION=.01

def four(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AI1250_VECTOR')
    return a

def future_safe(cash,units,opening,down,up,funding,exit_fee,initial_equity):
    n,p,d,u,f=map(four,(units,opening,down,up,funding))
    if (not np.isfinite(cash) or not np.isfinite(initial_equity)
        or cash<=0 or initial_equity<=0 or np.any(p<=0)
        or np.any(d<0) or np.any(d>=1) or np.any(u<0)
        or np.any(f<0) or exit_fee<0):
        return False,'BAD_INPUT'
    notionals=np.abs(n*p)
    directional_loss=float(np.sum(np.where(n>=0,notionals*d,notionals*u)))
    upper=float(np.sum(notionals*(1+u)))
    funding_reserve=FUNDING_HOURS*float(np.sum(notionals*f))
    exit_and_next=(exit_fee+CONTINUATION)*upper
    worst_cash=cash-directional_loss-funding_reserve-exit_and_next
    required=max(FUTURE_FLOOR*initial_equity,
                 MAINTENANCE*(1+CONTINUATION)*upper)
    return (bool(worst_cash>=required-1e-8),
            'PASS' if worst_cash>=required-1e-8 else 'FUTURE_SAFE_SET')

def ai_controlled_governor(cash_previous,old_units,prior_close,opening,
                           signed_target,prior_down,prior_up,funding_bound,
                           prior_quote,min_quote,fee_mode='base',
                           funding_order='carried_before_fill'):
    if fee_mode not in FEES or funding_order not in ORDERS:
        raise ValueError('AI1250_MODE')
    old,p0,p,w,d,u,f,q,qmin=map(four,(old_units,prior_close,opening,
        signed_target,prior_down,prior_up,funding_bound,prior_quote,min_quote))
    if (not np.isfinite(cash_previous) or cash_previous<=0
        or np.any(p0<=0) or np.any(p<=0) or np.any(d<0)
        or np.any(d>=1) or np.any(u<0) or np.any(f<0)
        or np.any(q<0) or np.any(qmin<0)):
        raise ValueError('AI1250_INPUT')
    fee,slip=FEES[fee_mode]
    cash_gap=float(cash_previous+old@(p-p0))
    if cash_gap<=0:raise ValueError('AI1250_REAL_GAP_BANKRUPTCY')
    current_margin=MAINTENANCE*float(np.sum(np.abs(old*p)))
    if cash_gap<max(current_margin,OPEN_FLOOR*cash_previous)-1e-8:
        raise ValueError('AI1250_REAL_OPEN_INSOLVENCY')
    max_delta=ORDER_SHARE*q/p
    max_abs=ORDER_SHARE*qmin/(EXIT_RESERVE*p*(1+u))
    desired=w*cash_gap/p
    desired=np.clip(desired,old-max_delta,old+max_delta)
    desired=np.clip(desired,-max_abs,max_abs)
    def feasible(n):
        if (np.any(np.abs(n-old)*p>ORDER_SHARE*q+1e-8)
            or np.any(np.abs(n)>max_abs+1e-9)):
            return False
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if funding_order=='carried_before_fill' else n
        reserve=float(np.sum(np.abs(payer*p)*f))
        cash=cash_gap-(fee+slip)*turnover-reserve
        ok,_=future_safe(cash,n,p,d,u,f,fee+slip,cash_gap)
        return bool(ok)
    if feasible(old):
        anchor=old.copy()
        reduced=False
    else:
        # This is an actual t-open executable reduction, never a fictional
        # exit before the overnight gap or beyond prior quote capacity.
        anchor=old-np.sign(old)*np.minimum(np.abs(old),max_delta)
        if not feasible(anchor):
            raise ValueError('AI1250_NO_REACHABLE_SAFE_REDUCTION')
        reduced=True
    if feasible(desired):
        n=desired
        alpha=1.
    else:
        lo,hi=0.,1.
        for _ in range(28):
            mid=(lo+hi)/2.
            trial=anchor+mid*(desired-anchor)
            if feasible(trial):lo=mid
            else:hi=mid
        alpha=lo
        n=anchor+alpha*(desired-anchor)
        if not feasible(n):
            raise ValueError('AI1250_NUMERIC_FEASIBILITY')
    return {'units':n.copy(),'fraction':float(alpha),
            'cash_after_gap':cash_gap,'real_open_solvent':True,
            'controlled_reduction':bool(reduced),
            'future_safe':True,'hidden_borrow':False}
