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

import run_v99_r98_friction_aware_hybrid as r98

r88 = r98.r88
r86 = r98.r86
r36 = r98.r36
cap = r98.cap
REPORT = PROJECT / "reports" / "candidate_v99_r103_sticky_expansion_execution.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
WINDOW_DAYS = (30, 90, 180, 365)
SAMPLES_PER_DURATION = 10
RNG_SEED = 99103
FOLDS = 5


def wealth_ratio(a: dict, b: dict) -> float:
    return float((1.0 + a["return"]) / max(1e-12, 1.0 + b["return"]))


def compare(a: dict, b: dict) -> dict:
    return {
        "wealth_ratio": wealth_ratio(a, b),
        "return_win": bool(a["return"] >= b["return"]),
        "dd_ratio": float(abs(a["max_drawdown"]) / max(1e-12, abs(b["max_drawdown"]))),
        "dd_win": bool(abs(a["max_drawdown"]) <= abs(b["max_drawdown"])),
        "worst_ratio": float(abs(a["worst_day"]) / max(1e-12, abs(b["worst_day"]))),
        "worst_day_win": bool(abs(a["worst_day"]) <= abs(b["worst_day"])),
    }


def build_targets(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(
        data, raw, ex, guard, gross, cost
    )
    gate, gdiag = r88.daily_gate(parent.equity)
    parent_gross = parent_targets.abs().sum(axis=1)
    high = gate & parent_gross.ge(r98.R97_GROSS_THRESHOLD)
    gross_cap = float(r86.P15["gross_cap"])

    # Canonical R98 reference.
    ref_targets = parent_targets.copy()
    if gate.any():
        ref_targets.loc[gate, :] = parent_targets.loc[gate, :] * r98.R88_SCALE
    if high.any():
        ref_targets.loc[high, :] = parent_targets.loc[high, :] * r98.R96_SCALE
    ref_targets = cap(ref_targets, gross_cap)

    # R103: same frozen decision/gross rules, but the incremental exposure is
    # snapshotted once per daily episode. The core remains the current hourly
    # R73 target. Overlay is removed for a symbol if the current core has exited
    # or flipped sign, and only remaining gross headroom is used. No fitted knob.
    overlay = pd.DataFrame(0.0, index=parent_targets.index, columns=parent_targets.columns)
    decision_positions = np.arange(0, len(parent_targets), 24, dtype=int)
    episode_count = 0
    qualified_episode_count = 0
    alignment_drops = 0
    headroom_clips = 0

    for pos in decision_positions:
        if not bool(gate.iloc[pos]):
            continue
        episode_count += 1
        scale = r98.R96_SCALE if bool(high.iloc[pos]) else r98.R88_SCALE
        if bool(high.iloc[pos]):
            qualified_episode_count += 1
        snap = parent_targets.iloc[pos].copy() * (float(scale) - 1.0)
        for j in range(int(pos), min(int(pos) + 24, len(parent_targets))):
            core = parent_targets.iloc[j]
            aligned = (np.sign(core) == np.sign(snap)) & core.abs().gt(1e-12) & snap.abs().gt(1e-12)
            alignment_drops += int((snap.abs().gt(1e-12) & ~aligned).sum())
            ov = snap.where(aligned, 0.0)
            available = max(0.0, gross_cap - float(core.abs().sum()))
            og = float(ov.abs().sum())
            if og > available + 1e-12 and og > 0.0:
                ov = ov * (available / og)
                headroom_clips += 1
            overlay.iloc[j] = ov

    sticky_targets = parent_targets + overlay
    # Numerical guard only; the construction above is core-preserving and should
    # already satisfy the cap without scaling the core.
    max_requested = float(sticky_targets.abs().sum(axis=1).max())
    if max_requested > gross_cap + 1e-8:
        raise RuntimeError(f"R103 core-preserving headroom construction exceeded cap: {max_requested}")

    ref = r36.run(data, ref_targets, ex, cost, gross_cap, guard)
    sticky = r36.run(data, sticky_targets, ex, cost, gross_cap, guard)
    diag = {
        **pdiag,
        **gdiag,
        "gross_cap": gross_cap,
        "r88_scale": r98.R88_SCALE,
        "r96_scale": r98.R96_SCALE,
        "r97_gross_threshold": r98.R97_GROSS_THRESHOLD,
        "daily_expansion_episodes": int(episode_count),
        "qualified_115_episodes": int(qualified_episode_count),
        "overlay_alignment_drops": int(alignment_drops),
        "overlay_headroom_clip_hours": int(headroom_clips),
        "sticky_overlay_mean_gross": float(overlay.abs().sum(axis=1).mean()),
        "sticky_overlay_active_fraction": float(overlay.abs().sum(axis=1).gt(1e-12).mean()),
        "sticky_max_requested_gross": max_requested,
        "turnover_ref": float(ref.turnover.sum()),
        "turnover_sticky": float(sticky.turnover.sum()),
        "turnover_ratio_sticky_to_r98": float(sticky.turnover.sum() / max(1e-12, ref.turnover.sum())),
        "fee_ref": float(ref.fees.sum()),
        "fee_sticky": float(sticky.fees.sum()),
        "fee_ratio_sticky_to_r98": float(sticky.fees.sum() / max(1e-12, ref.fees.sum())),
        "protect_overlap_gate_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
    }
    return sticky, ref, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    a, b, p, _ = build_targets(d, rr, ex, guard, gross, cost)
    return r36.stats(a.equity), r36.stats(b.equity), r36.stats(p.equity)


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_cost = severe_cost * 1.5

    cost_tests = {}
    base_objects = None
    for label, cost in (("base", base_cost), ("severe", severe_cost), ("super_severe_1p5x", super_cost)):
        sticky, ref, parent, diag = build_targets(data, raw, ex, guard, gross, cost)
        ss, rs, ps = r36.stats(sticky.equity), r36.stats(ref.equity), r36.stats(parent.equity)
        cost_tests[label] = {
            "r103": ss,
            "r98": rs,
            "r73": ps,
            "vs_r98": compare(ss, rs),
            "vs_r73": compare(ss, ps),
            "cost_per_side": cost,
            "diagnostics": diag,
        }
        if label == "base":
            base_objects = (sticky, ref, parent, diag)
        gc.collect()

    sticky_base, ref_base, parent_base, base_diag = base_objects
    hold_idx = sticky_base.equity.index[sticky_base.equity.index > r98.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else sticky_base.equity.index[-1]
    sh = r36.stats(sticky_base.equity.loc[hold_start:])
    rh = r36.stats(ref_base.equity.loc[hold_start:])
    ph = r36.stats(parent_base.equity.loc[hold_start:])
    holdout = {
        "start": hold_start.isoformat(),
        "r103": sh,
        "r98": rh,
        "r73": ph,
        "vs_r98": compare(sh, rh),
        "vs_r73": compare(sh, ph),
    }

    end = data.close.index[-1]
    isolated, alternative = {}, {}
    for days in HORIZONS:
        a, b, p = eval_slice(data, raw, ex, guard, gross, base_cost, end - pd.Timedelta(days=days), end)
        isolated[str(days)] = {"r103": a, "r98": b, "r73": p, "vs_r98": compare(a, b)}
        gc.collect()
    for days in ALT_HORIZONS:
        start = end - pd.Timedelta(days=days)
        if start < data.close.index[0]:
            continue
        a, b, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, end)
        alternative[str(days)] = {"r103": a, "r98": b, "r73": p, "vs_r98": compare(a, b)}
        gc.collect()

    idx = data.close.index
    bounds = np.linspace(0, len(idx), FOLDS + 1, dtype=int)
    folds = []
    for i in range(FOLDS):
        lo, hi = int(bounds[i]), int(bounds[i + 1] - 1)
        if hi <= lo:
            continue
        a, b, p = eval_slice(data, raw, ex, guard, gross, base_cost, idx[lo], idx[hi])
        folds.append({"fold": i + 1, "start": idx[lo].isoformat(), "end": idx[hi].isoformat(), "r103": a, "r98": b, "vs_r98": compare(a, b)})
        gc.collect()

    base_cmp = cost_tests["base"]["vs_r98"]
    sev_cmp = cost_tests["severe"]["vs_r98"]
    super_cmp = cost_tests["super_severe_1p5x"]["vs_r98"]
    hold_cmp = holdout["vs_r98"]
    main_wins = sum(int(v["vs_r98"]["return_win"]) for v in isolated.values())
    alt_wins = sum(int(v["vs_r98"]["return_win"]) for v in alternative.values())
    fold_wins = sum(int(v["vs_r98"]["return_win"]) for v in folds)
    turnover_ratio = float(base_diag["turnover_ratio_sticky_to_r98"])

    preliminary = bool(
        base_cmp["wealth_ratio"] >= 1.0
        and sev_cmp["wealth_ratio"] >= 1.0
        and super_cmp["wealth_ratio"] >= 1.0
        and hold_cmp["wealth_ratio"] >= 0.995
        and turnover_ratio <= 0.98
        and fold_wins >= 3
    )

    random_windows = {}
    if preliminary:
        rng = np.random.default_rng(RNG_SEED)
        for days in WINDOW_DAYS:
            span = int(days) * 24
            valid = np.arange(72, max(73, len(idx) - span - 1), 24, dtype=int)
            chosen = np.sort(rng.choice(valid, size=min(SAMPLES_PER_DURATION, len(valid)), replace=False)) if len(valid) else []
            rows = []
            for pos in chosen:
                start, stop = idx[int(pos)], idx[int(pos + span)]
                a, b, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, stop)
                rows.append({"start": start.isoformat(), "end": stop.isoformat(), "r103": a, "r98": b, "vs_r98": compare(a, b)})
                gc.collect()
            wr = np.array([x["vs_r98"]["wealth_ratio"] for x in rows], dtype=float)
            random_windows[str(days)] = {
                "samples": len(rows),
                "return_win_rate_vs_r98": float(np.mean([x["vs_r98"]["return_win"] for x in rows])) if rows else 0.0,
                "dd_win_rate_vs_r98": float(np.mean([x["vs_r98"]["dd_win"] for x in rows])) if rows else 0.0,
                "median_wealth_ratio_vs_r98": float(np.median(wr)) if len(wr) else 0.0,
                "p10_wealth_ratio_vs_r98": float(np.quantile(wr, 0.10)) if len(wr) else 0.0,
                "windows": rows,
            }

    random_pass = bool(
        preliminary
        and random_windows
        and all(v["median_wealth_ratio_vs_r98"] >= 1.0 for v in random_windows.values())
        and all(v["return_win_rate_vs_r98"] >= 0.50 for v in random_windows.values())
        and all(random_windows[str(d)]["return_win_rate_vs_r98"] >= 0.60 for d in (180, 365))
    )

    gates = {
        "turnover_reduction_pass": bool(turnover_ratio <= 0.95),
        "full_growth_pass": bool(base_cmp["wealth_ratio"] >= 1.01),
        "full_risk_pass": bool(base_cmp["dd_ratio"] <= 1.02 and base_cmp["worst_ratio"] <= 1.03),
        "holdout_pass": bool(hold_cmp["wealth_ratio"] >= 1.005 and hold_cmp["dd_ratio"] <= 1.03),
        "severe_pass": bool(sev_cmp["wealth_ratio"] >= 1.01 and sev_cmp["dd_ratio"] <= 1.03),
        "super_severe_pass": bool(super_cmp["wealth_ratio"] >= 1.01 and super_cmp["dd_ratio"] <= 1.04),
        "main_horizon_pass": bool(main_wins >= 3),
        "alternative_horizon_pass": bool(alt_wins >= max(1, int(np.ceil(0.60 * len(alternative))))),
        "chronological_fold_pass": bool(fold_wins >= 4),
        "random_window_pass": random_pass,
    }
    gates["r103_growth_candidate_pass"] = bool(all(gates.values()))

    out = {
        "study": "V99 R103 sticky daily execution of the frozen R98 expansion layer",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "preserve the R73 core and the exact frozen R98 expansion trigger/scale, but snapshot only the incremental expansion layer once per 24h episode so hourly core churn is not automatically amplified; test whether lower execution friction improves net growth without material downside regression",
        "precommitment": {
            "signal_threshold": r88.STRATEGY_R72_THRESHOLD,
            "base_expansion_scale": r98.R88_SCALE,
            "qualified_expansion_scale": r98.R96_SCALE,
            "qualified_parent_gross_threshold": r98.R97_GROSS_THRESHOLD,
            "overlay_refresh_hours": 24,
            "overlay_rule": "daily snapshot of (scale-1)*parent target; retain only same-signed still-active core symbols; proportional overlay-only headroom clip; never scale core to make room",
            "new_fitted_parameters": 0,
        },
        "cost_tests": cost_tests,
        "holdout": holdout,
        "isolated_horizons": isolated,
        "alternative_horizons": alternative,
        "chronological_folds": folds,
        "random_windows": {"seed": RNG_SEED, "samples_per_duration": SAMPLES_PER_DURATION, "executed": bool(preliminary), "results": random_windows},
        "summary_counts": {"main_return_wins_vs_r98": main_wins, "main_total": len(isolated), "alternative_return_wins_vs_r98": alt_wins, "alternative_total": len(alternative), "fold_return_wins_vs_r98": fold_wins, "fold_total": len(folds)},
        "preliminary_random_gate": preliminary,
        "promotion_gates": gates,
        "disclosure": "Historical research only. R103 changes execution architecture of the incremental expansion, not the frozen predictive thresholds/scales. Frozen V99, Paper and R98 remain untouched unless a later promotion decision is explicitly made.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "cost_tests": cost_tests, "holdout": holdout, "counts": out["summary_counts"], "preliminary": preliminary, "gates": gates}, indent=2), flush=True)


if __name__ == "__main__":
    main()
