#!/usr/bin/env python3
"""V98 NV independent source math: recompute raw decisions without reusing source indicators."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nv_sources import bundle
def check(d):
    raw,updates,active=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    checked=0
    for t in range(WARMUP,HOURS,336):
        target=np.zeros((4,4))
        def lr(j,k):return math.log(float(d['c'][t,j]/d['c'][t-k,j]))
        r504=[lr(j,504) for j in range(4)]
        r168=[lr(j,168) for j in range(4)]
        r72=[lr(j,72) for j in range(4)]
        r24=[lr(j,24) for j in range(4)]
        mean_close=[sum(float(d['c'][i,j]) for i in range(t-167,t+1))/168. for j in range(4)]
        eligible=[j for j in range(4) if r504[j]>0 and r168[j]>0 and float(d['c'][t,j])>mean_close[j]]
        ranked=sorted(eligible,key=lambda j:(-r504[j],j))
        if ranked:
            target[0,ranked[0]]=.72
            if len(ranked)>1:target[0,ranked[1]]=.08
        elif r168[0]<-.08:target[0,0]=-.28
        ratio=[]
        for j in range(4):
            recent=sum(float(d['q'][i,j]) for i in range(t-23,t+1))/24.
            prior=sum(float(d['q'][i,j]) for i in range(t-191,t-23))/168.
            ratio.append(recent/max(prior,1e-12))
        eligible=[j for j in range(4) if r72[j]>0 and r24[j]>0 and ratio[j]>1.05]
        if eligible:
            k=min(eligible,key=lambda j:(-r24[j]*ratio[j],j))
            target[1,k]=.14
        high=min(range(4),key=lambda j:(-ratio[j],j))
        low=min(range(4),key=lambda j:(ratio[j],j))
        if ratio[high]-ratio[low]>=.20:
            target[2,high]=.10;target[2,low]=-.10
        vtotal=sum(float(d['q'][i,0]) for i in range(t-71,t+1))
        vdown=sum(float(d['q'][i,0]) for i in range(t-71,t+1)
                  if float(d['c'][i,0])<float(d['o'][i,0]))
        down=vdown/vtotal if vtotal>0 else .5
        if down>.65 and r72[0]<-.07:target[3,0]=-.14
        elif down<.40 and r168[0]<-.10 and r24[0]>0:target[3,0]=.14
        risk_on=r168[0]>0 and sum(x>0 for x in r168)>=3
        target[1:]*=np.array([1.,.8,.5] if risk_on else [.75,.8,1.])[:,None]
        error=float(np.max(np.abs(raw[t]-target)))
        if error>1e-10 or not updates[t].all():
            raise ValueError('NV_INDEPENDENT_SOURCE_MISMATCH_'+str(t)+'_'+str(error))
        checked+=1
    if checked!=53 or int(updates[:,0].sum())!=53 or int(d['event'].sum())!=9144:
        raise ValueError('NV_INDEPENDENT_SOURCE_CALENDAR')
    if np.any((np.abs(np.diff(raw,axis=0)).sum(axis=(1,2))>1e-12)&~updates[1:,0]):
        raise ValueError('NV_INDEPENDENT_SOURCE_SILENT_CHANGE')
    return {'decision':'PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL','decisions':checked,
            'source_hours':HOURS,'funding_events':9144,'raw_target_mismatches':0,
            '2025_validation_accessed':False,'future_holdout_accessed':False,'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
