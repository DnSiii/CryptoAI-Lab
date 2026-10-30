#!/usr/bin/env python3
"""V98 AH1237 signed 168h BTC-beta-neutral 48h residual reversion source."""
from __future__ import annotations
import numpy as np


def ah_relative_value_source(close):
    c=np.asarray(close,dtype=float)
    if c.ndim!=2 or c.shape[1]!=4 or not np.isfinite(c).all() or np.any(c<=0):
        raise ValueError('AH1237_SOURCE_GEOMETRY')
    n=len(c)
    weights=np.zeros((n,4))
    betas=np.zeros((n,4))
    logc=np.log(c)
    lr=np.diff(logc,axis=0)
    for t in range(168,n):
        window=lr[t-168:t]
        x=window[:,0]
        centered=x-x.mean()
        var=float(np.mean(centered**2))
        if var<1e-10:continue
        y=window-window.mean(axis=0)
        beta=np.clip(np.mean(y*centered[:,None],axis=0)/var,-3.,3.)
        beta[0]=1.
        betas[t]=beta
        residual48=(logc[t]-logc[t-48]) - beta*(logc[t,0]-logc[t-48,0])
        resid_hour=window-beta[None,:]*x[:,None]
        scale=np.maximum(np.sqrt(48*np.mean(resid_hour**2,axis=0)),1e-4)
        raw=-residual48/scale
        A=np.vstack((np.ones(4),beta))
        gram=A@A.T
        neutral=raw-A.T@(np.linalg.pinv(gram,rcond=1e-12)@(A@raw))
        gross=float(np.abs(neutral).sum())
        if gross>1e-10:
            weights[t]=neutral/gross
            if abs(weights[t].sum())>1e-7 or abs(weights[t]@beta)>1e-7:
                raise ValueError('AH1237_BETA_NEUTRALITY')
    return weights,betas
