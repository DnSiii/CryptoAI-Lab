#!/usr/bin/env python3
"""V98 AF independent funded long-only relative-value rotation, source-only."""
from __future__ import annotations
import numpy as np
from phase1214_af_dual_ewma_core import validate_source

LOOKBACK=96
LIQUIDITY=336
GROSS=.15
ASSET_CAP=.10


def allocate_residual(score):
    s=np.asarray(score,dtype=float)
    if s.shape!=(4,) or not np.isfinite(s).all() or np.any(s<0):
        raise ValueError('AF1216_RESIDUAL')
    out=np.zeros(4)
    eligible=s>0
    for _ in range(4):
        remaining=GROSS-out.sum()
        if remaining<=1e-12 or not eligible.any():
            break
        trial=out[eligible]+remaining*s[eligible]/s[eligible].sum()
        capped=trial>=ASSET_CAP
        ids=np.flatnonzero(eligible)
        if not capped.any():
            out[ids]=trial
            break
        out[ids[capped]]=ASSET_CAP
        eligible[ids[capped]]=False
    return out


def af_relative_value_source(op,hi,lo,cl,quote,funding,event):
    idx,(_,_,_,close,q,_,_)=validate_source(
        op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    out=np.zeros((n,4))
    for t in range(LIQUIDITY,n):
        momentum=np.log(close[t]/close[t-LOOKBACK])
        residual=momentum-np.median(momentum)
        liquid=q[t-LIQUIDITY:t].min(axis=0)>0
        eligible=(momentum>0)&(residual>0)&liquid
        if int(eligible.sum())<2:
            continue
        score=np.maximum(0,residual)
        score[~eligible]=0
        out[t]=allocate_residual(score)
    if (not np.isfinite(out).all() or np.any(out<0) or
            np.any(out>ASSET_CAP+1e-10) or
            np.any(out.sum(axis=1)>GROSS+1e-10)):
        raise ValueError('AF1216_ROTATION_BUDGET')
    return out
