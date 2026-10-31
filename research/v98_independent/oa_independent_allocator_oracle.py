#!/usr/bin/env python3
"""Independent OA allocator oracle: reconstruct all 105 weekly choices from raw past data."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oa_sources import bundle
from oa_intents import build as original_build
def independent_targets(d,raw):
    targets={}
    ready_count=0
    for t in range(WARMUP,HOURS,168):
        chosen=raw[t].copy()*0.
        chosen[0]=raw[t,0]
        used=float(sum(abs(float(x)) for x in chosen.flat))
        ranked=[]
        if t>=WARMUP+1008:
            ready_count+=1
            means=[math.fsum(float(d['rate'][s,j]) for s in range(t-160,t+1,8))/21.
                   for j in range(4)]
            for module in (1,2,3):
                weight=raw[t,module]
                gross=math.fsum(abs(float(x)) for x in weight)
                if gross<=1e-12:continue
                log_returns=[]
                for k in range(6):
                    start=t-(6-k)*168
                    end=start+168
                    old=raw[start,module]
                    exposure=math.fsum(abs(float(x)) for x in old)
                    if exposure<=1e-12:log_returns.append(0.);continue
                    pnl=math.fsum(float(old[j])*(float(d['c'][end,j])/float(d['o'][start+1,j])-1.)
                                  for j in range(4))
                    if pnl<=-1:raise ValueError('OA_ORACLE_SHADOW_INSOLVENT')
                    log_returns.append(math.log1p(pnl)/exposure)
                historical=math.fsum(log_returns[k]*(k+1)/21. for k in range(6))
                carry=21*math.fsum(float(weight[j])*means[j] for j in range(4))/gross
                score=historical-carry-.0006
                if score>.002:ranked.append((score,module))
        ranked.sort(key=lambda item:(-item[0],item[1]))
        for score,module in ranked[:2]:
            remaining=.84-used
            if remaining<=1e-12:break
            gross=math.fsum(abs(float(x)) for x in raw[t,module])
            factor=min(1.,remaining/gross)
            chosen[module]=raw[t,module]*factor
            used+=gross*factor
        if used>.84+1e-9:raise ValueError('OA_ORACLE_GROSS')
        targets[t]=chosen
    return targets,ready_count
def verify(d):
    raw,updates,_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
    original=original_build(d,raw,updates)['weights']
    independent,ready=independent_targets(d,raw)
    mismatches=[]
    for t,expect in independent.items():
        err=float(np.max(np.abs(original[t]-expect)))
        if err>1e-9:mismatches.append((t,err))
    if mismatches:raise ValueError('OA_INDEPENDENT_ALLOCATOR_MISMATCH_'+str(mismatches[:5]))
    if len(independent)!=105 or ready!=99:raise ValueError('OA_ORACLE_COUNT')
    tampered=original[744].copy();tampered[0,0]+=.01
    if np.max(np.abs(tampered-independent[744]))<=1e-9:
        raise ValueError('OA_ORACLE_TAMPER_UNDETECTED')
    return {'decision':'PASS_INDEPENDENT_ALLOCATOR_105_DECISIONS_NOT_PNL',
            'decisions_replayed':len(independent),'shadow_ready_decisions':ready,
            'target_mismatches':0,'tamper_detected':True,
            'independent_formula':True,'future_prices_used':False,
            '2025_validation_accessed':False,'future_holdout_accessed':False,
            'live_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=verify(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
