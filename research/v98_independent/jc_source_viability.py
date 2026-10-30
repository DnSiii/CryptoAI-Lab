#!/usr/bin/env python3
"""JC authenticated Clean-4 source-only gate; no historical PnL, 2025 or external benchmarks."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from jc_core_protected_marginal_sources import bundle,static_check,WARMUP,CLOCK,PATHS
OUT=Path(__file__).with_name('jc_source_viability.json')

def run():
    assert static_check()
    frames,manifest=load_official()
    targets,updates,regimes,valid,forecasts=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    if len(targets)!=HOURS:raise ValueError('JC_WRONG_TRAINING_HOURS')
    names=('opportunity','relative_value','stress_recovery')
    counts={y:{name:0 for name in names} for y in ('2023','2024')}
    regimes_by_year={y:{} for y in counts}
    invalid={y:0 for y in counts}
    maximum={}
    for t in range(WARMUP,HOURS,CLOCK):
        year='2023' if t<9504 else '2024'
        if not updates[t] or not np.all(np.isfinite(targets[t])):
            raise ValueError('JC_EPOCH_INVALID')
        gross=np.abs(targets[t]).sum(axis=1)
        if valid[t]:
            if not np.allclose(gross,1.,atol=1e-10):
                raise ValueError('JC_VALID_GROSS_NONCONSERVATION')
        elif not (np.allclose(gross,1.,atol=1e-10) or np.allclose(gross,0.,atol=1e-10)):
            raise ValueError('JC_QUARANTINED_GROSS_NONCONSERVATION')
        if not valid[t]:
            invalid[year]+=1
            if not np.allclose(targets[t],targets[t,0]):
                raise ValueError('JC_INVALID_QUOTE_NOT_QUARANTINED')
            continue
        if np.any(np.abs(targets[t,1:])>1.0000000001):
            raise ValueError('JC_ASSET_CAP')
        regimes_by_year[year][regimes[t]]=regimes_by_year[year].get(regimes[t],0)+1
        for j,name in enumerate(names,2):
            delta=float(np.abs(targets[t,1]-targets[t,j]).sum())
            maximum[name]=max(maximum.get(name,0.),delta)
            counts[year][name]+=int(delta>.025)
    viable=all(counts[y][name]>=8 for y in counts for name in names)
    result={'architecture':'JC','training_years':[2023,2024],
            'assets':['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT'],
            'source_manifest':manifest,'financed_forecast_perturbation_epochs':counts,
            'max_perturbation_l1':maximum,'invalid_quote_epochs':invalid,
            'regimes':regimes_by_year,
            'decision':'PASS_JC_SOURCE_ONLY_NOT_ECONOMIC' if viable else
                       'REJECT_JC_SOURCE_ONLY_INSUFFICIENT_FUNDED_FORECAST_EPOCHS',
            'validation_2025_read':False,'historical_system_pnl_computed':False,
            'external_benchmarks_used':False,'trading_authorized':False}
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,default=str)+'\n')
    print('JC_SOURCE_ONLY',result['decision'],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return result

if __name__=='__main__':
    run()
