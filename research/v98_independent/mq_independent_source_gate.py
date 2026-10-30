#!/usr/bin/env python3
"""V98 MQ independent full-hour source and capital-priority replay before PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mq_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def independent(d):
    close=d['c'];lp=np.log(close)
    returns=np.diff(lp,axis=0,prepend=lp[:1])
    weights=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inventory=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    last_funding=np.zeros(4)
    breadth=0
    vol_ratio=1.
    up=False
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        quote_ok=bool((d['q'][t]>0).all())
        cooldown=set()
        for slot in (1,2,3):
            if expiry[slot]>=0 and t>=expiry[slot]:
                inventory[slot]=0.
                expiry[slot]=-1
                cooldown.add(slot)
        if k%672==0:
            if not quote_ok:raise ValueError('MQ_INDEPENDENT_MISSING_CORE_QUOTE_'+str(t))
            r336=np.log(close[t]/close[t-336])
            inventory[0]=0.
            if r336[1]>0 and r336[1]>r336[0]:
                inventory[0,0]=.53
                inventory[0,1]=.17
            else:inventory[0,0]=.70
            forced[t]=True
        if k%168==0:
            r168=np.log(close[t]/close[t-168])
            r72=np.log(close[t]/close[t-72])
            r24=np.log(close[t]/close[t-24])
            breadth=int(sum(r168>0))
            up=bool(r168[0]>0)
            vol_ratio=float(np.std(returns[t-71:t+1,0])/max(float(np.std(returns[t-335:t+1,0])),1e-8))
            if quote_ok and 1 not in cooldown and expiry[1]<0 and up and r24[0]>0:
                inventory[1,0]=.14
                expiry[1]=t+168
                entries[t,0]=True
            if quote_ok and 2 not in cooldown and expiry[2]<0:
                accel=r72[1:]-(72/168)*r168[1:]
                hi=int(np.argmax(accel))+1
                lo=int(np.argmin(accel))+1
                if (hi!=lo and accel[hi-1]-accel[lo-1]>.04 and r72[hi]>0
                    and r72[lo]<0 and last_funding[hi]-last_funding[lo]<=.0002):
                    inventory[2,hi]=.065
                    inventory[2,lo]=-.04
                    expiry[2]=t+168
                    entries[t,1]=True
            if (quote_ok and 3 not in cooldown and expiry[3]<0 and r168[0]<0
                and r24[0]<0 and int(sum(r168<0))>=2):
                inventory[3,0]=-.10
                expiry[3]=t+168
                entries[t,2]=True
        w=inventory.copy()
        w[1]*=1. if breadth>=2 else .65
        w[2]*=.75 if vol_ratio>1.5 else 1.
        w[3]*=.7 if breadth>=2 else 1.
        available=.89-float(np.abs(w[0]).sum())
        priority=[1,2,3] if up else [3,2,1]
        for slot in priority:
            gross=float(np.abs(w[slot]).sum())
            if gross>0:
                scale=min(1.,max(0.,available/gross))
                w[slot]*=scale
                available-=gross*scale
        weights[t]=w
        if np.any(d['event'][t]):
            last_funding=np.where(d['event'][t],d['rate'][t],last_funding)
    return weights,entries,forced
def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    expected,expected_entries,forced=independent(d)
    werr=int(np.count_nonzero(np.abs(original[0]-expected)>1e-10))
    eerr=int(np.count_nonzero(original[2]!=expected_entries))
    changed=np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12
    silent=int(np.count_nonzero(changed&~original[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not original[1][t,0] or not forced[t]]
    counts={str(y):{name:int(original[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
        for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if werr or eerr:failures.append('MQ_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('MQ_SILENT_WEIGHT_UPDATE')
    if missing:failures.append('MQ_FORCED_CORE_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MQ_NATIVE_FUNDING_COUNT')
    if np.max(np.sum(np.abs(original[0]),axis=(1,2)))>.89+1e-10:failures.append('MQ_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MQ_MINIMUM_'+y+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
            'failures':failures,'independent_hourly_weight_mismatches':werr,
            'independent_entry_mismatches':eerr,'silent_weight_updates':silent,
            'forced_core_refreshes':int(forced.sum()),'preregistered_core_refreshes':len(schedule),
            'missed_core_refresh_hours':missing,'native_funding_events':int(d['event'].sum()),
            'entry_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
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
