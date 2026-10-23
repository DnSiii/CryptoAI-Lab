#!/usr/bin/env python3
"""AD 90-cell synthetic crisis with actual-NAV stress activation; no PnL claims."""
from __future__ import annotations
import itertools
import json
import numpy as np
from phase1198_ad_complete_synthetic import fixture,source_slots,one_cell,PATHS,MODES,FEES,ORDERS


def crisis_fixture():
    frames,_,_=fixture(900)
    close=frames[3].to_numpy(copy=True)
    close[810:]*=.55
    close[850:]*=1.80
    opening=np.vstack([close[0],close[:-1]])
    high=np.maximum(opening,close)*1.003
    low=np.minimum(opening,close)*.997
    for k,a in ((0,opening),(1,high),(2,low),(3,close)):
        frames[k].iloc[:]=a
    event=frames[6].to_numpy(float)
    marks=(np.where(event!=0,close*.99,np.nan),
           np.where(event!=0,close*1.01,np.nan))
    return frames,marks


def run():
    frames,marks=crisis_fixture()
    slots=source_slots(frames)
    cells=[]
    for path,mode,fee,order in itertools.product(PATHS,MODES,FEES,ORDERS):
        try:
            cells.append(one_cell(path,mode,fee,order,frames,marks,slots))
        except Exception as exc:
            cells.append({'path':path,'mode':mode,'fee':fee,'order':order,
                          'passed':False,'reason':type(exc).__name__+': '+str(exc),
                          'historical_system_pnl_computed':False})
    stress=next((c for c in cells if c['path']=='AD_full' and c['mode']=='immediate'
                 and c['fee']=='base' and c['order']=='carried_before_fill'),{})
    passed=(len(cells)==90 and all(c['passed'] for c in cells) and
            stress.get('active_hours',{}).get('stress',0)>0)
    return {'phase':1200,'decision':'PASS_AD_90_CRISIS_SYNTHETIC_NOT_ECONOMIC'
            if passed else 'REJECT_AD_CRISIS_SYNTHETIC_NO_PNL',
            'historical_system_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'cells':cells}


if __name__=='__main__':
    r=run()
    print(json.dumps({'decision':r['decision'],'passed':sum(c['passed'] for c in r['cells']),
        'failed':[{k:c[k] for k in ('path','mode','fee','order','reason')}
                  for c in r['cells'] if not c['passed']][:10]},sort_keys=True))
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
