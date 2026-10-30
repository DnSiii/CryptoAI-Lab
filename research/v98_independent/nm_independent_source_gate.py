#!/usr/bin/env python3
"""Independent NM all-hour source reconstruction; never imports physical runner."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from nm_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    c=d['c']
    q=d['q']
    weights=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    held=np.zeros((4,4))
    multipliers=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%336==0:
            if np.any(q[t]<=0):raise ValueError('NM_ORACLE_CORE_VOLUME')
            r336=np.log(c[t]/c[t-336])
            r168=np.log(c[t]/c[t-168])
            if r336[0]>0 and sum(x>0 for x in r168)>=2:
                held[0]=[.30,.12,.08,.12]
            else:
                held[0]=[.20,.06,.04,.06]
            forced[t]=True
        if k%168==0:
            if np.any(q[t]<=0):raise ValueError('NM_ORACLE_WEEK_VOLUME')
            r24=np.log(c[t]/c[t-24])
            r72=np.log(c[t]/c[t-72])
            r168=np.log(c[t]/c[t-168])
            r336=np.log(c[t]/c[t-336])
            held[1:]=0.
            choices=[j for j in (1,2,3) if r72[j]>0 and r168[j]>0
                     and c[t,j]>max(c[t-72:t,j])]
            if choices:
                held[1,sorted(choices,key=lambda j:(-r72[j],j))[0]]=.12
            choices=[j for j in (1,2,3) if r336[j]-r336[0]>.03 and r168[j]>0]
            if choices:
                held[2,sorted(choices,key=lambda j:(-(r336[j]-r336[0]),j))[0]]=.10
            if c[t,0]/max(c[t-336:t+1,0])<=.94 and r24[0]>0 and r72[0]>0:
                held[3,0]=.12
            multipliers=np.array([1.,1.,.9] if r168[0]>0 and
                                 sum(x>0 for x in r168)>=2 else [.6,.6,1.])
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        w=held.copy()
        for slot in (1,2,3):
            w[slot]*=multipliers[slot-1]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NM_ORACLE_CORE_CAP')
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
    if mismatch or activity_mismatch:failures.append('NM_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NM_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NM_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NM_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NM_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NM_MINIMUM_'+year+'_'+name)
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
