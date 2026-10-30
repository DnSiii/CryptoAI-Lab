#!/usr/bin/env python3
"""V independent t-1 linked OCO and flat-then-enter reversal oracle. No PnL."""
from __future__ import annotations
import numpy as np

N=4
PARTICIPATION=.01

def preplace(prevclose,carried,desired,down,up,prior_quote):
    p,c,w,d,h,q=[np.asarray(x,float) for x in
                 (prevclose,carried,desired,down,up,prior_quote)]
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (p,c,w,d,h,q)) or
        (p<=0).any() or (d<0).any() or (d>=1).any() or (h<0).any() or (q<0).any()):
        raise ValueError('V_LINKED_INVALID_PRIOR')
    reversal=(np.abs(c)>1e-9)&(np.abs(w)>1e-9)&(np.sign(c)!=np.sign(w))
    signed=np.where(reversal,c,np.where(np.abs(w)>1e-9,
                     np.sign(w)*np.maximum(np.abs(w),np.abs(c)),c))
    side=np.sign(signed).astype(int)
    stop=np.where(side>0,p*(1-np.maximum(d,1e-8)),
          np.where(side<0,p*(1+np.maximum(h,1e-8)),np.nan))
    limit=np.where(side>0,p*(1+np.maximum(h,1e-8)),
           np.where(side<0,p*(1-np.maximum(d,1e-8)),np.nan))
    return {'side':side,'stop':stop,'limit':limit,'stop_qty':np.abs(signed),
            'limit_qty':np.abs(signed)/3.,'capacity_usd':q*PARTICIPATION,
            'reversal':reversal,'prevclose':p.copy()}

def opening_orders(plan,carried,desired,opening,fee,slip):
    """Flat first for reversal; no opposite entry same hour."""
    c,w,o=[np.asarray(x,float) for x in (carried,desired,opening)]
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (c,w,o)) or
        (o<=0).any() or not 0<=fee<=.02 or not 0<=slip<=.02):
        raise ValueError('V_OPEN_GEOMETRY')
    out=c.copy();cash_delta=0.;fees=0.;turnover=0.;events=[]
    for j in range(N):
        rev=bool(plan['reversal'][j]);s=int(plan['side'][j])
        if rev:
            qty=abs(c[j]);delta=-c[j];action='FLAT_REVERSAL'
        else:
            crossed=(s>0 and o[j]<=plan['stop'][j]) or (s<0 and o[j]>=plan['stop'][j])
            if crossed and abs(c[j])>1e-9:
                qty=abs(c[j]);delta=-c[j];action='GAP_STOP'
            else:
                delta=w[j]-c[j];qty=abs(delta);action='ENTRY_OR_REDUCE'
        if qty<=1e-12:continue
        price=o[j]*(1+np.sign(delta)*slip)
        notion=qty*price
        if notion>plan['capacity_usd'][j]+1e-8:
            if action!='ENTRY_OR_REDUCE':
                return {'ok':False,'reason':'V_MANDATORY_OPEN_CAPACITY','asset':j}
            qty=plan['capacity_usd'][j]/price
            delta=np.sign(delta)*qty;notion=qty*price
        out[j]+=delta
        if action in ('FLAT_REVERSAL','GAP_STOP') and abs(out[j])>1e-8:
            raise AssertionError('V_OPEN_NOT_FLAT')
        cash_delta-=delta*price+fee*notion
        fees+=fee*notion;turnover+=notion
        events.append({'asset':j,'action':action,'qty':qty,'price':price})
    return {'ok':True,'units':out,'cash_delta':cash_delta,'fee_usd':fees,
            'turnover_usd':turnover,'events':events}

def protective_fill(plan,units,opening,high,low,fee,slip):
    """Conservative stop-first, gap-aware OCO; never increase exposure."""
    u,o,h,l=[np.asarray(x,float) for x in (units,opening,high,low)]
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (u,o,h,l)) or
        (o<=0).any() or (l<=0).any() or (h<o).any() or (l>o).any() or
        not 0<=fee<=.02 or not 0<=slip<=.02):
        raise ValueError('V_PROTECTIVE_GEOMETRY')
    out=u.copy();cash_delta=fees=turnover=0.;events=[]
    for j in range(N):
        s=int(plan['side'][j]);qty=abs(u[j])
        if qty<=1e-12:continue
        if s==0 or np.sign(u[j])!=s or qty>plan['stop_qty'][j]+1e-8:
            return {'ok':False,'reason':'V_UNPROTECTED_QUANTITY_OR_SIGN','asset':j}
        stop=plan['stop'][j];limit=plan['limit'][j]
        stop_hit=l[j]<=stop if s>0 else h[j]>=stop
        limit_hit=h[j]>=limit if s>0 else l[j]<=limit
        if stop_hit:
            qty=min(qty,plan['stop_qty'][j])
            px=min(o[j],stop) if s>0 else max(o[j],stop)
            action='STOP'
        elif limit_hit:
            qty=min(qty,plan['limit_qty'][j]);px=limit;action='LIMIT'
        else:continue
        delta=-s*qty
        price=px*(1+np.sign(delta)*slip)
        notion=qty*price
        if notion>plan['capacity_usd'][j]+1e-8:
            return {'ok':False,'reason':'V_MANDATORY_PROTECTIVE_CAPACITY','asset':j}
        out[j]+=delta
        if out[j]*s < -1e-9:raise AssertionError('V_REDUCE_ONLY_FLIP')
        cash_delta-=delta*price+fee*notion
        fees+=fee*notion;turnover+=notion
        events.append({'asset':j,'action':action,'price':price,'qty':qty,
                       'both_touched':bool(stop_hit and limit_hit)})
    return {'ok':True,'units':out,'cash_delta':cash_delta,'fee_usd':fees,
            'turnover_usd':turnover,'events':events}
