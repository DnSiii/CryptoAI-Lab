#!/usr/bin/env python3
"""V98 NK independent 17,544-hour source reconstruction; never imports physical runner."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from nk_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    close=d['c'];q=d['q'];weights=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool);forced=np.zeros(HOURS,bool)
    held=np.zeros((4,4));multiplier=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%336==0:
            if np.any(q[t]<=0):raise ValueError('NK_ORACLE_CORE_VOLUME')
            r336=np.log(close[t]/close[t-336]);r168=np.log(close[t]/close[t-168])
            topalt=sorted((1,2,3),key=lambda j:(-r336[j],j))[0]
            held[0]=0.
            if r336[0]>0 and sum(r168[j]>0 for j in (1,2,3))>=2:
                held[0,0]=.18;held[0,topalt]=.40
            elif r336[0]<0 and sum(r168[j]<0 for j in (1,2,3))>=2:
                held[0,0]=-.36
                if r336[topalt]>0:held[0,topalt]=.14
            else:
                best=sorted(range(4),key=lambda j:(-r336[j],j))[0]
                if r336[best]>0:held[0,best]=.38
                else:held[0,0]=-.35
            forced[t]=True
        if k%168==0:
            if np.any(q[t]<=0):raise ValueError('NK_ORACLE_WEEK_VOLUME')
            r72=np.log(close[t]/close[t-72]);r168=np.log(close[t]/close[t-168])
            r24=np.log(close[t]/close[t-24]);r336=np.log(close[t]/close[t-336])
            held[1:]=0.
            longs=[j for j in (1,2,3) if r72[j]>0 and r168[j]>0]
            shorts=[j for j in (1,2,3) if r72[j]<0 and r168[j]<0]
            if longs:held[1,sorted(longs,key=lambda j:(-r72[j],j))[0]]=.16
            elif shorts:held[1,sorted(shorts,key=lambda j:(r72[j],j))[0]]=-.16
            lag=sorted((1,2,3),key=lambda j:(r72[j],j))[0]
            lead=sorted((1,2,3),key=lambda j:(-r72[j],j))[0]
            if lag!=lead:held[2,lag]=.05;held[2,lead]=-.05
            if r168[0]<-.03:
                if r24[0]<0:held[3,0]=-.10
                elif r24[0]>0:held[3,0]=.10
            constructive=r336[0]>0 and sum(r168[j]>0 for j in (1,2,3))>=2
            multiplier=np.array([1.,.75,.65] if constructive else [.75,1.,1.])
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        w=held.copy()
        for slot in (1,2,3):w[slot]*=multiplier[slot-1]
        room=.84-float(np.sum(np.abs(w[0])))
        optional=float(np.sum(np.abs(w[1:])))
        if room<0:raise ValueError('NK_ORACLE_CORE_CAP')
        if optional>room and optional>0:w[1:]*=room/optional
        weights[t]=w
    return weights,activity,forced

def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    expected,activity,forced=replay(d)
    mismatch=int(np.count_nonzero(np.abs(original[0]-expected)>1e-9))
    activity_mismatch=int(np.count_nonzero(original[2]!=activity))
    silent=int(np.count_nonzero((np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]))
    schedule=np.arange(WARMUP,HOURS,336)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
        for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('NK_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NK_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NK_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NK_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NK_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NK_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatch,
        'independent_active_week_mismatches':activity_mismatch,'silent_weight_updates':silent,
        'forced_core_refreshes':int(forced.sum()),'preregistered_core_refreshes':len(schedule),
        'missed_core_refresh_hours':missing,'native_funding_events':int(d['event'].sum()),
        'active_distinct_week_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
        'synthetic_future_mutation_pass':True,'training_only':True,'pnl_computed':False,
        'holdout_accessed':False}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
