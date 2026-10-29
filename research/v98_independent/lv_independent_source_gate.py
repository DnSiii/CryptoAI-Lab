#!/usr/bin/env python3
"""Independent LV source/event replay and authenticated causal gate, no PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from lv_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay_entries(d):
    p=np.log(d['c']);q=d['q'];r=d['rate'];e=d['event']
    out=np.zeros((HOURS,3),bool);end=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        expired=np.zeros(3,bool)
        for k in range(3):
            if end[k]>=0 and t>=end[k]:
                end[k]=-1;expired[k]=True
        if (t-WARMUP)%168:continue
        if np.any(q[t-23:t+1]<=0) or any(np.any(q[t-k]<=0) for k in (168,336,672)):
            continue
        r168=p[t]-p[t-168];r336=p[t]-p[t-336];r24=p[t]-p[t-24]
        m336=float(np.median(r336));btc24=float(r24[0]);btc168=float(r168[0])
        if not expired[0] and end[0]<0 and m336>0 and btc24>0 and np.max(r168)>0:
            out[t,0]=True;end[0]=t+168
        if not expired[1] and end[1]<0 and np.ptp(r168)>=.06:
            if not np.all(e[t-48:t+1:8]):raise ValueError('LV_REPLAY_FUNDING_MISSING')
            f=np.mean(r[t-48:t+1:8],axis=0)
            if int(np.argmin(f))!=int(np.argmax(f)) and np.ptp(f)>=.00010:
                out[t,1]=True;end[1]=t+168
        if not expired[2] and end[2]<0 and btc168<0 and btc24<0:
            out[t,2]=True;end[2]=t+168
    return out

def check(d):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    x=bundle(*args);a=x[2];b=replay_entries(d)
    synthetic_causality()
    changed=[z.copy() for z in args]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    future=bundle(*changed)
    if not all(np.array_equal(z[:14000],y[:14000]) for z,y in zip(x,future)):
        raise ValueError('LV_AUTHENTICATED_FUTURE_LEAK')
    mismatch=int((a!=b).sum())
    invalid=int(a[~x[3]].sum())
    silent=int(((np.abs(np.diff(x[0],axis=0)).sum(axis=2)>0)&~x[1][1:]).sum())
    gross=float(np.abs(x[0]).sum(axis=(1,2)).max())
    counts={str(y):{name:int(a[start:end,k].sum()) for k,name in enumerate(NAMES)}
            for y,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    decision='REJECT_SOURCE_ONLY' if (mismatch or invalid or silent or gross>.92+1e-9 or
            any(n<8 for year in counts.values() for n in year.values())) else 'PASS_SOURCE_ONLY'
    return {'decision':decision,'counts':counts,'independent_entry_mismatch':mismatch,
            'invalid_entries':invalid,'silent_updates':silent,'intended_gross_peak':gross,
            'funding_events':int(d['event'].sum()),'training_only':True,
            'pnl_computed':False,'holdout_read':False,'synthetic_causality':True}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
    z=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(z,indent=2,sort_keys=True)+'\n')
    print(json.dumps(z,indent=2))
    raise SystemExit(0 if z['decision']=='PASS_SOURCE_ONLY' else 2)
