#!/usr/bin/env python3
"""V98 AF independent causal funding/liquidity/breadth router, source-only."""
from __future__ import annotations
import numpy as np
from phase1214_af_dual_ewma_core import validate_source

WARMUP=336
VOL_WINDOW=72
BREADTH_WINDOW=24
FUNDING_WINDOW=168
OFF_VOL=.025
ON_VOL=.012
OFF_FUNDING=.015
ON_FUNDING=.008
ON_STREAK=6
CRASH_LOG=-.05


def af_router_source(op,hi,lo,cl,quote,funding,event):
    idx,(_,_,_,close,q,rate,_)=validate_source(
        op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    out=np.zeros((n,3))
    out[:,1]=1.
    market=np.zeros(n)
    market[1:]=np.log(close[1:]/close[:-1]).mean(axis=1)
    streak=0
    state=1
    for t in range(WARMUP,n):
        vol=float(np.std(market[t-VOL_WINDOW+1:t+1],ddof=0))
        breadth=float(np.mean(close[t]>close[t-BREADTH_WINDOW]))
        fstress=float(np.abs(rate[t-FUNDING_WINDOW+1:t+1]).sum())
        liquid=bool(np.all(q[t-WARMUP:t].min(axis=0)>0))
        off=(market[t]<=CRASH_LOG or not liquid or vol>OFF_VOL or
             fstress>OFF_FUNDING or breadth<=.25)
        on=(vol<ON_VOL and breadth>=.75 and fstress<ON_FUNDING and liquid)
        if off:
            state=0
            streak=0
        elif on:
            streak+=1
            state=2 if streak>=ON_STREAK else 1
        else:
            state=1
            streak=0
        out[t]=0
        out[t,state]=1
    if (not np.isfinite(out).all() or
            np.any((out!=0)&(out!=1)) or
            not np.all(out.sum(axis=1)==1)):
        raise ValueError('AF1218_ROUTER_INVARIANTS')
    return out
