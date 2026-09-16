from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase12_bhv_state_conditioned_gate as p12
import run_v99_r106_phase15_blv_shadow_alpha_health as p15
import run_v99_r106_phase17_blv_leadership_alpha as p17

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase18_blv_structure_router.json"
EPS = 1e-12
MIN_TRAIN_STATE_HOURS = 24 * 10
MIN_FOLD_STATE_HOURS = 24 * 2
MIN_HOLDOUT_STATE_HOURS = 24 * 3


def blv_substates(close: pd.DataFrame, direction: pd.Series, vol_state: pd.Series) -> dict[str, pd.Series]:
    """Three fixed causal market structures inside BULL+LOW_VOL.

    No fitted numeric threshold is used. Breadth is compared with its own trailing
    median available before the decision hour; short-horizon direction is the sign
    of the already-defined 7d BTC shock return.
    """
    _, _, diag = audit.classify_regimes(close)
    idx = close.index
    d = direction.shift(1).reindex(idx).fillna("UNKNOWN")
    v = vol_state.shift(1).reindex(idx).fillna("UNKNOWN")
    blv = d.eq("BULL") & v.eq("LOW_VOLATILITY")

    btc7 = diag["btc_7d_shock_return"].shift(1).reindex(idx)
    breadth = diag["breadth_30d"].shift(1).reindex(idx)
    breadth_reference = (
        diag["breadth_30d"]
        .rolling(24 * 90, min_periods=24 * 30)
        .median()
        .shift(1)
        .reindex(idx)
    )
    valid = blv & btc7.notna() & breadth.notna() & breadth_reference.notna()
    return {
        "PULLBACK": (valid & btc7.le(0.0)).fillna(False),
        "BROAD_ADVANCE": (valid & btc7.gt(0.0) & breadth.ge(breadth_reference)).fillna(False),
        "NARROW_ADVANCE": (valid & btc7.gt(0.0) & breadth.lt(breadth_reference)).fillna(False),
    }


def robust_state_mean(result, state: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    r = result.equity.pct_change(fill_method=None).fillna(0.0)
    m = state.reindex(r.index).fillna(False) & (r.index >= start) & (r.index <= end)
    values = r.loc[m].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return 0.0
    cutoff = np.quantile(values, 0.99)
    kept = values[values <= cutoff]
    return float(kept.mean()) if len(kept) else 0.0


def state_row(result, state: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    m = p4.segment_metrics(result.equity, state, start, end)
    m["robust_mean_without_top1pct"] = robust_state_mean(result, state, start, end)
    return m


def route_alpha(alpha: pd.DataFrame, state: pd.Series) -> pd.DataFrame:
    return alpha.where(state.reindex(alpha.index).fillna(False), 0.0)


def select_pair(
    sleeve_results: dict[str, object],
    states: dict[str, pd.Series],
    index: pd.DatetimeIndex,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
) -> tuple[tuple[str, str] | None, dict]:
    folds = p4.fold_bounds(index, train_start, train_end)
    matrix: dict[str, dict] = {}
    eligible_pairs: list[tuple[str, str, float]] = []

    for state_name, state in states.items():
        matrix[state_name] = {}
        for sleeve_name, result in sleeve_results.items():
            train = state_row(result, state, train_start, train_end)
            fold_rows = []
            valid = good = 0
            for i, (lo, hi) in enumerate(folds, 1):
                fm = state_row(result, state, lo, hi)
                fold_rows.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), **fm})
                if int(fm["active_hours"]) >= MIN_FOLD_STATE_HOURS:
                    valid += 1
                    good += int(
                        float(fm["roi"]) > 0.0
                        and float(fm["profit_factor"]) > 1.0
                        and float(fm["robust_mean_without_top1pct"]) > 0.0
                    )
            eligible = bool(
                int(train["active_hours"]) >= MIN_TRAIN_STATE_HOURS
                and float(train["roi"]) > 0.0
                and float(train["profit_factor"]) > 1.10
                and float(train["robust_mean_without_top1pct"]) > 0.0
                and valid >= 3
                and good >= 3
            )
            quality = (
                np.log(max(1.0 + float(train["roi"]), 1e-12))
                * max(float(train["profit_factor"]), 0.25)
                / max(float(train["max_drawdown_abs"]), 0.05)
                if eligible else -1e9
            )
            matrix[state_name][sleeve_name] = {
                "eligible": eligible,
                "quality_score": float(quality),
                "train": train,
                "valid_folds": int(valid),
                "good_folds": int(good),
                "folds": fold_rows,
            }
            if eligible:
                eligible_pairs.append((state_name, sleeve_name, float(quality)))

    if not eligible_pairs:
        selected = None
    else:
        best = max(eligible_pairs, key=lambda x: x[2])
        selected = (best[0], best[1])
    return selected, {
        "matrix": matrix,
        "selected_state": selected[0] if selected else None,
        "selected_sleeve": selected[1] if selected else None,
        "train_pass": bool(selected),
        "selection_uses_train_only": True,
    }


