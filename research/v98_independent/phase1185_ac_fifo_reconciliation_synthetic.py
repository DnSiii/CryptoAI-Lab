#!/usr/bin/env python3
"""AC 90-cell synthetic read-only FIFO observer, every-hour NAV reconciliation."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1174_ac_discrete_intents import compose_intents, PATHS, MODES
from phase1177_ac_actual_open_executor import execute_hour, funding_cash, FEES, ORDERS
from phase1184_ac_fifo_tradebook import FIFOTradebook
from test_phase1174_ac_discrete_intents import sample

CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}
OUT=Path(__file__).resolve().parent/'phase1185_ac_fifo_synthetic_receipt.json'


def run():
    frames=sample();source=compose_intents(*frames)
    op,hi,lo,cl,q,_=[f.to_numpy(float) for f in frames]
    returns=np.diff(np.log(cl),axis=0)
    cells=[]
    for path in PATHS:
        for mode in MODES:
            for fee_name,fee in FEES.items():
                for order in ORDERS:
                    capital=CAPITAL[mode];cash=capital;units=np.zeros(4)
                    book=FIFOTradebook(capital);error=None;count=0
                    for t in range(900,996):
                        cov=np.cov(returns[t-337:t-1].T,ddof=0)*24+np.eye(4)*1e-8
                        event=np.full(4,t%8==0,bool)
                        rate=np.array([(.0001 if ((t//8+j)%2==0) else -.0001)
                                       if event[j] else 0. for j in range(4)])
                        bounds=np.column_stack((cl[t]*.99,cl[t]*1.01))
                        r=execute_hour(prior=cl[t-1],opening=op[t],high=hi[t],low=lo[t],
                            closing=cl[t],cash=cash,old_units=units,
                            scores=source[path,mode][t-1],cov24=cov,
                            down=np.full(4,.25),up=np.full(4,.30),
                            funding_bound=np.full(4,.001),prior_quote=q[t-1],
                            min336_quote=np.min(q[t-336:t],axis=0),fee=fee,
                            funding_rate=rate,mark_bounds=bounds,funding_event=event,
                            order=order,rebalance=t%12==0)
                        if not r['ok']:
                            error='EXECUTION_'+str(r['reason']);break
                        delta=r['units']-units
                        fill=op[t]*(1+np.sign(delta)*.002)
                        flow_units=units if order=='carried_before_fill' else r['units']
                        flows=funding_cash(flow_units,rate,bounds,event)
                        if r['gap']:flows=np.minimum(flows,0.)
                        if order=='carried_before_fill':
                            for j in range(4):book.apply_funding(j,float(flows[j]))
                        for j in range(4):
                            book.trade(j,float(delta[j]),float(fill[j]),
                                       float(fee*abs(delta[j])*fill[j]))
                        if order=='new_after_fill':
                            for j in range(4):book.apply_funding(j,float(flows[j]))
                        try:book.reconcile(r['cash'],r['units'],cl[t])
                        except ValueError as exc:
                            error=str(exc);break
                        cash=r['cash'];units=r['units'];count+=1
                    cells.append({'path':path,'mode':mode,'fee':fee_name,
                                  'order':order,'hours_reconciled':count,
                                  'passed':error is None and count==96,
                                  'reason':error,'trade_metrics':book.trade_metrics()})
    passed=sum(c['passed'] for c in cells)
    result={'phase':1185,'decision':'PASS_AC_90_FIFO_SYNTHETIC_RECONCILIATION' if passed==90
            else 'FAIL_AC_FIFO_SYNTHETIC_RECONCILIATION',
            'cells_attempted':len(cells),'cells_passed':passed,
            'historical_pnl_computed':False,'validation_2025_read':False,
            'cells':cells}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'decision':result['decision'],'cells_passed':passed,
                      'failures':[c for c in cells if not c['passed']][:4]},sort_keys=True))
    return 0 if passed==90 else 2

if __name__=='__main__':raise SystemExit(run())
