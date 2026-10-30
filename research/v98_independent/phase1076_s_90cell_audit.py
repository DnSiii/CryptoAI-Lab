#!/usr/bin/env python3
"""V98 Independent S immutable five-receipt 90-cell training auditor.

Only preregistered growth/marginal/survival gates; no tuning or benchmarks.
No economic source imports and no holdout access.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from phase1069_s_sevenslot_source import PATHS
from phase1074_s_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES


def audit(receipts,manifest=None):
    errors=[];observed={};failed=[];valid=0
    if len(receipts)!=5 or {r.get('path') for r in receipts}!=set(PATHS):
        return {'decision':'BLOCKED_S_INCOMPLETE_FIVE_PATH_RECEIPTS','errors':['missing_or_duplicate_path']}
    for r in receipts:
        path=r['path']
        if manifest is not None and (manifest.get('decision')!='FROZEN_S_PRE_ECONOMIC' or r.get('canonical_sha256')!=manifest.get('canonical_sha256',{}).get(path)):
            errors.append((path,'frozen_source_hash_mismatch'))
        if r.get('phase')!=1075 or r.get('validation_2025_read') is not False or r.get('holdout_accessed') is not False or r.get('external_benchmarks_used') is not False:
            errors.append((path,'invalid_provenance_flags'))
        if r.get('cells_attempted')!=18 or r.get('historical_pnl_computed') is not True:
            errors.append((path,'incomplete_18_cell_execution'))
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key=(path,tier,order,mode)
                    try:c=r['cases'][tier][order][mode]
                    except (KeyError,TypeError):errors.append((key,'missing_cell'));continue
                    observed[key]=c
                    if c.get('survived') is not True:
                        failed.append((key,c.get('reason'),c.get('breach_index')))
                        if not c.get('reason'):errors.append((key,'unattributed_failure'))
                        continue
                    valid+=1
                    folds=c.get('folds',{})
                    if set(folds)!={'2023','2024'}:errors.append((key,'missing_chronological_folds'));continue
                    for year,days,hours in (('2023',365,8760),('2024',366,8784)):
                        f=folds[year]
                        if f.get('days')!=days or f.get('hourly_observations')!=hours:
                            errors.append((key,year,'incomplete_fold'))
                        for metric in ('log_wealth','cagr','max_drawdown','hourly_max_drawdown','win_rate','positive_days','cvar_5pct'):
                            x=f.get(metric)
                            if not isinstance(x,(float,int)) or not math.isfinite(x):errors.append((key,year,'invalid_'+metric))
                        if 'profit_factor' not in f or 'payoff' not in f:errors.append((key,year,'missing_payoff_or_pf'))
                    for metric in ('fees_usd','funding_debit_usd','turnover_usd','all_hourly_max_drawdown','total_log_wealth','hourly_cvar_5pct'):
                        x=c.get(metric)
                        if not isinstance(x,(float,int)) or not math.isfinite(x):errors.append((key,'invalid_'+metric))
                    con=c.get('concentration',{})
                    if len(con.get('asset_exposure_shares',[]))!=4 or 'asset_hhi' not in con:errors.append((key,'incomplete_concentration'))
                    if sum(c.get('regime_hours',{}).values())!=c.get('hourly_nav_observations'):
                        errors.append((key,'incomplete_regime_attribution'))
    if len(observed)!=90:errors.append(('matrix','not_90_cells'))
    for r in receipts:
        path=r['path'];path_survived=sum(c.get('survived') is True for (p,*_),c in observed.items() if p==path)
        if r.get('cells_survived')!=path_survived:errors.append((path,'path_survival_count_mismatch'))
    if errors:return {'decision':'BLOCKED_S_RECEIPT_INTEGRITY','errors':errors[:30],
                      'cells_observed':len(observed),'cells_survived':valid}
    if failed and any(breach is None for _,_,breach in failed):
        return {'decision':'BLOCKED_S_PREFLIGHT_SOURCE_NOT_ECONOMIC','cells_observed':90,
                'cells_survived':valid,'preflight_failures':sum(breach is None for _,_,breach in failed),
                'failure_reasons':dict(Counter(str(x[1]) for x in failed)),
                'growth_gate_evaluated':False}
    if failed:return {'decision':'REJECT_S_TRAINING_NO_RESCUE','cells_observed':90,
                      'cells_survived':valid,'failure_reasons':dict(Counter(str(x[1]) for x in failed)),
                      'preflight_failures':sum(x[2] is None for x in failed),
                      'growth_gate_evaluated':False}
    marginal=[]
    for year in ('2023','2024'):
        for tier in ('base','severe'):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    full=observed[('S_full',tier,order,mode)]['folds'][year]['log_wealth']
                    if full<=0:marginal.append((year,tier,order,mode,'nonpositive_full_log_wealth',full))
                    for path in PATHS:
                        if path=='S_full':continue
                        alt=observed[(path,tier,order,mode)]['folds'][year]['log_wealth']
                        if full<=alt:marginal.append((year,tier,order,mode,'nonpositive_marginal_'+path,full-alt))
    if marginal:return {'decision':'REJECT_S_TRAINING_NO_RESCUE','cells_observed':90,
                        'cells_survived':90,'growth_gate_evaluated':True,'growth_failures':marginal[:80]}
    return {'decision':'PASS_S_TRAINING_ONLY_PENDING_SEPARATE_2025_VALIDATION',
            'cells_observed':90,'cells_survived':90,'growth_gate_evaluated':True,
            'promotion_eligible':False,'benchmark_access_allowed':False}


def main(paths):
    receipts=[json.loads(Path(p).read_text()) for p in paths]
    manifest=json.loads((Path(__file__).resolve().parent/'phase1075_s_frozen_manifest.json').read_text())
    result=audit(receipts,manifest)
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    return 0 if result['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('receipts',nargs=5)
    raise SystemExit(main(p.parse_args().receipts))
