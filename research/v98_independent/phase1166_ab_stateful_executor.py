#!/usr/bin/env python3
"""AB actual-equity inventory executor with t-1 intents and native funding.
No fictitious forced fills. Source-only until independent economic freeze.
"""
from __future__ import annotations
import numpy as np
from phase1165_ab_stateful_allocator import (CORNERS,ASSET_CAP,NET_CAP,
    GROSS_CAP,FLOOR,ORDER_FRACTION,SLIPPAGE,gate,allocate,vec)
FEES={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')

def signed_mark(units,rate,bounds,event,close):
    u=vec(units);r=vec(rate);c=vec(close)
    b=np.asarray(bounds,float);e=np.asarray(event,bool)
    if (b.shape!=(4,2) or e.shape!=(4,) or not np.isfinite(b[e]).all()
        or (b[e]<=0).any() or (b[e,0]>b[e,1]).any()):
        raise ValueError('AB1166_NATIVE_MARK')
    return np.where(e,np.where(u*r>=0,b[:,1],b[:,0]),c)

def actual_corners(cash,units,low,opening,high,prior_equity,funding_debit):
    p=np.stack([vec(low),vec(opening),vec(high)])
    u=vec(units)
    if ((p<=0).any() or prior_equity<=0 or funding_debit<0
        or not np.isfinite(cash+prior_equity+funding_debit)):
        raise ValueError('AB1166_CORNERS_INPUT')
    ex=p[CORNERS,np.arange(4)]*u
    eq=cash+ex.sum(axis=1)-funding_debit
    reason=None
    if np.any(eq<FLOOR*prior_equity-1e-8):reason='AB1166_EQUITY_FLOOR'
    elif np.any(np.abs(ex)>ASSET_CAP*eq[:,None]+1e-8):reason='AB1166_ASSET_CONCENTRATION'
    elif np.any(np.abs(ex).sum(axis=1)>GROSS_CAP*eq+1e-8):reason='AB1166_GROSS_EXPOSURE'
    elif np.any(np.abs(ex.sum(axis=1))>NET_CAP*eq+1e-8):reason='AB1166_NET_EXPOSURE'
    return {'ok':reason is None,'reason':reason,'worst_equity':float(eq.min())}

def execute_hour(prior,opening,high,low,closing,carried_units,cash,intent,cov,
                 prior_down,prior_up,prior_funding_bound,prior_quote,prior_min336,
                 *,fee,order,funding_rate,funding_mark_bounds,funding_event,
                 rebalance=True):
    p,o,h,l,c,old,mu,d,u,f,q,qmin,rate=[vec(x) for x in (
        prior,opening,high,low,closing,carried_units,intent,prior_down,
        prior_up,prior_funding_bound,prior_quote,prior_min336,funding_rate)]
    ev=np.asarray(funding_event,bool)
    if (ev.shape!=(4,) or fee not in FEES.values() or order not in ORDERS
        or (p<=0).any() or (o<=0).any() or (c<=0).any() or (l<=0).any()
        or (h<np.maximum(o,c)).any() or (l>np.minimum(o,c)).any()
        or (q<0).any() or (qmin<0).any() or not np.isfinite(cash)):
        raise ValueError('AB1166_INVALID_SOURCE')
    equity=float(cash+np.dot(old,p))
    if equity<=0:return {'ok':False,'reason':'AB1166_PRIOR_EQUITY'}
    if rebalance or not gate(old,old,p,equity,d,u,f,q,qmin):
        try:
            target=allocate(mu if rebalance else np.zeros(4),cov,old,p,equity,d,u,f,q,qmin)
        except ValueError as exc:
            return {'ok':False,'reason':str(exc)}
    else:target=old.copy()
    stop=p*np.where(old>=0,1-d,1+u)
    gap=bool(np.any(((old>1e-12)&(o<=stop))|((old<-1e-12)&(o>=stop))))
    if gap:target=np.zeros(4)
    delta=target-old
    fill=o*(1+np.sign(delta)*SLIPPAGE)
    notion=np.abs(delta)*fill
    if np.any(notion>ORDER_FRACTION*q+1e-8):
        return {'ok':False,'reason':'AB1166_UNEXECUTABLE_GAP_EXIT' if gap else 'AB1166_OPEN_CAPACITY'}
    balance=float(cash-np.dot(delta,fill)-fee*notion.sum())
    units=target.copy()
    funded=old if order=='carried_before_fill' else units
    mark=signed_mark(funded,rate,funding_mark_bounds,ev,c)
    funding_cash=-np.where(ev,funded*mark*rate,0.)
    if gap:funding_cash=np.minimum(funding_cash,0.)
    debit=float(np.maximum(-funding_cash,0.).sum())
    corner=actual_corners(balance,units,l,o,h,equity,debit)
    if not corner['ok']:return {'ok':False,'reason':corner['reason']}
    balance+=float(funding_cash.sum())
    nav=float(balance+np.dot(units,c))
    if not np.isfinite(nav) or nav<=0:return {'ok':False,'reason':'AB1166_FINAL_EQUITY'}
    return {'ok':True,'reason':None,'units':units,'cash':balance,'equity':nav,
        'fees':float(fee*notion.sum()),'turnover':float(notion.sum()),
        'funding_cash_delta':float(funding_cash.sum()),'gap_exit':gap,
        'opening_fill':fill,'self_financing':True,'synthetic_only':True}
