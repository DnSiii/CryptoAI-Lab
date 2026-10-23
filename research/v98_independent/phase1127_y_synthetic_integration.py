#!/usr/bin/env python3
"""Y complete seven-slot 3-seed x 5-path SYNTHETIC survival gate, no historical PnL.

All decisions at t-1. Synthetic mark=synthetic close is a fixture ONLY;
authenticated native mark/funding is mandatory before historical economics.
"""
from __future__ import annotations
import json
import numpy as np
from test_phase1125_y_sevenslot_source import sample
from phase1125_y_sevenslot_source import compose_y,PATHS
from phase1126_y_hourly_ledger import execute_hour

SEEDS=(1127,1128,1129)
START=721

def run(seed=1127,n=2200):
    if n<=START+12:raise ValueError('Y1127_SHORT_SYNTHETIC_CALENDAR')
    f=sample(n,seed)
    op,hi,lo,cl,q,rate=[x.to_numpy(float) for x in f]
    paths,diag=compose_y(*f,capital_usd=1e6,diagnostics=True)
    out={}
    for name,targets in paths.items():
        weights=targets.to_numpy(float);cash=1e6;units=np.zeros(4)
        fail=None;active=stops=trades=0;paid=0.;fees=0.
        for t in range(START,n):
            down=np.maximum(0.,1-lo[t-336:t]/cl[t-337:t-1]).max(axis=0)
            up=np.maximum(0.,hi[t-336:t]/cl[t-337:t-1]-1).max(axis=0)
            funding_bound=np.abs(rate[t-720:t]).max(axis=0)
            x=execute_hour(cl[t-1],op[t],hi[t],lo[t],cl[t],units,
                weights[t-1],cash,down,up,funding_bound,q[t-1],.002,.002,
                rebalance=((t-1)%12==0),funding_rate=rate[t],
                funding_mark=cl[t],funding_event=np.full(4,t%8==0,bool))
            if not x['ok']:
                fail={'hour':t,'reason':x['reason']}
                break
            units=x['units'];cash=x['cash']
            active+=int(np.any(np.abs(units)>1e-12))
            stops+=int(x['basket_stop']);trades+=len(x['events'])
            paid+=x['funding_cash_delta'];fees+=x['fees']
        out[name]={'ok':fail is None,'first_failure':fail,
            'processed_hours':n-START if fail is None else fail['hour']-START,
            'active_hours':active,'basket_stops':stops,'events':trades,
            'fees_synthetic':fees,'funding_synthetic':paid}
    return {'seed':seed,'synthetic_only':True,'historical_pnl_computed':False,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'results':out,'diag':diag}

def receipt(seeds=SEEDS,n=2200):
    runs=[run(seed,n) for seed in seeds]
    passed=all(v['ok'] for r in runs for v in r['results'].values())
    return {'phase':1127,'decision':('PASS_Y_SYNTHETIC_ONLY_NOT_ECONOMIC'
        if passed else 'REJECT_Y_STRUCTURAL_SYNTHETIC'),
        'synthetic_only':True,'historical_pnl_computed':False,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'runs':runs}

if __name__=='__main__':
    r=receipt()
    with open('phase1127_y_synthetic_receipt.json','w') as f:
        json.dump(r,f,sort_keys=True,indent=2)
    print(json.dumps({'decision':r['decision'],
        'first_failures':{str(v['seed']):{k:x['first_failure']
        for k,x in v['results'].items()} for v in r['runs']}},sort_keys=True))
