#!/usr/bin/env python3
"""V98 N 90-cell official economic gate with hourly NAV reporting, no retuning.

Never runs historical PnL before fresh official source gate. 2025+ excluded.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from phase876_k_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES
from phase877_k_official_economic_dispatch import require_fresh_sources,load_source_arrays
from phase920_n_composed_source import N_PATHS,freeze_n
from phase924_n_official_90cell_dispatch import FROZEN_N,growth_gate_n
from phase939_n_funded_ledger_hourly import simulate_n_with_hourly

ROOT=Path(__file__).resolve().parent


def complete_matrix_hourly(targets,prices,quote,rate,mark,event,years):
    if tuple(targets)!=N_PATHS or tuple(FROZEN_N)!=N_PATHS:
        raise ValueError('frozen N path order mismatch')
    cases={};failures=[];count=0
    for name,weights in targets.items():
        cases[name]={}
        for tier,fee in FEE_TIERS.items():
            cases[name][tier]={}
            for order in ORDERS:
                cases[name][tier][order]={}
                for mode in CAPITAL_MODES:
                    count+=1
                    try:
                        cell=simulate_n_with_hourly(weights,prices['open'],prices['high'],prices['low'],prices['close'],
                             quote,rate,mark,event,fee,order=order,mode=mode,years=years,require_full_sample=True)
                        if cell.get('survived'):
                            folds=cell.get('folds',{})
                            if (cell.get('hourly_nav_observations')!=17544 or
                                cell.get('hourly_sample_complete') is not True or
                                cell.get('daily_nav_observations')!=731 or
                                set(folds)!=set(('2023','2024')) or
                                not math.isfinite(cell.get('all_hourly_close_max_drawdown',float('nan')))):
                                raise ValueError('complete two-year hourly NAV telemetry missing')
                            for year,hours,days in (('2023',8760,365),('2024',8784,366)):
                                fold=folds[year]
                                if (fold.get('hourly_nav_observations')!=hours or fold.get('days')!=days or
                                    not all(math.isfinite(fold.get(k,float('nan'))) for k in ('hourly_close_max_drawdown','daily_close_max_drawdown')) or
                                    fold['hourly_close_max_drawdown']>fold['daily_close_max_drawdown']+1e-12):
                                    raise ValueError('incomplete or contradictory hourly fold')
                    except Exception as exc:
                        cell={'survived':False,'reason':type(exc).__name__+': '+str(exc)[:200]}
                    if not cell.get('survived'):
                        failures.append((name,tier,order,mode,cell.get('reason','unknown failure')))
                    cases[name][tier][order][mode]=cell
    if count!=90:raise AssertionError('90 preregistered cells required')
    return {'cells_attempted':count,'cells_survived':count-len(failures),
            'failures':failures,'cases':cases,'hourly_telemetry_required':True}


def run(root=ROOT,source_gate=require_fresh_sources):
    root=Path(root)
    out={'phase':940,'decision':'BLOCKED_BEFORE_PNL','historical_pnl_computed':False,
         'vendor_origin_attested_this_run':False,'validation_2025_read':False,
         'holdout_accessed':False,'external_benchmarks_used':False,
         'promotion_eligible':False,'ledger_invocations':0,'frozen_N_paths':FROZEN_N}
    try:
        receipts=source_gate(root=root)
        # Never load bars, compose targets or invoke any funded simulator before gate.
        out['vendor_origin_attested_this_run']=True
        source,rate,mark,event,years=load_source_arrays(root)
        paths,info=freeze_n(root)
        if tuple(info['paths_sha256'])!=N_PATHS or info['paths_sha256']!=FROZEN_N:
            raise PermissionError('N frozen target SHA256 drift')
        out['source_receipts']={'ohlc':receipts['ohlc']['decision'],
                                'mark':receipts['mark']['decision'],
                                'funding_mark_sha256':receipts['bounds_csv_sha256']}
        out['historical_pnl_computed']=True
        matrix=complete_matrix_hourly({k:v.to_numpy(float) for k,v in paths.items()},
              {k:source[k] for k in ('open','high','low','close')},source['quote_volume'],
              rate,mark,event,years)
        out['ledger_invocations']=matrix['cells_attempted']
        out['matrix']=matrix
        out['growth_gate']=growth_gate_n(matrix)
        out['decision']='PASS_N_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION' if out['growth_gate']['passed'] else 'REJECT_N_TRAINING_NO_RESCUE'
    except Exception as exc:
        out['decision']='BLOCKED_AFTER_PNL_NO_PROMOTION' if out['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        out['reason']=type(exc).__name__+': '+str(exc)[:350]
    (root/'phase940_n_official_90cell_hourly_result.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:out.get(k) for k in ('decision','reason','ledger_invocations','historical_pnl_computed')},sort_keys=True))
    return out

if __name__=='__main__':
    result=run()
    raise SystemExit(0 if result['decision'].startswith('PASS_') else 2)
