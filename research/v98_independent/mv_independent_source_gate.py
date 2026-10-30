#!/usr/bin/env python3
"""V98 MV independent source-only all-hour replay and distinct active-week gate."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mv_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    p=np.log(d['c'])
    changes=np.diff(p,axis=0,prepend=p[:1])
    weights=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inv=np.zeros((4,4))
    mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('MV_INDEPENDENT_CORE_NO_VOLUME')
            inv[0]=0.
            if np.log(d['c'][t,0]/d['c'][t-336,0])>0:
                inv[0,0]=.52;inv[0,1]=.16
            else:inv[0,0]=.42;inv[0,1]=.12
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('MV_INDEPENDENT_WEEK_NO_VOLUME')
            a=np.log(d['c'][t]/d['c'][t-168])
            b=np.log(d['c'][t]/d['c'][t-72])
            z=np.log(d['c'][t]/d['c'][t-24])
            inv[1:]=0.
            v=np.std(changes[t-167:t+1,2:4],axis=0)*np.sqrt(168.)
            scores=(a[2:4]-a[0])/np.maximum(v,.01)
            j=int(np.argmax(scores))+2
            if a[j]>0:inv[1,j]=.16
            spread=b[1:4]-b[0]
            hi=int(np.argmax(spread))+1
            lo=int(np.argmin(spread))+1
            if hi!=lo and spread.max()-spread.min()>.015:
                inv[2,hi]=.075;inv[2,lo]=-.060
            if a[0]<0:inv[3,0]=-.12
            elif b[0]<0 and z[0]>0:inv[3,0]=.10
            bullish=bool(np.log(d['c'][t,0]/d['c'][t-336,0])>0 and int(np.sum(a>0))>=2)
            mult=np.asarray([1.,.8,.6] if bullish else [.7,1.,1.])
            volratio=float(np.std(changes[t-71:t+1,0])/max(np.std(changes[t-335:t+1,0]),1e-8))
            if volratio>1.5:mult[0]*=.7;mult[2]=1.
            activity[t]=np.abs(inv[1:]).sum(axis=1)>1e-12
        w=inv.copy()
        w[1:]*=mult[:,None]
        room=.84-np.abs(w[0]).sum()
        optional=np.abs(w[1:]).sum()
        if optional>room and optional>0:w[1:]*=room/optional
        weights[t]=w
    return weights,activity,forced
def check(d):
    synthetic_causality()
    source=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    weights,activity,forced=replay(d)
    mismatch=int(np.count_nonzero(np.abs(source[0]-weights)>1e-10))
    activity_mismatch=int(np.count_nonzero(source[2]!=activity))
    silent=int(np.count_nonzero((np.abs(np.diff(source[0],axis=0)).sum(axis=2)>1e-12)&~source[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not source[1][t,0] or not forced[t]]
    counts={str(y):{name:int(source[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('MV_INDEPENDENT_REPLAY_MISMATCH')
    if silent:failures.append('MV_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('MV_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MV_FUNDING_COUNT')
    if np.max(np.sum(np.abs(source[0]),axis=(1,2)))>.84+1e-10:failures.append('MV_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MV_MINIMUM_'+y+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatch,
        'independent_active_week_mismatches':activity_mismatch,'silent_weight_updates':silent,
        'forced_core_refreshes':int(forced.sum()),'preregistered_core_refreshes':len(schedule),
        'missed_core_refresh_hours':missing,'native_funding_events':int(d['event'].sum()),
        'active_distinct_week_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
        'synthetic_future_mutation_pass':True,'training_only':True,
        'pnl_computed':False,'holdout_accessed':False}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
