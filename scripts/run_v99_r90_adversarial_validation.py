from __future__ import annotations

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
REPORT = PROJECT / "reports" / "v99_r90_adversarial_validation.json"
BASE_THRESHOLD = r88.STRATEGY_R72_THRESHOLD
BASE_SCALE = r88.SCALE
RNG_SEED = 99090


def daily_gate(parent_equity: pd.Series, threshold: float, delay_hours: int = 0) -> tuple[pd.Series, dict]:
    r72 = parent_equity.astype(float).pct_change(72, fill_method=None)
    raw = (r72 >= threshold).fillna(False)
    decision = pd.Series(np.nan, index=raw.index, dtype=float)
    positions = np.arange(0, len(raw), 24, dtype=int)
    if len(positions):
        decision.iloc[positions] = raw.iloc[positions].astype(float).to_numpy()
    active = decision.ffill(limit=23).fillna(0.0).gt(0.0)
    if delay_hours:
        active = active.shift(int(delay_hours), fill_value=False)
    return active, {
        "raw_gate_fraction": float(raw.mean()),
        "daily_active_fraction": float(active.mean()),
        "decision_count": int(len(positions)),
        "threshold": float(threshold),
        "delay_hours": int(delay_hours),
    }


def build_variant(data, raw, ex, guard, gross, cost, threshold=BASE_THRESHOLD, scale=BASE_SCALE, delay_hours=0):
    parent, parent_targets, protect, pdiag, _ = r88.r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = daily_gate(parent.equity, float(threshold), int(delay_hours))
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * float(scale)
    targets = cap(targets, float(r88.r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r88.r86.P15["gross_cap"]), guard)
    diag = {
        **pdiag,
        **gdiag,
        "scale": float(scale),
        "effective_scaled_fraction": float(gate.mean()),
        "protect_overlap_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
        "turnover_delta_vs_parent": float(result.turnover.sum() - parent.turnover.sum()),
    }
    return result, parent, diag


def stats_pair(candidate, parent):
    cs = r36.stats(candidate.equity)
    ps = r36.stats(parent.equity)
    return {
        "candidate": cs,
        "parent_r73": ps,
        "wealth_ratio": float((1 + cs["return"]) / max(1e-12, 1 + ps["return"])),
        "dd_ratio": float(abs(cs["max_drawdown"]) / max(1e-12, abs(ps["max_drawdown"]))),
        "worst_ratio": float(abs(cs["worst_day"]) / max(1e-12, abs(ps["worst_day"]))),
    }


def daily_equity(eq: pd.Series) -> pd.Series:
    return eq.astype(float).resample("1D").last().dropna()


def remove_top_days(candidate_eq: pd.Series, parent_eq: pd.Series, k: int) -> dict:
    c = daily_equity(candidate_eq)
    p = daily_equity(parent_eq).reindex(c.index).dropna()
    c = c.reindex(p.index)
    cr = c.pct_change(fill_method=None).dropna()
    pr = p.pct_change(fill_method=None).reindex(cr.index).dropna()
    cr = cr.reindex(pr.index)
    top = list(cr.nlargest(k).index)
    keep = ~cr.index.isin(top)
    cw = float(np.prod(1.0 + cr.loc[keep].to_numpy()))
    pw = float(np.prod(1.0 + pr.loc[keep].to_numpy()))
    return {
        "removed_days": [x.isoformat() for x in top],
        "candidate_wealth": cw,
        "parent_wealth": pw,
        "wealth_ratio": float(cw / max(1e-12, pw)),
    }


