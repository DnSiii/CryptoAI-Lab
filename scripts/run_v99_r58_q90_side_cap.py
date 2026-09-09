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
cap = r55.cap
REPORT = PROJECT / "reports" / "candidate_v99_r58_q90_side_cap.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
PARENT = {**r55.FIXED, "hedge_size": 0.15}

# Exact R57 q90 thresholds learned on the first 60% and already checked on holdout.
EARLY_DOMINANT = {
    "name": "early_dominant_q90",
    "lo": 0.05,
    "hi": 0.12,
    "feature": "dominant",
    "threshold": 1.201942535993832,
    "train_lift": 1.7955743828820754,
    "holdout_lift": 1.4646700350218835,
}
MID_GROSS = {
    "name": "mid_gross_q90",
    "lo": 0.08,
    "hi": 0.18,
    "feature": "gross",
    "threshold": 1.3500000000000003,
    "train_lift": 1.9358471098647683,
    "holdout_lift": 1.5470015771446433,
}
DEEP_GROSS = {
    "name": "deep_gross_q90",
    "lo": 0.12,
    "hi": 0.24,
    "feature": "gross",
    "threshold": 1.425,
    "train_lift": 1.4660524568393092,
    "holdout_lift": 2.206075191076224,
}
POLICIES = (
    {"name": "early_only", "rules": (EARLY_DOMINANT,)},
    {"name": "mid_only", "rules": (MID_GROSS,)},
    {"name": "deep_only", "rules": (DEEP_GROSS,)},
    {"name": "hierarchical_all", "rules": (EARLY_DOMINANT, MID_GROSS, DEEP_GROSS)},
)


def build_parent(data, raw, ex, guard, gross, cost):
    core = r36.run(data, raw, ex, cost, gross, guard)
    parent, _, targets, active = r55.build_with_shadow(
        data, raw, ex, guard, gross, cost, PARENT, shadow=core
    )
    return parent, targets, active


def side_cap_targets(parent_targets: pd.DataFrame, parent_equity: pd.Series, policy: dict):
    idx = parent_targets.index.intersection(parent_equity.index)
    t = parent_targets.reindex(idx).fillna(0.0).copy()
    eq = parent_equity.reindex(idx).astype(float)
    dd_depth = (1.0 - eq / eq.cummax()).clip(lower=0.0)

    gross = t.abs().sum(axis=1)
    long_gross = t.clip(lower=0.0).sum(axis=1)
    short_gross = (-t.clip(upper=0.0)).sum(axis=1)
    long_dom = long_gross >= short_gross
    dominant = pd.concat([long_gross, short_gross], axis=1).max(axis=1)

    desired_dom = dominant.copy()
    gate_any = pd.Series(False, index=idx)
    rule_stats = {}

    for rule in policy["rules"]:
        state = (dd_depth >= float(rule["lo"])) & (dd_depth < float(rule["hi"]))
        if rule["feature"] == "dominant":
            gate = state & (dominant > float(rule["threshold"]))
            rule_dom_target = pd.Series(float(rule["threshold"]), index=idx)
        elif rule["feature"] == "gross":
            gate = state & (gross > float(rule["threshold"]))
            reduction = (gross - float(rule["threshold"])).clip(lower=0.0)
            rule_dom_target = (dominant - reduction).clip(lower=0.0)
        else:
            raise ValueError(rule["feature"])

        desired_dom = desired_dom.where(~gate, np.minimum(desired_dom, rule_dom_target))
        gate_any |= gate
        rule_stats[rule["name"]] = {
            "active_fraction": float(gate.mean()),
            "threshold": float(rule["threshold"]),
            "train_lift": float(rule["train_lift"]),
            "holdout_lift": float(rule["holdout_lift"]),
        }

    scale = (desired_dom / dominant.replace(0.0, np.nan)).fillna(1.0).clip(0.0, 1.0)
    out = t.copy()
    long_mask = out.gt(0.0)
    short_mask = out.lt(0.0)
    for col in out.columns:
        out.loc[long_dom & long_mask[col], col] = (
            out.loc[long_dom & long_mask[col], col] * scale.loc[long_dom & long_mask[col]]
        )
        out.loc[(~long_dom) & short_mask[col], col] = (
            out.loc[(~long_dom) & short_mask[col], col] * scale.loc[(~long_dom) & short_mask[col]]
        )

    out = cap(out, float(PARENT["gross_cap"]))
    diag = {
        "active_fraction": float(gate_any.mean()),
        "mean_dominant_scale_when_active": float(scale.loc[gate_any].mean()) if gate_any.any() else 1.0,
        "p10_dominant_scale_when_active": float(scale.loc[gate_any].quantile(0.10)) if gate_any.any() else 1.0,
        "minimum_dominant_scale": float(scale.min()),
        "mean_gross_when_active": float(gross.loc[gate_any].mean()) if gate_any.any() else 0.0,
        "mean_dominant_when_active": float(dominant.loc[gate_any].mean()) if gate_any.any() else 0.0,
        "rules": rule_stats,
        "execution": "trim only positions belonging to the currently dominant long/short side; opposite side is untouched",
    }
    return out, gate_any, diag


