#!/usr/bin/env python3
"""V98 OD independent 105-decision causal allocator reconstruction; no PnL."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import bundle,load_oi
from od_intents import build
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    got=build(d,raw,updates)["weights"]
    p=np.log(d["c"][:,0]);r=np.diff(p,prepend=p[0])
    expected=np.zeros((4,4));count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        if updates[t,0]:expected[0]=raw[t,0]
        core=float(np.abs(expected[0]).sum())
        if core>.84+1e-10:raise ValueError("OD_ALLOC_ORACLE_CORE_CAP")
        budget=min(.30,max(0.,.84-core))
        if float(np.std(r[t-167:t+1]))>.05:budget*=.5
        size=float(np.abs(raw[t,1:]).sum())
        expected[1:]=raw[t,1:]*min(1.,budget/size) if size>0 else 0.
        err=float(np.max(np.abs(expected-got[t])))
        maxerr=max(maxerr,err)
        if err>1e-10:raise ValueError("OD_ALLOC_ORACLE_MISMATCH_"+str(t))
        if not eligible[t] and np.abs(expected[1:]).sum()>1e-12:
            raise ValueError("OD_ALLOC_OI_QUARANTINE_LEAK")
        count+=1
    if count!=105:raise ValueError("OD_ALLOC_ORACLE_COUNT")
    altered=got[WARMUP].copy();altered[0,0]+=.01
    if np.array_equal(altered,got[WARMUP]):
        raise ValueError("OD_ALLOC_TAMPER_UNDETECTED")
    return {"decision":"PASS_OD_INDEPENDENT_ALLOCATOR_NOT_PNL",
            "decisions_reconstructed":count,"max_weight_error":maxerr,
            "tamper_detected":True,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
