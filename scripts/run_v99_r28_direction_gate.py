from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
sys.path.insert(0, str(PROJECT / 'scripts'))

from cryptoai_v13.backtest import screen
from paper_once_v15 import build_v15
from run_v99_r25_trisleeve_meta import stats, sdata, cap, run

REPORT = PROJECT / 'reports' / 'candidate_v99_r28_direction_gate.json'
H = (7, 30, 90, 180, 365)


def direction_factor(raw, close, p):
    r24 = close.pct_change(24, fill_method=None)
    r72 = close.pct_change(72, fill_method=None)
    ema = close.ewm(span=336, adjust=False, min_periods=336).mean()
    long = raw > 0
    short = raw < 0
    adverse = (
        (long & ((r24 <= -p['adverse24']) | (r72 <= -p['adverse72'])))
        | (short & ((r24 >= p['adverse24']) | (r72 >= p['adverse72'])))
    ).fillna(False)
    if p['cooldown'] > 1:
        adverse = adverse.astype(float).rolling(p['cooldown'], min_periods=1).max().gt(0)
    aligned = (
        (long & (r24 >= p['boost24']) & (r72 >= p['boost72']) & (close >= ema))
        | (short & (r24 <= -p['boost24']) & (r72 <= -p['boost72']) & (close <= ema))
    ).fillna(False)
    factor = pd.DataFrame(1.0, index=raw.index, columns=raw.columns)
    factor = factor.mask(aligned, p['boost_scale'])
    factor = factor.mask(adverse, p['cut_scale'])
    return factor, adverse, aligned


def build_targets(raw, close, p):
    factor, adverse, aligned = direction_factor(raw, close, p)
    return cap(raw * factor, p['gross_cap']), adverse, aligned


def exact_eval(data, targets, ex, guard, base_gross, cost, gross):
    return run(data, targets, ex, cost, gross, guard).equity


def slice_eval(data, targets, raw, ex, guard, base_gross, cost, start, end):
    d = sdata(data, start, end)
    t = targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    r = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    a = run(d, t, ex, cost, base_gross, guard).equity
    b = run(d, r, ex, cost, base_gross, guard).equity
    return stats(a), stats(b)


