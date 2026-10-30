#!/usr/bin/env python3
"""Phase1140 Y independent read-only economic receipt integrity firewall.

Never produces PnL, never rescues failure, never accesses data or benchmarks.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from phase1125_y_sevenslot_source import PATHS
from phase1135_y_funded_training_simulator import FEE_TIERS,ORDERS,CAPITAL_MODES

def check(receipts):
    errors=[];failures=[];seen=0;survived=0
    if len(receipts)!=5 or {r.get('path') for r in receipts}!=set(PATHS):
        return {'decision':'BLOCKED_Y1140_INCOMPLETE_PATHS'}
    for r in receipts:
        if (r.get('phase')!=1136 or r.get('validation_2025_read') is not False or
            r.get('holdout_accessed') is not False or
            r.get('external_benchmarks_used') is not False or
            r.get('cells_attempted')!=18):
            errors.append((r.get('path'),'provenance'))
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key=(r['path'],tier,order,mode)
                    try:x=r['cases'][tier][order][mode]
                    except (KeyError,TypeError):
                        errors.append((key,'missing'));continue
                    seen+=1
                    if x.get('survived') is not True:
                        if not x.get('reason') or x.get('breach_index') is None:
                            errors.append((key,'unattributed_failure'))
                        failures.append((key,x.get('reason')))
                        continue
                    survived+=1
                    try:
                        initial=float(x['initial_usd']);terminal=float(x['terminal_usd'])
                        total=float(x['total_log_wealth'])
                        if (not all(math.isfinite(v) for v in (initial,terminal,total))
                            or initial<=0 or terminal<=0 or
                            not math.isclose(math.log(terminal/initial),total,
                                rel_tol=0,abs_tol=1e-7)):
                            raise ValueError('NAV_LOG_WEALTH')
                        f=x['folds']
                        if set(f)!={'2023','2024'}:
                            raise ValueError('FOLDS')
                        if not math.isclose(sum(float(f[y]['log_wealth']) for y in f),
                            total,rel_tol=0,abs_tol=1e-7):
                            raise ValueError('FOLD_LOG_WEALTH')
                        regime=x['regime_log_wealth']
                        if set(regime)!={'0','1','2'} or not math.isclose(
                            sum(float(v) for v in regime.values()),total,
                            rel_tol=0,abs_tol=1e-7):
                            raise ValueError('REGIME_LOG_WEALTH')
                        hours=x['regime_hours']
                        if set(hours)!={'0','1','2'} or sum(int(v) for v in hours.values())!=17544:
                            raise ValueError('REGIME_HOURS')
                        if x['hourly_nav_observations']!=17544:
                            raise ValueError('CHRONOLOGY')
                        for year,days,n in (('2023',365,8760),('2024',366,8784)):
                            y=f[year]
                            if y['days']!=days or y['hourly_observations']!=n:
                                raise ValueError('FOLD_HOURS')
                            if not (0<=int(y['positive_days'])<=days and
                                math.isclose(float(y['positive_days_share']),
                                    y['positive_days']/days,abs_tol=1e-9)):
                                raise ValueError('POSITIVE_DAYS')
                            dd=float(y['max_drawdown'])
                            if not -1<=dd<=0:raise ValueError('FOLD_DRAWDOWN')
                        dd=float(x['all_hourly_max_drawdown'])
                        if not -1<=dd<=0:raise ValueError('MAX_DRAWDOWN')
                        for field,cap in (('max_asset_weight',.45),
                            ('max_gross_weight',1.35),('max_net_weight',.75)):
                            val=float(x[field])
                            if not math.isfinite(val) or val<0 or val>cap+1e-8:
                                raise ValueError('RISK_'+field)
                        for field in ('fees_usd','turnover_usd'):
                            val=float(x[field])
                            if not math.isfinite(val) or val<0:
                                raise ValueError('ACCOUNTING_'+field)
                        c=x['concentration']
                        hhi=float(c['asset_hhi'])
                        shares=[float(v) for v in c['asset_exposure_shares']]
                        if (len(shares)!=4 or not .25-1e-8<=hhi<=1+1e-8 or
                            not all(math.isfinite(v) and 0<=v<=1 for v in shares)):
                            raise ValueError('CONCENTRATION')
                    except (KeyError,TypeError,ValueError,OverflowError) as exc:
                        errors.append((key,type(exc).__name__+': '+str(exc)[:100]))
    if seen!=90:errors.append(('matrix','not_90'))
    if errors:
        return {'decision':'BLOCKED_Y1140_RECEIPT_INTEGRITY','cells_observed':seen,
            'cells_survived':survived,'errors':errors[:40]}
    if failures:
        return {'decision':'REJECT_Y1140_FAILED_ECONOMIC_CELLS_NO_RESCUE',
            'cells_observed':90,'cells_survived':survived,
            'failures':failures[:20]}
    return {'decision':'PASS_Y1140_RECEIPT_CONSISTENCY_ONLY_NOT_ECONOMIC_PROMOTION',
        'cells_observed':90,'cells_survived':90,
        'promotion_eligible':False,'benchmark_access_allowed':False}

def main(paths):
    r=check([json.loads(Path(p).read_text()) for p in paths])
    print(json.dumps(r,sort_keys=True,allow_nan=False))
    return 0 if r['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('receipts',nargs=5)
    raise SystemExit(main(p.parse_args().receipts))
