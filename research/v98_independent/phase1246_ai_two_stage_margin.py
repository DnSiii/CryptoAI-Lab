#!/usr/bin/env python3
"""V98 AI1246 independent signed futures two-stage invariant collateral ledger."""
from __future__ import annotations
import itertools
import numpy as np

CORNERS=np.asarray(tuple(itertools.product(range(3),repeat=4)),dtype=int)
FEES={'base':(.0005,.0005),'severe':(.002,.003),
      'supersevere':(.005,.010)}
ORDERS=('carried_before_fill','new_after_fill')
MAINTENANCE=.18
SURVIVAL_FLOOR=.35
INVARIANT_CUSHION=.05
ORDER_SHARE=.003
EXIT_MULTIPLIER=2.2
BENIGN_NEXT_STEP=.01
FUNDING_HOURS=24

def four(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AI1246_VECTOR')
    return a

def signed_funding(units,rate,event,mark_low,mark_high):
    n,r,e,lo,hi=map(four,(units,rate,event,mark_low,mark_high))
    if np.any(lo<=0) or np.any(hi<lo) or not np.isin(e,(0.,1.)).all():
        raise ValueError('AI1246_FUNDING_MARK')
    obligation=n*r*e
    mark=np.where(obligation>=0,hi,lo)
    return -float(np.sum(obligation*mark))

def two_stage_audit(cash,units,opening,prior_down,prior_up,
                    funding_bound,exit_fee,initial_cash):
    n,p,d,u,f=map(four,(units,opening,prior_down,prior_up,funding_bound))
    if (not np.isfinite(cash) or not np.isfinite(initial_cash)
        or cash<=0 or initial_cash<=0 or np.any(p<=0)
        or np.any(d<0) or np.any(d>=1) or np.any(u<0)
        or np.any(f<0) or exit_fee<0):
        return False,'BAD_INPUT'
    corners=np.stack((p*(1-d),p,p*(1+u)))[CORNERS,np.arange(4)]
    notional=np.abs(n)[None,:]*corners
    stressed_cash=(cash+(corners-p)@n
        -FUNDING_HOURS*float(np.sum(np.abs(n*p)*f)))
    stressed_gross=notional.sum(axis=1)
    maintenance=MAINTENANCE*stressed_gross
    floor=(SURVIVAL_FLOOR+INVARIANT_CUSHION)*initial_cash
    if np.any(stressed_cash<np.maximum(maintenance,floor)-1e-8):
        return False,'FIRST_STAGE_MARGIN'
    # A single full 81-corner jump, then one further ordinary adverse
    # continuation with funded collateral and full exit friction.
    continuation=(BENIGN_NEXT_STEP+exit_fee)*stressed_gross
    second_cash=stressed_cash-continuation
    second_maintenance=MAINTENANCE*(1+BENIGN_NEXT_STEP)*stressed_gross
    if np.any(second_cash<np.maximum(second_maintenance,floor)-1e-8):
        return False,'SECOND_STAGE_VIABILITY'
    return True,'PASS'

def ai_governor(cash_previous,old_units,prior_close,opening,signed_target,
                prior_down,prior_up,funding_bound,prior_quote,min_quote,
                fee_mode='base',funding_order='carried_before_fill'):
    if fee_mode not in FEES or funding_order not in ORDERS:
        raise ValueError('AI1246_MODE')
    old,p0,p,w,d,u,f,q,qmin=map(four,(old_units,prior_close,opening,
        signed_target,prior_down,prior_up,funding_bound,prior_quote,min_quote))
    if (not np.isfinite(cash_previous) or cash_previous<=0 or
        np.any(p0<=0) or np.any(p<=0) or np.any(d<0) or np.any(d>=1)
        or np.any(u<0) or np.any(f<0) or np.any(q<0) or np.any(qmin<0)):
        raise ValueError('AI1246_BAD_INPUT')
    fee,slip=FEES[fee_mode]
    cash_open=float(cash_previous+old@(p-p0))
    if cash_open<=0:raise ValueError('AI1246_GAP_INSOLVENCY')
    ok,reason=two_stage_audit(cash_open,old,p,d,u,f,fee+slip,cash_open)
    if not ok:raise ValueError('AI1246_CARRIED_'+reason)
    worst_exit=p*(1+u)
    max_abs=ORDER_SHARE*qmin/(EXIT_MULTIPLIER*worst_exit)
    if np.any(np.abs(old)>max_abs+1e-9):
        raise ValueError('AI1246_CARRIED_EXIT_RESERVE')
    desired=w*cash_open/p
    max_delta=ORDER_SHARE*q/p
    liquid=np.clip(desired,old-max_delta,old+max_delta)
    liquid=np.clip(liquid,-max_abs,max_abs)
    def feasible(a):
        n=old+a*(liquid-old)
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if funding_order=='carried_before_fill' else n
        reserve=float(np.sum(np.abs(payer*p)*f))
        cash=cash_open-(fee+slip)*turnover-reserve
        ok,_=two_stage_audit(cash,n,p,d,u,f,fee+slip,cash_open)
        return ok,n
    ok,_=feasible(0.)
    if not ok:raise ValueError('AI1246_CARRIED_NEXT_HOUR_UNSAFE')
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
            'cash_after_gap':cash_open,'two_stage_viable':True,
            'pretrade_corners':81,'hidden_borrow':False}

