#!/usr/bin/env python3
"""AD preregistered funding-event crowding dislocation sleeve, source-only.

Signals at completed settlement t can first fill at t+1 open; no PnL.
"""
from __future__ import annotations
from collections import deque
import numpy as np
from phase1189_ad_online_core_router import ASSETS, validate_source

HISTORY_EVENTS=90
WARMUP=720
Z_THRESHOLD=2.0
DIVERGENCE_THRESHOLD=.015
STD_FLOOR=.00005
HOLD_HOURS=16
COOLDOWN_HOURS=48


def opportunity_intents(op, hi, lo, cl, quote, funding, event, diagnostics=False):
    idx, (_, _, _, close, _, rate, mask)=validate_source(
        op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    if n<=WARMUP:
        raise ValueError('AD1191_WARMUP')
    logp=np.log(close)
    divergence=np.zeros((n,4),dtype=float)
    ret24=logp[24:]-logp[:-24]
    divergence[24:]=ret24-ret24.mean(axis=1,keepdims=True)
    history=[deque(maxlen=HISTORY_EVENTS) for _ in ASSETS]
    intent=np.zeros((n,4),dtype=np.int8)
    expiry=np.zeros(4,dtype=np.int64)
    next_allowed=np.zeros(4,dtype=np.int64)
    direction=np.zeros(4,dtype=np.int8)
    triggers=0
    eligible_events=0
    for t in range(n):
        for j in range(4):
            if mask[t,j]:
                if t>=WARMUP and len(history[j])==HISTORY_EVENTS:
                    baseline=np.asarray(history[j],dtype=float)
                    std=max(float(np.std(baseline,ddof=0)),STD_FLOOR)
                    z=(rate[t,j]-float(np.mean(baseline)))/std
                    div=divergence[t,j]
                    if abs(z)>=Z_THRESHOLD and abs(div)>=DIVERGENCE_THRESHOLD and z*div>0:
                        eligible_events+=1
                        if t>=next_allowed[j]:
                            direction[j]=np.int8(-np.sign(z))
                            expiry[j]=t+HOLD_HOURS
                            next_allowed[j]=t+COOLDOWN_HOURS
                            triggers+=1
                history[j].append(float(rate[t,j]))
            intent[t,j]=direction[j] if t<expiry[j] else 0
    if diagnostics:
        return intent,{'phase':1191,'source_only':True,
            'historical_system_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'earliest_fill':'t+1 open',
            'funding_events':int(mask.sum()),'eligible_events':eligible_events,
            'triggers':triggers,'active_asset_hours':int(np.count_nonzero(intent)),
            'last_event_history_sizes':[len(x) for x in history]}
    return intent
