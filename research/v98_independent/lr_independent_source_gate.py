#!/usr/bin/env python3
"""Independent LR expected-entry replay, no candidate event-generator use."""
import argparse,json,numpy as np
from v98_clean4_training_reader import load
from lr_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay(d):
 p=np.log(d['c']);q=d['q'];fund=d['rate'];event=d['event']
 starts=np.zeros((HOURS,3),bool);expiry=np.full(3,-1,int)
 for t in range(WARMUP,HOURS):
  if np.any(q[t-23:t+1]<=0) or any(np.any(q[t-k]<=0) for k in (24,96,168,336,720)):continue
  if (t-WARMUP)%96:continue
  a=p[t]-p[t-720];b=p[t]-p[t-336];r168=p[t]-p[t-168];r24=p[t]-p[t-24]
  m168=np.median(r168);m24=np.median(r24)
  if t>expiry[0] and m168>0 and m24<0 and np.any(a>0):
   starts[t,0]=True;expiry[0]=t+96
  if t>expiry[1] and m168>0:
   assert np.all(event[t-48:t+1:8])
   means=np.mean(fund[t-48:t+1:8],axis=0);lo=np.argmin(means);hi=np.argmax(means)
   if means[hi]-means[lo]>.00015 and b[lo]>=b[hi]:
    starts[t,1]=True;expiry[1]=t+96
  if t>expiry[2] and m168<0 and m24!=0:
   starts[t,2]=True;expiry[2]=t+96
 return starts

def run(root):
 d=load(root);args=[d[k] for k in ('o','h','l','c','q','rate','event')];a=bundle(*args);expected=replay(d)
 assert synthetic_causality()
 altered=[z.copy() for z in args]
 for z in altered[:4]:z[14000:]*=1.7
 altered[4][14000:]*=3;altered[5][14000:]*=-1
 b=bundle(*altered)
 assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b))
 counts={str(y):{name:int(a[2][lo:hi,k].sum()) for k,name in enumerate(NAMES)} for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
 mismatch=int((a[2]!=expected).sum());invalid=int(a[2][~a[3]].sum())
 silent=int(((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>0)&~a[1][1:]).sum())
 gross=float(np.abs(a[0]).sum(axis=(1,2)).max())
 fail=bool(mismatch or invalid or silent or gross>.94+1e-9 or any(v<8 for y in counts.values() for v in y.values()))
 return {'counts':counts,'mismatch':mismatch,'invalid':invalid,'silent':silent,'max_gross':gross,'funding_events':int(d['event'].sum()),'decision':'REJECT_SOURCE_ONLY' if fail else 'PASS_SOURCE_ONLY'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
 r=run(a.root)
 if a.output:open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(0 if r['decision']=='PASS_SOURCE_ONLY' else 2)
