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

import run_v99_r88_selective_exposure_expansion as r88

r36 = r88.r36
cap = r88.cap
REPORT = PROJECT / "reports" / "candidate_v99_r92_expansion_sleeve_breakeven_kill.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def governed_gate(parent_equity: pd.Series) -> tuple[pd.Series, dict]:
    base_gate, base_diag = r88.daily_gate(parent_equity)
    eq = parent_equity.astype(float)
    active = pd.Series(False, index=eq.index)
    decision_positions = np.arange(0, len(eq), 24, dtype=int)
    triggered = 0
    killed = 0
    active_hours = []

    for pos in decision_positions:
        if not bool(base_gate.iloc[pos]):
            continue
        triggered += 1
        baseline = float(eq.iloc[pos])
        on = True
        hours = 0
        for j in range(int(pos), min(int(pos) + 24, len(eq))):
            if j > pos and on and float(eq.iloc[j]) < baseline:
                on = False
                killed += 1
            if on:
                active.iloc[j] = True
                hours += 1
        active_hours.append(hours)

    diag = {
        **base_diag,
        "governor": "breakeven latch on shadow R73 equity within each 24h expansion episode",
        "triggered_episodes": int(triggered),
        "killed_episodes": int(killed),
        "kill_rate": float(killed / triggered) if triggered else 0.0,
        "mean_active_hours_per_trigger": float(np.mean(active_hours)) if active_hours else 0.0,
        "governed_active_fraction": float(active.mean()),
        "breakeven_offset": 0.0,
    }
    return active, diag


