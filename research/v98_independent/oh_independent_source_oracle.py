#!/usr/bin/env python3
"""OH independent recomputation of quote-volume participation raw targets, not PnL."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oh_sources import bundle,load_oi
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);q=d["q"];expected=np.zeros((4,4));matched=core=valid_count=0
    for t in range(WARMUP,HOURS,168):
        r336=p[t]-p[t-336];r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        v168=q[t-167:t+1].sum(axis=0)/np.maximum(q[t-335:t-167].sum(axis=0),1e-9)
        v24=q[t-23:t+1].sum(axis=0)/np.maximum(q[t-47:t-23].sum(axis=0),1e-9)
        pos=sum(r168>0)>=3 and np.median(v168)>1
        neg=sum(r168<0)>=3 and np.median(v168)>1
        if (t-WARMUP)%672==0:
            expected[0]=0
            leaders=sorted((j for j in range(4) if r336[j]>0 and v168[j]>1.05),
                           key=lambda j:(-r336[j]*min(v168[j],3),j))
            if leaders:
                expected[0,leaders[0]]=.58
                if len(leaders)>1:expected[0,leaders[1]]=.18
            elif sum(r168<0)>=3:expected[0,0]=-.30
            elif r336[0]>0:expected[0,0]=.24
            elif r336[0]<0:expected[0,0]=-.20
            core+=1
        expected[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167]);short=np.log(oi[t]/oi[t-24])
            picks=sorted((j for j in range(4) if r72[j]>.05 and r24[j]>.015 and v24[j]>1.4 and grow[j]>0),
                         key=lambda j:(-r72[j]*min(v24[j],3),j))
            if picks:expected[1,picks[0]]=.22
            lo=sorted(range(4),key=lambda j:(r168[j],j))[0]
            hi=sorted(range(4),key=lambda j:(-r168[j],j))[0]
            if lo!=hi and r168[hi]-r168[lo]>.12 and v168[lo]>v168[hi] and grow[lo]>0:
                expected[2,lo]=.12;expected[2,hi]=-.12
            if r24[0]<-.04 and v24[0]>2 and short[0]<-.02:
                expected[3,0]=-.22;expected[3,1]=-.10
            elif r168[0]<-.10 and r24[0]>.035 and v24[0]>1.6:
                expected[3,0]=.20
            mult=(1.,.8,.4) if pos else ((.6,.8,1.) if neg else (.8,1.,.8))
            for k in (1,2,3):expected[k]*=mult[k-1]
        if np.max(np.abs(expected-raw[t]))>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OH_INDEPENDENT_SOURCE_MISMATCH_"+str(t))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:raise ValueError("OH_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OH_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
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
