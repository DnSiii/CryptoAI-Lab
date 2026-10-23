#!/usr/bin/env python3
"""V98 Independent S signed, 16-corner, funded pre-trade LP oracle.

No price download or PnL. Uses t-1 target, volume and shock supplied by caller.
Precommitted Phase1073; rejected Q/R architectures remain untouched.
"""
from __future__ import annotations
import itertools
import math
import numpy as np
from scipy.optimize import linprog

N=4; FLOOR=.25; GROSS_CAP=1.35; ASSET_CAP=.45; NET_CAP=.75
PARTICIPATION=.01; MODES=('immediate','capacity_1m','capacity_10m')

def corners(down,up):
    d=np.asarray(down,float);u=np.asarray(up,float)
    if (d.shape!=(N,) or u.shape!=(N,) or not np.isfinite(d).all() or
        not np.isfinite(u).all() or (d<0).any() or (d>=1).any() or (u<0).any()):
        raise ValueError('S_INVALID_CAUSAL_SHOCK')
    return np.asarray([np.where(mask,1+u,1-d) for mask in itertools.product((False,True),repeat=N)])

def audit(cash,units,opening,down,up,*,baseline=None,buffer=0.,tol=1e-7):
    u=np.asarray(units,float);o=np.asarray(opening,float)
    if (u.shape!=(N,) or o.shape!=(N,) or not np.isfinite(u).all() or
        not np.isfinite(o).all() or (o<=0).any() or not math.isfinite(cash) or
        not math.isfinite(buffer) or buffer<0):
        raise ValueError('S_INVALID_SIGNED_STATE')
    base=cash+float(np.dot(u,o)) if baseline is None else float(baseline)
    if not math.isfinite(base) or base<=0:
        return {'ok':False,'reason':'S_NONPOSITIVE_BASELINE'}
    notion=u*o;worst=float('inf')
    for f in np.vstack((np.ones(N),corners(down,up))):
        x=notion*f;equity=cash+float(x.sum())-buffer
        worst=min(worst,equity)
        if equity<=0 or equity<FLOOR*base-tol*base:
            return {'ok':False,'reason':'S_EQUITY_FLOOR','worst_equity':worst}
        if np.abs(x).sum()>GROSS_CAP*equity+tol*base:
            return {'ok':False,'reason':'S_GROSS','worst_equity':worst}
        if np.abs(x).max()>ASSET_CAP*equity+tol*base:
            return {'ok':False,'reason':'S_ASSET','worst_equity':worst}
        if abs(x.sum())>NET_CAP*equity+tol*base:
            return {'ok':False,'reason':'S_NET','worst_equity':worst}
    return {'ok':True,'reason':None,'worst_equity':worst}

def execute(cash,units,opening,prior_quote,target,fee,down,up,*,buffer=0.,mode='immediate'):
    u,o,q,w=[np.asarray(v,float) for v in (units,opening,prior_quote,target)]
    if (any(v.shape!=(N,) for v in (u,o,q,w)) or
        not all(np.isfinite(v).all() for v in (u,o,q,w)) or (o<=0).any() or (q<0).any()):
        raise ValueError('S_INVALID_EXECUTION_INPUT')
    if (np.abs(w).max()>ASSET_CAP+1e-10 or np.abs(w).sum()>GROSS_CAP+1e-10 or
        abs(w.sum())>NET_CAP+1e-10):
        raise ValueError('S_INVALID_TARGET_CAPS')
    if (not math.isfinite(cash) or not math.isfinite(fee) or not 0<=fee<=.02 or
        not math.isfinite(buffer) or buffer<0 or mode not in MODES):
        raise ValueError('S_INVALID_EXECUTION_SETTINGS')
    fs=np.vstack((np.ones(N),corners(down,up)))
    base=cash+float(np.dot(u,o))
    if not math.isfinite(base) or base<=0:
        return {'ok':False,'reason':'S_PRETRADE_EQUITY_NONPOSITIVE'}
    old=u*o/base;buf=buffer/base
    # normalized 24-variable LP: position +/-; trade buy/sell; target deviation +/-.
    n=24;objective=np.zeros(n);objective[:8]=.0001;objective[8:16]=.002;objective[16:24]=1.
    ae=[];be=[];au=[];bu=[]
    for j in range(N):
        row=np.zeros(n);row[j]=1;row[4+j]=-1;row[8+j]=-1;row[12+j]=1
        ae.append(row);be.append(old[j])
        row=np.zeros(n);row[j]=1;row[4+j]=-1;row[16+j]=-1;row[20+j]=1
        ae.append(row);be.append(w[j])
    for f in fs:
        eco=np.zeros(n);eco[:4]=f-1;eco[4:8]=1-f;eco[8:16]=-fee
        eb=1.-buf
        au.append(-eco);bu.append(eb-FLOOR)
        gross=np.zeros(n);gross[:4]=f;gross[4:8]=f
        au.append(gross-GROSS_CAP*eco);bu.append(GROSS_CAP*eb)
        for j in range(N):
            row=np.zeros(n);row[j]=f[j];row[4+j]=f[j]
            au.append(row-ASSET_CAP*eco);bu.append(ASSET_CAP*eb)
        net=np.zeros(n);net[:4]=f;net[4:8]=-f
        au.append(net-NET_CAP*eco);bu.append(NET_CAP*eb)
        au.append(-net-NET_CAP*eco);bu.append(NET_CAP*eb)
    if mode!='immediate':
        for j in range(N):
            row=np.zeros(n);row[8+j]=1;row[12+j]=1
            au.append(row);bu.append(PARTICIPATION*q[j]/base)
    res=linprog(objective,A_ub=np.asarray(au),b_ub=np.asarray(bu),
                A_eq=np.asarray(ae),b_eq=np.asarray(be),bounds=[(0,None)]*n,method='highs')
    if not res.success or res.x is None or not np.isfinite(res.x).all():
        return {'ok':False,'reason':'S_SIGNED_LP_INFEASIBLE','solver_status':int(res.status)}
    notion=(res.x[:4]-res.x[4:8])*base
    trades=notion-u*o;turnover=float(np.abs(trades).sum())
    if mode!='immediate' and (np.abs(trades)>PARTICIPATION*q+1e-7*base).any():
        return {'ok':False,'reason':'S_PARTICIPATION_POSTCHECK'}
    new_cash=float(cash-trades.sum()-fee*turnover);new_units=notion/o
    check=audit(new_cash,new_units,o,down,up,baseline=base,buffer=buffer)
    if not check['ok']:return {'ok':False,'reason':'S_POSTCHECK_'+check['reason']}
    return {'ok':True,'reason':None,'cash':new_cash,'units':new_units,
            'trade_usd':trades,'turnover_usd':turnover,'fee_usd':fee*turnover,
            'pretrade_equity':base,'worst_stressed_equity':check['worst_equity']}
