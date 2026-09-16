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
import run_v99_r106_phase12_bhv_state_conditioned_gate as p12

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase14_bull_low_vol_structural_gate.json"
EPS = 1e-12
HORIZON = 3
MIN_SELECTED = 200
MIN_FOLD_SELECTED = 30
MIN_COVERAGE = 0.05
MAX_COVERAGE = 0.70


def forward_sum_frame(frame: pd.DataFrame, hours: int) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=frame.index, columns=frame.columns)
    for k in range(1, hours + 1):
        out = out.add(frame.shift(-k), fill_value=0.0)
    return out


def net_asset_pnl(result) -> pd.DataFrame:
    return result.asset_gross.fillna(0.0) - result.asset_fees.fillna(0.0) - result.asset_funding.fillna(0.0)


def trim_bottom(values: np.ndarray, q: float = 0.01) -> float:
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return 0.0
    cutoff = np.quantile(values, q)
    use = values[values >= cutoff]
    return float(use.mean()) if len(use) else 0.0


def blv_mask(index: pd.DatetimeIndex, direction: pd.Series, vol: pd.Series) -> pd.Series:
    d = direction.shift(1).reindex(index)
    v = vol.shift(1).reindex(index)
    return (d.eq("BULL") & v.eq("LOW_VOLATILITY")).fillna(False)


def broadcast(series: pd.Series, columns: pd.Index) -> pd.DataFrame:
    values = np.repeat(series.to_numpy()[:, None], len(columns), axis=1)
    return pd.DataFrame(values, index=series.index, columns=columns)


