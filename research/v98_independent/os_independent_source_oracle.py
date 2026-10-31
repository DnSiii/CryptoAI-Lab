#!/usr/bin/env python3
"""OS independent source oracle, reconstructs preregistered 105 signals without importing OS formulas."""
import argparse,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from od_sources import load_oi
from os_sources import bundle
def audit(d,oi):
    actual,updates,_,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")),oi)
    close=d["c"];high=d["h"];low=d["l"];volume=d["q"]
    logprice=np.log(close);last_core=np.zeros(4);count=core_count=0;maxerr=0.
    for t in range(WARMUP,HOURS,168):
        x=np.zeros((4,4))
        fortnight=logprice[t]-logprice[t-336]
        week=logprice[t]-logprice[t-168]
        three=logprice[t]-logprice[t-72]
        day=logprice[t]-logprice[t-24]
        changes=logprice[t-335:t+1]-logprice[t-336:t]
        annualized=np.sqrt(np.mean((changes-changes.mean(axis=0))**2,axis=0))*np.sqrt(336)
        adjusted=(fortnight-.65*fortnight[0]+.5*week)/np.maximum(annualized,.03)
        if fortnight[0]>0:
            ranks=sorted(range(4),key=lambda j:(-adjusted[j],j))
            for j,weight in zip(ranks[:2],(.30,.18)):
                if adjusted[j]>0:x[0,j]=weight
        elif fortnight[0]<0:
            ranks=sorted(range(4),key=lambda j:(adjusted[j],j))
            for j,weight in zip(ranks[:2],(-.24,-.14)):
                if adjusted[j]<0:x[0,j]=weight
        changed=not np.array_equal(last_core,x[0])
        if changed:core_count+=1
        last_core=x[0].copy()
        eligible=[]
        for j in range(4):
            a=np.log(np.max(high[t-335:t-167,j])/np.min(low[t-335:t-167,j]))
            b=np.log(np.max(high[t-167:t+1,j])/np.min(low[t-167:t+1,j]))
            old=sum(volume[t-47:t-23,j]);new=sum(volume[t-23:t+1,j])
            if b<.75*a and close[t,j]>np.max(high[t-168:t,j]) and new/max(old,1e-12)>1.1:
                eligible.append(j)
        if eligible:
            j=sorted(eligible,key=lambda k:(-day[k],k))[0]
            x[1,j]=.18
        residual=week-.65*week[0]
        rich=sorted(range(4),key=lambda j:(-residual[j],j))[0]
        cheap=sorted(range(4),key=lambda j:(residual[j],j))[0]
        if residual[rich]-residual[cheap]>.18 and day[rich]<0 and day[cheap]>0:
            x[2,cheap]=.10;x[2,rich]=-.10
        if sum(three<-.10)>=3:
            if day[0]>0:x[3,0]=.18
            elif day[0]<0:x[3,0]=-.18
        bull=sum(fortnight>0)>=3;bear=sum(fortnight<0)>=3
        factors=(1.,.8,.6) if bull else ((.5,1.,1.) if bear else (.75,.8,.8))
        for k in (1,2,3):x[k]*=factors[k-1]
        err=float(np.max(np.abs(x-actual[t])));maxerr=max(maxerr,err)
        if err>1e-10 or not updates[t,1:].all() or bool(updates[t,0])!=changed:
            raise ValueError("OS_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        count+=1
    if count!=105 or core_count!=int(updates[:,0].sum()):raise ValueError("OS_SOURCE_ORACLE_COUNTS")
    return {"decision":"PASS_OS_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "decisions_reconstructed":count,"core_state_transitions_reconstructed":core_count,
            "max_weight_error":maxerr,"training_only":True,"holdout_accessed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("root","oi-root","output"):p.add_argument("--"+a,required=True)
    a=p.parse_args();oi,_=load_oi(a.oi_root)
    result=audit(load(a.root),oi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
