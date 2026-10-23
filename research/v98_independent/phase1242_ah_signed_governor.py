#!/usr/bin/env python3
"""V98 Independent AH1242 prior-only 81-corner signed collateral governor."""
from __future__ import annotations
import numpy as np
from phase1234_ah_signed_variation_margin import (
    FEE_MODES,ORDERS,ORDER_SHARE,EXIT_RESERVE_MULTIPLIER,scenario_audit,four)

def ah_governor_target(cash_previous,old_units,prior_close,opening,
                       signed_target,prior_down,prior_up,funding_bound,
                       prior_quote,min_quote,fee_mode='base',
                       order='carried_before_fill'):
    if fee_mode not in FEE_MODES or order not in ORDERS:
        raise ValueError('AH1242_MODE')
    old,p0,p,w,d,u,f,q,qmin=map(four,
        (old_units,prior_close,opening,signed_target,prior_down,
         prior_up,funding_bound,prior_quote,min_quote))
    if (not np.isfinite(cash_previous) or cash_previous<=0
        or np.any(p0<=0) or np.any(p<=0) or np.any(d<0)
        or np.any(d>=1) or np.any(u<0) or np.any(f<0)
        or np.any(q<0) or np.any(qmin<0)):
        raise ValueError('AH1242_BAD_INPUT')
    fee,slip=FEE_MODES[fee_mode]
    cash_open=float(cash_previous+old@(p-p0))
    if cash_open<=0:
        raise ValueError('AH1242_GAP_INSOLVENCY')
    lo=p*(1-d)
    hi=p*(1+u)
    exit_fee=fee+slip
    # Carried inventory cannot be made fictitiously safe by pretending to
    # close before the observed opening gap or by ignoring its margin.
    carried_ok,carried_reason=scenario_audit(
        cash_open,old,p,lo,hi,exit_fee,f,cash_open)
    if not carried_ok:
        raise ValueError('AH1242_CARRIED_'+carried_reason)
    worst_exit=p*(1+u)
    max_abs=ORDER_SHARE*qmin/(EXIT_RESERVE_MULTIPLIER*worst_exit)
    if np.any(np.abs(old)>max_abs+1e-9):
        raise ValueError('AH1242_CARRIED_EXIT_LIQUIDITY')
    desired=w*cash_open/p
    max_delta=ORDER_SHARE*q/p
    liquidity_target=np.clip(desired,old-max_delta,old+max_delta)
    liquidity_target=np.clip(liquidity_target,-max_abs,max_abs)
    def feasible(alpha):
        target=old+alpha*(liquidity_target-old)
        turnover=float(np.sum(np.abs(target-old)*p))
        if np.any(np.abs(target-old)*p>ORDER_SHARE*q+1e-8):
            return False,target
        cash=cash_open-(fee+slip)*turnover
        # Conservative reserve for whichever units can pay native funding.
        # The realized event is charged separately by the actual ledger.
        payer=old if order=='carried_before_fill' else target
        cash-=float(np.sum(np.abs(payer*p)*f))
        if cash<=0:
            return False,target
        ok,_=scenario_audit(cash,target,p,lo,hi,exit_fee,f,cash_open)
        return bool(ok),target
    ok0,_=feasible(0.)
    if not ok0:
        raise ValueError('AH1242_CARRIED_FUNDING_UNSAFE')
    ok,target=feasible(1.)
    alpha=1.
    if not ok:
        left,right=0.,1.
        for _ in range(24):
            mid=(left+right)/2
            good,_=feasible(mid)
            if good:left=mid
            else:right=mid
        alpha=left
        _,target=feasible(alpha)
    if not np.isfinite(target).all():
        raise ValueError('AH1242_NONFINITE')
    return {'units':target.copy(),'fraction':float(alpha),
            'desired_units':desired.copy(),
            'liquidity_target':liquidity_target.copy(),
            'cash_after_gap':cash_open,
            'prior_only':True,'collateralized':True,
            'pretrade_corners':81}
