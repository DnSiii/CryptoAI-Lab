#!/usr/bin/env python3
"""V98 MD independent entry calendar and authenticated source-only gate."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from md_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES
def replay(d):
    p=np.log(d['c']);q=d['q'];rate=d['rate'];event=d['event']
    out=np.zeros((HOURS,3),bool);expiry=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        expired=np.zeros(3,bool)
        for k in range(3):
            if expiry[k]>=0 and t>=expiry[k]:
                expiry[k]=-1;expired[k]=True
        if not (np.all(q[t-335:t+1]>0) and np.all(q[t-672]>0)):continue
        r336=p[t]-p[t-336];r168=p[t]-p[t-168];r72=p[t]-p[t-72]
        breadth=int(np.count_nonzero(r336>0))
        if (t-WARMUP)%336==0 and expiry[0]<0 and not expired[0] and breadth>=2:
            eligible=np.flatnonzero((r336>0)&(r72>0))
            if eligible.size:
                j=int(eligible[np.argmax(r72[eligible])])
                if np.mean(q[t-71:t+1,j])>np.mean(q[t-335:t-71,j]):
                    out[t,0]=True;expiry[0]=t+336
        if (t-WARMUP)%168==0 and expiry[1]<0 and not expired[1]:
            events=event[t-167:t+1]
            n=np.sum(events,axis=0)
            if np.all(n==21):
                avg=np.sum(rate[t-167:t+1],axis=0)/n
                low=int(np.argmin(avg));high=int(np.argmax(avg))
                if avg[high]-avg[low]>.00015 and abs(r168[high]-r168[low])<.10:
                    out[t,1]=True;expiry[1]=t+336
        if (t-WARMUP)%168==0 and expiry[2]<0 and not expired[2]:
            if np.count_nonzero(r336<0)>=2 and np.count_nonzero(r72>0)>=2:
                out[t,2]=True;expiry[2]=t+168
    return out
def check(d):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    a=bundle(*args);expected=replay(d);synthetic_causality()
    mutated=[x.copy() for x in args]
    for x in mutated[:4]:x[14000:]*=1.7
    mutated[4][14000:]*=3;mutated[5][14000:]*=-1
    b=bundle(*mutated)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MD_AUTHENTICATED_FUTURE_LEAK')
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
