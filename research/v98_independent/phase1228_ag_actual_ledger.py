#!/usr/bin/env python3
"""V98 AG actual long-only cash/inventory execution, native 8h funding and audit."""
from __future__ import annotations
import numpy as np
from phase1226_ag_atomic_portfolio import (
    joint_plan,corner_audit,CORNERS,COSTS)


ORDERS=('carried_before_fill','new_after_fill')


def native_funding(units,rate,event,mark_low,mark_high):
    units=np.asarray(units,dtype=float)
    rate=np.asarray(rate,dtype=float)
    event=np.asarray(event,dtype=float)
    if units.shape!=(4,) or rate.shape!=(4,) or event.shape!=(4,):
        raise ValueError('AG1228_FUNDING_SHAPE')
    mask=event!=0
    if not np.any(mask):
        return 0.
    lo=np.asarray(mark_low,dtype=float)[mask]
    hi=np.asarray(mark_high,dtype=float)[mask]
    r=rate[mask]
    if np.any(~np.isfinite(lo)) or np.any(~np.isfinite(hi)) or np.any(lo<=0):
        raise ValueError('AG1228_FUNDING_MARK')
    # Conservative payer: higher mark; conservative receiver: lower mark.
    price=np.where(r>=0,hi,lo)
    return -float(np.sum(units[mask]*price*r))


def execute_hour(old_units,cash,opening,high,low,closing,
                 growth_mu,cash_reserve,down,up,funding_bound,
                 prior_quote,min_quote,fee_mode,rate,event,
                 mark_low,mark_high,order,scheduled_rebalance):
    if order not in ORDERS or fee_mode not in COSTS:
        raise ValueError('AG1228_ORDER_MODE')
    old=np.asarray(old_units,dtype=float)
    p=np.asarray(opening,dtype=float)
    if old.shape!=(4,) or np.any(old<0) or np.any(p<=0) or cash<0:
        raise ValueError('AG1228_INVALID_CARRIED')
    funding=0.
    if order=='carried_before_fill':
        funding=native_funding(old,rate,event,mark_low,mark_high)
        cash+=funding
        if cash < -1e-7:
            raise ValueError('AG1228_UNFUNDED_CARRIED_FUNDING')
    fee,slip=COSTS[fee_mode]
    eq=float(cash+old@p)
    risk_prices=np.stack([1-np.asarray(down),np.ones(4),
                          1+np.asarray(up)])[CORNERS,np.arange(4)]
    ok,_=corner_audit(old*p,old*p,eq,risk_prices,
                      np.asarray(funding_bound),fee+slip,0.,
                      np.asarray(prior_quote),np.asarray(min_quote),
                      cash_floor=cash_reserve)
    if scheduled_rebalance or not ok:
        r=joint_plan(old,p,cash,growth_mu,down,up,funding_bound,
                     prior_quote,min_quote,fee_mode,cash_floor=cash_reserve)
        units=np.asarray(r['units'])
        cash=float(r['cash'])
        turnover=float(r['turnover'])
        fees=float(r['fees'])
        slippage=float(r['slippage'])
    else:
        units=old.copy()
        turnover=fees=slippage=0.
    if order=='new_after_fill':
        funding=native_funding(units,rate,event,mark_low,mark_high)
        cash+=funding
    if cash < -1e-7:
        raise ValueError('AG1228_UNFUNDED_POSTTRADE_FUNDING')
    if np.any(units<0) or not np.isfinite(cash):
        raise ValueError('AG1228_BAD_INVENTORY')
    # Realized intrabar OHLC is used ONLY for ex-post survival audit.
    actual=np.stack([np.asarray(low)/p,np.ones(4),
                     np.asarray(high)/p])[CORNERS,np.arange(4)]
    actual_ok,reason=corner_audit(units*p,old*p,eq,actual,
                    np.asarray(funding_bound),fee+slip,fee+slip,
                    np.asarray(prior_quote),np.asarray(min_quote),
                    cash_floor=0.)
    if not actual_ok:
        raise ValueError('AG1228_REALIZED_CORNER_'+reason)
    nav=float(cash+units@np.asarray(closing))
    if nav<=0 or not np.isfinite(nav):
        raise ValueError('AG1228_INSOLVENT_CLOSE')
    if abs(nav-cash-units@np.asarray(closing))>1e-6:
        raise ValueError('AG1228_NAV_MISMATCH')
    return {'units':units,'cash':cash,'nav':nav,'turnover':turnover,
            'fees':fees,'slippage':slippage,'funding':funding,
            'executed':turnover>0,'joint_survival':True}
