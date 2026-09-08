from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
sys.path.insert(0, str(PROJECT / 'scripts'))

from paper_once_v15 import build_v15
from run_v99_r25_trisleeve_meta import stats, sdata, cap, run

REPORT = PROJECT / 'reports' / 'candidate_v99_r27_discrete_governor.json'
H = (7, 30, 90, 180, 365)


def guard_factor(eq, g):
    vals = eq.astype(float).to_numpy()
    out = np.ones(len(vals), dtype=float)
    peak = 1.0
    active = False
    until = -1
    for i, x in enumerate(vals):
        if active and i >= until:
            active = False
            peak = x
        dd = x / peak - 1.0 if peak else -1.0
        if (not active) and dd <= -abs(g['drawdown_threshold']):
            active = True
            until = i + int(g['cooldown_hours'])
        out[i] = float(g['exposure_multiplier']) if active else 1.0
        peak = max(peak, x)
    return pd.Series(out, index=eq.index)


def masks(core, close, strong_level, stress_level, cooldown):
    btc = close['BTCUSDT']
    r24 = btc.pct_change(24, fill_method=None)
    r72 = btc.pct_change(72, fill_method=None)
    r7 = btc.pct_change(168, fill_method=None)
    r30 = btc.pct_change(720, fill_method=None)
    ema14 = btc.ewm(span=336, adjust=False, min_periods=336).mean()
    breadth24 = close.pct_change(24, fill_method=None).gt(0).mean(axis=1)
    breadth72 = close.pct_change(72, fill_method=None).gt(0).mean(axis=1)
    cr7 = core.pct_change(168, fill_method=None)
    cr30 = core.pct_change(720, fill_method=None)
    cdd = core / core.cummax() - 1.0

    if strong_level == 1:
        strong = (btc > ema14) & (r7 > 0.015) & (r30 > 0.03) & (breadth72 > 0.52) & (cr7 > 0) & (cdd > -0.06)
    elif strong_level == 2:
        strong = (btc > ema14) & (r7 > 0.03) & (r30 > 0.06) & (breadth72 > 0.57) & (cr7 > 0.015) & (cr30 > 0.04) & (cdd > -0.045)
    else:
        strong = (btc > ema14) & (r7 > 0.05) & (r30 > 0.09) & (breadth72 > 0.62) & (cr7 > 0.025) & (cr30 > 0.07) & (cdd > -0.03)

    if stress_level == 1:
        stress = (r24 < -0.025) | ((btc < ema14) & (r72 < -0.04) & (breadth24 < 0.42)) | ((r7 < -0.05) & (breadth72 < 0.42))
    elif stress_level == 2:
        stress = (r24 < -0.035) | ((btc < ema14) & (r72 < -0.055) & (breadth24 < 0.36)) | ((r7 < -0.065) & (breadth72 < 0.38))
    else:
        stress = (r24 < -0.045) | ((btc < ema14) & (r72 < -0.07) & (breadth24 < 0.30)) | ((r7 < -0.08) & (breadth72 < 0.34))

    stress = stress.fillna(False).astype(float).rolling(int(cooldown), min_periods=1).max().gt(0)
    strong = strong.fillna(False) & ~stress
    return strong, stress


def scale_series(core, close, p):
    strong, stress = masks(core, close, p['strong_level'], p['stress_level'], p['cooldown'])
    s = pd.Series(1.0, index=core.index)
    s.loc[strong] = p['attack_scale']
    s.loc[stress] = p['defense_scale']
    return s, strong, stress


def build_targets(raw, shadow, close, guard, p):
    scale, strong, stress = scale_series(shadow, close, p)
    t = raw.mul(guard_factor(shadow, guard) * scale, axis=0)
    return cap(t, p['gross_cap']), scale, strong, stress


def exact_candidate(data, raw, ex, guard, cost, p):
    shadow = run(data, raw, ex, cost, p['base_gross'], guard).equity
    targets, scale, strong, stress = build_targets(raw, shadow, data.close, guard, p)
    equity = run(data, targets, ex, cost, p['gross_cap'], None).equity
    return equity, shadow, scale, strong, stress


