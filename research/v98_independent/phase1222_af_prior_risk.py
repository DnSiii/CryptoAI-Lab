#!/usr/bin/env python3
"""V98 AF independent strict prior 336/720h causal risk arrays; no PnL."""
from __future__ import annotations
import numpy as np
import pandas as pd
from phase1214_af_dual_ewma_core import validate_source


def af_prior_risk(op,hi,lo,cl,quote,funding,event):
    idx,(_,high,low,close,q,rate,_)=validate_source(
        op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    if n<=720:
        raise ValueError('AF1222_MINIMUM_720_WARMUP')
    downside=np.zeros_like(close)
    upside=np.zeros_like(close)
    downside[1:]=np.maximum(0.,1-low[1:]/close[:-1])
    upside[1:]=np.maximum(0.,high[1:]/close[:-1]-1)
    def prior_roll(a,window,kind):
        x=pd.DataFrame(a,index=idx).rolling(window,min_periods=window)
        return getattr(x,kind)().shift(1).to_numpy(float)
    down=np.minimum(.99,np.maximum(.40,prior_roll(downside,336,'max')))
    up=np.maximum(.50,prior_roll(upside,336,'max'))
    min_quote=prior_roll(q,336,'min')
    prior_quote=np.vstack((np.full((1,4),np.nan),q[:-1]))
    funding_bound=np.maximum(.007,prior_roll(np.abs(rate),720,'sum'))
    result={'down':down,'up':up,'min_quote':min_quote,
            'prior_quote':prior_quote,'funding_bound':funding_bound}
    if any(x.shape!=(n,4) or not np.isfinite(x[720:]).all()
           for x in result.values()):
        raise ValueError('AF1222_NONFINITE_PRIOR_RISK')
    if (np.any(down[720:]<0) or np.any(down[720:]>=1) or
            np.any(up[720:]<0) or np.any(min_quote[720:]<0) or
            np.any(prior_quote[720:]<0) or np.any(funding_bound[720:]<0)):
        raise ValueError('AF1222_INVALID_PRIOR_RISK')
    return result
