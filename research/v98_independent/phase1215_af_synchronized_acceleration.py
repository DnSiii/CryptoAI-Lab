#!/usr/bin/env python3
"""V98 AF synchronized positive 6h acceleration opportunity, source-only."""
from __future__ import annotations
import numpy as np
from phase1214_af_dual_ewma_core import validate_source

BASELINE=336
LOOKBACK=6
MAD_SCALE=1.4826
MAD_FLOOR=.001
ROBUST_SIGMAS=3.
HOLD=12
GROSS=.20


def af_opportunity_source(op,hi,lo,cl,quote,funding,event):
    idx,(_,_,_,close,q,_,_)=validate_source(
        op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    r6=np.zeros_like(close)
    r6[LOOKBACK:]=np.log(close[LOOKBACK:]/close[:-LOOKBACK])
    out=np.zeros((n,4),dtype=float)
    until=-1
    active=np.zeros(4,dtype=float)
    for t in range(BASELINE+LOOKBACK,n):
        history=r6[t-BASELINE:t]
        median=np.median(history,axis=0)
        mad=np.median(np.abs(history-median),axis=0)
        threshold=np.maximum(0.,median+ROBUST_SIGMAS*MAD_SCALE*
                             np.maximum(mad,MAD_FLOOR))
        liquid=q[t-BASELINE:t].min(axis=0)>0
        confirmed=(r6[t]>threshold)&(r6[t]>0)&liquid
        if int(confirmed.sum())>=2:
            active=np.zeros(4,dtype=float)
            active[confirmed]=GROSS/confirmed.sum()
            until=t+HOLD
        if t<until:
            out[t]=active
    if (not np.isfinite(out).all() or np.any(out<0) or
            np.any(out.sum(axis=1)>GROSS+1e-10)):
        raise ValueError('AF1215_OPPORTUNITY_BUDGET')
    return out
