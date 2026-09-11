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

import run_v99_r86_tristate_hedge_router as r86

r36 = r86.r36
cap = r86.cap
REPORT = PROJECT / "reports" / "candidate_v99_r88_selective_exposure_expansion.json"

SCALE = 1.10
STRATEGY_R72_THRESHOLD = 0.03360248266113066  # frozen R87 first-60% train q80
TRAIN_END = pd.Timestamp("2024-01-18T00:00:00+00:00")
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def daily_gate(parent_equity: pd.Series) -> tuple[pd.Series, dict]:
    r72 = parent_equity.astype(float).pct_change(72, fill_method=None)
    raw = (r72 >= STRATEGY_R72_THRESHOLD).fillna(False)
    decision = pd.Series(np.nan, index=raw.index, dtype=float)
    positions = np.arange(0, len(raw), 24, dtype=int)
    if len(positions):
        decision.iloc[positions] = raw.iloc[positions].astype(float).to_numpy()
    active = decision.ffill(limit=23).fillna(0.0).gt(0.0)
    return active, {
        "raw_gate_fraction": float(raw.mean()),
        "daily_active_fraction": float(active.mean()),
        "decision_count": int(len(positions)),
        "decision_cadence_hours": 24,
        "threshold": STRATEGY_R72_THRESHOLD,
    }


def build_candidate(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = daily_gate(parent.equity)
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * SCALE
    targets = cap(targets, float(r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r86.P15["gross_cap"]), guard)
    diag = {
        **pdiag,
        **gdiag,
        "scale": SCALE,
        "protect_overlap_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
        "effective_scaled_fraction": float(gate.mean()),
        "turnover_delta_vs_parent": float(result.turnover.sum() - parent.turnover.sum()),
        "parent_mean_gross_when_scaled": float(parent_targets.abs().sum(axis=1).loc[gate].mean()) if gate.any() else 0.0,
        "candidate_mean_gross_when_scaled": float(targets.abs().sum(axis=1).loc[gate].mean()) if gate.any() else 0.0,
    }
    return result, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    c, p, _ = build_candidate(d, rr, ex, guard, gross, cost)
    return r36.stats(c.equity), r36.stats(p.equity)


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    cand, parent, diag = build_candidate(data, raw, ex, guard, gross, base_cost)
    cand_sev, parent_sev, sev_diag = build_candidate(data, raw, ex, guard, gross, severe_cost)
    cs, ps = r36.stats(cand.equity), r36.stats(parent.equity)
    csev, psev = r36.stats(cand_sev.equity), r36.stats(parent_sev.equity)

    hold_idx = cand.equity.index[cand.equity.index > TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else cand.equity.index[-1]
    ch = r36.stats(cand.equity.loc[hold_start:])
    ph = r36.stats(parent.equity.loc[hold_start:])

    benchmarks = r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    full_bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"])) for n, x in benchmarks.items()}
    severe_bench = {n: r36.exact_benchmark(x, float(x["execution"]["severe_cost_per_side"])) for n, x in benchmarks.items()}
    common_end = min(x["data"].close.index[-1] for x in benchmarks.values())
    earliest = max(x["data"].close.index[0] for x in benchmarks.values())

    iso, iso_parent, parent_wins, env_wins = {}, {}, {}, {}
    for days in HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        c, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, common_end)
        bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"]), start, common_end) for n, x in benchmarks.items()}
        env = r36.envelope(bench)
        k = str(days)
        iso[k], iso_parent[k] = c, p
        parent_wins[k] = {
            "return": c["return"] >= p["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }
        env_wins[k] = {
            "return": c["return"] >= env["return"],
            "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
            "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
        }
        gc.collect()

    alt = {}
    for days in ALT_HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        if start < earliest:
            continue
        c, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, common_end)
        alt[str(days)] = {
            "candidate": c,
            "parent_r73": p,
            "return_vs_parent": c["return"] >= p["return"],
            "drawdown_vs_parent": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day_vs_parent": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }
        gc.collect()

    full_dom = cs["return"] >= ps["return"] and abs(cs["max_drawdown"]) <= abs(ps["max_drawdown"]) and abs(cs["worst_day"]) <= abs(ps["worst_day"])
    hold_dom = ch["return"] >= ph["return"] and abs(ch["max_drawdown"]) <= abs(ph["max_drawdown"])
    severe_dom = csev["return"] >= psev["return"] and abs(csev["max_drawdown"]) <= abs(psev["max_drawdown"]) and abs(csev["worst_day"]) <= abs(psev["worst_day"])
    dim_wins = int(sum(sum(v.values()) for v in parent_wins.values()))

    out = {
        "study": "V99 R88 selective R73 exposure expansion",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "apply the predeclared 1.10x capped expansion for 24h only when the shadow R73 trailing 72h return exceeds the frozen R87 train-only threshold; retain R73 protection logic unchanged and evaluate exact full/holdout/severe/multihorizon behavior",
        "frozen_rule": {
            "feature": "shadow_r73_strategy_r72",
            "direction": "high",
            "threshold": STRATEGY_R72_THRESHOLD,
            "scale": SCALE,
            "decision_cadence_hours": 24,
            "hold_hours": 24,
            "threshold_source": "R87 first-60% training only",
            "R87_train_lift": 1.545814739688979,
            "R87_holdout_lift": 1.7519289373014326,
            "R87_positive_mean_folds": "5/5",
            "R87_positive_lift_folds": "5/5",
            "thresholds_refit": False,
            "scale_refit": False,
        },
        "parent_r73": {"summary": ps, "holdout": ph, "severe": psev},
        "candidate": {"summary": cs, "holdout": ch, "severe": csev, "diagnostics": diag, "severe_diagnostics": sev_diag},
        "ratios_vs_parent": {
            "full_wealth": float((1+cs["return"])/max(1e-12,1+ps["return"])),
            "holdout_wealth": float((1+ch["return"])/max(1e-12,1+ph["return"])),
            "severe_wealth": float((1+csev["return"])/max(1e-12,1+psev["return"])),
            "full_dd": float(abs(cs["max_drawdown"])/max(1e-12,abs(ps["max_drawdown"]))),
            "full_worst": float(abs(cs["worst_day"])/max(1e-12,abs(ps["worst_day"]))),
        },
        "isolated": iso,
        "isolated_parent_r73": iso_parent,
        "parent_horizon_wins": parent_wins,
        "envelope_wins": env_wins,
        "alternative_horizons": alt,
        "full_parent_dominance": bool(full_dom),
        "holdout_parent_dominance": bool(hold_dom),
        "severe_parent_dominance": bool(severe_dom),
        "requested_parent_dimension_wins": dim_wins,
        "strict_parent_gate_passed": bool(full_dom and hold_dom and severe_dom and dim_wins == 15),
        "full_benchmarks": full_bench,
        "severe_benchmarks": severe_bench,
        "disclosure": "Historical research only. The signal threshold and 1.10 scale were frozen before this candidate; requested horizons are validation only. The signal uses an independent shadow R73 path so the expansion cannot alter its own trigger. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "parent": out["parent_r73"], "candidate": out["candidate"], "ratios": out["ratios_vs_parent"], "strict": out["strict_parent_gate_passed"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
