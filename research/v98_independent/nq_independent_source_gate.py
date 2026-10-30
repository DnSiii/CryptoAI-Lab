#!/usr/bin/env python3
"""V98 NQ independent source-only replay; NO adaptive shadow PnL in source gate."""
import argparse,json,math
import numpy as np
from v98_clean4_training_reader import load
from nq_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def replay(d):
    c,q,r,e=[d[k] for k in ('c','q','rate','event')]
    p=np.log(c)
    weights=np.zeros((HOURS,4,4))
    activity=np.zeros((HOURS,3),bool)
    decisions=np.zeros(HOURS,bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%168==0:
            if np.any(q[t]<=0):raise ValueError('NQ_ORACLE_ZERO_QUOTE')
            one=p[t]-p[t-168]
            day=p[t]-p[t-24]
            held[:]=0.
            for j,v in enumerate((.20,.15,.12,.13)):
                if one[j]>0:held[0,j]=v
            std=np.maximum(np.std(np.diff(p[t-168:t+1],axis=0),axis=0),.01)
            score=day[1:]/std[1:]
            jhi=sorted((1,2,3),key=lambda j:(-score[j-1],j))[0]
            jlo=sorted((1,2,3),key=lambda j:(score[j-1],j))[0]
            if score[jhi-1]>0:held[1,jhi]=.14
            else:held[1,jlo]=-.14
            if t%8 or not e[t-160:t+1:8].all():
                raise ValueError('NQ_ORACLE_FUNDING_CALENDAR')
            carry=np.mean(r[t-160:t+1:8],axis=0)
            ranks=sorted(range(4),key=lambda j:(carry[j],j))
            held[2,ranks[0]]=.06;held[2,ranks[-1]]=-.06
            peak=max(c[t-168:t+1,0])
            if c[t,0]/peak-1<=-.06:
                choices=[j for j in (1,2,3) if one[j]>0]
                chosen=max(choices,key=lambda j:(one[j],-j)) if choices else 0
                held[3,chosen]=-.10
            else:held[3,0]=.07
            on=one[0]>0 and int((one>0).sum())>=2
            held[1:]*=np.array([1.,.8,.7] if on else [.7,1.,1.])[:,None]
            room=.84-np.abs(held[0]).sum()
            optional=np.abs(held[1:]).sum()
            if optional>room and optional>0:held[1:]*=room/optional
            activity[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
            decisions[t]=True
        weights[t]=held
    return weights,activity,decisions

def check(d):
    synthetic_causality()
    raw,updates,activity=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    independent,ind_activity,decisions=replay(d)
    mismatch=int(np.count_nonzero(np.abs(raw-independent)>1e-9))
    amismatch=int(np.count_nonzero(activity!=ind_activity))
    silent=int(np.count_nonzero((np.abs(np.diff(raw,axis=0)).sum(axis=(2,3))>1e-12)&~updates[1:,0]))
    counts={str(year):{name:int(activity[lo:hi,i].sum()) for i,name in enumerate(NAMES)}
            for year,lo,hi in ((2023,744,9504),(2024,9504,HOURS))}
    failures=[]
    if mismatch or amismatch:failures.append('NQ_INDEPENDENT_SOURCE_MISMATCH')
    if silent:failures.append('NQ_SILENT_WEIGHT_CHANGE')
    if not np.array_equal(updates[:,0],decisions):failures.append('NQ_MISSING_OR_EXTRA_WEEKLY')
    if int(d['event'].sum())!=9144:failures.append('NQ_FUNDING_COUNT')
    if np.abs(raw).sum(axis=(2,3)).max()>.84+1e-10:failures.append('NQ_GROSS')
    for year in ('2023','2024'):
        for i,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[i]:failures.append('NQ_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if failures else 'PASS_SOURCE_ONLY',
        'failures':failures,'hourly_raw_weight_mismatches':mismatch,
        'active_week_mismatches':amismatch,'silent_updates':silent,
        'weekly_decisions':int(decisions.sum()),
        'funding_events':int(d['event'].sum()),'active_week_counts':counts,
        'synthetic_future_mutation_pass':True,'pnl_computed':False,
        'training_only':True,'holdout_accessed':False}

def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output')
    a=p.parse_args();out=run(a.root)
    if a.output:
        with open(a.output,'w') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['decision']=='PASS_SOURCE_ONLY' else 2)
