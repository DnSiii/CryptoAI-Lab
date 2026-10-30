#!/usr/bin/env python3
"""V98 MU independent source replay, source-only, never PnL or future holdout."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mu_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def replay(d):
    p=np.log(d['c'])
    returns=np.diff(p,axis=0,prepend=p[:1])
    weights=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inv=np.zeros((4,4))
    expiry=[-1]*4
    settled=np.zeros(4)
    mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(d['q'][t]>0))
        cooldown=[]
        for s in (1,2,3):
            if expiry[s]>=0 and t>=expiry[s]:
                inv[s]=0
                expiry[s]=-1
                cooldown.append(s)
        if k%672==0:
            if not good:raise ValueError('MU_INDEPENDENT_CORE_NO_VOLUME')
            z=np.log(d['c'][t,:2]/d['c'][t-336,:2])
            inv[0]=0
            if z[0]>0 and z[1]>0:inv[0,0]=.46;inv[0,1]=.22
            elif z[0]>0:inv[0,0]=.68
            elif z[1]>0:inv[0,0]=.28;inv[0,1]=.36
            else:inv[0,0]=.45;inv[0,1]=.10
            forced[t]=True
        if k%168==0:
            a=np.log(d['c'][t]/d['c'][t-168])
            b=np.log(d['c'][t]/d['c'][t-72])
            z=np.log(d['c'][t]/d['c'][t-24])
            leader=int(np.argmax(a[2:])+2)
            if (good and 1 not in cooldown and expiry[1]<0 and
                d['c'][t,leader]>np.max(d['c'][t-168:t,leader]) and
                b[leader]>.035 and a[0]>-.03):
                inv[1,leader]=.16;expiry[1]=t+168;entries[t,0]=True
            weak=int(np.argmin(z[1:])+1)
            strong=int(np.argmax(z[1:])+1)
            if (good and 2 not in cooldown and expiry[2]<0 and
                weak!=strong and z[strong]-z[weak]>.055 and
                a[weak]>0 and a[strong]>0 and
                settled[weak]-settled[strong]<=.0002):
                inv[2,weak]=.075;inv[2,strong]=-.060
                expiry[2]=t+168;entries[t,1]=True
            if (good and 3 not in cooldown and expiry[3]<0 and
                b[0]<-.055 and z[0]<0 and int(np.sum(a<0))>=3):
                inv[3,0]=-.13;expiry[3]=t+168;entries[t,2]=True
            bullish=bool(a[0]>0 and int(np.sum(a>0))>=2)
            mult=np.asarray([1.,.85,.60] if bullish else [.55,.70,1.])
            v=float(np.std(returns[t-71:t+1,0])/max(np.std(returns[t-335:t+1,0]),1e-8))
            if v>1.5:mult[0]*=.5;mult[2]=1.
        w=inv.copy()
        w[1:]*=mult[:,None]
        room=.84-np.abs(w[0]).sum()
        gross=np.abs(w[1:]).sum()
        if gross>room and gross>0:w[1:]*=room/gross
        weights[t]=w
        if np.any(d['event'][t]):settled=np.where(d['event'][t],d['rate'][t],settled)
    return weights,entries,forced
def check(d):
    synthetic_causality()
    source=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    weights,entries,forced=replay(d)
    mismatches=int(np.count_nonzero(np.abs(source[0]-weights)>1e-10))
    entry_mismatches=int(np.count_nonzero(source[2]!=entries))
    silent=int(np.count_nonzero((np.abs(np.diff(source[0],axis=0)).sum(axis=2)>1e-12)&~source[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not source[1][t,0] or not forced[t]]
    counts={str(y):{name:int(source[2][start:end,i].sum()) for i,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatches or entry_mismatches:failures.append('MU_INDEPENDENT_REPLAY_MISMATCH')
    if silent:failures.append('MU_SILENT_WEIGHT_CHANGE')
    if missing:failures.append('MU_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MU_FUNDING_COUNT')
    if np.max(np.sum(np.abs(source[0]),axis=(1,2)))>.84+1e-10:failures.append('MU_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MU_MINIMUM_'+y+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'independent_hourly_weight_mismatches':mismatches,
        'independent_entry_mismatches':entry_mismatches,'silent_weight_updates':silent,
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
