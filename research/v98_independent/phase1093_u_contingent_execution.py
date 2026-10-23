#!/usr/bin/env python3
"""V98 U preregistered reduce-only OCO mechanics, synthetic-only, no PnL."""
from __future__ import annotations
import itertools
import math
import numpy as np

N=4;ASSET_CAP=.45;NET_CAP=.75;GROSS_CAP=1.35;EQUITY_FLOOR=.25
PARTICIPATION=.01

def plan(prev_close, units, prior_down, prior_up, prior_quote):
    p,u,d,h,q=map(lambda x:np.asarray(x,float),(prev_close,units,prior_down,prior_up,prior_quote))
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (p,u,d,h,q)) or
        (p<=0).any() or (q<0).any() or (d<0).any() or (d>=1).any() or (h<0).any()):
        raise ValueError('U_INVALID_PRIOR_ORDER_INPUT')
    dist_down=np.maximum(d,1e-8);dist_up=np.maximum(h,1e-8)
    stop=np.where(u>0,p*(1-dist_down),np.where(u<0,p*(1+dist_up),np.nan))
    limit=np.where(u>0,p*(1+dist_up),np.where(u<0,p*(1-dist_down),np.nan))
    return {'stop':stop,'limit':limit,'stop_qty':np.abs(u),
            'limit_qty':np.abs(u)/3.,'side':np.sign(u).astype(int),
            'capacity_usd':q*PARTICIPATION,'prior_close':p.copy(),
            'prior_down':d.copy(),'prior_up':h.copy()}

def fill(plan, units, cash, opening, high, low, fee, *, slippage=0.,capacity=True):
    """Stop first if both touched; gap at adverse opening; reduce-only."""
    u,o,h,l=[np.asarray(x,float) for x in (units,opening,high,low)]
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (u,o,h,l)) or
        (o<=0).any() or (l<=0).any() or (h<o).any() or (l>o).any() or
        not math.isfinite(cash) or not 0<=fee<=.02 or not 0<=slippage<=.02):
        raise ValueError('U_INVALID_FILL_INPUT')
    out=u.copy();total_fee=0.;total_turnover=0.;events=[]
    for j in range(N):
        s=int(plan['side'][j]);qty=min(abs(u[j]),float(plan['stop_qty'][j]))
        if s==0 or qty<=0:continue
        if np.sign(u[j])!=s:raise ValueError('U_ORDER_NOT_REDUCE_ONLY')
        stop=float(plan['stop'][j]);limit=float(plan['limit'][j])
        stop_hit=bool(l[j]<=stop) if s>0 else bool(h[j]>=stop)
        limit_hit=bool(h[j]>=limit) if s>0 else bool(l[j]<=limit)
        if stop_hit:
            base=min(o[j],stop) if s>0 else max(o[j],stop)
            price=base*(1-slippage) if s>0 else base*(1+slippage)
            action='STOP'
        elif limit_hit:
            qty=min(qty,float(plan['limit_qty'][j]))
            price=limit*(1-slippage) if s>0 else limit*(1+slippage)
            action='LIMIT'
        else:continue
        if price<=0 or not math.isfinite(price):raise ValueError('U_BAD_EXECUTION_PRICE')
        notion=qty*price
        if capacity and notion>plan['capacity_usd'][j]+1e-8:
            return {'ok':False,'reason':'U_CONTINGENT_CAPACITY_SHORTFALL','asset':j,'event':action}
        signed_delta=-s*qty
        out[j]+=signed_delta
        if out[j]*s < -1e-10:raise AssertionError('U_REDUCE_ONLY_FLIP')
        cash-=signed_delta*price+fee*notion
        total_fee+=fee*notion;total_turnover+=notion
        events.append({'asset':j,'action':action,'qty':qty,'price':price,
                       'gap':bool((s>0 and o[j]<stop) or (s<0 and o[j]>stop)) if stop_hit else False,
                       'both_touched':stop_hit and limit_hit})
    return {'ok':True,'cash':cash,'units':out,'fee_usd':total_fee,
            'turnover_usd':total_turnover,'events':events}

