#!/usr/bin/env python3
"""ON independently reimplemented stateful source oracle, no ON signal implementation import."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from on_sources import bundle
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    close=d["c"];q=d["q"];rate=d["rate"]
    btc=eth=0;previous=np.zeros(4);count=core_count=valid_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        expected=np.zeros((4,4))
        r672=np.log(close[t]/close[t-672])
        r168=np.log(close[t]/close[t-168])
        r48=np.log(close[t]/close[t-48])
        if btc==1:
            if r672[0]<-.04 or r168[0]<-.08:btc=0
        elif btc==-1:
            if r672[0]>.01 or r168[0]>.08:btc=0
        if btc==0:
            if r672[0]>.04 and r168[0]>-.02:btc=1
            elif r672[0]<-.10 and r168[0]<-.02:btc=-1
        relative=r672[1]-r672[0]
        if eth and (r672[1]<-.03 or relative<-.05 or btc==-1):eth=0
        if not eth and btc!=-1 and r672[1]>.08 and relative>.01:eth=1
        expected[0,0]=.46 if btc==1 else (-.36 if btc==-1 else 0.)
        expected[0,1]=.18 if eth else 0.
        changed=not np.array_equal(previous,expected[0])
        if changed:core_count+=1
        previous=expected[0].copy()
        valid=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if valid:
            valid_count+=1
            oi_growth=np.log(oi[t]/oi[t-167])
            volume=q[t-47:t+1].sum(axis=0)/np.maximum(q[t-95:t-47].sum(axis=0),1e-9)
            picks=sorted((j for j in (2,3) if r48[j]>.06 and oi_growth[j]>0 and volume[j]>1.20),
                         key=lambda j:(-r48[j],j))
            if picks:expected[1,picks[0]]=.16
        carry=np.sum(np.vstack([rate[t-k] for k in range(0,161,8)]),axis=0)
        high=max((1,2,3),key=lambda j:(carry[j],-j))
        low=min((1,2,3),key=lambda j:(carry[j],j))
        if carry[high]-carry[low]>.005 and np.ptp(r168[1:])<.20:
            expected[2,high]=-.08;expected[2,low]=.08
        if int(np.count_nonzero(r48<0))>=3 and r48[0]<-.06:expected[3,0]=-.14
        elif r168[0]<-.10 and r48[0]>.03:expected[3,0]=.12
        bull=int(np.count_nonzero(r672>0))>=3 and r168[0]>=0
        bear=int(np.count_nonzero(r672<0))>=3 and r168[0]<0
        mult=(1.,.7,.5) if bull else ((.5,1.,1.) if bear else (.75,1.,.75))
        for k in (1,2,3):expected[k]*=mult[k-1]
        err=float(np.max(np.abs(expected-raw[t])));maxerr=max(maxerr,err)
        if err>1e-10 or valid!=bool(eligible[t]) or not updates[t,1:].all() or bool(updates[t,0])!=changed:
            raise ValueError("ON_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        count+=1
    if count!=105 or valid_count!=95 or core_count!=int(updates[:,0].sum()):
        raise ValueError("ON_INDEPENDENT_SOURCE_COUNTS")
    return {"decision":"PASS_ON_INDEPENDENT_STATEFUL_SOURCE_ONLY_NOT_PNL",
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
