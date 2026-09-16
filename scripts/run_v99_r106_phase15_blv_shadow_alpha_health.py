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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase15_blv_shadow_alpha_health.json"
EPS = 1e-12
FUTURE_HOURS = 6
RISK_SCALE = 0.50
MIN_SELECTED_HOURS = 100
MIN_FOLD_HOURS = 20
MIN_COVERAGE = 0.05
MAX_COVERAGE = 0.50


def blv_mask(index: pd.DatetimeIndex, direction: pd.Series, vol: pd.Series) -> pd.Series:
    d = direction.shift(1).reindex(index)
    v = vol.shift(1).reindex(index)
    return (d.eq("BULL") & v.eq("LOW_VOLATILITY")).fillna(False)


def shadow_alpha_hourly(targets: pd.DataFrame, data, cost: float) -> pd.Series:
    """Causal fixed-alpha health proxy independent of any later risk scaling.

    It approximates the unscaled F7 stream using only information available by
    the close of each hour. Target t is decided at close t and executes later,
    so health observed through t may causally scale target t.
    """
    close = data.close.reindex(index=targets.index, columns=targets.columns).astype(float)
    opened = data.frames["open"].reindex(index=targets.index, columns=targets.columns).astype(float)
    funding = data.funding.reindex(index=targets.index, columns=targets.columns).fillna(0.0)

    at_open = targets.shift(1).fillna(0.0)
    overnight_pos = targets.shift(2).fillna(0.0)
    overnight_move = opened.div(close.shift(1)).sub(1.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    intraday_move = close.div(opened).sub(1.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    gross = (overnight_pos * overnight_move).sum(axis=1) + (at_open * intraday_move).sum(axis=1)
    turnover = at_open.sub(overnight_pos).abs().sum(axis=1)
    fees = turnover * float(cost)
    funding_cost = (overnight_pos * funding).sum(axis=1)
    return (gross - fees - funding_cost).fillna(0.0)


def future_compounded(hourly: pd.Series, hours: int) -> pd.Series:
    factors = pd.DataFrame(
        {k: (1.0 + hourly.shift(-k).clip(lower=-0.999999)) for k in range(1, hours + 1)}
    )
    return factors.prod(axis=1, min_count=hours) - 1.0


def rolling_q75(series: pd.Series, hours: int = 24 * 90) -> pd.Series:
    return series.shift(1).rolling(hours, min_periods=24 * 30).quantile(0.75)


def health_rules(targets: pd.DataFrame, data, cost: float) -> tuple[dict[str, pd.Series], dict]:
    health = shadow_alpha_hourly(targets, data, cost)
    h6 = health.rolling(6, min_periods=6).sum()
    h24 = health.rolling(24, min_periods=18).sum()

    gross = targets.abs().sum(axis=1)
    concentration = targets.abs().max(axis=1).div(gross.replace(0.0, np.nan)).fillna(0.0)
    turnover = targets.sub(targets.shift(1).fillna(0.0)).abs().sum(axis=1)
    net_ratio = targets.sum(axis=1).div(gross.replace(0.0, np.nan)).fillna(0.0)

    concentration_high = concentration > rolling_q75(concentration)
    turnover_high = turnover > rolling_q75(turnover)
    h6_neg = h6 < 0.0
    h24_neg = h24 < 0.0

    rules = {
        "shadow6_negative": h6_neg,
        "shadow24_negative": h24_neg,
        "shadow6_and_24_negative": h6_neg & h24_neg,
        "shadow6_negative_concentration_high": h6_neg & concentration_high,
        "shadow6_negative_turnover_high": h6_neg & turnover_high,
        "shadow6_negative_net_short": h6_neg & (net_ratio < 0.0),
        "shadow6_negative_concentration_or_turnover_high": h6_neg & (concentration_high | turnover_high),
    }
    diag = {
        "shadow_health_mean": float(health.mean()),
        "shadow_health_std": float(health.std(ddof=0)),
        "concentration_mean": float(concentration.mean()),
        "concentration_q75_mean": float(rolling_q75(concentration).dropna().mean()),
        "turnover_mean": float(turnover.mean()),
        "turnover_q75_mean": float(rolling_q75(turnover).dropna().mean()),
        "net_ratio_mean": float(net_ratio.mean()),
    }
    return rules, diag


def trim_bottom(values: np.ndarray, q: float = 0.01) -> float:
    values = values[np.isfinite(values)]
    if not len(values):
        return 0.0
    cutoff = np.quantile(values, q)
    kept = values[values >= cutoff]
    return float(kept.mean()) if len(kept) else 0.0


def evaluate_rule(
    rule: pd.Series,
    eligible: pd.Series,
    future: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    idx = eligible.index
    window = (idx >= start) & (idx <= end)
    e = eligible.loc[window].fillna(False)
    r = rule.reindex(idx).loc[window].fillna(False) & e
    f = future.reindex(idx).loc[window]
    selected = f[r].dropna().to_numpy(dtype=float)
    base = f[e].dropna().to_numpy(dtype=float)

    def q10(x: np.ndarray) -> float:
        return float(np.quantile(x, 0.10)) if len(x) else 0.0

    mean = float(selected.mean()) if len(selected) else 0.0
    base_mean = float(base.mean()) if len(base) else 0.0
    return {
        "eligible_hours": int(e.sum()),
        "selected_hours": int(r.sum()),
        "coverage": float(r.sum() / e.sum()) if int(e.sum()) else 0.0,
        "mean_future_return": mean,
        "robust_mean_without_bottom1pct": trim_bottom(selected),
        "q10_future_return": q10(selected),
        "positive_rate": float((selected > 0.0).mean()) if len(selected) else 0.0,
        "base_mean_future_return": base_mean,
        "base_robust_mean_without_bottom1pct": trim_bottom(base),
        "base_q10_future_return": q10(base),
        "base_positive_rate": float((base > 0.0).mean()) if len(base) else 0.0,
        "mean_delta": float(mean - base_mean),
        "q10_delta": float(q10(selected) - q10(base)),
    }


def harmful(row: dict, min_hours: int) -> bool:
    return bool(
        row.get("selected_hours", 0) >= min_hours
        and row.get("robust_mean_without_bottom1pct", 0.0) < 0.0
        and row.get("mean_delta", 0.0) < 0.0
        and row.get("q10_delta", 0.0) < 0.0
    )


def choose_rule(
    targets: pd.DataFrame,
    result,
    data,
    cost: float,
    direction: pd.Series,
    vol: pd.Series,
    start: pd.Timestamp,
    train_end: pd.Timestamp,
) -> tuple[str | None, dict]:
    rules, health_diag = health_rules(targets, data, cost)
    blv = blv_mask(targets.index, direction, vol)
    eligible = blv & targets.abs().sum(axis=1).gt(EPS)
    hourly = result.equity.pct_change(fill_method=None).fillna(0.0)
    future = future_compounded(hourly, FUTURE_HOURS)

    train = {
        name: evaluate_rule(rule, eligible, future, start, train_end)
        for name, rule in rules.items()
    }
    candidates = [
        (name, row)
        for name, row in train.items()
        if row["selected_hours"] >= MIN_SELECTED_HOURS
        and MIN_COVERAGE <= row["coverage"] <= MAX_COVERAGE
        and harmful(row, MIN_SELECTED_HOURS)
    ]
    candidates.sort(
        key=lambda item: (
            item[1]["robust_mean_without_bottom1pct"],
            item[1]["q10_delta"],
            item[1]["mean_delta"],
        )
    )
    selected = candidates[0][0] if candidates else None

    folds = []
    valid = good = 0
    for i, (lo, hi) in enumerate(p12.fold_bounds(targets.index, start, train_end), 1):
        rows = {name: evaluate_rule(rule, eligible, future, lo, hi) for name, rule in rules.items()}
        folds.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), "rules": rows})
        if selected:
            row = rows[selected]
            if row["selected_hours"] >= MIN_FOLD_HOURS:
                valid += 1
                good += int(harmful(row, MIN_FOLD_HOURS))

    passed = bool(selected and valid >= 3 and good >= 3)
    return selected, {
        "health": health_diag,
        "train": train,
        "folds": folds,
        "selected_rule": selected,
        "valid_folds": valid,
        "good_folds": good,
        "train_pass": passed,
    }


