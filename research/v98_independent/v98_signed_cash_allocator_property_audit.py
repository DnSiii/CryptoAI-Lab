#!/usr/bin/env python3
"""Independent deterministic 10k-scenario physical gross property check; no PnL."""
import sys
import numpy as np
from v98_signed_cash_aware_allocator import authorize_signed

def run(seed=20261028,cases=10000):
    rng=np.random.default_rng(seed)
    valid=blocked=reversed=0
    for i in range(cases):
        p=rng.uniform(10,1000,4)
        nav=float(rng.uniform(100,100000))
        # Build independently signed rows with no opposing component signs.
        sign=rng.choice([-1.,0.,1.],size=4)
        rows=np.zeros((4,4))
        for j in range(4):
            for k in range(4):
                if rng.random()<.4:rows[k,j]=sign[j]*rng.uniform(0,nav/(20*p[j]))
        physical=rows.sum(axis=0)*rng.uniform(.5,1.5,4)
        k=int(rng.integers(0,4))
        if rng.random()<.08:
            j=int(rng.integers(0,4))
            if physical[j]:physical[j]=-physical[j]
        desired=rows[k].copy()
        for j in range(4):
            if rng.random()<.4:
                desired[j]=sign[j]*rng.uniform(0,nav/(8*p[j]))
        if rng.random()<.03:
            j=int(rng.integers(0,4))
            if rows[k,j]:desired[j]=-rows[k,j]
        occupied=np.maximum(np.abs(physical),np.abs(rows).sum(axis=0))
        before=float(occupied@p)
        room=max(0,.95*nav-before)
        try:out,meta=authorize_signed(rows,k,desired,nav,p,physical)
        except ValueError as exc:
            if 'REVERSAL' not in str(exc):raise
            reversed+=1;continue
        if meta['blocked']:
            assert np.array_equal(out,rows)
            blocked+=1;continue
        after=float(np.maximum(np.abs(physical),np.abs(out).sum(axis=0))@p)
        assert after<=before+room+1e-6,(i,before,after,room)
        assert np.array_equal(out[np.arange(4)!=k],rows[np.arange(4)!=k])
        assert np.all(np.abs(out[k])<=np.maximum(np.abs(rows[k]),np.abs(desired))+1e-9)
        valid+=1
    return {'cases':cases,'authorized':valid,'blocked_opposing':blocked,'rejected_reversal':reversed,'decision':'PASS_SIGNED_GROSS_FUZZ_NO_GHOST_COLLATERAL','seed':seed}
if __name__=='__main__':
    print(run())
