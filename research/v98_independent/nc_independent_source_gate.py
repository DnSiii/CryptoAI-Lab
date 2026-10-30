#!/usr/bin/env python3
"""V98 NC independent source-only full-history replay, no PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from nc_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    p=np.log(d['c']);r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4));active=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool);held=np.zeros((4,4));factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('NC_INDEPENDENT_CORE_NO_VOLUME')
            trend336=np.log(d['c'][t]/d['c'][t-336])
            order=np.argsort(-trend336,kind='stable')
            held[0]=0
            if sum(trend336[j]>0 for j in range(4))>=2:
                held[0,int(order[0])]=.48;held[0,int(order[1])]=.18
            else:
                held[0,0]=.32;held[0,1]=.08
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NC_INDEPENDENT_WEEK_NO_VOLUME')
            trend336=np.log(d['c'][t]/d['c'][t-336])
            trend168=np.log(d['c'][t]/d['c'][t-168])
            trend72=np.log(d['c'][t]/d['c'][t-72])
            trend24=np.log(d['c'][t]/d['c'][t-24])
            held[1:]=0
            efficiency={}
            for j in (1,2,3):
                travel=float(np.sum(np.abs(r[t-71:t+1,j])))
                efficiency[j]=abs(float(trend72[j]))/max(travel,1e-10)
            eligible=[j for j in (1,2,3) if
                      trend168[j]>0 and trend72[j]>0 and efficiency[j]>.16]
            if eligible:
                best=max(eligible,key=lambda j:(efficiency[j],-j))
                held[1,best]=.12
            btc=r[t-335:t+1,0]
            meanbtc=float(np.mean(btc))
            var=max(float(np.mean((btc-meanbtc)**2)),1e-12)
            residual=[]
            for j in (1,2,3):
                y=r[t-335:t+1,j]
                cov=float(np.mean((btc-meanbtc)*(y-np.mean(y))))
                b=float(np.clip(cov/var,0.,3.))
                residual.append(float(trend168[j]-b*trend168[0]))
            richest=1+int(np.argmax(residual))
            poorest=1+int(np.argmin(residual))
            if richest!=poorest and max(residual)-min(residual)>.030:
                held[2,richest]=.06;held[2,poorest]=-.06
            negatives=sum(trend72[j]<0 for j in range(4))
            if negatives>=2 and trend72[0]<0:
                held[3,0]=-.12
            elif negatives>=2 and trend24[0]>0:
                held[3,0]=.12
            bull=trend336[0]>0 and sum(trend168[j]>0 for j in range(4))>=2
            factors=np.array([1.,.85,.70] if bull else [.75,1.,1.])
            if np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8)>1.5:
                factors[0]*=.5;factors[2]=1.
            active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        w=held.copy()
        for s in (1,2,3):w[s]*=factors[s-1]
        capacity=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if capacity<0:raise ValueError('NC_INDEPENDENT_CORE_GROSS')
        if optional>capacity and optional>0:w[1:]*=capacity/optional
        target[t]=w
    return target,active,forced
def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    independently,activity,forced=replay(d)
    mismatch=int(np.count_nonzero(np.abs(original[0]-independently)>1e-10))
    activity_mismatch=int(np.count_nonzero(original[2]!=activity))
    silent=int(np.count_nonzero(
        (np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('NC_INDEPENDENT_REPLAY_MISMATCH')
    if silent:failures.append('NC_SILENT_WEIGHT_UPDATE')
    if missing:failures.append('NC_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NC_NATIVE_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:
        failures.append('NC_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:
                failures.append('NC_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatch,
        'independent_active_week_mismatches':activity_mismatch,
        'silent_weight_updates':silent,'forced_core_refreshes':int(forced.sum()),
        'preregistered_core_refreshes':len(schedule),'missed_core_refresh_hours':missing,
        'native_funding_events':int(d['event'].sum()),
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
