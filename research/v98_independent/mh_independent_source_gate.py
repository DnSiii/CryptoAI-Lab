#!/usr/bin/env python3
"""V98 MH independent source-only replay; PnL is deliberately inaccessible."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from mh_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES
MINIMUM=(6,4,3)
def replay(d):
    p=np.log(d['c'])
    q=d['q']
    out=np.zeros((HOURS,3),bool)
    expiry=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        expired=np.zeros(3,bool)
        for k in range(3):
            if expiry[k]>=0 and t>=expiry[k]:
                expiry[k]=-1;expired[k]=True
        if not np.all(q[t-335:t+1]>0):continue
        r336=p[t]-p[t-336]
        r168=p[t]-p[t-168]
        r72=p[t]-p[t-72]
        r24=p[t]-p[t-24]
        if (t-WARMUP)%168==0 and expiry[0]<0 and not expired[0]:
            if r336[3]>r336[0] and r72[3]>0:
                out[t,0]=True;expiry[0]=t+168
        if (t-WARMUP)%336==0 and expiry[1]<0 and not expired[1]:
            if r336[0]>r336[1] and r168[0]>0:
                out[t,1]=True;expiry[1]=t+336
        if (t-WARMUP)%168==0 and expiry[2]<0 and not expired[2]:
            if np.count_nonzero(r168<0)>=2 and r24[0]>0:
                out[t,2]=True;expiry[2]=t+168
    return out
def replay_weights(d):
    """Independent complete hourly four-sleeve weight ledger; not using bundle state."""
    p=np.log(d['c']);q=d['q']
    target=np.zeros((HOURS,4,4));raw=np.zeros((4,4))
    expiry=[-1,-1,-1]
    for t in range(WARMUP,HOURS):
        expired=[False,False,False]
        for k in range(3):
            if expiry[k]>=0 and t>=expiry[k]:
                raw[k+1,:]=0.;expiry[k]=-1;expired[k]=True
        if np.all(q[t-335:t+1]>0):
            r336=p[t]-p[t-336];r168=p[t]-p[t-168]
            if (t-WARMUP)%672==0:
                raw[0,:]=[.60,0.,0.,0.]
            if (t-WARMUP)%168==0 and not expired[0] and expiry[0]<0:
                if r336[3]>r336[0] and p[t,3]-p[t-72,3]>0:
                    raw[1,3]=.12;expiry[0]=t+168
            if (t-WARMUP)%336==0 and not expired[1] and expiry[1]<0:
                if r336[0]>r336[1] and r168[0]>0:
                    raw[2,0]=.05;raw[2,1]=-.05;expiry[1]=t+336
            if (t-WARMUP)%168==0 and not expired[2] and expiry[2]<0:
                if np.sum(r168<0)>=2 and p[t,0]-p[t-24,0]>0:
                    raw[3,0]=.06;expiry[2]=t+168
        intended=raw.copy()
        gross=np.sum(np.abs(intended))
        if gross>.88:
            core=np.sum(np.abs(intended[0]))
            optional=np.sum(np.abs(intended[1:]))
            if optional>0:intended[1:]*=(.88-core)/optional
        target[t]=intended
    return target
def check(d):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    a=bundle(*args);expected=replay(d);synthetic_causality()
    mutated=[x.copy() for x in args]
    for x in mutated[:4]:x[14000:]*=1.7
    mutated[4][14000:]*=3;mutated[5][14000:]*=-1
    b=bundle(*mutated)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MH_AUTHENTICATED_FUTURE_LEAK')
    entries=a[2]
    mismatch=int(np.count_nonzero(entries!=expected))
    weights_expected=replay_weights(d)
    weight_mismatch=int(np.count_nonzero(np.abs(weights_expected-a[0])>1e-12))
    invalid=int(np.count_nonzero(entries[~a[3]]))
    silent=int(np.count_nonzero((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]))
    gross=float(np.abs(a[0]).sum(axis=(1,2)).max())
    counts={str(y):{name:int(entries[start:end,k].sum()) for k,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    fail=bool(weight_mismatch or mismatch or invalid or silent or gross>.88+1e-9 or
              any(yr[name]<MINIMUM[k] for yr in counts.values() for k,name in enumerate(NAMES)))
    return {'decision':'REJECT_SOURCE_ONLY' if fail else 'PASS_SOURCE_ONLY',
            'counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
            'independent_entry_mismatch':mismatch,'independent_hourly_weight_mismatch':weight_mismatch,'invalid_entries':invalid,
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
