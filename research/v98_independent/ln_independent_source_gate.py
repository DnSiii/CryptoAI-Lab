#!/usr/bin/env python3
"""Independent LN entry replay; no reuse of LN decision generator for expected events."""
import argparse,json,numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from ln_sources import bundle,synthetic_causality,NAMES

def independent_entries(data):
    lc=np.log(data['c']);q=data['q'];starts=np.zeros((HOURS,3),bool);exp=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        if not np.all(q[t-23:t+1]>0) or any(not np.all(q[t-lag]>0) for lag in (0,24,72,168,336,720)):continue
        v336=lc[t]-lc[t-336];v168=lc[t]-lc[t-168];v72=lc[t]-lc[t-72];v24=lc[t]-lc[t-24]
        m336=np.median(v336);m168=np.median(v168);m72=np.median(v72);m24=np.median(v24)
        if (t-WARMUP)%72==0 and t>exp[0] and m336>.02 and np.any((v24<-.015)&(v72>-.04)):
            starts[t,0]=True;exp[0]=t+72
        if (t-WARMUP)%168==0 and t>exp[1] and m168>0 and np.ptp(v24)>.045 and np.min(v24)<-.005 and np.max(v24)>.005:
            starts[t,1]=True;exp[1]=t+168
        if (t-WARMUP)%72==0 and t>exp[2] and ((m168<0 and m72<-.015) or (m336<-.04 and m24>.02)):
            starts[t,2]=True;exp[2]=t+72
    return starts

def run(root):
    data=load(root);assert synthetic_causality()
    args=[data[x] for x in ('o','h','l','c','q','rate','event')];actual=bundle(*args)
    expected=independent_entries(data);mismatch=int(np.count_nonzero(actual[2]!=expected))
    counts={str(y):{name:int(actual[2][lo:hi,i].sum()) for i,name in enumerate(NAMES)} for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    altered=[x.copy() for x in args]
    for x in altered[:4]:x[14000:]*=1.7
    altered[4][14000:]*=3;altered[5][14000:]*=-1
    prefix=all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(actual,bundle(*altered)))
    silent=bool(np.any(np.any(np.diff(actual[0],axis=0)!=0,axis=2)&~actual[1][1:]))
    invalid=int(np.count_nonzero(actual[2][~actual[3]]));gross=float(np.abs(actual[0]).sum(axis=(1,2)).max())
    fails=[]
    if mismatch:fails.append('ENTRY_MISMATCH')
    if not prefix:fails.append('FUTURE_LEAK')
    if silent:fails.append('SILENT_UPDATE')
    if invalid:fails.append('INVALID_QUOTE_ENTRY')
    if gross>.94+1e-10:fails.append('GROSS_BREACH')
    for y in counts:
        for k,v in counts[y].items():
            if v<8:fails.append('LOW_'+y+'_'+k)
    return {'architecture':'LN','training_only':True,'hours':HOURS,'native_funding_events':int(data['event'].sum()),
            'counts':counts,'independent_entry_mismatches':mismatch,'future_prefix_pass':prefix,
            'silent_updates':silent,'invalid_quote_entries':invalid,'max_intended_gross':gross,
            'failures':fails,'decision':'PASS_SOURCE_ONLY' if not fails else 'REJECT_SOURCE_ONLY',
            'system_pnl_computed':False,'holdout_read':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
    r=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps(r,indent=2));raise SystemExit(0 if not r['failures'] else 2)
