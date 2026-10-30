#!/usr/bin/env python3
"""KD original publisher-authenticated trade-count source-only funded-epoch gate; no PnL."""
from __future__ import annotations
import json,hashlib
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from kd_native_trade_count_source import load_native
from kd_trade_fragmentation_sources import bundle,static_check,WARMUP,CLOCK
ROOT=Path(__file__).resolve().parent

def run():
    assert static_check()
    frames,manifest=load_official()
    count,source_sha=load_native()
    o,h,l,c,q,r,e,ml,mh=frames
    if count.shape!=(HOURS,4):raise ValueError("KD_NATIVE_COUNT_SHAPE")
    targets,updates,regimes,valid,budgets=bundle(o,h,l,c,r,e,q,count)
    names=("opportunity","relative_value","stress_recovery")
    years=("2023","2024")
    funded={y:{name:0 for name in names} for y in years}
    invalid={y:0 for y in years}
    states={y:{} for y in years}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t] or not np.isfinite(targets[t]).all():
            raise ValueError("KD_NONFINITE_DECISION")
        gross=np.abs(targets[t]).sum(axis=1)
        if not np.isclose(targets[t,0].sum(),1.,atol=1e-10) or np.any(targets[t,0]<-1e-12):
            raise ValueError("KD_CORE_CONSERVATION")
        if np.any(gross>1.+1e-10):
            raise ValueError("KD_GROSS")
        if not valid[t]:
            invalid[year]+=1
            if not np.allclose(targets[t],targets[t,0]):
                raise ValueError("KD_SOURCE_QUARANTINE_LEAK")
            continue
        states[year][regimes[t]]=states[year].get(regimes[t],0)+1
        for j,name in enumerate(names,2):
            funded[year][name]+=int(np.abs(targets[t,1]-targets[t,j]).sum()>.025)
    viable=all(funded[y][name]>=8 for y in years for name in names)
    result={"architecture":"KD","source_only":True,
            "historical_system_pnl_computed":False,"validation_2025_read":False,
            "holdout_accessed":False,"external_benchmarks_used":False,
            "trading_authorized":False,
            "source_manifest":manifest,
            "native_trade_count_sha256":source_sha,
            "financed_full_minus_sleeve_epochs":funded,
            "invalid_native_epochs":invalid,"regimes":states,
            "decision":"PASS_KD_SOURCE_ONLY_NOT_ECONOMIC" if viable else
                       "REJECT_KD_SOURCE_ONLY_INSUFFICIENT_FUNDED_EPOCHS"}
    (ROOT/"kd_source_viability.json").write_text(json.dumps(result,sort_keys=True,indent=2,default=str)+"\n")
    print("KD_SOURCE_ONLY",result["decision"],json.dumps(funded,sort_keys=True),
          "quarantine",json.dumps(invalid,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return result

if __name__=="__main__":run()
