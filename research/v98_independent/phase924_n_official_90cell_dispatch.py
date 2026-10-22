#!/usr/bin/env python3
"""V98 N official 90-cell historical dispatcher: source gate BEFORE ANY PnL.

N full seven-slot target pins and economic hypothesis preregistered Phase919/922.
Never uses V14/V15/V99, XRP, 2025+, contaminated holdout or cached receipt.
"""
from __future__ import annotations
import json,math
from pathlib import Path
from phase876_k_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES
from phase877_k_official_economic_dispatch import require_fresh_sources,load_source_arrays
from phase920_n_composed_source import N_PATHS,freeze_n
from phase923_n_funded_ledger import simulate_n

ROOT=Path(__file__).resolve().parent
FROZEN_N={
'N_core_only':'cdf4545413701578d08753ab7d7cba9303c33b71fca8cd2668f91ed5a7e3a0af',
'N_full':'4fd3baf645c2d3d3f91251fa6e0de1944e5e7cbfbd82060d613d28423be5182b',
'N_minus_opportunity':'880d96766c74505e6b4182e1cd79fb0a0b191aa2838879e4ff6fee074976764f',
'N_minus_relative_value':'600accd6ba7008be14ca7e993be3aa4c03822762437063d1bbf284b512767c5b',
'N_minus_recovery':'d6320fe8d6a25b0bbc808b8053002850dc75d037099fa10f249f56a8a5b3c230',
}


def complete_matrix_n(targets,prices,quote,rate,mark,event,years):
    if tuple(targets)!=N_PATHS or tuple(FROZEN_N)!=N_PATHS:
        raise ValueError('N five-path order not preregistered')
    cases={};failures=[];count=0
    for name,w in targets.items():
        cases[name]={}
        for tier,fee in FEE_TIERS.items():
            cases[name][tier]={}
            for order in ORDERS:
                cases[name][tier][order]={}
                for mode in CAPITAL_MODES:
                    count+=1
                    try:
                        result=simulate_n(w,prices['open'],prices['high'],prices['low'],prices['close'],quote,rate,mark,event,
                                          fee,order=order,mode=mode,years=years)
                    except Exception as exc:
                        result={'survived':False,'reason':f'{type(exc).__name__}: {str(exc)[:200]}'}
                    cases[name][tier][order][mode]=result
                    if not result.get('survived',False):
                        failures.append((name,tier,order,mode,result.get('reason')))
    if count!=90:raise AssertionError('N incomplete economic matrix')
    return {'cells_attempted':count,'cells_survived':count-len(failures),'failures':failures,'cases':cases}


def growth_gate_n(matrix):
    if matrix['cells_attempted']!=90 or matrix['failures']:
        return {'passed':False,'reason':'incomplete_or_failed_survival','failed_cells':len(matrix['failures'])}
    for name in N_PATHS:
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    folds=matrix['cases'][name][tier][order][mode].get('folds',{})
                    if set(folds)!=set(('2023','2024')) or folds['2023'].get('days')!=365 or folds['2024'].get('days')!=366:
                        return {'passed':False,'reason':'incomplete_chronological_folds'}
    failures=[];edges={}
    for year in ('2023','2024'):
        for tier in ('base','severe'):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key='/'.join((year,tier,order,mode))
                    full=matrix['cases']['N_full'][tier][order][mode]['folds'][year]['log_wealth']
                    if not math.isfinite(full) or full<=0:
                        failures.append({'scenario':key,'reason':'nonpositive_full_growth','value':full})
                    margins={}
                    for name in N_PATHS:
                        if name=='N_full':continue
                        alt=matrix['cases'][name][tier][order][mode]['folds'][year]['log_wealth']
                        diff=full-alt;margins[name]=diff
                        if not math.isfinite(diff) or diff<=0:
                            failures.append({'scenario':key,'reason':'nonpositive_marginal','path':name,'value':diff})
                    edges[key]={'N_full_log_wealth':full,'marginals':margins}
    return {'passed':not failures,'reason':'training_only_pending_separate_validation' if not failures else 'nonpositive_training_growth_or_marginal',
            'failure_count':len(failures),'failures':failures,'all_edges':edges}


def run(root=ROOT,source_gate=require_fresh_sources):
    root=Path(root)
    result={'phase':924,'decision':'BLOCKED_BEFORE_PNL','historical_pnl_computed':False,
            'vendor_origin_attested_this_run':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'promotion_eligible':False,'ledger_invocations':0,'frozen_N_paths':FROZEN_N}
    try:
        receipts=source_gate(root=root)  # fresh 100 OHLC + 100 funding + 100 mark ZIP/CHECKSUM
        result['vendor_origin_attested_this_run']=True
        source,rate,mark,event,years=load_source_arrays(root)
        frames,info=freeze_n(root)
        if tuple(info['paths_sha256'])!=N_PATHS or info['paths_sha256']!=FROZEN_N:
            raise PermissionError('N frozen target SHA256 drift')
        result['source_receipts']={'ohlc':receipts['ohlc']['decision'],
                                   'mark':receipts['mark']['decision'],
                                   'funding_mark_sha256':receipts['bounds_csv_sha256']}
        result['historical_pnl_computed']=True
        matrix=complete_matrix_n({k:v.to_numpy(float) for k,v in frames.items()},
                                  {k:source[k] for k in ('open','high','low','close')},
                                  source['quote_volume'],rate,mark,event,years)
        result['ledger_invocations']=matrix['cells_attempted']
        result['matrix']=matrix
        result['growth_gate']=growth_gate_n(matrix)
        result['decision']='PASS_N_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION' if result['growth_gate']['passed'] else 'REJECT_N_TRAINING_NO_RESCUE'
    except Exception as exc:
        result['decision']='BLOCKED_AFTER_PNL_NO_PROMOTION' if result['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        result['reason']=f'{type(exc).__name__}: {str(exc)[:350]}'
    (root/'phase924_n_official_90cell_result.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in ('decision','reason','ledger_invocations','historical_pnl_computed')},sort_keys=True))
    return result

if __name__=='__main__':
    r=run()
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
