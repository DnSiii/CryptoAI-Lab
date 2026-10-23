#!/usr/bin/env python3
"""Phase1126 Y: causal, signed, self-financing OHLC survival oracle.

SYNTHETIC ONLY until authenticated source/manifest/chronological folds are frozen.
No alpha selection and no historical PnL. Decisions use t-1 close/quote;
open/high/low/mark are settlement and hard-failure observations only.
"""
from __future__ import annotations
import itertools
import numpy as np
from phase1123_y_continuous_feedback import max_safe_retention

N=4
CORNERS=np.asarray(tuple(itertools.product(range(3),repeat=N)),dtype=np.int8)
ASSET=.45; NET=.75; GROSS=1.35; FLOOR=.25; PARTICIPATION=.01

def _vec(x, label):
    a=np.asarray(x,dtype=float)
    if a.shape!=(N,) or not np.isfinite(a).all():
        raise ValueError('Y1126_BAD_'+label)
    return a

def execute_hour(prior,opening,high,low,closing,carried_units,desired_weights,
                 cash,prior_down,prior_up,prior_funding_bound,prior_quote,
                 fee,slip,*,rebalance,funding_rate,funding_mark,funding_event):
    p,o,h,l,c,u,w,d,a,f,q,rate,mark=[_vec(v,name) for v,name in (
        (prior,'PRIOR'),(opening,'OPEN'),(high,'HIGH'),(low,'LOW'),
        (closing,'CLOSE'),(carried_units,'UNITS'),(desired_weights,'WEIGHTS'),
        (prior_down,'DOWN'),(prior_up,'UP'),(prior_funding_bound,'FUNDING_BOUND'),
        (prior_quote,'QUOTE'),(funding_rate,'RATE'),(funding_mark,'MARK'))]
    events=np.asarray(funding_event,dtype=bool)
    if (events.shape!=(N,) or not np.isfinite(cash) or (p<=0).any()
        or (o<=0).any() or (l<=0).any() or (h<np.maximum(o,c)).any()
        or (l>np.minimum(o,c)).any() or (d<0).any() or (d>=1).any()
        or (a<0).any() or (f<0).any() or (q<0).any()
        or (mark<=0).any() or not 0<=fee<=.02 or not 0<=slip<=.02):
        raise ValueError('Y1126_BAD_SOURCE')
    equity0=float(cash+np.dot(u,p))
    if equity0<=0:
        return {'ok':False,'reason':'Y1126_PRIOR_EQUITY','planned_units':u.tolist()}
    # Only t-1 values can determine target units or feedback retention.
    if rebalance:
        planned=w*equity0/p
        mode='ALPHA_REFRESH'
    else:
        ctrl=max_safe_retention(p,p,u,cash,d,a,f,q,fee,slip)
        if not ctrl['ok']:
            return {'ok':False,'reason':ctrl['reason'],'planned_units':u.tolist()}
        planned=np.asarray(ctrl['units'],float)
        mode='REDUCE_ONLY_FEEDBACK'
    # A preplaced gap-stop on carried inventory takes precedence over new entries.
    stop=p*np.where(u>=0,1-d,1+a)
    gap=bool(np.any(((u>1e-12)&(o<=stop))|((u<-1e-12)&(o>=stop))))
    if gap:
        planned=np.zeros(N)
        mode='GAP_STOP_FIRST'
    planned_snapshot=planned.copy()
    balance=float(cash); units=u.copy(); fees=turnover=0.
    used=np.zeros(N);records=[]
    def trade(delta,prices,action):
        nonlocal balance,fees,turnover,units
        fill=prices*(1+np.sign(delta)*slip)
        traded=np.abs(delta)*fill
        if np.any(used+traded>PARTICIPATION*q+1e-8):return False
        balance-=float(np.dot(delta,fill)+fee*traded.sum())
        fees+=float(fee*traded.sum());turnover+=float(traded.sum())
        used[:]+=traded;units[:]+=delta
        records.append({'action':action,'notional':float(traded.sum())})
        return True
    if not trade(planned-units,o,mode):
        return {'ok':False,'reason':'Y1126_OPEN_CAPACITY',
                'planned_units':planned_snapshot.tolist()}
    # Preplaced basket contingency: if ANY held asset touches its adverse
    # t-1 boundary, close ALL at worst tradable observed bar extreme.
    stop=p*np.where(units>=0,1-d,1+a)
    prestop_units=u.copy() if gap else units.copy()
    touched=bool(np.any(((units>1e-12)&(l<=stop))|
                        ((units<-1e-12)&(h>=stop))))
    if touched and not gap:
        worst=np.where(units>=0,l,h)
        if not trade(-units.copy(),worst,'WHOLE_BASKET_STOP_WORST_EXTREME'):
            return {'ok':False,'reason':'Y1126_STOP_CAPACITY',
                    'planned_units':planned_snapshot.tolist()}
    # On a stop, never count favorable funding credits that may have arrived
    # after the liquidation. Charges are reserved conservatively.
    funding_cash=float(-np.sum(np.where(events,prestop_units*mark*rate,0.)))
    if touched or gap:funding_cash=min(0.,funding_cash)
    before_funding=balance
    balance+=funding_cash
    # Evaluate actual intrabar 3^4 OHLC corners, not just the closing mark.
    prices=np.stack((l,o,h),axis=0)[CORNERS,np.arange(N)]
    exposures=prices*units[None,:]
    equities=before_funding+exposures.sum(axis=1)
    equities=np.minimum(equities,balance+exposures.sum(axis=1))
    asset=np.abs(exposures).max(axis=1)
    gross=np.abs(exposures).sum(axis=1)
    net=np.abs(exposures.sum(axis=1))
    floor=FLOOR*equity0
    if np.any(equities<floor-1e-8):reason='Y1126_INTRABAR_EQUITY'
    elif np.any(asset>ASSET*equities+1e-8):reason='Y1126_INTRABAR_ASSET'
    elif np.any(gross>GROSS*equities+1e-8):reason='Y1126_INTRABAR_GROSS'
    elif np.any(net>NET*equities+1e-8):reason='Y1126_INTRABAR_NET'
    else:reason=None
    final_equity=float(balance+np.dot(units,c))
    if not np.isfinite(final_equity) or final_equity<=0:
        reason='Y1126_FINAL_EQUITY'
    result={'ok':reason is None,'reason':reason,'planned_units':planned_snapshot.tolist(),
        'units':units.copy(),'cash':float(balance),'equity':final_equity,
        'fees':fees,'turnover':turnover,'funding_cash_delta':funding_cash,
        'basket_stop':bool(touched or gap),'worst_intrabar_equity':float(equities.min()),
        'events':records,'self_financing':True,'synthetic_only':True}
    return result
