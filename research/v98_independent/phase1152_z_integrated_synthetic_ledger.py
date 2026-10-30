#!/usr/bin/env python3
"""Z integrated ledger and FIFO cross-check on synthetic bars ONLY."""
import json
import numpy as np
import pandas as pd
from phase1146_z_inventory_ledger import execute_hour,FEE_TIERS,ORDERS
from phase1151_z_fifo_tradebook import TradeBook

def run(hours=300,seed=1152):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2023-01-01T00:00Z',periods=hours,freq='h')
    returns=rng.normal(0,.002,(hours,4))
    close=100*np.exp(np.cumsum(returns,axis=0))
    opening=np.vstack([close[0],close[:-1]])
    high=np.maximum(opening,close)*1.005
    low=np.minimum(opening,close)*.995
    rate=np.zeros((hours,4));rate[::8]=rng.uniform(-.0002,.0002,(len(rate[::8]),4))
    mark=np.stack((close*.999,close*1.001),axis=2)
    result=[];errors=[]
    for fee in FEE_TIERS.values():
      for order in ORDERS:
       for initial in (10000.,1e6,1e7):
        units=np.zeros(4);cash=initial;book=TradeBook(initial)
        filled=stops=0;fail=None
        for t in range(1,hours):
            target=np.array([.04,-.035,.02,-.015]) if (t-1)%12==0 else np.zeros(4)
            event=np.full(4,t%8==0,bool)
            try:
                x=execute_hour(close[t-1],opening[t],high[t],low[t],close[t],units,
                    target,cash,np.full(4,.15),np.full(4,.15),np.full(4,.001),
                    np.full(4,initial*100),fee=fee,order=order,
                    funding_rate=rate[t],funding_mark_bounds=mark[t],
                    funding_event=event,rebalance=(t-1)%12==0)
                if not x['ok']:
                    fail=x['reason'];break
                book.apply_hour(x['events'],x['funding_by_asset'],idx[t],order)
                if not np.allclose(book.units(),x['units'],atol=1e-8,rtol=0):
                    raise ArithmeticError('Z1152_FIFO_UNITS')
                if not np.isclose(book.total_pnl(close[t]),x['equity']-initial,
                    atol=max(1e-6,initial*1e-9),rtol=0):
                    raise ArithmeticError('Z1152_FIFO_NAV')
                cash=x['cash'];units=x['units'].copy()
                filled+=len(x['events']);stops+=int(x['basket_stop'])
            except Exception as exc:
                fail=type(exc).__name__+': '+str(exc);break
        result.append({'fee':fee,'order':order,'initial':initial,'hours':t,
            'fills':filled,'stops':stops,'failed':fail})
        if fail:errors.append(result[-1])
    out={'phase':1152,'cases':len(result),'passed':len(result)-len(errors),
        'failures':errors,'decision':'PASS_Z_INTEGRATED_SYNTHETIC_ONLY' if not errors
        else 'BLOCKED_Z_INTEGRATED_SYNTHETIC',
        'historical_pnl_computed':False,'validation_2025_read':False}
    print(json.dumps(out,sort_keys=True))
    return 0 if not errors else 2

if __name__=='__main__':raise SystemExit(run())
