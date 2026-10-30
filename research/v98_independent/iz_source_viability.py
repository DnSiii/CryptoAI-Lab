#!/usr/bin/env python3
"""IZ source-only pre-PnL gates: authenticated Clean-4, causal online-shadow, financed epochs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from iz_online_shadow_growth_sources import bundle,static_check,WARMUP,CLOCK
OUT=Path(__file__).with_name("iz_source_viability.json")

def run():
    assert static_check()
    frames,manifest=load_official()
    signals,updates,regimes,budgets,validity,edges=bundle(
        frames[0],frames[1],frames[2],frames[3],
        frames[5],frames[6],frames[4])
    if len(signals)!=HOURS:raise ValueError("IZ_WRONG_TRAINING_HOURS")
    counts={year:{s:0 for s in ("core","opportunity","relative_value","stress_recovery")}
            for year in ("2023","2024")}
    regime_counts={year:{} for year in counts}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t].all() or not np.isclose(budgets[t].sum(),1.):
            raise ValueError("IZ_EPOCH_INVALID")
        regime_counts[year][regimes[t]]=regime_counts[year].get(regimes[t],0)+1
        for i,name in enumerate(counts[year]):
            gross=float(np.abs(signals[t,i]).sum())
            if not (np.isclose(gross,1.) or (i>0 and np.isclose(gross,0.))):
                raise ValueError("IZ_SLEEVE_GROSS_INVALID")
            if budgets[t,i]>1e-12 and (gross<1e-12 or not validity[t,i]):
                raise ValueError("IZ_FINANCED_INVALID_SLEEVE")
            counts[year][name]+=int(budgets[t,i]>1e-12 and gross>1e-12)
    viable=all(counts[y][name]>=8 for y in counts
               for name in ("opportunity","relative_value","stress_recovery"))
    result={"architecture":"IZ","training_years":[2023,2024],
            "assets":["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
            "financed_epochs":counts,"regimes":regime_counts,
            "decision":"PASS_IZ_SOURCE_ONLY_NOT_ECONOMIC" if viable else
                       "REJECT_IZ_SOURCE_ONLY_INSUFFICIENT_FINANCED_EPOCHS",
            "validation_2025_read":False,"historical_system_pnl_computed":False,
            "external_benchmarks_used":False,"trading_authorized":False}
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("IZ_SOURCE_ONLY",result["decision"],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return result

if __name__=="__main__":
    run()
