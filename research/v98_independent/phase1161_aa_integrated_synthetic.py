#!/usr/bin/env python3
"""AA 90-cell synthetic source->t-1 targets->inventory integration, NO market PnL."""
import json
import numpy as np
import pandas as pd
from phase1157_aa_sevenslot_source import ASSETS,CAPITAL,compose_aa,prior_bounds
from phase1160_aa_inventory_executor import execute_hour,FEE_TIERS,FUNDING_ORDERS

def source(n=900):
    rng=np.random.default_rng(1161)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    r=rng.normal(.00005,.003,(n,4));c=100*np.exp(np.cumsum(r,axis=0))
    o=np.vstack([c[0],c[:-1]])
    h=np.maximum(o,c)*(1+rng.uniform(.0001,.002,(n,4)))
    l=np.minimum(o,c)*(1-rng.uniform(.0001,.002,(n,4)))
    q=np.full((n,4),1e8);f=np.zeros((n,4))
    f[::8]=rng.normal(0,.0001,(len(f[::8]),4))
    return tuple(pd.DataFrame(a,index=idx,columns=ASSETS) for a in (o,h,l,c,q,f))

def run():
    frames=source();op,hi,lo,cl,q,f=frames
    targets=compose_aa(*frames)
    d,u,fb=prior_bounds(cl,hi,lo,f)
    qmin=q.rolling(72).min().to_numpy()
    a=[x.to_numpy(float) for x in frames]
    results={};passed=blocked=0
    for (path,mode),frame in targets.items():
        weights=frame.to_numpy(float)
        for tier,fee in FEE_TIERS.items():
            for order in FUNDING_ORDERS:
                cash=CAPITAL[mode];units=np.zeros(4);nsteps=0;reason=None
                for t in range(721,len(cl)):
                    rate=a[5][t];event=rate!=0
                    bounds=np.full((4,2),np.nan)
                    bounds[event,0]=a[3][t,event]*.999
                    bounds[event,1]=a[3][t,event]*1.001
                    changed=not np.array_equal(weights[t-1],weights[t-2])
                    result=execute_hour(a[3][t-1],a[0][t],a[1][t],a[2][t],a[3][t],
                        units,weights[t-1],cash,d[t-1],u[t-1],fb[t-1],a[4][t-1],
                        qmin[t-1],fee=fee,order=order,funding_rate=rate,
                        funding_mark_bounds=bounds,funding_event=event,rebalance=changed)
                    if not result['ok']:
                        reason=result['reason'];break
                    units=result['units'];cash=result['cash'];nsteps+=1
                    assert np.isclose(result['equity'],cash+np.dot(units,a[3][t]),atol=1e-7)
                key=f'{path}__{mode}__{tier}__{order}'
                results[key]={'hours_executed':nsteps,'blocked_reason':reason}
                passed+=reason is None;blocked+=reason is not None
    assert len(results)==90 and passed+blocked==90
    reasons=sorted(set(x['blocked_reason'] for x in results.values())-{None})
    receipt={'phase':1161,'synthetic_only':True,'historical_pnl_computed':False,
        'cells':90,'full_path_cells':passed,'fail_closed_cells':blocked,
        'first_failure_counts':{r:sum(x['blocked_reason']==r for x in results.values()) for r in reasons},
        'by_cell':results,'promotion_eligible':False}
    print(json.dumps({k:v for k,v in receipt.items() if k!='by_cell'},sort_keys=True))
    return receipt
if __name__=='__main__':run()
