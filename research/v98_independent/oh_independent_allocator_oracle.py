#!/usr/bin/env python3
"""OH independent allocator oracle: reconstructs participation regime and budget."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oh_sources import bundle,load_oi
from oh_intents import build
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    got=build(d,raw,updates)["weights"];p=np.log(d["c"]);q=d["q"]
    expected=np.zeros((4,4));count=0;maxerr=0.;first_expected=None
    for t in range(WARMUP,HOURS,168):
        if updates[t,0]:expected[0]=raw[t,0]
        core=float(np.abs(expected[0]).sum())
        remaining=min(.38,max(0.,.84-core))
        r168=p[t]-p[t-168]
        v=q[t-167:t+1].sum(axis=0)/np.maximum(q[t-335:t-167].sum(axis=0),1e-9)
        bull=sum(r168>0)>=3 and np.median(v)>1
        bear=sum(r168<0)>=3 and np.median(v)>1
        priority=(1,2,3) if bull else ((3,2,1) if bear else (2,1,3))
        expected[1:]=0
        for k in priority:
            gross=float(np.abs(raw[t,k]).sum())
            if gross>0 and remaining>0:
                used=min(gross,remaining);expected[k]=raw[t,k]*(used/gross);remaining-=used
        if first_expected is None:first_expected=expected.copy()
        err=float(np.max(np.abs(expected-got[t])));maxerr=max(maxerr,err)
        if err>1e-10:raise ValueError("OH_ALLOC_ORACLE_MISMATCH_"+str(t))
        if np.abs(expected).sum()>.84+1e-10:raise ValueError("OH_HIDDEN_GROSS")
        if not eligible[t] and np.abs(expected[1:]).sum()>1e-12:raise ValueError("OH_OI_MASK_LEAK")
        count+=1
    if count!=105:raise ValueError("OH_ALLOC_COUNT")
    altered=got[WARMUP].copy();altered[0,0]+=.01
    if np.max(np.abs(altered-first_expected))<.009:raise ValueError("OH_TAMPER_NOT_DETECTED")
    return {"decision":"PASS_OH_INDEPENDENT_ALLOCATOR_NOT_PNL",
            "decisions_reconstructed":count,"max_weight_error":maxerr,
            "tamper_detected":True,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
