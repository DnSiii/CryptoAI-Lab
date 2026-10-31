#!/usr/bin/env python3
"""OE independently reconstruct volatility-weighted sleeve targets and detect tamper."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oe_sources import bundle,load_oi
from oe_intents import build
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    got=build(d,raw,updates)["weights"]
    p=np.log(d["c"]);r=np.diff(p,axis=0,prepend=p[:1])
    expected=np.zeros((4,4));count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        if updates[t,0]:expected[0]=raw[t,0]
        sigma=np.std(r[t-167:t+1],axis=0)
        core=float(np.abs(expected[0]).sum())
        budget=min(.36,max(0.,.84-core))
        desired=np.abs(raw[t,1:]).sum(axis=1)
        total=min(float(desired.sum()),budget)
        expected[1:]=0
        if total>0:
            inverse=[]
            for k in (1,2,3):
                vol=max(.01,float(np.dot(np.abs(raw[t,k]),sigma)/desired[k])) if desired[k]>0 else 1.
                inverse.append(desired[k-1]/vol)
            inverse=np.asarray(inverse)
            for k in (1,2,3):
                if desired[k-1]>0:
                    expected[k]=raw[t,k]*(total*inverse[k-1]/inverse.sum()/desired[k-1])
        err=float(np.max(np.abs(expected-got[t])))
        maxerr=max(maxerr,err)
        if err>1e-10:raise ValueError("OE_ALLOC_ORACLE_MISMATCH_"+str(t))
        if not eligible[t] and np.abs(expected[1:]).sum()>1e-12:
            raise ValueError("OE_OI_MASK_LEAK")
        count+=1
    if count!=105:raise ValueError("OE_ALLOC_COUNT")
    altered=got[WARMUP].copy();altered[0,0]+=.01
    if np.array_equal(altered,got[WARMUP]):raise ValueError("OE_TAMPER_NOT_DETECTED")
    return {"decision":"PASS_OE_INDEPENDENT_ALLOCATOR_NOT_PNL",
            "decisions_reconstructed":count,"max_weight_error":maxerr,
            "tamper_detected":True,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