def build_variant(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, _ = r88.r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    base_gate, _ = r88.daily_gate(parent.equity)

    r88_targets = parent_targets.copy()
    if base_gate.any():
        r88_targets.loc[base_gate, :] = r88_targets.loc[base_gate, :] * r88.SCALE
    r88_targets = cap(r88_targets, float(r88.r86.P15["gross_cap"]))
    r88_result = r36.run(data, r88_targets, ex, cost, float(r88.r86.P15["gross_cap"]), guard)

    gate, gdiag = governed_gate(parent.equity)
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * r88.SCALE
    targets = cap(targets, float(r88.r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r88.r86.P15["gross_cap"]), guard)

    diag = {
        **pdiag,
        **gdiag,
        "scale": r88.SCALE,
        "effective_scaled_fraction": float(gate.mean()),
        "protect_overlap_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
        "turnover_delta_vs_r73": float(result.turnover.sum() - parent.turnover.sum()),
        "turnover_delta_vs_r88": float(result.turnover.sum() - r88_result.turnover.sum()),
    }
    return result, r88_result, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    c, g, p, _ = build_variant(d, rr, ex, guard, gross, cost)
    return r36.stats(c.equity), r36.stats(g.equity), r36.stats(p.equity)


def ratio(a: dict, b: dict) -> float:
    return float((1.0 + a["return"]) / max(1e-12, 1.0 + b["return"]))


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base = float(ex["base_cost_per_side"])
    severe = float(ex["severe_cost_per_side"])

    cand, growth, parent, diag = build_variant(data, raw, ex, guard, gross, base)
    cand_sev, growth_sev, parent_sev, sev_diag = build_variant(data, raw, ex, guard, gross, severe)

    cs, gs, ps = r36.stats(cand.equity), r36.stats(growth.equity), r36.stats(parent.equity)
    csev, gsev, psev = r36.stats(cand_sev.equity), r36.stats(growth_sev.equity), r36.stats(parent_sev.equity)

    hold_idx = cand.equity.index[cand.equity.index > r88.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else cand.equity.index[-1]
    ch = r36.stats(cand.equity.loc[hold_start:])
    gh = r36.stats(growth.equity.loc[hold_start:])
    ph = r36.stats(parent.equity.loc[hold_start:])

    common_end = data.close.index[-1]
    earliest = data.close.index[0]
    isolated = {}
    parent_wins = {}
    growth_wins = {}

    for days in HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        c, g, p = eval_slice(data, raw, ex, guard, gross, base, start, common_end)
        k = str(days)
        isolated[k] = {"candidate": c, "r88_growth": g, "r73_parent": p}
        parent_wins[k] = {
            "return": c["return"] >= p["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }
        growth_wins[k] = {
            "return": c["return"] >= g["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(g["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(g["worst_day"]),
        }
        gc.collect()

    alternative = {}
    for days in ALT_HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        if start < earliest:
            continue
        c, g, p = eval_slice(data, raw, ex, guard, gross, base, start, common_end)
        alternative[str(days)] = {
            "candidate": c,
            "r88_growth": g,
            "r73_parent": p,
            "wealth_vs_r88": ratio(c, g),
            "wealth_vs_r73": ratio(c, p),
            "dd_vs_r88": abs(c["max_drawdown"]) <= abs(g["max_drawdown"]),
            "worst_vs_r88": abs(c["worst_day"]) <= abs(g["worst_day"]),
        }
        gc.collect()

    dim_wins_parent = int(sum(sum(v.values()) for v in parent_wins.values()))
    dim_wins_growth = int(sum(sum(v.values()) for v in growth_wins.values()))

    full_parent_dom = cs["return"] >= ps["return"] and abs(cs["max_drawdown"]) <= abs(ps["max_drawdown"]) and abs(cs["worst_day"]) <= abs(ps["worst_day"])
    hold_parent_dom = ch["return"] >= ph["return"] and abs(ch["max_drawdown"]) <= abs(ph["max_drawdown"]) and abs(ch["worst_day"]) <= abs(ph["worst_day"])
    severe_parent_dom = csev["return"] >= psev["return"] and abs(csev["max_drawdown"]) <= abs(psev["max_drawdown"]) and abs(csev["worst_day"]) <= abs(psev["worst_day"])

    out = {
        "study": "V99 R92 R88 expansion-sleeve breakeven kill",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "keep the frozen R87/R88 expansion signal and 1.10 scale, but let only the incremental sleeve latch off for the rest of its 24h episode if shadow R73 equity falls below the episode-start equity; core R73 targets remain untouched",
        "design": {
            "expansion_threshold": r88.STRATEGY_R72_THRESHOLD,
            "scale": r88.SCALE,
            "episode_hours": 24,
            "kill_level": "shadow R73 equity < episode-start equity",
            "kill_offset": 0.0,
            "reenable_policy": "only at next daily decision if the frozen R88 gate is true again",
            "fitted_parameters": 0,
        },
        "r73_parent": {"summary": ps, "holdout": ph, "severe": psev},
        "r88_growth_parent": {"summary": gs, "holdout": gh, "severe": gsev},
        "candidate": {"summary": cs, "holdout": ch, "severe": csev, "diagnostics": diag, "severe_diagnostics": sev_diag},
        "ratios": {
            "full_wealth_vs_r88": ratio(cs, gs),
            "holdout_wealth_vs_r88": ratio(ch, gh),
            "severe_wealth_vs_r88": ratio(csev, gsev),
            "full_wealth_vs_r73": ratio(cs, ps),
            "holdout_wealth_vs_r73": ratio(ch, ph),
            "severe_wealth_vs_r73": ratio(csev, psev),
            "full_dd_ratio_vs_r88": float(abs(cs["max_drawdown"]) / max(1e-12, abs(gs["max_drawdown"]))),
            "holdout_dd_ratio_vs_r88": float(abs(ch["max_drawdown"]) / max(1e-12, abs(gh["max_drawdown"]))),
            "severe_dd_ratio_vs_r88": float(abs(csev["max_drawdown"]) / max(1e-12, abs(gsev["max_drawdown"]))),
        },
        "isolated": isolated,
        "parent_horizon_wins": parent_wins,
        "r88_horizon_wins": growth_wins,
        "alternative_horizons": alternative,
        "requested_parent_dimension_wins": dim_wins_parent,
        "requested_r88_dimension_wins": dim_wins_growth,
        "full_parent_dominance": bool(full_parent_dom),
        "holdout_parent_dominance": bool(hold_parent_dom),
        "severe_parent_dominance": bool(severe_parent_dom),
        "strict_r73_gate_passed": bool(full_parent_dom and hold_parent_dom and severe_parent_dom and dim_wins_parent == 15),
        "disclosure": "Historical research only. R92 adds no fitted numeric threshold: the sleeve kill is exactly breakeven on an independent shadow R73 path. R88 remains the research growth parent; Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "r73": out["r73_parent"], "r88": out["r88_growth_parent"], "candidate": out["candidate"], "ratios": out["ratios"], "strict_r73": out["strict_r73_gate_passed"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