def build_candidate(data, raw, ex, guard, gross, cost, policy):
    parent, parent_targets, hedge_active = build_parent(data, raw, ex, guard, gross, cost)
    targets, gate, diag = side_cap_targets(parent_targets, parent.equity, policy)
    result = r36.run(data, targets, ex, cost, float(PARENT["gross_cap"]), guard)
    return result, parent, targets, gate, {"side_cap": diag, "parent_hedge_active_fraction": float(hedge_active.mean())}


def isolated(data, raw, ex, guard, gross, cost, policy, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, parent, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, policy)
    return r36.stats(result.equity), r36.stats(parent.equity)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    parent, _, _ = build_parent(data, raw, ex, guard, gross, base_cost)
    parent_sev, _, _ = build_parent(data, raw, ex, guard, gross, severe_cost)
    parent_stats = r36.stats(parent.equity)
    parent_severe = r36.stats(parent_sev.equity)
    split = int(len(parent.equity) * 0.60)
    hold_start = parent.equity.index[min(split + 1, len(parent.equity) - 1)]
    parent_hold = r36.stats(parent.equity.loc[hold_start:])

    benchmarks = r55.benchmark_items(cand, data, raw, ex, guard, gross)
    full_bench = {
        name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench = {
        name: r36.exact_benchmark(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    full_env = r36.envelope(full_bench)
    severe_env = r36.envelope(severe_bench)

    rows = []
    for policy in POLICIES:
        result, _, _, gate, diag = build_candidate(data, raw, ex, guard, gross, base_cost, policy)
        sev_result, _, _, sev_gate, sev_diag = build_candidate(data, raw, ex, guard, gross, severe_cost, policy)
        s = r36.stats(result.equity)
        sev = r36.stats(sev_result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        sev_return_env = (1.0 + sev["return"]) / max(1e-12, 1.0 + severe_env["return"])
        parent_wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + parent_stats["return"])
        parent_hold_wealth = (1.0 + hold["return"]) / max(1e-12, 1.0 + parent_hold["return"])
        score = (
            10.0 * np.log(max(return_env, 1e-12))
            + 5.0 * np.log(max(sev_return_env, 1e-12))
            + 6.0 * np.log(max(parent_hold_wealth, 1e-12))
            + 20.0 * max(0.0, 1.0 - dd_env)
            - 20.0 * max(0.0, dd_env - 1.0)
            + 14.0 * max(0.0, 1.0 - worst_env)
            - 16.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "policy": policy["name"],
            "rules": list(policy["rules"]),
            "summary": s,
            "holdout": hold,
            "severe_cost": sev,
            "active_fraction": float(gate.mean()),
            "severe_active_fraction": float(sev_gate.mean()),
            "diagnostics": diag,
            "severe_diagnostics": sev_diag,
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "severe_return_ratio_to_envelope": float(sev_return_env),
            "wealth_ratio_to_parent": float(parent_wealth),
            "holdout_wealth_ratio_to_parent": float(parent_hold_wealth),
            "score": float(score),
        })
        gc.collect()

    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []
    for row in rows:
        policy = next(p for p in POLICIES if p["name"] == row["policy"])
        iso, iso_parent, iso_bench, wins, material = {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c, par = isolated(data, raw, ex, guard, gross, base_cost, policy, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            k = str(days)
            iso[k], iso_parent[k], iso_bench[k] = c, par, bench
            wins[k] = {
                "return": c["return"] >= env["return"],
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
            }
            material[k] = {
                "return": c["return"] >= env["return"] + r36.metric_margin(env["return"]),
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"] * 0.95,
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"] * 0.95,
            }

        alt = {}
        for days in ALT_HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            if start < earliest:
                continue
            c, par = isolated(data, raw, ex, guard, gross, base_cost, policy, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alt[str(days)] = {
                "candidate": c,
                "parent": par,
                "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        horizon_wins = sum(sum(v.values()) for v in wins.values())
        material_wins = sum(sum(v.values()) for v in material.values())
        alt_wins = sum(
            int(v["return_win"]) + int(v["drawdown_win"]) + int(v["worst_day_win"])
            for v in alt.values()
        )
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_dd_pass = abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
        full_worst_pass = abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        severe_return_pass = row["severe_cost"]["return"] >= severe_env["return"]
        severe_dd_pass = abs(row["severe_cost"]["max_drawdown"]) <= severe_env["max_drawdown_abs"]
        severe_worst_pass = abs(row["severe_cost"]["worst_day"]) <= severe_env["worst_day_abs"]
        finalists.append({
            **row,
            "isolated": iso,
            "isolated_parent": iso_parent,
            "isolated_benchmarks": iso_bench,
            "envelope_wins": wins,
            "material_envelope_wins": material,
            "alternative_horizons": alt,
            "requested_horizon_dimension_wins": int(horizon_wins),
            "requested_horizon_material_wins": int(material_wins),
            "alternative_dimension_wins": int(alt_wins),
            "full_return_pass": full_return_pass,
            "full_drawdown_pass": full_dd_pass,
            "full_worst_day_pass": full_worst_pass,
            "severe_return_pass": severe_return_pass,
            "severe_drawdown_pass": severe_dd_pass,
            "severe_worst_day_pass": severe_worst_pass,
            "dominant_gate_passed": bool(
                full_return_pass and full_dd_pass and full_worst_pass
                and severe_return_pass and severe_dd_pass and severe_worst_pass
                and horizon_wins == 15
                and all(v["return_win"] and v["drawdown_win"] and v["worst_day_win"] for v in alt.values())
            ),
        })
        gc.collect()

    finalists.sort(key=lambda z: (
        z["dominant_gate_passed"],
        z["requested_horizon_material_wins"],
        z["requested_horizon_dimension_wins"],
        z["alternative_dimension_wins"],
        z["severe_return_pass"], z["full_return_pass"], z["score"],
    ), reverse=True)
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R58 q90 side-specific continuation cap",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": (
            "preserve the R55 hedge-0.15 growth parent and, only in R57-validated drawdown-continuation states, "
            "trim the currently dominant long/short side back to the causal q90 risk threshold while leaving the opposite side untouched"
        ),
        "parent_fixed": PARENT,
        "parent_summary": parent_stats,
        "parent_severe": parent_severe,
        "threshold_source": "R57 first-60%-chronological q90 thresholds; each included rule had positive train and holdout lift for 7d/5pp continuation",
        "grid_policy": "4 predeclared structural policies; no free trim-size or cooldown parameter. The cap amount is implied directly by the q90 threshold.",
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "disclosure": "Historical research only. Gate state and target exposure use information known by close t and execute through the existing causal engine. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
