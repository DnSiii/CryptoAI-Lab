#!/usr/bin/env python3
"""V98 ND independent full-hour source replay; no physical runner imports/PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from nd_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    logp=np.log(d['c']);hourly=np.diff(logp,axis=0,prepend=logp[:1])
    target=np.zeros((HOURS,4,4));active=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool);held=np.zeros((4,4));multipliers=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        if k%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('ND_INDEPENDENT_CORE_VOLUME')
            score=[]
            for j in range(4):
                negative=np.minimum(hourly[t-167:t+1,j],0)
                risk=max(float(np.sqrt(np.mean(negative**2))),.001)
                score.append(float(np.log(d['c'][t,j]/d['c'][t-504,j])/risk))
            order=sorted(range(4),key=lambda j:(-score[j],j))
            held[0]=0
            if sum(x>0 for x in score)>=2:
                held[0,order[0]]=.44;held[0,order[1]]=.18
            else:
                held[0,order[0]]=.18;held[0,order[-1]]=-.28
            forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('ND_INDEPENDENT_WEEK_VOLUME')
            ret={n:np.log(d['c'][t]/d['c'][t-n]) for n in (24,48,72,168,504)}
            held[1:]=0
            vol={j:float(np.mean(d['q'][t-47:t+1,j])/max(
                np.mean(d['q'][t-167:t-47,j]),1e-12)) for j in (1,2,3)}
            positive=[j for j in (1,2,3) if ret[168][j]>0 and ret[48][j]>0 and vol[j]>1.05]
            if positive:
                winner=max(positive,key=lambda j:(ret[48][j],-j));held[1,winner]=.14
            elif ret[168][0]<0:
                negative=[j for j in (1,2,3) if ret[168][j]<0 and ret[48][j]<0 and vol[j]>1.05]
                if negative:
                    loser=min(negative,key=lambda j:(ret[48][j],j));held[1,loser]=-.14
            rates=d['rate'][t-168:t:8]
            btc=float(np.mean(rates[:,0]))
            spreads=[float(np.mean(rates[:,j])-btc) for j in (1,2,3)]
            strongest=max(range(3),key=lambda i:(abs(spreads[i]),-i))
            if abs(spreads[strongest])>=.000025:
                j=strongest+1;direction=-1. if spreads[strongest]>0 else 1.
                held[2,j]=direction*.08;held[2,0]=-direction*.08
            if ret[72][0]<-.04 and sum(ret[72][j]<0 for j in (1,2,3))>=2:
                loser=min((1,2,3),key=lambda j:(ret[72][j],j))
                held[3,loser]=-.12
            elif ret[72][0]>0 and ret[168][0]<-.04 and sum(ret[168][j]<0 for j in (1,2,3))>=2:
                winner=max((1,2,3),key=lambda j:(ret[24][j],-j))
                held[3,winner]=.12
            bull=ret[504][0]>0 and sum(ret[168][j]>0 for j in range(4))>=2
            multipliers=np.array([1.,.8,.7] if bull else [.85,1.,1.])
            ratio=np.std(hourly[t-71:t+1,0])/max(np.std(hourly[t-335:t+1,0]),1e-8)
            if ratio>1.5:multipliers[0]*=.5;multipliers[2]=1.
            active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        weights=held.copy()
        for s in (1,2,3):weights[s]*=multipliers[s-1]
        room=.84-float(np.abs(weights[0]).sum())
        optional=float(np.abs(weights[1:]).sum())
        if room<0:raise ValueError('ND_INDEPENDENT_CORE_CAP')
        if optional>room and optional>0:weights[1:]*=room/optional
        target[t]=weights
    return target,active,forced
def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    independent,activity,forced=replay(d)
    mismatches=int(np.count_nonzero(np.abs(original[0]-independent)>1e-10))
    activity_mismatch=int(np.count_nonzero(original[2]!=activity))
    silent=int(np.count_nonzero((np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
        for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatches or activity_mismatch:failures.append('ND_INDEPENDENT_REPLAY')
    if silent:failures.append('ND_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('ND_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('ND_FUNDING_COUNT')
    if np.max(np.abs(original[0]).sum(axis=(1,2)))>.84+1e-10:failures.append('ND_VIRTUAL_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('ND_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatches,
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
