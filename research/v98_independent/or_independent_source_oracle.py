#!/usr/bin/env python3
"""Independent OR seven-slot signal reconstruction; no OR signal helper in oracle logic."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from or_sources import bundle
def audit(d,oi):
    actual,updates,_,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    c=d["c"];q=d["q"];rate=d["rate"]
    p=np.log(c)
    previous=np.zeros(4);count=core_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        x=np.zeros((4,4))
        slow=p[t]-p[t-672];weekly=p[t]-p[t-168]
        three=p[t]-p[t-72];prior_three=p[t-72]-p[t-144]
        two=p[t]-p[t-48];day=p[t]-p[t-24]
        native=np.array([sum(float(rate[t-k,j]) for k in range(0,161,8)) for j in range(4)])
        quality=slow+.5*weekly-2*np.maximum(native,0)
        leaders=sorted(range(4),key=lambda j:(-quality[j],j))
        if quality[leaders[0]]>0:x[0,leaders[0]]=.38
        if quality[leaders[1]]>0:x[0,leaders[1]]=.22
        changed=not np.array_equal(previous,x[0])
        if changed:core_count+=1
        previous=x[0].copy()
        candidates=[]
        for j in range(4):
            old=float(np.sum(q[t-47:t-23,j]))
            now=float(np.sum(q[t-23:t+1,j]))
            if three[j]>.08 and three[j]-prior_three[j]>.04 and now/max(old,1e-12)>1.2:
                candidates.append(j)
        if candidates:
            best=sorted(candidates,key=lambda j:(-three[j],j))[0]
            x[1,best]=.16
        hi=sorted(range(4),key=lambda j:(-weekly[j],j))[0]
        lo=sorted(range(4),key=lambda j:(weekly[j],j))[0]
        if weekly[hi]-weekly[lo]>.15 and weekly[lo]<0:
            x[2,hi]=.09;x[2,lo]=-.09
        if sum(two<-.08)>=3 and day[0]>0:x[3,0]=.16
        elif sum(two<-.12)>=3 and day[0]<0:x[3,0]=-.16
        bull=sum(weekly>0)>=3;bear=sum(weekly<0)>=3
        factors=(1.,.8,.5) if bull else ((.6,1.,1.) if bear else (.8,.8,.8))
        for k in (1,2,3):x[k]*=factors[k-1]
        err=float(np.max(np.abs(x-actual[t])));maxerr=max(maxerr,err)
        if err>1e-10 or not updates[t,1:].all() or bool(updates[t,0])!=changed:
            raise ValueError("OR_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        count+=1
    if count!=105 or core_count!=int(updates[:,0].sum()):
        raise ValueError("OR_SOURCE_ORACLE_COUNTS")
    return {"decision":"PASS_OR_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":count,"core_state_transitions_reconstructed":core_count,
            "max_weight_error":maxerr,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
