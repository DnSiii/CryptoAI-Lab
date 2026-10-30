#!/usr/bin/env python3
"""Z source-only adversarial structural oracle; no historical data or PnL."""
import json
import numpy as np
from phase1143_z_sevenslot_source import (
    optimize_joint,corner_gate,ASSET_CAP,GROSS_CAP,NET_CAP,
    PARTICIPATION,SLIPPAGE)

def run(cases=1000,seed=1144):
    rng=np.random.default_rng(seed)
    passed=blocked=0;violations=[]
    for i in range(cases):
        alpha=rng.uniform(-.06,.06,4)
        m=rng.normal(size=(4,4))
        cov=m.T@m*.0002
        old=np.zeros(4)
        dn=rng.uniform(.01,.25,4)
        up=rng.uniform(.01,.35,4)
        funding=rng.uniform(0,.003,4)
        quote=10**rng.uniform(3,9,4)
        mode=10**rng.uniform(4,7)
        try:
            w=optimize_joint(alpha,cov,old,dn,up,funding,quote,mode)
            cap=.8*PARTICIPATION*quote/(mode*(1+SLIPPAGE))
            ok=(corner_gate(w,dn,up,funding,old) and
                np.max(np.abs(w))<=ASSET_CAP+1e-10 and
                np.sum(np.abs(w))<=GROSS_CAP+1e-10 and
                abs(w.sum())<=NET_CAP+1e-10 and
                np.all(np.abs(w-old)<=cap+1e-10))
            if not ok:violations.append({'case':i,'weights':w.tolist()})
            else:passed+=1
        except ValueError as e:
            if str(e)=='Z1143_PREVIOUS_INVENTORY_INFEASIBLE':blocked+=1
            else:violations.append({'case':i,'error':str(e)})
        except Exception as e:
            violations.append({'case':i,'error':type(e).__name__+':'+str(e)})
    out={'phase':1144,'cases':cases,'passed':passed,'fail_closed':blocked,
         'violations':violations[:10],'decision':('PASS_Z_STRUCTURAL_SYNTHETIC_ONLY'
           if not violations and passed+blocked==cases else 'BLOCKED_Z_SYNTHETIC'),
         'historical_pnl_computed':False,'validation_2025_read':False,
         'external_benchmarks_used':False}
    print(json.dumps(out,sort_keys=True,allow_nan=False))
    return 0 if not violations else 2

if __name__=='__main__':raise SystemExit(run())
