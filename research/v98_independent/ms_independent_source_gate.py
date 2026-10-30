#!/usr/bin/env python3
"""V98 MS independent source replay: separate algebra, no PnL or future holdout."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from ms_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def independent(d):
    close=d['c']
    rr=np.diff(np.log(close),axis=0,prepend=np.log(close[:1]))
    weights=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inventory=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    last_funding=np.zeros(4)
    ratio=1.
    factors=np.ones(3)
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
            if not quote_ok:raise ValueError('MS_INDEPENDENT_MISSING_CORE_QUOTE_'+str(t))
            m=np.log(close[t]/close[t-336])
            inventory[0]=0.
            if m[0]>0:inventory[0,0]=.72
            elif m[1]>0:
                inventory[0,0]=.60
                inventory[0,1]=.08
            else:inventory[0,0]=.68
            forced[t]=True
        if k%168==0:
            m=np.log(close[t]/close[t-168])
            m72=np.log(close[t]/close[t-72])
            m24=np.log(close[t]/close[t-24])
            leader=int(np.argmax(m[1:]))+1
            if (quote_ok and 1 not in cooldown and expiry[1]<0 and m[leader]>.05
                and m24[leader]>0 and m[0]>0):
                inventory[1,leader]=.16
                expiry[1]=t+168
                entries[t,0]=True
            if quote_ok and 2 not in cooldown and expiry[2]<0:
                x=rr[t-335:t+1,0]
                x0=x-np.mean(x)
                v=max(float(np.sum(x0*x0)),1e-12)
                b=[]
                for j in (1,2,3):
                    y=rr[t-335:t+1,j]
                    b.append(float(np.sum(x0*(y-np.mean(y)))/v))
                resid=m72[1:]-np.asarray(b)*m72[0]
                hi=int(np.argmax(resid))+1
                lo=int(np.argmin(resid))+1
                if (hi!=lo and resid[hi-1]-resid[lo-1]>.045
                    and resid[hi-1]>0 and resid[lo-1]<0
                    and last_funding[hi]-last_funding[lo]<=.0002):
                    inventory[2,hi]=.075
                    inventory[2,lo]=-.045
                    expiry[2]=t+168
                    entries[t,1]=True
            ethvol=float(np.std(rr[t-71:t+1,1])/max(float(np.std(rr[t-335:t+1,1])),1e-8))
            if (quote_ok and 3 not in cooldown and expiry[3]<0 and m[1]<0
                and m24[1]<0 and ethvol>1.30 and int(sum(m<0))>=2):
                inventory[3,1]=-.13
                expiry[3]=t+168
                entries[t,2]=True
            strong=bool(int(sum(m>0))>=3 and m72[0]>0)
            router=[1.,1.,.60] if strong else [.75,.85,1.]
            base=max(float(np.std(rr[t-167:t+1,0])),1e-8)
            for slot in (1,2,3):
                legs=np.where(np.abs(inventory[slot])>1e-12)[0]
                if len(legs):
                    v=float(np.mean([np.std(rr[t-167:t+1,j]) for j in legs]))
                    factors[slot-1]=float(router[slot-1]*np.clip(np.sqrt(base/max(v,1e-8)),.65,1.25))
                else:factors[slot-1]=float(router[slot-1])
        w=inventory.copy()
        for slot in (1,2,3):w[slot]*=factors[slot-1]
        free=.89-float(np.abs(w[0]).sum())
        desired=float(np.abs(w[1:]).sum())
        if desired>0:w[1:]*=min(1.,max(0.,free/desired))
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
    if werr or eerr:failures.append('MS_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('MS_SILENT_WEIGHT_UPDATE')
    if missing:failures.append('MS_FORCED_CORE_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MS_NATIVE_FUNDING_COUNT')
    if np.max(np.sum(np.abs(original[0]),axis=(1,2)))>.89+1e-10:failures.append('MS_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MS_MINIMUM_'+y+'_'+name)
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
