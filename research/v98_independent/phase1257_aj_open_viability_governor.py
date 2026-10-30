#!/usr/bin/env python3
"""V98 Independent AJ1257: actual-open cash-funded signed viability governor."""
from __future__ import annotations
import numpy as np

FEES={'base':(.0005,.0005),'severe':(.002,.003),
      'supersevere':(.005,.010)}
ORDERS=('carried_before_fill','new_after_fill')
SHARE=.003
EXIT_RESERVE=2.2
MAINTENANCE=.18
SURVIVAL_FLOOR=.40
FUNDING_HOURS=24

def four(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AJ1257_VECTOR')
    return a

def future_safe(cash,units,opening,down,up,funding,exit_friction,opening_cash,
                previous_cash):
    n,p,d,u,f=map(four,(units,opening,down,up,funding))
    if (not np.isfinite(cash) or not np.isfinite(opening_cash) or
        not np.isfinite(previous_cash) or cash<=0 or
        opening_cash<=0 or previous_cash<=0 or np.any(p<=0) or
        np.any(d<0) or np.any(d>=1) or np.any(u<0) or
        np.any(f<0) or exit_friction<0):
        return False
    notionals=np.abs(n*p)
    worst_loss=float(np.sum(np.where(n>=0,notionals*d,notionals*u)))
    stressed_gross=float(np.sum(notionals*(1+u)))
    reserve=FUNDING_HOURS*float(np.sum(notionals*f))
    exit_reserve=exit_friction*stressed_gross
    remaining=cash-worst_loss-reserve-exit_reserve
    required=max(SURVIVAL_FLOOR*opening_cash,
                 SURVIVAL_FLOOR*previous_cash,
                 MAINTENANCE*stressed_gross)
    return bool(remaining>=required-1e-8)

def aj_governor(cash_previous,old_units,prior_close,opening,signed_target,
                prior_down,prior_up,funding_bound,prior_quote,min_quote,
                fee_mode='base',funding_order='carried_before_fill'):
    if fee_mode not in FEES or funding_order not in ORDERS:
        raise ValueError('AJ1257_MODE')
    old,p0,p,w,d,u,f,q,qmin=map(four,(old_units,prior_close,opening,
        signed_target,prior_down,prior_up,funding_bound,prior_quote,min_quote))
    if (not np.isfinite(cash_previous) or cash_previous<=0 or
        np.any(p0<=0) or np.any(p<=0) or np.any(d<0) or
        np.any(d>=1) or np.any(u<0) or np.any(f<0) or
        np.any(q<0) or np.any(qmin<0)):
        raise ValueError('AJ1257_INPUT')
    cash_gap=float(cash_previous+old@(p-p0))
    if cash_gap<=0:
        raise ValueError('AJ1257_REAL_GAP_BANKRUPTCY')
    if cash_gap<max(MAINTENANCE*float(np.sum(np.abs(old*p))),
                    SURVIVAL_FLOOR*cash_previous)-1e-8:
        raise ValueError('AJ1257_REAL_OPEN_INSOLVENCY')
    fee,slip=FEES[fee_mode]
    max_delta=SHARE*np.minimum(q,qmin)/p
    max_abs=SHARE*qmin/(EXIT_RESERVE*p*(1+u))
    desired=w*cash_gap/p
    desired=np.clip(desired,old-max_delta,old+max_delta)
    desired=np.clip(desired,-max_abs,max_abs)

    def feasible(n):
        if (np.any(np.abs(n-old)>max_delta+1e-10) or
            np.any(np.abs(n)>max_abs+1e-10)):
            return False
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if funding_order=='carried_before_fill' else n
        funding_reserve=float(np.sum(np.abs(payer*p)*f))
        funded_cash=cash_gap-(fee+slip)*turnover-funding_reserve
        return future_safe(funded_cash,n,p,d,u,f,fee+slip,
                           cash_gap,cash_previous)

    if feasible(old):
        anchor=old.copy()
        reduced=False
    else:
        # The only allowed escape is an ACTUAL OPEN order bounded by
        # prior quote capacity. Never invent an exit before a gap.
        anchor=old-np.sign(old)*np.minimum(np.abs(old),max_delta)
        if not feasible(anchor):
            raise ValueError('AJ1257_NO_REACHABLE_SAFE_REDUCTION')
        reduced=True
    if feasible(desired):
        result=desired.copy()
        alpha=1.
    else:
        lo,hi=0.,1.
        for _ in range(32):
            mid=(lo+hi)/2.
            trial=anchor+mid*(desired-anchor)
            if feasible(trial):
                lo=mid
            else:
                hi=mid
        alpha=lo
        result=anchor+alpha*(desired-anchor)
        if not feasible(result):
            raise ValueError('AJ1257_NUMERIC_FEASIBILITY')
    return {'units':result.copy(),'fraction':float(alpha),
            'cash_after_gap':cash_gap,'real_open_solvent':True,
            'controlled_reduction':bool(reduced),
            'future_safe':True,'hidden_borrow':False}
