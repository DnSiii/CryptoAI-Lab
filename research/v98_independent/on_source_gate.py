#!/usr/bin/env python3
"""ON source-only independent clock and persistent-state transition gate before PnL."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from on_sources import bundle,load_oi,synthetic_causality,NAMES
def check(d,oi,oi_receipt):
    synthetic_causality()
    raw,updates,active,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    times=np.arange(WARMUP,HOURS,168)
    failures=[]
    if not np.array_equal(np.flatnonzero(updates[:,1]),times) or not np.all(updates[times,1:]):failures.append("ON_OPTIONAL_CLOCK")
    coretimes=np.flatnonzero(updates[:,0])
    if not np.all(np.isin(coretimes,times)) or not (0<len(coretimes)<=105):failures.append("ON_CORE_TRANSITION_CLOCK")
    if int(d["event"].sum())!=9144:failures.append("ON_FUNDING_EVENTS")
    if np.any(np.abs(raw[:,0]).sum(axis=1)>.84+1e-10):failures.append("ON_CORE_BUDGET")
    if np.any((np.abs(np.diff(raw,axis=0)).sum(axis=(1,2))>1e-12)&~np.any(updates[1:],axis=1)):failures.append("ON_SILENT_CHANGE")
    if not np.isfinite(raw).all():failures.append("ON_NONFINITE")
    if np.any(np.abs(raw[times[~eligible[times]],1]).sum(axis=1)>1e-12):failures.append("ON_OI_QUARANTINE_LEAK")
    if int(eligible[times].sum())!=95:failures.append("ON_OI_MASK_NOT_FROZEN_95")
    prev=np.zeros(4)
    for t in times:
        changed=not np.array_equal(raw[t,0],prev)
        if changed!=bool(updates[t,0]):failures.append("ON_CORE_UNDECLARED_CHANGE_"+str(t))
        prev=raw[t,0].copy()
    counts={str(year):{name:int(active[times[(times>=lo)&(times<hi)],i].sum()) for i,name in enumerate(NAMES)}
            for year,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    return {"decision":"REJECT_SOURCE_ONLY" if failures else "PASS_SOURCE_ONLY",
            "failures":failures,"source_hours":HOURS,"decision_count":len(times),
            "core_decision_count":len(coretimes),"funding_events":int(d["event"].sum()),
            "oi_eligible_decisions":int(eligible[times].sum()),
            "oi_blocked_decisions":int((~eligible[times]).sum()),
            "oi_source":oi_receipt,"raw_active_decision_counts":counts,
            "synthetic_future_mutation_pass":True,"pnl_computed":False,
            "training_only":True,"holdout_accessed":False}
def run(root,oi_root):
    d=load(root);oi,oi_receipt=load_oi(oi_root)
    return check(d,oi,oi_receipt)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--oi-root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=run(a.root,a.oi_root)
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("ON_SOURCE_GATE",json.dumps(out,sort_keys=True),flush=True)
    raise SystemExit(0 if out["decision"]=="PASS_SOURCE_ONLY" else 2)
