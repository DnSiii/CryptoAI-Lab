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
from run_v99_r25_trisleeve_meta import stats, sdata, run

REPORT = PROJECT / 'reports' / 'candidate_v99_r29_guard_frontier.json'
H = (7, 30, 90, 180, 365)


def shadow_guard_factor(eq, threshold, multiplier, cooldown):
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
        if (not active) and dd <= -abs(threshold):
            active = True
            until = i + int(cooldown)
        out[i] = multiplier if active else 1.0
        peak = max(peak, x)
    return pd.Series(out, index=eq.index)


def slice_eval(data, raw, ex, base_gross, base_cost, cand_guard, v15_guard, start, end):
    d = sdata(data, start, end)
    r = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    a = run(d, r, ex, base_cost, base_gross, cand_guard).equity
    b = run(d, r, ex, base_cost, base_gross, v15_guard).equity
    return stats(a), stats(b)


def main():
    cand, data, raw, _, _, quarantined, metadata = build_v15()
    v14 = json.loads((PROJECT / 'config' / cand['parent_candidate_config']).read_text())
    finalist = json.loads((PROJECT / 'config' / v14['frozen_core_config']).read_text())
    base = json.loads((PROJECT / 'config' / finalist['base_candidate_config']).read_text())
    ex = base['execution']
    v15_guard = v14['circuit_breaker']
    base_gross = float(v14['allocation']['gross_drift_guard_cap'])
    base_cost = float(ex['base_cost_per_side'])
    severe_cost = float(ex['severe_cost_per_side'])

    v15_eq = run(data, raw, ex, base_cost, base_gross, v15_guard).equity
    v15_sev_eq = run(data, raw, ex, severe_cost, base_gross, v15_guard).equity
    v15, v15_sev = stats(v15_eq), stats(v15_sev_eq)
    approx_base = screen(data, raw, cost_per_side=base_cost).equity
    approx_base_stats = stats(approx_base)

    approx_rows = []
    for threshold, multiplier, cooldown in itertools.product(
        (0.08,0.10,0.12,0.14,0.16,0.18,0.20),
        (0.0,0.20,0.40,0.60,0.80),
        (24,48,72,120,168,240)
    ):
        p = {'drawdown_threshold':threshold,'exposure_multiplier':multiplier,'cooldown_hours':cooldown}
        f = shadow_guard_factor(approx_base, threshold, multiplier, cooldown)
        t = raw.mul(f, axis=0)
        s = stats(screen(data, t, cost_per_side=base_cost).equity)
        wealth = (1+s['return']) / max(1e-12,1+approx_base_stats['return'])
        dd = abs(s['max_drawdown']) / max(1e-12,abs(approx_base_stats['max_drawdown']))
        worst = abs(s['worst_day']) / max(1e-12,abs(approx_base_stats['worst_day']))
        active_fraction = float((f < 0.999999).mean())
        score = 4*np.log(max(wealth,1e-12)) + 5*max(0,1-dd) - 6*max(0,dd-1) - 2*max(0,worst-1) - max(0,active_fraction-0.35)
        approx_rows.append({'params':p,'approx':s,'approx_wealth_ratio':float(wealth),'approx_drawdown_ratio':float(dd),'approx_worst_day_ratio':float(worst),'approx_guard_active_fraction':active_fraction,'approx_score':float(score)})

    approx_rows.sort(key=lambda z:z['approx_score'], reverse=True)
    split = int(len(v15_eq)*0.60)
    hold_start = v15_eq.index[min(split+1,len(v15_eq)-1)]
    v15_hold = stats(v15_eq.loc[hold_start:])
    exact_rows = []

    for row in approx_rows[:40]:
        p = row['params']
        eq = run(data, raw, ex, base_cost, base_gross, p).equity
        s, hold = stats(eq), stats(eq.loc[hold_start:])
        wealth = (1+s['return'])/max(1e-12,1+v15['return'])
        hold_wealth = (1+hold['return'])/max(1e-12,1+v15_hold['return'])
        dd = abs(s['max_drawdown'])/max(1e-12,abs(v15['max_drawdown']))
        worst = abs(s['worst_day'])/max(1e-12,abs(v15['worst_day']))
        score = 5*np.log(max(wealth,1e-12))+4*np.log(max(hold_wealth,1e-12))+5*max(0,1-dd)-7*max(0,dd-1)-3*max(0,worst-1)
        exact_rows.append({**row,'summary':s,'holdout':hold,'wealth_ratio_to_v15':float(wealth),'holdout_wealth_ratio_to_v15':float(hold_wealth),'drawdown_ratio_to_v15':float(dd),'worst_day_ratio_to_v15':float(worst),'exact_score':float(score)})

    exact_rows.sort(key=lambda z:z['exact_score'], reverse=True)
    finalists=[]; end=data.close.index[-1]
    for row in exact_rows[:10]:
        p=row['params']; iso={};iv={};rw={};dw={};ww={};pw={}
        for days in H:
            a,b=slice_eval(data,raw,ex,base_gross,base_cost,p,v15_guard,end-pd.Timedelta(days=days),end)
            k=str(days);iso[k]=a;iv[k]=b;rw[k]=a['return']>=b['return'];dw[k]=abs(a['max_drawdown'])<=abs(b['max_drawdown']);ww[k]=abs(a['worst_day'])<=abs(b['worst_day']);pw[k]=a['positive_days']>=b['positive_days']
        sev=stats(run(data,raw,ex,severe_cost,base_gross,p).equity)
        sr=(1+sev['return'])/max(1e-12,1+v15_sev['return'])
        gate=bool(all(rw.values()) and all(dw.values()) and all(ww.values()) and row['wealth_ratio_to_v15']>=1.50 and row['holdout_wealth_ratio_to_v15']>=1.25 and row['drawdown_ratio_to_v15']<=0.70 and row['worst_day_ratio_to_v15']<=0.75 and sr>=1.25)
        finalists.append({**row,'isolated':iso,'isolated_v15':iv,'isolated_return_wins_vs_v15':rw,'isolated_drawdown_wins_vs_v15':dw,'isolated_worst_day_wins_vs_v15':ww,'isolated_positive_days_wins_vs_v15':pw,'severe_cost':sev,'severe_wealth_ratio_to_v15':float(sr),'superior_gate_passed':gate})

    finalists.sort(key=lambda z:(z['superior_gate_passed'],sum(z['isolated_return_wins_vs_v15'].values()),sum(z['isolated_drawdown_wins_vs_v15'].values()),z['holdout_wealth_ratio_to_v15'],z['wealth_ratio_to_v15'],-z['drawdown_ratio_to_v15']),reverse=True)
    selected=finalists[0] if finalists else None
    out={'study':'V99 R29 circuit-breaker frontier','status':'RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER','objective':'find a causal drawdown guard that cuts risk earlier without sacrificing compounding','approx_grid_size':len(approx_rows),'exact_screen_size':len(exact_rows),'v15':{'summary':v15,'severe_cost':v15_sev,'guard':v15_guard},'selected':selected,'finalists':finalists,'top_exact':exact_rows[:25],'top_approx':approx_rows[:50],'disclosure':'Historical research only. Approximate screen is ranking-only; exact stateful replay, isolated resets, holdout, and severe costs determine the gate. Any winner must be frozen before fresh forward paper.','funding_quarantined_symbols':quarantined,'v15_metadata':metadata}
    REPORT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'study':out['study'],'approx_grid_size':len(approx_rows),'exact_screen_size':len(exact_rows),'v15':out['v15'],'selected':selected},indent=2),flush=True)

if __name__=='__main__':main()
