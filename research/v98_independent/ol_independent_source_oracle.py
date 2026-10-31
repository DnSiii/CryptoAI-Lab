#!/usr/bin/env python3
"""OL independent source reconstruction: no import of OL signal functions."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from ol_sources import bundle
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);c=d["c"];h=d["h"];l=d["l"];q=d["q"];rate=d["rate"]
    expected=np.zeros((4,4));matched=core=valid_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        r336=np.log(c[t]/c[t-336]);r168=np.log(c[t]/c[t-168]);r24=np.log(c[t]/c[t-24])
        v24=np.std(np.diff(np.log(c[t-24:t+1]),axis=0),axis=0)
        v168=np.std(np.diff(np.log(c[t-168:t+1]),axis=0),axis=0)
        bull=int(sum(r168>0))>=3;bear=int(sum(r168<0))>=3
        if (t-WARMUP)%672==0:
            expected[0]=0
            picks=sorted((j for j in range(4) if c[t,j]>max(h[t-672:t,j]) and r336[j]>0),
                         key=lambda j:(-np.log(c[t,j]/max(h[t-672:t,j]))/max(float(v168[j]),1e-8),j))
            if picks:
                expected[0,picks[0]]=.58
                if len(picks)>1:expected[0,picks[1]]=.14
            elif sum(r336<0)>=3 and c[t,0]<min(l[t-336:t,0]):expected[0,0]=-.32
            core+=1
        expected[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            grow=np.log(oi[t]/oi[t-167])
            volratio=v24/np.maximum(v168,1e-8)
            volume=q[t-23:t+1].sum(axis=0)/np.maximum(q[t-47:t-23].sum(axis=0),1e-9)
            picks=sorted((j for j in range(4) if volratio[j]<.8 and volume[j]>1.2 and r24[j]>.02 and grow[j]>0),
                         key=lambda j:(-r24[j],j))
            if picks:expected[1,picks[0]]=.16
        carry=np.sum(np.vstack([rate[t-k] for k in range(0,161,8)]),axis=0)
        residual=r168-r168.mean()
        rank=sorted((1,2,3),key=lambda j:(-residual[j],j))
        top,bottom=rank[0],rank[-1]
        if residual[top]-residual[bottom]>.06 and carry[top]<=carry[bottom]:
            expected[2,top]=.06;expected[2,bottom]=-.06
        if sum(r24<0)>=3 and v24[0]>1.5*max(float(v168[0]),1e-8):expected[3,0]=-.14
        elif bull and v24[0]<.7*max(float(v168[0]),1e-8):expected[3,0]=.10
        mult=(1.,.9,.5) if bull else ((.4,1.,1.) if bear else (.7,1.,.6))
        for k in (1,2,3):expected[k]*=mult[k-1]
        err=float(np.max(np.abs(expected-raw[t])));maxerr=max(maxerr,err)
        if err>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OL_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:raise ValueError("OL_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OL_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
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
