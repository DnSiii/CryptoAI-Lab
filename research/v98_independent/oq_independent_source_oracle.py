#!/usr/bin/env python3
"""Independent OQ source oracle: rederives all four sleeve signals, no OQ signal import."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from oq_sources import bundle
def audit(d,oi):
    raw,updates,_,eligible=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    close=d["c"];rate=d["rate"]
    previous=np.zeros(4);count=core_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        expected=np.zeros((4,4))
        r168=np.log(close[t]/close[t-168]);r48=np.log(close[t]/close[t-48]);r24=np.log(close[t]/close[t-24])
        funding=np.array([sum(float(rate[t-k,j]) for k in range(0,161,8)) for j in range(4)])
        score=funding+.04*r168
        high=sorted(range(4),key=lambda j:(-score[j],j))[0]
        low=sorted(range(4),key=lambda j:(score[j],j))[0]
        if score[high]-score[low]>.004 and r168[high]-r168[low]>.025:
            expected[0,high]=-.30;expected[0,low]=+.30
        changed=not np.array_equal(previous,expected[0])
        if changed:core_count+=1
        previous=expected[0].copy()
        residual=r48-np.median(r48)
        j=sorted(range(4),key=lambda x:(-abs(residual[x]),x))[0]
        if abs(residual[j])>.07 and all(rate[t-k,j]*np.sign(residual[j])>0 for k in (0,8,16)):
            expected[1,j]=-.14*np.sign(residual[j])
        if abs(funding[0]-funding[1])>.0025 and abs(r168[0]-r168[1])<.20:
            high=0 if funding[0]>funding[1] else 1
            expected[2,high]=-.09;expected[2,1-high]=+.09
        if sum(r48<-.05)>=3 and r24[0]<-.04:expected[3,0]=-.16
        elif sum(r168<-.10)>=3 and r48[0]>.035:expected[3,0]=+.16
        bull=sum(r168>0)>=3;bear=sum(r168<0)>=3
        multipliers=(.7,.8,.5) if bull else ((1.,1.,1.) if bear else (1.,1.,.8))
        for k in (1,2,3):expected[k]*=multipliers[k-1]
        err=float(np.max(np.abs(expected-raw[t])));maxerr=max(maxerr,err)
        if err>1e-10 or not updates[t,1:].all() or bool(updates[t,0])!=changed:
            raise ValueError("OQ_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        count+=1
    if count!=105 or core_count!=int(updates[:,0].sum()):raise ValueError("OQ_SOURCE_ORACLE_COUNTS")
    return {"decision":"PASS_OQ_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":count,"core_state_transitions_reconstructed":core_count,
            "max_weight_error":maxerr,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
