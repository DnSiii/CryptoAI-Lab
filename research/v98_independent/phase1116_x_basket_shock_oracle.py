#!/usr/bin/env python3
"""X preregistered all-leg basket OCO, synthetic-only, no alpha/PnL.

ANY stop triggers a preplaced full basket exit, at WORST observed bar extreme,
not at a favorable stop price. Signed funding, capacity, fees and post-book caps.
"""
from __future__ import annotations
import numpy as np
N=4
ASSET_CAP=.45;NET_CAP=.75;GROSS_CAP=1.35;FLOOR=.25;CAPACITY=.01

def vec(x):
    a=np.asarray(x,float)
    if a.shape!=(N,) or not np.isfinite(a).all():
        raise ValueError('X_SHOCK_BAD_GEOMETRY')
    return a

def execute_preplaced_basket(prevclose,opening,high,low,closing,units,cash,
                             prior_down,prior_up,prior_quote,fee,slip,
                             *,funding_rate=None,funding_mark=None,funding_event=None):
    p,o,h,l,c,u,d,a,q=[vec(x) for x in
        (prevclose,opening,high,low,closing,units,prior_down,prior_up,prior_quote)]
    if (not np.isfinite(cash) or not 0<=fee<=.02 or not 0<=slip<=.02
        or (p<=0).any() or (o<=0).any() or (l<=0).any()
        or (h<np.maximum(o,c)).any() or (l>np.minimum(o,c)).any()
        or (d<0).any() or (d>=1).any() or (a<0).any() or (q<0).any()):
        raise ValueError('X_SHOCK_INVALID_EVENT')
    rate=vec(np.zeros(N) if funding_rate is None else funding_rate)
    mark=vec(c if funding_mark is None else funding_mark)
    event=np.asarray(np.zeros(N,bool) if funding_event is None else funding_event)
    if event.shape!=(N,) or event.dtype!=bool or (mark<=0).any():
        raise ValueError('X_SHOCK_INVALID_FUNDING')
    equity0=float(cash+np.dot(u,p))
    if equity0<=0:return {'ok':False,'reason':'X_NONPOSITIVE_PRIOR_EQUITY'}
    s=np.sign(u)
    stop=np.where(s>0,p*(1-d),np.where(s<0,p*(1+a),np.nan))
    limit=np.where(s>0,p*(1+a),np.where(s<0,p*(1-d),np.nan))
    stop_hit=((s>0)&(l<=stop+1e-9))|((s<0)&(h>=stop-1e-9))
    limit_hit=((s>0)&(h>=limit-1e-9))|((s<0)&(l<=limit+1e-9))
    basket_stop=bool(np.any(stop_hit))
    new=u.copy();balance=float(cash);fees=turnover=0.;events=[]
    for j in range(N):
        if abs(u[j])<=1e-12:continue
        if basket_stop:
            qty=abs(u[j])
            px=min(o[j],l[j]) if s[j]>0 else max(o[j],h[j])
            action='BASKET_STOP_WORST_BAR'
        elif limit_hit[j]:
            qty=abs(u[j])/3.;px=limit[j];action='PARTIAL_LIMIT'
        else:continue
        delta=-s[j]*qty
        fill=px*(1+np.sign(delta)*slip)
        notional=qty*fill
        if notional>CAPACITY*q[j]+1e-8:
            return {'ok':False,'reason':'X_UNTRADEABLE_MANDATORY_EXIT','asset':j}
        new[j]+=delta
        balance-=delta*fill+fee*notional
        fees+=fee*notional;turnover+=notional
        events.append({'asset':j,'action':action,'fill_price':float(fill),
            'qty':float(qty),'stop_hit':bool(stop_hit[j]),
            'limit_hit':bool(limit_hit[j])})
    signed_funding=float(np.sum(new*mark*rate*event))
    balance-=signed_funding
    exposure=new*c
    equity=float(balance+exposure.sum())
    ok=(np.isfinite(equity) and equity>=FLOOR*equity0-1e-8
        and np.abs(exposure).max()<=ASSET_CAP*equity+1e-8
        and np.abs(exposure).sum()<=GROSS_CAP*equity+1e-8
        and abs(exposure.sum())<=NET_CAP*equity+1e-8)
    if not ok:return {'ok':False,'reason':'X_POST_BASKET_SURVIVAL',
                      'basket_stop':basket_stop}
    return {'ok':True,'basket_stop':basket_stop,'units':new,'cash':balance,
        'equity':equity,'events':events,'fees':fees,'turnover':turnover,
        'signed_funding_cash_delta':-signed_funding,
        'future_data_used_for_order_selection':False}
