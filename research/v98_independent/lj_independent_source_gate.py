#!/usr/bin/env python3
"""Independent LJ source-entry replay without importing LJ source implementation."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from lj_sources import bundle,synthetic_causality,NAMES

def independent_entries(data):
    c=np.log(data['c']);q=data['q']
    starts=np.zeros((HOURS,3),bool);exp=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        if not np.all(q[t-23:t+1]>0):continue
        if not all(np.all(q[t-lag]>0) for lag in (0,24,72,144,168,336,720)):continue
        v168=c[t]-c[t-168];v72=c[t]-c[t-72];v24=c[t]-c[t-24]
        m168=np.median(v168);m72=np.median(v72);m24=np.median(v24)
        if (t-WARMUP)%72==0 and t>exp[0] and m168>.02 and np.any((v72>.025)&(v24>.005)):
            starts[t,0]=True;exp[0]=t+72
        if (t-WARMUP)%168==0 and t>exp[1] and m168>0 and np.ptp(v168)>.08:
            starts[t,1]=True;exp[1]=t+168
        if (t-WARMUP)%72==0 and t>exp[2]:
            if (m168<-.035 and m72<-.015) or (m168<0 and m24>.015):
                starts[t,2]=True;exp[2]=t+72
    return starts

def run(root):
    data=load(root);assert synthetic_causality()
    s=bundle(*(data[x] for x in ('o','h','l','c','q','rate','event')))
    intents,updates,entries,valid,regimes=s
    independent=independent_entries(data)
    diff=int(np.count_nonzero(entries!=independent))
    counts={year:{nm:int(entries[lo:hi,i].sum()) for i,nm in enumerate(NAMES)} for year,lo,hi in [('2023',744,9504),('2024',9504,HOURS)]}
    fails=[]
    if diff:fails.append('INDEPENDENT_ENTRY_MISMATCH')
    if np.any(entries[~valid]):fails.append('INVALID_QUOTE_ENTRY')
    if np.any(np.abs(intents).sum(axis=(1,2))>.94+1e-10):fails.append('GROSS_BREACH')
    if np.any(np.any(np.diff(intents,axis=0)!=0,axis=2)&~updates[1:]):fails.append('SILENT_ROW_UPDATE')
    for year in counts:
        for name,n in counts[year].items():
            if n<8:fails.append('LOW_'+year+'_'+name)
    # Authenticated source mutation beyond 14000h cannot change historical signals.
    altered=[data[x].copy() for x in ('o','h','l','c','q','rate','event')]
    for a in altered[:4]:a[14000:]*=1.7
    altered[4][14000:]*=3;altered[5][14000:]*=-1
    s2=bundle(*altered)
    if not all(np.array_equal(a[:14000],b[:14000]) for a,b in zip(s,s2)):
        fails.append('AUTHENTICATED_FUTURE_LEAK')
    return {'architecture':'LJ','training_only':True,'source_only':True,'system_pnl_computed':False,
        'hours':HOURS,'native_funding_events':int(data['event'].sum()),'independent_entry_mismatches':diff,
        'counts':counts,'max_intended_gross':float(np.abs(intents).sum(axis=(1,2)).max()),
        'failures':fails,'decision':'PASS_SOURCE_ONLY' if not fails else 'REJECT_SOURCE_ONLY'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
    out=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if not out['failures'] else 2)
