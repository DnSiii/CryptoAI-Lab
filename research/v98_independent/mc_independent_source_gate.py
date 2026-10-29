#!/usr/bin/env python3
"""V98 MC independent pre-PnL entry calendar, source integrity, causal mutation."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mc_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES
def replay(d):
    p=np.log(d['c']);q=d['q']
    entries=np.zeros((HOURS,3),bool);expiry=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        expired=np.zeros(3,bool)
        for k in range(3):
            if expiry[k]>=0 and t>=expiry[k]:
                expiry[k]=-1;expired[k]=True
        if not (np.all(q[t-167:t+1]>0) and np.all(q[t-504]>0)):continue
        r168=p[t]-p[t-168];r48=p[t]-p[t-48];r24=p[t]-p[t-24]
        breadth=int(np.count_nonzero(r168>0))
        if (t-WARMUP)%96==0 and expiry[0]<0 and not expired[0] and breadth>=3:
            eligible=np.where((r168>0)&(r48>0))[0]
            if eligible.size:
                j=int(eligible[np.argmax(r48[eligible])])
                if np.mean(q[t-47:t+1,j])>np.mean(q[t-167:t-47,j]):
                    entries[t,0]=True;expiry[0]=t+96
        if (t-WARMUP)%48==0 and expiry[1]<0 and not expired[1] and breadth<=2:
            if np.max(r48)-np.min(r48)>.025:
                entries[t,1]=True;expiry[1]=t+48
        if (t-WARMUP)%48==0 and expiry[2]<0 and not expired[2] and breadth<=2:
            if np.count_nonzero(r168<0)>=2 and np.count_nonzero(r24>0)>=2:
                entries[t,2]=True;expiry[2]=t+96
    return entries
def check(d):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    a=bundle(*args);expected=replay(d)
    synthetic_causality()
    mutated=[x.copy() for x in args]
    for x in mutated[:4]:x[14000:]*=1.7
    mutated[4][14000:]*=3;mutated[5][14000:]*=-1
    b=bundle(*mutated)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MC_AUTHENTICATED_FUTURE_LEAK')
    entries=a[2]
    mismatch=int(np.count_nonzero(entries!=expected))
    invalid=int(np.count_nonzero(entries[~a[3]]))
    silent=int(np.count_nonzero((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]))
    gross=float(np.abs(a[0]).sum(axis=(1,2)).max())
    counts={str(y):{name:int(entries[start:end,k].sum()) for k,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    fail=bool(mismatch or invalid or silent or gross>.88+1e-9 or
              any(n<8 for yr in counts.values() for n in yr.values()))
    return {'decision':'REJECT_SOURCE_ONLY' if fail else 'PASS_SOURCE_ONLY',
            'counts':counts,'independent_entry_mismatch':mismatch,'invalid_entries':invalid,
            'silent_updates':silent,'intended_gross_peak':gross,
            'funding_events':int(d['event'].sum()),'training_only':True,
            'pnl_computed':False,'holdout_read':False,'synthetic_causality':True}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();result=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
