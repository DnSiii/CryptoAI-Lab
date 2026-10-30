#!/usr/bin/env python3
"""V98 LZ independent event replay and source-only gate, executed before any PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from lz_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay(d):
    p=np.log(d['c']);q=d['q']
    out=np.zeros((HOURS,3),bool)
    expiry=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        r672=p[t]-p[t-672];r168=p[t]-p[t-168];r24=p[t]-p[t-24];r6=p[t]-p[t-6]
        expired=np.zeros(3,bool)
        for k in range(3):
            if expiry[k]>=0 and t>=expiry[k]:
                expiry[k]=-1;expired[k]=True
        if not (np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,168,336,672))):
            continue
        eligible=np.flatnonzero(r672>0)
        if (t-WARMUP)%72==0:
            if not expired[0] and expiry[0]<0 and np.count_nonzero(r168>0)>=3 and len(eligible)>0:
                out[t,0]=True;expiry[0]=t+72
            if not expired[1] and expiry[1]<0 and r168[0]>0 and len(eligible)>=2:
                out[t,1]=True;expiry[1]=t+72
        if (t-WARMUP)%24==0 and not expired[2] and expiry[2]<0:
            if np.count_nonzero(r24<0)>=3 and np.count_nonzero(r6>0)>=2:
                out[t,2]=True;expiry[2]=t+72
    return out

def check(d):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    x=bundle(*args)
    a=x[2];b=replay(d)
    synthetic_causality()
    changed=[z.copy() for z in args]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    future=bundle(*changed)
    if not all(np.array_equal(z[:14000],y[:14000]) for z,y in zip(x,future)):
        raise ValueError('LZ_AUTHENTICATED_FUTURE_LEAK')
    mismatch=int((a!=b).sum())
    invalid=int(a[~x[3]].sum())
    silent=int(((np.abs(np.diff(x[0],axis=0)).sum(axis=2)>1e-12)&~x[1][1:]).sum())
    gross=float(np.abs(x[0]).sum(axis=(1,2)).max())
    counts={str(y):{name:int(a[start:end,k].sum()) for k,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    fail=(mismatch or invalid or silent or gross>.93+1e-9 or
          any(n<8 for year in counts.values() for n in year.values()))
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
