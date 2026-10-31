#!/usr/bin/env python3
"""Independent OS allocator oracle: rederives core-first allocation and priority."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from os_sources import bundle,load_oi
from os_intents import build
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    got=build(d,raw,updates)["weights"];p=np.log(d["c"])
    expected=np.zeros((4,4));count=core_count=0;maxerr=0.;first_expected=None
    for t in range(WARMUP,HOURS,168):
        if updates[t,0]:expected[0]=raw[t,0];core_count+=1
        core=float(np.abs(expected[0]).sum())
        remaining=min(.36,max(0.,.84-core))
        r336=p[t]-p[t-336]
        bull=int(sum(r336>0))>=3;bear=int(sum(r336<0))>=3
        priority=(1,2,3) if bull else ((3,2,1) if bear else (2,3,1))
        expected[1:]=0
        for k in priority:
            gross=float(np.abs(raw[t,k]).sum())
            if gross>0 and remaining>0:
                used=min(gross,remaining);expected[k]=raw[t,k]*(used/gross);remaining-=used
        if first_expected is None:first_expected=expected.copy()
        err=float(np.max(np.abs(expected-got[t])));maxerr=max(maxerr,err)
        if err>1e-10:raise ValueError("OS_ALLOC_OSACLE_MISMATCH_"+str(t))
        if np.abs(expected).sum()>.84+1e-10:raise ValueError("OS_HIDDEN_GROSS")
        count+=1
    if count!=105 or core_count!=int(updates[:,0].sum()):raise ValueError("OS_ALLOC_COUNT")
    altered=got[WARMUP].copy();altered[0,0]+=.01
    if np.max(np.abs(altered-first_expected))<.009:raise ValueError("OS_TAMPER_NOT_DETECTED")
    return {"decision":"PASS_OS_INDEPENDENT_ALLOCATOS_NOT_PNL",
            "decisions_reconstructed":count,"core_transitions_reconstructed":core_count,
            "max_weight_error":maxerr,"tamper_detected":True,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
