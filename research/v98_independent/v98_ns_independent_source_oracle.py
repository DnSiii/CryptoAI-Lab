#!/usr/bin/env python3
"""Independent NS source reconstruction from authenticated 2023-24 Clean4 only.
Does not import NS source, allocator, or executor while constructing expected weights.
"""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
def independent_replay(d):
    logp=np.log(d['c'])
    returns=np.vstack((np.zeros((1,4)),np.diff(logp,axis=0)))
    weights=np.zeros((HOURS,4,4))
    decisions=np.zeros(HOURS,bool)
    current=np.zeros((4,4))
    incumbent=None
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%336==0:
            if t%8 or not d['event'][t].all():raise ValueError('NS_INDEPENDENT_CALENDAR')
            w=np.zeros((4,4))
            sixweek=logp[t]-logp[t-336]
            leaders=sorted(range(4),key=lambda j:(-sixweek[j],j))
            lead=leaders[0]
            if incumbent is not None and sixweek[incumbent]>0 and sixweek[lead]-sixweek[incumbent]<=.10:
                lead=incumbent
            second=next(j for j in leaders if j!=lead)
            if sixweek[lead]>0:
                w[0,lead]=.42
                if sixweek[second]>0:w[0,second]=.24
            incumbent=lead if sixweek[lead]>0 else None
            r168=logp[t]-logp[t-168]
            opportunities=[j for j in range(4) if r168[j]>0 and d['rate'][t,j]<0]
            if opportunities:
                j=sorted(opportunities,key=lambda k:(-r168[k],k))[0]
                w[1,j]=.18
            r48=logp[t]-logp[t-48]
            relative=r48[1:]-r48[0]
            hi=sorted((1,2,3),key=lambda j:(-relative[j-1],j))[0]
            lo=sorted((1,2,3),key=lambda j:(relative[j-1],j))[0]
            if relative[hi-1]-relative[lo-1]>=.08:
                w[2,lo]=.12
                w[2,hi]=-.12
            btc72=float(logp[t,0]-logp[t-72,0])
            v24=float(np.std(returns[t-23:t+1,0]))
            v336=float(np.std(returns[t-335:t+1,0]))
            if btc72<-.07 and v24>v336:w[3,0]=-.16
            elif btc72<-.07 and logp[t,0]-logp[t-24,0]>0:w[3,0]=.12
            if sixweek[0]>0 and int(np.sum(sixweek>0))>=3:
                w[1]*=1.;w[2]*=.75;w[3]*=.5
            else:
                w[1]*=.75;w[2]*=1.;w[3]*=1.25
            current=w
            decisions[t]=True
        weights[t]=current
    return weights,decisions
def audit(d):
    expected,calendar=independent_replay(d)
    from ns_sources import bundle
    actual,updates,_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    mismatch=int(np.count_nonzero(np.abs(expected-actual)>1e-9))
    maximum=float(np.max(np.abs(expected-actual)))
    if mismatch or not np.array_equal(calendar,updates[:,0]):
        raise ValueError('NS_INDEPENDENT_SOURCE_MISMATCH_'+str((mismatch,maximum)))
    return {'decision':'PASS_NS_INDEPENDENT_RAW_SOURCE_53_DECISIONS_NOT_PNL',
        'hours_replayed':HOURS,'decisions':int(calendar.sum()),
        'raw_weight_mismatches':mismatch,'max_raw_weight_error':maximum,
        'training_only':True,'future_holdout_accessed':False,'pnl_computed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=audit(load(a.root))
    with open(a.output,'w') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps(out,indent=2,sort_keys=True))
