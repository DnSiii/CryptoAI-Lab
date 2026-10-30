#!/usr/bin/env python3
"""V98 Independent P Phase1025: state-aware, pretrade 16-corner envelope.

Pure deterministic execution infrastructure, not an alpha. Only prior completed
OHLC shocks and t-1 quote volume are allowed; current high/low are never inputs.
Funding buffer is supplied by the caller from causal, pre-open information.
"""
from __future__ import annotations
import itertools
import math
import numpy as np
from scipy.optimize import linprog
from phase1002_lp_opening_repair import repair_open_lp, PARTICIPATION

CAP_ASSET = .70
CAP_GROSS = 1.75
FLOOR = .10


def corners(down, up):
    dn, hi = np.asarray(down,float), np.asarray(up,float)
    if dn.shape != (4,) or hi.shape != (4,) or not np.isfinite(dn).all() or not np.isfinite(hi).all():
        raise ValueError('P_SHOCK_SHAPE_OR_NONFINITE')
    if (dn<0).any() or (dn>=1).any() or (hi<0).any():
        raise ValueError('P_SHOCK_INVALID')
    return np.array([np.where(b,1+hi,1-dn) for b in itertools.product((False,True),repeat=4)])


def survives(cash, units, opening, down, up, fee_buffer=0., baseline=None, tol=1e-9):
    o,u = np.asarray(opening,float), np.asarray(units,float)
    if o.shape!=(4,) or u.shape!=(4,) or not np.isfinite(o).all() or not np.isfinite(u).all() or (o<=0).any() or (u<0).any():
        raise ValueError('P_INVALID_POSITION')
    if not math.isfinite(cash) or not math.isfinite(fee_buffer) or fee_buffer<0:
        raise ValueError('P_INVALID_CASH_BUFFER')
    equity = cash + float(np.dot(u,o))
    reference = equity if baseline is None else baseline
    if reference<=0 or not math.isfinite(reference):
        return False
    for f in corners(down,up):
        v = u*o*f
        e = cash + float(v.sum()) - fee_buffer
        if e < FLOOR*reference-tol*reference or v.sum()>CAP_GROSS*e+tol*reference or (v>CAP_ASSET*e+tol*reference).any():
            return False
    return True


