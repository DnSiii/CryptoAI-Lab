#!/usr/bin/env python3
"""AA Phase1158 independent pre-economic 5,000-case liquidity/risk oracle."""
import json
import numpy as np
from phase1156_aa_exit_reserve_governor import gate,allocate

def run(n=5000,seed=1158):
    rng=np.random.default_rng(seed);ok=blocked=0;errors={}
    for _ in range(n):
        capital=float(rng.choice([10000.,1e6,1e7]))
        q=rng.lognormal(15.,2.,4)
        qmin=q*rng.uniform(.001,1.,4)
        old=rng.uniform(-.4,.4,4)
        if rng.random()<.3:old=np.zeros(4)
        d=rng.uniform(.01,.65,4);u=rng.uniform(.01,1.2,4)
        f=rng.uniform(0,.01,4)
        mu=rng.normal(0,.015,4)
        A=rng.normal(0,.01,(4,4));cov=A@A.T
        try:
            w=allocate(mu,cov,old,d,u,f,q,qmin,capital)
            assert gate(w,old,d,u,f,q,qmin,capital)
            assert np.all(np.abs(w-old)<=.01*q/(capital*1.002)+1e-10)
            assert np.all(np.abs(w)*(1+u)<=.006*qmin/capital+1e-10)
            ok+=1
        except ValueError as e:
            code=str(e);errors[code]=errors.get(code,0)+1
            assert code in ('AA1156_UNEXECUTABLE_PRIOR_EXIT',
                            'AA1156_UNEXECUTABLE_QUANTIZATION'),code
            blocked+=1
    receipt={'phase':1158,'synthetic_only':True,'historical_pnl_computed':False,
        'cases':n,'valid_executable':ok,'fail_closed':blocked,'errors':errors,
        'all_invariants_pass':ok+blocked==n}
    print(json.dumps(receipt,sort_keys=True))
    return receipt
if __name__=='__main__':run()
