#!/usr/bin/env python3
"""V98 NP independent 17,544h causal source reconstruction, no physical runner."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from np_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    close=d['c'];q=d['q'];rate=d['rate'];event=d['event']
    weights=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    held=np.zeros((4,4))
    multiplier=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%336==0:
            if np.any(q[t]<=0):raise ValueError('NP_ORACLE_CORE_VOLUME')
            slow=np.log(close[t]/close[t-672])
            medium=np.log(close[t]/close[t-336])
            held[0]=np.array([.17 if slow[j]>0 and medium[j]>0 else (.08 if slow[j]>0 else 0.) for j in range(4)])
            forced[t]=True
        if k%168==0:
            if np.any(q[t]<=0):raise ValueError('NP_ORACLE_WEEK_VOLUME')
            r24=np.log(close[t]/close[t-24])
            r168=np.log(close[t]/close[t-168])
            slow=np.log(close[t]/close[t-672])
            held[1:]=0.
            accel=r24-r168/7.
            best=sorted((1,2,3),key=lambda j:(-accel[j],j))[0]
            worst=sorted((1,2,3),key=lambda j:(accel[j],j))[0]
            if accel[best]>0:held[1,best]=.12
            else:held[1,worst]=-.12
            if t%8 or not np.all(event[t-160:t+1:8]):
                raise ValueError('NP_ORACLE_UNSETTLED_FUNDING')
            residual=r168-float(sum(r168)/4.)
            ranks=sorted(range(4),key=lambda j:(residual[j],j))
            held[2,ranks[0]]=.05
            held[2,ranks[-1]]=-.05
            breadth=sum(x>0 for x in r168)
            held[3,0]=-.12 if breadth<=1 else (.08 if breadth>=3 else 0.)
            multiplier=np.array([1.,.7,.8] if slow[0]>0 and breadth>=2
                                else [.65,.7,1.])
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        w=held.copy()
        for slot in (1,2,3):w[slot]*=multiplier[slot-1]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NP_ORACLE_CORE_CAP')
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
    if mismatch or activity_mismatch:failures.append('NP_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NP_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NP_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NP_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NP_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NP_MINIMUM_'+year+'_'+name)
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