def settle_hour(cash_previous,old_units,prior_close,opening,high,low,
                closing,target_units,rate,event,mark_low,mark_high,
                fee_mode='base',funding_order='carried_before_fill'):
    if fee_mode not in FEES or funding_order not in ORDERS:
        raise ValueError('AI1246_SETTLEMENT_MODE')
    old,p0,p,h,l,c,target,r,e,ml,mh=map(four,
        (old_units,prior_close,opening,high,low,closing,target_units,
         rate,event,mark_low,mark_high))
    if (not np.isfinite(cash_previous) or cash_previous<=0 or
        np.any(p0<=0) or np.any(p<=0) or np.any(l<=0) or
        np.any(l>np.minimum(p,c)) or np.any(h<np.maximum(p,c))):
        raise ValueError('AI1246_SETTLEMENT_GEOMETRY')
    fee,slip=FEES[fee_mode]
    gap=float(old@(p-p0))
    cash=float(cash_previous+gap)
    if cash<=0:raise ValueError('AI1246_GAP_BANKRUPTCY')
    funding=0.
    if funding_order=='carried_before_fill':
        funding=signed_funding(old,r,e,ml,mh)
        cash+=funding
    turnover=float(np.sum(np.abs(target-old)*p))
    fees=fee*turnover
    slippage=slip*turnover
    cash-=fees+slippage
    if funding_order=='new_after_fill':
        funding=signed_funding(target,r,e,ml,mh)
        cash+=funding
    if cash<=0:raise ValueError('AI1246_FUNDING_BANKRUPTCY')
    # Ex-post actual 81-corner intrabar audit, never used to choose target.
    corners=np.stack((l,p,h))[CORNERS,np.arange(4)]
    stress_cash=cash+(corners-p)@target
    stress_margin=MAINTENANCE*np.sum(np.abs(target)[None,:]*corners,axis=1)
    if np.any(stress_cash<stress_margin-1e-8):
        raise ValueError('AI1246_REALIZED_MAINTENANCE')
    if np.any(stress_cash<SURVIVAL_FLOOR*cash_previous-1e-8):
        raise ValueError('AI1246_REALIZED_EQUITY_FLOOR')
    pnl=float(target@(c-p))
    close_cash=float(cash+pnl)
    if close_cash<=0:raise ValueError('AI1246_CLOSE_BANKRUPTCY')
    return {'cash':close_cash,'units':target.copy(),'equity':close_cash,
            'gap_pnl':gap,'intrabar_pnl':pnl,'funding':funding,
            'turnover':turnover,'fees':fees,'slippage':slippage,
            'cash_settled':True,'hidden_borrow':False}