def build_rules(targets: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    close = close.reindex(index=targets.index, columns=targets.columns).astype(float)
    # Every market feature is shifted one bar: the gate at t only sees information through t-1.
    r3 = close.pct_change(3, fill_method=None).shift(1)
    r24 = close.pct_change(24, fill_method=None).shift(1)
    broad24 = r24.median(axis=1)
    rel24 = r24.sub(broad24, axis=0)

    long_side = targets > EPS
    short_side = targets < -EPS
    broad_up = broadcast(broad24 > 0.0, targets.columns)

    abs_w = targets.abs()
    active_w = abs_w.where(abs_w > EPS)
    q75 = active_w.quantile(0.75, axis=1)
    concentrated = abs_w.ge(q75, axis=0) & abs_w.gt(EPS)

    return {
        # Shorts fighting a slow bull grind.
        "short_against_broad_24h_up": short_side & broad_up,
        "short_asset_24h_up": short_side & r24.gt(0.0),
        "short_relative_winner_24h": short_side & rel24.gt(0.0),
        "short_broad_up_and_relative_winner": short_side & broad_up & rel24.gt(0.0),
        # Longs that may be late/exhausted in a low-volatility grind.
        "long_3h_down_after_24h_up": long_side & r24.gt(0.0) & r3.lt(0.0),
        "long_relative_loser_24h": long_side & rel24.lt(0.0),
        "long_decelerating_relative_loser": long_side & r24.gt(0.0) & r3.lt(0.0) & rel24.lt(0.0),
        # Concentration hypothesis: the largest active weights may dominate BLV drawdowns.
        "top_quartile_weight": concentrated,
    }


def eval_harm(
    rule: pd.DataFrame,
    eligible: pd.DataFrame,
    future: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    rows = (eligible.index >= start) & (eligible.index <= end)
    e = eligible.loc[rows]
    r = rule.loc[rows] & e
    f = future.loc[rows]

    vals = f.where(r).stack().dropna().to_numpy(dtype=float)
    base_vals = f.where(e).stack().dropna().to_numpy(dtype=float)
    selected = int(r.to_numpy().sum())
    total = int(e.to_numpy().sum())

    mean = float(vals.mean()) if len(vals) else 0.0
    base_mean = float(base_vals.mean()) if len(base_vals) else 0.0
    positive = float((vals > 0.0).mean()) if len(vals) else 0.0
    base_positive = float((base_vals > 0.0).mean()) if len(base_vals) else 0.0
    robust = trim_bottom(vals, 0.01)

    return {
        "eligible_asset_hours": total,
        "selected_asset_hours": selected,
        "coverage": float(selected / total) if total else 0.0,
        "mean_future_net_pnl": mean,
        "mean_without_bottom1pct": robust,
        "base_mean_future_net_pnl": base_mean,
        "mean_delta_vs_blv_active": float(mean - base_mean),
        "positive_rate": positive,
        "base_positive_rate": base_positive,
        "positive_rate_delta": float(positive - base_positive),
    }


def diagnostic_good(row: dict) -> bool:
    return bool(
        row.get("selected_asset_hours", 0) >= MIN_FOLD_SELECTED
        and row.get("mean_without_bottom1pct", 0.0) < 0.0
        and row.get("mean_delta_vs_blv_active", 0.0) < 0.0
        and row.get("positive_rate_delta", 0.0) <= 0.0
    )


def apply_rule_veto(
    targets: pd.DataFrame,
    selected_rule: str | None,
    close: pd.DataFrame,
    blv: pd.Series,
) -> pd.DataFrame:
    if not selected_rule:
        return targets.copy()
    rules = build_rules(targets, close)
    out = targets.copy()
    eligible = targets.abs().gt(EPS).mul(blv.reindex(targets.index).fillna(False), axis=0)
    flagged = rules[selected_rule] & eligible
    return out.mask(flagged, 0.0)


def side_attribution(
    targets: pd.DataFrame,
    future: pd.DataFrame,
    blv: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    rows = (targets.index >= start) & (targets.index <= end)
    regime = blv.reindex(targets.index).fillna(False)
    out = {}
    for side, mask in {
        "long": targets.gt(EPS),
        "short": targets.lt(-EPS),
    }.items():
        eligible = mask.mul(regime, axis=0).loc[rows]
        vals = future.loc[rows].where(eligible).stack().dropna().to_numpy(dtype=float)
        out[side] = {
            "asset_hours": int(eligible.to_numpy().sum()),
            "mean_future_net_pnl": float(vals.mean()) if len(vals) else 0.0,
            "mean_without_bottom1pct": trim_bottom(vals, 0.01),
            "positive_rate": float((vals > 0.0).mean()) if len(vals) else 0.0,
            "net_future_pnl_sum": float(vals.sum()) if len(vals) else 0.0,
        }
    return out


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_cost = severe_cost * 1.5
    direction, vol, _ = audit.classify_regimes(data.close)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, common_end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    enable_short_veto, phase7_diag = p12.choose_short_veto(
        data, raw, ex, guard, gross, direction, vol, base_cost
    )
    f7_targets, f7_base, _, r98_diag, _ = p12.build_f7_core(
        data, raw, ex, guard, gross, base_cost, enable_short_veto
    )

    blv = blv_mask(f7_targets.index, direction, vol)
    pnl = net_asset_pnl(f7_base)
    future = forward_sum_frame(pnl, HORIZON)
    eligible = f7_targets.abs().gt(EPS).mul(blv.reindex(f7_targets.index).fillna(False), axis=0)
    rules = build_rules(f7_targets, data.close)

    train_diag = {
        name: eval_harm(rule, eligible, future, common_start, train_end)
        for name, rule in rules.items()
    }
    candidates = [
        (name, row)
        for name, row in train_diag.items()
        if row["selected_asset_hours"] >= MIN_SELECTED
        and MIN_COVERAGE <= row["coverage"] <= MAX_COVERAGE
        and row["mean_without_bottom1pct"] < 0.0
        and row["mean_delta_vs_blv_active"] < 0.0
        and row["positive_rate_delta"] <= 0.0
    ]
    candidates.sort(
        key=lambda item: (
            item[1]["mean_without_bottom1pct"],
            item[1]["mean_delta_vs_blv_active"],
            item[1]["positive_rate_delta"],
        )
    )
    selected = candidates[0][0] if candidates else None

    fold_diag = {}
    selected_good_folds = 0
    selected_valid_folds = 0
    for i, (lo, hi) in enumerate(p12.fold_bounds(f7_targets.index, common_start, train_end), 1):
        rows = {
            name: eval_harm(rule, eligible, future, lo, hi)
            for name, rule in rules.items()
        }
        fold_diag[str(i)] = {
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "rules": rows,
        }
        if selected:
            sr = rows[selected]
            if sr["selected_asset_hours"] >= MIN_FOLD_SELECTED:
                selected_valid_folds += 1
                selected_good_folds += int(diagnostic_good(sr))

    hold_diag = {
        name: eval_harm(rule, eligible, future, hold_start, common_end)
        for name, rule in rules.items()
    }
    selected_train = train_diag.get(selected, {}) if selected else {}
    selected_hold = hold_diag.get(selected, {}) if selected else {}

    diagnostic_train_pass = bool(
        selected
        and selected_train.get("selected_asset_hours", 0) >= MIN_SELECTED
        and diagnostic_good(selected_train)
        and selected_valid_folds >= 3
        and selected_good_folds >= 3
    )
    diagnostic_holdout_pass = bool(selected and diagnostic_good(selected_hold))

    candidate_targets = apply_rule_veto(f7_targets, selected if diagnostic_train_pass else None, data.close, blv)
    candidate_base = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)

    def analyze_pair(base_res, candidate_res):
        return {
            "f7": audit.analyze_result(base_res, data, direction, vol, common_start, common_end),
            "candidate": audit.analyze_result(candidate_res, data, direction, vol, common_start, common_end),
            "f7_holdout": audit.analyze_result(base_res, data, direction, vol, hold_start, common_end),
            "candidate_holdout": audit.analyze_result(candidate_res, data, direction, vol, hold_start, common_end),
        }

    base = analyze_pair(f7_base, candidate_base)
    train_f7 = audit.analyze_result(f7_base, data, direction, vol, common_start, train_end)
    train_candidate = audit.analyze_result(candidate_base, data, direction, vol, common_start, train_end)
    train_delta = p12.delta(train_candidate, train_f7)

    candidate_fold_rows = []
    for i, (lo, hi) in enumerate(p12.fold_bounds(f7_targets.index, common_start, train_end), 1):
        fb = audit.analyze_result(f7_base, data, direction, vol, lo, hi)
        cb = audit.analyze_result(candidate_base, data, direction, vol, lo, hi)
        d = p12.delta(cb, fb)
        candidate_fold_rows.append({
            "fold": i,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "delta": d,
            "strict_pareto": p12.strict_pareto(d),
        })
    pareto_train_folds = sum(int(row["strict_pareto"]) for row in candidate_fold_rows)

    f7_sev_targets, f7_sev, _, _, _ = p12.build_f7_core(
        data, raw, ex, guard, gross, severe_cost, enable_short_veto
    )
    cand_sev_targets = apply_rule_veto(
        f7_sev_targets,
        selected if diagnostic_train_pass else None,
        data.close,
        blv,
    )
    cand_sev = p1.run_targets(data, cand_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = analyze_pair(f7_sev, cand_sev)

    f7_super_targets, f7_super, _, _, _ = p12.build_f7_core(
        data, raw, ex, guard, gross, super_cost, enable_short_veto
    )
    cand_super_targets = apply_rule_veto(
        f7_super_targets,
        selected if diagnostic_train_pass else None,
        data.close,
        blv,
    )
    cand_super = p1.run_targets(data, cand_super_targets, ex, guard, super_cost, p1.GROSS_CAP)
    super_severe = analyze_pair(f7_super, cand_super)

    hold_delta = p12.delta(base["candidate_holdout"], base["f7_holdout"])
    severe_delta = p12.delta(severe["candidate"], severe["f7"])
    severe_hold_delta = p12.delta(severe["candidate_holdout"], severe["f7_holdout"])
    super_delta = p12.delta(super_severe["candidate"], super_severe["f7"])
    super_hold_delta = p12.delta(super_severe["candidate_holdout"], super_severe["f7_holdout"])

    bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    bench = {
        name: audit.analyze_result(result, benchmarks[name]["data"], direction, vol, common_start, common_end)
        for name, result in bench_results.items()
    }
    envelope = audit.metric_envelope({name: row["global"] for name, row in bench.items()})
    envelope_cmp = audit.candidate_vs_envelope(base["candidate"]["global"], envelope)

    accepted = bool(
        diagnostic_train_pass
        and diagnostic_holdout_pass
        and p12.strict_pareto(train_delta)
        and pareto_train_folds >= 3
        and p12.strict_pareto(hold_delta)
        and p12.strict_pareto(severe_delta)
        and p12.strict_pareto(severe_hold_delta)
        and p12.strict_pareto(super_delta)
        and p12.strict_pareto(super_hold_delta)
    )

    blv_base = {
        "f7": base["f7"]["regimes"]["matrix"]["BULL__LOW_VOLATILITY"],
        "candidate": base["candidate"]["regimes"]["matrix"]["BULL__LOW_VOLATILITY"],
        "f7_holdout": base["f7_holdout"]["regimes"]["matrix"]["BULL__LOW_VOLATILITY"],
        "candidate_holdout": base["candidate_holdout"]["regimes"]["matrix"]["BULL__LOW_VOLATILITY"],
    }

    out = {
        "study": "V99 R106 phase 14 — causal BULL+LOW_VOL structural loss gate on F7 core",
        "status": "PROMOTABLE_RESEARCH_CANDIDATE" if accepted else "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "repair F7 BULL+LOW_VOL drawdown without sacrificing return quality",
            "future_horizon_hours": HORIZON,
            "market_features_shifted_t_minus_1": True,
            "candidate_rules": list(rules),
            "no_numeric_threshold_grid": True,
            "selection_uses_train_only": True,
            "train_rule_eligibility": {
                "minimum_selected_asset_hours": MIN_SELECTED,
                "coverage_min": MIN_COVERAGE,
                "coverage_max": MAX_COVERAGE,
                "robust_harm": "mean remains negative after removing worst 1% outcomes",
            },
            "fold_gate": ">=3 valid chronological train folds and >=3 confirm robust harm",
            "candidate_action": "veto only the train-selected harmful asset-hours inside causal BULL+LOW_VOL",
            "promotion_gate": "strict Pareto vs F7 on train, >=3/4 train folds, untouched holdout, severe, severe holdout, supersevere and supersevere holdout",
            "holdout_used_for_selection": False,
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "phase7_short_veto_enabled": enable_short_veto,
        "phase7_side_train": phase7_diag,
        "blv_side_attribution": {
            "train": side_attribution(f7_targets, future, blv, common_start, train_end),
            "holdout": side_attribution(f7_targets, future, blv, hold_start, common_end),
        },
        "rule_diagnostics": {
            "train": train_diag,
            "folds": fold_diag,
            "holdout": hold_diag,
            "selected_rule": selected,
            "selected_valid_folds": selected_valid_folds,
            "selected_good_folds": selected_good_folds,
            "diagnostic_train_pass": diagnostic_train_pass,
            "diagnostic_holdout_pass": diagnostic_holdout_pass,
        },
        "base": base,
        "bull_low_vol": blv_base,
        "train_delta": train_delta,
        "candidate_train_folds": candidate_fold_rows,
        "pareto_train_folds": pareto_train_folds,
        "holdout_delta": hold_delta,
        "severe": severe,
        "severe_delta": severe_delta,
        "severe_holdout_delta": severe_hold_delta,
        "super_severe": super_severe,
        "super_severe_delta": super_delta,
        "super_severe_holdout_delta": super_hold_delta,
        "vs_v13_v16_metric_envelope": envelope_cmp,
        "pass_count": {
            "passed": sum(int(v["passed"]) for v in envelope_cmp.values()),
            "total": len(envelope_cmp),
        },
        "research_gate": {
            "accepted": accepted,
            "reason": "no promotion unless the same frozen structural rule survives train folds, untouched holdout and both stress-cost tiers",
        },
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research and chronological holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")

    print(json.dumps({
        "selected_rule": selected,
        "diagnostic_train_pass": diagnostic_train_pass,
        "diagnostic_holdout_pass": diagnostic_holdout_pass,
        "selected_valid_folds": selected_valid_folds,
        "selected_good_folds": selected_good_folds,
        "blv_side_attribution": out["blv_side_attribution"],
        "research_gate": out["research_gate"],
        "pareto_train_folds": pareto_train_folds,
        "base": {name: p12.compact(row) for name, row in base.items()},
        "bull_low_vol": blv_base,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "severe_delta": severe_delta,
        "severe_holdout_delta": severe_hold_delta,
        "super_severe_delta": super_delta,
        "super_severe_holdout_delta": super_hold_delta,
        "pass_count": out["pass_count"],
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
