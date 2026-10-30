#!/usr/bin/env python3
"""V98 NG independent 17,544-hour source oracle; no physical-runner import."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from ng_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    close=d['c'];logs=np.log(close)
    returns=np.vstack((np.zeros((1,4)),np.diff(logs,axis=0)))
    weights=np.zeros((HOURS,4,4));activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool);held=np.zeros((4,4));multiplier=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('NG_ORACLE_CORE_VOLUME')
            trend={j:float(np.log(close[t,j]/close[t-504,j])) for j in range(4)}
            quality={}
            for j in range(4):
                downside=float(np.sqrt(np.mean(np.minimum(returns[t-335:t+1,j],0)**2)))
                quality[j]=trend[j]/max(downside,.001)
            ranked=sorted(range(4),key=lambda j:(-quality[j],j))
            held[0]=0.
            if trend[ranked[0]]>0:held[0,ranked[0]]=.42
            if trend[ranked[0]]>0 and trend[ranked[1]]>0:
                held[0,ranked[1]]=.22
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NG_ORACLE_WEEK_VOLUME')
            ret={}
            for lag in (24,72,168,504):
                ret[lag]={j:float(np.log(close[t,j]/close[t-lag,j])) for j in range(4)}
            held[1:]=0.
            eligible=[]
            for j in range(4):
                fast=float(np.std(returns[t-71:t+1,j]))
                slow=float(np.std(returns[t-335:t+1,j]))
                if ret[168][j]>.05 and ret[24][j]>0 and fast<.90*max(slow,1e-8):
                    eligible.append(j)
            if eligible:
                winner=max(eligible,key=lambda j:(ret[168][j],-j))
                held[1,winner]=.14
            means={j:float(np.mean(d['rate'][t-168:t:8,j])) for j in (1,2,3)}
            cheap=min((1,2,3),key=lambda j:(means[j],j))
            dear=max((1,2,3),key=lambda j:(means[j],-j))
            if cheap!=dear and means[dear]-means[cheap]>=.00003:
                held[2,cheap]=.06;held[2,dear]=-.06
            btc_carry=float(np.mean(d['rate'][t-168:t:8,0]))
            if ret[72][0]<-.03 and btc_carry>0:
                held[3,0]=-.12
            elif ret[72][0]<-.03 and ret[24][0]>0 and btc_carry<=0:
                held[3,0]=.12
            good=sum(ret[504][j]>0 for j in range(4))>=2 and ret[168][0]>0
            multiplier=np.array([1.,.8,.7] if good else [.7,1.,1.])
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        w=held.copy()
        for slot in (1,2,3):w[slot]*=multiplier[slot-1]
        room=.84-float(np.sum(np.abs(w[0])))
        optional=float(np.sum(np.abs(w[1:])))
        if room<0:raise ValueError('NG_ORACLE_CORE_CAP')
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
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
        for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('NG_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NG_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NG_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NG_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NG_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NG_MINIMUM_'+year+'_'+name)
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
    p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
