#!/usr/bin/env python3
"""V98 NI independent 17,544-hour source reconstruction; never imports physical runner."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from ni_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    close=d['c'];q=d['q'];logc=np.log(close)
    weights=np.zeros((HOURS,4,4));activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool);held=np.zeros((4,4));multiplier=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%336==0:
            if np.any(q[t]<=0):raise ValueError('NI_ORACLE_CORE_VOLUME')
            ret336=np.log(close[t]/close[t-336])
            ret168=np.log(close[t]/close[t-168])
            hourly=logc[t-167:t+1]-logc[t-168:t]
            rms=np.sqrt(np.sum(hourly**2,axis=0)/168)
            score=np.where(ret336>0,ret336/np.maximum(rms,.001),-np.inf)
            ranked=sorted(range(4),key=lambda j:(-score[j],j))
            held[0]=0.
            positive=[j for j in ranked if ret336[j]>0]
            if positive:
                held[0,positive[0]]=.32
                if len(positive)>1:held[0,positive[1]]=.22
            elif ret168[0]<0:held[0,0]=-.30
            forced[t]=True
        if k%168==0:
            if np.any(q[t]<=0):raise ValueError('NI_ORACLE_WEEK_VOLUME')
            ret168=np.log(close[t]/close[t-168])
            ret72=np.log(close[t]/close[t-72])
            ret24=np.log(close[t]/close[t-24])
            ret336=np.log(close[t]/close[t-336])
            held[1:]=0.
            recent=np.sum(q[t-23:t+1],axis=0)/24.
            older=np.sum(q[t-167:t-23],axis=0)/144.
            good=[j for j in (1,2,3) if ret168[j]>0 and ret24[j]>0 and recent[j]>older[j]]
            if good:
                winner=sorted(good,key=lambda j:(-ret72[j],j))[0]
                held[1,winner]=.14
            order=sorted((1,2,3),key=lambda j:(ret168[j],j))
            laggard=order[0];leader=sorted((1,2,3),key=lambda j:(-ret168[j],j))[0]
            if leader!=laggard and ret168[leader]-ret168[laggard]>=.07 and ret168[0]>0:
                held[2,laggard]=.07;held[2,leader]=-.07
            if ret168[0]<-.05 and sum(ret168[j]<0 for j in (1,2,3))>=2:
                if ret24[0]<=0:
                    worst=order[0];held[3,worst]=-.12
                else:
                    rebound=sorted((1,2,3),key=lambda j:(-ret24[j],j))[0]
                    held[3,rebound]=.12
            constructive=ret336[0]>0 and sum(ret168[j]>0 for j in (1,2,3))>=2
            multiplier=np.array([1.,.75,.75] if constructive else [.7,1.,1.])
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        w=held.copy()
        for slot in (1,2,3):w[slot]*=multiplier[slot-1]
        room=.84-float(np.sum(np.abs(w[0])))
        optional=float(np.sum(np.abs(w[1:])))
        if room<0:raise ValueError('NI_ORACLE_CORE_CAP')
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
    if mismatch or activity_mismatch:failures.append('NI_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NI_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NI_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NI_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('NI_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NI_MINIMUM_'+year+'_'+name)
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
