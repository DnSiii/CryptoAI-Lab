from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r28_direction_gate as r28
import run_v99_r55_low_hedge_amplitude_frontier as r55

r36 = r55.r36
r37 = r55.r37
cap = r55.cap
REPORT = PROJECT / "reports" / "v99_r72_r28_component_attribution.json"
H = (7, 30, 90, 180, 365)
RECENT_HOLD_START = pd.Timestamp("2024-01-05T00:00:00+00:00")
P15 = r55.params(0.15)
BASE_RULE = {
    "adverse24": 0.05,
    "adverse72": 0.10,
    "boost24": 0.04,
    "boost72": 0.08,
    "cooldown": 6,
}
VARIANTS = (
    {"name": "parent_h15", "cut_scale": 1.0, "boost_scale": 1.0, "gross_cap": 1.90},
    {"name": "boost_only_g19", "cut_scale": 1.0, "boost_scale": 1.30, "gross_cap": 1.90},
    {"name": "cut_only_g19", "cut_scale": 0.50, "boost_scale": 1.0, "gross_cap": 1.90},
    {"name": "both_g19", "cut_scale": 0.50, "boost_scale": 1.30, "gross_cap": 1.90},
    {"name": "boost_only_g21", "cut_scale": 1.0, "boost_scale": 1.30, "gross_cap": 2.10},
    {"name": "both_g21", "cut_scale": 0.50, "boost_scale": 1.30, "gross_cap": 2.10},
)


def build_targets(raw: pd.DataFrame, close: pd.DataFrame, shadow_eq: pd.Series, variant: dict):
    p = {**BASE_RULE, "cut_scale": variant["cut_scale"], "boost_scale": variant["boost_scale"], "gross_cap": variant["gross_cap"]}
    feat = r28.features(close)
    factor, adverse, aligned = r28.direction_factor(raw, close, *feat, p)
    adjusted = raw * factor

    # Preserve the current R55 h0.15 direct-hedge logic independently of the
    # R28 factor so the attribution measures the direction gate on the core,
    # not a modified hedge signal.
    active = r37.r30_stress_mask(shadow_eq, close["BTCUSDT"], P15)
    net = raw.sum(axis=1)
    direction = -np.sign(net).where(net.abs() >= P15["min_net"], 0.0)
    out = adjusted.copy()
    out["BTCUSDT"] = out["BTCUSDT"] + active.astype(float) * direction * P15["hedge_size"]
    out = cap(out, float(variant["gross_cap"]))
    diag = {
        "adverse_fraction": float(adverse.to_numpy(dtype=float).mean()),
        "aligned_fraction": float(aligned.to_numpy(dtype=float).mean()),
        "h15_stress_fraction": float(active.mean()),
        "gross_cap": float(variant["gross_cap"]),
    }
    return out, diag


def eval_full(data, raw, ex, guard, base_gross, cost, variant):
    shadow = r36.run(data, raw, ex, cost, base_gross, guard)
    targets, diag = build_targets(raw, data.close, shadow.equity, variant)
    res = r36.run(data, targets, ex, cost, float(variant["gross_cap"]), guard)
    return res, diag


def eval_slice(data, raw, ex, guard, base_gross, cost, variant, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    res, diag = eval_full(d, rr, ex, guard, base_gross, cost, variant)
    return r36.stats(res.equity), diag


def main():
    cand, data, raw, ex, guard, base_gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    end = data.close.index[-1]

    rows = []
    for variant in VARIANTS:
        res, diag = eval_full(data, raw, ex, guard, base_gross, base_cost, variant)
        sev, sev_diag = eval_full(data, raw, ex, guard, base_gross, severe_cost, variant)
        summary = r36.stats(res.equity)
        severe = r36.stats(sev.equity)
        hold_idx = res.equity.index[res.equity.index >= RECENT_HOLD_START]
        hold = r36.stats(res.equity.loc[hold_idx]) if len(hold_idx) > 1 else summary
        iso = {}
        for days in H:
            s, _ = eval_slice(data, raw, ex, guard, base_gross, base_cost, variant, end-pd.Timedelta(days=int(days)), end)
            iso[str(days)] = s
        rows.append({
            "variant": variant,
            "summary": summary,
            "holdout_after_2024_01_05": hold,
            "severe_cost": severe,
            "diagnostics": diag,
            "severe_diagnostics": sev_diag,
            "isolated": iso,
        })

    parent = next(x for x in rows if x["variant"]["name"] == "parent_h15")
    for row in rows:
        row["vs_parent"] = {
            "full_wealth_ratio": float((1+row["summary"]["return"])/max(1e-12,1+parent["summary"]["return"])),
            "full_dd_ratio": float(abs(row["summary"]["max_drawdown"])/max(1e-12,abs(parent["summary"]["max_drawdown"]))),
            "full_worst_ratio": float(abs(row["summary"]["worst_day"])/max(1e-12,abs(parent["summary"]["worst_day"]))),
            "severe_wealth_ratio": float((1+row["severe_cost"]["return"])/max(1e-12,1+parent["severe_cost"]["return"])),
            "holdout_wealth_ratio": float((1+row["holdout_after_2024_01_05"]["return"])/max(1e-12,1+parent["holdout_after_2024_01_05"]["return"])),
            "one_year_wealth_ratio": float((1+row["isolated"]["365"]["return"])/max(1e-12,1+parent["isolated"]["365"]["return"])),
        }

    rows.sort(key=lambda x: (
        x["vs_parent"]["one_year_wealth_ratio"],
        x["vs_parent"]["severe_wealth_ratio"],
        x["vs_parent"]["full_wealth_ratio"],
        -x["vs_parent"]["full_dd_ratio"],
    ), reverse=True)

    out = {
        "study": "V99 R72 R28 component attribution on current R55 h0.15 parent",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "separate the historical R28 aligned-position boost, adverse-position cut and extra gross-cap effects when layered on the current h0.15 hedge parent, without refitting any R28 threshold",
        "historical_r28_rule_fixed": BASE_RULE,
        "variant_policy": "six predeclared attribution variants: parent, boost-only, cut-only, both at gross 1.9, plus boost-only/both at the old R28 gross cap 2.1",
        "parent": parent,
        "ranked_variants": rows,
        "disclosure": "Diagnostic historical research only. R28 thresholds were historically selected on overlapping data and therefore R72 cannot promote a candidate. Its purpose is causal component attribution only. Any useful component must be rebuilt with a fresh train/holdout protocol before promotion. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps({"study": out["study"], "ranked": [{"variant": x["variant"], "summary": x["summary"], "severe": x["severe_cost"], "one_year": x["isolated"]["365"], "vs_parent": x["vs_parent"]} for x in rows]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
