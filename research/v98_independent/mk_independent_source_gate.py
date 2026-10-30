#!/usr/bin/env python3
"""Independent source-only MK native funding carry oracle; no system PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mk_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM
def independent(d):
    lp=np.log(d['c'])
    output=np.zeros((HOURS,4,4))
    entries=np.zeros((HOURS,3),bool)
    refresh=np.zeros(HOURS,bool)
    positions=np.zeros((4,4))
    expire=[-1,-1,-1]
    breadth=0
    for hour in range(WARMUP,HOURS):
        k=hour-WARMUP
        good=bool((d['q'][hour]>0).all())
        cooldown=[False]*3
        for slot in range(3):
            if expire[slot]>=0 and hour>=expire[slot]:
                positions[slot+1,:]=0.
                expire[slot]=-1
                cooldown[slot]=True
        if k%672==0:
            if not good:raise ValueError('MK_INDEPENDENT_SCHEDULED_ZERO_QUOTE_'+str(hour))
            positions[0,:]=[.72,0,0,0]
            refresh[hour]=True
        if k%168==0:
            returns168=lp[hour]-lp[hour-168]
            breadth=sum(x>0 for x in returns168)
            if good and expire[0]<0 and not cooldown[0]:
                r336=lp[hour]-lp[hour-336]
                r72=lp[hour]-lp[hour-72]
                if r336[3]>r336[0] and r72[3]>0 and returns168[0]>0:
                    positions[1,3]=.10
                    expire[0]=hour+168
                    entries[hour,0]=True
            if good and expire[2]<0 and not cooldown[2]:
                s72=float(np.std(np.diff(lp[hour-72:hour+1,0])))
                s336=float(np.std(np.diff(lp[hour-336:hour+1,0])))
                if s336>0 and s72>1.4*s336 and lp[hour,0]>lp[hour-24,0]:
                    positions[3,0]=.08
                    expire[2]=hour+168
                    entries[hour,2]=True
        if k%336==0 and good and expire[1]<0 and not cooldown[1]:
            past_funding=d['rate'][hour-160:hour+1:8,1:4]
            averages=np.sum(past_funding,axis=0)/len(past_funding)
            lo=int(np.argmin(averages))
            hi=int(np.argmax(averages))
            if lo!=hi and averages[hi]-averages[lo]>=.0001:
                positions[2,lo+1]=.045
                positions[2,hi+1]=-.045
                expire[1]=hour+336
                entries[hour,1]=True
        w=positions.copy()
        w[1,:]*=(1. if breadth>=3 else .5)
        w[2,:]*=(1. if breadth<=2 else .8)
        w[3,:]*=(1. if breadth<=2 else .7)
        cap=.88-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if optional>0:w[1:,:]*=min(1.,max(0.,cap/optional))
        output[hour]=w
    return output,entries,refresh
def check(d):
    synthetic_causality()
    original=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    weights,entries,refresh=independent(d)
    mismatch=int(np.count_nonzero(np.abs(original[0]-weights)>1e-12))
    entry_mismatch=int(np.count_nonzero(original[2]!=entries))
    silent=int(np.count_nonzero((np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]))
    calendar=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in calendar if not original[1][t,0] or not refresh[t]]
    counts={str(y):{name:int(original[2][start:end,k].sum()) for k,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or entry_mismatch:failures.append('MK_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('MK_SILENT_UPDATES')
    if missing:failures.append('MK_CORE_REFRESH_MISSING')
    if int(d['event'].sum())!=9144:failures.append('MK_FUNDING_EVENT_COUNT')
    if float(np.abs(original[0]).sum(axis=(1,2)).max())>.88+1e-10:failures.append('MK_TARGET_GROSS')
    for y in ('2023','2024'):
        for k,name in enumerate(NAMES):
            if counts[y][name]<MINIMUM[k]:failures.append('MK_ACTIVATION_'+y+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
            'failures':failures,'entry_counts':counts,
            'minimums':dict(zip(NAMES,MINIMUM)),
            'independent_hourly_weight_mismatches':mismatch,
            'independent_entry_mismatches':entry_mismatch,
            'silent_weight_updates':silent,'forced_core_refreshes':int(refresh.sum()),
            'preregistered_core_refreshes':len(calendar),'missing_core_refreshes':missing,
            'native_funding_events':int(d['event'].sum()),
            'native_carry_uses_only_past_21_events':True,
            'training_only':True,'pnl_computed':False,'holdout_accessed':False}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();r=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(r,f,indent=2,sort_keys=True)
    print(json.dumps(r,indent=2,sort_keys=True))
    raise SystemExit(0 if r['decision']=='PASS_SOURCE_ONLY' else 2)
