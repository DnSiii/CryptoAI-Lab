#!/usr/bin/env python3
"""V98 Independent AH cash-settled signed USD-M variation margin (not AG spot LP)."""
from __future__ import annotations
import itertools
import numpy as np

CORNERS=np.asarray(tuple(itertools.product(range(3),repeat=4)),dtype=int)
FEE_MODES={'base':(.0005,.0005),'severe':(.002,.003),
           'supersevere':(.005,.010)}
ORDERS=('carried_before_fill','new_after_fill')
MAINTENANCE_RATE=.18
EQUITY_FLOOR=.35
ORDER_SHARE=.003
EXIT_RESERVE_MULTIPLIER=2.2


def four(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError('AH1234_VECTOR')
    return a


def funding_delta(units,rate,event,mark_low,mark_high):
    n,r,e=four(units),four(rate),four(event)
    mask=e!=0
    if not np.any(mask):return 0.
    lo,hi=four(mark_low)[mask],four(mark_high)[mask]
    if np.any(lo<=0) or np.any(hi<lo):
        raise ValueError('AH1234_MARK')
    # Signed futures: positive funding pays longs, credits shorts.
    # Negative funding credits longs, charges shorts. Adverse mark bound
    # follows the sign of units*rate, not just the sign of rate.
    obligation=n[mask]*r[mask]
    mark=np.where(obligation>=0,hi,lo)
    return -float(np.sum(obligation*mark))


def scenario_audit(cash_open,units,opening,low,high,fee_exit,
                   funding_bound,initial_equity):
    n,p,l,h,f=map(four,(units,opening,low,high,funding_bound))
    if cash_open<=0 or initial_equity<=0 or np.any(p<=0) or np.any(l<=0) or np.any(h<l):
        return False,'BAD_MARGIN_INPUT'
    prices=np.stack([l,p,h])[CORNERS,np.arange(4)]
    pnl=(prices-p)@n
    stressed=cash_open+pnl-np.abs(n*p)@f-fee_exit*np.abs(n*p).sum()
    maintenance=MAINTENANCE_RATE*np.sum(np.abs(n)*prices,axis=1)
    if np.any(stressed<maintenance-1e-7):
        return False,'MAINTENANCE_MARGIN'
    if np.any(stressed<EQUITY_FLOOR*initial_equity-1e-7):
        return False,'EQUITY_FLOOR'
    return True,'PASS'


def settle_hour(cash_previous,old_units,prior_close,opening,high,low,closing,
                desired_units,prior_quote,min_quote,down,up,
                funding_bound,rate,event,mark_low,mark_high,
                fee_mode='base',order='carried_before_fill'):
    if fee_mode not in FEE_MODES or order not in ORDERS:
        raise ValueError('AH1234_MODE')
    old,p0,p,h,l,c,target=map(four,
        (old_units,prior_close,opening,high,low,closing,desired_units))
    q,qmin,d,u,f,r,e=map(four,
        (prior_quote,min_quote,down,up,funding_bound,rate,event))
    if (not np.isfinite(cash_previous) or cash_previous<=0 or
        np.any(p0<=0) or np.any(p<=0) or np.any(l<=0) or
        np.any(q<0) or np.any(qmin<0) or np.any(d<0) or np.any(d>=1) or
        np.any(u<0) or np.any(f<0)):
        raise ValueError('AH1234_BAD_COLLATERAL')
    if np.any(l>np.minimum(p,c)) or np.any(h<np.maximum(p,c)):
        raise ValueError('AH1234_BAD_OHLC_GEOMETRY')
    fee,slip=FEE_MODES[fee_mode]
    # Old futures settle overnight open gap into real cash; no spot notional
    # purchases, no unrealized PnL hidden outside the account.
    cash=float(cash_previous+old@(p-p0))
    if cash<=0:raise ValueError('AH1234_OVERNIGHT_MARGIN_INSOLVENCY')
    funding=0.
    if order=='carried_before_fill':
        funding=funding_delta(old,r,e,mark_low,mark_high)
        cash+=funding
        if cash<=0:raise ValueError('AH1234_CARRIED_FUNDING_INSOLVENCY')
    initial_equity=cash
    delta=target-old
    notionals=np.abs(delta)*p
    if np.any(notionals>ORDER_SHARE*q+1e-8):
        raise ValueError('AH1234_ORDER_CAPACITY')
    worst_exit=np.maximum(p*(1+u),p*(1-d))
    if np.any(EXIT_RESERVE_MULTIPLIER*np.abs(target)*worst_exit>
              ORDER_SHARE*qmin+1e-8):
        raise ValueError('AH1234_FUTURE_EXIT_RESERVE')
    turnover=float(notionals.sum())
    fees=fee*turnover
    slippage=slip*turnover
    cash-=fees+slippage
    if order=='new_after_fill':
        funding=funding_delta(target,r,e,mark_low,mark_high)
        cash+=funding
    if cash<=0:raise ValueError('AH1234_TRADE_FUNDING_INSOLVENCY')
    ok,reason=scenario_audit(cash,target,p,l,h,fee+slip,f,initial_equity)
    if not ok:raise ValueError('AH1234_REALIZED_'+reason)
    close_pnl=float(target@(c-p))
    cash_close=cash+close_pnl
    if cash_close<=0:raise ValueError('AH1234_CLOSE_INSOLVENCY')
    if not np.isclose(cash_close,cash+target@(c-p),atol=1e-7,rtol=0):
        raise ValueError('AH1234_VARIATION_RECONCILIATION')
    return {'cash':float(cash_close),'units':target.copy(),
            'equity':float(cash_close),'overnight_pnl':float(old@(p-p0)),
            'intrabar_pnl':close_pnl,'turnover':turnover,
            'fees':fees,'slippage':slippage,'funding':funding,
            'maintenance_at_close':MAINTENANCE_RATE*float(np.abs(target*c).sum()),
            'cash_settled':True,'hidden_borrow':False}
