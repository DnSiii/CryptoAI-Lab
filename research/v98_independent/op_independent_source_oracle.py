#!/usr/bin/env python3
"""OP independent source oracle, reimplements persistent breakout state without importing OP signals."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from op_sources import bundle
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    close=d["c"];q=d["q"];rate=d["rate"]
    leader=-1;previous=np.zeros(4);count=core_count=valid_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        expected=np.zeros((4,4))
        r672=np.log(close[t]/close[t-672]);r168=np.log(close[t]/close[t-168]);r48=np.log(close[t]/close[t-48])
        released=False
        if leader>=0 and (close[t,leader]<min(close[t-168:t,leader]) or r168[leader]<-.08):
            leader=-1;released=True
        if leader<0 and not released:
            picks=[j for j in range(4) if close[t,j]>max(close[t-672:t,j]) and r168[j]>.04]
            if picks:leader=sorted(picks,key=lambda j:(-r672[j],j))[0]
        if leader>=0:expected[0,leader]=.58
        if leader<0 and r672[0]>.06 and r168[0]>0:expected[0,0]=.14
        if leader>=0 and leader!=0 and r672[0]>0 and r168[0]>0:expected[0,0]=.12
        changed=not np.array_equal(previous,expected[0])
        if changed:core_count+=1
        previous=expected[0].copy()
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167])
            vol=q[t-47:t+1].sum(axis=0)/np.maximum(q[t-95:t-47].sum(axis=0),1e-9)
            picks=[j for j in range(4) if r48[j]>.035 and grow[j]>0 and vol[j]>1.10]
            if picks:expected[1,sorted(picks,key=lambda j:(-r48[j],j))[0]]=.14
        carry=np.sum(np.vstack([rate[t-k] for k in range(0,161,8)]),axis=0)
        hi=max((1,2,3),key=lambda j:(carry[j],-j));low=min((1,2,3),key=lambda j:(carry[j],j))
        if carry[hi]-carry[low]>.004 and np.ptp(r168[1:])<.30:
            expected[2,hi]=-.07;expected[2,low]=.07
        if int(np.count_nonzero(r48<0))>=3 and r48[0]<-.05:expected[3,0]=-.16
        elif r168[0]<-.08 and r48[0]>.025:expected[3,0]=.12
        bull=int(np.count_nonzero(r672>0))>=3 and r168[0]>=0
        bear=int(np.count_nonzero(r672<0))>=3 and r168[0]<0
        mult=(1.,.75,.5) if bull else ((.6,1.,1.) if bear else (.8,1.,.8))
        for k in (1,2,3):expected[k]*=mult[k-1]
        err=float(np.max(np.abs(expected-raw[t])));maxerr=max(maxerr,err)
        if err>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all() or bool(updates[t,0])!=changed:
            raise ValueError("OP_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        count+=1
    if count!=105 or valid_count!=95 or core_count!=int(updates[:,0].sum()):
        raise ValueError("OP_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OP_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":count,"core_state_transitions_reconstructed":core_count,
            "oi_eligible":valid_count,"blocked":count-valid_count,
            "max_weight_error":maxerr,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
