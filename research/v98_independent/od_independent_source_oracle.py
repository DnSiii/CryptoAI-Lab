#!/usr/bin/env python3
"""OD independent OI-price source reconstruction: 105 decisions, source-only."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi,bundle
def audit(d,oi):
    got,updates,_,mask=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    lp=np.log(d["c"]);held=np.zeros((4,4))
    matched=eligible=core=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        p672=lp[t]-lp[t-672];p336=lp[t]-lp[t-336]
        p168=lp[t]-lp[t-168];p24=lp[t]-lp[t-24]
        if (t-WARMUP)%672==0:
            held[0]=0
            selected=sorted((j for j in range(4) if p672[j]>0 and p168[j]>0),
                            key=lambda j:(-p672[j],j))
            if selected:
                held[0,selected[0]]=.54
                if len(selected)>1:held[0,selected[1]]=.18
            elif p168[0]<0 and (p168<0).sum()>=3:
                held[0,0]=-.30
            core+=1
        held[1:]=0
        window=oi[t-167:t+1]
        valid=bool(np.isfinite(window).all() and np.all(window>0))
        if valid:
            eligible+=1
            d24=np.log(oi[t]/oi[t-24])
            d168=np.log(oi[t]/oi[t-167])
            pick=sorted((j for j in range(4) if p24[j]>.025 and d24[j]>.02 and d168[j]>0),
                        key=lambda j:(-p24[j]*d24[j],j))
            if pick:held[1,pick[0]]=.18
            rank=p168-d168
            j=sorted((1,2,3),key=lambda k:(-rank[k],k))[0]
            if rank[j]>rank[0]+.08 and p168[j]>0:
                held[2,j]=.10;held[2,0]=-.10
            if (p24<-.035).sum()>=3 and (d24<-.025).sum()>=3:
                held[3,0]=-.16
            elif p168[0]<-.10 and p24[0]>.025 and (p24[1:]>0).sum()>=2:
                held[3,0]=.14
            if p336[0]>0 and (p168>0).sum()>=3:
                held[2]*=.75;held[3]*=.50
            else:held[1]*=.75
        err=float(np.max(np.abs(held-got[t])))
        maxerr=max(maxerr,err)
        if err>1e-10 or valid!=bool(mask[t]) or not updates[t,1:].all():
            raise ValueError("OD_INDEPENDENT_SOURCE_MISMATCH_"+str(t))
        matched+=1
    if matched!=105 or core!=27 or eligible!=95:raise ValueError("OD_SOURCE_ORACLE_COUNTS")
    return {"decision":"PASS_OD_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decision_reconstructions":matched,"core_reconstructions":core,
            "native_oi_eligible":eligible,"blocked":matched-eligible,
            "max_weight_error":maxerr,"holdout_accessed":False,"training_only":True}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
