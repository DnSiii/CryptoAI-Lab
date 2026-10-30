#!/usr/bin/env python3
"""AB 90-cell actual-NAV source->stateful executor synthetic gate. No PnL."""
import json
import numpy as np,pandas as pd
from phase1163_ab_sevenslot_intents import ASSETS,CAPITAL,compose_ab_intents
from phase1166_ab_stateful_executor import execute_hour,FEES,ORDERS

def source(n=950):
    rng=np.random.default_rng(1167)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    r=rng.normal(.0001,.004,(n,4));c=100*np.exp(np.cumsum(r,axis=0))
    o=np.vstack([c[0],c[:-1]]);h=np.maximum(o,c)*1.002;l=np.minimum(o,c)*.998
    q=np.full((n,4),1e8);f=np.zeros((n,4))
    f[::8]=rng.normal(0,.0001,(len(f[::8]),4))
    return tuple(pd.DataFrame(x,index=idx,columns=ASSETS) for x in (o,h,l,c,q,f))

def run():
    frames=source();op,hi,lo,cl,q,f=frames
    intents=compose_ab_intents(*frames)
    prev=cl.shift(1);down=(1-lo/prev).clip(lower=0).rolling(336).max().to_numpy()
    up=(hi/prev-1).clip(lower=0).rolling(336).max().to_numpy()
    fb=f.abs().rolling(720).max().to_numpy()
    qmin=q.rolling(336).min().to_numpy()
    arrays=[x.to_numpy(float) for x in frames]
    ret=np.log(cl).diff().fillna(0).to_numpy(float)
    cov=[None]*len(cl)
    for t in range(720,len(cl)):
        cov[t]=np.cov(ret[t-167:t+1],rowvar=False,ddof=0)*12
    results={};passed=0
    for (path,mode),frame in intents.items():
        alpha=frame.to_numpy(float)
        for tier,fee in FEES.items():
            for order in ORDERS:
                cash=CAPITAL[mode];units=np.zeros(4);reason=None;hours=0
                for t in range(721,len(cl)):
                    rate=arrays[5][t];event=rate!=0
                    mark=np.full((4,2),np.nan)
                    mark[event,0]=arrays[3][t,event]*.999
                    mark[event,1]=arrays[3][t,event]*1.001
                    result=execute_hour(arrays[3][t-1],arrays[0][t],arrays[1][t],
                        arrays[2][t],arrays[3][t],units,cash,alpha[t-1],cov[t-1],
                        down[t-1],up[t-1],fb[t-1],arrays[4][t-1],qmin[t-1],
                        fee=fee,order=order,funding_rate=rate,funding_mark_bounds=mark,
                        funding_event=event,rebalance=(t%12==0))
                    if not result['ok']:reason=result['reason'];break
                    units=result['units'];cash=result['cash'];hours+=1
                    assert np.isclose(result['equity'],cash+np.dot(units,arrays[3][t]),atol=1e-7)
                results[f'{path}__{mode}__{tier}__{order}']={'hours':hours,'reason':reason}
                passed+=reason is None
    reasons=sorted(set(x['reason'] for x in results.values())-{None})
    receipt={'phase':1167,'synthetic_only':True,'historical_pnl_computed':False,
        'cells':90,'full_path_cells':passed,'fail_closed_cells':90-passed,
        'failures':{r:sum(x['reason']==r for x in results.values()) for r in reasons}}
    print(json.dumps(receipt,sort_keys=True));return receipt
if __name__=='__main__':run()
