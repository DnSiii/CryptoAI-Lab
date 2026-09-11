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
REPORT = PROJECT / "reports" / "candidate_v99_r104_nested_120_conviction_tier.json"
ULTRA_SCALE = 1.20
ULTRA_QUANTILE = 0.75
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
WINDOW_DAYS = (30, 90, 180, 365)
RNG_SEED = 99104
SAMPLES_PER_DURATION = 10
FOLDS = 5


def stats(x):
    return r36.stats(x.equity)


def ratio(a: dict, b: dict) -> float:
    return float((1.0 + a["return"]) / max(1e-12, 1.0 + b["return"]))


def cmp(a: dict, b: dict) -> dict:
    return {
        "wealth_ratio": ratio(a, b),
        "return_win": bool(a["return"] >= b["return"]),
        "dd_ratio": float(abs(a["max_drawdown"]) / max(1e-12, abs(b["max_drawdown"]))),
        "dd_win": bool(abs(a["max_drawdown"]) <= abs(b["max_drawdown"])),
        "worst_ratio": float(abs(a["worst_day"]) / max(1e-12, abs(b["worst_day"]))),
        "worst_win": bool(abs(a["worst_day"]) <= abs(b["worst_day"])),
    }


def derive_ultra_threshold(data, raw, ex, guard, gross, base_cost: float) -> tuple[float, dict]:
    parent, parent_targets, _, _, _ = r86.build_parent_r73(data, raw, ex, guard, gross, base_cost)
    gate, _ = r88.daily_gate(parent.equity)
    pg = parent_targets.abs().sum(axis=1)
    positions = np.arange(0, len(pg), 24, dtype=int)
    dec = pd.Series(False, index=pg.index)
    dec.iloc[positions] = True
    train = pg.loc[dec & gate & pg.ge(r98.R97_GROSS_THRESHOLD) & (pg.index <= r98.TRAIN_END)]
    if len(train) < 50:
        raise RuntimeError(f"Too few qualified training decisions for R104: {len(train)}")
    threshold = float(train.quantile(ULTRA_QUANTILE))
    return threshold, {
        "source_rows": int(len(train)),
        "quantile": ULTRA_QUANTILE,
        "threshold": threshold,
        "train_end": r98.TRAIN_END.isoformat(),
        "minimum_parent_gross": r98.R97_GROSS_THRESHOLD,
        "selection_uses_outcome_labels": False,
    }


