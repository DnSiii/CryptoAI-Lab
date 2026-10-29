#!/usr/bin/env python3
"""Independent LM entry-event replay, using no LM signal function for expected starts."""
import argparse,json,numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from lm_sources import bundle,synthetic_causality,NAMES

def independent_entries(data):
    lc=np.log(data['c']);q=data['q'];entries=np.zeros((HOURS,3),bool)
    exp=np.full(3,-1,int)
    for t in range(WARMUP,HOURS):
        if not np.all(q[t-23:t+1]>0):continue
        if any(not np.all(q[t-lag]>0) for lag in (0,24,72,168,336,504,672,720)):continue
        d336=lc[t]-lc[t-336];d168=lc[t]-lc[t-168]
        d72=lc[t]-lc[t-72];d24=lc[t]-lc[t-24]
        m336=np.median(d336);m168=np.median(d168);m72=np.median(d72);m24=np.median(d24)
        if (t-WARMUP)%168!=0:continue
        if t>exp[0] and m336>.04 and d168[0]>.025 and np.any((d168>.04)&(d24>0)):
            entries[t,0]=True;exp[0]=t+168
        if t>exp[1] and m336>.015 and np.ptp(d168)>.10 and np.max(d168)>.03 and np.min(d168)<0:
            entries[t,1]=True;exp[1]=t+168
        if t>exp[2] and ((m168<-.025 and m72<-.012) or (m336<-.03 and m24>.025)):
            entries[t,2]=True;exp[2]=t+168
    return entries

def run(root):
    data=load(root);assert synthetic_causality()
    args=[data[x] for x in ('o','h','l','c','q','rate','event')]
    actual=bundle(*args);expected=independent_entries(data)
    mismatches=int(np.count_nonzero(actual[2]!=expected))
    counts={str(y):{name:int(actual[2][lo:hi,i].sum()) for i,name in enumerate(NAMES)} for y,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    altered=[x.copy() for x in args]
    for a in altered[:4]:a[14000:]*=1.7
    altered[4][14000:]*=3;altered[5][14000:]*=-1
    future=bundle(*altered)
    prefix=all(np.array_equal(a[:14000],b[:14000]) for a,b in zip(actual,future))
    silent=bool(np.any(np.any(np.diff(actual[0],axis=0)!=0,axis=2)&~actual[1][1:]))
    max_gross=float(np.abs(actual[0]).sum(axis=(1,2)).max())
    bad_quotes=int(np.count_nonzero(actual[2][~actual[3]]))
    failures=[]
    if mismatches:failures.append('INDEPENDENT_ENTRY_MISMATCH')
    if not prefix:failures.append('FUTURE_LEAK')
    if silent:failures.append('SILENT_UPDATE')
    if bad_quotes:failures.append('INVALID_QUOTE_ENTRY')
    if max_gross>.94+1e-10:failures.append('INTENDED_GROSS')
    for year in counts:
        for name,n in counts[year].items():
            if n<8:failures.append('LOW_'+year+'_'+name)
    return {'architecture':'LM','training_only':True,'hours':HOURS,'funding_events':int(data['event'].sum()),
            'independent_entry_mismatches':mismatches,'future_mutation_prefix_pass':prefix,
            'silent_updates':silent,'invalid_quote_entries':bad_quotes,'max_intended_gross':max_gross,
            'counts':counts,'failures':failures,'decision':'PASS_SOURCE_ONLY' if not failures else 'REJECT_SOURCE_ONLY',
            'system_pnl_computed':False,'holdout_read':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output');a=p.parse_args()
    r=run(a.root)
    if a.output:open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps(r,indent=2));raise SystemExit(0 if not r['failures'] else 2)