def random_window_audit(candidate_eq: pd.Series, parent_eq: pd.Series, days: int, n: int, rng: np.random.Generator) -> dict:
    c = daily_equity(candidate_eq)
    p = daily_equity(parent_eq).reindex(c.index).dropna()
    c = c.reindex(p.index)
    if len(c) <= days + 2:
        return {"days": int(days), "samples": 0}
    starts = np.arange(0, len(c) - days - 1)
    take = rng.choice(starts, size=min(int(n), len(starts)), replace=False)
    rows = []
    for s in sorted(take):
        ce = c.iloc[s:s + days + 1]
        pe = p.iloc[s:s + days + 1]
        cr = float(ce.iloc[-1] / ce.iloc[0])
        pr = float(pe.iloc[-1] / pe.iloc[0])
        cdd = float((ce / ce.cummax() - 1.0).min())
        pdd = float((pe / pe.cummax() - 1.0).min())
        rows.append({
            "start": ce.index[0].isoformat(),
            "end": ce.index[-1].isoformat(),
            "wealth_ratio": float(cr / max(1e-12, pr)),
            "candidate_dd": cdd,
            "parent_dd": pdd,
            "return_win": bool(cr >= pr),
            "dd_win": bool(abs(cdd) <= abs(pdd)),
        })
    wr = np.array([x["wealth_ratio"] for x in rows], dtype=float)
    return {
        "days": int(days),
        "samples": int(len(rows)),
        "return_win_rate": float(np.mean([x["return_win"] for x in rows])) if rows else 0.0,
        "dd_win_rate": float(np.mean([x["dd_win"] for x in rows])) if rows else 0.0,
        "median_wealth_ratio": float(np.median(wr)) if len(wr) else 0.0,
        "p10_wealth_ratio": float(np.quantile(wr, 0.10)) if len(wr) else 0.0,
        "p90_wealth_ratio": float(np.quantile(wr, 0.90)) if len(wr) else 0.0,
        "windows": rows,
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base = float(ex["base_cost_per_side"])
    severe = float(ex["severe_cost_per_side"])

    nominal, parent, nominal_diag = build_variant(data, raw, ex, guard, gross, base)
    nominal_pair = stats_pair(nominal, parent)

    cost_tests = {}
    for name, cost in {
        "base": base,
        "severe": severe,
        "super_severe_1p5x": severe * 1.5,
    }.items():
        c, p, d = build_variant(data, raw, ex, guard, gross, float(cost))
        cost_tests[name] = {**stats_pair(c, p), "cost_per_side": float(cost), "diagnostics": d}

    threshold_tests = {}
    for mult in (0.90, 1.00, 1.10):
        th = BASE_THRESHOLD * mult
        c, p, d = build_variant(data, raw, ex, guard, gross, base, threshold=th)
        threshold_tests[f"x{mult:.2f}"] = {**stats_pair(c, p), "threshold": float(th), "diagnostics": d}

    scale_tests = {}
    for scale in (1.05, 1.10, 1.15):
        c, p, d = build_variant(data, raw, ex, guard, gross, base, scale=scale)
        scale_tests[f"x{scale:.2f}"] = {**stats_pair(c, p), "scale": float(scale), "diagnostics": d}

    delay_tests = {}
    for delay in (0, 24, 48):
        c, p, d = build_variant(data, raw, ex, guard, gross, base, delay_hours=delay)
        delay_tests[f"{delay}h"] = {**stats_pair(c, p), "diagnostics": d}

    top_day_tests = {str(k): remove_top_days(nominal.equity, parent.equity, k) for k in (1, 5, 10)}

    rng = np.random.default_rng(RNG_SEED)
    random_windows = {
        str(days): random_window_audit(nominal.equity, parent.equity, days, 60, rng)
        for days in (30, 90, 180, 365)
    }

    cost_pass = all(v["wealth_ratio"] > 1.0 for v in cost_tests.values())
    threshold_pass = all(v["wealth_ratio"] > 1.0 for v in threshold_tests.values())
    scale_pass = all(v["wealth_ratio"] > 1.0 for v in scale_tests.values())
    delay_pass = all(v["wealth_ratio"] > 1.0 for v in delay_tests.values())
    top_day_pass = all(v["wealth_ratio"] > 1.0 for v in top_day_tests.values())
    window_pass = all(v.get("return_win_rate", 0.0) >= 0.60 and v.get("median_wealth_ratio", 0.0) > 1.0 for v in random_windows.values())

    out = {
        "study": "V99 R90 adversarial validation of frozen R88 selective expansion",
        "status": "DIAGNOSTIC_ONLY_NO_PROMOTION_AND_NO_FROZEN_REWRITE",
        "objective": "stress-test R88 without tuning it: stronger costs, threshold and scale perturbations, execution delay, removal of best candidate days, and deterministic random calendar windows on the same full replay path",
        "frozen_r88": {
            "threshold": BASE_THRESHOLD,
            "scale": BASE_SCALE,
            "decision_cadence_hours": 24,
            "hold_hours": 24,
            "source": "R87 train-only signal + R88 implementation",
        },
        "nominal": {**nominal_pair, "diagnostics": nominal_diag},
        "cost_tests": cost_tests,
        "threshold_sensitivity": threshold_tests,
        "scale_sensitivity": scale_tests,
        "delay_sensitivity": delay_tests,
        "remove_best_candidate_days": top_day_tests,
        "random_calendar_windows": random_windows,
        "gates": {
            "cost_pass": bool(cost_pass),
            "threshold_pass": bool(threshold_pass),
            "scale_pass": bool(scale_pass),
            "delay_pass": bool(delay_pass),
            "top_day_pass": bool(top_day_pass),
            "random_window_pass": bool(window_pass),
            "growth_robustness_pass": bool(cost_pass and threshold_pass and scale_pass and delay_pass and top_day_pass and window_pass),
        },
        "interpretation_policy": "R90 cannot select a new threshold, scale or delay. Sensitivity variants are robustness probes only. A failure does not authorize choosing the best probe. Random windows are path-segment diagnostics, not isolated-horizon replays.",
        "disclosure": "Historical research only. R88 remains unchanged regardless of probe results. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "nominal": out["nominal"], "gates": out["gates"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
