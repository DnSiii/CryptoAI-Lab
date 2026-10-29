#!/usr/bin/env python3
"""V98 MA independent source entry replay. Strictly source-only; no PnL."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from ma_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay(d):
    prices=np.log(d['c']);volume=d['q'];rates=d['rate']
    out=np.zeros((HOURS,3),bool)
    ends=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        p=prices[t]
        oneweek=p-prices[t-168]
        day=p-prices[t-24]
        accel=(p-prices[t-48])-oneweek/3.
        month=p-prices[t-672]
        expired=np.zeros(3,bool)
        for k in range(3):
            if ends[k]>=0 and t>=ends[k]:
                ends[k]=-1;expired[k]=True
        if not (np.all(volume[t-23:t+1]>0) and all(np.all(volume[t-k]>0) for k in (24,48,168,504,672))):
            continue
        breadth=int(np.sum(oneweek>0))
        if (t-WARMUP)%168==0 and ends[0]<0 and not expired[0] and breadth>=2:
            eligible=np.where(month>0)[0]
            if eligible.size and np.max(accel[eligible])>0:
                out[t,0]=True;ends[0]=t+168
        if (t-WARMUP)%336==0 and ends[1]<0 and not expired[1] and breadth>=2:
            last=(t//8)*8
            carry=np.sum(rates[last-56:last+1:8],axis=0)/8.
            if np.max(carry)>np.min(carry):
                out[t,1]=True;ends[1]=t+336
        if (t-WARMUP)%72==0 and ends[2]<0 and not expired[2]:
            if np.sum(oneweek<0)>=2 and np.sum(day>0)>=2:
                out[t,2]=True;ends[2]=t+144
    return out

def check(d):
    args=[d[k] for k in ('o','h','l','c','q','rate','event')]
    original=bundle(*args)
    expected=replay(d)
    synthetic_causality()
    future=[z.copy() for z in args]
    for z in future[:4]:z[14000:]*=1.7
    future[4][14000:]*=3
    future[5][14000:]*=-1
    mutated=bundle(*future)
    if not all(np.array_equal(a[:14000],b[:14000]) for a,b in zip(original,mutated)):
        raise ValueError('MA_AUTHENTICATED_FUTURE_LEAK')
    entries=original[2]
    mismatch=int((entries!=expected).sum())
    invalid=int(entries[~original[3]].sum())
    silent=int(((np.abs(np.diff(original[0],axis=0)).sum(axis=2)>1e-12)&~original[1][1:]).sum())
    gross=float(np.abs(original[0]).sum(axis=(1,2)).max())
    counts={str(y):{name:int(entries[start:end,k].sum()) for k,name in enumerate(NAMES)}
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
