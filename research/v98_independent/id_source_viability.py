#!/usr/bin/env python3
"""ID immutable source-only pre-PnL viability: inventory absorption and funding carry, causal future mutation, financed epochs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from id_deleveraging_sources import bundle,static_check,WARMUP,CLOCK,load_oi

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"id_source_viability.json"
def run():
    if not static_check():raise ValueError("ID_STATIC_CAUSALITY")
    frames,manifest=load_official()
    oi,oi_sha=load_oi()
    signals,updates,regimes,budgets,validity=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4],oi)
    counts={"2023":{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0},
            "2024":{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0}}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t].all() or not validity[t,0]:
            raise ValueError("ID_NATIVE_EPOCH_INVALID")
        if not np.isclose(budgets[t].sum(),1.,atol=1e-12):
            raise ValueError("ID_BUDGET_NONCONSERVATION")
        for i,name in enumerate(("core","opportunity","relative_value","stress_recovery")):
            gross=float(np.abs(signals[t,i]).sum())
            if not (np.isclose(gross,1.,atol=1e-12) or (i>0 and np.isclose(gross,0.,atol=1e-12))):
                raise ValueError("ID_SIGNED_SLEEVE_NONCONSERVATION")
            if gross>1e-12 and not validity[t,i]:
                raise ValueError('ID_OI_INVALID_SLEEVE_ACTIVATED')
            counts[year][name]+=int(budgets[t,i]>1e-12 and gross>1e-12)
    viable=all(min(counts[y].values())>=8 for y in ("2023","2024"))
    report={"decision":"PASS_ID_SOURCE_ONLY_NOT_ECONOMIC" if viable else "REJECT_ID_SOURCE_ONLY_INSUFFICIENT_FINANCED_EPOCHS",
            "training_years":[2023,2024],"assets":["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
            "warmup_hours":WARMUP,"oi_hourly_csv_sha256":oi_sha,"financed_epoch_counts":counts,
            "holdout_2025_read":False,"historical_system_pnl_computed":False,
            "external_benchmarks_used":False,"trading_authorized":False}
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("ID_SOURCE_ONLY",report["decision"],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return report
if __name__=="__main__":
    run()