def build_variant(data, raw, ex, guard, gross, cost: float, ultra_threshold: float):
    parent, pt, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)
    pg = pt.abs().sum(axis=1)
    high = gate & pg.ge(r98.R97_GROSS_THRESHOLD)
    ultra = high & pg.ge(float(ultra_threshold))
    gross_cap = float(r86.P15["gross_cap"])

    ref_t = pt.copy()
    ref_t.loc[gate, :] = pt.loc[gate, :] * r98.R88_SCALE
    ref_t.loc[high, :] = pt.loc[high, :] * r98.R96_SCALE
    ref_t = cap(ref_t, gross_cap)

    cand_t = ref_t.copy()
    cand_t.loc[ultra, :] = pt.loc[ultra, :] * ULTRA_SCALE
    cand_t = cap(cand_t, gross_cap)

    ref = r36.run(data, ref_t, ex, cost, gross_cap, guard)
    cand = r36.run(data, cand_t, ex, cost, gross_cap, guard)
    diag = {
        **pdiag,
        **gdiag,
        "r98_high_fraction": float(high.mean()),
        "r104_ultra_fraction": float(ultra.mean()),
        "r104_ultra_decision_days": int(ultra.iloc[np.arange(0, len(ultra), 24, dtype=int)].sum()),
        "ultra_threshold": float(ultra_threshold),
        "ultra_scale": ULTRA_SCALE,
        "gross_cap": gross_cap,
        "turnover_r98": float(ref.turnover.sum()),
        "turnover_r104": float(cand.turnover.sum()),
        "turnover_ratio": float(cand.turnover.sum() / max(1e-12, ref.turnover.sum())),
        "fee_r98": float(ref.fees.sum()),
        "fee_r104": float(cand.fees.sum()),
        "protect_overlap_ultra_fraction": float((ultra & protect.reindex(ultra.index).fillna(False)).mean()),
    }
    return cand, ref, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, threshold, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    c, r, p, _ = build_variant(d, rr, ex, guard, gross, cost, threshold)
    return stats(c), stats(r), stats(p)


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base = float(ex["base_cost_per_side"])
    severe = float(ex["severe_cost_per_side"])
    super_severe = severe * 1.5
    threshold, threshold_diag = derive_ultra_threshold(data, raw, ex, guard, gross, base)

    cost_tests = {}
    base_objs = None
    for name, cost in (("base", base), ("severe", severe), ("super_severe_1p5x", super_severe)):
        c, r, p, d = build_variant(data, raw, ex, guard, gross, cost, threshold)
        cs, rs, ps = stats(c), stats(r), stats(p)
        cost_tests[name] = {"r104": cs, "r98": rs, "r73": ps, "vs_r98": cmp(cs, rs), "cost_per_side": cost, "diagnostics": d}
        if name == "base":
            base_objs = (c, r, p)
        gc.collect()

    c0, r0, p0 = base_objs
    hidx = c0.equity.index[c0.equity.index > r98.TRAIN_END]
    hs = hidx[0] if len(hidx) else c0.equity.index[-1]
    ch, rh, ph = r36.stats(c0.equity.loc[hs:]), r36.stats(r0.equity.loc[hs:]), r36.stats(p0.equity.loc[hs:])
    holdout = {"start": hs.isoformat(), "r104": ch, "r98": rh, "r73": ph, "vs_r98": cmp(ch, rh)}

    end = data.close.index[-1]
    isolated, alternative = {}, {}
    for days in HORIZONS:
        a, b, p = eval_slice(data, raw, ex, guard, gross, base, threshold, end - pd.Timedelta(days=days), end)
        isolated[str(days)] = {"r104": a, "r98": b, "r73": p, "vs_r98": cmp(a, b)}
        gc.collect()
    for days in ALT_HORIZONS:
        start = end - pd.Timedelta(days=days)
        if start < data.close.index[0]:
            continue
        a, b, p = eval_slice(data, raw, ex, guard, gross, base, threshold, start, end)
        alternative[str(days)] = {"r104": a, "r98": b, "r73": p, "vs_r98": cmp(a, b)}
        gc.collect()

    idx = data.close.index
    edges = np.linspace(0, len(idx), FOLDS + 1, dtype=int)
    folds = []
    for i in range(FOLDS):
        lo, hi = int(edges[i]), int(edges[i + 1] - 1)
        if hi <= lo:
            continue
        a, b, p = eval_slice(data, raw, ex, guard, gross, base, threshold, idx[lo], idx[hi])
        folds.append({"fold": i + 1, "start": idx[lo].isoformat(), "end": idx[hi].isoformat(), "r104": a, "r98": b, "vs_r98": cmp(a, b)})
        gc.collect()

    bc = cost_tests["base"]["vs_r98"]
    sc = cost_tests["severe"]["vs_r98"]
    ssc = cost_tests["super_severe_1p5x"]["vs_r98"]
    hc = holdout["vs_r98"]
    main_wins = sum(int(v["vs_r98"]["return_win"]) for v in isolated.values())
    alt_wins = sum(int(v["vs_r98"]["return_win"]) for v in alternative.values())
    fold_wins = sum(int(v["vs_r98"]["return_win"]) for v in folds)

    preliminary = bool(
        bc["wealth_ratio"] >= 1.01
        and hc["wealth_ratio"] >= 1.005
        and sc["wealth_ratio"] >= 1.0
        and ssc["wealth_ratio"] >= 0.995
        and bc["dd_ratio"] <= 1.05
        and hc["dd_ratio"] <= 1.05
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
                a, b, p = eval_slice(data, raw, ex, guard, gross, base, threshold, start, stop)
                rows.append({"start": start.isoformat(), "end": stop.isoformat(), "r104": a, "r98": b, "vs_r98": cmp(a, b)})
                gc.collect()
            wr = np.array([z["vs_r98"]["wealth_ratio"] for z in rows], dtype=float)
            random_windows[str(days)] = {
                "samples": len(rows),
                "return_win_rate": float(np.mean([z["vs_r98"]["return_win"] for z in rows])) if rows else 0.0,
                "dd_win_rate": float(np.mean([z["vs_r98"]["dd_win"] for z in rows])) if rows else 0.0,
                "median_wealth_ratio": float(np.median(wr)) if len(wr) else 0.0,
                "p10_wealth_ratio": float(np.quantile(wr, 0.10)) if len(wr) else 0.0,
                "windows": rows,
            }

    random_pass = bool(
        preliminary and random_windows
        and all(v["median_wealth_ratio"] >= 1.0 for v in random_windows.values())
        and all(v["return_win_rate"] >= 0.50 for v in random_windows.values())
        and random_windows["180"]["return_win_rate"] >= 0.60
        and random_windows["365"]["return_win_rate"] >= 0.60
    )

    gates = {
        "meaningful_full_growth": bool(bc["wealth_ratio"] >= 1.02),
        "full_risk": bool(bc["dd_ratio"] <= 1.05 and bc["worst_ratio"] <= 1.05),
        "holdout_growth": bool(hc["wealth_ratio"] >= 1.01),
        "holdout_risk": bool(hc["dd_ratio"] <= 1.05 and hc["worst_ratio"] <= 1.08),
        "severe_growth": bool(sc["wealth_ratio"] >= 1.01),
        "severe_risk": bool(sc["dd_ratio"] <= 1.06),
        "super_severe_growth": bool(ssc["wealth_ratio"] >= 1.005),
        "super_severe_risk": bool(ssc["dd_ratio"] <= 1.07),
        "main_horizons": bool(main_wins >= 4),
        "alternative_horizons": bool(alt_wins >= max(1, int(np.ceil(0.70 * len(alternative))))),
        "chronological_folds": bool(fold_wins >= 4),
        "random_windows": random_pass,
    }
    gates["r104_promotion_pass"] = bool(all(gates.values()))

    out = {
        "study": "V99 R104 nested 1.20x conviction tier on top of R98",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "retain R98 exactly, then allow a third 1.20x tier only in the upper quartile of already-qualified R98 high-gross daily decisions; the quartile threshold is derived from the first-60% training distribution only and uses no return labels",
        "precommitment": {
            "r88_scale": r98.R88_SCALE,
            "r98_high_scale": r98.R96_SCALE,
            "r98_high_gross_threshold": r98.R97_GROSS_THRESHOLD,
            "r104_ultra_scale": ULTRA_SCALE,
            "ultra_quantile": ULTRA_QUANTILE,
            "ultra_threshold_train_only": threshold,
            "threshold_diagnostics": threshold_diag,
            "threshold_refit_on_validation": False,
            "outcome_based_selection": False,
        },
        "cost_tests": cost_tests,
        "holdout": holdout,
        "isolated_horizons": isolated,
        "alternative_horizons": alternative,
        "chronological_folds": folds,
        "random_windows": {"seed": RNG_SEED, "samples_per_duration": SAMPLES_PER_DURATION, "executed": bool(preliminary), "results": random_windows},
        "summary_counts": {"main_return_wins": main_wins, "main_total": len(isolated), "alternative_return_wins": alt_wins, "alternative_total": len(alternative), "fold_return_wins": fold_wins, "fold_total": len(folds)},
        "preliminary_random_gate": preliminary,
        "promotion_gates": gates,
        "disclosure": "Historical research only. R104 changes only the exposure scale in a frozen train-defined upper-conviction subset; no benchmark, Frozen V99, Paper or R98 state is rewritten.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "threshold": threshold, "cost_tests": cost_tests, "holdout": holdout, "counts": out["summary_counts"], "preliminary": preliminary, "gates": gates}, indent=2), flush=True)


if __name__ == "__main__":
    main()
