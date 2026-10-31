#!/usr/bin/env python3
"""V98 NY independent source oracle: recompute all 53 targets without importing NY signal math."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from ny_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")))
    checked=0
    for t in range(WARMUP,HOURS,336):
        target=np.zeros((4,4))
        def ret(j,k):return math.log(float(d["c"][t,j]/d["c"][t-k,j]))
        r504=[ret(j,504) for j in range(4)]
        r336=[ret(j,336) for j in range(4)]
        r168=[ret(j,168) for j in range(4)]
        r72=[ret(j,72) for j in range(4)]
        r24=[ret(j,24) for j in range(4)]
        downside=[]
        for j in range(4):
            series=[math.log(float(d["c"][i,j]/d["c"][i-1,j])) for i in range(t-503,t+1)]
            downside.append(math.sqrt(math.fsum(min(x,0.)**2 for x in series)/504))
        good=[j for j in range(4) if r504[j]>0 and r168[j]>0]
        good.sort(key=lambda j:(-r504[j]/max(downside[j],.001),j))
        if good:
            target[0,good[0]]=.72
            if len(good)>1:target[0,good[1]]=.08
        elif sum(x<0 for x in r168)>=3:target[0,0]=-.58
        expansion=[]
        for j in range(4):
            recent=math.fsum((float(d["h"][i,j])-float(d["l"][i,j]))/float(d["c"][i,j])
                             for i in range(t-23,t+1))/24
            prior=math.fsum((float(d["h"][i,j])-float(d["l"][i,j]))/float(d["c"][i,j])
                            for i in range(t-191,t-23))/168
            expansion.append(recent/max(prior,1e-12))
        opp=[j for j in range(4) if r24[j]>.03 and r72[j]>.05 and expansion[j]>1.15]
        if opp:
            j=min(opp,key=lambda k:(-r24[k]/expansion[k],k))
            target[1,j]=.18
        channel={}
        for j in (1,2,3):
            hi=max(float(d["h"][i,j]) for i in range(t-167,t+1))
            lo=min(float(d["l"][i,j]) for i in range(t-167,t+1))
            channel[j]=(float(d["c"][t,j])-lo)/max(hi-lo,1e-12)
        low=min((1,2,3),key=lambda j:(channel[j],j))
        high=min((1,2,3),key=lambda j:(-channel[j],j))
        if low!=high and channel[high]-channel[low]>.40:
            target[2,low]=.12;target[2,high]=-.12
        btc=[math.log(float(d["c"][i,0]/d["c"][i-1,0])) for i in range(t-167,t+1)]
        down=math.sqrt(math.fsum(min(x,0.)**2 for x in btc)/168)
        up=math.sqrt(math.fsum(max(x,0.)**2 for x in btc)/168)
        if down/max(up,.001)>1.50 and r168[0]<-.04:
            if r24[0]>.01:target[3,0]=.18
            elif r24[0]<-.04:target[3,0]=-.18
        risk_on=r336[0]>0 and sum(x>0 for x in r168)>=3
        target[1:]*=np.array([1.,.7,.5] if risk_on else [.75,1.,1.])[:,None]
        err=float(np.max(np.abs(raw[t]-target)))
        if err>1e-8 or not updates[t].all():
            raise ValueError("NY_INDEPENDENT_SOURCE_MISMATCH_"+str(t)+"_"+str(err))
        checked+=1
    if checked!=53 or int(updates[:,0].sum())!=53 or int(d["event"].sum())!=9144:
        raise ValueError("NY_INDEPENDENT_SOURCE_CALENDAR")
    return {"decision":"PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL","decisions":checked,
            "source_hours":HOURS,"funding_events":9144,"raw_target_mismatches":0,
            "2025_validation_accessed":False,"future_holdout_accessed":False,
            "live_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
