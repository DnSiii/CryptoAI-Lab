from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase7_train_validated_bhv_short_veto as p7
import run_v99_r106_phase12_bhv_state_conditioned_gate as p12
import run_v99_r106_phase15_blv_shadow_alpha_health as p15
import run_v99_r106_phase18_blv_structure_router as p18

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase19_blv_broad_advance_short_veto.json"
MIN_FOLD_STATE_HOURS = 24 * 2
MIN_HOLDOUT_STATE_HOURS = 24 * 3


def veto_shorts(targets, mask):
    out = targets.copy()
    out.loc[mask, :] = targets.loc[mask].clip(lower=0.0)
    return out


def side_fold_diagnostics(result, state, folds, desired: str):
    rows = []
    valid = passed = 0
    for i, (lo, hi) in enumerate(folds, 1):
        row = p18.state_row(result, state, lo, hi)
        eligible = int(row["active_hours"]) >= MIN_FOLD_STATE_HOURS
        if eligible:
            valid += 1
            if desired == "healthy":
                ok = bool(
                    float(row["roi"]) > 0.0
                    and float(row["profit_factor"]) > 1.0
                    and float(row["robust_mean_without_top1pct"]) > 0.0
                )
            else:
                ok = bool(
                    float(row["roi"]) < 0.0
                    and float(row["profit_factor"]) < 1.0
                    and float(row["robust_mean_without_top1pct"]) < 0.0
                )
            passed += int(ok)
        else:
            ok = False
        rows.append({
            "fold": i,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "eligible": eligible,
            "passed": ok,
            **row,
        })
    return {"valid_folds": valid, "passed_folds": passed, "folds": rows}


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

    enable_bhv_veto, phase7_diag = p12.choose_short_veto(
        data, raw, ex, guard, gross, direction, vol_state, base_cost
    )
    f7_targets, f7_base, _, r98_diag, _ = p12.build_f7_core(
        data, raw, ex, guard, gross, base_cost, enable_bhv_veto
    )

    states = p18.blv_substates(data.close, direction, vol_state)
    broad = states["BROAD_ADVANCE"]
    long_targets = p7.isolated_side_targets(f7_targets, broad, "long")
    short_targets = p7.isolated_side_targets(f7_targets, broad, "short")
    long_result = p1.run_targets(data, long_targets, ex, guard, base_cost, p1.GROSS_CAP)
    short_result = p1.run_targets(data, short_targets, ex, guard, base_cost, p1.GROSS_CAP)

    long_train = p18.state_row(long_result, broad, common_start, train_end)
    short_train = p18.state_row(short_result, broad, common_start, train_end)
    folds = p4.fold_bounds(data.close.index, common_start, train_end)
    long_folds = side_fold_diagnostics(long_result, broad, folds, "healthy")
    short_folds = side_fold_diagnostics(short_result, broad, folds, "harmful")

    train_pass = bool(
        int(long_train["active_hours"]) >= MIN_FOLD_STATE_HOURS
        and int(short_train["active_hours"]) >= MIN_FOLD_STATE_HOURS
        and float(long_train["roi"]) > 0.0
        and float(long_train["profit_factor"]) > 1.0
        and float(long_train["robust_mean_without_top1pct"]) > 0.0
        and float(short_train["roi"]) < 0.0
        and float(short_train["profit_factor"]) < 1.0
        and float(short_train["robust_mean_without_top1pct"]) < 0.0
        and int(long_folds["valid_folds"]) >= 3
        and int(short_folds["valid_folds"]) >= 3
        and int(long_folds["passed_folds"]) >= 3
        and int(short_folds["passed_folds"]) >= 3
    )

    candidate_targets = veto_shorts(f7_targets, broad) if train_pass else f7_targets.copy()
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

    core_fold_rows = []
    nonharm_folds = pareto_folds = 0
    for i, (lo, hi) in enumerate(folds, 1):
        b = analyze(f7_base, data, direction, vol_state, lo, hi)
        c = analyze(candidate_base, data, direction, vol_state, lo, hi)
        d = p15.core_delta(c, b)
        strict = p15.core_pareto(d)
        nonharm = bool(d["wealth_ratio"] >= 0.995 and d["dd_delta"] <= 0.01 and d["pf_delta"] >= -0.03)
        pareto_folds += int(strict)
        nonharm_folds += int(nonharm)
        core_fold_rows.append({
            "fold": i,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "delta": d,
            "strict_pareto": strict,
            "nonharm": nonharm,
        })

    holdout_broad_hours = int(broad.loc[(broad.index >= hold_start) & (broad.index <= common_end)].sum())
    holdout_eligible = holdout_broad_hours >= MIN_HOLDOUT_STATE_HOURS

    stress = {}
    stress_pass = True
    for name, cost in (("severe", severe_cost), ("supersevere", super_cost)):
        f7_t, f7_r, _, _, _ = p12.build_f7_core(data, raw, ex, guard, gross, cost, enable_bhv_veto)
        cand_t = veto_shorts(f7_t, broad) if train_pass else f7_t.copy()
        cand_r = p1.run_targets(data, cand_t, ex, guard, cost, p1.GROSS_CAP)
        b_all = analyze(f7_r, data, direction, vol_state, common_start, common_end)
        c_all = analyze(cand_r, data, direction, vol_state, common_start, common_end)
        b_hold = analyze(f7_r, data, direction, vol_state, hold_start, common_end)
        c_hold = analyze(cand_r, data, direction, vol_state, hold_start, common_end)
        d_all = p15.core_delta(c_all, b_all)
        d_hold = p15.core_delta(c_hold, b_hold)
        pass_all = p15.core_pareto(d_all)
        pass_hold = p15.core_pareto(d_hold)
        stress_pass = stress_pass and pass_all and pass_hold
        stress[name] = {
            "delta": d_all,
            "holdout_delta": d_hold,
            "strict_pareto": pass_all,
            "holdout_strict_pareto": pass_hold,
        }

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
        train_pass
        and p15.core_pareto(train_delta)
        and nonharm_folds >= 3
        and holdout_eligible
        and p15.core_pareto(hold_delta)
        and p15.core_pareto(global_delta)
        and stress_pass
    )

    out = {
        "study": "V99 R106 phase 19 — BULL+LOW_VOL BROAD_ADVANCE short-veto audit",
        "status": "PROMOTABLE_RESEARCH_CANDIDATE" if accepted else "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "hypothesis": "inside causal BULL+LOW_VOL BROAD_ADVANCE, F7 shorts may systematically fight broad market appreciation while longs remain healthy",
            "candidate_action": "veto only short exposure inside BROAD_ADVANCE; never choose side after seeing results",
            "selection_uses_train_only": True,
            "holdout_used_for_selection": False,
            "no_numeric_threshold_grid": True,
            "regime_and_substate_features_causal_t_minus_1": True,
            "train_gate": "long aggregate ROI>0/PF>1/tail-robust and >=3 healthy folds; short aggregate ROI<0/PF<1/tail-negative and >=3 harmful folds",
            "promotion_gate": "candidate must Pareto-improve F7 on train, untouched holdout, full path, severe and supersevere exact replay; >=3 train folds nonharmful",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "holdout_broad_advance_hours": holdout_broad_hours,
        },
        "phase7_short_veto_enabled": enable_bhv_veto,
        "phase7_side_train": phase7_diag,
        "selection": {
            "train_pass": train_pass,
            "long_train": long_train,
            "short_train": short_train,
            "long_folds": long_folds,
            "short_folds": short_folds,
        },
        "f7": f7_all,
        "candidate": cand_all,
        "f7_train": f7_train,
        "candidate_train": cand_train,
        "f7_holdout": f7_hold,
        "candidate_holdout": cand_hold,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "global_delta": global_delta,
        "train_folds": core_fold_rows,
        "pareto_train_folds": pareto_folds,
        "nonharm_train_folds": nonharm_folds,
        "stress": stress,
        "vs_v13_v16_metric_envelope": envelope_cmp,
        "pass_count": {"passed": sum(int(v["passed"]) for v in envelope_cmp.values()), "total": len(envelope_cmp)},
        "research_gate": {
            "accepted": accepted,
            "reason": "no promotion unless broad-advance short harm is stable in train folds and the frozen veto improves untouched holdout plus stressed exact replay",
        },
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research and chronological untouched holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")

    print(json.dumps({
        "train_pass": train_pass,
        "long_train": long_train,
        "short_train": short_train,
        "long_fold_passes": long_folds["passed_folds"],
        "short_fold_passes": short_folds["passed_folds"],
        "research_gate": out["research_gate"],
        "f7": p12.compact(f7_all),
        "candidate": p12.compact(cand_all),
        "f7_holdout": p12.compact(f7_hold),
        "candidate_holdout": p12.compact(cand_hold),
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "global_delta": global_delta,
        "nonharm_train_folds": nonharm_folds,
        "stress": stress,
        "pass_count": out["pass_count"],
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
