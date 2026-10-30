#!/usr/bin/env python3
"""AC preregistered 90-cell synthetic-only full seven-slot inventory integration."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase1174_ac_discrete_intents import compose_intents, PATHS, MODES
from phase1177_ac_actual_open_executor import execute_hour, FEES, ORDERS
from test_phase1174_ac_discrete_intents import sample

CAPITAL = {'immediate': 10000., 'capacity_1m': 1e6, 'capacity_10m': 1e7}
START, STOP = 900, 996
OUT = Path(__file__).resolve().parent / 'phase1179_ac_90cell_synthetic_receipt.json'


def run():
    frames = sample()
    source = compose_intents(*frames)
    op, hi, lo, cl, quote, _ = [f.to_numpy(float) for f in frames]
    returns = np.diff(np.log(cl), axis=0)
    results = []
    for path in PATHS:
        for mode in MODES:
            scores = source[path, mode]
            for fee_name, fee in FEES.items():
                for order in ORDERS:
                    capital = CAPITAL[mode]
                    cash = capital
                    units = np.zeros(4)
                    turnover = fees = funding = 0.
                    gap_count = 0
                    reason = None
                    for t in range(START, STOP):
                        covariance = np.cov(returns[t-337:t-1].T, ddof=0) * 24 + np.eye(4)*1e-8
                        event = np.full(4, t % 8 == 0, dtype=bool)
                        rate = np.array([(.0001 if ((t//8+j)%2==0) else -.0001)
                                         if event[j] else 0. for j in range(4)])
                        bounds = np.column_stack((cl[t]*.99, cl[t]*1.01))
                        result = execute_hour(
                            prior=cl[t-1], opening=op[t], high=hi[t], low=lo[t], closing=cl[t],
                            cash=cash, old_units=units, scores=scores[t-1], cov24=covariance,
                            down=np.full(4, .25), up=np.full(4, .30),
                            funding_bound=np.full(4, .001), prior_quote=quote[t-1],
                            min336_quote=np.min(quote[t-336:t],axis=0), fee=fee,
                            funding_rate=rate, mark_bounds=bounds, funding_event=event,
                            order=order, rebalance=t%12==0)
                        if not result['ok']:
                            reason = result['reason']
                            break
                        units, cash = result['units'], result['cash']
                        turnover += result['turnover']
                        fees += result['fees']
                        funding += result['funding_cash_delta']
                        gap_count += int(result['gap'])
                    nav = float(cash + np.dot(units, cl[t]))
                    results.append({'path':path,'mode':mode,'fee':fee_name,'funding_order':order,
                                    'passed':reason is None and np.isfinite(nav) and nav>0,
                                    'reason':reason,'hours_attempted':t-START+1,
                                    'final_synthetic_nav':nav,'turnover':turnover,
                                    'fees_paid':fees,'funding_cash':funding,'gap_events':gap_count})
    passed = sum(r['passed'] for r in results)
    receipt = {'phase':1179,'decision':'PASS_AC_90_OF_90_SYNTHETIC_ONLY' if passed==90
               else 'REJECT_AC_SYNTHETIC_INTEGRATION_NO_RESCUE',
               'cells_attempted':len(results),'cells_passed':passed,
               'historical_pnl_computed':False,'validation_2025_read':False,
               'external_benchmarks_used':False,'synthetic_only':True,
               'cells':results}
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'decision':receipt['decision'],'cells_passed':passed,
                      'cells_attempted':len(results),
                      'failures':[{'path':r['path'],'mode':r['mode'],'fee':r['fee'],
                                   'order':r['funding_order'],'reason':r['reason']}
                                  for r in results if not r['passed']][:12]},sort_keys=True))
    return 0 if passed==90 else 2


if __name__=='__main__':
    raise SystemExit(run())
