#!/usr/bin/env python3
"""V98 N-only opening gap repair primitive; synthetic contract, NO historical PnL."""
from __future__ import annotations
import math
import numpy as np

ASSET_CAP=.70
GROSS_CAP=1.75
PARTICIPATION=.05


def repair_open(cash,units,opening,prev_quote,fee):
    """Minimal sell-only sequential projection under causal previous-hour volume.

    Caller supplies open(t), carried units and quote_volume(t-1); returns
    (post_cash, post_units, sell_notional, success), with no discretionary buys.
    """
    u=np.asarray(units,dtype=float).copy()
    p=np.asarray(opening,dtype=float)
    q=np.asarray(prev_quote,dtype=float)
    if u.shape!=(4,) or p.shape!=(4,) or q.shape!=(4,):raise ValueError('four assets required')
    if not all(np.isfinite(v).all() for v in (u,p,q)) or (u<0).any() or (p<=0).any() or (q<0).any():
        raise ValueError('invalid causal opening source')
    if not math.isfinite(cash) or not math.isfinite(fee) or not 0<=fee<=.02:
        raise ValueError('invalid cash or all-in fee')
    cash=float(cash)
    cap=PARTICIPATION*q
    sold=np.zeros(4,dtype=float)
    for _ in range(128):
        v=u*p;gross=float(v.sum());eq=cash+gross
        if not math.isfinite(eq) or eq<=0:return cash,u,sold,False
        asset_excess=v-ASSET_CAP*eq
        gross_excess=gross-GROSS_CAP*eq
        if max(float(asset_excess.max()),gross_excess)<=1e-9*eq:
            return cash,u,sold,True
        if asset_excess.max()>1e-9*eq:
            j=int(np.argmax(asset_excess))
            required=float(asset_excess[j]/(1-ASSET_CAP*fee))
        else:
            # Gross-only excess: sell largest available inventory first.
            available=np.minimum(v,cap-sold)
            j=int(np.argmax(available))
            required=float(gross_excess/(1-GROSS_CAP*fee))
        available=max(0.,min(float(v[j]),float(cap[j]-sold[j])))
        take=min(required,available)
        if take<=max(1e-11*eq,1e-9):return cash,u,sold,False
        u[j]-=take/p[j]
        cash+=take*(1-fee)
        sold[j]+=take
    # Iteration budget exhaustion must never be silently accepted.
    return cash,u,sold,False
