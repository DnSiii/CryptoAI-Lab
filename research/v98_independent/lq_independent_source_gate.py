#!/usr/bin/env python3
"""LQ independent entry replay; does not import candidate source for expected events."""
import argparse,json,numpy as np
from v98_clean4_training_reader import load
from lq_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES

def replay(d):
 p=np.log(d['c']);v=d['q'];out=np.zeros((HOURS,3),bool);blocked=np.full(3,-1,dtype=int)
 for hour in range(WARMUP,HOURS):
  if np.any(v[hour-23:hour+1]<=0) or any(np.any(v[hour-k]<=0) for k in (24,72,168,336,720)):continue
  if (hour-WARMUP)%72:continue
  r24=p[hour]-p[hour-24];r72=p[hour]-p[hour-72];r168=p[hour]-p[hour-168]
  med168=float(np.median(r168));med24=float(np.median(r24))
  if hour>blocked[0] and med168>0 and (r72>0).sum()>=3:
   out[hour,0]=True;blocked[0]=hour+72
  if hour>blocked[1] and med168>0 and float(r72.max()-r72.min())>.05:
   out[hour,1]=True;blocked[1]=hour+72
  if hour>blocked[2] and med168<0 and (med24<-.015 or med24>.012):
   out[hour,2]=True;blocked[2]=hour+72
 return out

def run(root):
 d=load(root);args=[d[k] for k in ('o','h','l','c','q','rate','event')];a=bundle(*args)
 expected=replay(d);synthetic_causality()
 altered=[z.copy() for z in args]
 for z in altered[:4]:z[14000:]*=1.7
 altered[4][14000:]*=3;altered[5][14000:]*=-1
 b=bundle(*altered)
 assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b))
 counts={str(y):{name:int(a[2][lo:hi,k].sum()) for k,name in enumerate(NAMES)} for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
 mismatch=int((a[2]!=expected).sum());invalid=int(a[2][~a[3]].sum())
 silent=int(((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>0)&~a[1][1:]).sum())
 gross=float(np.abs(a[0]).sum(axis=(1,2)).max())
 fail=bool(mismatch or invalid or silent or gross>.92+1e-9 or any(v<8 for y in counts.values() for v in y.values()))
 return {'counts':counts,'mismatch':mismatch,'invalid':invalid,'silent':silent,'max_gross':gross,'funding_events':int(d['event'].sum()),'decision':'REJECT_SOURCE_ONLY' if fail else 'PASS_SOURCE_ONLY'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
 r=run(a.root)
 if a.output:open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(0 if r['decision']=='PASS_SOURCE_ONLY' else 2)
