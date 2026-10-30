#!/usr/bin/env python3
"""V98 MP independently reconstruct all 17,544 training-hour targets and entries."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mp_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def independent(d):
    close=d['c'];lp=np.log(close)
    returns=np.diff(lp,axis=0,prepend=lp[:1])
    weights=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    paper=np.zeros((HOURS,3))
    inventory=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    last_funding=np.zeros(4)
    breadth=0
    vol_ratio=1.
    factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        quote_ok=bool((d['q'][t]>0).all())
        if t>WARMUP:
            ret=(close[t]-close[t-1])/close[t-1]
            for sleeve in range(3):
                paper[t,sleeve]=float(np.dot(inventory[sleeve+1],ret))
        cooldown=set()
        for slot in (1,2,3):
            if expiry[slot]>=0 and t>=expiry[slot]:
                inventory[slot]=0.
                expiry[slot]=-1
                cooldown.add(slot)
        if k%672==0:
            if not quote_ok:raise ValueError('MP_INDEPENDENT_MISSING_CORE_QUOTE_'+str(t))
            inventory[0]=0.
            inventory[0,0]=.69 if np.log(close[t,0]/close[t-336,0])>0 else .62
            forced[t]=True
        if k%168==0:
            r168=np.log(close[t]/close[t-168])
            r72=np.log(close[t]/close[t-72])
            r24=np.log(close[t]/close[t-24])
            breadth=int(sum(r168>0))
            vol_ratio=float(np.std(returns[t-71:t+1,0])/max(float(np.std(returns[t-335:t+1,0])),1e-8))
            if quote_ok and 1 not in cooldown and expiry[1]<0 and r168[0]>0:
                elig=[j for j in (1,2,3) if r168[j]>r168[0] and r72[j]>0 and r24[j]>0]
                if elig:
                    pick=sorted(elig,key=lambda j:(-float(r168[j]-r168[0]),j))[0]
                    inventory[1,pick]=.14
                    expiry[1]=t+168
                    entries[t,0]=True
            if quote_ok and 2 not in cooldown and expiry[2]<0:
                x=returns[t-335:t+1,0]
                xcenter=x-x.mean()
                den=max(float(np.sum(xcenter*xcenter)),1e-8)
                beta=[]
                for j in (1,2,3):
                    y=returns[t-335:t+1,j]
                    beta.append(float(np.sum(xcenter*(y-y.mean()))/den))
                residual=r168[1:]-np.array(beta)*r168[0]
                hi=int(np.argmax(residual))+1
                lo=int(np.argmin(residual))+1
                if (hi!=lo and residual[hi-1]-residual[lo-1]>.06 and r24[hi]>r24[lo]
                    and last_funding[hi]-last_funding[lo]<=.0002):
                    inventory[2,hi]=.07
                    inventory[2,lo]=-.04
                    expiry[2]=t+168
                    entries[t,1]=True
            if quote_ok and 3 not in cooldown and expiry[3]<0 and r168[0]<0 and r24[0]>0 and breadth<=2:
                inventory[3,0]=.09
                expiry[3]=t+168
                entries[t,2]=True
            if k>=672:
                score=paper[t-671:t+1].sum(axis=0)-.002*entries[t-672:t].sum(axis=0)
                factors=np.array([1. if s>0 else .25 for s in score])
        w=inventory.copy()
        w[1]*=(1. if breadth>=2 else .6)*factors[0]
        w[2]*=(1. if vol_ratio<=1.5 else .6)*factors[1]
        w[3]*=(1. if breadth<=1 else .7)*factors[2]
        optional=float(np.abs(w[1:]).sum())
        if optional>0:
            w[1:]*=min(1.,max(0.,(.89-float(np.abs(w[0]).sum()))/optional))
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
    if werr or eerr:failures.append('MP_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('MP_SILENT_WEIGHT_UPDATE')
    if missing:failures.append('MP_FORCED_CORE_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MP_NATIVE_FUNDING_COUNT')
    if np.max(np.sum(np.abs(original[0]),axis=(1,2)))>.89+1e-10:failures.append('MP_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MP_MINIMUM_'+y+'_'+name)
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
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output')
    a=p.parse_args()
    result=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
