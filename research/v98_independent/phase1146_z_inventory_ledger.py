#!/usr/bin/env python3
"""Z preregistered inventory-first synthetic OHLC executor; no historical PnL.

Targets come from prior completed bar. Current bar OHLC and native mark are
settlement/survival observations ONLY, never target selection inputs.
"""
from __future__ import annotations
import numpy as np
from phase1143_z_sevenslot_source import (
    CORNERS,ASSET_CAP,GROSS_CAP,NET_CAP,FLOOR,PARTICIPATION,SLIPPAGE,
    corner_gate)
FEE_TIERS={'base':.0007,'severe':.0012,'supersevere':.002}
ORDERS=('carried_before_fill','new_after_fill')

def vector(x,name):
    a=np.asarray(x,float)
    if a.shape!=(4,) or not np.isfinite(a).all():raise ValueError('Z1146_BAD_'+name)
    return a

def risk_corners(cash,units,prices,prior_equity,funding_debit=0.):
    """81 OHLC corners on actual inventory with conservative funding reserve."""
    u=vector(units,'UNITS');cash=float(cash)
    p=np.asarray(prices,float)
    if (p.shape!=(3,4) or not np.isfinite(p).all() or (p<=0).any()
        or not np.isfinite(cash+prior_equity+funding_debit) or prior_equity<=0
        or funding_debit<0):raise ValueError('Z1146_BAD_CORNERS')
    corner=p[CORNERS,np.arange(4)]
    exposures=corner*u
    eq=cash+exposures.sum(axis=1)-funding_debit
    if np.any(eq<FLOOR*prior_equity-1e-8):reason='Z1146_INTRABAR_EQUITY'
    elif np.any(np.abs(exposures)>ASSET_CAP*eq[:,None]+1e-8):reason='Z1146_INTRABAR_ASSET'
    elif np.any(np.abs(exposures).sum(axis=1)>GROSS_CAP*eq+1e-8):reason='Z1146_INTRABAR_GROSS'
    elif np.any(np.abs(exposures.sum(axis=1))>NET_CAP*eq+1e-8):reason='Z1146_INTRABAR_NET'
    else:reason=None
    return {'ok':reason is None,'reason':reason,'worst_equity':float(eq.min()),
        'max_asset_weight':float(np.max(np.abs(exposures)/np.maximum(eq[:,None],1e-12))),
        'max_gross_weight':float(np.max(np.abs(exposures).sum(axis=1)/np.maximum(eq,1e-12))),
        'max_net_weight':float(np.max(np.abs(exposures.sum(axis=1))/np.maximum(eq,1e-12)))}

def signed_mark(held,rate,mark,event,close):
    u=vector(held,'HELD');r=vector(rate,'RATE');p=vector(close,'CLOSE')
    m=np.asarray(mark,float);ev=np.asarray(event,bool)
    if (m.shape!=(4,2) or ev.shape!=(4,) or
        np.any(~np.isfinite(m[ev])) or np.any(m[ev]<=0) or
        np.any(m[ev,0]>m[ev,1])):raise ValueError('Z1146_BAD_NATIVE_MARK')
    return np.where(ev,np.where(u*r>=0,m[:,1],m[:,0]),p)

