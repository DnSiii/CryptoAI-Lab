#!/usr/bin/env python3
"""V98 AQ paired-marginal composed preregistered 90-cell 2023/24 chronological training runner.\n\nReuses only common AK/AI actual-open ledger and historical receipt mechanics,\nnever any rejected AN strategy signals, parameters or architecture.

No 2025 data, benchmark engines, or 2026 data may be read by this module.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
import numpy as np
from aq_causal_marginal_sources import source_bundle
from aq_causal_marginal_allocator import AQAllocator
from ak_slow_compound_execution import (
    govern, risk_history, FEES, ORDERS)
from phase1246_ai_two_stage_margin import settle_hour
from phase1260_aj_authenticated_source_digest import load_official, HOURS

PATHS = ('AQ_core_only', 'AQ_full', 'AQ_minus_opportunity',
         'AQ_minus_RV', 'AQ_minus_stress')
CAQITAL = {'immediate': 10000., 'capacity_1m': 1e6,
           'capacity_10m': 1e7}
FIRST_2023 = 744
FIRST_2024 = 9504
START_EXECUTION = 2016

def metrics(dollars, returns, positive_days, total_days):
    d = np.asarray(dollars, dtype=float)
    r = np.asarray(returns, dtype=float)
    win, loss = d[d > 1e-10], -d[d < -1e-10]
    var = float(np.quantile(r, .01)) if len(r) else None
    return {
        'hourly_net_profit_factor':
            float(win.sum() / loss.sum()) if len(loss) and loss.sum() else None,
        'hourly_net_payoff':
            float(win.mean() / loss.mean()) if len(win) and len(loss) else None,
        'hourly_net_win_rate':
            float(len(win) / (len(win) + len(loss))) if len(win) + len(loss) else 0.,
        'positive_utc_days': int(positive_days),
        'total_utc_days': int(total_days),
        'positive_day_fraction':
            float(positive_days / total_days) if total_days else 0.,
        'worst_hour_net_return': float(r.min()) if len(r) else None,
        'hourly_var_1pct': var,
        'hourly_cvar_1pct':
            float(r[r <= var].mean()) if var is not None else None,
        'positive_hours': int(len(win)),
        'negative_hours': int(len(loss)),
    }

def prepare_risk(frames):
    o, h, l, c, q, r, e, ml, mh = frames
    result = [None] * HOURS
    for t in range(START_EXECUTION, HOURS):
        result[t] = risk_history(o, h, l, r, e, q, t)
    return result

def cell(path, mode, fee, order, frames, sources, risks):
    o, h, l, c, q, r, e, ml, mh = frames
    growth, opportunity, relative, stress, router = sources
    cash = float(CAQITAL[mode])
    initial = cash
    old = np.zeros(4)
    pending = np.zeros(4)
    rebalance = False
    allocator = AQAllocator()
    peak = cash
    max_dd = 0.
    min_nav = cash
    gross_peak = net_peak = concentration_peak = 0.
    fees = slippage = funding = turnover = 0.
    rebalances = 0
    year_start = {'2023': cash}
    year_end = {}
    year_peak = {'2023': cash}
    year_dd = {'2023': 0., '2024': 0.}
    deltas = {'2023': [], '2024': []}
    returns = {'2023': [], '2024': []}
    days = {'2023': 0, '2024': 0}
    positive = {'2023': 0, '2024': 0}
    day_start = cash
    for t in range(HOURS):
        if t >= FIRST_2023:
            year = '2023' if t < FIRST_2024 else '2024'
            if t == FIRST_2024:
                year_start['2024'] = cash
                year_peak['2024'] = cash
                day_start = cash
            previous_cash = cash
            if t >= START_EXECUTION:
                try:
                    down, up, bound, minq = risks[t]
                    target = govern(
                        cash, old, c[t - 1], o[t], pending, rebalance,
                        down, up, bound, q[t - 1], minq,
                        fee_mode=fee, funding_order=order)
                    out = settle_hour(
                        cash, old, c[t - 1], o[t], h[t], l[t], c[t],
                        target, r[t], e[t], ml[t], mh[t],
                        fee_mode=fee, funding_order=order)
                except Exception as exc:
                    raise ValueError('AQ_T' + str(t) + '_' + str(exc)) from exc
                cash = float(out['cash'])
                old = out['units'].copy()
                if (out['hidden_borrow'] or not out['cash_settled'] or
                    not np.isclose(out['equity'], cash, rtol=0, atol=1e-7)):
                    raise ValueError('AQ_NAV_RECONCILIATION_T' + str(t))
                fees += out['fees']
                slippage += out['slippage']
                funding += out['funding']
                turnover += out['turnover']
                rebalances += int(out['turnover'] > 1e-10)
                notionals = np.abs(old * c[t])
                gross = float(notionals.sum())
                gross_peak = max(gross_peak, gross / cash)
                net_peak = max(net_peak, abs(float(old @ c[t])) / cash)
                if gross > 0:
                    concentration_peak = max(
                        concentration_peak, float(notionals.max() / gross))
            delta = cash - previous_cash
            deltas[year].append(float(delta))
            returns[year].append(float(delta / previous_cash))
            peak = max(peak, cash)
            min_nav = min(min_nav, cash)
            max_dd = max(max_dd, 1. - cash / peak)
            year_peak[year] = max(year_peak[year], cash)
            year_dd[year] = max(year_dd[year], 1. - cash / year_peak[year])
            if t % 24 == 23:
                days[year] += 1
                positive[year] += int(cash > day_start)
                day_start = cash
            if t == FIRST_2024 - 1:
                year_end['2023'] = cash
            if t == HOURS - 1:
                year_end['2024'] = cash
        s = np.stack((growth[t], opportunity[t], relative[t], stress[t]))
        if path == 'AQ_core_only':
            s[1:] = 0.
        elif path == 'AQ_minus_opportunity':
            s[1] = 0.
        elif path == 'AQ_minus_RV':
            s[2] = 0.
        elif path == 'AQ_minus_stress':
            s[3] = 0.
        lr = np.log(c[t] / c[t - 1]) if t else np.zeros(4)
        allocator.observe(lr, r[t], e[t])
        pending, rebalance = allocator.decide(
            s, str(router['state'][t]), t)
    annual = {}
    for yr, duration in (('2023', 365), ('2024', 366)):
        start, end = year_start[yr], year_end[yr]
        annual[yr] = {
            'start_nav': float(start), 'end_nav': float(end),
            'net_return': float(end / start - 1.),
            'annualized_cagr': float((end / start) ** (365.25 / duration) - 1.),
            'net_log_growth': float(math.log(end / start)),
            'max_drawdown': float(year_dd[yr]),
            **metrics(deltas[yr], returns[yr], positive[yr], days[yr])}
    return {
        'path': path, 'mode': mode, 'fee': fee, 'order': order,
        'passed': True, 'historical_training_only': True,
        'validation_2025_read': False, 'external_benchmarks_used': False,
        'executed_hours': HOURS - START_EXECUTION,
        'rebalances': rebalances, 'initial_nav': initial, 'final_nav': cash,
        'net_total_return': float(cash / initial - 1.),
        'net_log_growth': float(math.log(cash / initial)),
        'two_year_cagr': float((cash / initial) ** (365.25 / 731) - 1.),
        'max_drawdown': float(max_dd), 'min_nav': float(min_nav),
        'max_gross_to_nav': float(gross_peak),
        'max_abs_net_to_nav': float(net_peak),
        'max_single_asset_gross_concentration': float(concentration_peak),
        'turnover': float(turnover), 'fees': float(fees),
        'slippage': float(slippage), 'funding': float(funding),
        'annual': annual,
        **metrics(deltas['2023'] + deltas['2024'],
                  returns['2023'] + returns['2024'],
                  positive['2023'] + positive['2024'],
                  days['2023'] + days['2024']),
    }

def run(path):
    if path not in PATHS:
        raise ValueError('AQ_UNKNOWN_PATH')
    frames, manifest = load_official()
    sources = source_bundle(frames[3], frames[1], frames[2],
                            frames[5], frames[6], frames[4])
    risks = prepare_risk(frames)
    cells = []
    for mode, fee, order in itertools.product(CAQITAL, FEES, ORDERS):
        try:
            cells.append(cell(path, mode, fee, order, frames, sources, risks))
        except Exception as exc:
            cells.append({
                'path': path, 'mode': mode, 'fee': fee, 'order': order,
                'passed': False, 'reason': str(exc)[:450],
                'historical_training_only': True,
                'validation_2025_read': False})
    passed = len(cells) == 18 and all(x['passed'] for x in cells)
    return {
        'architecture': 'AQ', 'path': path,
        'historical_training_only': True, 'validation_2025_read': False,
        'external_benchmarks_used': False, 'cells_expected': 18,
        'source_manifest_sha256': hashlib.sha256(json.dumps(
            manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'cells': cells,
        'decision': 'PASS_AQ_PATH_18_MECHAQICAL_ONLY' if passed else
                    'REJECT_AQ_PATH_SURVIVAL',
    }

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--path', choices=PATHS, required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    a = run(args.path)
    with open(args.output, 'w') as f:
        json.dump(a, f, sort_keys=True, indent=2, allow_nan=False)
    print('AQ_TRAINING_PATH', a['path'], a['decision'],
          'survived', sum(c['passed'] for c in a['cells']),
          'of', len(a['cells']))
    raise SystemExit(0 if all(c['passed'] for c in a['cells']) else 2)
