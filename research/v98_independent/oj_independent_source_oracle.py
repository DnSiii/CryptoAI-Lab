#!/usr/bin/env python3
"""OJ independent source oracle: reconstruct each preregistered target without importing OJ signal functions."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oj_sources import bundle,load_oi
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);q=d["q"];expected=np.zeros((4,4));matched=core=valid_count=0
    for t in range(WARMUP,HOURS,168):
        ret={n:p[t]-p[t-n] for n in (24,72,168,336)}
        r24,r72,r168,r336=(ret[n] for n in (24,72,168,336))
        vol=q[t-23:t+1].sum(axis=0)/np.maximum(q[t-47:t-23].sum(axis=0),1e-9)
        positive=int(sum(r168>0))>=3
        negative=int(sum(r168<0))>=3
        if (t-WARMUP)%672==0:
            expected[0]=0
            leaders=sorted((j for j in range(4) if r336[j]>0 and r168[j]>0),
                           key=lambda j:(-(r336[j]+r168[j]),j))
            if leaders:
                expected[0,leaders[0]]=.42
                if len(leaders)>1:expected[0,leaders[1]]=.12
            elif r168[0]<0:expected[0,0]=-.32
            elif r336[0]>0:expected[0,0]=.20
            core+=1
        expected[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167])
            picks=sorted((j for j in range(4) if r72[j]>0 and r24[j]>0 and grow[j]>0 and vol[j]>1),
                         key=lambda j:(-(r72[j]+r24[j]),j))
            if picks:expected[1,picks[0]]=.12
            elif all(r72<0) and grow[0]>0:expected[1,0]=-.12
            score=r168-.35*grow
            hi=sorted(range(4),key=lambda j:(-score[j],j))[0]
            lo=sorted(range(4),key=lambda j:(score[j],j))[0]
            if hi!=lo and score[hi]-score[lo]>.03:
                expected[2,hi]=.05;expected[2,lo]=-.05
            if r168[0]<0 and r24[0]<0:expected[3,0]=-.08
            elif r168[0]<0 and r24[0]>0:expected[3,0]=.08
            elif r168[0]>0 and r24[0]>0:expected[3,0]=.08
            multipliers=(1.,.8,.8) if positive else ((.8,1.,1.) if negative else (.9,.9,.9))
            for k in (1,2,3):expected[k]*=multipliers[k-1]
        if np.max(np.abs(expected-raw[t]))>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OJ_INDEPENDENT_SOURCE_MISMATCH_"+str(t))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:raise ValueError("OJ_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OJ_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
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
