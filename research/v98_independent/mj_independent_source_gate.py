#!/usr/bin/env python3
"""MJ independently reconstruct causal 7-slot source weights before ANY PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mj_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def independent(d):
    logpx=np.log(d['c'])
    out=np.zeros((HOURS,4,4))
    opened=np.zeros((HOURS,3),bool)
    scheduled=np.zeros(HOURS,bool)
    holdings=np.zeros((4,4))
    expires=[-1,-1,-1]
    breadth=0
    for hour in range(WARMUP,HOURS):
        k=hour-WARMUP
        quote_ok=bool((d['q'][hour]>0).all())
        r336=logpx[hour]-logpx[hour-336]
        r168=logpx[hour]-logpx[hour-168]
        r72=logpx[hour]-logpx[hour-72]
        r24=logpx[hour]-logpx[hour-24]
        cooling=[False]*3
        for sleeve in range(3):
            if expires[sleeve]>=0 and hour>=expires[sleeve]:
                holdings[sleeve+1,:]=0.
                expires[sleeve]=-1
                cooling[sleeve]=True
        if k%672==0:
            if not quote_ok:raise ValueError('MJ_INDEPENDENT_CORE_ZERO_QUOTE_'+str(hour))
            holdings[0,:]=[.66 if r336[0]>0 else .50,0.,0.,0.]
            scheduled[hour]=True
        if k%168==0:
            breadth=sum(x>0 for x in r168)
            if quote_ok and not cooling[0] and expires[0]<0 and r168[0]>0:
                leader=int(np.argmax(r336[1:]))+1
                if r336[leader]>0 and r72[leader]>0:
                    holdings[1,leader]=.14
                    expires[0]=hour+168
                    opened[hour,0]=True
            if quote_ok and not cooling[2] and expires[2]<0 and r168[0]<0 and r24[0]>0:
                holdings[3,0]=.08
                expires[2]=hour+168
                opened[hour,2]=True
        if k%336==0 and quote_ok and not cooling[1] and expires[1]<0:
            leader=int(np.argmax(r336[1:]))+1
            laggard=int(np.argmin(r336[1:]))+1
            if leader!=laggard and r336[leader]-r336[laggard]>.12 and r168[leader]>0:
                holdings[2,leader]=.055
                holdings[2,laggard]=-.055
                expires[1]=hour+336
                opened[hour,1]=True
        desired=holdings.copy()
        desired[1,:]*=(1. if breadth>=3 else .7)
        desired[2,:]*=(1. if breadth>=2 else .6)
        desired[3,:]*=(1.2 if breadth<=1 else .7)
        gross_core=float(np.abs(desired[0]).sum())
        gross_sleeves=float(np.abs(desired[1:]).sum())
        if gross_sleeves>0:
            desired[1:,:]*=min(1.,max(0.,(.88-gross_core)/gross_sleeves))
        out[hour]=desired
    return out,opened,scheduled
def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    independently,events,refresh=independent(d)
    werr=int(np.count_nonzero(np.abs(original[0]-independently)>1e-12))
    eerr=int(np.count_nonzero(original[2]!=events))
    change=(np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)
    silent=int(np.count_nonzero(change&~original[1][1:]))
    calendar=np.arange(WARMUP,HOURS,672)
    missed=[int(t) for t in calendar if not original[1][t,0] or not refresh[t]]
    zero_current=np.argwhere(np.any(d['q']==0,axis=1)).ravel().astype(int).tolist()
    counts={str(year):{name:int(original[2][start:end,i].sum())
        for i,name in enumerate(NAMES)}
        for year,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    bad=[]
    if werr or eerr:bad.append('MJ_INDEPENDENT_SIGNAL_MISMATCH')
    if silent:bad.append('MJ_SILENT_WEIGHT_CHANGE')
    if missed:bad.append('MJ_MISSING_FORCED_CORE_REFRESH')
    if int(d['event'].sum())!=9144:bad.append('MJ_FUNDING_EVENT_COUNT')
    if float(np.abs(original[0]).sum(axis=(1,2)).max())>.88+1e-10:bad.append('MJ_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:
                bad.append('MJ_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if bad else 'PASS_SOURCE_ONLY',
            'failures':bad,'independent_hourly_weight_mismatches':werr,
            'independent_entry_mismatches':eerr,'silent_weight_updates':silent,
            'forced_core_refreshes':int(refresh.sum()),
            'preregistered_core_refreshes':len(calendar),
            'missed_core_refresh_hours':missed,'zero_quote_hours':zero_current,
            'native_funding_events':int(d['event'].sum()),
            'entry_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
            'training_only':True,'pnl_computed':False,'holdout_accessed':False,
            'synthetic_future_mutation_pass':True}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output')
    a=p.parse_args()
    result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
