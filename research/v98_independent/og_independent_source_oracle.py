#!/usr/bin/env python3
"""OG independent source target oracle: independently rebuilds 105 weekly raw targets."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from og_sources import bundle,load_oi
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);expected=np.zeros((4,4));matched=core=valid_count=0
    for t in range(WARMUP,HOURS,168):
        r672=p[t]-p[t-672];r336=p[t]-p[t-336];r168=p[t]-p[t-168];r24=p[t]-p[t-24]
        pos=r336[0]>0 and int(sum(r168>0))>=3
        neg=r336[0]<0 and int(sum(r168<0))>=3
        if (t-WARMUP)%672==0:
            expected[0]=0
            hourly=p[t-167:t+1]-p[t-168:t]
            scale=np.maximum(hourly.std(axis=0)*np.sqrt(168),.015)
            score=r672/scale
            picks=sorted((j for j in range(4) if r672[j]>0 and r168[j]>0),
                         key=lambda j:(-score[j],j))
            if len(picks)>=2:
                expected[0,picks[0]]=.42;expected[0,picks[1]]=.20
            elif sum(r672<0)>=3 and r168[0]<0:
                j=sorted(range(1,4),key=lambda k:(score[k],k))[0]
                expected[0,0]=-.34;expected[0,j]=-.18
            elif r672[0]>0:expected[0,0]=.22
            elif r672[0]<0:expected[0,0]=-.22
            core+=1
        expected[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167]);short=np.log(oi[t]/oi[t-24])
            pulls=sorted((j for j in range(4) if r168[j]>.06 and r24[j]<-.015 and grow[j]>0),
                         key=lambda j:(-(r168[j]-r24[j]),j))
            if pulls:expected[1,pulls[0]]=.22
            low=sorted(range(4),key=lambda j:(d["rate"][t,j],j))[0]
            high=sorted(range(4),key=lambda j:(-d["rate"][t,j],j))[0]
            if low!=high and d["rate"][t,high]-d["rate"][t,low]>.00015:
                expected[2,low]=.12;expected[2,high]=-.12
            if r24[0]<-.045 and short[0]<-.025:
                expected[3,0]=-.22;expected[3,1]=-.10
            elif r168[0]<-.10 and r24[0]>.025 and short[0]>0:
                expected[3,0]=.20
            mult=(1.,.75,.5) if pos else ((.6,.8,1.) if neg else (.8,1.,.8))
            for k in (1,2,3):expected[k]*=mult[k-1]
        if np.max(np.abs(expected-raw[t]))>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OG_INDEPENDENT_SOURCE_MISMATCH_"+str(t))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:raise ValueError("OG_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OG_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
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
