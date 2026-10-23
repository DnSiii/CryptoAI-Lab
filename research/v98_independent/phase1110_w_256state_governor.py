#!/usr/bin/env python3
"""V98 W: 256 executable portfolio states, no PnL or holdout. Inputs t-1 only."""
from __future__ import annotations
import itertools
import numpy as np

N=4
STATES=np.asarray(tuple(itertools.product(range(4),repeat=N)),dtype=np.int8)
ASSET_CAP,NET_CAP,GROSS_CAP=.45,.75,1.35
EQUITY_FLOOR=.25
FEE,SLIPPAGE=.002,.002
PARTICIPATION=.01
FUNDING_EVENTS_RESERVE=6
ITERATIONS=32
QUANTUM=1e-6

def _check(raw,prevclose,down,up,prior_funding_max,prior_quote_usd,capital_usd):
    w,p,d,h,f,q=[np.asarray(v,dtype=np.float64) for v in
        (raw,prevclose,down,up,prior_funding_max,prior_quote_usd)]
    if (any(v.shape!=(N,) or not np.isfinite(v).all() for v in (w,p,d,h,f,q))
        or (p<=0).any() or (d<0).any() or (d>=1).any() or (h<0).any()
        or (f<0).any() or (q<0).any() or not np.isfinite(capital_usd)
        or capital_usd<=0):
        raise ValueError('W_INVALID_CAUSAL_INPUT')
    return w,p,d,h,f,q

def executable_256_feasible(weights,prevclose,down,up,prior_funding_max,
                            prior_quote_usd,capital_usd,*,details=False):
    """States: live close, adverse pre-stop, fully stopped, 1/3 limit then adverse.

    Includes hedge removal, stop-first adverse fill, liquidity and signed funding
    reserve. This is a conservative scenario oracle, not a full path simulator.
    """
    w,p,d,h,f,q=_check(weights,prevclose,down,up,prior_funding_max,
                       prior_quote_usd,capital_usd)
    max_fill_factor=np.maximum(1+h,1-d)*(1+SLIPPAGE)
    capacity_ok=np.all(np.abs(w)*capital_usd*max_fill_factor<=
                       PARTICIPATION*q+1e-8)
    sign=np.sign(w)[None,:]
    adverse=np.where(w>=0,1-d,1+h)[None,:]
    favorable=np.where(w>=0,1+h,1-d)[None,:]
    filled=np.where(STATES==2,1.,np.where(STATES==3,1./3.,0.))
    fill_factor=np.where(STATES==2,adverse,np.where(STATES==3,favorable,1.))
    mark_factor=np.where(STATES==0,1.,adverse)
    post=w[None,:]*(1-filled)*mark_factor
    proceeds=w[None,:]*filled*fill_factor*(1-sign*SLIPPAGE)
    exit_cost=FEE*np.abs(w[None,:])*filled*fill_factor*(1+SLIPPAGE)
    entry_cost=(FEE+SLIPPAGE)*np.abs(w).sum()
    cash=1.-w.sum()-entry_cost+np.sum(proceeds-exit_cost,axis=1)
    reserve=FUNDING_EVENTS_RESERVE*np.sum(np.abs(w)*f*(1+h))
    equity=cash+post.sum(axis=1)-reserve
    max_asset=np.max(np.abs(post),axis=1)
    gross=np.abs(post).sum(axis=1)
    net=np.abs(post.sum(axis=1))
    feasible=(bool(capacity_ok) and bool(np.isfinite(equity).all())
        and bool(np.all(equity>=EQUITY_FLOOR-1e-12))
        and bool(np.all(max_asset<=ASSET_CAP*equity+1e-12))
        and bool(np.all(gross<=GROSS_CAP*equity+1e-12))
        and bool(np.all(net<=NET_CAP*equity+1e-12)))
    if not details:return feasible
    return {'feasible':feasible,'states_checked':len(STATES),
        'capacity_ok':bool(capacity_ok),'worst_equity':float(equity.min()),
        'max_asset_over_equity':float(np.max(max_asset/np.maximum(equity,1e-12))),
        'max_net_over_equity':float(np.max(net/np.maximum(equity,1e-12))),
        'max_gross_over_equity':float(np.max(gross/np.maximum(equity,1e-12))),
        'worst_equity_state':STATES[int(np.argmin(equity))].tolist(),
        'funding_reserve_fraction':float(reserve)}

def max_feasible_w(raw,prevclose,down,up,prior_funding_max,prior_quote_usd,
                   capital_usd):
    """Maximize common positive scalar by exactly 32 quantized bisections."""
    w,p,d,h,f,q=_check(raw,prevclose,down,up,prior_funding_max,
                       prior_quote_usd,capital_usd)
    if not np.any(w):return np.zeros(N,dtype=float)
    lo,hi=0.,1.
    for _ in range(ITERATIONS):
        mid=(lo+hi)*.5
        proposal=np.trunc(w*mid/QUANTUM)*QUANTUM
        if executable_256_feasible(proposal,p,d,h,f,q,capital_usd):lo=mid
        else:hi=mid
    out=np.trunc(w*lo/QUANTUM)*QUANTUM
    if not executable_256_feasible(out,p,d,h,f,q,capital_usd):
        raise AssertionError('W_256_STATE_SERIALIZATION_BREACH')
    return out
