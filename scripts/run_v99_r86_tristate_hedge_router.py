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
import run_v99_r67_dynamic_hedge_router as r67

r36 = r55.r36
r37 = r55.r37
cap = r55.cap
REPORT = PROJECT / "reports" / "candidate_v99_r86_tristate_hedge_router.json"

P10 = r55.params(0.10)
P15 = r55.params(0.15)
P25 = r55.params(0.25)
PROTECT_GROSS_THRESHOLD = 0.4478403629219058  # frozen R66/R71/R73 train-derived
OPP_CROSS_VOL_THRESHOLD = 0.04973417292341461  # frozen R77 train-derived, R78 4/5 positive-mean folds
TRAIN_END = pd.Timestamp("2024-01-05T00:00:00+00:00")
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def daily_decision(raw_gate: pd.Series) -> pd.Series:
    decision = pd.Series(np.nan, index=raw_gate.index, dtype=float)
    positions = np.arange(0, len(raw_gate), 24, dtype=int)
    if len(positions):
        decision.iloc[positions] = raw_gate.iloc[positions].astype(float).to_numpy()
    return decision


def protection_gate(t15: pd.DataFrame) -> tuple[pd.Series, dict]:
    raw = (t15.abs().sum(axis=1) <= PROTECT_GROSS_THRESHOLD).fillna(False)
    decision = daily_decision(raw)
    trigger = decision.fillna(0.0).gt(0.0)
    active = trigger.astype(float).rolling(72, min_periods=1).max().gt(0.0)
    return active, {
        "raw_protect_fraction": float(raw.mean()),
        "daily_protect_trigger_fraction": float(trigger.mean()),
        "protect_active_fraction": float(active.mean()),
        "protect_persistence_hours": 72,
    }


def opportunity_gate(data, index: pd.Index) -> tuple[pd.Series, dict]:
    close = data.close.reindex(index)
    cross_vol = close.pct_change(24, fill_method=None).std(axis=1)
    raw = (cross_vol >= OPP_CROSS_VOL_THRESHOLD).fillna(False)
    decision = daily_decision(raw)
    active = decision.ffill(limit=23).fillna(0.0).gt(0.0)
    return active, {
        "raw_opportunity_fraction": float(raw.mean()),
        "opportunity_active_fraction": float(active.mean()),
        "opportunity_threshold": OPP_CROSS_VOL_THRESHOLD,
        "opportunity_decision_cadence_hours": 24,
    }


def build_states(data, raw, ex, guard, gross, cost):
    core = r36.run(data, raw, ex, cost, gross, guard)
    t10, active10 = r37.r30_targets(raw, core.equity, data.close, P10)
    t15, active15 = r37.r30_targets(raw, core.equity, data.close, P15)
    t25, active25 = r37.r30_targets(raw, core.equity, data.close, P25)
    t10 = cap(t10, float(P15["gross_cap"]))
    t15 = cap(t15, float(P15["gross_cap"]))
    t25 = cap(t25, float(P15["gross_cap"]))
    return core, t10, t15, t25, active10, active15, active25


def build_parent_r73(data, raw, ex, guard, gross, cost):
    core, t10, t15, t25, active10, active15, active25 = build_states(data, raw, ex, guard, gross, cost)
    protect, pdiag = protection_gate(t15)
    targets = t15.copy()
    targets.loc[protect, :] = t25.loc[protect, :]
    targets = cap(targets, float(P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(P15["gross_cap"]), guard)
    diag = {
        **pdiag,
        "h15_active_fraction": float(active15.mean()),
        "h25_active_fraction": float(active25.mean()),
        "effective_protect_fraction": float((protect & active15.reindex(protect.index).fillna(False)).mean()),
    }
    return result, targets, protect, diag, (t10, t15, t25)


def build_candidate(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, states = build_parent_r73(data, raw, ex, guard, gross, cost)
    t10, t15, t25 = states
    opportunity, odiag = opportunity_gate(data, t15.index)
    opp_effective = opportunity & ~protect

    targets = t15.copy()
    targets.loc[opp_effective, :] = t10.loc[opp_effective, :]
    targets.loc[protect, :] = t25.loc[protect, :]  # protection always wins
    targets = cap(targets, float(P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(P15["gross_cap"]), guard)

    diag = {
        **pdiag,
        **odiag,
        "effective_opportunity_fraction": float(opp_effective.mean()),
        "protect_priority_overlap_fraction": float((opportunity & protect).mean()),
        "turnover_delta_vs_r73": float(result.turnover.sum() - parent.turnover.sum()),
    }
    return result, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    c, p, _ = build_candidate(d, rr, ex, guard, gross, cost)
    return r36.stats(c.equity), r36.stats(p.equity)


def main():
    cand_cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
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

    benchmarks = r55.benchmark_items(cand_cfg, data, raw, ex, guard, gross)
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
        "study": "V99 R86 tri-state hedge router: h0.25 protection > h0.10 opportunity > h0.15 neutral",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "preserve the R73 fixed h0.25 protection state exactly, and use frozen R78 cross-sectional-volatility opportunity evidence to route to h0.10 only when protection is inactive; otherwise remain h0.15",
        "frozen_rules": {
            "protection": {
                "feature": "h15_gross",
                "direction": "low",
                "threshold": PROTECT_GROSS_THRESHOLD,
                "decision_cadence_hours": 24,
                "persistence_hours": 72,
                "source": "R66 train threshold + R71 temporal validation + R73 implementation",
            },
            "opportunity": {
                "feature": "cross_vol_24h",
                "direction": "high",
                "threshold": OPP_CROSS_VOL_THRESHOLD,
                "decision_cadence_hours": 24,
                "hold_hours": 24,
                "source": "R77 train-only threshold + R78 4/5 positive mean-advantage folds",
            },
            "priority": "protection_over_opportunity",
            "thresholds_refit": False,
            "amplitudes_refit": False,
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
        "disclosure": "Historical research only. Both regime thresholds and all three hedge amplitudes were fixed before this candidate. Protection has absolute priority. No requested-horizon result is used to fit the router. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "parent": out["parent_r73"], "candidate": out["candidate"], "ratios": out["ratios_vs_parent"], "strict": out["strict_parent_gate_passed"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
