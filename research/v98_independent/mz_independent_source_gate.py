#!/usr/bin/env python3
"""V98 MZ independently reimplemented 17,544-hour signal audit; no physical PnL import."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mz_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    p=np.log(d['c'])
    hourly=np.diff(p,axis=0,prepend=p[:1])
    out=np.zeros((HOURS,4,4))
    active=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inventory=np.zeros((4,4))
    regime=np.ones(3)
    multipliers=np.ones(3)
    for t in range(WARMUP,HOURS):
        elapsed=t-WARMUP
        if elapsed%672==0:
            if np.any(d['q'][t]<=0):raise ValueError('MZ_INDEPENDENT_CORE_NO_VOLUME')
            trend=np.log(d['c'][t]/d['c'][t-336])
            risk=np.std(hourly[t-335:t+1,1:],axis=0)*np.sqrt(336.)
            candidate=int(np.argmax(trend[1:]/np.maximum(risk,.03)))+1
            inventory[0]=0.
            if trend[0]>0 and trend[candidate]>0:
                inventory[0,0]=.49;inventory[0,candidate]=.21
            else:
                inventory[0,0]=.42;inventory[0,2]=.08
            forced[t]=True
        if elapsed%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('MZ_INDEPENDENT_WEEK_NO_VOLUME')
            trend168=np.log(d['c'][t]/d['c'][t-168])
            trend72=np.log(d['c'][t]/d['c'][t-72])
            trend24=np.log(d['c'][t]/d['c'][t-24])
            btc336=float(np.log(d['c'][t,0]/d['c'][t-336,0]))
            longvol=np.std(hourly[t-335:t+1,1:],axis=0)
            shortvol=np.std(hourly[t-71:t+1,1:],axis=0)
            held=np.where(inventory[1]>0)[0]
            inventory[1]=0.
            if held.size==1 and trend168[held[0]]>0 and btc336>0:
                inventory[1,held[0]]=.12
            else:
                options=[j for j in (1,2,3) if
                         trend168[j]>0 and trend24[j]>0 and
                         shortvol[j-1]<=1.2*max(longvol[j-1],1e-10)]
                if options:
                    score=[trend168[j]/max(longvol[j-1]*np.sqrt(336.),.03) for j in options]
                    inventory[1,options[int(np.argmax(score))]]=.12
            f=np.mean(d['rate'][t-160:t+1:8,1:],axis=0)
            low=int(np.argmin(f))+1;high=int(np.argmax(f))+1
            spread=float(f[high-1]-f[low-1])
            held_long=np.where(inventory[2]>0)[0]
            held_short=np.where(inventory[2]<0)[0]
            retained=(held_long.size==1 and held_short.size==1 and
                      held_long[0]==low and held_short[0]==high)
            inventory[2]=0.
            if low!=high and (spread>.00002 or (retained and spread>.00001)):
                inventory[2,low]=.06;inventory[2,high]=-.06
            inventory[3]=0.
            negative=int(sum(trend72[j]<0 for j in range(4)))
            if negative>=3 and trend24[0]<0:
                worst=int(np.argmin(trend72[1:]))+1
                inventory[3,worst]=-.12
            elif negative>=2 and trend24[0]>0:
                best=int(np.argmax(trend24[1:]))+1
                inventory[3,best]=.12
            if elapsed%672==0:
                bullish=btc336>0 and sum(trend168[j]>0 for j in (1,2,3))>=2
                regime=np.array([1.,.75,.8] if bullish else [.65,1.,1.])
            multipliers=regime.copy()
            volatility_ratio=float(np.std(hourly[t-71:t+1,0])/
                max(np.std(hourly[t-335:t+1,0]),1e-8))
            if volatility_ratio>1.4:
                multipliers[0]*=.5;multipliers[2]=1.
            active[t]=np.abs(inventory[1:]).sum(axis=1)>1e-12
        w=inventory.copy()
        w[1:]*=multipliers[:,None]
        capacity=.84-np.abs(w[0]).sum()
        optional=np.abs(w[1:]).sum()
        if optional>capacity and optional>0:w[1:]*=capacity/optional
        out[t]=w
    return out,active,forced

def check(d):
    synthetic_causality()
    expected=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    actual,activity,forced=replay(d)
    mismatch=int(np.count_nonzero(np.abs(expected[0]-actual)>1e-10))
    activity_mismatch=int(np.count_nonzero(expected[2]!=activity))
    silent=int(np.count_nonzero(
        (np.abs(np.diff(expected[0],axis=0)).sum(axis=2)>1e-12)&~expected[1][1:]))
    scheduled=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in scheduled if not expected[1][t,0] or not forced[t]]
    counts={str(y):{name:int(expected[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or activity_mismatch:failures.append('MZ_INDEPENDENT_REPLAY_MISMATCH')
    if silent:failures.append('MZ_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('MZ_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MZ_FUNDING_COUNT')
    if np.max(np.abs(expected[0]).sum(axis=(1,2)))>.84+1e-10:
        failures.append('MZ_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:
                failures.append('MZ_MINIMUM_'+y+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatch,
        'independent_active_week_mismatches':activity_mismatch,
        'silent_weight_updates':silent,
        'forced_core_refreshes':int(forced.sum()),
        'preregistered_core_refreshes':len(scheduled),
        'missed_core_refresh_hours':missing,
        'native_funding_events':int(d['event'].sum()),
        'active_distinct_week_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
        'synthetic_future_mutation_pass':True,
        'training_only':True,'pnl_computed':False,'holdout_accessed':False}

def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
