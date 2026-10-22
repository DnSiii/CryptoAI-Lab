#!/usr/bin/env python3
"""V98 N separate-2025-validation firewall; does not read 2025 or any PnL source.

Validates a completed immutable 2023/24 training receipt BEFORE any future
validation dataset may be opened. Never promotes a synthetic/blocked receipt.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from phase924_n_official_90cell_dispatch import FROZEN_N,growth_gate_n
from phase876_k_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES
from phase877_k_official_economic_dispatch import PASS_OHLC,PASS_MARK

ROOT=Path(__file__).resolve().parent
PASS='PASS_N_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION'


def seal_training_receipt(obj):
    if not isinstance(obj,dict):raise PermissionError('training receipt object required')
    flags={'decision':PASS,'historical_pnl_computed':True,
           'vendor_origin_attested_this_run':True,'ledger_invocations':90,
           'validation_2025_read':False,'holdout_accessed':False,
           'external_benchmarks_used':False,'promotion_eligible':False}
    for key,value in flags.items():
        if type(obj.get(key)) is not type(value) or obj[key]!=value:
            raise PermissionError('training freeze flag invalid: '+key)
    if obj.get('frozen_N_paths')!=FROZEN_N:
        raise PermissionError('five frozen N path hashes differ')
    receipt=obj.get('source_receipts',{})
    if receipt.get('ohlc')!=PASS_OHLC or receipt.get('mark')!=PASS_MARK:
        raise PermissionError('official source attestation absent')
    digest=receipt.get('funding_mark_sha256','')
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
        raise PermissionError('funding-mark evidence SHA256 missing')
    matrix=obj.get('matrix',{})
    if matrix.get('cells_attempted')!=90 or matrix.get('cells_survived')!=90 or matrix.get('failures')!=[]:
        raise PermissionError('complete 90-cell survival not demonstrated')
    cases=matrix.get('cases',{})
    if set(cases)!=set(FROZEN_N):raise PermissionError('N ablation registry drift')
    for name in FROZEN_N:
        if set(cases[name])!=set(FEE_TIERS):raise PermissionError('fee tier registry drift')
        for tier in FEE_TIERS:
            if set(cases[name][tier])!=set(ORDERS):raise PermissionError('funding-order registry drift')
            for order in ORDERS:
                if set(cases[name][tier][order])!=set(CAPITAL_MODES):raise PermissionError('capital-mode registry drift')
                for mode in CAPITAL_MODES:
                    cell=cases[name][tier][order][mode]
                    if cell.get('survived') is not True or cell.get('hourly_sample_complete') is not True:
                        raise PermissionError('unsurvived or incomplete hourly cell')
                    if cell.get('hourly_nav_observations')!=17544 or cell.get('daily_nav_observations')!=731:
                        raise PermissionError('hourly or daily coverage incomplete')
                    if set(cell.get('folds',{}))!={'2023','2024'}:
                        raise PermissionError('chronological fold registry drift')
                    for year,hours,days in (('2023',8760,365),('2024',8784,366)):
                        fold=cell['folds'][year]
                        if fold.get('days')!=days or fold.get('hourly_nav_observations')!=hours:
                            raise PermissionError('fold hour/day coverage invalid')
                        for key in ('log_wealth','hourly_close_max_drawdown','daily_close_max_drawdown'):
                            val=fold.get(key)
                            if not isinstance(val,(float,int)) or not math.isfinite(val):
                                raise PermissionError('fold financial telemetry missing: '+key)
                        if fold['hourly_close_max_drawdown']>fold['daily_close_max_drawdown']+1e-12:
                            raise PermissionError('hourly drawdown understates daily')
    # Recompute preregistered growth and ablation gate, do not trust reported boolean.
    check=growth_gate_n(matrix)
    if check['passed'] is not True or obj.get('growth_gate',{}).get('passed') is not True:
        raise PermissionError('growth/marginal contribution gate failed')
    # This is a receipt hash, not a claim that 2025 was read or validated.
    raw=json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return {'decision':'TRAINING_FROZEN_READY_FOR_SEPARATE_2025_VALIDATION',
            'training_receipt_sha256':hashlib.sha256(raw).hexdigest(),
            'training_source_mark_sha256':digest,
            'frozen_N_paths':dict(FROZEN_N),
            'validation_2025_read':False,'holdout_accessed':False,
            'external_benchmarks_used':False,'historical_pnl_computed_this_check':False}


def run(root=ROOT):
    root=Path(root)
    result={'phase':948,'decision':'BLOCKED_BEFORE_2025_VALIDATION',
            'validation_2025_read':False,'holdout_accessed':False,
            'external_benchmarks_used':False,'historical_pnl_computed_this_check':False}
    try:
        obj=json.loads((root/'phase940_n_official_90cell_hourly_result.json').read_text())
        result.update(seal_training_receipt(obj))
    except Exception as exc:
        result['reason']=type(exc).__name__+': '+str(exc)[:250]
    (root/'phase948_n_validation_firewall_result.json').write_text(
        json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    out=run()
    print(json.dumps({k:out.get(k) for k in ('decision','reason','validation_2025_read')},sort_keys=True))
