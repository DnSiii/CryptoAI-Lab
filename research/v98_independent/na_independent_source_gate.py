#!/usr/bin/env python3
"""V98 NA independently reconstructed all-hour source-only gate; never computes PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from na_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    p=np.log(d['c'])
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    active=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    held=np.zeros((4,4))
    mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('NA_INDEPENDENT_CORE_NO_VOLUME')
            ret504=p[t]-p[t-504]
            ret168=p[t]-p[t-168]
            held[0]=0
            if ret504[0]>0 and sum(ret168[j]>0 for j in (1,2,3))>=2:
                leader=1+int(np.argmax(ret504[1:]))
                held[0,0]=.50
                held[0,leader]=.20
            else:
                lowvol=1+int(np.argmin(np.std(r[t-167:t+1,1:],axis=0)))
                held[0,0]=-.40
                held[0,lowvol]=.10
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NA_INDEPENDENT_WEEK_NO_VOLUME')
            ret504=p[t]-p[t-504]
            ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72]
            ret24=p[t]-p[t-24]
            held[1:]=0
            # Independently construct signed price/volume breakout candidates.
            volume24=np.sum(d['q'][t-23:t+1,1:],axis=0)
            volume168=np.sum(d['q'][t-167:t+1,1:],axis=0)
            ranked=[]
            for j in (1,2,3):
                v=float(volume24[j-1]/max(volume168[j-1]/7.,1e-10))
                if v<=1.20:continue
                high=float(np.max(d['h'][t-96:t,j]))
                low=float(np.min(d['l'][t-96:t,j]))
                px=float(d['c'][t,j])
                if px>high:ranked.append((px/high-1.,-j,j,1.))
                elif px<low:ranked.append((1.-px/low,-j,j,-1.))
            if ranked:
                selected=max(ranked)
                held[1,selected[2]]=.14*selected[3]
            # Independent OLS residuals on BTC, 336 completed hourly returns.
            btc=r[t-335:t+1,0]
            btc_mean=float(np.mean(btc))
            denom=max(float(np.mean((btc-btc_mean)**2)),1e-12)
            residual=[]
            for j in (1,2,3):
                y=r[t-335:t+1,j]
                covariance=float(np.mean((btc-btc_mean)*(y-np.mean(y))))
                b=float(np.clip(covariance/denom,0.,3.))
                residual.append(float(ret168[j]-b*ret168[0]))
            cheap=int(np.argmin(residual))+1
            rich=int(np.argmax(residual))+1
            if rich!=cheap and max(residual)-min(residual)>.045:
                held[2,cheap]=.08
                held[2,rich]=-.08
            breadth=sum(ret72[j]<0 for j in range(4))
            if ret24[0]<-.035 and breadth>=3:
                held[3,0]=-.14
            elif ret24[0]>.020 and ret72[0]<0 and breadth>=2:
                held[3,0]=.14
            bull=ret504[0]>0 and sum(ret168[j]>0 for j in (1,2,3))>=2
            mult=np.array([1.,.9,.6] if bull else [.8,1.,1.])
            if np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8)>1.5:
                mult[0]*=.5
                mult[2]=1.
            active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        w=held.copy()
        for s in (1,2,3):w[s]*=mult[s-1]
        room=.84-float(np.abs(w[0]).sum())
        if room<0:raise ValueError('NA_INDEPENDENT_CORE_GROSS')
        need=float(np.abs(w[1:]).sum())
        if need>room and need>0:w[1:]*=room/need
        target[t]=w
    return target,active,forced

def check(d):
    synthetic_causality()
    expected=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    actual,active,forced=replay(d)
    mismatch=int(np.count_nonzero(np.abs(expected[0]-actual)>1e-10))
    activity_mismatch=int(np.count_nonzero(expected[2]!=active))
    silent=int(np.count_nonzero(
        (np.abs(np.diff(expected[0],axis=0)).sum(axis=2)>1e-12)&~expected[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not expected[1][t,0] or not forced[t]]
    counts={str(y):{name:int(expected[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('NA_INDEPENDENT_REPLAY_MISMATCH')
    if silent:failures.append('NA_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('NA_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('NA_FUNDING_COUNT')
    if np.max(np.abs(expected[0]).sum(axis=(1,2)))>.84+1e-10:
        failures.append('NA_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:
                failures.append('NA_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatch,
        'independent_active_week_mismatches':activity_mismatch,
        'silent_weight_updates':silent,'forced_core_refreshes':int(forced.sum()),
        'preregistered_core_refreshes':len(schedule),'missed_core_refresh_hours':missing,
        'native_funding_events':int(d['event'].sum()),
        'active_distinct_week_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
        'synthetic_future_mutation_pass':True,
        'training_only':True,'pnl_computed':False,'holdout_accessed':False}

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