def slice_eval(data, raw, ex, guard, cost, p, start, end):
    d = sdata(data, start, end)
    r = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    eq, shadow, _, _, _ = exact_candidate(d, r, ex, guard, cost, p)
    return stats(eq), stats(shadow)


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

    shadow = run(data, raw, ex, base_cost, base_gross, guard).equity
    shadow_sev = run(data, raw, ex, severe_cost, base_gross, guard).equity
    v15 = stats(shadow)
    v15_sev = stats(shadow_sev)
    rc = shadow.pct_change(fill_method=None).fillna(0.0)

    approx = []
    for attack_scale, defense_scale, strong_level, stress_level, cooldown, gross in itertools.product(
        (1.15, 1.30, 1.45, 1.60), (0.25, 0.40, 0.55, 0.70), (1, 2, 3), (1, 2, 3), (24, 48, 72), (1.9, 2.2, 2.5)
    ):
        p = {
            'attack_scale': attack_scale,
            'defense_scale': defense_scale,
            'strong_level': strong_level,
            'stress_level': stress_level,
            'cooldown': cooldown,
            'gross_cap': gross,
            'base_gross': base_gross,
        }
        scale, strong, stress = scale_series(shadow, data.close, p)
        approx_eq = (1.0 + rc * scale.shift(1).fillna(1.0)).clip(lower=0.001).cumprod()
        s = stats(approx_eq)
        wealth = (1 + s['return']) / max(1e-12, 1 + v15['return'])
        dd = abs(s['max_drawdown']) / max(1e-12, abs(v15['max_drawdown']))
        worst = abs(s['worst_day']) / max(1e-12, abs(v15['worst_day']))
        attack_frac = float(strong.mean())
        defense_frac = float(stress.mean())
        score = 4.0 * np.log(max(wealth, 1e-12)) + 4.0 * max(0.0, 1.0-dd) - 5.0 * max(0.0, dd-1.0) - 2.0 * max(0.0, worst-1.0)
        if defense_frac > 0.35:
            score -= 3.0 * (defense_frac - 0.35)
        approx.append({'params': p, 'approx': s, 'approx_wealth_ratio': float(wealth), 'approx_dd_ratio': float(dd), 'approx_worst_ratio': float(worst), 'attack_fraction': attack_frac, 'defense_fraction': defense_frac, 'score': float(score)})

    approx.sort(key=lambda z: z['score'], reverse=True)
    screened = approx[:36]
    exact_rows = []
    split = int(len(shadow) * 0.60)
    hold_start = shadow.index[min(split + 1, len(shadow)-1)]
    v15_hold = stats(shadow.loc[hold_start:])

    for row in screened:
        p = row['params']
        eq, sh, scale, strong, stress = exact_candidate(data, raw, ex, guard, base_cost, p)
        s = stats(eq)
        hold = stats(eq.loc[hold_start:])
        wealth = (1 + s['return']) / max(1e-12, 1 + v15['return'])
        hold_wealth = (1 + hold['return']) / max(1e-12, 1 + v15_hold['return'])
        dd = abs(s['max_drawdown']) / max(1e-12, abs(v15['max_drawdown']))
        worst = abs(s['worst_day']) / max(1e-12, abs(v15['worst_day']))
        score = 5*np.log(max(wealth,1e-12)) + 4*np.log(max(hold_wealth,1e-12)) + 5*max(0,1-dd) - 7*max(0,dd-1) - 3*max(0,worst-1)
        exact_rows.append({**row, 'summary': s, 'holdout': hold, 'wealth_ratio_to_v15': float(wealth), 'holdout_wealth_ratio_to_v15': float(hold_wealth), 'drawdown_ratio_to_v15': float(dd), 'worst_day_ratio_to_v15': float(worst), 'exact_score': float(score), 'attack_fraction_exact': float(strong.mean()), 'defense_fraction_exact': float(stress.mean())})

    exact_rows.sort(key=lambda z: z['exact_score'], reverse=True)
    finalists = []
    end = data.close.index[-1]
    for row in exact_rows[:8]:
        p = row['params']
        iso, iso_v15, rw, dw, ww, pw = {}, {}, {}, {}, {}, {}
        for days in H:
            a, b = slice_eval(data, raw, ex, guard, base_cost, p, end-pd.Timedelta(days=days), end)
            k = str(days)
            iso[k], iso_v15[k] = a, b
            rw[k] = a['return'] >= b['return']
            dw[k] = abs(a['max_drawdown']) <= abs(b['max_drawdown'])
            ww[k] = abs(a['worst_day']) <= abs(b['worst_day'])
            pw[k] = a['positive_days'] >= b['positive_days']

        sev, _, _, _, _ = exact_candidate(data, raw, ex, guard, severe_cost, p)
        sev_stats = stats(sev)
        severe_ratio = (1 + sev_stats['return']) / max(1e-12, 1 + v15_sev['return'])
        gate = bool(
            all(rw.values()) and all(dw.values()) and all(ww.values())
            and row['wealth_ratio_to_v15'] >= 1.50
            and row['holdout_wealth_ratio_to_v15'] >= 1.25
            and row['drawdown_ratio_to_v15'] <= 0.70
            and row['worst_day_ratio_to_v15'] <= 0.75
            and severe_ratio >= 1.25
            and row['defense_fraction_exact'] <= 0.35
        )
        finalists.append({**row, 'isolated': iso, 'isolated_v15': iso_v15, 'isolated_return_wins_vs_v15': rw, 'isolated_drawdown_wins_vs_v15': dw, 'isolated_worst_day_wins_vs_v15': ww, 'isolated_positive_days_wins_vs_v15': pw, 'severe_cost': sev_stats, 'severe_wealth_ratio_to_v15': float(severe_ratio), 'superior_gate_passed': gate})

    finalists.sort(key=lambda z: (z['superior_gate_passed'], sum(z['isolated_return_wins_vs_v15'].values()), sum(z['isolated_drawdown_wins_vs_v15'].values()), z['holdout_wealth_ratio_to_v15'], z['wealth_ratio_to_v15'], -z['drawdown_ratio_to_v15']), reverse=True)
    selected = finalists[0] if finalists else None
    out = {
        'study': 'V99 R27 discrete causal risk governor',
        'status': 'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER',
        'objective': 'keep V15 near full exposure in normal regimes, boost only strong regimes, and de-risk only short causal stress episodes',
        'approx_grid_size': len(approx),
        'exact_screen_size': len(exact_rows),
        'v15': {'summary': v15, 'severe_cost': v15_sev},
        'selected': selected,
        'finalists': finalists,
        'top_exact': exact_rows[:20],
        'top_approx': approx[:40],
        'disclosure': 'Historical research only. Approximate screening is never used as proof; gates are based on exact replay, isolated horizons, holdout, and severe-cost replay. Any winner still requires freezing and fresh forward validation.',
        'funding_quarantined_symbols': quarantined,
        'v15_metadata': metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'study': out['study'], 'approx_grid_size': len(approx), 'exact_screen_size': len(exact_rows), 'v15': out['v15'], 'selected': selected}, indent=2), flush=True)


if __name__ == '__main__':
    main()
