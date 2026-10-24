#!/usr/bin/env python3
"""V98 Independent source-only staged exit capacity feasibility; NO strategy PnL.

Uses pinned Clean-4 Dec2022-Dec2024 authenticated data. Never accesses 2025.
Theoretical capacity upper bound is NOT a backtest or permission to increase
positions: future exit liquidity and 24h adverse continuation remain uncertain.
"""
from __future__ import annotations
import hashlib
import json
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from v98_staged_exit_capacity_governor import (
    PARTICIPATION,STRESSED_QUOTE_FRACTION,EXIT_FRICTION_MULTIPLIER,
    HOURS as EXIT_HOURS)

def run():
    frames,manifest=load_official()
    q=frames[4]
    first=2016
    prior_min=np.array([np.min(q[t-336:t],axis=0)
                        for t in range(first,HOURS)])
    one=PARTICIPATION*prior_min/EXIT_FRICTION_MULTIPLIER
    staged=(EXIT_HOURS*STRESSED_QUOTE_FRACTION*
            PARTICIPATION*prior_min/EXIT_FRICTION_MULTIPLIER)
    assert np.isfinite(one).all() and np.isfinite(staged).all()
    assert np.all(one>=0) and np.all(staged>=0)
    assert np.allclose(staged,one*EXIT_HOURS*STRESSED_QUOTE_FRACTION)
    years={}
    for year,start,end in (("2023",first,9504),("2024",9504,HOURS)):
        lo=start-first;hi=end-first
        x=one[lo:hi].sum(axis=1)
        y=staged[lo:hi].sum(axis=1)
        years[year]={
            "observed_hours":len(x),
            "one_hour_total_notional_quantiles_usd":{
                str(p):round(float(np.quantile(x,p)),2)
                for p in (0.,.01,.1,.5,.9,1.)},
            "staged_24h_total_notional_quantiles_usd":{
                str(p):round(float(np.quantile(y,p)),2)
                for p in (0.,.01,.1,.5,.9,1.)},
            "staged_fraction_of_capital_median":{
                str(int(cap)):round(float(np.median(y/cap)),6)
                for cap in (1e4,1e6,1e7)},
            "hours_staged_notional_ge_10m":int(np.count_nonzero(y>=1e7)),
            "hours_staged_notional_ge_1m":int(np.count_nonzero(y>=1e6)),
        }
    payload={
        "kind":"V98_INDEPENDENT_STAGED_EXIT_SOURCE_ONLY",
        "no_pnl":True,"training_only":True,"validation_2025_read":False,
        "exit_hours":EXIT_HOURS,
        "volume_haircut":STRESSED_QUOTE_FRACTION,
        "participation":PARTICIPATION,
        "manifest_sha256":hashlib.sha256(json.dumps(
            manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        "years":years,
        "decision":"SOURCE_CAPACITY_DIAGNOSTIC_ONLY_NOT_RISK_OR_ECONOMIC_APPROVAL"}
    return payload

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    x=run()
    with open(args.output,"w") as f:
        json.dump(x,f,indent=2,sort_keys=True,allow_nan=False)
    print("V98_STAGED_EXIT_SOURCE_CAPACITY",json.dumps(x,sort_keys=True))
