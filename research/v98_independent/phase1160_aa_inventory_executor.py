#!/usr/bin/env python3
"""AA inventory-unit OHLC/funding executor; source-only synthetic, no PnL."""
from __future__ import annotations
import numpy as np
from phase1156_aa_exit_reserve_governor import (CORNERS,ASSET_CAP,GROSS_CAP,
    NET_CAP,EQUITY_FLOOR,ENTRY_PARTICIPATION,EXIT_RESERVE,SLIPPAGE,gate,allocate)
FEE_TIERS={'base':.0007,'severe':.0012,'supersevere':.002}
FUNDING_ORDERS=('carried_before_fill','new_after_fill')

def vec(x,name):
    a=np.asarray(x,float)
    if a.shape!=(4,) or not np.isfinite(a).all():raise ValueError('AA1160_BAD_'+name)
    return a

def corners(cash,units,low,open_,high,prior_equity,adverse_funding=0.):
    u=vec(units,'UNITS')
    p=np.stack([vec(low,'LOW'),vec(open_,'OPEN'),vec(high,'HIGH')])
    if ((p<=0).any() or not np.isfinite(cash+prior_equity+adverse_funding)
        or prior_equity<=0 or adverse_funding<0):raise ValueError('AA1160_BAD_CORNERS')
    exposure=p[CORNERS,np.arange(4)]*u
    equity=cash+exposure.sum(axis=1)-adverse_funding
    reason=None
    if np.any(equity<EQUITY_FLOOR*prior_equity-1e-8):reason='AA1160_EQUITY_FLOOR'
    elif np.any(np.abs(exposure)>ASSET_CAP*equity[:,None]+1e-8):reason='AA1160_ASSET_CONCENTRATION'
    elif np.any(np.abs(exposure).sum(axis=1)>GROSS_CAP*equity+1e-8):reason='AA1160_GROSS_EXPOSURE'
    elif np.any(np.abs(exposure.sum(axis=1))>NET_CAP*equity+1e-8):reason='AA1160_NET_EXPOSURE'
    return {'ok':reason is None,'reason':reason,'worst_equity':float(equity.min())}

def signed_mark(units,rate,bounds,event,close):
    u=vec(units,'UNITS');r=vec(rate,'RATE');c=vec(close,'CLOSE')
    m=np.asarray(bounds,float);ev=np.asarray(event,bool)
    if (m.shape!=(4,2) or ev.shape!=(4,) or
        not np.isfinite(m[ev]).all() or (m[ev]<=0).any() or
        (m[ev,0]>m[ev,1]).any()):raise ValueError('AA1160_BAD_SIGNED_MARK')
    return np.where(ev,np.where(u*r>=0,m[:,1],m[:,0]),c)

