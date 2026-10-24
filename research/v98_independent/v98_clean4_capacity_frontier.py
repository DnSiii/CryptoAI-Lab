#!/usr/bin/env python3
"""V98 Clean4 source-only conservative deployable-capital frontier.
No strategy signals, system PnL, holdout, or benchmark imports.
"""
from __future__ import annotations
import argparse,hashlib,json
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
from v98_staged_exit_viability_governor_v2 import (
    prior_min_exit_window_quote,PARTICIPATION,STRESSED_QUOTE_FRACTION,
    EXIT_FRICTION_MULTIPLIER)
from ba_ratio_reversion_governor import ENTRY_FRACTION

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
SLICES={"2023":slice(744,9504),"2024":slice(9504,18288)}
def percentiles(x):
    return {k:float(np.quantile(x,q)) for k,q in (
        ("p05",.05),("median",.5),("p95",.95))}
def run():
    frames,manifest=load_official()
    q=frames[4]
    if q.shape!=(18288,4):raise ValueError("V98_CAPACITY_CALENDAR")
    min24=np.full_like(q,np.nan)
    for j in range(4):
        # Previous 336 completed hours contain 313 contiguous 24h windows.
        rolling24=pd.Series(q[:,j]).rolling(24,min_periods=24).sum()
        min24[:,j]=rolling24.shift(1).rolling(313,min_periods=313).min().to_numpy()
    for t in (336,2016,9504,18287):
        if not np.allclose(min24[t],prior_min_exit_window_quote(q,t),rtol=0,atol=1e-5):
            raise ValueError("V98_CAPACITY_SOURCE_WINDOW_RECONCILIATION_T"+str(t))
    authorized=ENTRY_FRACTION*PARTICIPATION*STRESSED_QUOTE_FRACTION*min24/EXIT_FRICTION_MULTIPLIER
    annual={}
    for year,sl in SLICES.items():
        a=authorized[sl]
        annual[year]={
            "per_asset_max_authorized_notional_usd":{
                asset:percentiles(a[:,j]) for j,asset in enumerate(ASSETS)},
            "joint_four_asset_max_authorized_gross_notional_usd":
                percentiles(np.sum(a,axis=1)),
            "joint_gross_capacity_fraction_of_10m":
                percentiles(np.sum(a,axis=1)/1e7),
            "ringfenced_BX_per_book_cap_usd":{
                asset:percentiles(a[:,j]/4) for j,asset in enumerate(ASSETS)},
        }
    return {
        "decision":"PASS_V98_TRAINING_ONLY_SOURCE_CAPACITY_FRONTIER_NOT_PNL",
        "historical_training_only":True,
        "validation_2025_read":False,"external_benchmarks_used":False,
        "assets":ASSETS,"years":annual,
        "entry_fraction":ENTRY_FRACTION,"participation":PARTICIPATION,
        "stressed_quote_fraction":STRESSED_QUOTE_FRACTION,
        "exit_friction_multiplier":EXIT_FRICTION_MULTIPLIER,
        "source_manifest_sha256":hashlib.sha256(
            json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "physical_capacity_is_not_expected_fill_or_trading_authorization":True,
    }
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();result=run()
    with open(a.output,"w") as f:
        json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    print(result["decision"])
    for year,v in result["years"].items():
        print(year,"joint_median_gross_cap_USD",
              round(v["joint_four_asset_max_authorized_gross_notional_usd"]["median"]),
              "fraction_10m",
              round(v["joint_gross_capacity_fraction_of_10m"]["median"],4))
