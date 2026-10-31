#!/usr/bin/env python3
"""V98 OA independent 105-decision source oracle; no import of OA signal formulas."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oa_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    count=0
    for t in range(WARMUP,HOURS,168):
        target=np.zeros((4,4))
        def ret(j,k):
            return math.log(float(d['c'][t,j]/d['c'][t-k,j]))
        r336=[ret(j,336) for j in range(4)]
        r168=[ret(j,168) for j in range(4)]
        r72=[ret(j,72) for j in range(4)]
        r24=[ret(j,24) for j in range(4)]
        elig=[j for j in range(4) if r336[j]>0 and r168[j]>0]
        elig.sort(key=lambda j:(-r336[j],j))
        if elig:
            target[0,elig[0]]=.60
            if len(elig)>1:target[0,elig[1]]=.08
        elif r336[0]<0 and sum(z<0 for z in r168)>=3:
            target[0,0]=-.55
        up=[j for j in range(4) if r72[j]>.04 and r24[j]>.015]
        down=[j for j in range(4) if r72[j]<-.05 and r24[j]<-.025]
        if up:
            target[1,min(up,key=lambda j:(-r24[j],j))]=.16
        elif down:
            target[1,min(down,key=lambda j:(r24[j],j))]=-.16
        weak=min((1,2,3),key=lambda j:(r168[j],j))
        strong=min((1,2,3),key=lambda j:(-r168[j],j))
        if weak!=strong and r168[strong]-r168[weak]>.10 and r168[strong]>0:
            target[2,strong]=.09;target[2,weak]=-.09
        if r72[0]<-.05 and sum(z<0 for z in r168)>=3:
            target[3,0]=-.18
        elif r336[0]<-.08 and r72[0]<0 and r24[0]>.025:
            target[3,0]=.18
        risk_on=r336[0]>0 and sum(z>0 for z in r168)>=2
        target[1:]*=np.array([1.,1.,.45] if risk_on else [.8,.65,1.])[:,None]
        err=float(np.max(np.abs(raw[t]-target)))
        if err>1e-8 or not updates[t].all():
            raise ValueError('OA_INDEPENDENT_SOURCE_MISMATCH_'+str(t)+'_'+str(err))
        count+=1
    if count!=105 or int(updates[:,0].sum())!=105 or int(d['event'].sum())!=9144:
        raise ValueError('OA_INDEPENDENT_SOURCE_CALENDAR')
    return {'decision':'PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL','decisions':count,
            'source_hours':HOURS,'funding_events':9144,'raw_target_mismatches':0,
            '2025_validation_accessed':False,'future_holdout_accessed':False,
            'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