def execute_hour(prior,opening,high,low,closing,carried_units,desired_weights,
                 cash,prior_down,prior_up,prior_funding_bound,prior_quote,
                 prior_min72_quote,*,fee,order,funding_rate,funding_mark_bounds,
                 funding_event,rebalance=True):
    p,o,h,l,c,u,w,d,a,f,q,qmin,rate=[vec(x,k) for x,k in (
        (prior,'PRIOR'),(opening,'OPEN'),(high,'HIGH'),(low,'LOW'),
        (closing,'CLOSE'),(carried_units,'UNITS'),(desired_weights,'TARGET'),
        (prior_down,'DOWN'),(prior_up,'UP'),(prior_funding_bound,'FUNDING_BOUND'),
        (prior_quote,'QUOTE'),(prior_min72_quote,'MIN72'),(funding_rate,'RATE'))]
    ev=np.asarray(funding_event,bool)
    if (ev.shape!=(4,) or order not in FUNDING_ORDERS or fee not in FEE_TIERS.values()
        or (p<=0).any() or (o<=0).any() or (c<=0).any() or (l<=0).any()
        or (h<np.maximum(o,c)).any() or (l>np.minimum(o,c)).any()
        or (d<0).any() or (d>=1).any() or (a<0).any() or (f<0).any()
        or (q<0).any() or (qmin<0).any() or not np.isfinite(cash)):
        raise ValueError('AA1160_INVALID_SOURCE')
    equity=float(cash+np.dot(u,p))
    if equity<=0:return {'ok':False,'reason':'AA1160_PRIOR_EQUITY'}
    old_w=u*p/equity
    if rebalance:
        planned=w*equity/p
        if not gate(w,old_w,d,a,f,q,qmin,equity):
            return {'ok':False,'reason':'AA1160_UNEXECUTABLE_TARGET'}
    else:
        if gate(old_w,old_w,d,a,f,q,qmin,equity):planned=u.copy()
        else:
            try:
                reduced=allocate(np.zeros(4),np.eye(4)*.0001,old_w,d,a,f,q,qmin,equity)
                planned=reduced*equity/p
            except ValueError:
                return {'ok':False,'reason':'AA1160_UNEXECUTABLE_REDUCE_ONLY'}
    stop=p*np.where(u>=0,1-d,1+a)
    gap=bool(np.any(((u>1e-12)&(o<=stop))|((u<-1e-12)&(o>=stop))))
    if gap:planned=np.zeros(4)
    planned_snapshot=planned.copy();balance=float(cash);units=u.copy()
    fees=turnover=0.;used=np.zeros(4);events=[]
    def trade(delta,price,action):
        nonlocal balance,fees,turnover,units
        if np.all(np.abs(delta)<1e-12):return True
        fill=price*(1+np.sign(delta)*SLIPPAGE)
        notional=np.abs(delta)*fill
        if np.any(used+notional>ENTRY_PARTICIPATION*q+1e-8):return False
        balance-=float(np.dot(delta,fill)+fee*notional.sum())
        fees+=float(fee*notional.sum());turnover+=float(notional.sum())
        used[:]+=notional;units[:]+=delta
        for j in np.flatnonzero(np.abs(delta)>1e-12):
            events.append({'asset':int(j),'action':action,'delta_units':float(delta[j]),
                           'fill_price':float(fill[j]),'fee_usd':float(fee*notional[j])})
        return True
    if not trade(planned-units,o,'GAP_EXIT' if gap else ('AA_TARGET' if rebalance else 'AA_REDUCE_ONLY')):
        return {'ok':False,'reason':'AA1160_OPEN_CAPACITY'}
    if np.any(np.abs(units)*p*(1+a)>EXIT_RESERVE*qmin+1e-8):
        return {'ok':False,'reason':'AA1160_EXIT_RESERVE'}
    pre=units.copy()
    touched=bool(np.any(((units>1e-12)&(l<=p*(1-d)))|
                        ((units<-1e-12)&(h>=p*(1+a)))))
    funded=u if order=='carried_before_fill' else pre
    marks=signed_mark(funded,rate,funding_mark_bounds,ev,c)
    cash_funding=-np.where(ev,funded*marks*rate,0.)
    if gap or touched:cash_funding=np.minimum(cash_funding,0.)
    debit=float(np.maximum(-cash_funding,0.).sum())
    if not gap:
        check=corners(balance,pre,l,o,h,equity,debit)
        if not check['ok']:return {'ok':False,'reason':check['reason']}
    if touched and not gap:
        worst=np.where(units>=0,l,h)
        if not trade(-units.copy(),worst,'WHOLE_BASKET_STOP'):
            return {'ok':False,'reason':'AA1160_STOP_CAPACITY'}
    balance+=float(cash_funding.sum())
    post=corners(balance,units,l,o,h,equity)
    if not post['ok']:return {'ok':False,'reason':post['reason']}
    nav=float(balance+np.dot(units,c))
    if nav<=0 or not np.isfinite(nav):return {'ok':False,'reason':'AA1160_FINAL_EQUITY'}
    return {'ok':True,'reason':None,'units':units.copy(),'cash':balance,'equity':nav,
            'fees':fees,'turnover':turnover,'funding_cash_delta':float(cash_funding.sum()),
            'events':events,'basket_stop':bool(touched or gap),
            'planned_units':planned_snapshot,'self_financing':True,'synthetic_only':True}
