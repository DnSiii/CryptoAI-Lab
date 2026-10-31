#!/usr/bin/env python3
"""NZ independent source-only 53 decision oracle; no importing source signal formulas."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nz_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")))
    checked=0
    for t in range(WARMUP,HOURS,336):
        target=np.zeros((4,4))
        def ret(j,k):return math.log(float(d["c"][t,j]/d["c"][t-k,j]))
        r336=[ret(j,336) for j in range(4)]
        r168=[ret(j,168) for j in range(4)]
        r84=[ret(j,84) for j in range(4)]
        r48=[ret(j,48) for j in range(4)]
        r24=[ret(j,24) for j in range(4)]
        elig=[j for j in range(4) if r336[j]>0 and r84[j]>0]
        elig.sort(key=lambda j:(-r336[j],j))
        if elig:
            target[0,elig[0]]=.58
            if len(elig)>1:target[0,elig[1]]=.18
        elif sum(x<0 for x in r336)>=3:target[0,0]=-.55
        vol=[]
        for j in range(4):
            recent=math.fsum(float(d["q"][i,j]) for i in range(t-47,t+1))/48
            prior=math.fsum(float(d["q"][i,j]) for i in range(t-335,t-47))/288
            vol.append(recent/max(prior,1e-12))
        opp=[j for j in range(4) if r48[j]>.025 and r24[j]>.005 and vol[j]>1.35]
        if opp:
            j=min(opp,key=lambda k:(-r48[k]*vol[k],k))
            target[1,j]=.16
        weak=min((1,2,3),key=lambda j:(r336[j],j))
        strong=min((1,2,3),key=lambda j:(-r336[j],j))
        if weak!=strong and r336[strong]-r336[weak]>.12:
            target[2,weak]=.11;target[2,strong]=-.11
        if sum(x<0 for x in r168)>=3:
            if r24[0]<-.03:target[3,0]=-.14
            elif r24[0]>.015 and r168[0]<-.04:target[3,0]=.14
        risk_on=r336[0]>0 and sum(x>0 for x in r168)>=2
        target[1:]*=np.array([1.,.65,.55] if risk_on else [.70,1.,1.])[:,None]
        err=float(np.max(np.abs(raw[t]-target)))
        if err>1e-8 or not updates[t].all():
            raise ValueError("NZ_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        checked+=1
    if checked!=53 or int(updates[:,0].sum())!=53 or int(d["event"].sum())!=9144:
        raise ValueError("NZ_INDEPENDENT_SOURCE_CALENDAR")
    return {"decision":"PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL","decisions":checked,
            "source_hours":HOURS,"funding_events":9144,"raw_target_mismatches":0,
            "2025_validation_accessed":False,"future_holdout_accessed":False,
            "live_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