def analyze(result, data, direction, vol_state, start, end):
    return audit.analyze_result(result, data, direction, vol_state, start, end)


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_cost = severe_cost * 1.5
    direction, vol_state, _ = audit.classify_regimes(data.close)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, common_end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    enable_short_veto, phase7_diag = p12.choose_short_veto(data, raw, ex, guard, gross, direction, vol_state, base_cost)
    f7_targets, f7_base, _, r98_diag, _ = p12.build_f7_core(data, raw, ex, guard, gross, base_cost, enable_short_veto)

    states = blv_substates(data.close, direction, vol_state)
    sleeves = p17.fixed_blv_sleeves(data, direction, vol_state)
    sleeve_results = {
        name: p1.run_targets(data, target, ex, guard, base_cost, p1.GROSS_CAP)
        for name, target in sleeves.items()
    }

    selected, selection = select_pair(sleeve_results, states, data.close.index, common_start, train_end)
    state_name, sleeve_name = selected if selected else (None, None)

    holdout_pair = {}
    holdout_pair_pass = False
    selected_alpha = None
    if selected:
        state = states[state_name]
        result = sleeve_results[sleeve_name]
        holdout_pair = state_row(result, state, hold_start, common_end)
        holdout_pair_pass = bool(
            int(holdout_pair["active_hours"]) >= MIN_HOLDOUT_STATE_HOURS
            and float(holdout_pair["roi"]) > 0.0
            and float(holdout_pair["profit_factor"]) > 1.05
            and float(holdout_pair["robust_mean_without_top1pct"]) > 0.0
        )
        selected_alpha = route_alpha(sleeves[sleeve_name], state)

    candidate_targets, combine_diag = p17.combine(f7_targets, selected_alpha, enabled=bool(selected))
    candidate_base = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)

    f7_train = analyze(f7_base, data, direction, vol_state, common_start, train_end)
    cand_train = analyze(candidate_base, data, direction, vol_state, common_start, train_end)
    f7_hold = analyze(f7_base, data, direction, vol_state, hold_start, common_end)
    cand_hold = analyze(candidate_base, data, direction, vol_state, hold_start, common_end)
    f7_all = analyze(f7_base, data, direction, vol_state, common_start, common_end)
    cand_all = analyze(candidate_base, data, direction, vol_state, common_start, common_end)
    train_delta = p15.core_delta(cand_train, f7_train)
    hold_delta = p15.core_delta(cand_hold, f7_hold)
    global_delta = p15.core_delta(cand_all, f7_all)

    f7_state_diag = {}
    for name, state in states.items():
        f7_state_diag[name] = {
            "train": state_row(f7_base, state, common_start, train_end),
            "holdout": state_row(f7_base, state, hold_start, common_end),
            "full": state_row(f7_base, state, common_start, common_end),
        }

    fold_rows = []
    nonharm_folds = 0
    pareto_folds = 0
    for i, (lo, hi) in enumerate(p4.fold_bounds(data.close.index, common_start, train_end), 1):
        b = analyze(f7_base, data, direction, vol_state, lo, hi)
        c = analyze(candidate_base, data, direction, vol_state, lo, hi)
        d = p15.core_delta(c, b)
        strict = p15.core_pareto(d)
        nonharm = bool(d["wealth_ratio"] >= 0.995 and d["dd_delta"] <= 0.01 and d["pf_delta"] >= -0.03)
        pareto_folds += int(strict)
        nonharm_folds += int(nonharm)
        fold_rows.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), "delta": d, "strict_pareto": strict, "nonharm": nonharm})

    stress = {}
    stress_pass = True
    for label, cost in (("severe", severe_cost), ("supersevere", super_cost)):
        f7_t, f7_r, _, _, _ = p12.build_f7_core(data, raw, ex, guard, gross, cost, enable_short_veto)
        cand_t, cdiag = p17.combine(f7_t, selected_alpha, enabled=bool(selected))
        cand_r = p1.run_targets(data, cand_t, ex, guard, cost, p1.GROSS_CAP)
        b_all = analyze(f7_r, data, direction, vol_state, common_start, common_end)
        c_all = analyze(cand_r, data, direction, vol_state, common_start, common_end)
        b_hold = analyze(f7_r, data, direction, vol_state, hold_start, common_end)
        c_hold = analyze(cand_r, data, direction, vol_state, hold_start, common_end)
        d_all = p15.core_delta(c_all, b_all)
        d_hold = p15.core_delta(c_hold, b_hold)
        pa = p15.core_pareto(d_all)
        ph = p15.core_pareto(d_hold)
        stress_pass = stress_pass and pa and ph
        stress[label] = {"combine": cdiag, "delta": d_all, "holdout_delta": d_hold, "strict_pareto": pa, "holdout_strict_pareto": ph}

    bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    bench = {
        name: analyze(result, benchmarks[name]["data"], direction, vol_state, common_start, common_end)
        for name, result in bench_results.items()
    }
    envelope = audit.metric_envelope({name: row["global"] for name, row in bench.items()})
    envelope_cmp = audit.candidate_vs_envelope(cand_all["global"], envelope)

    accepted = bool(
        selection["train_pass"]
        and holdout_pair_pass
        and p15.core_pareto(train_delta)
        and nonharm_folds >= 3
        and p15.core_pareto(hold_delta)
        and p15.core_pareto(global_delta)
        and stress_pass
    )

    out = {
        "study": "V99 R106 phase 18 — causal BULL+LOW_VOL market-structure router",
        "status": "PROMOTABLE_RESEARCH_CANDIDATE" if accepted else "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "test whether phase17 leadership alpha is structurally stable only within fixed causal BULL+LOW_VOL market structures",
            "substates": ["PULLBACK", "BROAD_ADVANCE", "NARROW_ADVANCE"],
            "substate_definition": "PULLBACK: prior-known BTC 7d<=0; BROAD/NARROW_ADVANCE: BTC 7d>0 and prior-known breadth30 above/below its own trailing 90d median",
            "alpha_family_frozen_from_phase17": list(sleeves),
            "alpha_parameters_changed_from_phase17": False,
            "selection_uses_train_only": True,
            "holdout_used_for_selection": False,
            "no_numeric_threshold_grid": True,
            "regime_and_substate_features_causal_t_minus_1": True,
            "fold_gate": ">=3 valid and >=3 positive/PF>1/tail-robust folds for a fixed state+sleeve pair",
            "holdout_gate": "only the train-selected state+sleeve pair is validated; no rescue pair",
            "promotion_gate": "pair survives holdout and combined core is strict Pareto on train/holdout/full/severe/supersevere with >=3 nonharm train folds",
        },
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "train_end": train_end.isoformat(), "holdout_start": hold_start.isoformat()},
        "phase7_short_veto_enabled": enable_short_veto,
        "phase7_side_train": phase7_diag,
        "f7_substate_diagnostics": f7_state_diag,
        "selection": selection,
        "selected_holdout": holdout_pair,
        "selected_holdout_pass": holdout_pair_pass,
        "combine": combine_diag,
        "f7": f7_all,
        "candidate": cand_all,
        "f7_train": f7_train,
        "candidate_train": cand_train,
        "f7_holdout": f7_hold,
        "candidate_holdout": cand_hold,
        "global_delta": global_delta,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "train_folds": fold_rows,
        "pareto_train_folds": pareto_folds,
        "nonharm_train_folds": nonharm_folds,
        "stress": stress,
        "vs_v13_v16_metric_envelope": envelope_cmp,
        "pass_count": {"passed": sum(int(v["passed"]) for v in envelope_cmp.values()), "total": len(envelope_cmp)},
        "research_gate": {"accepted": accepted, "reason": "no promotion unless a fixed BLV structure explains stable alpha across folds and survives untouched holdout plus stressed exact replay"},
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research and chronological holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_state": selection["selected_state"],
        "selected_sleeve": selection["selected_sleeve"],
        "train_pass": selection["train_pass"],
        "selected_holdout_pass": holdout_pair_pass,
        "selected_holdout": holdout_pair,
        "f7_substates": f7_state_diag,
        "research_gate": out["research_gate"],
        "f7": p12.compact(f7_all),
        "candidate": p12.compact(cand_all),
        "f7_holdout": p12.compact(f7_hold),
        "candidate_holdout": p12.compact(cand_hold),
        "global_delta": global_delta,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "nonharm_train_folds": nonharm_folds,
        "stress": stress,
        "pass_count": out["pass_count"],
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
