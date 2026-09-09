from __future__ import annotations

import gc
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r59_h15_mild_crash as r59

r36 = r59.r36
r37 = r59.r37
cap = r59.cap
REPORT = PROJECT / "reports" / "candidate_v99_r64_severe_medium_hedge_topup.json"
PARENT = r59.PARENT
MEDIUM = r59.CRASH_PRESETS[0]
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
FEATURE_TRAIN_END = pd.Timestamp("2023-03-15T15:00:00+00:00")
CORE_NET_Q80 = 0.6394893988807664
DOMINANT_Q80 = 0.9402306763453886

GATES = (
    {"name": "drawdown_accel", "type": "drawdown_accel"},
    {"name": "core_net_q80", "type": "core_net", "threshold": CORE_NET_Q80},
    {"name": "dominant_q80", "type": "dominant", "threshold": DOMINANT_Q80},
)
TOPUPS = (0.10, 0.25)
PULSE_HOURS = 12


def build_parent(data, raw, ex, guard, gross, cost):
    return r59.build_parent(data, raw, ex, guard, gross, cost)


def severe_medium_gate(parent, targets: pd.DataFrame, close: pd.DataFrame, gate_def: dict):
    eq = parent.equity.reindex(targets.index).astype(float)
    btc = close["BTCUSDT"].reindex(targets.index)
    r6 = eq.pct_change(6, fill_method=None)
    r24 = eq.pct_change(24, fill_method=None)
    dd = eq / eq.cummax() - 1.0
    b24 = btc.pct_change(24, fill_method=None)
    b72 = btc.pct_change(72, fill_method=None)

    fast = r6 <= MEDIUM["r6_trigger"]
    accel = (dd <= MEDIUM["dd_trigger"]) & (r24 <= MEDIUM["r24_trigger"])
    conflict = ((b24 <= MEDIUM["btc24_trigger"]) | (b72 <= MEDIUM["btc72_trigger"])) & (r6 < 0.0)
    instant = (fast | accel | conflict).fillna(False)
    medium_active = instant.astype(float).rolling(int(MEDIUM["cooldown"]), min_periods=1).max().gt(0.0)
    entry = medium_active & ~medium_active.shift(1, fill_value=False)

    long_gross = targets.clip(lower=0.0).sum(axis=1)
    short_gross = (-targets.clip(upper=0.0)).sum(axis=1)
    dominant = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    core_net_abs = (targets["BTCUSDT"] + targets["ETHUSDT"]).abs()

    if gate_def["type"] == "drawdown_accel":
        qualified = entry & accel
        observed = accel.astype(float)
    elif gate_def["type"] == "core_net":
        qualified = entry & (core_net_abs >= float(gate_def["threshold"]))
        observed = core_net_abs
    elif gate_def["type"] == "dominant":
        qualified = entry & (dominant >= float(gate_def["threshold"]))
        observed = dominant
    else:
        raise ValueError(gate_def)

    pulse = qualified.astype(float).rolling(PULSE_HOURS, min_periods=1).max().gt(0.0)
    return pulse, {
        "medium_entry_count": int(entry.sum()),
        "qualified_entry_count": int(qualified.sum()),
        "qualified_entry_fraction_of_medium": float(qualified.sum() / max(1, int(entry.sum()))),
        "pulse_active_fraction": float(pulse.mean()),
        "observed_median_at_qualified_entry": float(observed.loc[qualified].median()) if qualified.any() else 0.0,
    }