def stress_repair(cash, units, opening, prev_quote, fee, down, up, funding_buffer=0.):
    """Minimum USD sells to meet all corners, including fee and buffer effects.

    Independent exact LP. Sell limits use strictly previous-bar quote volume.
    Return (cash, units, sold USD, feasible), never mutate input arrays.
    """
    o,u,q = [np.asarray(x,float).copy() for x in (opening,units,prev_quote)]
    if any(x.shape!=(4,) for x in (o,u,q)) or not all(np.isfinite(x).all() for x in (o,u,q)) or (o<=0).any() or (u<0).any() or (q<0).any():
        raise ValueError('P_STRESS_REPAIR_INVALID_ARRAYS')
    if not math.isfinite(cash) or not math.isfinite(fee) or not 0<=fee<=.02 or not math.isfinite(funding_buffer) or funding_buffer<0:
        raise ValueError('P_STRESS_REPAIR_INVALID_SCALARS')
    pre_eq = cash+float(np.dot(u,o))
    sold=np.zeros(4)
    if pre_eq<=0:return cash,u,sold,False
    if survives(cash,u,o,down,up,funding_buffer,baseline=pre_eq):
        return cash,u,sold,True
    v=u*o
    a=[];b=[]
    for f in corners(down,up):
        fv=v*f
        base_eq=cash+float(fv.sum())-funding_buffer
        de=(1-fee)-f
        a.append(-de);b.append(base_eq-FLOOR*pre_eq)
        a.append(-f-CAP_GROSS*de);b.append(CAP_GROSS*base_eq-float(fv.sum()))
        for j in range(4):
            row=-CAP_ASSET*de.copy()
            row[j]-=f[j]
            a.append(row);b.append(CAP_ASSET*base_eq-fv[j])
    # Include current opening constraints as a separate no-shock corner.
    f=np.ones(4)
    de=(1-fee)-f
    base_eq=cash+float(v.sum())
    a.append(-f-CAP_GROSS*de);b.append(CAP_GROSS*base_eq-float(v.sum()))
    for j in range(4):
        row=-CAP_ASSET*de.copy();row[j]-=1
        a.append(row);b.append(CAP_ASSET*base_eq-v[j])
    cap=np.minimum(v,PARTICIPATION*q)
    # Dollar normalization reduces LP sensitivity to account size.
    res=linprog(np.ones(4), A_ub=np.asarray(a)/pre_eq, b_ub=np.asarray(b)/pre_eq,
                bounds=[(0,float(x)) for x in cap],method='highs',
                options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not res.success or res.x is None or not np.isfinite(res.x).all():
        return cash,u,sold,False
    sold=np.clip(res.x,0,cap)
    post_cash=cash+float(sold.sum())*(1-fee)
    post_units=np.maximum(u-sold/o,0)
    if not survives(post_cash,post_units,o,down,up,funding_buffer,baseline=pre_eq,tol=1e-8):
        return cash,u,np.zeros(4),False
    return post_cash,post_units,sold,True


def execute_open(cash,units,opening,prev_quote,target,fee,down,up,*,funding_buffer=0.,mode='capacity_1m'):
    """Pre-open governor: exact repair, stress repair, sells, then safe buys.

    Target must have been computed at close(t-1). Funding buffer must be causal.
    No current high/low, current quote volume, mark or current return accepted.
    """
    o,u,q,w=[np.asarray(x,float).copy() for x in (opening,units,prev_quote,target)]
    if any(x.shape!=(4,) for x in (o,u,q,w)) or not all(np.isfinite(x).all() for x in (o,u,q,w)) or (w<0).any() or w.max()>CAP_ASSET+1e-9 or w.sum()>CAP_GROSS+1e-9:
        raise ValueError('P_INVALID_TARGET_OR_SOURCE')
    if mode not in ('immediate','capacity_1m','capacity_10m'):
        raise ValueError('P_INVALID_CAPITAL_MODE')
    baseline=cash+float(np.dot(u,o))
    cash,u,opening_sells,ok=repair_open_lp(cash,u,o,q,fee)
    if not ok:return {'ok':False,'reason':'OPENING_REPAIR_INFEASIBLE'}
    remaining=np.maximum(PARTICIPATION*q-opening_sells,0)
    cash,u,stress_sells,ok=stress_repair(cash,u,o,remaining/PARTICIPATION,fee,down,up,funding_buffer)
    if not ok:return {'ok':False,'reason':'STRESS_REPAIR_INFEASIBLE'}
    remaining=np.maximum(remaining-stress_sells,0)
    desired=w*(cash+float(np.dot(u,o)))
    value=u*o
    cap=np.full(4,np.inf) if mode=='immediate' else remaining
    sells=np.minimum(np.maximum(value-desired,0),cap)
    cash+=float(sells.sum())*(1-fee)
    u-=sells/o
    remaining=np.maximum(remaining-sells,0)
    if not survives(cash,u,o,down,up,funding_buffer,baseline=baseline):
        return {'ok':False,'reason':'POST_SELL_STRESS_INFEASIBLE'}
    value=u*o
    buys=np.minimum(np.maximum(desired-value,0),np.full(4,np.inf) if mode=='immediate' else remaining)
    buys[(opening_sells+stress_sells)>1e-8]=0
    def feasible(k):
        b=buys*k
        new_cash=cash-float(b.sum())*(1+fee)
        new_u=u+b/o
        eq=new_cash+float(np.dot(new_u,o))
        v=new_u*o
        return (eq>0 and v.sum()<=CAP_GROSS*eq+1e-9*baseline and
                (v<=CAP_ASSET*eq+1e-9*baseline).all() and
                survives(new_cash,new_u,o,down,up,funding_buffer,baseline=baseline))
    if not feasible(0):return {'ok':False,'reason':'PRE_BUY_STRESS_INFEASIBLE'}
    k=1.
    if not feasible(1):
        low,high=0.,1.
        for _ in range(48):
            mid=(low+high)/2
            if feasible(mid):low=mid
            else:high=mid
        k=low
    buys*=k
    cash-=float(buys.sum())*(1+fee)
    u+=buys/o
    if not feasible(0) or not survives(cash,u,o,down,up,funding_buffer,baseline=baseline):
        raise AssertionError('P_POST_FILL_ENVELOPE_BREACH')
    return {'ok':True,'cash':float(cash),'units':u,'opening_repair_usd':opening_sells,
            'stress_repair_usd':stress_sells,'sells_usd':sells,'buys_usd':buys,
            'funding_buffer_usd':funding_buffer,'pre_open_equity':baseline,
            'discretionary_buy_scale':float(k)}
