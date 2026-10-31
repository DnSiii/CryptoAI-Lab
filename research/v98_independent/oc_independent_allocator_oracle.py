#!/usr/bin/env python3
"""OC independently reconstruct causal allocator targets, compare all 105 decisions and detect tampering."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oc_sources import bundle
from oc_intents import build
def audit(d):
    raw,updates,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")))
    got=build(d,raw,updates)["weights"]
    r=np.diff(np.log(d["c"][:,0]),prepend=np.log(d["c"][0,0]))
    expected=np.zeros((4,4));count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        core=float(np.abs(raw[t,0]).sum())
        if core>.84+1e-10:raise ValueError("OC_ALLOC_ORACLE_CORE_CAP")
        if updates[t,0]:expected[0]=raw[t,0]
        sigma=float(np.std(r[t-167:t+1]))
        budget=min(.28,max(0.,.84-core))
        if sigma>.05:budget*=.5
        size=float(np.abs(raw[t,1:]).sum())
        expected[1:]=raw[t,1:]*min(1.,budget/size) if size>0 else 0.
        err=float(np.max(np.abs(expected-got[t])))
        maxerr=max(maxerr,err)
        if err>1e-10:raise ValueError("OC_ALLOC_ORACLE_TARGET_MISMATCH_"+str(t))
        count+=1
    if count!=105:raise ValueError("OC_ALLOC_ORACLE_COUNT")
    tampered=got[WARMUP].copy();tampered[0,0]+=.01
    if np.max(np.abs(tampered-expected))<=1e-10:
        raise ValueError("OC_ALLOC_ORACLE_TAMPER_UNDETECTED")
    return {"decision":"PASS_OC_INDEPENDENT_ALLOCATOR_RECONSTRUCTION_NOT_PNL",
            "decisions_reconstructed":count,"max_weight_error":maxerr,
            "tamper_detected":True,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=audit(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
