#!/usr/bin/env python3
"""HW source-only gate before economic PnL; immutable preregistered hypothesis."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from hw_spot_perp_basis_sources import bundle,static_check,WARMUP,CLOCK
from hw_spot_perp_basis_loader import load_spot

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"hw_source_viability.json"

def run():
    if not static_check():raise ValueError("HW_STATIC_CAUSALITY")
    frames,manifest=load_official()
    signals,updates,regimes,budgets,validity=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4],*load_spot())
    cash_counts={"2023":{"opportunity":0,"relative_value":0,"stress_recovery":0},"2024":{"opportunity":0,"relative_value":0,"stress_recovery":0}}
    counts={"2023":{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0},
            "2024":{"core":0,"opportunity":0,"relative_value":0,"stress_recovery":0}}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t].all() or not validity[t].all():
            raise ValueError("HW_NATIVE_EPOCH_INVALID")
        if not np.isclose(budgets[t].sum(),1.,atol=1e-12):
            raise ValueError("HW_BUDGET_NONCONSERVATION")
        for i,name in enumerate(("core","opportunity","relative_value","stress_recovery")):
            gross=float(np.abs(signals[t,i]).sum())
            if not (np.isclose(gross,1.,atol=1e-12) or np.isclose(gross,0.,atol=1e-12)):
                raise ValueError("HW_SIGNED_SLEEVE_UNFINANCED")
            counts[year][name]+=int(budgets[t,i]>1e-12 and (gross>0. or (i==3 and regimes[t]=="STRESS")))
            if i>0: cash_counts[year][name]+=int(gross==0. and budgets[t,i]>1e-12)
    viable=all(min(counts[y].values())>=8 for y in ("2023","2024"))
    report={"decision":"PASS_HW_SOURCE_ONLY_NOT_ECONOMIC" if viable else "REJECT_HW_SOURCE_ONLY_INSUFFICIENT_FINANCED_EPOCHS",
            "training_years":[2023,2024],"assets":["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"],
            "warmup_hours":WARMUP,"financed_epoch_counts":counts,"funded_cash_epoch_counts":cash_counts,
            "holdout_2025_read":False,"historical_system_pnl_computed":False,
            "external_benchmarks_used":False,"trading_authorized":False}
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("HW_SOURCE_ONLY",report["decision"],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return report

if __name__=="__main__":
    run()
