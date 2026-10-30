#!/usr/bin/env python3
"""V98 NJ independent source-to-weights reconstruction; no physical runner imports."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from nj_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    c=d['c'];q=d['q'];p=np.log(c)
    weights=np.zeros((HOURS,4,4));activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool);held=np.zeros((4,4));multiplier=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%168==0:
            if np.any(q[t]<=0):raise ValueError('NJ_ORACLE_WEEK_VOLUME')
            ret={lag:np.log(c[t]/c[t-lag]) for lag in (24,72,168,336)}
            held[:]=0.
            best=sorted(range(4),key=lambda j:(-ret[336][j],j))[0]
            worst=sorted(range(4),key=lambda j:(ret[336][j],j))[0]
            selected=best if ret[336][best]>0 else worst
            held[0,selected]=.52 if ret[336][best]>0 else -.45
            others=[j for j in range(4) if j!=selected]
            longs=[j for j in others if ret[72][j]>0 and ret[168][j]>0]
            shorts=[j for j in others if ret[72][j]<0 and ret[168][j]<0]
            if longs:
                winner=sorted(longs,key=lambda j:(-ret[72][j],j))[0]
                held[1,winner]=.16
            elif shorts:
                loser=sorted(shorts,key=lambda j:(ret[72][j],j))[0]
                held[1,loser]=-.16
            residual={j:float(ret[24][j]-ret[24][0]) for j in (1,2,3)}
            lag=sorted((1,2,3),key=lambda j:(residual[j],j))[0]
            lead=sorted((1,2,3),key=lambda j:(-residual[j],j))[0]
            if lag!=lead and residual[lead]-residual[lag]>=.05 and (
                residual[lag]<-.025 or residual[lead]>.025):
                held[2,lag]=.07;held[2,lead]=-.07
            rr=np.log(c[t-407:t+1,0]/c[t-408:t,0])
            recent=np.sqrt(np.sum(rr[-72:]**2)/72)
            prior=np.sqrt(np.sum(rr[:-72]**2)/336)
            if recent>1.35*max(prior,1e-8) and abs(ret[72][0])>.035:
                if ret[24][0]<0:held[3,0]=-.12
                elif ret[24][0]>0:held[3,0]=.12
            constructive=sum(ret[168][j]>0 for j in range(4))>=3
            multiplier=np.array([1.,.75,.7] if constructive else [.75,1.,1.])
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
            forced[t]=True
        w=held.copy()
        for slot in (1,2,3):w[slot]*=multiplier[slot-1]
        room=.84-float(np.sum(np.abs(w[0])))
        optional=float(np.sum(np.abs(w[1:])))
        if room<0:raise ValueError('NJ_ORACLE_CORE_CAP')
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
    schedule=np.arange(WARMUP,HOURS,168)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
        for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('NJ_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NJ_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NJ_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NJ_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NJ_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NJ_MINIMUM_'+year+'_'+name)
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
