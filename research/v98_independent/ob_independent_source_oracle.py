#!/usr/bin/env python3
"""V98 OB independent 53 optional/27 core two-clock source oracle."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from ob_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    held=np.zeros((4,4));checked=core_count=0
    for t in range(WARMUP,HOURS,336):
        def ret(j,k):return math.log(float(d['c'][t,j]/d['c'][t-k,j]))
        r672=[ret(j,672) for j in range(4)]
        r336=[ret(j,336) for j in range(4)]
        r168=[ret(j,168) for j in range(4)]
        r24=[ret(j,24) for j in range(4)]
        core_update=(t-WARMUP)%672==0
        if core_update:
            held[0]=0.
            eligible=[j for j in range(4) if r672[j]>0 and r168[j]>0]
            eligible.sort(key=lambda j:(-r672[j],j))
            if eligible:
                held[0,eligible[0]]=.60
                if len(eligible)>1:held[0,eligible[1]]=.10
            elif sum(x<0 for x in r336)>=3:
                held[0,0]=-.52
            core_count+=1
        held[1:]=0.
        means=[math.fsum(float(d['rate'][s,j]) for s in range(t-160,t+1,8))/21.
               for j in range(4)]
        volumes=[]
        for j in range(4):
            recent=math.fsum(float(d['q'][s,j]) for s in range(t-167,t+1))/168.
            prior=math.fsum(float(d['q'][s,j]) for s in range(t-335,t-167))/168.
            volumes.append(recent/max(prior,1e-12))
        longs=[j for j in range(4) if r168[j]>.06 and volumes[j]>1.15 and means[j]<.00005]
        shorts=[j for j in range(4) if r168[j]<-.07 and volumes[j]>1.15 and means[j]>.0001]
        if longs:
            held[1,min(longs,key=lambda j:(-r168[j]*volumes[j],j))]=.16
        elif shorts:
            held[1,min(shorts,key=lambda j:(r168[j]*volumes[j],j))]=-.16
        rel=[r336[j]-r336[0] for j in range(4)]
        med=sorted(means[1:])[1]
        strong=min((1,2,3),key=lambda j:(-rel[j],j))
        weak=min((1,2,3),key=lambda j:(rel[j],j))
        if strong!=weak and rel[strong]>0 and rel[weak]<0 and rel[strong]-rel[weak]>.10 and means[strong]<=med and means[weak]>=med:
            held[2,strong]=.10;held[2,weak]=-.10
        if r168[0]<-.08 and sum(x<0 for x in r168)>=3:
            held[3,0]=-.16
        elif r336[0]<-.10 and r24[0]>.02:
            held[3,0]=.16
        risk_on=r672[0]>0 and sum(x>0 for x in r168)>=3
        held[1:]*=np.array([1.,.75,.5] if risk_on else [.7,1.,1.])[:,None]
        error=float(np.max(np.abs(held-raw[t])))
        if error>1e-8 or not updates[t,1:].all() or bool(updates[t,0])!=core_update:
            raise ValueError('OB_SOURCE_ORACLE_MISMATCH_'+str(t)+'_'+str(error))
        checked+=1
    if checked!=53 or core_count!=27 or int(d['event'].sum())!=9144:
        raise ValueError('OB_SOURCE_ORACLE_COUNT')
    return {'decision':'PASS_OB_INDEPENDENT_TWO_CLOCK_SOURCE_NOT_PNL',
            'optional_decisions':checked,'core_decisions':core_count,
            'raw_target_mismatches':0,'funding_events':9144,
            'training_only':True,'holdout_accessed':False,'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
