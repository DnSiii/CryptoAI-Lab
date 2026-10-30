#!/usr/bin/env python3
"""V98 Independent Q economic receipt verifier: immutable results, no PnL.

Accepts honest full-matrix rejection. Never promotes incomplete/failed cells.
"""
from __future__ import annotations
import json
import math
from collections import Counter
from pathlib import Path
from phase1042_q_signed_sevenslot_source import PATHS
from phase1044_q_funded_signed_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES


def audit(receipt):
    if receipt.get('phase')!=1051 or receipt.get('historical_pnl_computed') is not True or receipt.get('ledger_invocations')!=90:
        return {'passed':False,'reason':'Q_INCOMPLETE_OR_NON_ECONOMIC_RECEIPT'}
    m=receipt.get('matrix',{})
    if m.get('cells_attempted')!=90 or set(m.get('cases',{}))!=set(PATHS):
        return {'passed':False,'reason':'Q_INCOMPLETE_90_CASE_KEYS'}
    observed=[];errors=[];failed=[];passed=0
    for path in PATHS:
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key=(path,tier,order,mode)
                    try:r=m['cases'][path][tier][order][mode]
                    except (KeyError,TypeError):errors.append((key,'missing_cell'));continue
                    observed.append(key)
                    if r.get('survived') is not True:
                        failed.append((key,r.get('reason'),r.get('breach_index')))
                        if not r.get('reason'):errors.append((key,'missing_failure_reason'))
                        continue
                    passed+=1
                    f=r.get('folds',{})
                    if set(f)!={'2023','2024'} or f['2023'].get('days')!=365 or f['2024'].get('days')!=366:
                        errors.append((key,'missing_fold'));continue
                    for y in ('2023','2024'):
                        fold=f[y]
                        for metric in ('log_wealth','cagr','max_drawdown','win_rate','positive_days','cvar_5pct','hourly_max_drawdown'):
                            v=fold.get(metric)
                            if v is None or not isinstance(v,(int,float)) or not math.isfinite(v):errors.append((key,y,'bad_'+metric))
                        if 'profit_factor' not in fold or 'payoff' not in fold:
                            errors.append((key,y,'missing_pf_or_payoff_field'))
                    for metric in ('fees_usd','turnover_usd','funding_debit_usd','total_log_wealth','all_hourly_max_drawdown','hourly_cvar_5pct'):
                        v=r.get(metric)
                        if v is None or not isinstance(v,(int,float)) or not math.isfinite(v):errors.append((key,'bad_'+metric))
                    c=r.get('concentration',{})
                    if len(c.get('asset_exposure_shares',[]))!=4 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in c.get('asset_exposure_shares',[])):
                        errors.append((key,'missing_concentration'))
                    if sum(r.get('regime_hours',{}).values())!=r.get('hourly_nav_observations'):
                        errors.append((key,'regime_hours_incomplete'))
    if len(observed)!=90 or m.get('cells_survived')!=passed or len(m.get('failures',[]))!=len(failed):
        errors.append(('matrix','count_mismatch'))
    if passed<90 and receipt.get('decision')!='REJECT_Q_TRAINING_NO_RESCUE':
        errors.append(('decision','non_rejected_failed_matrix'))
    if passed==90 and receipt.get('decision') not in ('PASS_Q_TRAINING_PENDING_2025_VALIDATION','REJECT_Q_TRAINING_NO_RESCUE'):
        errors.append(('decision','unexpected_all_survived_decision'))
    if receipt.get('decision')=='PASS_Q_TRAINING_PENDING_2025_VALIDATION' and receipt.get('growth_gate',{}).get('passed') is not True:
        errors.append(('decision','growth_gate_not_proven'))
    return {'passed':not errors,'reason':None if not errors else 'Q_RECEIPT_INTEGRITY_FAILED',
            'cells_attempted':len(observed),'cells_survived':passed,'cells_failed':len(failed),
            'failure_reason_counts':dict(Counter(str(x[1]) for x in failed)),
            'unattributed_failure_indices':sum(x[2] is None for x in failed),
            'errors':errors[:30],'economic_approval':receipt.get('decision')=='PASS_Q_TRAINING_PENDING_2025_VALIDATION' and receipt.get('growth_gate',{}).get('passed') is True and passed==90 and not errors}


def run(path):
    r=audit(json.loads(Path(path).read_text()))
    print(json.dumps(r,sort_keys=True,allow_nan=False))
    return 0 if r['passed'] else 2

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('receipt')
    raise SystemExit(run(p.parse_args().receipt))
