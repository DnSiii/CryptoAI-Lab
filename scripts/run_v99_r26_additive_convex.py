from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
sys.path.insert(0, str(PROJECT / 'scripts'))

from paper_once_v15 import build_v15
from run_v99_r25_trisleeve_meta import stats, sdata, run, regime, attack_targets, crash_targets

REPORT = PROJECT / 'reports' / 'candidate_v99_r26_additive_convex.json'
H = (7, 30, 90, 180, 365)


def combine_additive(core, attack, hedge, attack_weight, hedge_weight):
    idx = core.index.intersection(attack.index).intersection(hedge.index)
    rc = core.reindex(idx).pct_change(fill_method=None).fillna(0.0)
    ra = attack.reindex(idx).pct_change(fill_method=None).fillna(0.0)
    rh = hedge.reindex(idx).pct_change(fill_method=None).fillna(0.0)
    net = rc + float(attack_weight) * ra + float(hedge_weight) * rh
    return (1.0 + net).clip(lower=0.001).cumprod()


def eval_slice(data, raw, ex, guard, base_gross, cost, ap, hp, aw, hw, start, end):
    d = sdata(data, start, end)
    r = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    core = run(d, r, ex, cost, base_gross, guard).equity
    strong, stress = regime(core, d.close['BTCUSDT'])
    at = attack_targets(r, strong, ap['scale'], ap['gross'])
    attack = run(d, at, ex, cost, ap['gross'] + 0.10, None, (0.10, 0.25, 72)).equity
    ht = crash_targets(d, hp['t24'], hp['t72'], hp['breadth'], hp['topn'])
    hedge = run(d, ht, ex, cost, 1.10, None, (0.12, 0.25, 48)).equity
    return stats(combine_additive(core, attack, hedge, aw, hw)), stats(core)


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
    strong, stress = regime(core, data.close['BTCUSDT'])

    attacks = {}
    for scale, gross in itertools.product((1.5, 2.0, 2.5, 3.0), (1.8, 2.2, 2.6)):
        key = f'x{scale:.1f}_g{gross:.1f}'
        t = attack_targets(raw, strong, scale, gross)
        attacks[key] = (
            run(data, t, ex, base_cost, gross + 0.10, None, (0.10, 0.25, 72)).equity,
            run(data, t, ex, severe_cost, gross + 0.10, None, (0.10, 0.25, 72)).equity,
            {'scale': scale, 'gross': gross},
        )

    hedges = {}
    for t24, t72, breadth, topn in itertools.product(
        (-0.025, -0.035, -0.045), (-0.05, -0.07), (0.30, 0.40), (2, 3)
    ):
        key = f'h{t24:.3f}_{t72:.3f}_{breadth:.2f}_{topn}'
        t = crash_targets(data, t24, t72, breadth, topn)
        hedges[key] = (
            run(data, t, ex, base_cost, 1.10, None, (0.12, 0.25, 48)).equity,
            run(data, t, ex, severe_cost, 1.10, None, (0.12, 0.25, 48)).equity,
            {'t24': t24, 't72': t72, 'breadth': breadth, 'topn': topn},
        )

    split = int(len(core) * 0.60)
    hold_start = core.index[min(split + 1, len(core) - 1)]
    core_hold = stats(core.loc[hold_start:])
    rows = []

    for (ak, (ae, asev, ap)), (hk, (he, hsev, hp)), aw, hw in itertools.product(
        attacks.items(), hedges.items(), (0.10, 0.20, 0.30, 0.40), (0.10, 0.20, 0.30, 0.40)
    ):
        eq = combine_additive(core, ae, he, aw, hw)
        s = stats(eq)
        hold = stats(eq.loc[hold_start:])
        wealth = (1.0 + s['return']) / max(1e-12, 1.0 + v15['return'])
        hold_wealth = (1.0 + hold['return']) / max(1e-12, 1.0 + core_hold['return'])
        dd = abs(s['max_drawdown']) / max(1e-12, abs(v15['max_drawdown']))
        worst = abs(s['worst_day']) / max(1e-12, abs(v15['worst_day']))
        pos_delta = s['positive_days'] - v15['positive_days']
        score = (
            5.0 * np.log(max(wealth, 1e-12))
            + 4.0 * np.log(max(hold_wealth, 1e-12))
            + 4.0 * max(0.0, 1.0 - dd)
            - 6.0 * max(0.0, dd - 1.0)
            - 3.0 * max(0.0, worst - 1.0)
            + 2.0 * pos_delta
        )
        rows.append({
            'attack_key': ak, 'hedge_key': hk,
            'attack_params': ap, 'hedge_params': hp,
            'attack_weight': aw, 'hedge_weight': hw,
            'summary': s, 'holdout': hold,
            'wealth_ratio_to_v15': float(wealth),
            'holdout_wealth_ratio_to_v15': float(hold_wealth),
            'drawdown_ratio_to_v15': float(dd),
            'worst_day_ratio_to_v15': float(worst),
            'positive_day_delta_to_v15': float(pos_delta),
            'score': float(score),
        })

    rank = sorted(rows, key=lambda z: z['score'], reverse=True)
    finalists = []
    end = data.close.index[-1]

    for row in rank[:10]:
        iso, iso_v15, ret_wins, dd_wins, worst_wins, pos_wins = {}, {}, {}, {}, {}, {}
        for days in H:
            a, b = eval_slice(
                data, raw, ex, guard, base_gross, base_cost,
                row['attack_params'], row['hedge_params'],
                row['attack_weight'], row['hedge_weight'],
                end - pd.Timedelta(days=days), end,
            )
            k = str(days)
            iso[k], iso_v15[k] = a, b
            ret_wins[k] = a['return'] >= b['return']
            dd_wins[k] = abs(a['max_drawdown']) <= abs(b['max_drawdown'])
            worst_wins[k] = abs(a['worst_day']) <= abs(b['worst_day'])
            pos_wins[k] = a['positive_days'] >= b['positive_days']

        ae, asev, _ = attacks[row['attack_key']]
        he, hsev, _ = hedges[row['hedge_key']]
        sev = stats(combine_additive(core_sev, asev, hsev, row['attack_weight'], row['hedge_weight']))
        severe_ratio = (1.0 + sev['return']) / max(1e-12, 1.0 + v15_sev['return'])

        gate = bool(
            all(ret_wins.values())
            and all(dd_wins.values())
            and all(worst_wins.values())
            and row['wealth_ratio_to_v15'] >= 1.50
            and row['holdout_wealth_ratio_to_v15'] >= 1.25
            and row['drawdown_ratio_to_v15'] <= 0.70
            and row['worst_day_ratio_to_v15'] <= 0.75
            and severe_ratio >= 1.25
        )
        finalists.append({
            **row,
            'isolated': iso,
            'isolated_v15': iso_v15,
            'isolated_return_wins_vs_v15': ret_wins,
            'isolated_drawdown_wins_vs_v15': dd_wins,
            'isolated_worst_day_wins_vs_v15': worst_wins,
            'isolated_positive_days_wins_vs_v15': pos_wins,
            'severe_cost': sev,
            'severe_wealth_ratio_to_v15': float(severe_ratio),
            'superior_gate_passed': gate,
        })

    finalists.sort(
        key=lambda z: (
            z['superior_gate_passed'],
            sum(z['isolated_return_wins_vs_v15'].values()),
            sum(z['isolated_drawdown_wins_vs_v15'].values()),
            z['holdout_wealth_ratio_to_v15'], z['wealth_ratio_to_v15'],
            -z['drawdown_ratio_to_v15']
        ), reverse=True
    )
    selected = finalists[0] if finalists else None
    out = {
        'study': 'V99 R26 additive convex overlay',
        'status': 'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER',
        'architecture': '100% untouched V15 core plus independently governed strong-regime alpha overlay and crash-short hedge overlay; no capital rotation away from core',
        'grid_size': len(rows),
        'v15': {'summary': v15, 'severe_cost': v15_sev},
        'selected': selected,
        'finalists': finalists,
        'top_screen': rank[:40],
        'disclosure': 'Historical research only. Additive overlays use extra conditional notional and therefore must beat V15 on drawdown and worst-day gates despite higher temporary gross exposure. Any winner requires freezing and independent forward validation.',
        'funding_quarantined_symbols': quarantined,
        'v15_metadata': metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'study': out['study'], 'grid_size': len(rows), 'v15': out['v15'], 'selected': selected}, indent=2), flush=True)


if __name__ == '__main__':
    main()
