#!/usr/bin/env python3
"""V98 NR independently reconstruct raw seven-slot weekly source from pinned 2023-24 bars.
No imports of NR signal helpers, allocator or physical executor. No PnL.
"""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
def independent_replay(d):
    price=np.log(d['c'])
    ret=np.vstack((np.zeros((1,4)),np.diff(price,axis=0)))
    expected=np.zeros((HOURS,4,4))
    events=np.zeros(HOURS,bool)
    prev=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%168==0:
            if (t%8)!=0 or not d['event'][t].all():raise ValueError('NR_ORACLE_WEEKLY_FUNDING_CALENDAR')
            w=np.zeros((4,4))
            recent=ret[t-335:t+1]
            vol=recent.std(axis=0)
            r48=price[t]-price[t-48]
            r336=price[t]-price[t-336]
            qualifying=[j for j in range(4) if r48[j]>0 and r336[j]>0]
            budget=.70
            while qualifying and budget>1e-12:
                scores={j:1/max(float(vol[j]),.001) for j in qualifying}
                total=sum(scores.values())
                increments={j:budget*scores[j]/total for j in qualifying}
                capped=[j for j in qualifying if increments[j]>=.28-w[0,j]-1e-12]
                if capped:
                    for j in capped:
                        amt=max(0.,.28-w[0,j])
                        w[0,j]+=amt
                        budget-=amt
                    qualifying=[j for j in qualifying if j not in capped]
                else:
                    for j in qualifying:w[0,j]+=increments[j]
                    budget=0.
            day=price[t]-price[t-24]
            vol24=d['q'][t-23:t+1].sum(axis=0)
            previous=np.stack([d['q'][t-359+24*k:t-335+24*k].sum(axis=0)
                               for k in range(14)],axis=0)
            typical=np.median(previous,axis=0)
            qualifying=[j for j in range(4)
                        if d['c'][t,j]>d['h'][t-72:t,j].max()
                        and vol24[j]>typical[j] and day[j]>0]
            if qualifying:
                j=sorted(qualifying,key=lambda k:(-day[k],k))[0]
                w[1,j]=.18
            b=recent[:,0]
            b0=b-b.mean()
            den=float(np.sum(b0*b0))
            beta=[]
            for j in (1,2,3):
                a=recent[:,j]
                beta.append(float(np.clip(np.sum(b0*(a-a.mean()))/den,-1.5,1.5)) if den>1e-18 else 0.)
            r72=price[t]-price[t-72]
            spread=r72[1:]-np.array(beta)*r72[0]
            first=sorted((1,2,3),key=lambda j:(-spread[j-1],j))[0]
            last=sorted((1,2,3),key=lambda j:(spread[j-1],j))[0]
            if spread[first-1]-spread[last-1]>=.015:
                w[2,first]=.12;w[2,last]=-.12
            short_vol=float(ret[t-47:t+1,0].std())
            long_vol=max(float(vol[0]),1e-6)
            if r48[0]<-.045 and price[t,0]-price[t-12,0]>0:
                w[3,0]=.14
            elif short_vol>1.5*long_vol and r48[0]<0:
                w[3,0]=-.12
            r168=price[t]-price[t-168]
            if r168[0]>0 and np.count_nonzero(r168>0)>=3:
                w[1]*=1.25;w[2]*=.75;w[3]*=.5
            else:
                w[1]*=.75;w[2]*=1.;w[3]*=1.25
            prev=w
            events[t]=True
        expected[t]=prev
    return expected,events

def audit(d):
    # Import only after independent construction; do not call its helpers in oracle.
    independently,calendar=independent_replay(d)
    from nr_sources import bundle
    original,updates,activity=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    delta=np.abs(independently-original)
    maxerr=float(delta.max())
    mismatches=int(np.count_nonzero(delta>1e-9))
    if mismatches or not np.array_equal(calendar,updates[:,0]):
        raise ValueError('NR_INDEPENDENT_RAW_SOURCE_MISMATCH_'+str((mismatches,maxerr)))
    return {'decision':'PASS_NR_INDEPENDENT_RAW_SOURCE_105_WEEKLY_NOT_PNL',
        'hours_replayed':HOURS,'weekly_decisions':int(calendar.sum()),
        'raw_weight_mismatches':mismatches,'max_raw_weight_error':maxerr,
        'original_source_imported_only_for_comparison':True,
        'no_future_pnl_or_holdout_accessed':True,'training_only':True}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=audit(load(a.root))
    with open(a.output,'w') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps(out,indent=2,sort_keys=True))