def execute_hour(prior,opening,high,low,closing,carried_units,desired_weights,
                 cash,prior_down,prior_up,prior_funding_bound,prior_quote,
                 *,fee,order,funding_rate,funding_mark_bounds,funding_event,
                 rebalance=True):
    p,o,h,l,c,u,w,d,a,f,q,rate=[vector(v,name) for v,name in (
        (prior,'PRIOR'),(opening,'OPEN'),(high,'HIGH'),(low,'LOW'),
        (closing,'CLOSE'),(carried_units,'UNITS'),(desired_weights,'WEIGHTS'),
        (prior_down,'DOWN'),(prior_up,'UP'),(prior_funding_bound,'FUNDING'),
        (prior_quote,'QUOTE'),(funding_rate,'RATE'))]
    ev=np.asarray(funding_event,bool)
    if (ev.shape!=(4,) or order not in ORDERS or fee not in FEE_TIERS.values()
        or (p<=0).any() or (o<=0).any() or (c<=0).any() or (l<=0).any()
        or (h<np.maximum(o,c)).any() or (l>np.minimum(o,c)).any()
        or (d<0).any() or (d>=1).any() or (a<0).any() or (f<0).any()
        or (q<0).any() or not np.isfinite(cash)):
        raise ValueError('Z1146_INVALID_SOURCE')
    initial_equity=float(cash+np.dot(u,p))
    if initial_equity<=0:return {'ok':False,'reason':'Z1146_PRIOR_EQUITY'}
    carried=u.copy()
    if rebalance:
        planned=w*initial_equity/p
    else:
        # Only reduce existing inventory when its prior 81-corner envelope fails.
        old_w=u*p/initial_equity
        if corner_gate(old_w,d,a,f,old_w):planned=u.copy()
        else:
            left,right=0.,1.
            for _ in range(24):
                mid=(left+right)/2
                if corner_gate(old_w*mid,d,a,f,old_w):left=mid
                else:right=mid
            planned=u*left
    stop_level=p*np.where(u>=0,1-d,1+a)
    gap=bool(np.any(((u>1e-12)&(o<=stop_level))|
                    ((u<-1e-12)&(o>=stop_level))))
    if gap:planned=np.zeros(4)
    planned_snapshot=planned.copy()
    balance=float(cash);units=u.copy();fees=turnover=0.
    used=np.zeros(4);events=[]
    def trade(delta,prices,action):
        nonlocal balance,fees,turnover,units
        if np.all(np.abs(delta)<1e-12):return True
        fill=prices*(1+np.sign(delta)*SLIPPAGE)
        notion=np.abs(delta)*fill
        if np.any(used+notion>PARTICIPATION*q+1e-8):return False
        balance-=float(np.dot(delta,fill)+fee*notion.sum())
        fees+=float(fee*notion.sum());turnover+=float(notion.sum())
        used[:]+=notion;units[:]+=delta
        for j in np.flatnonzero(np.abs(delta)>1e-12):
            events.append({'asset':int(j),'action':action,
                'delta_units':float(delta[j]),'fill_price':float(fill[j]),
                'fee_usd':float(fee*notion[j]),'notional':float(notion[j])})
        return True
    if not trade(planned-units,o,'GAP_REDUCE_ONLY' if gap else
                 ('Z_ALPHA_REFRESH' if rebalance else 'Z_REDUCE_ONLY_FEEDBACK')):
        return {'ok':False,'reason':'Z1146_OPEN_CAPACITY',
                'planned_units':planned_snapshot.tolist()}
    prestop=units.copy()
    touched=bool(np.any(((units>1e-12)&(l<=p*(1-d)))|
                        ((units<-1e-12)&(h>=p*(1+a)))))
    funded=carried if order=='carried_before_fill' else prestop
    mark=signed_mark(funded,rate,funding_mark_bounds,ev,c)
    cash_by_asset=-np.where(ev,funded*mark*rate,0.)
    if gap or touched:cash_by_asset=np.minimum(cash_by_asset,0.)
    funding_debit=float(np.maximum(-cash_by_asset,0.).sum())
    if not gap:
        pre=risk_corners(balance,prestop,np.stack((l,o,h)),initial_equity,funding_debit)
        if not pre['ok']:
            return {'ok':False,'reason':pre['reason'],
                    'planned_units':planned_snapshot.tolist(),'pre_stop':pre}
    if touched and not gap:
        worst=np.where(units>=0,l,h)
        if not trade(-units.copy(),worst,'WHOLE_BASKET_STOP_WORST_EXTREME'):
            return {'ok':False,'reason':'Z1146_STOP_CAPACITY',
                    'planned_units':planned_snapshot.tolist()}
    balance+=float(cash_by_asset.sum())
    post=risk_corners(balance,units,np.stack((l,o,h)),initial_equity)
    if not post['ok']:
        return {'ok':False,'reason':post['reason'],
                'planned_units':planned_snapshot.tolist(),'post_stop':post}
    final_equity=float(balance+np.dot(units,c))
    if final_equity<=0 or not np.isfinite(final_equity):
        return {'ok':False,'reason':'Z1146_FINAL_EQUITY'}
    return {'ok':True,'reason':None,'planned_units':planned_snapshot.tolist(),
        'units':units.copy(),'cash':balance,'equity':final_equity,
        'fees':fees,'turnover':turnover,'funding_cash_delta':float(cash_by_asset.sum()),
        'funding_by_asset':cash_by_asset.tolist(),'events':events,
        'basket_stop':bool(touched or gap),'pre_stop_checked':not gap,
        'post_stop':post,'self_financing':True,'synthetic_only':True}
