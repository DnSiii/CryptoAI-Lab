#!/usr/bin/env python3
"""X causal 12h opening targets + full basket contingency; synthetic only."""
from __future__ import annotations
import numpy as np
from phase1116_x_basket_shock_oracle import execute_preplaced_basket,vec
N=4

def execute_hour(prevclose,opening,high,low,closing,carried_units,desired_weights,
                 cash,prior_down,prior_up,prior_quote,fee,slip,*,rebalance,
                 funding_rate,funding_mark,funding_event):
    p,o,h,l,c,u,w,d,a,q=[vec(x) for x in
        (prevclose,opening,high,low,closing,carried_units,desired_weights,
         prior_down,prior_up,prior_quote)]
    if ((p<=0).any() or (o<=0).any() or not np.isfinite(cash)
        or not 0<=fee<=.02 or not 0<=slip<=.02 or (q<0).any()):
        raise ValueError('X_HOURLY_INVALID_PRIOR')
    equity0=float(cash+np.dot(u,p))
    if equity0<=0:return {'ok':False,'reason':'X_PRIOR_EQUITY_NONPOSITIVE'}
    target=w*equity0/p if rebalance else u.copy()
    units=u.copy();balance=float(cash);fees=turnover=0.;events=[]
    def fill(j,delta,action):
        nonlocal balance,fees,turnover
        if abs(delta)<1e-12:return True
        px=o[j]*(1+np.sign(delta)*slip);notion=abs(delta)*px
        if notion>.01*q[j]+1e-8:return False
        balance-=delta*px+fee*notion
        fees+=fee*notion;turnover+=notion;units[j]+=delta
        events.append({'asset':j,'action':action,'delta_units':float(delta),
                       'fill_price':float(px)})
        return True
    for j in range(N):
        if not rebalance:continue
        reversal=(abs(u[j])>1e-12 and abs(target[j])>1e-12
                  and np.sign(u[j])!=np.sign(target[j]))
        side=np.sign(u[j]) if abs(u[j])>1e-12 else np.sign(target[j])
        stop=p[j]*(1-d[j]) if side>0 else p[j]*(1+a[j])
        gap=(side>0 and o[j]<=stop+1e-9) or (side<0 and o[j]>=stop-1e-9)
        if reversal:
            if not fill(j,-u[j],'ATOMIC_REVERSAL_FLAT'):
                return {'ok':False,'reason':'X_OPEN_CAPACITY'}
        elif gap:
            if abs(u[j])<=1e-12:
                events.append({'asset':j,'action':'SKIP_GAP_ENTRY'})
        else:
            if not fill(j,target[j]-u[j],'OPEN_TARGET'):
                return {'ok':False,'reason':'X_OPEN_CAPACITY'}
    protective=execute_preplaced_basket(p,o,h,l,c,units,balance,d,a,q,fee,slip,
        funding_rate=funding_rate,funding_mark=funding_mark,
        funding_event=funding_event)
    if not protective['ok']:
        return {'ok':False,'reason':protective['reason']}
    return {'ok':True,'units':protective['units'],'cash':protective['cash'],
        'equity':protective['equity'],'events':events+protective['events'],
        'fees':fees+protective['fees'],'turnover':turnover+protective['turnover'],
        'basket_stop':protective['basket_stop'],
        'signed_funding_cash_delta':protective['signed_funding_cash_delta']}
