#!/usr/bin/env python3
"""LA authenticated source-only viability and independent prefix future-mutation audit.
Never compute historical system PnL before source gate; never access 2025+.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
from la_convex_breakout_residual_sources import bundle, static_check, WARMUP, BUDGET
from phase1260_aj_authenticated_source_digest import load_official, HOURS

OUT=Path(__file__).resolve().parent/"la_source_viability.json"

def main():
    assert static_check()
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    intents,updates,entries,valid,regimes=bundle(o,h,l,c,r,e,q)
    violations=[]
    if HOURS!=18288 or len(c)!=HOURS or intents.shape!=(HOURS,4,4):
        violations.append("LA_AUTHENTICATED_LENGTH")
    if updates[:WARMUP].any():violations.append("LA_WARMUP_LEAK")
    counts={}
    for year,lo,hi in (("2023",744,9504),("2024",9504,HOURS)):
        counts[year]={name:int(entries[lo:hi,j].sum())
            for j,name in enumerate(("Opportunity","Relative_Value","Stress_Recovery"))}
        for name,value in counts[year].items():
            if value<8:violations.append("LA_INSUFFICIENT_"+year+"_"+name)
    if np.any(entries[~valid]):violations.append("LA_INVALID_SOURCE_ENTRY")
    if np.any(np.abs(intents).sum(axis=(1,2))>.92+1e-10):
        violations.append("LA_GROSS")
    for k in range(4):
        changes=np.any(np.diff(intents[:,k,:],axis=0)!=0,axis=1)
        if np.any(changes & ~updates[1:,k]):
            violations.append("LA_UNANNOUNCED_ROW_CHANGE_"+str(k))
        if np.any(np.abs(intents[:,k]).sum(axis=1)>BUDGET[k]+1e-10):
            violations.append("LA_COMPONENT_OVERBUDGET_"+str(k))
    prefix=14000
    mutated=[x.copy() for x in (o,h,l,c,q,r,e)]
    for j in (0,1,2,3):
        mutated[j][prefix:]*=1.45
    mutated[4][prefix:]*=3.
    mutated[5][prefix:]*=-1.
    alternative=bundle(mutated[0],mutated[1],mutated[2],mutated[3],
                       mutated[5],mutated[6],mutated[4])
    future_ok=all(np.array_equal(intents_oracle[:prefix],future_oracle[:prefix])
                  for intents_oracle,future_oracle in zip((intents,updates,entries,valid,regimes),alternative))
    if not future_ok:violations.append("LA_REAL_FUTURE_MUTATION_LEAK")
    report={
        "architecture":"LA","source_only":True,"historical_training_only":True,
        "validation_2025_read":False,"future_holdout_read":False,
        "benchmark_internals_read":False,"system_pnl_computed":False,
        "trading_authorized":False,
        "source":"phase243_pinned_clean4_1h_signed_native_funding",
        "manifest_sha256":hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
        "hours":HOURS,"event_entries_by_year":counts,
        "row_update_count":updates.sum(axis=0).astype(int).tolist(),
        "invalid_quote_decision_hours":int((~valid[WARMUP:]).sum()),
        "real_future_mutation_prefix_hours":prefix,"real_future_mutation_pass":future_ok,
        "max_intended_gross":float(np.abs(intents).sum(axis=(1,2)).max()),
        "violations":violations,
        "decision":"PASS_LA_SOURCE_ONLY" if not violations else "REJECT_LA_SOURCE_ONLY_NO_PNL"
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("LA_SOURCE_GATE",json.dumps(report,sort_keys=True),flush=True)
    return report

if __name__=="__main__":
    result=main()
    raise SystemExit(0 if not result["violations"] else 2)
