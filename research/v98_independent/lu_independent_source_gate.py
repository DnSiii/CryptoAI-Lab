#!/usr/bin/env python3
"""LU independent state-event replay, source authentication and causal fail-closed gates."""
import argparse,json,numpy as np
from v98_clean4_training_reader import load
from lu_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay(d):
    p=np.log(d['c']);q=d['q'];r=d['rate'];e=d['event'];out=np.zeros((HOURS,3),bool);end=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        expired=np.zeros(3,bool)
        for k in range(3):
            if end[k]>=0 and t>=end[k]:end[k]=-1;expired[k]=True
        if (t-WARMUP)%72:continue
        if np.any(q[t-23:t+1]<=0) or any(np.any(q[t-k]<=0) for k in (24,168,504)):continue
        r168=p[t]-p[t-168];r24=p[t]-p[t-24]
        m168=float(np.median(r168));m24=float(np.median(r24))
        if not expired[0] and end[0]<0 and m168<0 and m24>0:
            out[t,0]=True;end[0]=t+72
        if not expired[1] and end[1]<0 and m168>0 and m24<0:
            if not np.all(e[t-48:t+1:8]):raise ValueError('LU_NATIVE_FUNDING_MISSING')
            f=np.mean(r[t-48:t+1:8],axis=0);lo=np.argmin(f);hi=np.argmax(f)
            if lo!=hi and f[hi]>f[lo]:out[t,1]=True;end[1]=t+72
        if not expired[2] and end[2]<0 and m168<0 and m24<0:
            out[t,2]=True;end[2]=t+72
    return out

def check(d,require_activation=True):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    a=bundle(*args);expected=replay(d);assert synthetic_causality()
    changed=[z.copy() for z in args]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LU_AUTHENTICATED_FUTURE_LEAK'
    counts={str(y):{name:int(a[2][lo:hi,k].sum()) for k,name in enumerate(NAMES)} for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    mismatch=int((a[2]!=expected).sum());invalid=int(a[2][~a[3]].sum())
    silent=int(((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>0)&~a[1][1:]).sum())
    gross=float(np.abs(a[0]).sum(axis=(1,2)).max())
    overlap=int((a[2].sum(axis=1)>1).sum())
    fail=bool(mismatch or invalid or silent or overlap or gross>.92+1e-9 or (require_activation and any(v<8 for y in counts.values() for v in y.values())))
    return {'counts':counts,'mismatch':mismatch,'invalid':invalid,'silent':silent,'overlap':overlap,'max_gross':gross,'funding_events':int(d['event'].sum()),'decision':'REJECT_SOURCE_ONLY' if fail else 'PASS_SOURCE_ONLY','pnl_computed':False,'training_only':True}

def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
    x=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(x,indent=2,sort_keys=True)+'\n')
    print(json.dumps(x,indent=2));raise SystemExit(0 if x['decision']=='PASS_SOURCE_ONLY' else 2)
