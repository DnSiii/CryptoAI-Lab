#!/usr/bin/env python3
"""V98 NX independent source recomputation, without imported source indicators."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nx_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    checked=0
    for t in range(WARMUP,HOURS,336):
        target=np.zeros((4,4))
        def ret(j,k):return math.log(float(d['c'][t,j]/d['c'][t-k,j]))
        r336=[ret(j,336) for j in range(4)]
        r168=[ret(j,168) for j in range(4)]
        r72=[ret(j,72) for j in range(4)]
        r24=[ret(j,24) for j in range(4)]
        risk_on=r336[0]>0 and sum(x>0 for x in r168)>=2
        if risk_on:
            target[0,0]=.62
            top=min((1,2,3),key=lambda j:(-r168[j],j))
            if r168[top]>0:target[0,top]=.18
        else:
            target[0,0]=-.62
            bottom=min((1,2,3),key=lambda j:(r168[j],j))
            if r168[bottom]<0:target[0,bottom]=-.12
        j=min(range(4),key=lambda k:(-abs(r24[k]),k))
        if abs(r24[j])>.025 and r24[j]*r72[j]>0:
            target[1,j]=.18 if r24[j]>0 else -.18
        means=[math.fsum(float(d['rate'][i,j]) for i in range(t-160,t+1,8))/21 for j in range(4)]
        low=min(range(4),key=lambda k:(means[k],k))
        high=min(range(4),key=lambda k:(-means[k],k))
        if low!=high and means[high]-means[low]>.00001:
            target[2,low]=.12;target[2,high]=-.12
        if r168[0]<0 and r24[0]<0:target[3,0]=-.18
        elif r168[0]<0 and r24[0]>0:target[3,0]=.12
        elif r168[0]>=0 and r24[0]<-.04:target[3,0]=-.18
        target[1:]*=np.array([1.,.7,.4] if risk_on else [.8,1.,1.])[:,None]
        err=float(np.max(np.abs(raw[t]-target)))
        if err>1e-9 or not updates[t].all():
            raise ValueError('NX_INDEPENDENT_SOURCE_MISMATCH_'+str(t)+'_'+str(err))
        checked+=1
    if checked!=53 or int(updates[:,0].sum())!=53 or int(d['event'].sum())!=9144:
        raise ValueError('NX_INDEPENDENT_SOURCE_CALENDAR')
    return {'decision':'PASS_INDEPENDENT_SOURCE_ONLY_NOT_PNL','decisions':checked,
            'source_hours':HOURS,'funding_events':9144,'raw_target_mismatches':0,
            '2025_validation_accessed':False,'future_holdout_accessed':False,'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
