#!/usr/bin/env python3
"""KL pinned Clean-4 source-only event activation gate, BEFORE any PnL."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from kl_event_frozen_sources import bundle,static_check,WARMUP,BUDGET
from phase1260_aj_authenticated_source_digest import load_official,HOURS
OUT=Path(__file__).resolve().parent/"kl_source_viability.json"
def main():
    assert static_check()
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    intents,updates,entries,valid,regimes=bundle(o,h,l,c,r,e,q)
    assert HOURS==18288 and len(c)==HOURS and intents.shape==(HOURS,4,4)
    assert not updates[:WARMUP].any()
    violations=[]
    counts={}
    for year,lo,hi in (("2023",744,9504),("2024",9504,HOURS)):
        counts[year]={name:int(entries[lo:hi,j].sum())
            for j,name in enumerate(("Opportunity","Relative_Value","Stress_Recovery"))}
        for name,value in counts[year].items():
            if value<8:violations.append("KL_INSUFFICIENT_"+year+"_"+name)
    if np.any(entries[~valid]):violations.append("KL_INVALID_SOURCE_ENTRY")
    if np.any(np.abs(intents).sum(axis=(1,2))>1.+1e-10):
        violations.append("KL_GROSS")
    for k in range(4):
        changes=np.any(np.diff(intents[:,k,:],axis=0)!=0,axis=1)
        if np.any(changes & ~updates[1:,k]):
            violations.append("KL_UNANNOUNCED_ROW_CHANGE_"+str(k))
    if np.any(np.abs(intents[:,0]).sum(axis=1)>BUDGET[0]+1e-10):
        violations.append("KL_CORE_OVERBUDGET")
    # Independent timestamp check: never use a 2025+ observation.
    report={"architecture":"KL","source_only":True,"historical_training_only":True,
        "validation_2025_read":False,"future_holdout_read":False,
        "benchmark_internals_read":False,"system_pnl_computed":False,
        "trading_authorized":False,
        "source":"phase243_pinned_clean4_1h_signed_native_funding",
        "manifest_sha256":hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
        "hours":HOURS,"event_entries_by_year":counts,
        "row_update_count":updates.sum(axis=0).astype(int).tolist(),
        "invalid_quote_decision_hours":int((~valid[WARMUP:]).sum()),
        "violations":violations,
        "decision":"PASS_KL_SOURCE_ONLY" if not violations else "REJECT_KL_SOURCE_ONLY_NO_PNL"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("KL_SOURCE_GATE",json.dumps(report,sort_keys=True),flush=True)
    return report
if __name__=="__main__":
    result=main()
    raise SystemExit(0 if not result["violations"] else 2)
