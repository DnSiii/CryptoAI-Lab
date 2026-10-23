#!/usr/bin/env python3
"""W end-to-end seeded SYNTHETIC portfolio safety; never historical PnL.

Three fixed seeds, 2200h, five ablation paths. Reject when any executable
hour violates prior bounds/capacity/post-stop constraints. No result tuning.
"""
import json
import numpy as np
from test_phase1111_w_sevenslot_source import sample
from phase1111_w_sevenslot_source import compose_w
from phase1112_w_atomic_ledger import execute_hour

def run(seed=1113,n=2200):
    frames=sample(n=n,seed=seed)
    op,hi,lo,cl,q,rate=[f.to_numpy(float) for f in frames]
    paths,diag=compose_w(*frames,capital_usd=1e6,diagnostics=True)
    results={}
    for name,targets in paths.items():
        w=targets.to_numpy(float)
        cash=1e6;units=np.zeros(4);fail=None;trades=0;active=0
        for t in range(721,n):
            prev=cl[t-1]
            d=np.maximum(0,1-lo[t-336:t]/cl[t-337:t-1]).max(axis=0)
            h=np.maximum(0,hi[t-336:t]/cl[t-337:t-1]-1).max(axis=0)
            evt=np.full(4,t%8==0,dtype=bool)
            out=execute_hour(prev,op[t],hi[t],lo[t],cl[t],units,w[t-1],
                cash,d,h,q[t-1],.002,.002,
                funding_rate=rate[t],funding_mark=cl[t],funding_event=evt,
                rebalance=(t-1)%12==0)
            if not out['ok']:
                fail={'hour':t,'reason':out['reason']}
                break
            cash=out['cash'];units=out['units']
            trades+=len(out['events'])
            active+=int(np.any(np.abs(units)>1e-10))
        results[name]={'ok':fail is None,'first_failure':fail,
            'processed_hours':(n-721 if fail is None else fail['hour']-721),
            'events':trades,'active_hours':active}
    return {'synthetic_only':True,'historical_pnl_computed':False,
        'seed':seed,'hours':n,'results':results,'diag':diag}

if __name__=='__main__':
    runs=[run(seed) for seed in (1113,1114,1115)]
    report={'phase':1113,'decision':'REJECT_W_STRUCTURAL_SYNTHETIC'
        if any(not v['ok'] for r in runs for v in r['results'].values())
        else 'PASS_W_SYNTHETIC_ONLY_NOT_ECONOMIC',
        'historical_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'runs':runs}
    with open('phase1113_w_synthetic_receipt.json','w') as f:
        json.dump(report,f,sort_keys=True,indent=2)
    print(json.dumps({'decision':report['decision'],
        'first_failures':{str(r['seed']):{k:v['first_failure']
        for k,v in r['results'].items()} for r in runs}},sort_keys=True))
