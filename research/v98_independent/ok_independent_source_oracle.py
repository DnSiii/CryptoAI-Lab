#!/usr/bin/env python3
"""V98 OK independent source reconstruction, no import of OK source decision logic."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from ok_sources import bundle
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);q=d["q"];rate=d["rate"];expected=np.zeros((4,4))
    matched=core=valid_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        r504=p[t]-p[t-504];r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        bull=int(sum(r168>0))>=3;bear=int(sum(r168<0))>=3
        if (t-WARMUP)%672==0:
            expected[0]=0
            sigma=np.std(np.diff(p[t-168:t+1],axis=0),axis=0)
            picks=sorted((j for j in range(4) if r504[j]>0 and r168[j]>0),
                         key=lambda j:(-r504[j]/max(float(sigma[j]),1e-8),j))
            if picks:
                expected[0,picks[0]]=.52
                if len(picks)>1:expected[0,picks[1]]=.12
            elif r168[0]<0 and bear:expected[0,0]=-.28
            core+=1
        expected[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167])
            vol=q[t-23:t+1].sum(axis=0)/np.maximum(q[t-47:t-23].sum(axis=0),1e-9)
            picks=sorted((j for j in range(4) if r72[j]>0 and r24[j]>0 and grow[j]<-.015 and vol[j]>1.10),
                         key=lambda j:(-(r72[j]+r24[j]),j))
            if picks:expected[1,picks[0]]=.14
        carry=np.sum(np.vstack([rate[t-k] for k in range(0,161,8)]),axis=0)
        lo=sorted(range(4),key=lambda j:(carry[j],j))[0]
        hi=sorted(range(4),key=lambda j:(-carry[j],j))[0]
        if lo!=hi and carry[hi]-carry[lo]>=.001 and r168[lo]>-.12 and r168[hi]>-.12:
            expected[2,lo]=.04;expected[2,hi]=-.04
        if bear and r24[0]<0:expected[3,0]=-.10
        elif bull and r24[0]>0:expected[3,0]=.10
        mult=(1.,.65,.8) if bull else ((.5,1.,1.) if bear else (.8,1.,.75))
        for k in (1,2,3):expected[k]*=mult[k-1]
        err=float(np.max(np.abs(expected-raw[t])));maxerr=max(maxerr,err)
        if err>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OK_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:raise ValueError("OK_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OK_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":matched,"core_reconstructed":core,
            "oi_eligible":valid_count,"blocked":matched-valid_count,
            "max_weight_error":maxerr,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
