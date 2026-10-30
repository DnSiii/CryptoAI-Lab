#!/usr/bin/env python3
"""Independent ML 2023/24 source-only audit; no economic PnL or future data."""
import argparse,json
import numpy as np
from v98_clean4_training_reader import load
from ml_sources import bundle,synthetic_causality,HOURS,WARMUP,NAMES,MINIMUM

def independent(d):
    lp=np.log(d['c'])
    desired=np.zeros((HOURS,4,4))
    events=np.zeros((HOURS,3),bool)
    refresh=np.zeros(HOURS,bool)
    inventory=np.zeros((4,4))
    expiry=np.full(3,-1,int)
    market_breadth=0
    residual_gap=0.
    for hour in range(WARMUP,HOURS):
        elapsed=hour-WARMUP
        ok=bool(np.min(d['q'][hour])>0)
        cooling=np.zeros(3,bool)
        for sleeve in range(3):
            if expiry[sleeve]>=0 and hour>=expiry[sleeve]:
                inventory[sleeve+1]=0
                expiry[sleeve]=-1
                cooling[sleeve]=True
        if elapsed%672==0:
            if not ok:raise ValueError('ML_INDEPENDENT_CORE_QUOTE_'+str(hour))
            inventory[0]=[.83 if lp[hour,0]>lp[hour-336,0] else .67,0,0,0]
            refresh[hour]=True
        if elapsed%168==0:
            rr168=lp[hour]-lp[hour-168]
            rr24=lp[hour]-lp[hour-24]
            market_breadth=sum(v>0 for v in rr168)
            returns=np.log(d['c'][hour-335:hour+1]/d['c'][hour-336:hour])
            btc=returns[:,0]
            variance=np.mean((btc-btc.mean())**2)
            beta=[]
            for j in range(1,4):
                alt=returns[:,j]
                cov=np.mean((btc-btc.mean())*(alt-alt.mean()))
                beta.append(cov/variance if variance>=1e-16/336 else 1.)
            resid=np.array([rr168[j]-beta[j-1]*rr168[0] for j in range(1,4)])
            residual_gap=float(np.ptp(resid))
            if ok and not cooling[0] and expiry[0]<0 and rr168[0]>0:
                rr336=lp[hour]-lp[hour-336]
                rr72=lp[hour]-lp[hour-72]
                leader=1+int(np.argmax(rr336[1:]))
                vol_recent=float(np.sum(d['q'][hour-71:hour+1,leader])/72)
                vol_past=float(np.sum(d['q'][hour-335:hour+1,leader])/336)
                if rr336[leader]>0 and rr72[leader]>0 and vol_past>0 and vol_recent/vol_past>1.15:
                    inventory[1,leader]=.11
                    expiry[0]=hour+168
                    events[hour,0]=True
            if ok and not cooling[2] and expiry[2]<0 and rr168[0]<0 and sum(rr24>0)>=3:
                inventory[3,0]=.08
                expiry[2]=hour+168
                events[hour,2]=True
            if elapsed%336==0 and ok and not cooling[1] and expiry[1]<0:
                laggard=1+int(np.argmin(resid))
                leader=1+int(np.argmax(resid))
                if laggard!=leader and residual_gap>.09 and rr168[0]>0:
                    inventory[2,laggard]=.045
                    inventory[2,leader]=-.045
                    expiry[1]=hour+336
                    events[hour,1]=True
        scaled=inventory.copy()
        factors=[1. if market_breadth>=3 else .6,
                 1. if residual_gap>=.10 else .6,
                 1. if market_breadth<=2 else .6]
        for k,factor in enumerate(factors,1):
            scaled[k]*=factor
        head=float(np.sum(np.abs(scaled[0])))
        rest=float(np.sum(np.abs(scaled[1:])))
        if rest>0:
            scaled[1:]*=min(1.,max(0.,(.89-head)/rest))
        desired[hour]=scaled
    return desired,events,refresh

def check(d):
    synthetic_causality()
    produced=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    weights,entries,forced=independent(d)
    werr=int(np.count_nonzero(np.abs(produced[0]-weights)>1e-11))
    eerr=int(np.count_nonzero(produced[2]!=entries))
    changed=(np.abs(np.diff(produced[0],axis=0)).sum(axis=2)>1e-12)
    silent=int(np.count_nonzero(changed&~produced[1][1:]))
    schedule=np.arange(WARMUP,HOURS,672)
    missing=[int(t) for t in schedule if not produced[1][t,0] or not forced[t]]
    counts={str(year):{name:int(produced[2][start:end,k].sum()) for k,name in enumerate(NAMES)}
        for year,start,end in ((2023,744,9504),(2024,9504,HOURS))}
    fail=[]
    if werr or eerr:fail.append('ML_INDEPENDENT_SOURCE_MISMATCH')
    if silent:fail.append('ML_SILENT_UPDATE')
    if missing:fail.append('ML_FORCED_REFRESH')
    if int(d['event'].sum())!=9144:fail.append('ML_NATIVE_FUNDING_COUNT')
    if np.max(np.sum(np.abs(produced[0]),axis=(1,2)))>.89+1e-10:fail.append('ML_GROSS')
    for year in ('2023','2024'):
        for k,name in enumerate(NAMES):
            if counts[year][name]<MINIMUM[k]:fail.append('ML_MINIMUM_'+year+'_'+name)
    return {'decision':'REJECT_SOURCE_ONLY' if fail else 'PASS_SOURCE_ONLY',
            'failures':fail,'independent_hourly_weight_mismatches':werr,
            'independent_entry_mismatches':eerr,'silent_weight_updates':silent,
            'forced_core_refreshes':int(forced.sum()),'preregistered_core_refreshes':len(schedule),
            'missed_core_refresh_hours':missing,
            'native_funding_events':int(d['event'].sum()),
            'entry_counts':counts,'minimums':dict(zip(NAMES,MINIMUM)),
            'synthetic_future_mutation_pass':True,
            'training_only':True,'pnl_computed':False,'holdout_accessed':False}
def run(root):return check(load(root))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output')
    args=p.parse_args()
    result=run(args.root)
    if args.output:
        with open(args.output,'w') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_SOURCE_ONLY' else 2)
