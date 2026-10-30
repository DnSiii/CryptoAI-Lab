#!/usr/bin/env python3
"""KA authenticated OI-v2 / Clean-4 source and material financed epoch gate; no PnL."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from ic_oi_crowding_sources import load_oi
from ka_deleveraging_convexity_sources import bundle,static_check,WARMUP,CLOCK
ROOT=Path(__file__).resolve().parent

def run():
    assert static_check()
    frames,manifest=load_official()
    oi,oi_sha=load_oi()
    o,h,l,c,q,r,e,ml,mh=frames
    targets,updates,regimes,valid,budgets=bundle(o,h,l,c,r,e,q,oi)
    if len(targets)!=HOURS:raise ValueError("KA_TRAINING_HOURS")
    names=("opportunity","relative_value","stress_recovery")
    counts={y:{name:0 for name in names} for y in ("2023","2024")}
    invalid={y:0 for y in counts}
    states={y:{} for y in counts}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t] or not np.isfinite(targets[t]).all():
            raise ValueError("KA_NONFINITE_EPOCH")
        gross=np.abs(targets[t]).sum(axis=1)
        if np.any(targets[t,0]<-1e-12) or not np.isclose(targets[t,0].sum(),1.,atol=1e-10):
            raise ValueError("KA_CORE_COLLATERAL_CONSERVATION")
        if np.any(gross>1.+1e-10):
            raise ValueError("KA_GROSS_NONCONSERVATION")
        if not valid[t]:
            invalid[year]+=1
            if not np.allclose(targets[t],targets[t,0]):
                raise ValueError("KA_QUARANTINED_OPTIONAL_LEAK")
            continue
        states[year][regimes[t]]=states[year].get(regimes[t],0)+1
        for j,name in enumerate(names,2):
            counts[year][name]+=int(np.abs(targets[t,1]-targets[t,j]).sum()>.025)
    viable=all(counts[y][name]>=8 for y in counts for name in names)
    result={"architecture":"KA","source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"source_manifest":manifest,
            "oi_hourly_sha256":oi_sha,"oi_lag_completed_hours":1,
            "financed_forecast_perturbation_epochs":counts,
            "invalid_oi_epochs":invalid,"regimes":states,
            "decision":"PASS_KA_SOURCE_ONLY_NOT_ECONOMIC" if viable else
                       "REJECT_KA_SOURCE_ONLY_INSUFFICIENT_FUNDED_EPOCHS"}
    (ROOT/"ka_source_viability.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,default=str)+"\n")
    print("KA_SOURCE_ONLY",result["decision"],json.dumps(counts,sort_keys=True),
          "quarantine",json.dumps(invalid,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return result

if __name__=="__main__":run()
