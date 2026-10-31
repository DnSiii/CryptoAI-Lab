#!/usr/bin/env python3
"""OF independent recomputation of every native-source target, without strategy PnL."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from of_sources import bundle,load_oi

def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);expected=np.zeros((4,4));matched=core=valid_count=0
    for t in range(WARMUP,HOURS,168):
        r672=np.subtract(p[t],p[t-672]);r168=np.subtract(p[t],p[t-168])
        r72=np.subtract(p[t],p[t-72]);r24=np.subtract(p[t],p[t-24])
        bull=int(sum(x>0 for x in r672))>=3 and r168[0]>0
        bear=int(sum(x<0 for x in r672))>=3 and r168[0]<0
        if (t-WARMUP)%672==0:
            expected[0]=0
            if bull:
                best=sorted(range(1,4),key=lambda j:(-r672[j],j))[0]
                expected[0,0]=.34;expected[0,best]=.24
            elif bear:
                worst=sorted(range(1,4),key=lambda j:(r672[j],j))[0]
                expected[0,0]=-.34;expected[0,worst]=-.16
            elif r672[0]>0:expected[0,0]=.24
            elif r672[0]<0:expected[0,0]=-.20
            core+=1
        expected[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167])
            candidates=sorted((j for j in range(4) if r72[j]>.035 and r24[j]>0 and grow[j]>.025),
                              key=lambda j:(-r72[j]*grow[j],j))
            if candidates:expected[1,candidates[0]]=.24
            elif r168[0]<-.08 and grow[0]>.03:expected[1,0]=-.20
            score=r168-.5*grow
            lo=sorted(range(4),key=lambda j:(score[j],j))[0]
            hi=sorted(range(4),key=lambda j:(-score[j],j))[0]
            if lo!=hi and score[hi]-score[lo]>.075 and grow[lo]>0 and grow[hi]>0:
                expected[2,lo]=.12;expected[2,hi]=-.12
            if sum(x<0 for x in r168)>=3 and r72[0]<-.04:
                expected[3,0]=-.24;expected[3,1]=-.10
            elif r168[0]<-.12 and r24[0]>.025 and sum(x>0 for x in r24)>=3:
                expected[3,0]=.24
            multipliers=(1.,.8,.4) if bull else ((.6,.6,1.) if bear else (.8,1.,.8))
            for k in (1,2,3):expected[k]*=multipliers[k-1]
        if np.max(np.abs(expected-raw[t]))>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OF_INDEPENDENT_SOURCE_MISMATCH_"+str(t))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:
        raise ValueError("OF_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OF_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":matched,"core_reconstructed":core,
            "oi_eligible":valid_count,"blocked":matched-valid_count,
            "max_weight_error":0.0,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
