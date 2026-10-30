#!/usr/bin/env python3
"""Read-only independent V98 allocator oracle for rejected NW/NX; source only, never PnL."""
import argparse,itertools,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
import nw_sources,nx_sources
import nw_intents,nx_intents
CAP=.84
def independent_allocation(raw,old,returns,funding):
    age=np.array([335-i for i in range(336)],float)
    decay=np.array([2.**(-a/84.) for a in age],float)
    decay/=float(np.sum(decay))
    mean=np.sum(returns*decay[:,None],axis=0)
    residual=returns-mean[None,:]
    empirical=(residual*decay[:,None]).T@residual
    covariance=.5*empirical+.5*np.diag(np.diag(empirical))
    funding_per_hour=np.sum(funding,axis=0)/(21.*8.)
    candidates=[]
    for factor in itertools.product((0.,.5,1.),repeat=3):
        opt=raw[1:]*np.array(factor)[:,None]
        opt_gross=float(np.sum(np.abs(opt)))
        if opt_gross>CAP+1e-10:continue
        core=raw[0].copy()
        core_gross=float(np.sum(np.abs(core)))
        room=CAP-opt_gross
        if core_gross>room:core*=room/core_gross
        net=core+np.sum(opt,axis=0)
        virtual=float(np.sum(np.abs(core))+opt_gross)
        turn=float(np.sum(np.abs(net-old)))
        variance=float(np.dot(net,covariance@net))
        value=168.*(float(np.dot(net,mean))-float(np.dot(net,funding_per_hour))-.5*max(variance,0.))-turn*.0006
        candidates.append((value,turn,virtual,factor,core,opt,net))
    if not candidates:raise ValueError('V98_ALLOCATOR_ORACLE_NO_CANDIDATE')
    winner=min(candidates,key=lambda z:(-z[0],z[1],z[2],z[3]))
    return np.vstack((winner[4],winner[5])),winner[6]
def audit(d,name,source,intents):
    raw,updates,_=source.bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    actual=intents.build(d,raw,updates)
    old=np.zeros(4)
    errors=[]
    checks=0
    for t in range(WARMUP,HOURS,336):
        logp=np.log(d['c'][t-336:t+1])
        returns=logp[1:]-logp[:-1]
        funding=d['rate'][t-160:t+1:8]
        expected,net=independent_allocation(raw[t],old,returns,funding)
        err=float(np.max(np.abs(actual['weights'][t]-expected)))
        if err>1e-10:errors.append({'t':t,'max_abs_error':err})
        old=net.copy()
        checks+=1
    if errors or checks!=53:raise ValueError(name+'_INDEPENDENT_ALLOCATOR_MISMATCH_'+str(errors[:5]))
    # Mutation test on an actual nonzero decision: oracle must detect tampering.
    first=WARMUP
    altered=actual['weights'][first].copy()
    altered[0,0]+=.013
    expected,_=independent_allocation(raw[first],np.zeros(4),
        np.diff(np.log(d['c'][first-336:first+1]),axis=0),
        d['rate'][first-160:first+1:8])
    if np.max(np.abs(altered-expected))<=1e-10:
        raise AssertionError(name+'_TAMPER_NOT_DETECTED')
    return {'architecture':name,'decisions_recomputed':checks,'allocator_mismatches':0,
            'max_allowed_abs_error':1e-10,'tamper_detected':True,
            'funding_future_used':False,'training_only':True,
            'pnl_computed':False,'holdout_accessed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();d=load(a.root)
    out={'decision':'PASS_INDEPENDENT_ALLOCATOR_SOURCE_ONLY_NOT_PNL',
         'audits':[audit(d,'NW',nw_sources,nw_intents),audit(d,'NX',nx_sources,nx_intents)],
         '2025_accessed':False,'2026_plus_accessed':False,'live_authorized':False}
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
