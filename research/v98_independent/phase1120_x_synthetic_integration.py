#!/usr/bin/env python3
"""X 3-seed 5-path 2200h SYNTHETIC composition; no historical PnL."""
import json
import numpy as np
from test_phase1118_x_sevenslot_source import sample
from phase1118_x_sevenslot_source import compose_x
from phase1119_x_hourly_ledger import execute_hour

def run(seed=1120,n=2200):
    f=sample(n,seed)
    op,hi,lo,cl,q,rate=[x.to_numpy(float) for x in f]
    paths,diag=compose_x(*f,capital_usd=1e6,diagnostics=True)
    out={}
    for name,targets in paths.items():
        weights=targets.to_numpy();cash=1e6;units=np.zeros(4)
        fail=None;active=stops=trades=0
        for t in range(721,n):
            d=np.maximum(0,1-lo[t-336:t]/cl[t-337:t-1]).max(axis=0)
            h=np.maximum(0,hi[t-336:t]/cl[t-337:t-1]-1).max(axis=0)
            x=execute_hour(cl[t-1],op[t],hi[t],lo[t],cl[t],units,
                weights[t-1],cash,d,h,q[t-1],.002,.002,
                rebalance=(t-1)%12==0,funding_rate=rate[t],
                funding_mark=cl[t],
                funding_event=np.full(4,t%8==0,dtype=bool))
            if not x['ok']:
                fail={'hour':t,'reason':x['reason']}
                break
            units=x['units'];cash=x['cash']
            active+=int(np.any(np.abs(units)>1e-12))
            stops+=int(x['basket_stop']);trades+=len(x['events'])
        out[name]={'ok':fail is None,'first_failure':fail,
            'processed_hours':n-721 if fail is None else fail['hour']-721,
            'active_hours':active,'basket_stops':stops,'events':trades}
    return {'seed':seed,'synthetic_only':True,
        'historical_pnl_computed':False,'results':out,'diag':diag}

if __name__=='__main__':
    runs=[run(s) for s in (1120,1121,1122)]
    decision='REJECT_X_STRUCTURAL_SYNTHETIC' if any(
        not v['ok'] for r in runs for v in r['results'].values()
    ) else 'PASS_X_SYNTHETIC_ONLY_NOT_ECONOMIC'
    report={'phase':1120,'decision':decision,'synthetic_only':True,
        'historical_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'runs':runs}
    with open('phase1120_x_synthetic_receipt.json','w') as f:
        json.dump(report,f,sort_keys=True,indent=2)
    print(json.dumps({'decision':decision,'first_failures':{
        str(r['seed']):{k:v['first_failure'] for k,v in r['results'].items()}
        for r in runs}},sort_keys=True))
