from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r55_low_hedge_amplitude_frontier as r55

r36 = r55.r36
r37 = r55.r37
cap = r55.cap
REPORT = PROJECT / "reports" / "candidate_v99_r67_dynamic_hedge_router.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
TRAIN_END = pd.Timestamp("2024-01-05T00:00:00+00:00")
P15 = r55.params(0.15)
P25 = r55.params(0.25)

# Fixed from R66 first-60% training split. Holdout did not participate in fitting.
VOL24_Q80 = 0.051253990575389194
BTC24_Q20 = -0.019039657268342308
H15_GROSS_Q20 = 0.4478403629219058
BTC72_Q20 = -0.03338695841687384

ROUTERS = (
    {"name": "market_vol24_high", "rule": "vol24"},
    {"name": "btc24_down", "rule": "btc24"},
    {"name": "btc72_down", "rule": "btc72"},
    {"name": "h15_gross_low", "rule": "gross"},
    {"name": "two_of_four", "rule": "vote2"},
)


def build_pair(data, raw, ex, guard, gross, cost):
    core = r36.run(data, raw, ex, cost, gross, guard)
    t15, active15 = r37.r30_targets(raw, core.equity, data.close, P15)
    t25, active25 = r37.r30_targets(raw, core.equity, data.close, P25)
    t15 = cap(t15, float(P15["gross_cap"]))
    t25 = cap(t25, float(P25["gross_cap"]))
    res15 = r36.run(data, t15, ex, cost, float(P15["gross_cap"]), guard)
    res25 = r36.run(data, t25, ex, cost, float(P25["gross_cap"]), guard)
    return core, res15, res25, t15, t25, active15, active25


def gate_series(data, t15: pd.DataFrame, router: dict) -> tuple[pd.Series, dict]:
    close = data.close.reindex(t15.index)
    btc = close["BTCUSDT"]
    r24 = close.pct_change(24, fill_method=None)
    market_vol = r24.abs().median(axis=1)
    btc24 = btc.pct_change(24, fill_method=None)
    btc72 = btc.pct_change(72, fill_method=None)
    h15_gross = t15.abs().sum(axis=1)

    c1 = market_vol >= VOL24_Q80
    c2 = btc24 <= BTC24_Q20
    c3 = btc72 <= BTC72_Q20
    c4 = h15_gross <= H15_GROSS_Q20
    votes = c1.astype(int) + c2.astype(int) + c3.astype(int) + c4.astype(int)

    rule = router["rule"]
    if rule == "vol24": gate = c1
    elif rule == "btc24": gate = c2
    elif rule == "btc72": gate = c3
    elif rule == "gross": gate = c4
    elif rule == "vote2": gate = votes >= 2
    else: raise ValueError(router)

    gate = gate.fillna(False)
    return gate, {
        "gate_fraction": float(gate.mean()),
        "vol24_fraction": float(c1.fillna(False).mean()),
        "btc24_fraction": float(c2.fillna(False).mean()),
        "btc72_fraction": float(c3.fillna(False).mean()),
        "gross_fraction": float(c4.fillna(False).mean()),
        "mean_votes": float(votes.fillna(0).mean()),
    }


