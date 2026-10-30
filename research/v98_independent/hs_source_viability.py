#!/usr/bin/env python3
"""HS signed funding-carry source-only viability, before any system PnL."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from hs_signed_carry_sources import bundle,static_check,WARMUP,CLOCK

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"hs_source_viability.json"


def run():
    if not static_check():raise ValueError("HS_STATIC_CAUSALITY")
    frames,manifest=load_official()
    signals,updates,regimes,budgets,validity=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    counts={"2023":{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0},
            "2024":{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0}}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t].all() or not validity[t].all():
            raise ValueError("HS_NATIVE_EPOCH_INVALID")
        for i,name in enumerate(("core","opportunity","relative_value","stress_recovery")):
            if not np.isclose(np.abs(signals[t,i]).sum(),1.,atol=1e-12):
                raise ValueError("HS_SIGNED_SLEEVE_UNFINANCED")
            counts[year][name]+=1
    for year in ("2023","2024"):
        if min(counts[year].values())<8:
            raise ValueError("HS_INSUFFICIENT_FINANCED_EPOCHS_"+year)
    report={"decision":"PASS_HS_SIGNED_SEVEN_SLOT_SOURCE_ONLY_NOT_ECONOMIC",
            "training_years":[2023,2024],"assets":["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
            "warmup_hours":WARMUP,"financed_epoch_counts":counts,
            "holdout_2025_read":False,"historical_system_pnl_computed":False,
            "external_benchmarks_used":False,"trading_authorized":False}
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("HS_SIGNED_SOURCE_ONLY_PASS",json.dumps(counts,sort_keys=True),flush=True)
    return report


if __name__=="__main__":
    run()
