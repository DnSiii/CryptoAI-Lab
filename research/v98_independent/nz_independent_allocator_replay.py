#!/usr/bin/env python3
"""NZ independent 53-decision shadow-history + allocator replay; NO market PnL."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from nz_sources import bundle
from nz_intents import build
from v98_causal_shadow_sleeve_independent_oracle import independent
def replay(d):
    raw,updates,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")))
    actual=build(d,raw,updates)
    weights=actual["weights"]
    old=np.zeros(4)
    decisions=0;ready_count=0;nonzero=0
    for t in range(WARMUP,HOURS,336):
        hist=np.zeros((4,4))
        ready=t-WARMUP>=4*336
        if ready:
            for k in range(4):
                start=t-(4-k)*336
                end=start+336
                if start<WARMUP or end>t:raise ValueError("NZ_ORACLE_FUTURE_WINDOW")
                for module in range(4):
                    target=raw[start,module]
                    gross=math.fsum(abs(float(z)) for z in target)
                    if gross==0:continue
                    changes=[float(d["c"][end,j])/float(d["o"][start+1,j])-1. for j in range(4)]
                    price=math.fsum(float(target[j])*changes[j] for j in range(4))
                    if price<=-1:raise ValueError("NZ_ORACLE_INSOLVENT_SHADOW")
                    hist[module,k]=math.log1p(price)/gross
        if not np.all(d["event"][t-160:t+1:8]):
            raise ValueError("NZ_ORACLE_FUNDING_CALENDAR")
        funding=d["rate"][t-160:t+1:8]
        oracle=independent(raw[t,0],raw[t,1:],old,hist,funding,ready=ready)
        factors=oracle[3]
        expected=raw[t]*np.asarray(factors)[:,None]
        error=float(np.max(np.abs(expected-weights[t])))
        if error>1e-9:raise ValueError("NZ_INDEPENDENT_ALLOCATOR_MISMATCH_"+str(t)+"_"+str(error))
        old=np.asarray(oracle[4],float)
        if float(np.max(np.abs(old-weights[t].sum(axis=0))))>1e-9:
            raise ValueError("NZ_INDEPENDENT_NET_MISMATCH_"+str(t))
        if np.abs(expected[1:]).sum()>1e-12:nonzero+=1
        ready_count+=int(ready);decisions+=1
    if decisions!=53 or ready_count!=49:
        raise ValueError("NZ_INDEPENDENT_REPLAY_INCOMPLETE")
    return {"decision":"PASS_INDEPENDENT_53_CAUSAL_SHADOW_AND_ALLOCATION_DECISIONS_NOT_PNL",
            "decisions":decisions,"ready_shadow_decisions":ready_count,
            "decisions_with_optional_exposure":nonzero,
            "shadow_windows_per_ready_decision":4,
            "allocator_action_mismatches":0,"funding_future_used":False,
            "2025_validation_accessed":False,"future_holdout_accessed":False,
            "live_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();r=replay(load(a.root))
    Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,indent=2,sort_keys=True))
