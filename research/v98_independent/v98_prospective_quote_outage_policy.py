#!/usr/bin/env python3
"""Prospective V98 source-safety gate; never retroactively rescues rejected engines."""
from __future__ import annotations
import numpy as np
COOLDOWN=24

def quote_safe(quote,t,feature_lags=(),continuous_windows=()):
    """Only completed quote bars <=t. Reject invalid feature endpoints and windows.

    feature_lags: historical endpoint offsets used by preregistered indicators.
    continuous_windows: historical quote windows of length W ending at t.
    This function controls NEW entries only; never blocks risk exits.
    """
    q=np.asarray(quote,dtype=float)
    if (q.ndim!=2 or q.shape[1]!=4 or
        not isinstance(t,(int,np.integer)) or t<0 or t>=len(q)):
        raise ValueError('V98_QUOTE_INVALID_SOURCE')
    lags=tuple(feature_lags);windows=tuple(continuous_windows)
    if (any(not isinstance(k,(int,np.integer)) or k<0 for k in lags) or
        any(not isinstance(w,(int,np.integer)) or w<1 for w in windows)):
        raise ValueError('V98_QUOTE_INVALID_FEATURE_SPEC')
    history=max((COOLDOWN,*lags,*windows))
    if t<history:return False
    segments=[q[t-COOLDOWN+1:t+1]]
    segments.extend(q[t-k:t-k+1] for k in lags)
    segments.extend(q[t-w+1:t+1] for w in windows)
    for segment in segments:
        if not np.isfinite(segment).all() or np.any(segment<0):
            raise ValueError('V98_QUOTE_INVALID_FEATURE_SOURCE')
        if not np.all(segment>0):return False
    return True

def static_check():
    q=np.ones((800,4),dtype=float)
    lags=(6,24,168,336,504)
    windows=(168,)
    assert quote_safe(q,700,lags,windows)
    # Single asset outage at t=600: cooldown, continuous windows and endpoint.
    q[600,2]=0.
    for t in (600,601,623,650,767,768):
        assert not quote_safe(q,t,lags,windows)
    assert quote_safe(q,769,lags,windows)
    # Endpoint-only contamination after continuous-window clearance.
    q=np.ones((1000,4));q[100,1]=0.
    assert not quote_safe(q,604,lags,windows) # t-504=100
    assert quote_safe(q,605,lags,windows)
    # Future mutation cannot alter a historical source decision.
    q=np.ones((1000,4));a=quote_safe(q,650,lags,windows)
    q[651:]=np.nan
    assert quote_safe(q,650,lags,windows)==a
    for bad in (np.nan,np.inf,-1.):
        q=np.ones((1000,4));q[650,0]=bad
        try:quote_safe(q,650,lags,windows)
        except ValueError:pass
        else:raise AssertionError('INVALID_QUOTE_ACCEPTED')
    return True
if __name__=='__main__':
    assert static_check()
    print('V98_PROSPECTIVE_QUOTE_OUTAGE_STATIC_PASS')
