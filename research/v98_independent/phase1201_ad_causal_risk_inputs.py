#!/usr/bin/env python3
"""AD strict t-1 336/720h causal risk inputs for actual-open governor."""
from __future__ import annotations
import numpy as np
import pandas as pd
from phase1189_ad_online_core_router import validate_source


def causal_risk(op,hi,lo,cl,quote,funding,event):
    idx,(_,high,low,close,q,rate,_)=validate_source(op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    if n<=720:
        raise ValueError('AD1201_MINIMUM_WARMUP')
    downside=np.zeros_like(close)
    upside=np.zeros_like(close)
    downside[1:]=1-low[1:]/close[:-1]
    upside[1:]=high[1:]/close[:-1]-1
    def prior_rolling(a,window,op):
        f=pd.DataFrame(a,index=idx)
        x=f.rolling(window,min_periods=window)
        return getattr(x,op)().shift(1).to_numpy(float)
    down=np.minimum(.99,np.maximum(.25,prior_rolling(downside,336,'max')))
    up=np.maximum(.30,prior_rolling(upside,336,'max'))
    qmin=prior_rolling(q,336,'min')
    qprior=np.vstack([np.full(4,np.nan),q[:-1]])
    fbound=np.maximum(.005,prior_rolling(np.abs(rate),720,'sum'))
    for x in (down,up,qmin,qprior,fbound):
        if x.shape!=(n,4) or not np.isfinite(x[720:]).all():
            raise ValueError('AD1201_MISSING_PRIOR_RISK')
    if np.any(qmin[720:]<0) or np.any(qprior[720:]<0):
        raise ValueError('AD1201_QUOTE_CAPACITY')
    return {'down':down,'up':up,'min_quote':qmin,
            'prior_quote':qprior,'funding_bound':fbound}
