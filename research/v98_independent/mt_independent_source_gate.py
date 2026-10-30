#!/usr/bin/env python3
"""V98 MT independent all-hour source replay; no economic PnL.\n\nRuns against the restored full repository tree, never a partial snapshot.\n"""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mt_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def independent(d):
    close=d['c']
    returns=np.diff(np.log(close),axis=0,prepend=np.log(close[:1]))
    weights=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inventory=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    settled=np.zeros(4)
    mult=np.ones(3)
    priority=(1,2,3)
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
            if not quote_ok:raise ValueError('MT_INDEPENDENT_MISSING_CORE_QUOTE_'+str(t))
            trend=np.log(close[t]/close[t-336])
            inventory[0]=0.
            if min(trend[:2])>0:
                inventory[0,0]=.62
                inventory[0,1]=.10
            else:inventory[0,0]=.70
            forced[t]=True
        if k%168==0:
            trend=np.log(close[t]/close[t-168])
            move72=np.log(close[t]/close[t-72])
            move48=np.log(close[t]/close[t-48])
            move24=np.log(close[t]/close[t-24])
            rel=trend[1:]-trend[0]
            leader=int(np.argmax(rel))+1
            if (quote_ok and 1 not in cooldown and expiry[1]<0 and
                rel[leader-1]>.025 and move48[leader]>0):
                inventory[1,leader]=.16
                expiry[1]=t+168
                entries[t,0]=True
            if quote_ok and 2 not in cooldown and expiry[2]<0:
                cheap=int(np.argmin(settled))
                rich=int(np.argmax(settled))
                if (cheap!=rich and settled[rich]-settled[cheap]>.00003 and
                    move72[cheap]>=move72[rich]):
                    inventory[2,cheap]=.065
                    inventory[2,rich]=-.055
                    expiry[2]=t+168
                    entries[t,1]=True
            drawdown=close[t,0]/max(close[t-335:t+1,0])-1.
            if (quote_ok and 3 not in cooldown and expiry[3]<0 and
                drawdown<=-.08 and move72[0]<0 and move24[0]>0):
                inventory[3,0]=.12
                expiry[3]=t+168
                entries[t,2]=True
            constructive=bool(int(sum(trend>0))>=2 and move72[0]>0)
            ratio=float(np.std(returns[t-71:t+1,0])/max(float(np.std(returns[t-335:t+1,0])),1e-8))
            mult=np.asarray([1.,.70,.65] if constructive else [.70,1.,1.])
            if ratio>1.5:
                mult[0]*=.80
                mult[2]*=1.10
            priority=(1,2,3) if constructive else (3,2,1)
        w=inventory.copy()
        for slot in (1,2,3):w[slot]*=mult[slot-1]
        free=.89-float(np.abs(w[0]).sum())
        for slot in priority:
            requested=float(np.abs(w[slot]).sum())
            if requested:
                share=min(1.,max(0.,free/requested))
                w[slot]*=share
                free-=requested*share
        weights[t]=w
        if np.any(d['event'][t]):
            settled=np.where(d['event'][t],d['rate'][t],settled)
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
    if werr or eerr:failures.append('MT_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('MT_SILENT_WEIGHT_UPDATE')
    if missing:failures.append('MT_FORCED_CORE_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MT_NATIVE_FUNDING_COUNT')
    if np.max(np.sum(np.abs(original[0]),axis=(1,2)))>.89+1e-10:failures.append('MT_GROSS')
    for y in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[i]:failures.append('MT_MINIMUM_'+y+'_'+name)
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
