#!/usr/bin/env python3
"""Independent V98 NU source-only math, 27 decisions; not a PnL oracle."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nu_sources import bundle
def check(d):
    raw,updates,active=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    checked=0
    for t in range(WARMUP,HOURS,672):
        target=np.zeros((4,4))
        def lr(j,k):return math.log(float(d['c'][t,j]/d['c'][t-k,j]))
        r672=[lr(j,672) for j in range(4)]
        r336=[lr(j,336) for j in range(4)]
        r168=[lr(j,168) for j in range(4)]
        r48=[lr(j,48) for j in range(4)]
        score=[]
        for j in range(4):
            r=[math.log(float(d['c'][i,j]/d['c'][i-1,j])) for i in range(t-167,t+1)]
            m=sum(r)/len(r)
            sd=math.sqrt(sum((x-m)**2 for x in r)/len(r))
            score.append(max(r672[j],0.)/max(sd,.001))
        ranking=sorted(range(4),key=lambda j:(-score[j],j))
        if score[ranking[0]]>0:
            target[0,ranking[0]]=.62
            if score[ranking[1]]>0:target[0,ranking[1]]=.18
        elif r672[0]<-.10:target[0,0]=-.35
        rates=[sum(float(d['rate'][k,j]) for k in range(t-160,t+1,8))/21. for j in range(4)]
        mid=sorted(rates)
        median=(mid[1]+mid[2])/2.
        eligible=[j for j in range(4) if r168[j]>0 and rates[j]<median]
        if eligible:
            j=min(eligible,key=lambda k:(-r168[k],k))
            target[1,j]=.14
        low=min(range(4),key=lambda j:(rates[j],j))
        high=min(range(4),key=lambda j:(-rates[j],j))
        if rates[high]-rates[low]>=.00008:
            target[2,low]=.10;target[2,high]=-.10
        if sum(x>0 for x in r336)<=1 and r168[0]<0:
            target[3,0]=-.12
        elif r336[0]<-.06 and r48[0]>0:
            target[3,0]=.12
        risk_on=r672[0]>0 and sum(x>0 for x in r672)>=3
        target[1:]*=np.array([1.,.8,.5] if risk_on else [.75,1.,1.])[:,None]
        err=float(np.max(np.abs(raw[t]-target)))
        if err>1e-10 or not updates[t].all():
            raise ValueError('NU_INDEPENDENT_SOURCE_MISMATCH_'+str(t)+'_'+str(err))
        checked+=1
    if checked!=27 or int(updates[:,0].sum())!=27 or int(d['event'].sum())!=9144:
        raise ValueError('NU_INDEPENDENT_SOURCE_CALENDAR')
    if np.any((np.abs(np.diff(raw,axis=0)).sum(axis=(1,2))>1e-12)&~updates[1:,0]):
        raise ValueError('NU_INDEPENDENT_SOURCE_SILENT_CHANGE')
    return {'decision':'PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL','decisions':checked,
            'source_hours':HOURS,'funding_events':9144,'raw_target_mismatches':0,
            '2025_validation_accessed':False,'future_holdout_accessed':False,
            'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