def main():
    cand, data, raw, _, _, quarantined, metadata = build_v15()
    v14 = json.loads((PROJECT / 'config' / cand['parent_candidate_config']).read_text())
    finalist = json.loads((PROJECT / 'config' / v14['frozen_core_config']).read_text())
    base = json.loads((PROJECT / 'config' / finalist['base_candidate_config']).read_text())
    ex = base['execution']
    guard = v14['circuit_breaker']
    base_gross = float(v14['allocation']['gross_drift_guard_cap'])
    base_cost = float(ex['base_cost_per_side'])
    severe_cost = float(ex['severe_cost_per_side'])

    core = run(data, raw, ex, base_cost, base_gross, guard).equity
    core_sev = run(data, raw, ex, severe_cost, base_gross, guard).equity
    v15 = stats(core)
    v15_sev = stats(core_sev)

    adverse_presets = ((0.025, 0.05), (0.035, 0.07), (0.05, 0.10))
    boost_presets = ((0.015, 0.03), (0.025, 0.05), (0.04, 0.08))
    screened = []
    target_cache = {}

    for (a24, a72), (b24, b72), cut_scale, boost_scale, cooldown, gross in itertools.product(
        adverse_presets, boost_presets, (0.0, 0.25, 0.50), (1.10, 1.20, 1.30), (6, 12, 24), (base_gross, 1.90, 2.10)
    ):
        p = {
            'adverse24': a24, 'adverse72': a72,
            'boost24': b24, 'boost72': b72,
            'cut_scale': cut_scale, 'boost_scale': boost_scale,
            'cooldown': cooldown, 'gross_cap': gross,
        }
        key = f"a{a24:.3f}_{a72:.3f}_b{b24:.3f}_{b72:.3f}_c{cut_scale:.2f}_x{boost_scale:.2f}_p{cooldown}_g{gross:.3f}"
        targets, adverse, aligned = build_targets(raw, data.close, p)
        approx = screen(data, targets, cost_per_side=base_cost).equity
        s = stats(approx)
        base_approx = screen(data, raw, cost_per_side=base_cost).equity
        bs = stats(base_approx)
        wealth = (1 + s['return']) / max(1e-12, 1 + bs['return'])
        dd = abs(s['max_drawdown']) / max(1e-12, abs(bs['max_drawdown']))
        worst = abs(s['worst_day']) / max(1e-12, abs(bs['worst_day']))
        score = 4*np.log(max(wealth,1e-12)) + 4*max(0,1-dd) - 5*max(0,dd-1) - 2*max(0,worst-1)
        screened.append({
            'key': key, 'params': p, 'screen': s,
            'screen_wealth_ratio': float(wealth), 'screen_dd_ratio': float(dd),
            'screen_worst_ratio': float(worst),
            'adverse_fraction': float(adverse.to_numpy(dtype=float).mean()),
            'aligned_fraction': float(aligned.to_numpy(dtype=float).mean()),
            'screen_score': float(score),
        })
        target_cache[key] = targets

    screened.sort(key=lambda z: z['screen_score'], reverse=True)
    exact_rows = []
    split = int(len(core) * 0.60)
    hold_start = core.index[min(split + 1, len(core)-1)]
    v15_hold = stats(core.loc[hold_start:])

    for row in screened[:36]:
        p = row['params']
        targets = target_cache[row['key']]
        eq = run(data, targets, ex, base_cost, p['gross_cap'], guard).equity
        s = stats(eq)
        hold = stats(eq.loc[hold_start:])
        wealth = (1+s['return']) / max(1e-12, 1+v15['return'])
        hold_wealth = (1+hold['return']) / max(1e-12, 1+v15_hold['return'])
        dd = abs(s['max_drawdown']) / max(1e-12, abs(v15['max_drawdown']))
        worst = abs(s['worst_day']) / max(1e-12, abs(v15['worst_day']))
        exact_score = 5*np.log(max(wealth,1e-12)) + 4*np.log(max(hold_wealth,1e-12)) + 5*max(0,1-dd) - 7*max(0,dd-1) - 3*max(0,worst-1)
        exact_rows.append({**row, 'summary': s, 'holdout': hold, 'wealth_ratio_to_v15': float(wealth), 'holdout_wealth_ratio_to_v15': float(hold_wealth), 'drawdown_ratio_to_v15': float(dd), 'worst_day_ratio_to_v15': float(worst), 'exact_score': float(exact_score)})

    exact_rows.sort(key=lambda z: z['exact_score'], reverse=True)
    finalists = []
    end = data.close.index[-1]
    for row in exact_rows[:8]:
        p = row['params']
        targets = target_cache[row['key']]
        iso, iso_v15, rw, dw, ww, pw = {}, {}, {}, {}, {}, {}
        for days in H:
            a, b = slice_eval(data, targets, raw, ex, guard, p['gross_cap'], base_cost, end-pd.Timedelta(days=days), end)
            k = str(days)
            iso[k], iso_v15[k] = a, b
            rw[k] = a['return'] >= b['return']
            dw[k] = abs(a['max_drawdown']) <= abs(b['max_drawdown'])
            ww[k] = abs(a['worst_day']) <= abs(b['worst_day'])
            pw[k] = a['positive_days'] >= b['positive_days']
        sev = stats(run(data, targets, ex, severe_cost, p['gross_cap'], guard).equity)
        severe_ratio = (1+sev['return']) / max(1e-12, 1+v15_sev['return'])
        gate = bool(
            all(rw.values()) and all(dw.values()) and all(ww.values())
            and row['wealth_ratio_to_v15'] >= 1.50
            and row['holdout_wealth_ratio_to_v15'] >= 1.25
            and row['drawdown_ratio_to_v15'] <= 0.70
            and row['worst_day_ratio_to_v15'] <= 0.75
            and severe_ratio >= 1.25
        )
        finalists.append({**row, 'isolated': iso, 'isolated_v15': iso_v15, 'isolated_return_wins_vs_v15': rw, 'isolated_drawdown_wins_vs_v15': dw, 'isolated_worst_day_wins_vs_v15': ww, 'isolated_positive_days_wins_vs_v15': pw, 'severe_cost': sev, 'severe_wealth_ratio_to_v15': float(severe_ratio), 'superior_gate_passed': gate})

    finalists.sort(key=lambda z: (z['superior_gate_passed'], sum(z['isolated_return_wins_vs_v15'].values()), sum(z['isolated_drawdown_wins_vs_v15'].values()), z['holdout_wealth_ratio_to_v15'], z['wealth_ratio_to_v15'], -z['drawdown_ratio_to_v15']), reverse=True)
    selected = finalists[0] if finalists else None
    out = {
        'study': 'V99 R28 direction-aware position gate',
        'status': 'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER',
        'objective': 'cut only positions moving materially against their requested direction while selectively boosting aligned positions, preserving the rest of V15',
        'screen_grid_size': len(screened), 'exact_screen_size': len(exact_rows),
        'v15': {'summary': v15, 'severe_cost': v15_sev},
        'selected': selected, 'finalists': finalists,
        'top_exact': exact_rows[:20], 'top_screen': screened[:40],
        'disclosure': 'Historical research only. Direction gates use only information available at close t for orders executed at open t+1. Screen replay is ranking-only; proof gates use exact stateful replay, isolated horizons, holdout, and severe costs. Any winner requires fresh forward validation.',
        'funding_quarantined_symbols': quarantined,
        'v15_metadata': metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'study': out['study'], 'screen_grid_size': len(screened), 'exact_screen_size': len(exact_rows), 'v15': out['v15'], 'selected': selected}, indent=2), flush=True)


if __name__ == '__main__':
    main()
