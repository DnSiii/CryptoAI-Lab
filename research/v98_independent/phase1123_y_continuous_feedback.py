#!/usr/bin/env python3
"""Y t-1 self-financing reduce-only max-retention feedback; no PnL.

81 prior high/open/low mark states, full basket exit, signed funding reserve,
real opening used for settlement ONLY. Never select a plan from future open.
"""
from __future__ import annotations
import itertools
import numpy as np
N=4
STATES=np.asarray(tuple(itertools.product(range(3),repeat=4)),np.int8)
ASSET=.45;NET=.75;GROSS=1.35;FLOOR=.25;PARTICIPATION=.01
ITERATIONS=32;QUANTUM=1e-6;FUNDING_EVENTS=6

def check_inputs(prior,opening,units,cash,down,up,funding,quote,fee,slip):
    p,o,u,d,h,f,q=[np.asarray(x,float) for x in
        (prior,opening,units,down,up,funding,quote)]
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (p,o,u,d,h,f,q))
        or (p<=0).any() or (o<=0).any() or (d<0).any() or (d>=1).any()
        or (h<0).any() or (f<0).any() or (q<0).any()
        or not np.isfinite(cash) or not 0<=fee<=.02 or not 0<=slip<=.02):
        raise ValueError('Y_FEEDBACK_BAD_CAUSAL_INPUT')
    return p,o,u,d,h,f,q

def evaluate(retention,prior,opening,units,cash,down,up,funding,quote,fee,slip,
             *,details=False):
    p,o,u,d,h,f,q=check_inputs(prior,opening,units,cash,down,up,funding,quote,fee,slip)
    if not np.isfinite(retention) or not 0<=retention<=1:
        raise ValueError('Y_FEEDBACK_RETENTION')
    after=u*retention;delta=after-u
    fill=o*(1+np.sign(delta)*slip)
    traded=np.abs(delta)*fill
    capacity_ok=bool(np.all(traded<=PARTICIPATION*q+1e-8))
    balance=float(cash-np.sum(delta*fill+fee*traded))
    marks=np.stack((p*(1-d),o,p*(1+h)),axis=0)
    prices=marks[STATES,np.arange(N)]
    exposure=prices*after[None,:]
    reserve=FUNDING_EVENTS*np.sum(np.abs(after)*f*(1+h)*p)
    equity=balance+exposure.sum(axis=1)-reserve
    asset=np.abs(exposure).max(axis=1)
    gross=np.abs(exposure).sum(axis=1)
    net=np.abs(exposure.sum(axis=1))
    prior_equity=float(cash+np.dot(u,p))
    adverse=np.where(after>=0,p*(1-d),p*(1+h))
    exit_delta=-after
    exit_fill=adverse*(1+np.sign(exit_delta)*slip)
    basket_cash=balance-float(np.sum(exit_delta*exit_fill+fee*np.abs(exit_delta)*exit_fill))-float(reserve)
    ok=(capacity_ok and prior_equity>0 and np.isfinite(equity).all()
        and np.all(equity>=FLOOR*prior_equity-1e-8)
        and basket_cash>=FLOOR*prior_equity-1e-8
        and np.all(asset<=ASSET*equity+1e-8)
        and np.all(gross<=GROSS*equity+1e-8)
        and np.all(net<=NET*equity+1e-8))
    if not details:return bool(ok)
    return {'ok':bool(ok),'retention':float(retention),'units':after,
        'cash':balance,'fees':float(fee*traded.sum()),
        'turnover':float(traded.sum()),'capacity_ok':capacity_ok,
        'worst_equity':float(equity.min()),'basket_exit_equity':float(basket_cash),'reserved_funding':float(reserve),
        'states':len(STATES),'prior_equity':prior_equity}

def max_safe_retention(prior,opening,units,cash,down,up,funding,quote,fee,slip):
    p,o,u,d,h,f,q=check_inputs(prior,opening,units,cash,down,up,funding,quote,fee,slip)
    # PLAN at t-1 with p. Never select retention using future opening o.
    planned_open=p
    if evaluate(1.,p,planned_open,u,cash,d,h,f,q,fee,slip):
        actual=evaluate(1.,p,o,u,cash,d,h,f,q,fee,slip,details=True)
        if not actual['ok']:
            return {'ok':False,'reason':'Y_UNEXPECTED_OPENING_RISK',
                    'planned_retention':1.}
        actual['planned_retention']=1.
        return actual
    required=np.where(np.abs(u)>1e-12,
        1.-PARTICIPATION*q/np.maximum(np.abs(u)*planned_open*(1+slip),1e-12),0.)
    lower=max(0.,float(np.max(required)))
    lower=min(1.,np.ceil(lower/QUANTUM)*QUANTUM)
    if not evaluate(lower,p,planned_open,u,cash,d,h,f,q,fee,slip):
        return {'ok':False,'reason':'Y_NO_LIQUID_SAFE_RETENTION',
                'min_retention_due_capacity':lower}
    lo,hi=lower,1.
    for _ in range(ITERATIONS):
        mid=(lo+hi)/2
        candidate=max(lower,np.floor(mid/QUANTUM)*QUANTUM)
        if evaluate(candidate,p,planned_open,u,cash,d,h,f,q,fee,slip):
            lo=candidate
        else:hi=mid
    planned=evaluate(lo,p,planned_open,u,cash,d,h,f,q,fee,slip,details=True)
    if not planned['ok']:raise AssertionError('Y_FEEDBACK_SERIALIZATION')
    result=evaluate(lo,p,o,u,cash,d,h,f,q,fee,slip,details=True)
    if not result['ok']:
        return {'ok':False,'reason':'Y_UNEXPECTED_OPENING_RISK',
                'planned_retention':float(lo)}
    result['planned_retention']=float(lo)
    return result
