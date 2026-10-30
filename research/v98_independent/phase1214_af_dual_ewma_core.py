#!/usr/bin/env python3
"""V98 AF independent long-only dual-EWMA compounded-growth source, no PnL."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
START=pd.Timestamp('2022-12-01T00:00:00Z')
END_EXCLUSIVE=pd.Timestamp('2025-01-01T00:00:00Z')
FAST_ALPHA=2/(36+1)
SLOW_ALPHA=2/(288+1)
FAST_SHARE=.70
SLOW_SHARE=.30
FRICTION_HURDLE=.00015
LIQUIDITY_WINDOW=336
CORE_GROSS=.75
ASSET_CAP=.30


def validate_source(op,hi,lo,cl,quote,funding,event):
    frames=(op,hi,lo,cl,quote,funding,event)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in frames):
        raise ValueError('AF1214_CLEAN4_COLUMNS')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or
            len(idx)<=LIQUIDITY_WINDOW or idx[0]!=START or
            idx[-1]>=END_EXCLUSIVE or
            not idx.equals(pd.date_range(START,periods=len(idx),freq='h')) or
            any(not x.index.equals(idx) for x in frames)):
        raise ValueError('AF1214_TRAINING_CHRONOLOGY')
    arrays=tuple(x.to_numpy(float) for x in frames)
    if any(x.shape!=(len(idx),4) or not np.isfinite(x).all() for x in arrays):
        raise ValueError('AF1214_NONFINITE')
    o,h,l,c,q,f,e=arrays
    if (np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
            np.any(h<np.maximum(o,c)) or np.any(l>np.minimum(o,c)) or
            np.any(q<0)):
        raise ValueError('AF1214_OHLC_QUOTE')
    if (np.any((e!=0)&(e!=1)) or np.any(f[e==0]!=0) or
            np.any((e!=0)&(idx.hour.to_numpy()[:,None]%8!=0))):
        raise ValueError('AF1214_NATIVE_MASK')
    return idx,arrays


def capped_growth(scores):
    s=np.asarray(scores,dtype=float)
    if s.shape!=(4,) or not np.isfinite(s).all() or np.any(s<0):
        raise ValueError('AF1214_SCORE')
    w=np.zeros(4)
    eligible=s>0
    for _ in range(4):
        remaining=CORE_GROSS-w.sum()
        if remaining<=1e-12 or not eligible.any():
            break
        share=remaining*s[eligible]/s[eligible].sum()
        trial=w[eligible]+share
        cap=trial>=ASSET_CAP
        idx=np.flatnonzero(eligible)
        if not cap.any():
            w[idx]=trial
            break
        w[idx[cap]]=ASSET_CAP
        eligible[idx[cap]]=False
    if (np.any(w<0) or np.any(w>ASSET_CAP+1e-10) or
            w.sum()>CORE_GROSS+1e-10):
        raise ValueError('AF1214_BUDGET')
    return w


def af_growth_source(op,hi,lo,cl,quote,funding,event):
    idx,(_,_,_,close,q,_,_)=validate_source(op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    out=np.zeros((n,4),dtype=float)
    fast=np.zeros(4)
    slow=np.zeros(4)
    for t in range(1,n):
        completed=np.log(close[t]/close[t-1])
        fast=(1-FAST_ALPHA)*fast+FAST_ALPHA*completed
        slow=(1-SLOW_ALPHA)*slow+SLOW_ALPHA*completed
        if t<LIQUIDITY_WINDOW:
            continue
        valid=(fast>0)&(slow>0)&(q[t-LIQUIDITY_WINDOW:t].min(axis=0)>0)
        if valid.sum()<2:
            continue
        score=np.maximum(0,FAST_SHARE*fast+SLOW_SHARE*slow-FRICTION_HURDLE)
        score[~valid]=0
        out[t]=capped_growth(score)
    if (not np.isfinite(out).all() or np.any(out<0) or
            np.any(out>ASSET_CAP+1e-10) or
            np.any(out.sum(axis=1)>CORE_GROSS+1e-10)):
        raise ValueError('AF1214_SOURCE_INVARIANTS')
    return out


def source_digest(index,weights):
    if weights.shape!=(len(index),4):
        raise ValueError('AF1214_DIGEST_SHAPE')
    quant=np.rint(weights*1_000_000).astype('<i8')
    return hashlib.sha256(b'AF1214_SOURCE_ONLY_V1\n'+
        index.tz_convert('UTC').asi8.astype('<i8').tobytes()+
        quant.tobytes()).hexdigest()
