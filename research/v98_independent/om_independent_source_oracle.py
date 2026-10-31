#!/usr/bin/env python3
"""OM independent source oracle; reconstructs all weekly targets without importing OM signal implementation."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from om_sources import bundle
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);q=d["q"];rate=d["rate"]
    count=core=valid_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        expected=np.zeros((4,4))
        r336=np.log(d["c"][t]/d["c"][t-336])
        r168=np.log(d["c"][t]/d["c"][t-168])
        r24=np.log(d["c"][t]/d["c"][t-24])
        bull=int(np.count_nonzero(r168>0))>=3
        bear=int(np.count_nonzero(r168<0))>=3
        leaders=sorted((j for j in range(4) if r336[j]>0 and r168[j]>0),
                       key=lambda j:(-r336[j],j))
        if bull and leaders:
            expected[0,leaders[0]]=.52
            if len(leaders)>1:expected[0,leaders[1]]=.16
        elif bear and r336[0]<0:expected[0,0]=-.48
        elif r336[0]>0 and r168[0]>0:expected[0,0]=.40
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            oi_growth=np.log(oi[t]/oi[t-167])
            volume=q[t-23:t+1].sum(axis=0)/np.maximum(q[t-47:t-23].sum(axis=0),1e-9)
            picks=sorted((j for j in range(4) if oi_growth[j]>0 and r24[j]>.02 and volume[j]>1.10 and r24[j]>r168[j]/7),
                         key=lambda j:(-r24[j],j))
            if picks:expected[1,picks[0]]=.16
        carry=np.sum(np.vstack([rate[t-k] for k in range(0,161,8)]),axis=0)
        ranking=sorted((1,2,3),key=lambda j:(-r168[j],j))
        winner,loser=ranking[0],ranking[-1]
        if r168[winner]-r168[loser]>=.08 and carry[winner]>carry[loser]:
            expected[2,winner]=-.07;expected[2,loser]=.07
        if int(np.count_nonzero(r24<0))>=3 and r24[0]<-.035:expected[3,0]=-.16
        elif int(np.count_nonzero(r24>0))>=3 and r168[0]<0:expected[3,0]=.12
        mult=(1.,.75,.50) if bull else ((.65,1.,1.) if bear else (.8,1.,.8))
        for k in (1,2,3):expected[k]*=mult[k-1]
        err=float(np.max(np.abs(expected-raw[t])));maxerr=max(maxerr,err)
        if err>1e-10 or valid!=bool(eligible[t]) or not updates[t].all():
            raise ValueError("OM_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        count+=1;core+=1
    if count!=105 or core!=105 or valid_count!=95:raise ValueError("OM_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OM_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":count,"core_reconstructed":core,
            "oi_eligible":valid_count,"blocked":count-valid_count,
            "max_weight_error":maxerr,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
