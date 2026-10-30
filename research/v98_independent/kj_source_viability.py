#!/usr/bin/env python3
"""KJ source-only pre-economic activation, time, and collateral gate; no PnL."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from kj_persistent_inventory_sources import bundle,static_check,WARMUP,CLOCK,PATHS
from phase1260_aj_authenticated_source_digest import load_official,HOURS

OUT=Path(__file__).resolve().parent/"kj_source_viability.json"
def main():
    assert static_check()
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    targets,updates,regimes,valid,budgets=bundle(o,h,l,c,r,e,q)
    assert len(c)==HOURS and HOURS==18288
    assert targets.shape==(HOURS,5,4)
    assert not updates[:WARMUP].any()
    counts={};invalid=[];violations=[]
    # Anchor all decisions at the immutable Dec-2022 warmup, NOT each
    # calendar-year boundary (2023 has 365 days, not a whole 168h multiple).
    all_epochs=np.arange(WARMUP,HOURS,CLOCK)
    for year,lo,hi in (("2023",744,9504),("2024",9504,HOURS)):
        epochs=all_epochs[(all_epochs>=lo)&(all_epochs<hi)]
        counts[year]={}
        for i,name in enumerate(("Opportunity","Relative_Value","Stress_Recovery")):
            distances=np.abs(targets[epochs,1]-targets[epochs,i+2]).sum(axis=1)
            counts[year][name]=int(np.sum(distances>.025))
            if counts[year][name]<8:
                violations.append("KJ_INSUFFICIENT_"+year+"_"+name)
        invalid.extend(int(t) for t in epochs if not valid[t])
    epochs=all_epochs
    if np.any(np.abs(targets[epochs]).sum(axis=2)>1.+1e-10):
        violations.append("KJ_GROSS_NONCONSERVATION")
    if np.any((np.abs(targets[epochs,1]-targets[epochs,0]).sum(axis=1)>1e-10) & (~valid[epochs])):
        violations.append("KJ_SOURCE_INVALID_LEAK")
    zero_quote_hours_by_year={"2023":int(np.sum(np.any(q[744:9504]<=0,axis=1))),
                              "2024":int(np.sum(np.any(q[9504:]<=0,axis=1)))}
    invalid_epoch_by_year={"2023":sum(744<=t<9504 for t in invalid),
                           "2024":sum(9504<=t<HOURS for t in invalid)}
    report={"architecture":"KJ","historical_training_only":True,
        "validation_2025_read":False,"benchmark_internals_read":False,
        "economic_pnl_computed":False,"live_trading_authorized":False,
        "source":"canonical_phase243_clean4_pinned_1h_native_funding",
        "epochs":int(updates.sum()),"invalid_optional_epochs":invalid,
        "zero_quote_hours_by_year":zero_quote_hours_by_year,
        "invalid_epoch_by_year":invalid_epoch_by_year,
        "material_funded_epochs_by_year":counts,
        "violations":violations,
        "decision":"PASS_KJ_SOURCE_ONLY_NEEDS_ECONOMIC_GATE" if not violations
                    else "REJECT_KJ_SOURCE_ONLY_NO_PNL"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("KJ_SOURCE",report["decision"],"epochs",report["epochs"],
          "counts",counts,"invalid",len(invalid),
          "invalid_by_year",invalid_epoch_by_year,
          "zero_quote_hours_by_year",zero_quote_hours_by_year,
          "first_invalid",invalid[:10],"violations",violations,flush=True)
    return report
if __name__=="__main__":
    result=main()
    raise SystemExit(0 if not result["violations"] else 2)
