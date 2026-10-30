#!/usr/bin/env python3
"""V98 Independent Phase950: preregistered accounting audit of a frozen N receipt.

Read-only pure verifier. No data download, PnL computation, benchmark inspection,
parameter change or 2025 validation. Run BEFORE authorizing Phase948 seal.
"""
from __future__ import annotations
import math
from phase924_n_official_90cell_dispatch import FROZEN_N
from phase876_k_funded_ledger import FEE_TIERS, ORDERS, CAPITAL_MODES


def _finite_number(x, label):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise PermissionError('nonfinite or absent financial field: ' + label)
    return float(x)


def _close(a, b, label, *, tol=1e-9):
    if not math.isclose(a, b, rel_tol=tol, abs_tol=1e-10):
        raise PermissionError('inconsistent accounting identity: ' + label)


def audit_n_training_accounting(receipt):
    """Check ALL 90 scenarios; fail closed without selecting winning scenarios.

    NAV telemetry is not stored in the compact receipt. This audit checks
    algebraic consistency, not source authenticity or an independent replay.
    """
    matrix=receipt.get('matrix', {})
    if matrix.get('cells_attempted')!=90 or matrix.get('cells_survived')!=90 or matrix.get('failures')!=[]:
        raise PermissionError('not a complete 90-cell survival matrix')
    cases=matrix.get('cases', {})
    if set(cases)!=set(FROZEN_N):raise PermissionError('path registry drift')
    audited=0
    for name in FROZEN_N:
        if set(cases[name])!=set(FEE_TIERS):raise PermissionError('fee registry drift')
        for tier in FEE_TIERS:
            if set(cases[name][tier])!=set(ORDERS):raise PermissionError('settlement registry drift')
            for order in ORDERS:
                if set(cases[name][tier][order])!=set(CAPITAL_MODES):
                    raise PermissionError('capital registry drift')
                for mode, initial in CAPITAL_MODES.items():
                    tag='/'.join((name,tier,order,mode))
                    c=cases[name][tier][order][mode]
                    if c.get('survived') is not True or c.get('hourly_sample_complete') is not True:
                        raise PermissionError('survival/telemetry absent: '+tag)
                    if c.get('hourly_nav_observations')!=17544 or c.get('daily_nav_observations')!=731:
                        raise PermissionError('coverage mismatch: '+tag)
                    start=_finite_number(c.get('initial_usd'),tag+'/initial')
                    end=_finite_number(c.get('terminal_usd'),tag+'/terminal')
                    if start<=0 or end<=0:raise PermissionError('nonpositive equity: '+tag)
                    _close(start, initial, tag+'/initial capital')
                    total_log=_finite_number(c.get('total_log_wealth'),tag+'/total_log')
                    total_mult=_finite_number(c.get('total_wealth_multiple'),tag+'/total_mult')
                    _close(total_log, math.log(end/start),tag+'/total log NAV')
                    _close(total_mult, end/start,tag+'/total wealth NAV')
                    folds=c.get('folds',{})
                    if set(folds)!={'2023','2024'}:raise PermissionError('fold registry drift: '+tag)
                    fold_sum=0.
                    fold_product=1.
                    for year,days,hours in [('2023',365,8760),('2024',366,8784)]:
                        f=folds[year]
                        if f.get('days')!=days or f.get('hourly_nav_observations')!=hours:
                            raise PermissionError('fold coverage mismatch: '+tag+'/'+year)
                        g=_finite_number(f.get('log_wealth'),tag+'/'+year+'/log')
                        multiple=_finite_number(f.get('wealth_multiple'),tag+'/'+year+'/multiple')
                        cagr=_finite_number(f.get('cagr'),tag+'/'+year+'/cagr')
                        if multiple<=0:raise PermissionError('fold wealth nonpositive: '+tag)
                        _close(multiple, math.exp(g),tag+'/'+year+'/fold multiple')
                        _close(cagr, math.expm1(g/(days/365.25)),tag+'/'+year+'/fold CAGR')
                        hourly=_finite_number(f.get('hourly_close_max_drawdown'),tag+'/'+year+'/hourly DD')
                        daily=_finite_number(f.get('daily_close_max_drawdown'),tag+'/'+year+'/daily DD')
                        if not (-1<=hourly<=daily<=0):raise PermissionError('fold drawdown order invalid: '+tag)
                        fold_sum+=g;fold_product*=multiple
                    _close(total_log,fold_sum,tag+'/chronological log folds')
                    _close(total_mult,fold_product,tag+'/chronological wealth folds')
                    full_dd=_finite_number(c.get('all_hourly_close_max_drawdown'),tag+'/full hourly DD')
                    if not -1<=full_dd<=min(folds['2023']['hourly_close_max_drawdown'],folds['2024']['hourly_close_max_drawdown'])+1e-10:
                        raise PermissionError('full sample drawdown inconsistent: '+tag)
                    for field in ('fees_usd','turnover_usd','opening_repair_turnover_usd'):
                        if _finite_number(c.get(field),tag+'/'+field)<0:
                            raise PermissionError('negative cost/turnover: '+tag)
                    if c['opening_repair_turnover_usd']>c['turnover_usd']+1e-8:
                        raise PermissionError('repair turnover exceeds total: '+tag)
                    _finite_number(c.get('funding_debit_usd'),tag+'/funding')
                    audited+=1
    if audited!=90:raise PermissionError('incomplete audit')
    return {'decision':'PASS_90CELL_N_ACCOUNTING_IDENTITIES_ONLY',
            'cells_audited':audited,'source_authenticated_by_this_audit':False,
            'historical_pnl_computed_by_this_audit':False,
            'validation_2025_read':False,'external_benchmarks_used':False}
