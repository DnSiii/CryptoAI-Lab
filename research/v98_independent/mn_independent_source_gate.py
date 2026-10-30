#!/usr/bin/env python3
"""MN independent 17544-hour signal and entry audit before economic PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mn_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def independent(d):
    lp=np.log(d['c'])
    out=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    forced=np.zeros(HOURS,bool)
    inventory=np.zeros((4,4))
    expire=[-1,-1,-1]
    breadth=0
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        quote_ok=bool((d['q'][t]>0).all())
        cooldown=[False,False,False]
        for slot in range(3):
            if expire[slot]>=0 and t>=expire[slot]:
                inventory[slot+1]=0.
                expire[slot]=-1
                cooldown[slot]=True
        if k%672==0:
            if not quote_ok:raise ValueError('MN_INDEPENDENT_MISSING_CORE_QUOTE_'+str(t))
            inventory[0]=[.72 if lp[t,0]>lp[t-336,0] else .64,0,0,0]
            forced[t]=True
        if k%168==0:
            r168=np.log(d['c'][t]/d['c'][t-168])
            r24=np.log(d['c'][t]/d['c'][t-24])
            r72=np.log(d['c'][t]/d['c'][t-72])
            breadth=sum(r168>0)
            if quote_ok and not cooldown[0] and expire[0]<0 and r168[0]>0:
                eligible=[j for j in (1,2,3) if r168[j]>r168[0] and r24[j]>0 and r72[j]>0]
                if eligible:
                    leader=sorted(eligible,key=lambda j:(-float(r168[j]),j))[0]
                    inventory[1,leader]=.11
                    expire[0]=t+168
                    entries[t,0]=True
            if quote_ok and not cooldown[1] and expire[1]<0 and r168[0]>0:
                eligible=[j for j in (1,2,3) if r168[j]<0]
                if eligible:
                    laggard=sorted(eligible,key=lambda j:(float(r168[j]),j))[0]
                    inventory[2,0]=.055
                    inventory[2,laggard]=-.025
                    expire[1]=t+168
                    entries[t,1]=True
            if quote_ok and not cooldown[2] and expire[2]<0 and r168[0]<0 and sum(r24>0)>=2:
                inventory[3,0]=.08
                expire[2]=t+168
                entries[t,2]=True
        w=inventory.copy()
        w[1]*=1. if breadth>=2 else .7
        w[2]*=1. if breadth<=2 else .8
        w[3]*=1. if breadth<=2 else .7
        core=np.abs(w[0]).sum()
        rest=np.abs(w[1:]).sum()
        if rest>0:w[1:]*=min(1.,max(0.,(.89-core)/rest))
        out[t]=w
    return out,entries,forced

def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    independent_w,independent_entries,refresh=independent(d)
    werr=int(np.count_nonzero(np.abs(original[0]-independent_w)>1e-11))
    eerr=int(np.count_nonzero(original[2]!=independent_entries))
    changed=np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12
    silent=int(np.count_nonzero(changed&~original[1][1:]))
    calendar=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in calendar if not original[1][t,0] or not refresh[t]]
    counts={str(year):{name:int(original[2][start:end,k].sum()) for k,name in enumerate(NAMES)}
        for year,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if werr or eerr:failures.append('MN_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('MN_SILENT_WEIGHT_UPDATE')
    if missing:failures.append('MN_FORCED_CORE_REFRESH')
    if int(d['event'].sum())!=9144:failures.append('MN_NATIVE_FUNDING_COUNT')
    if np.max(np.sum(np.abs(original[0]),axis=(1,2)))>.89+1e-10:failures.append('MN_GROSS')
    for year in ('2023','2024'):
        for k,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[k]:failures.append('MN_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
            'failures':failures,'independent_hourly_weight_mismatches':werr,
            'independent_entry_mismatches':eerr,'silent_weight_updates':silent,
            'forced_core_refreshes':int(refresh.sum()),'preregistered_core_refreshes':len(calendar),
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
