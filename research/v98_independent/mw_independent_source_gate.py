#!/usr/bin/env python3
"""V98 MW independent all-hour replay, no physical runner import."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mw_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    p=np.log(d['c'])
    delta=np.diff(p,axis=0,prepend=p[:1])
    weights=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inv=np.zeros((4,4))
    multipliers=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('MW_INDEPENDENT_CORE_NO_VOLUME')
            past=np.log(d['c'][t]/d['c'][t-336])
            vols=np.std(delta[t-335:t+1,1:4],axis=0)*np.sqrt(336.)
            candidate=int(np.argmax(past[1:4]/np.maximum(vols,.03)))+1
            inv[0]=0.
            if past[0]>0 and past[candidate]>0:
                inv[0,0]=.50;inv[0,candidate]=.18
            else:
                inv[0,0]=.46;inv[0,1]=.10
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('MW_INDEPENDENT_WEEK_NO_VOLUME')
            a=np.log(d['c'][t]/d['c'][t-168])
            b=np.log(d['c'][t]/d['c'][t-72])
            z=np.log(d['c'][t]/d['c'][t-24])
            inv[1:]=0.
            vv=np.std(delta[t-71:t+1,1:4],axis=0)*np.sqrt(72.)
            idx=int(np.argmax(b[1:4]/np.maximum(vv,.02)))+1
            lower=np.min(d['l'][t-167:t+1,idx])
            upper=np.max(d['h'][t-167:t+1,idx])
            if b[idx]>0 and (d['c'][t,idx]-lower)/max(upper-lower,1e-9)>=.70:
                inv[1,idx]=.12
            historical_funding=np.mean(d['rate'][t-160:t+1:8,1:4],axis=0)
            low=int(np.argmin(historical_funding))+1
            high=int(np.argmax(historical_funding))+1
            if a[low]>0:inv[2,low]=.08
            elif a[high]<0:inv[2,high]=-.07
            if int(np.sum(b<0))>=3:inv[3,1]=-.10
            elif a[0]<0 and z[0]>0:inv[3,0]=.08
            bullish=bool(np.log(d['c'][t,0]/d['c'][t-336,0])>0 and int(np.sum(a>0))>=2)
            multipliers=np.asarray([1.,1.,.7] if bullish else [.7,.9,1.])
            ratio=float(np.std(delta[t-71:t+1,0])/max(np.std(delta[t-335:t+1,0]),1e-8))
            if ratio>1.5:multipliers[0]*=.7;multipliers[2]=1.
            activity[t]=np.abs(inv[1:]).sum(axis=1)>1e-12
        w=inv.copy()
        w[1:]*=multipliers[:,None]
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
    if mismatch or activity_mismatch:failures.append('MW_INDEPENDENT_REPLAY_MISMATCH')
    if silent:failures.append('MW_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('MW_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MW_FUNDING_COUNT')
    if np.max(np.sum(np.abs(source[0]),axis=(1,2)))>.84+1e-10:failures.append('MW_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MW_MINIMUM_'+y+'_'+name)
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
