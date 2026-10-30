#!/usr/bin/env python3
"""AB 1000-case deterministic adverse actual-NAV survival oracle, synthetic only."""
import json
import numpy as np
from phase1165_ab_stateful_allocator import gate,allocate

def run(n=1000,seed=1169):
    rng=np.random.default_rng(seed);passed=blocked=0;reasons={}
    for _ in range(n):
        equity=float(rng.choice([1e4,1e6,1e7]))
        price=rng.lognormal(4.,1.,4)
        q=rng.lognormal(15.,2.,4)
        qmin=q*rng.uniform(.0001,1.,4)
        old=rng.uniform(-.3,.3,4)*equity/price
        if rng.random()<.3:old=np.zeros(4)
        down=rng.uniform(.01,.6,4);up=rng.uniform(.01,1.,4)
        funding=rng.uniform(0,.01,4)
        mu=rng.normal(0,.015,4)
        m=rng.normal(0,.01,(4,4));cov=m@m.T
        try:
            new=allocate(mu,cov,old,price,equity,down,up,funding,q,qmin)
            assert gate(new,old,price,equity,down,up,funding,q,qmin)
            assert np.all(np.abs(new-old)*price*1.002<=.005*q+1e-8)
            passed+=1
        except ValueError as exc:
            reason=str(exc)
            assert reason in ('AB1165_UNEXECUTABLE_SURVIVAL_REDUCTION',
                              'AB1165_FINAL_SURVIVAL'),reason
            reasons[reason]=reasons.get(reason,0)+1;blocked+=1
    receipt={'phase':1169,'synthetic_only':True,'historical_pnl_computed':False,
        'cases':n,'executable':passed,'fail_closed':blocked,'reasons':reasons,
        'all_invariants_pass':passed+blocked==n}
    print(json.dumps(receipt,sort_keys=True));return receipt
if __name__=='__main__':run()