def corners_audit(cash,units,reference,down,up,*,baseline=None,buffer=0.):
    u,p,d,h=[np.asarray(x,float) for x in (units,reference,down,up)]
    if any(x.shape!=(N,) or not np.isfinite(x).all() for x in (u,p,d,h)):
        raise ValueError('U_CORNER_GEOMETRY')
    if (p<=0).any() or (d<0).any() or (d>=1).any() or (h<0).any() or buffer<0:
        raise ValueError('U_CORNER_INVALID_INPUT')
    base=cash+float(np.dot(u,p)) if baseline is None else float(baseline)
    if not math.isfinite(base) or base<=0:return {'ok':False,'reason':'U_NONPOSITIVE_BASE'}
    worst=float('inf')
    for bits in itertools.product((False,True),repeat=N):
        price=p*np.where(bits,1+h,1-d)
        exposure=u*price
        equity=cash+exposure.sum()-buffer
        worst=min(worst,equity)
        if equity<EQUITY_FLOOR*base-1e-7*base:return {'ok':False,'reason':'U_EQUITY_FLOOR','worst':worst}
        if np.abs(exposure).max()>ASSET_CAP*equity+1e-7*base:return {'ok':False,'reason':'U_ASSET','worst':worst}
        if np.abs(exposure).sum()>GROSS_CAP*equity+1e-7*base:return {'ok':False,'reason':'U_GROSS','worst':worst}
        if abs(exposure.sum())>NET_CAP*equity+1e-7*base:return {'ok':False,'reason':'U_NET','worst':worst}
    return {'ok':True,'reason':None,'worst':worst}

def audit_bracket_paths(plan_data, cash, units, opening, high, low, fee, *,
                        slippage=0., buffer=0., capacity=True):
    u,o,h,l=[np.asarray(x,float) for x in (units,opening,high,low)]
    if not math.isfinite(buffer) or buffer<0:raise ValueError('U_BAD_FUNDING_BUFFER')
    result=fill(plan_data,u,cash,o,h,l,fee,slippage=slippage,capacity=capacity)
    if not result['ok']:return result
    event_by_asset={e['asset']:e for e in result['events']}
    base=float(cash+np.dot(u,o))
    if not math.isfinite(base) or base<=0:return {'ok':False,'reason':'U_NONPOSITIVE_BASE'}
    choices=[]
    for j in range(N):
        ev=event_by_asset.get(j)
        s=int(plan_data['side'][j]);stop=float(plan_data['stop'][j]) if s else None
        if ev and ev['action']=='STOP':
            if (s>0 and o[j]<=stop) or (s<0 and o[j]>=stop):
                preprices=[o[j]]
            elif s>0:preprices=[stop,h[j]]
            else:preprices=[l[j],stop]
        else:preprices=[l[j],h[j]]
        states=[(0.,u[j],float(p)) for p in preprices]
        if ev:
            delta=-s*ev['qty'];notion=ev['qty']*ev['price']
            cash_effect=-delta*ev['price']-fee*notion
            for p in (l[j],h[j]):
                states.append((cash_effect,u[j]+delta,float(p)))
        choices.append(states)
    worst=float('inf');scenarios=0
    for combo in itertools.product(*choices):
        scenarios+=1
        exposure=np.array([v[1]*v[2] for v in combo])
        equity=cash+sum(v[0] for v in combo)+exposure.sum()-buffer
        worst=min(worst,equity)
        if equity<EQUITY_FLOOR*base-1e-7*base:
            return {'ok':False,'reason':'U_PATH_EQUITY_FLOOR','scenarios':scenarios,'worst':worst}
        if np.abs(exposure).max()>ASSET_CAP*equity+1e-7*base:
            return {'ok':False,'reason':'U_PATH_ASSET','scenarios':scenarios,'worst':worst}
        if np.abs(exposure).sum()>GROSS_CAP*equity+1e-7*base:
            return {'ok':False,'reason':'U_PATH_GROSS','scenarios':scenarios,'worst':worst}
        if abs(exposure.sum())>NET_CAP*equity+1e-7*base:
            return {'ok':False,'reason':'U_PATH_NET','scenarios':scenarios,'worst':worst}
    result.update({'scenarios':scenarios,'worst':worst})
    return result