def build_candidate(data, raw, ex, guard, gross, cost, router):
    core, res15, res25, t15, t25, active15, active25 = build_pair(data, raw, ex, guard, gross, cost)
    gate, diag = gate_series(data, t15, router)
    targets = t15.copy()
    targets.loc[gate, :] = t25.loc[gate, :]
    targets = cap(targets, float(P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(P15["gross_cap"]), guard)
    diag.update({
        "h15_active_fraction": float(active15.mean()),
        "h25_active_fraction": float(active25.mean()),
        "effective_switch_fraction": float((gate & active15.reindex(gate.index).fillna(False)).mean()),
    })
    return result, res15, res25, targets, gate, diag


def isolated(data, raw, ex, guard, gross, cost, router, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, p15, p25, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, router)
    return r36.stats(result.equity), r36.stats(p15.equity), r36.stats(p25.equity)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    _, parent15, parent25, _, _, _, _ = build_pair(data, raw, ex, guard, gross, base_cost)
    _, parent15_sev, parent25_sev, _, _, _, _ = build_pair(data, raw, ex, guard, gross, severe_cost)
    parent15_stats = r36.stats(parent15.equity)
    parent25_stats = r36.stats(parent25.equity)
    parent15_severe = r36.stats(parent15_sev.equity)
    parent25_severe = r36.stats(parent25_sev.equity)
    hold_idx = parent15.equity.index[parent15.equity.index > TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else parent15.equity.index[-1]
    parent15_hold = r36.stats(parent15.equity.loc[hold_start:])
    parent25_hold = r36.stats(parent25.equity.loc[hold_start:])

    benchmarks = r55.benchmark_items(cand, data, raw, ex, guard, gross)
    full_bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"])) for n, x in benchmarks.items()}
    severe_bench = {n: r36.exact_benchmark(x, float(x["execution"]["severe_cost_per_side"])) for n, x in benchmarks.items()}
    full_env = r36.envelope(full_bench); severe_env = r36.envelope(severe_bench)

    rows = []
    for router in ROUTERS:
        result, _, _, _, gate, diag = build_candidate(data, raw, ex, guard, gross, base_cost, router)
        sev_result, _, _, _, sev_gate, sev_diag = build_candidate(data, raw, ex, guard, gross, severe_cost, router)
        s = r36.stats(result.equity); sev = r36.stats(sev_result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        parent15_wr = (1+s["return"]) / max(1e-12, 1+parent15_stats["return"])
        parent15_hr = (1+hold["return"]) / max(1e-12, 1+parent15_hold["return"])
        parent15_sr = (1+sev["return"]) / max(1e-12, 1+parent15_severe["return"])
        score = (
            10*np.log(max(parent15_wr,1e-12)) + 8*np.log(max(parent15_hr,1e-12)) + 8*np.log(max(parent15_sr,1e-12))
            + 18*max(0,1-abs(s["max_drawdown"])/abs(parent15_stats["max_drawdown"]))
            - 20*max(0,abs(s["max_drawdown"])/abs(parent15_stats["max_drawdown"])-1)
            + 16*max(0,1-abs(s["worst_day"])/abs(parent15_stats["worst_day"]))
            - 18*max(0,abs(s["worst_day"])/abs(parent15_stats["worst_day"])-1)
        )
        rows.append({
            "router": router, "summary": s, "holdout_after_r66_train": hold, "severe_cost": sev,
            "diagnostics": diag, "severe_diagnostics": sev_diag,
            "wealth_ratio_to_h15": float(parent15_wr), "holdout_wealth_ratio_to_h15": float(parent15_hr),
            "severe_wealth_ratio_to_h15": float(parent15_sr), "score": float(score),
        })
        gc.collect()

    common_end = min(x["data"].close.index[-1] for x in benchmarks.values())
    earliest = max(x["data"].close.index[0] for x in benchmarks.values())
    finalists = []
    for row in rows:
        router = row["router"]
        iso, iso15, iso25, wins, parent_wins = {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=int(days))
            c, p15, p25 = isolated(data, raw, ex, guard, gross, base_cost, router, start, common_end)
            bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"]), start, common_end) for n,x in benchmarks.items()}
            env = r36.envelope(bench); k=str(days)
            iso[k], iso15[k], iso25[k] = c,p15,p25
            wins[k] = {
                "return": c["return"] >= env["return"],
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
            }
            parent_wins[k] = {
                "return_vs_h15": c["return"] >= p15["return"],
                "drawdown_vs_h15": abs(c["max_drawdown"]) <= abs(p15["max_drawdown"]),
                "worst_day_vs_h15": abs(c["worst_day"]) <= abs(p15["worst_day"]),
            }
        alt={}
        for days in ALT_HORIZONS:
            start=common_end-pd.Timedelta(days=int(days))
            if start<earliest: continue
            c,p15,p25=isolated(data,raw,ex,guard,gross,base_cost,router,start,common_end)
            bench={n:r36.exact_benchmark(x,float(x["execution"]["base_cost_per_side"]),start,common_end) for n,x in benchmarks.items()}
            env=r36.envelope(bench)
            alt[str(days)]={"candidate":c,"h15":p15,"h25":p25,"envelope":env,
                "return_win":c["return"]>=env["return"],"drawdown_win":abs(c["max_drawdown"])<=env["max_drawdown_abs"],
                "worst_day_win":abs(c["worst_day"])<=env["worst_day_abs"]}
        horizon_wins=sum(sum(v.values()) for v in wins.values())
        parent_horizon_wins=sum(sum(v.values()) for v in parent_wins.values())
        full_parent_pass=(row["summary"]["return"]>=parent15_stats["return"] and abs(row["summary"]["max_drawdown"])<=abs(parent15_stats["max_drawdown"]) and abs(row["summary"]["worst_day"])<=abs(parent15_stats["worst_day"]))
        hold_parent_pass=(row["holdout_after_r66_train"]["return"]>=parent15_hold["return"] and abs(row["holdout_after_r66_train"]["max_drawdown"])<=abs(parent15_hold["max_drawdown"]))
        severe_parent_pass=(row["severe_cost"]["return"]>=parent15_severe["return"] and abs(row["severe_cost"]["max_drawdown"])<=abs(parent15_severe["max_drawdown"]) and abs(row["severe_cost"]["worst_day"])<=abs(parent15_severe["worst_day"]))
        finalists.append({**row,"isolated":iso,"isolated_h15":iso15,"isolated_h25":iso25,"envelope_wins":wins,
            "parent_horizon_wins":parent_wins,"alternative_horizons":alt,"requested_horizon_dimension_wins":int(horizon_wins),
            "requested_parent_dimension_wins":int(parent_horizon_wins),"full_parent_dominance":bool(full_parent_pass),
            "holdout_parent_dominance":bool(hold_parent_pass),"severe_parent_dominance":bool(severe_parent_pass),
            "dominant_gate_passed":bool(full_parent_pass and hold_parent_pass and severe_parent_pass and parent_horizon_wins==15)})
        gc.collect()

    finalists.sort(key=lambda z:(z["dominant_gate_passed"],z["full_parent_dominance"],z["holdout_parent_dominance"],z["severe_parent_dominance"],z["requested_parent_dimension_wins"],z["requested_horizon_dimension_wins"],z["score"]),reverse=True)
    selected=finalists[0] if finalists else None
    out={
        "study":"V99 R67 dynamic hedge amplitude router",
        "status":"RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective":"use R66 training-only regimes to route causally between R55 h0.15 and h0.25, seeking h0.15 one-year upside plus h0.25 historical/severe robustness without fitting on requested horizons",
        "r66_train_end":TRAIN_END.isoformat(),
        "thresholds":{"market_abs_median_24h_q80":VOL24_Q80,"btc24_q20":BTC24_Q20,"h15_gross_q20":H15_GROSS_Q20,"btc72_q20":BTC72_Q20},
        "grid_policy":"5 predeclared routers: four single stable R66 train-only rules plus a 2-of-4 consensus; h0.15/h0.25 amplitudes and all R55 stress/timing parameters fixed",
        "h15":{"summary":parent15_stats,"holdout":parent15_hold,"severe":parent15_severe},
        "h25":{"summary":parent25_stats,"holdout":parent25_hold,"severe":parent25_severe},
        "full_benchmarks":full_bench,"full_envelope":full_env,"severe_benchmarks":severe_bench,"severe_envelope":severe_env,
        "selected":selected,"finalists":finalists,
        "disclosure":"Historical research only. Router thresholds were fixed by R66 training data ending 2024-01-05. Decisions use close-t information and targets enter the same causal next-open replay. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols":quarantined,"v15_metadata":metadata,
    }
    REPORT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"study":out["study"],"selected":selected},indent=2),flush=True)


if __name__=="__main__":
    main()
