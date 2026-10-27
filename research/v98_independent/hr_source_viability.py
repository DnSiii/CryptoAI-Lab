#!/usr/bin/env python3
"""HR source-only viability before economic PnL, frozen seven-slot hypothesis."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from hq_spot_masked_feature_gate import load_verified,ASSETS
from hr_spot_participation_sources import bundle,static_check,WARMUP,CLOCK

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"hr_source_viability.json"


def run():
    if not static_check():
        raise ValueError("HR_STATIC_CAUSALITY_FAIL")
    frames,native_receipt=load_official()
    spot_root=ROOT/"hq_gap_aware_spot_source_only"
    spot=load_verified(spot_root/"hq_spot_calendar_masked.csv",
                       spot_root/"hq_masked_source_receipt.json")
    if spot["hours_per_asset"]!=HOURS:
        raise ValueError("HR_SPOT_FUTURES_CLOCK_MISMATCH")
    sq=np.column_stack([np.asarray(spot["assets"][a]["quote_volume"],dtype=float)
                        for a in ASSETS])
    mask=np.column_stack([np.asarray(spot["assets"][a]["eligible"],dtype=bool)
                          for a in ASSETS])
    signals,updates,regimes,budgets,validity=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4],sq,mask)
    counts={"2023":{"core":0,"opportunity":0,"relative_value":0,"stress_financed":0,"stress_cash":0},
            "2024":{"core":0,"opportunity":0,"relative_value":0,"stress_financed":0,"stress_cash":0}}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t].all():
            raise ValueError("HR_EPOCH_UPDATE_MISSING")
        if not validity[t].any() and (signals[t,1].any() or signals[t,3].any()):
            raise ValueError("HR_INELIGIBLE_SPOT_ALPHA_LEAK")
        c=counts[year]
        c["core"]+=int(signals[t,0].any())
        c["opportunity"]+=int(signals[t,1].any())
        c["relative_value"]+=int(signals[t,2].any())
        c["stress_financed"]+=1
        c["stress_cash"]+=int(not signals[t,3].any())
    for year in ("2023","2024"):
        for sleeve in ("core","opportunity","relative_value","stress_financed"):
            if counts[year][sleeve]<8:
                raise ValueError("HR_INSUFFICIENT_FINANCED_EPOCHS_"+year+"_"+sleeve)
    report={
        "decision":"PASS_HR_SEVEN_SLOT_SOURCE_ONLY_NOT_ECONOMIC",
        "training_years":[2023,2024],"warmup_hours":WARMUP,
        "assets":list(ASSETS),"spot_canonical_sha256":spot["source_sha256"],
        "spot_eligible_asset_hours":spot["eligible_asset_hours"],
        "spot_partial_asset_hours":spot["partial_asset_hours"],
        "spot_missing_asset_hours":spot["missing_asset_hours"],
        "financed_epoch_counts":counts,
        "holdout_2025_read":False,"historical_system_pnl_computed":False,
        "external_benchmarks_used":False,"trading_authorized":False,
    }
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("HR_SEVEN_SLOT_SOURCE_ONLY_PASS",json.dumps(counts,sort_keys=True),flush=True)
    return report


if __name__=="__main__":
    run()
