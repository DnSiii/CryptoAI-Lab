#!/usr/bin/env python3
"""LS independent event reconstruction; never imports candidate signal logic for expected starts."""
import argparse,json,numpy as np
from v98_clean4_training_reader import load
from ls_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay(d):
    p=np.log(d['c']);q=d['q'];rate=d['rate'];event=d['event']
    starts=np.zeros((HOURS,3),bool);expiry=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        expired=np.zeros(3,bool)
        for k in range(3):
            if expiry[k]>=0 and t>=expiry[k]:
                expiry[k]=-1;expired[k]=True
        if np.any(q[t-23:t+1]<=0) or any(np.any(q[t-k]<=0) for k in (24,72,168,672)):
            continue
        if (t-WARMUP)%168:continue
        r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        m168=float(np.median(r168));m72=float(np.median(r72));m24=float(np.median(r24))
        if not expired[0] and expiry[0]<0 and m168>0 and m72<0 and m24>0 and np.max(r168)>0:
            starts[t,0]=True;expiry[0]=t+168
        if not expired[1] and expiry[1]<0 and abs(m168)<=.035:
            if not np.all(event[t-48:t+1:8]):raise ValueError('LS_FUNDING_EVENT_MISSING')
            f=np.mean(rate[t-48:t+1:8],axis=0);lo=np.argmin(f);hi=np.argmax(f)
            if lo!=hi and f[hi]>f[lo] and abs(r168[lo]-r168[hi])<=.12:
                starts[t,1]=True;expiry[1]=t+168
        if not expired[2] and expiry[2]<0 and m168<0 and m24!=0:
            starts[t,2]=True;expiry[2]=t+168
    return starts

def check(d,require_activation=True):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    got=bundle(*args);want=replay(d)
    assert synthetic_causality()
    changed=[x.copy() for x in args]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    other=bundle(*changed)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(got,other)),'LS_AUTHENTICATED_FUTURE_LEAK'
    counts={str(y):{name:int(got[2][lo:hi,k].sum()) for k,name in enumerate(NAMES)} for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    mismatch=int((got[2]!=want).sum())
    invalid=int(got[2][~got[3]].sum())
    silent=int(((np.abs(np.diff(got[0],axis=0)).sum(axis=2)>0)&~got[1][1:]).sum())
    gross=float(np.abs(got[0]).sum(axis=(1,2)).max())
    failed=bool(mismatch or invalid or silent or gross>.91+1e-9 or (require_activation and any(v<8 for y in counts.values() for v in y.values())))
    return {'counts':counts,'mismatch':mismatch,'invalid':invalid,'silent':silent,'max_gross':gross,'funding_events':int(d['event'].sum()),'decision':'REJECT_SOURCE_ONLY' if failed else 'PASS_SOURCE_ONLY','training_only':True,'pnl_computed':False}

def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
    x=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(x,indent=2,sort_keys=True)+'\n')
    print(json.dumps(x,indent=2));raise SystemExit(0 if x['decision']=='PASS_SOURCE_ONLY' else 2)
