#!/usr/bin/env python3
"""IX liquidity-participation source-only, pre-PnL viability: authenticated Clean-4, causal liquidity and funded epochs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from ix_liquidity_rotation_sources import bundle,static_check,WARMUP,CLOCK

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"ix_source_viability.json"

def run():
    if not static_check():
        raise ValueError("IX_STATIC_CAUSALITY")
    frames,manifest=load_official()
    signals,updates,regimes,budgets,validity=bundle(
        frames[0],frames[1],frames[2],frames[3],
        frames[5],frames[6],frames[4])
    counts={y:{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0}
            for y in ("2023","2024")}
    inactive={y:0 for y in ("2023","2024")}
    regimes_by_year={y:{} for y in ("2023","2024")}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t].all() or not validity[t,0]:
            raise ValueError("IX_NATIXE_EPOCH_INVALID")
        if not np.isclose(budgets[t].sum(),1.,atol=1e-12):
            raise ValueError("IX_BUDGET_NONCONSERVATION")
        regimes_by_year[year][regimes[t]]=regimes_by_year[year].get(regimes[t],0)+1
        if not validity[t,1:].all():inactive[year]+=1
        for i,name in enumerate(("core","opportunity","relative_value","stress_recovery")):
            gross=float(np.abs(signals[t,i]).sum())
            if not (np.isclose(gross,1.,atol=1e-12) or
                    (i>0 and np.isclose(gross,0.,atol=1e-12))):
                raise ValueError("IX_SIGNED_SLEEVE_NONCONSERVATION")
            if gross>1e-12 and not validity[t,i]:
                raise ValueError("IX_INVALID_QUOTE_SLEEVE_ACTIXATED")
            counts[year][name]+=int(budgets[t,i]>1e-12 and gross>1e-12)
    viable=all(min(counts[y].values())>=8 for y in ("2023","2024"))
    report={"architecture":"IX",
        "decision":"PASS_IX_SOURCE_ONLY_NOT_ECONOMIC" if viable else
                   "REJECT_IX_SOURCE_ONLY_INSUFFICIENT_FINANCED_EPOCHS",
        "training_years":[2023,2024],
        "assets":["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
        "warmup_hours":WARMUP,"financed_epoch_counts":counts,
        "inactive_optional_epochs":inactive,"regimes_by_year":regimes_by_year,
        "holdout_2025_read":False,"historical_system_pnl_computed":False,
        "external_benchmarks_used":False,"trading_authorized":False}
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("IX_SOURCE_ONLY",report["decision"],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return report

if __name__=="__main__":
    run()
