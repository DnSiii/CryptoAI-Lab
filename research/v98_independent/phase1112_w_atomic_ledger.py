#!/usr/bin/env python3
"""W atomic signed t-1 hourly OCO execution; synthetic-only pre-economic oracle.

12h rebalance; hourly carried-risk checks without refilling stops. Stop-first
when both touched; gap-aware adverse fills; no same-hour reversal entry.
Unanticipated exposed gaps or liquidity/cap failures reject fail-closed.
"""
from __future__ import annotations
import numpy as np
from phase1110_w_256state_governor import ASSET_CAP,NET_CAP,GROSS_CAP,EQUITY_FLOOR,PARTICIPATION
N=4

def _arr(v):
    x=np.asarray(v,float)
    if x.shape!=(N,) or not np.isfinite(x).all():
        raise ValueError('W_LEDGER_GEOMETRY')
    return x

def _book_ok(cash,units,price,equity_reference):
    exposure=units*price
    equity=float(cash+exposure.sum())
    return (np.isfinite(equity) and equity>=EQUITY_FLOOR*equity_reference-1e-8
        and np.abs(exposure).max()<=ASSET_CAP*equity+1e-8
        and np.abs(exposure).sum()<=GROSS_CAP*equity+1e-8
        and abs(exposure.sum())<=NET_CAP*equity+1e-8)

def execute_hour(prevclose,opening,high,low,closing,carried_units,desired_weights,
                 cash,down,up,prior_quote,fee,slip,*,funding_rate=None,
                 funding_mark=None,funding_event=None,rebalance=True):
    p,o,h,l,c,u,w,d,a,q=[_arr(x) for x in
        (prevclose,opening,high,low,closing,carried_units,
         desired_weights,down,up,prior_quote)]
    if (not np.isfinite(cash) or cash<=-1e15 or not 0<=fee<=.02
        or not 0<=slip<=.02 or (p<=0).any() or (o<=0).any()
        or (l<=0).any() or (h<np.maximum(o,c)).any()
        or (l>np.minimum(o,c)).any() or (d<0).any()
        or (d>=1).any() or (a<0).any() or (q<0).any()):
        raise ValueError('W_LEDGER_INVALID_EVENT')
    if funding_rate is None:funding_rate=np.zeros(N)
    if funding_mark is None:funding_mark=c
    if funding_event is None:funding_event=np.zeros(N,bool)
    rate=_arr(funding_rate);mark=_arr(funding_mark)
    event=np.asarray(funding_event)
    if event.shape!=(N,) or event.dtype!=bool or (mark<=0).any():
        raise ValueError('W_LEDGER_FUNDING_EVENT')
    equity0=float(cash+np.dot(u,p))
    if equity0<=0:
        return {'ok':False,'reason':'W_PRIOR_EQUITY_NONPOSITIVE'}
    # Flat unrelated assets cannot cause a failure; exposed assets must survive.
    at_risk=(np.abs(u)>1e-12)|((np.abs(w)>1e-12)&bool(rebalance))
    if np.any(at_risk&((l<p*(1-d)-1e-9)|(h>p*(1+a)+1e-9))):
        return {'ok':False,'reason':'W_UNANTICIPATED_GAP_OR_RANGE'}
    prior_side=np.where(u!=0,u,w)
    stop=np.where((u!=0)|(w!=0),
        np.where(prior_side>0,p*(1-d),p*(1+a)),np.nan)
    capacity=q*PARTICIPATION
    target_units=w*equity0/p if rebalance else u.copy()
    new=u.copy();balance=float(cash);fees=turnover=0.;events=[]
    def fill(j,delta,px,action):
        nonlocal balance,fees,turnover
        if abs(delta)<1e-12:return True
        execution=px*(1+np.sign(delta)*slip)
        notion=abs(delta)*execution
        if notion>capacity[j]+1e-7:return False
        balance-=delta*execution+fee*notion
        fees+=fee*notion;turnover+=notion;new[j]+=delta
        events.append({'asset':j,'action':action,
            'delta_units':float(delta),'fill_price':float(execution)})
        return True
    for j in range(N):
        sign=np.sign(u[j]) if abs(u[j])>1e-12 else np.sign(target_units[j])
        reversal=(abs(u[j])>1e-12 and abs(target_units[j])>1e-12
                  and np.sign(u[j])!=np.sign(target_units[j]))
        gap=(sign>0 and o[j]<=stop[j]+1e-9) or (sign<0 and o[j]>=stop[j]-1e-9)
        if reversal:
            if not fill(j,-u[j],o[j],'ATOMIC_FLAT_REVERSAL'):
                return {'ok':False,'reason':'W_OPEN_MANDATORY_CAPACITY'}
        elif gap:
            if abs(u[j])>1e-12 and not fill(j,-u[j],o[j],'OPEN_GAP_STOP'):
                return {'ok':False,'reason':'W_OPEN_MANDATORY_CAPACITY'}
            elif abs(u[j])<=1e-12:
                events.append({'asset':j,'action':'SKIP_GAP_ENTRY'})
        else:
            if not fill(j,target_units[j]-u[j],o[j],'OPEN_TARGET'):
                return {'ok':False,'reason':'W_OPEN_MANDATORY_CAPACITY'}
    if not _book_ok(balance,new,o,equity0):
        return {'ok':False,'reason':'W_OPEN_BOOK_CAP'}
    for j in range(N):
        if abs(new[j])<=1e-12:continue
        s=np.sign(new[j])
        stop_j=p[j]*(1-d[j]) if s>0 else p[j]*(1+a[j])
        limit_j=p[j]*(1+a[j]) if s>0 else p[j]*(1-d[j])
        stop_hit=l[j]<=stop_j+1e-9 if s>0 else h[j]>=stop_j-1e-9
        limit_hit=h[j]>=limit_j-1e-9 if s>0 else l[j]<=limit_j+1e-9
        if stop_hit:
            px=min(o[j],stop_j) if s>0 else max(o[j],stop_j)
            if not fill(j,-new[j],px,'STOP_FIRST'):
                return {'ok':False,'reason':'W_STOP_MANDATORY_CAPACITY'}
        elif limit_hit:
            if not fill(j,-new[j]/3.,limit_j,'PARTIAL_LIMIT'):
                return {'ok':False,'reason':'W_LIMIT_MANDATORY_CAPACITY'}
    funding=float(np.sum(new*mark*rate*event))
    balance-=funding
    if not _book_ok(balance,new,c,equity0):
        return {'ok':False,'reason':'W_POST_EXECUTION_BOOK_CAP'}
    return {'ok':True,'units':new,'cash':balance,
        'equity':float(balance+np.dot(new,c)),'fees':fees,
        'turnover':turnover,'signed_funding_cash_delta':-funding,
        'events':events,'prior_equity':equity0}
