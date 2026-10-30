#!/usr/bin/env python3
"""Independent AC economic 90-cell receipt audit; no signals, PnL or benchmarks."""
from __future__ import annotations
import itertools
import json
import math
import sys
from pathlib import Path
import numpy as np

PATHS=('AC_core_only','AC_full','AC_minus_opportunity',
       'AC_minus_relative_value','AC_minus_stress')
MODES=('immediate','capacity_1m','capacity_10m')
FEES=('base','severe','supersevere')
ORDERS=('carried_before_fill','new_after_fill')
SOURCE_SHA='f706812b7989666c3efd0b24045a5c31f4d9c79b46d61da7b5e6cde6c6e73f5e'


def finite(x):
    return isinstance(x,(int,float)) and math.isfinite(x)


def receipt_path(root,path):
    a=root/('v98-ac-1182-'+path)/('phase1182_ac_official_'+path+'.json')
    b=root/('phase1182_ac_official_'+path+'.json')
    return a if a.exists() else b


def audit(root):
    root=Path(root)
    problems=[];cells={};missing=[];metrics=[]
    for path in PATHS:
        p=receipt_path(root,path)
        if not p.is_file():
            missing.append(path);continue
        try:r=json.loads(p.read_text())
        except (OSError,ValueError) as exc:
            problems.append(path+':JSON_'+str(exc)[:80]);continue
        if (r.get('path')!=path or r.get('validation_2025_read') is not False
            or r.get('external_benchmarks_used') is not False
            or r.get('official_source_mark_sha256')!=SOURCE_SHA):
            problems.append(path+':SCOPE_OR_VENDOR_SHA');continue
        if len(r.get('cells',[]))!=18:
            problems.append(path+':NOT_18_CELLS')
        for c in r.get('cells',[]):
            key=(c.get('path'),c.get('mode'),c.get('fee'),c.get('funding_order'))
            if key in cells:
                problems.append('DUPLICATE_'+str(key));continue
            cells[key]=c
    expected=set(itertools.product(PATHS,MODES,FEES,ORDERS))
    if set(cells)!=expected:problems.append('MISSING_OR_EXTRA_CELL_KEYS')
    for key,c in cells.items():
        if (c.get('passed') is not True or c.get('hours_completed')!=17544
            or c.get('historical_pnl_computed') is not True):
            problems.append('UNSURVIVED_'+str(key));continue
        for field,limit in (('max_gross',1.20),('max_abs_net',.60),('max_asset_concentration',.40)):
            v=c.get(field)
            if not finite(v) or v<0 or v>limit+1e-8:
                problems.append('RISK_'+field+'_'+str(key))
        for field in ('final_equity','turnover','fees_paid','funding_cash'):
            if not finite(c.get(field)):
                problems.append('NONFINITE_'+field+'_'+str(key))
        if c.get('final_equity',0)<=0 or c.get('fees_paid',-1)<0:
            problems.append('NAV_OR_FEES_'+str(key))
        folds=c.get('folds') or {}
        if set(folds)!={'2023','2024'}:
            problems.append('FOLDS_'+str(key));continue
        for year,hours in (('2023',8760),('2024',8784)):
            f=folds[year]
            if f.get('hours')!=hours:
                problems.append('HOURS_'+str(key)+'_'+year)
            for field in ('starting_equity','ending_equity','net_return','cagr_annualized',
                          'max_drawdown','daily_win_rate','daily_cvar5'):
                if not finite(f.get(field)):
                    problems.append('FOLD_NONFINITE_'+field+'_'+str(key)+'_'+year)
            if f.get('trade_level_pf_payoff_win_rate')!='PENDING_SEPARATE_FROZEN_FIFO_AUDIT':
                problems.append('TRADE_PF_MISLABEL_'+str(key))
            metrics.append({'path':key[0],'mode':key[1],'fee':key[2],
                            'funding_order':key[3],'year':year,
                            'cagr':f.get('cagr_annualized'),
                            'max_drawdown':f.get('max_drawdown'),
                            'positive_days':f.get('positive_days'),
                            'daily_cvar5':f.get('daily_cvar5')})
    if missing or len(cells)!=90:
        decision='BLOCKED_AC_ECONOMIC_RECEIPTS_NO_PROMOTION'
        return {'phase':1183,'decision':decision,'cells_seen':len(cells),
                'missing_paths':missing,'problems':problems[:100],
                'promotion_eligible':False,'validation_2025_read':False}
    growth=[];marginal={};passed_growth=True;passed_marginal=True
    for mode,fee,order in itertools.product(MODES,('base','severe'),ORDERS):
        full=cells['AC_full',mode,fee,order]
        for year in ('2023','2024'):
            v=(full.get('folds') or {}).get(year,{}).get('cagr_annualized')
            ok=finite(v) and v>0
            growth.append({'mode':mode,'fee':fee,'order':order,'year':year,
                           'cagr':v,'passed':ok})
            passed_growth &=ok
    for sleeve in ('opportunity','relative_value','stress'):
        improvements=[]
        for mode,fee,order,year in itertools.product(MODES,('base','severe'),ORDERS,('2023','2024')):
            full=(cells['AC_full',mode,fee,order].get('folds') or {}).get(year,{})
            minus=(cells['AC_minus_'+sleeve,mode,fee,order].get('folds') or {}).get(year,{})
            fr,br=full.get('net_return'),minus.get('net_return')
            improvements.append(math.log1p(fr)-math.log1p(br) if finite(fr) and finite(br)
                                and fr>-1 and br>-1 else float('nan'))
        positive=sum(np.isfinite(v) and v>0 for v in improvements)
        median=float(np.median(improvements)) if all(np.isfinite(v) for v in improvements) else None
        passed=positive>=18 and median is not None and median>0
        marginal[sleeve]={'positive_comparisons':positive,'total':24,
                          'median_annual_log_growth_improvement':median,'passed':passed}
        passed_marginal &=passed
    decision=('PASS_AC_INTERNAL_GROWTH_PENDING_FIFO_AND_VALIDATION'
              if not problems and passed_growth and passed_marginal else
              'REJECT_AC_ECONOMIC_NO_RESCUE')
    return {'phase':1183,'decision':decision,'cells_seen':len(cells),
            'cells_survived':sum(c.get('passed') is True for c in cells.values()),
            'growth_gate':growth,'marginal_gate':marginal,'problems':problems[:100],
            'metrics':metrics,'promotion_eligible':False,
            'validation_2025_read':False,'external_benchmarks_used':False}


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('AC1183_RECEIPT_DIRECTORY_REQUIRED')
    r=audit(sys.argv[1])
    print(json.dumps({k:r.get(k) for k in ('decision','cells_seen','cells_survived',
        'missing_paths','marginal_gate','problems')},sort_keys=True,allow_nan=False))
    Path('phase1183_ac_growth_gate_receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
