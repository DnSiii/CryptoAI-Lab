#!/usr/bin/env python3
"""Independent NE signal oracle: reconstruct all hourly targets without importing NE physical executor."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from ne_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    close=d['c'];logs=np.log(close)
    returns=np.vstack((np.zeros((1,4)),np.diff(logs,axis=0)))
    weights=np.zeros((HOURS,4,4))
    active=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    held=np.zeros((4,4))
    multipliers=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('NE_ORACLE_CORE_VOLUME')
            trend336=np.log(close[t,0]/close[t-336,0])
            quality=[]
            for j in range(4):
                trend504=float(np.log(close[t,j]/close[t-504,j]))
                rms=float(np.sqrt(np.mean(returns[t-335:t+1,j]**2)))
                quality.append(trend504/max(rms,.001))
            held[0]=0.
            if trend336>0:
                held[0,0]=.36
                winner=max((1,2,3),key=lambda j:(quality[j],-j))
                held[0,winner]=.26
            else:
                held[0,0]=-.32
                loser=min((1,2,3),key=lambda j:(quality[j],j))
                held[0,loser]=-.26
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NE_ORACLE_WEEK_VOLUME')
            ret={}
            for lag in (24,72,168,336):
                ret[lag]=[float(np.log(close[t,j]/close[t-lag,j])) for j in range(4)]
            held[1:]=0.
            accel={j:ret[72][j]-(72./168.)*ret[168][j] for j in (1,2,3)}
            hi=max((1,2,3),key=lambda j:(accel[j],-j))
            lo=min((1,2,3),key=lambda j:(accel[j],j))
            if accel[hi]>0 and ret[168][hi]>0:held[1,hi]=.12
            elif accel[lo]<0 and ret[168][lo]<0:held[1,lo]=-.12
            settled=d['rate'][t-168:t:8]
            funding={j:float(np.mean(settled[:,j])) for j in (1,2,3)}
            cheap=min((1,2,3),key=lambda j:(funding[j],j))
            dear=max((1,2,3),key=lambda j:(funding[j],-j))
            if cheap!=dear and funding[dear]-funding[cheap]>=.000025:
                held[2,cheap]=.07
                held[2,dear]=-.07
            if ret[168][0]<0 and ret[24][0]>0:
                best=max((1,2,3),key=lambda j:(ret[24][j],-j))
                held[3,best]=.12
            elif ret[24][0]<0:
                fast=float(np.std(returns[t-71:t+1,0]))
                slow=float(np.std(returns[t-335:t+1,0]))
                if fast>1.15*max(slow,1e-8):
                    worst=min((1,2,3),key=lambda j:(ret[72][j],j))
                    held[3,worst]=-.12
            good=ret[336][0]>0 and sum(ret[168][j]>0 for j in range(4))>=2
            multipliers=np.array([1.,.85,.85] if good else [.75,1.,1.])
            active[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        w=held.copy()
        for k in (1,2,3):w[k]*=multipliers[k-1]
        optional=float(np.sum(np.abs(w[1:])))
        remaining=.84-float(np.sum(np.abs(w[0])))
        if remaining<0:raise ValueError('NE_ORACLE_CORE_CAP')
        if optional>remaining and optional>0:w[1:]*=remaining/optional
        weights[t]=w
    return weights,active,forced

def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    expected,activity,forced=replay(d)
    mismatch=int(np.count_nonzero(np.abs(original[0]-expected)>1e-9))
    activity_mismatch=int(np.count_nonzero(original[2]!=activity))
    silent=int(np.count_nonzero((np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
        for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('NE_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NE_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NE_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NE_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NE_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NE_MINIMUM_'+year+'_'+name)
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
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output')
    a=p.parse_args()
    result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
