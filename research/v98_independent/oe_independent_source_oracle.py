#!/usr/bin/env python3
"""OE independent native OI/funding-price source reconstruction; no PnL."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oe_sources import bundle,load_oi
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    p=np.log(d["c"]);r=np.diff(p,axis=0,prepend=p[:1])
    held=np.zeros((4,4));matched=core=valid_count=0
    for t in range(WARMUP,HOURS,168):
        a=p[t]-p[t-336];b=p[t]-p[t-168]
        d72=p[t]-p[t-72];d24=p[t]-p[t-24]
        if (t-WARMUP)%672==0:
            held[0]=0
            vol=np.std(r[t-167:t+1],axis=0)
            ranks=sorted((j for j in range(4) if a[j]>0 and b[j]>0),
                         key=lambda j:(-a[j]/(1+8*vol[j]),j))
            for rank,j in enumerate(ranks[:3]):held[0,j]=(.42,.20,.10)[rank]
            if not ranks and (b<0).sum()>=3:held[0,0]=-.36
            core+=1
        held[1:]=0
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            d168=np.log(oi[t]/oi[t-167]);d_24=np.log(oi[t]/oi[t-24])
            rates=d["rate"][t]
            candidates=sorted((j for j in range(4) if d72[j]>.025 and d168[j]>.02 and rates[j]<0),
                              key=lambda j:(-(-rates[j]*d72[j]),j))
            if candidates:held[1,candidates[0]]=.20
            low=int(np.argmin(rates));high=int(np.argmax(rates))
            if low!=high and rates[high]-rates[low]>.00020 and d168[low]>0 and d168[high]>0:
                held[2,low]=.10;held[2,high]=-.10
            if (d24<-.04).sum()>=3 and (d_24<-.03).sum()>=3:
                held[3,0]=-.20
            elif d72[0]<-.09 and d24[0]>.03 and d_24[0]>.01:
                held[3,0]=.16
            if a[0]>0 and (b>0).sum()>=3:
                held[2]*=.75;held[3]*=.5
            else:held[1]*=.75
        err=float(np.max(np.abs(raw[t]-held)))
        if err>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all():
            raise ValueError("OE_INDEPENDENT_SOURCE_MISMATCH_"+str(t))
        matched+=1
    if matched!=105 or core!=27 or valid_count!=95:
        raise ValueError("OE_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_OE_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
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
