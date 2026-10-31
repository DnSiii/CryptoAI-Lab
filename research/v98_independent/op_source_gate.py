#!/usr/bin/env python3
"""OP source-only independent clock and persistent-state transition gate before PnL."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from op_sources import bundle,load_oi,synthetic_causality,NAMES
def check(d,oi,oi_receipt):
    synthetic_causality()
    raw,updates,active,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    times=np.arange(WARMUP,HOURS,168)
    failures=[]
    if not np.array_equal(np.flatnonzero(updates[:,1]),times) or not np.all(updates[times,1:]):failures.append("OP_OPTIOPAL_CLOCK")
    coretimes=np.flatnonzero(updates[:,0])
    if not np.all(np.isin(coretimes,times)) or not (0<len(coretimes)<=105):failures.append("OP_CORE_TRANSITIOP_CLOCK")
    if int(d["event"].sum())!=9144:failures.append("OP_FUNDING_EVENTS")
    if np.any(np.abs(raw[:,0]).sum(axis=1)>.84+1e-10):failures.append("OP_CORE_BUDGET")
    if np.any((np.abs(np.diff(raw,axis=0)).sum(axis=(1,2))>1e-12)&~np.any(updates[1:],axis=1)):failures.append("OP_SILENT_CHANGE")
    if not np.isfinite(raw).all():failures.append("OP_NOPFINITE")
    if np.any(np.abs(raw[times[~eligible[times]],1]).sum(axis=1)>1e-12):failures.append("OP_OI_QUARANTINE_LEAK")
    if int(eligible[times].sum())!=95:failures.append("OP_OI_MASK_NOT_FROZEN_95")
    prev=np.zeros(4)
    for t in times:
        changed=not np.array_equal(raw[t,0],prev)
        if changed!=bool(updates[t,0]):failures.append("OP_CORE_UNDECLARED_CHANGE_"+str(t))
        prev=raw[t,0].copy()
    counts={str(year):{name:int(active[times[(times>=lo)&(times<hi)],i].sum()) for i,name in enumerate(NAMES)}
            for year,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    return {"decision":"REJECT_SOURCE_OPLY" if failures else "PASS_SOURCE_OPLY",
            "failures":failures,"source_hours":HOURS,"decisiop_count":len(times),
            "core_decisiop_count":len(coretimes),"funding_events":int(d["event"].sum()),
            "oi_eligible_decisions":int(eligible[times].sum()),
            "oi_blocked_decisions":int((~eligible[times]).sum()),
            "oi_source":oi_receipt,"raw_active_decisiop_counts":counts,
            "synthetic_future_mutatiop_pass":True,"pnl_computed":False,
            "training_only":True,"holdout_accessed":False}
def run(root,oi_root):
    d=load(root);oi,oi_receipt=load_oi(oi_root)
    return check(d,oi,oi_receipt)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--oi-root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=run(a.root,a.oi_root)
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("OP_SOURCE_GATE",json.dumps(out,sort_keys=True),flush=True)
    raise SystemExit(0 if out["decision"]=="PASS_SOURCE_OPLY" else 2)
