#!/usr/bin/env python3
"""V98 NB independent signal replay, source-only pre-PnL fail-fast."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from nb_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    p=np.log(d['c']);r=np.diff(p,axis=0,prepend=p[:1])
    out=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    positions=np.zeros((4,4))
    factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('NB_INDEPENDENT_CORE_ZERO_QUOTE')
            trend504=np.log(d['c'][t]/d['c'][t-504])
            trend168=np.log(d['c'][t]/d['c'][t-168])
            positions[0]=0
            if trend504[0]>0 and sum(trend168[j]>0 for j in (1,2,3))>=2:
                leader=1+int(np.argmax(trend504[1:]))
                positions[0,0]=.48
                positions[0,leader]=.22
            else:
                calm=1+int(np.argmin(np.std(r[t-167:t+1,1:],axis=0)))
                positions[0,0]=-.32
                positions[0,calm]=.12
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NB_INDEPENDENT_WEEK_ZERO_QUOTE')
            trend504=np.log(d['c'][t]/d['c'][t-504])
            trend168=np.log(d['c'][t]/d['c'][t-168])
            trend72=np.log(d['c'][t]/d['c'][t-72])
            positions[1:]=0
            scores={j:float(trend72[j]/72.-trend168[j]/168.) for j in (1,2,3)}
            if trend168[0]>0:
                allowed=[j for j in (1,2,3) if trend72[j]>0 and scores[j]>0]
                if allowed:positions[1,max(allowed,key=lambda j:(scores[j],-j))]=.14
            elif trend168[0]<0:
                allowed=[j for j in (1,2,3) if trend72[j]<0 and scores[j]<0]
                if allowed:positions[1,min(allowed,key=lambda j:(scores[j],j))]=-.14
            velocity=[]
            for j in (1,2,3):
                new=float(np.mean(d['rate'][t-48:t+1:8,j]))
                old=float(np.mean(d['rate'][t-104:t-55:8,j]))
                velocity.append(new-old)
            low=1+int(np.argmin(velocity))
            high=1+int(np.argmax(velocity))
            if low!=high and max(velocity)-min(velocity)>.00001:
                positions[2,low]=.07
                positions[2,high]=-.07
            short=np.std(r[t-71:t+1,0])
            long=np.std(r[t-335:t+1,0])
            vr=float(short/max(long,1e-8))
            if vr>1.20:
                if trend72[0]<0:positions[3,0]=-.12
                elif trend72[0]>0:positions[3,0]=.12
            bull=trend504[0]>0 and sum(trend168[j]>0 for j in (1,2,3))>=2
            factors=np.array([1.,.85,.70] if bull else [.80,1.,1.])
            if vr>1.5:factors[0]*=.5;factors[2]=1.
            activity[t]=np.abs(positions[1:]).sum(axis=1)>1e-12
        w=positions.copy()
        for s in (1,2,3):w[s]*=factors[s-1]
        remaining=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if remaining<0:raise ValueError('NB_INDEPENDENT_CORE_GROSS')
        if optional>remaining and optional>0:w[1:]*=remaining/optional
        out[t]=w
    return out,activity,forced
def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    independent,active,forced=replay(d)
    mismatches=int(np.count_nonzero(np.abs(original[0]-independent)>1e-10))
    active_mismatches=int(np.count_nonzero(original[2]!=active))
    silent=int(np.count_nonzero(
        (np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatches or active_mismatches:failures.append('NB_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NB_SILENT_UPDATE')
    if missing:failures.append('NB_MISSING_CORE_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NB_NATIVE_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:
        failures.append('NB_TARGET_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('NB_MINIMUM_'+y+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatches,
        'independent_active_week_mismatches':active_mismatches,
        'silent_weight_updates':silent,'forced_core_refreshes':int(forced.sum()),
        'preregistered_core_refreshes':len(schedule),'missed_core_refresh_hours':missing,
        'native_funding_events':int(d['event'].sum()),'active_distinct_week_counts':counts,
        'minimums':dict(zip(NAMES,MINIMUM)),'synthetic_future_mutation_pass':True,
        'training_only':True,'pnl_computed':False,'holdout_accessed':False}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args()
    result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