def apply_topup(data, parent, parent_targets, ex, guard, cost, gate_def, topup):
    pulse, diag = severe_medium_gate(parent, parent_targets, data.close, gate_def)
    targets = parent_targets.copy()
    net = parent_targets.sum(axis=1)
    direction = -np.sign(net).where(net.abs() >= float(PARENT["min_net"]), 0.0)
    targets["BTCUSDT"] = targets["BTCUSDT"] + pulse.astype(float) * direction * float(topup)
    targets = cap(targets, float(PARENT["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(PARENT["gross_cap"]), guard)
    return result, targets, pulse, diag


def build_candidate(data, raw, ex, guard, gross, cost, p):
    parent, shadow, parent_targets, parent_active = build_parent(data, raw, ex, guard, gross, cost)
    result, targets, pulse, diag = apply_topup(
        data, parent, parent_targets, ex, guard, cost, p["gate"], p["topup"]
    )
    return result, parent, targets, pulse, {
        "parent_hedge_active_fraction": float(parent_active.mean()),
        "severe_medium": diag,
    }


def isolated(data, raw, ex, guard, gross, cost, p, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, parent, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, p)
    return r36.stats(result.equity), r36.stats(parent.equity)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    parent, _, parent_targets, parent_active = build_parent(data, raw, ex, guard, gross, base_cost)
    parent_sev, _, parent_targets_sev, parent_active_sev = build_parent(data, raw, ex, guard, gross, severe_cost)
    parent_stats = r36.stats(parent.equity)
    parent_severe = r36.stats(parent_sev.equity)
    hold_candidates = parent.equity.index[parent.equity.index > FEATURE_TRAIN_END]
    hold_start = hold_candidates[0] if len(hold_candidates) else parent.equity.index[-1]
    parent_hold = r36.stats(parent.equity.loc[hold_start:])

    benchmarks = r59.r55.benchmark_items(cand, data, raw, ex, guard, gross)
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
    for gate_def, topup in itertools.product(GATES, TOPUPS):
        p = {"gate": gate_def, "topup": topup, "pulse_hours": PULSE_HOURS}
        result, _, pulse, diag = apply_topup(data, parent, parent_targets, ex, guard, base_cost, gate_def, topup)
        sev_result, _, sev_pulse, sev_diag = apply_topup(
            data, parent_sev, parent_targets_sev, ex, guard, severe_cost, gate_def, topup
        )
        s = r36.stats(result.equity)
        sev = r36.stats(sev_result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        sev_return_env = (1.0 + sev["return"]) / max(1e-12, 1.0 + severe_env["return"])
        hold_parent = (1.0 + hold["return"]) / max(1e-12, 1.0 + parent_hold["return"])
        score = (
            9.0 * np.log(max(return_env, 1e-12))
            + 7.0 * np.log(max(sev_return_env, 1e-12))
            + 6.0 * np.log(max(hold_parent, 1e-12))
            + 22.0 * max(0.0, 1.0 - dd_env)
            - 24.0 * max(0.0, dd_env - 1.0)
            + 20.0 * max(0.0, 1.0 - worst_env)
            - 22.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "params": p, "summary": s, "holdout_after_feature_train": hold,
            "severe_cost": sev, "diagnostics": diag, "severe_diagnostics": sev_diag,
            "pulse_active_fraction": float(pulse.mean()),
            "severe_pulse_active_fraction": float(sev_pulse.mean()),
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "severe_return_ratio_to_envelope": float(sev_return_env),
            "holdout_wealth_ratio_to_parent": float(hold_parent),
            "score": float(score),
        })
        gc.collect()

    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []
    for row in rows:
        p = row["params"]
        iso, iso_parent, iso_bench, wins, material = {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=int(days))
            c, par = isolated(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench); k = str(days)
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
            start = common_end - pd.Timedelta(days=int(days))
            if start < earliest:
                continue
            c, par = isolated(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alt[str(days)] = {
                "candidate": c, "parent": par, "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_dd_pass = abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
        full_worst_pass = abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        severe_return_pass = row["severe_cost"]["return"] >= severe_env["return"]
        severe_dd_pass = abs(row["severe_cost"]["max_drawdown"]) <= severe_env["max_drawdown_abs"]
        severe_worst_pass = abs(row["severe_cost"]["worst_day"]) <= severe_env["worst_day_abs"]
        horizon_wins = sum(sum(v.values()) for v in wins.values())
        material_wins = sum(sum(v.values()) for v in material.values())
        alt_wins = sum(int(v["return_win"])+int(v["drawdown_win"])+int(v["worst_day_win"]) for v in alt.values())
        finalists.append({
            **row, "isolated": iso, "isolated_parent": iso_parent,
            "isolated_benchmarks": iso_bench, "envelope_wins": wins,
            "material_envelope_wins": material, "alternative_horizons": alt,
            "requested_horizon_dimension_wins": int(horizon_wins),
            "requested_horizon_material_wins": int(material_wins),
            "alternative_dimension_wins": int(alt_wins),
            "full_return_pass": full_return_pass, "full_drawdown_pass": full_dd_pass,
            "full_worst_day_pass": full_worst_pass, "severe_return_pass": severe_return_pass,
            "severe_drawdown_pass": severe_dd_pass, "severe_worst_day_pass": severe_worst_pass,
            "dominant_gate_passed": bool(
                full_return_pass and full_dd_pass and full_worst_pass
                and severe_return_pass and severe_dd_pass and severe_worst_pass
                and horizon_wins == 15 and material_wins == 15
                and all(v["return_win"] and v["drawdown_win"] and v["worst_day_win"] for v in alt.values())
            ),
        })
        gc.collect()

    finalists.sort(key=lambda z: (
        z["dominant_gate_passed"], z["requested_horizon_material_wins"],
        z["requested_horizon_dimension_wins"], z["alternative_dimension_wins"],
        z["full_return_pass"], z["severe_return_pass"], z["full_drawdown_pass"],
        z["full_worst_day_pass"], z["severe_drawdown_pass"], z["severe_worst_day_pass"], z["score"]
    ), reverse=True)
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R64 severe-medium selective BTC hedge top-up",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": (
            "keep the R55 hedge-0.15 growth parent unchanged and add a short opposite-net BTC hedge only after "
            "R63-validated severe medium-entry conditions, seeking tail protection without broad deleveraging"
        ),
        "parent_fixed": PARENT, "parent_summary": parent_stats,
        "parent_holdout_after_feature_train": parent_hold, "parent_severe": parent_severe,
        "feature_train_end": FEATURE_TRAIN_END.isoformat(), "medium_fixed": MEDIUM,
        "gate_policy": {
            "drawdown_accel": "exact medium component; no fitted threshold",
            "core_net_q80": CORE_NET_Q80,
            "dominant_q80": DOMINANT_Q80,
            "threshold_source": "R63 first-60%-of-events training split only",
        },
        "grid_policy": "6 predeclared combinations = 3 R63 severe-entry gates x structural BTC hedge top-ups +0.10/+0.25; fixed 12h pulse; no broad exposure cut and no signal retuning",
        "full_benchmarks": full_bench, "full_envelope": full_env,
        "severe_benchmarks": severe_bench, "severe_envelope": severe_env,
        "selected": selected, "finalists": finalists,
        "disclosure": (
            "Historical research only. Gate thresholds are frozen from R63 training events and candidate evaluation "
            "uses later holdout plus isolated horizons and severe costs. Frozen V99/paper remains untouched."
        ),
        "funding_quarantined_symbols": quarantined, "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)

if __name__ == "__main__":
    main()
