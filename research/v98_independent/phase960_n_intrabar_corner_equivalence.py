#!/usr/bin/env python3
"""V98 Independent Phase960: mathematical audit of the frozen risk kernel.

No price source, funding, PnL, future validation or benchmark access.
For long-only quantities u>=0 and cash c (possibly negative), with equity
E=c+sum(u_i p_i)>0, gross G=sum(u_i p_i)/E and asset A_j=u_j p_j/E:

- dG/dp_i = u_i*c/E**2, constant sign across assets. Its worst
  attainable value is all-low if cash<0 or all-high if cash>=0.
- dA_j/dp_i = -u_j*p_j*u_i/E**2 <=0 for i!=j, so others at low.
- dA_j/dp_j = u_j*(c+sum_{i!=j}u_i*p_i)/E**2, constant sign in p_j.
  Its maximum is either all-low or j-high/others-low.
- Equity is minimized at all-low.

Thus the existing six corners (all-low, all-high, four one-high)
are exhaustive for long-only, fixed cash and price-independent quantities.
The 16-corner audit remains useful as an independent check.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase876_k_funded_ledger import CAP_ASSET, CAP_GROSS

ROOT=Path(__file__).resolve().parent


def audit(seed=960, samples=250_000):
    rng=np.random.default_rng(seed)
    units=rng.lognormal(mean=0.,sigma=2.,size=(samples,4))
    low=rng.lognormal(mean=0.,sigma=1.,size=(samples,4))
    high=low*rng.uniform(1.,3.,size=(samples,4))
    vlow=units*low
    # Mixed positive/negative cash, with some states near the leverage boundary.
    cash=vlow.sum(axis=1)*rng.uniform(-.95,2.,size=samples)
    corners=[]
    for mask in range(16):
        prices=np.where([(mask>>i)&1 for i in range(4)],high,low)
        value=units*prices
        equity=cash+value.sum(axis=1)
        gross=np.divide(value.sum(axis=1),equity,out=np.full(samples,np.inf),where=equity>0)
        asset=np.divide(value.max(axis=1),equity,out=np.full(samples,np.inf),where=equity>0)
        corners.append((equity>0)&(gross<=CAP_GROSS+1e-9)&(asset<=CAP_ASSET+1e-9))
    full=np.logical_and.reduce(corners)
    six=np.logical_and.reduce([corners[i] for i in (0,15,1,2,4,8)])
    mismatch=int(np.count_nonzero(full!=six))
    if mismatch:
        raise AssertionError(f'frozen six-corner kernel misses {mismatch} 16-corner violations')
    return {'phase':960,'decision':'PASS_SIX_CORNERS_EQUIVALENT_TO_ALL_16_FOR_LONG_ONLY',
            'seed':seed,'samples':samples,'full16_pass':int(full.sum()),
            'full16_fail':int((~full).sum()),'six_vs_16_mismatches':mismatch,
            'mathematical_scope':'long_only_fixed_units_cash_and_ohlc_bounds',
            'historical_pnl_computed':False,'external_benchmarks_used':False,
            'validation_2025_read':False,'source_files_accessed':False}


if __name__=='__main__':
    result=audit()
    (ROOT/'phase960_n_intrabar_corner_equivalence_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
