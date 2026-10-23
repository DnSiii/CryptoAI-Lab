#!/usr/bin/env python3
"""AD actual-NAV-conditioned stress insurance demands; no assumed fills."""
from __future__ import annotations
import numpy as np
from phase1189_ad_online_core_router import validate_source

WARMUP=336
ACTIVATE_DD=-.12
ESCALATE_DD=-.20
RECOVERY_DD=-.06
ACTIVATE_ACCEL=-.04
RECOVERY_ACCEL=.01
MIN_DWELL=24
LOW_HEDGE=.15
HIGH_HEDGE=.30


def stress_targets(op,hi,lo,cl,quote,funding,event,realized_nav,diagnostics=False):
    idx,(_,_,_,close,_,_,_)=validate_source(op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    nav=np.asarray(realized_nav,dtype=float)
    if nav.shape!=(n,) or not np.isfinite(nav).all() or np.any(nav<=0):
        raise ValueError('AD1193_ACTUAL_NAV_INVALID')
    market=np.log(close).mean(axis=1)
    accel=np.zeros(n)
    accel[24:]=(market[24:]-market[12:-12])-(market[12:-12]-market[:-24])
    peak=np.maximum.accumulate(nav)
    drawdown=nav/peak-1
    targets=np.zeros((n,4),dtype=float)
    active=False
    size=0.
    activation=-1
    activations=escalations=recoveries=0
    for t in range(WARMUP,n):
        if not active and drawdown[t]<=ACTIVATE_DD and accel[t]<=ACTIVATE_ACCEL:
            active=True
            activation=t
            size=HIGH_HEDGE if drawdown[t]<=ESCALATE_DD else LOW_HEDGE
            activations+=1
        elif active:
            if drawdown[t]<=ESCALATE_DD and size< HIGH_HEDGE:
                size=HIGH_HEDGE
                escalations+=1
            if (t-activation>=MIN_DWELL and drawdown[t]>=RECOVERY_DD
                    and accel[t]>=RECOVERY_ACCEL):
                active=False
                size=0.
                recoveries+=1
        if active:
            targets[t]=-size/4.
    if diagnostics:
        return targets,{'phase':1193,'source_only':True,
            'historical_system_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'earliest_fill':'t+1 open',
            'activations':activations,'escalations':escalations,'recoveries':recoveries,
            'active_hours':int(np.any(targets!=0,axis=1).sum()),
            'max_short_gross_demand':float(np.abs(targets).sum(axis=1).max()),
            'actual_exit_execution_proven':False}
    return targets