def apply_health_controller(
    targets: pd.DataFrame,
    data,
    cost: float,
    direction: pd.Series,
    vol: pd.Series,
    selected: str | None,
    enabled: bool,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    rules, diag = health_rules(targets, data, cost)
    blv = blv_mask(targets.index, direction, vol)
    flag = pd.Series(False, index=targets.index)
    if enabled and selected:
        flag = (rules[selected] & blv & targets.abs().sum(axis=1).gt(EPS)).fillna(False)
    out = targets.copy()
    out.loc[flag, :] = out.loc[flag, :] * RISK_SCALE
    return out, flag, {
        **diag,
        "risk_scale": RISK_SCALE,
        "flagged_hours": int(flag.sum()),
        "flagged_fraction": float(flag.mean()),
    }


def core_metrics(analysis: dict) -> dict:
    m = analysis["global"]
    return {
        "roi": float(m["roi"]),
        "max_drawdown_abs": float(m["max_drawdown_abs"]),
        "worst_day_abs": float(m["worst_day_abs"]),
        "profit_factor": float(m["profit_factor"]),
        "payoff_ratio": float(m["payoff_ratio"]),
        "trade_win_rate": float(m["trade_win_rate"]),
        "positive_day_ratio": float(m["positive_day_ratio"]),
    }


def core_delta(candidate: dict, base: dict) -> dict:
    c, b = core_metrics(candidate), core_metrics(base)
    return {
        "wealth_ratio": float((1.0 + c["roi"]) / max(1e-12, 1.0 + b["roi"])),
        "roi_delta": c["roi"] - b["roi"],
        "dd_delta": c["max_drawdown_abs"] - b["max_drawdown_abs"],
        "worst_day_delta": c["worst_day_abs"] - b["worst_day_abs"],
        "pf_delta": c["profit_factor"] - b["profit_factor"],
        "payoff_delta": c["payoff_ratio"] - b["payoff_ratio"],
        "win_rate_delta": c["trade_win_rate"] - b["trade_win_rate"],
        "positive_days_delta": c["positive_day_ratio"] - b["positive_day_ratio"],
    }


def core_pareto(delta: dict) -> bool:
    return bool(
        delta["wealth_ratio"] > 1.0
        and delta["dd_delta"] <= 1e-12
        and delta["worst_day_delta"] <= 1e-12
        and delta["pf_delta"] >= -1e-12
    )


def analyze(result, data, direction, vol, start, end):
    return audit.analyze_result(result, data, direction, vol, start, end)


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

    selected, selection = choose_rule(
        f7_targets, f7_base, data, base_cost, direction, vol, common_start, train_end
    )
    candidate_targets, base_flags, controller_diag = apply_health_controller(
        f7_targets, data, base_cost, direction, vol, selected, selection["train_pass"]
    )
    candidate_base = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)

    hold_rules, _ = health_rules(f7_targets, data, base_cost)
    blv = blv_mask(f7_targets.index, direction, vol)
    eligible = blv & f7_targets.abs().sum(axis=1).gt(EPS)
    future = future_compounded(f7_base.equity.pct_change(fill_method=None).fillna(0.0), FUTURE_HOURS)
    hold_diag = (
        evaluate_rule(hold_rules[selected], eligible, future, hold_start, common_end)
        if selected else {}
    )
    holdout_rule_pass = bool(selected and harmful(hold_diag, MIN_FOLD_HOURS))

    f7_train = analyze(f7_base, data, direction, vol, common_start, train_end)
    cand_train = analyze(candidate_base, data, direction, vol, common_start, train_end)
    f7_hold = analyze(f7_base, data, direction, vol, hold_start, common_end)
    cand_hold = analyze(candidate_base, data, direction, vol, hold_start, common_end)
    f7_all = analyze(f7_base, data, direction, vol, common_start, common_end)
    cand_all = analyze(candidate_base, data, direction, vol, common_start, common_end)

    train_delta = core_delta(cand_train, f7_train)
    hold_delta = core_delta(cand_hold, f7_hold)
    global_delta = core_delta(cand_all, f7_all)

    fold_rows = []
    pareto_folds = 0
    for i, (lo, hi) in enumerate(p12.fold_bounds(f7_targets.index, common_start, train_end), 1):
        b = analyze(f7_base, data, direction, vol, lo, hi)
        c = analyze(candidate_base, data, direction, vol, lo, hi)
        d = core_delta(c, b)
        passed = core_pareto(d)
        pareto_folds += int(passed)
        fold_rows.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), "delta": d, "strict_pareto": passed})

    stress = {}
    stress_pass = True
    for name, cost in (("severe", severe_cost), ("supersevere", super_cost)):
        f7_t, f7_r, _, _, _ = p12.build_f7_core(data, raw, ex, guard, gross, cost, enable_short_veto)
        cand_t, flags, diag = apply_health_controller(
            f7_t, data, cost, direction, vol, selected, selection["train_pass"]
        )
        cand_r = p1.run_targets(data, cand_t, ex, guard, cost, p1.GROSS_CAP)
        b_all = analyze(f7_r, data, direction, vol, common_start, common_end)
        c_all = analyze(cand_r, data, direction, vol, common_start, common_end)
        b_hold = analyze(f7_r, data, direction, vol, hold_start, common_end)
        c_hold = analyze(cand_r, data, direction, vol, hold_start, common_end)
        d_all = core_delta(c_all, b_all)
        d_hold = core_delta(c_hold, b_hold)
        pass_all = core_pareto(d_all)
        pass_hold = core_pareto(d_hold)
        stress_pass = stress_pass and pass_all and pass_hold
        stress[name] = {
            "controller": diag,
            "flagged_hours": int(flags.sum()),
            "f7": b_all,
            "candidate": c_all,
            "f7_holdout": b_hold,
            "candidate_holdout": c_hold,
            "delta": d_all,
            "holdout_delta": d_hold,
            "strict_pareto": pass_all,
            "holdout_strict_pareto": pass_hold,
        }

    blv_base = f7_all["regimes"]["matrix"]["BULL__LOW_VOLATILITY"]
    blv_candidate = cand_all["regimes"]["matrix"]["BULL__LOW_VOLATILITY"]
    blv_hold_base = f7_hold["regimes"]["matrix"]["BULL__LOW_VOLATILITY"]
    blv_hold_candidate = cand_hold["regimes"]["matrix"]["BULL__LOW_VOLATILITY"]

    bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    bench = {
        name: analyze(result, benchmarks[name]["data"], direction, vol, common_start, common_end)
        for name, result in bench_results.items()
    }
    envelope = audit.metric_envelope({name: row["global"] for name, row in bench.items()})
    envelope_cmp = audit.candidate_vs_envelope(cand_all["global"], envelope)

    accepted = bool(
        selection["train_pass"]
        and holdout_rule_pass
        and core_pareto(train_delta)
        and pareto_folds >= 3
        and core_pareto(hold_delta)
        and core_pareto(global_delta)
        and stress_pass
    )

    out = {
        "study": "V99 R106 phase 15 — causal BULL+LOW_VOL shadow-alpha health controller",
        "status": "PROMOTABLE_RESEARCH_CANDIDATE" if accepted else "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "reduce BULL+LOW_VOL tail drawdown by reacting to deterioration in the raw F7 alpha rather than market regime alone",
            "future_validation_horizon_hours": FUTURE_HOURS,
            "risk_scale": RISK_SCALE,
            "candidate_rules": list(health_rules(f7_targets, data, base_cost)[0]),
            "selection_uses_train_only": True,
            "holdout_used_for_selection": False,
            "causal_shadow_health": True,
            "adaptive_concentration_and_turnover_thresholds": "rolling 90d q75 shifted one hour; no holdout fit",
            "no_numeric_threshold_grid": True,
            "action": "scale the complete F7 target to 50% only on selected adverse BLV hours",
            "promotion_gate": "rule stable in >=3 train folds plus strict ROI/DD/worst-day/PF Pareto on train, >=3 train folds, holdout, global, severe and supersevere including holdouts",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "phase7_short_veto_enabled": enable_short_veto,
        "phase7_side_train": phase7_diag,
        "selection": selection,
        "holdout_rule_validation": hold_diag,
        "holdout_rule_pass": holdout_rule_pass,
        "controller": controller_diag,
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
        "bull_low_vol": {
            "f7": blv_base,
            "candidate": blv_candidate,
            "f7_holdout": blv_hold_base,
            "candidate_holdout": blv_hold_candidate,
        },
        "stress": stress,
        "vs_v13_v16_metric_envelope": envelope_cmp,
        "pass_count": {
            "passed": sum(int(v["passed"]) for v in envelope_cmp.values()),
            "total": len(envelope_cmp),
        },
        "research_gate": {
            "accepted": accepted,
            "reason": "no promotion unless raw-alpha adversity is stable across train folds and the fixed controller improves F7 under untouched holdout and both stress tiers",
        },
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research and chronological holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")

    print(json.dumps({
        "selected_rule": selected,
        "selection_train_pass": selection["train_pass"],
        "selection_valid_folds": selection["valid_folds"],
        "selection_good_folds": selection["good_folds"],
        "holdout_rule_pass": holdout_rule_pass,
        "controller": controller_diag,
        "research_gate": out["research_gate"],
        "pareto_train_folds": pareto_folds,
        "f7": p12.compact(f7_all),
        "candidate": p12.compact(cand_all),
        "f7_holdout": p12.compact(f7_hold),
        "candidate_holdout": p12.compact(cand_hold),
        "global_delta": global_delta,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "bull_low_vol": out["bull_low_vol"],
        "stress": {
            k: {
                "delta": v["delta"],
                "holdout_delta": v["holdout_delta"],
                "strict_pareto": v["strict_pareto"],
                "holdout_strict_pareto": v["holdout_strict_pareto"],
            }
            for k, v in stress.items()
        },
        "pass_count": out["pass_count"],
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
