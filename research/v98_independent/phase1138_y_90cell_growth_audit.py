#!/usr/bin/env python3
"""Phase1138 Y: immutable 90-cell chronological growth-first receipt auditor.

No data acquisition or trading logic. Rejection is final for this frozen Y.
"""
from __future__ import annotations
import json
import math
from collections import Counter
from pathlib import Path
from phase1125_y_sevenslot_source import PATHS
from phase1135_y_funded_training_simulator import FEE_TIERS,ORDERS,CAPITAL_MODES

def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def audit(receipts,manifest=None):
    if len(receipts)!=len(PATHS) or {r.get('path') for r in receipts}!=set(PATHS):
        return {'decision':'BLOCKED_Y_INCOMPLETE_FIVE_PATH_RECEIPTS','cells_observed':0}
    observed={};errors=[];failures=[]
    for r in receipts:
        path=r['path']
        if manifest is not None and (
            manifest.get('decision')!='FROZEN_Y_FULL_PRE_ECONOMIC' or
            r.get('canonical_sha256')!=manifest.get('canonical_sha256',{}).get(path)):
            errors.append((path,'freeze_or_target_mismatch'))
        if (r.get('phase')!=1136 or r.get('cells_attempted')!=18 or
            r.get('historical_pnl_computed') is not True or
            r.get('validation_2025_read') is not False or
            r.get('external_benchmarks_used') is not False or
            r.get('holdout_accessed') is not False):
            errors.append((path,'invalid_receipt_provenance_or_partial'))
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key=(path,tier,order,mode)
                    try:cell=r['cases'][tier][order][mode]
                    except (KeyError,TypeError):
                        errors.append((key,'missing_cell'));continue
                    observed[key]=cell
                    if cell.get('survived') is not True:
                        if not cell.get('reason') or cell.get('breach_index') is None:
                            errors.append((key,'unattributed_or_preflight_failure'))
                        failures.append((key,cell.get('reason'),cell.get('breach_index')))
                        continue
                    if cell.get('hourly_nav_observations')!=17544:
                        errors.append((key,'missing_chronological_hours'))
                    if cell.get('active_hours',0)<=0 or cell.get('filled_orders',0)<=0:
                        errors.append((key,'no_economic_exposure'))
                    if set(cell.get('folds',{}))!={'2023','2024'}:
                        errors.append((key,'incomplete_folds'));continue
                    for year,days,hours in (('2023',365,8760),('2024',366,8784)):
                        f=cell['folds'][year]
                        if f.get('days')!=days or f.get('hourly_observations')!=hours:
                            errors.append((key,year,'fold_geometry'))
                        for field in ('log_wealth','cagr','max_drawdown',
                                      'hourly_cvar_5pct','positive_days_share'):
                            if not finite(f.get(field)):
                                errors.append((key,year,'nonfinite_'+field))
                        if not isinstance(f.get('positive_days'),int):
                            errors.append((key,year,'positive_days_missing'))
                        for field in ('profit_factor','payoff','win_rate'):
                            if field not in f or (f[field] is not None and not finite(f[field])):
                                errors.append((key,year,'invalid_'+field))
                    for field in ('total_log_wealth','all_hourly_max_drawdown',
                        'hourly_cvar_5pct','fees_usd','funding_debit_usd','turnover_usd',
                        'max_asset_weight','max_gross_weight','max_net_weight'):
                        if not finite(cell.get(field)):
                            errors.append((key,'nonfinite_'+field))
                    if (len(cell.get('concentration',{}).get('asset_exposure_shares',[]))!=4
                        or not finite(cell.get('concentration',{}).get('asset_hhi'))):
                        errors.append((key,'concentration'))
                    if sum(cell.get('regime_hours',{}).values())!=17544:
                        errors.append((key,'regime_hour_count'))
                    if not all(finite(v) for v in cell.get('regime_log_wealth',{}).values()):
                        errors.append((key,'regime_attribution'))
        survived=sum(x.get('survived') is True for (p,*_),x in observed.items() if p==path)
        if r.get('cells_survived')!=survived:
            errors.append((path,'survival_count_mismatch'))
    if len(observed)!=90:errors.append(('matrix','not_90'))
    if errors:
        return {'decision':'BLOCKED_Y_RECEIPT_INTEGRITY','cells_observed':len(observed),
                'errors':errors[:30],'cells_survived':sum(x.get('survived') is True for x in observed.values())}
    if failures:
        return {'decision':'REJECT_Y_TRAINING_NO_RESCUE','cells_observed':90,
                'cells_survived':90-len(failures),
                'first_failures':failures[:15],
                'failure_reasons':dict(Counter(str(x[1]) for x in failures)),
                'growth_gate_evaluated':False}
    growth_fail=[]
    for year in ('2023','2024'):
        for tier in ('base','severe'):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    full=observed[('Y_full',tier,order,mode)]['folds'][year]['log_wealth']
                    if full<=0:growth_fail.append((year,tier,order,mode,'nonpositive_full',full))
                    for path in PATHS:
                        if path=='Y_full':continue
                        alt=observed[(path,tier,order,mode)]['folds'][year]['log_wealth']
                        if full<=alt:
                            growth_fail.append((year,tier,order,mode,'no_marginal_'+path,full-alt))
    if growth_fail:
        return {'decision':'REJECT_Y_TRAINING_NO_RESCUE','cells_observed':90,
                'cells_survived':90,'growth_gate_evaluated':True,
                'growth_failures':growth_fail[:80]}
    return {'decision':'PASS_Y_TRAINING_ONLY_PENDING_UNTOUCHED_VALIDATION',
        'cells_observed':90,'cells_survived':90,'growth_gate_evaluated':True,
        'promotion_eligible':False,'benchmark_access_allowed':False}

def main(paths):
    receipts=[json.loads(Path(p).read_text()) for p in paths]
    manifest=json.loads((Path(__file__).resolve().parent/
        'phase1137_y_full_pre_economic_freeze.json').read_text())
    result=audit(receipts,manifest)
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    return 0 if result['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('receipts',nargs=5)
    raise SystemExit(main(p.parse_args().receipts))
