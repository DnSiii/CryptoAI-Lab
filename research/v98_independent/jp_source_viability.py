#!/usr/bin/env python3
"""JP source-only causal and funded-epoch activation gate, NO system PnL."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from jp_delayed_shadow_sources import bundle,static_check,WARMUP,CLOCK
ROOT=Path(__file__).resolve().parent

def run():
    assert static_check()
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    targets,updates,regimes,valid,forecasts=bundle(o,h,l,c,r,e,q)
    names=("opportunity","relative_value","stress_recovery")
    counts={y:{name:0 for name in names} for y in ("2023","2024")}
    invalid={y:0 for y in counts}
    states={y:{} for y in counts}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t] or not np.isfinite(targets[t]).all():
            raise ValueError("JP_NONFINITE_EPOCH")
        gross=np.abs(targets[t]).sum(axis=1)
        if np.any(gross>1.+1e-10):
            raise ValueError("JP_GROSS_NONCONSERVATION")
        if not valid[t]:
            invalid[year]+=1
            if not np.allclose(targets[t],targets[t,0]):
                raise ValueError("JP_INVALID_QUOTE_TARGET")
            continue
        states[year][regimes[t]]=states[year].get(regimes[t],0)+1
        for j,name in enumerate(names,2):
            counts[year][name]+=int(np.abs(targets[t,1]-targets[t,j]).sum()>.025)
    viable=all(counts[y][name]>=8 for y in counts for name in names)
    result={"architecture":"JP","source_only":True,
            "historical_system_pnl_computed":False,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"source_manifest":manifest,
            "financed_forecast_perturbation_epochs":counts,
            "invalid_epochs":invalid,"regimes":states,
            "decision":"PASS_JP_SOURCE_ONLY_NOT_ECONOMIC" if viable else
                       "REJECT_JP_SOURCE_ONLY_INSUFFICIENT_FUNDED_EPOCHS"}
    (ROOT/"jp_source_viability.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,default=str)+"\n")
    print("JP_SOURCE_ONLY",result["decision"],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return result
if __name__=="__main__":run()
