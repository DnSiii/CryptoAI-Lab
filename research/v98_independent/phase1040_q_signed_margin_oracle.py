#!/usr/bin/env python3
"""V98 Independent Q: source-only signed four-asset execution/margin oracle.

No historical PnL, Q selection, 2025+ access or external engines. Only caller
supplied t-1 shocks, t-1 volume, fee and funding buffer may influence trades.
"""
from __future__ import annotations
import itertools
import math
import numpy as np
from scipy.optimize import linprog

N = 4
FLOOR = .25
GROSS_CAP = 1.40
ASSET_CAP = .55
NET_CAP = .65
PARTICIPATION = .01  # fixed Q infrastructure limit


def factors(down, up):
    d, h = np.asarray(down, float), np.asarray(up, float)
    if d.shape != (N,) or h.shape != (N,) or not np.isfinite(d).all() or not np.isfinite(h).all() or (d < 0).any() or (d >= 1).any() or (h < 0).any():
        raise ValueError('Q_INVALID_SHOCK')
    return np.asarray([np.where(b, 1+h, 1-d) for b in itertools.product((False, True), repeat=N)])


def corner_audit(cash, units, opening, down, up, *, baseline=None, buffer=0., tolerance=1e-9):
    u, o = np.asarray(units, float), np.asarray(opening, float)
    if u.shape != (N,) or o.shape != (N,) or not np.isfinite(u).all() or not np.isfinite(o).all() or (o <= 0).any() or not math.isfinite(cash) or not math.isfinite(buffer) or buffer < 0:
        raise ValueError('Q_INVALID_SIGNED_STATE')
    eq0 = cash + float(np.dot(u, o))
    base = eq0 if baseline is None else float(baseline)
    if not math.isfinite(base) or base <= 0:
        return {'ok':False, 'reason':'Q_NONPOSITIVE_BASELINE'}
    x = u * o
    worst = float('inf')
    for f in np.vstack((np.ones(N), factors(down, up))):
        vf = x * f
        equity = cash + float(vf.sum()) - buffer
        worst = min(worst, equity)
        tol = tolerance * base
        if equity < FLOOR*base - tol or equity <= 0:
            return {'ok':False,'reason':'Q_EQUITY_FLOOR','worst_equity':worst}
        if float(np.abs(vf).sum()) > GROSS_CAP*equity + tol:
            return {'ok':False,'reason':'Q_GROSS','worst_equity':worst}
        if np.max(np.abs(vf)) > ASSET_CAP*equity + tol:
            return {'ok':False,'reason':'Q_ASSET','worst_equity':worst}
        if abs(float(vf.sum())) > NET_CAP*equity + tol:
            return {'ok':False,'reason':'Q_NET','worst_equity':worst}
    return {'ok':True,'reason':None,'worst_equity':worst}


def execute_signed(cash, units, opening, prior_quote, desired_weights, fee, down, up, *, funding_buffer=0., mode='capacity_1m'):
    """LP target tracking under all 16 corners, volume caps and signed margin.

    Targets refer to *pretrade* equity. Returns a new state or fails closed.
    No future OHLC/quote/funding input is accepted by this interface.
    """
    u,o,q,w = [np.asarray(z,float) for z in (units,opening,prior_quote,desired_weights)]
    if any(z.shape!=(N,) for z in (u,o,q,w)) or not all(np.isfinite(z).all() for z in (u,o,q,w)) or (o<=0).any() or (q<0).any() or np.max(np.abs(w))>ASSET_CAP+1e-12 or np.abs(w).sum()>GROSS_CAP+1e-12 or abs(w.sum())>NET_CAP+1e-12:
        raise ValueError('Q_INVALID_INPUT')
    if not math.isfinite(cash) or not math.isfinite(fee) or not 0<=fee<=.02 or not math.isfinite(funding_buffer) or funding_buffer<0 or mode not in ('immediate','capacity_1m','capacity_10m'):
        raise ValueError('Q_INVALID_EXECUTION_SETTINGS')
    base=cash+float(np.dot(u,o))
    if base<=0:return {'ok':False,'reason':'Q_PRETRADE_EQUITY_NONPOSITIVE'}
    old=u*o
    target=w*base
    # variables: 0:4 xplus, 4:8 xminus, 8:12 tplus, 12:16 tminus,
    # 16:20 deviation_plus, 20:24 deviation_minus.
    n=24
    obj=np.zeros(n);obj[8:16]=.002;obj[16:24]=1.
    ae=[];be=[]
    for j in range(N):
        row=np.zeros(n);row[j]=1;row[4+j]=-1;row[8+j]=-1;row[12+j]=1
        ae.append(row);be.append(old[j])
        row=np.zeros(n);row[j]=1;row[4+j]=-1;row[16+j]=-1;row[20+j]=1
        ae.append(row);be.append(target[j])
    au=[];bu=[]
    for f in np.vstack((np.ones(N), factors(down,up))):
        # equity = pretrade equity + sum_j((f_j-1)*x_j) - fee*turnover - buffer
        eco=np.zeros(n);eco[:4]=f-1;eco[4:8]=1-f;eco[8:16]=-fee
        eb=base-funding_buffer
        # equity >= floor*base
        au.append(-eco);bu.append(eb-FLOOR*base)
        # abs gross <= grosscap*equity
        row=np.zeros(n);row[:4]=f;row[4:8]=f
        au.append(row-GROSS_CAP*eco);bu.append(GROSS_CAP*eb)
        for j in range(N):
            row=np.zeros(n);row[j]=f[j];row[4+j]=f[j]
            au.append(row-ASSET_CAP*eco);bu.append(ASSET_CAP*eb)
        row=np.zeros(n);row[:4]=f;row[4:8]=-f
        au.append(row-NET_CAP*eco);bu.append(NET_CAP*eb)
        au.append(-row-NET_CAP*eco);bu.append(NET_CAP*eb)
    for j in range(N):
        row=np.zeros(n);row[8+j]=1;row[12+j]=1
        if mode!='immediate':
            au.append(row);bu.append(PARTICIPATION*q[j])
    # Normalize objective and all linear constraints to equity, for stability.
    res=linprog(obj, A_ub=np.asarray(au)/base, b_ub=np.asarray(bu)/base,
                A_eq=np.asarray(ae)/base, b_eq=np.asarray(be)/base,
                bounds=[(0,None)]*n, method='highs')
    if not res.success or res.x is None or not np.isfinite(res.x).all():
        return {'ok':False,'reason':'Q_SIGNED_LP_INFEASIBLE','solver_status':int(res.status)}
    # Executed trades derived from net positions; avoid split-variable cancellation.
    x=res.x[:4]-res.x[4:8]
    trades=x-old
    turnover=float(np.abs(trades).sum())
    if mode!='immediate' and (np.abs(trades)>PARTICIPATION*q+1e-7*base).any():
        return {'ok':False,'reason':'Q_PARTICIPATION_POSTCHECK'}
    new_cash=float(cash-trades.sum()-fee*turnover)
    new_units=x/o
    audit=corner_audit(new_cash,new_units,o,down,up,baseline=base,buffer=funding_buffer,tolerance=1e-7)
    if not audit['ok']:
        return {'ok':False,'reason':'Q_SIGNED_POSTCHECK_'+audit['reason']}
    return {'ok':True,'reason':None,'cash':new_cash,'units':new_units,
            'trade_usd':trades,'turnover_usd':turnover,'fee_usd':fee*turnover,
            'pretrade_equity':base,'worst_stressed_equity':audit['worst_equity']}
