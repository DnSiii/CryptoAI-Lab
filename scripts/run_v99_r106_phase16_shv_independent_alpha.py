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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase16_shv_independent_alpha.json"
EPS = 1e-12
ALPHA_GROSS = 0.30
TOP_N = 2
REBALANCE_HOURS = 6
VOL_LOOKBACK = 168
MIN_TRAIN_ACTIVE_HOURS = 24 * 10
MIN_FOLD_ACTIVE_HOURS = 24 * 3
MIN_HOLDOUT_ACTIVE_HOURS = 24 * 3


def shv_mask(index: pd.DatetimeIndex, direction: pd.Series, vol: pd.Series) -> pd.Series:
    """Causal SIDEWAYS+HIGH_VOL state known before a target is emitted."""
    d = direction.shift(1).reindex(index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(index).fillna("UNKNOWN")
    return (d.eq("SIDEWAYS") & v.eq("HIGH_VOLATILITY")).fillna(False)


def rebalance_and_hold(targets: pd.DataFrame, every: int = REBALANCE_HOURS) -> pd.DataFrame:
    event = pd.Series(np.arange(len(targets)) % int(every) == 0, index=targets.index)
    return targets.where(event, np.nan).ffill().fillna(0.0)


def market_neutral_inverse_vol(signals: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    hourly = close.pct_change(fill_method=None)
    vol = hourly.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK // 2).std().replace(0.0, np.nan)
    inv = 1.0 / vol
    longs = signals.clip(lower=0.0) * inv
    shorts = (-signals.clip(upper=0.0)) * inv
    long_sum = longs.sum(axis=1).replace(0.0, np.nan)
    short_sum = shorts.sum(axis=1).replace(0.0, np.nan)
    long_target = longs.div(long_sum, axis=0).fillna(0.0) * (ALPHA_GROSS / 2.0)
    short_target = shorts.div(short_sum, axis=0).fillna(0.0) * (ALPHA_GROSS / 2.0)
    return long_target - short_target


def rank_reversal(score: pd.DataFrame) -> pd.DataFrame:
    valid = score.notna()
    long_rank = score.rank(axis=1, ascending=True, method="first")
    short_rank = score.rank(axis=1, ascending=False, method="first")
    long_sig = valid & long_rank.le(TOP_N)
    short_sig = valid & short_rank.le(TOP_N)
    return long_sig.astype(float) - short_sig.astype(float)


def fixed_shv_sleeves(data, direction: pd.Series, vol_state: pd.Series) -> dict[str, pd.DataFrame]:
    """Four predeclared, economically distinct relative-value alpha families.

    There is intentionally no threshold/lookback grid. All scores use information
    observable at the target close; exact replay executes the target later.
    """
    close = data.close.astype(float)
    hourly = close.pct_change(fill_method=None)

    # 1) Very short cross-sectional reversal around the market median.
    r6 = close.pct_change(6, fill_method=None)
    xs6 = r6.sub(r6.median(axis=1), axis=0)

    # 2) 24h reversal after stripping a causal rolling BTC beta component.
    btc_h = hourly["BTCUSDT"]
    mean_asset = hourly.rolling(168, min_periods=96).mean()
    mean_btc = btc_h.rolling(168, min_periods=96).mean()
    cross = hourly.mul(btc_h, axis=0).rolling(168, min_periods=96).mean()
    cov = cross - mean_asset.mul(mean_btc, axis=0)
    var_btc = btc_h.pow(2).rolling(168, min_periods=96).mean() - mean_btc.pow(2)
    beta = cov.div(var_btc.replace(0.0, np.nan), axis=0).clip(lower=-3.0, upper=3.0)
    r24 = close.pct_change(24, fill_method=None)
    btc24 = close["BTCUSDT"].pct_change(24, fill_method=None)
    residual24 = r24 - beta.mul(btc24, axis=0)

    # 3) Fade assets sitting at opposite extremes of their own recent range.
    lo48 = close.rolling(48, min_periods=36).min()
    hi48 = close.rolling(48, min_periods=36).max()
    range_position = close.sub(lo48).div(hi48.sub(lo48).replace(0.0, np.nan)) - 0.5

    # 4) Cross-sectional reversal normalized by each asset's recent realized vol.
    sigma = hourly.rolling(168, min_periods=96).std().replace(0.0, np.nan)
    r12 = close.pct_change(12, fill_method=None)
    volnorm12 = r12.div(sigma * np.sqrt(12.0))

    scores = {
        "xs_reversal_6h": xs6,
        "btc_residual_reversal_24h": residual24,
        "range_position_fade_48h": range_position,
        "vol_normalized_reversal_12h": volnorm12,
    }
    regime = shv_mask(close.index, direction, vol_state)
    out: dict[str, pd.DataFrame] = {}
    for name, score in scores.items():
        signals = rank_reversal(score)
        target = market_neutral_inverse_vol(signals, close)
        target = rebalance_and_hold(target)
        target = target.where(regime, 0.0)
        out[name] = p1.cap(target, ALPHA_GROSS)
    return out


def robust_mean_without_top1pct(equity: pd.Series, active: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    r = equity.pct_change(fill_method=None).fillna(0.0)
    use = active.reindex(r.index).fillna(False) & r.index.to_series().between(start, end).to_numpy()
    values = r.loc[use].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return 0.0
    cutoff = np.quantile(values, 0.99)
    kept = values[values <= cutoff]
    return float(kept.mean()) if len(kept) else 0.0


def sleeve_row(result, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    active = result.gross_exposure.gt(EPS)
    m = p4.segment_metrics(result.equity, active, start, end)
    m["robust_mean_without_top1pct"] = robust_mean_without_top1pct(result.equity, active, start, end)
    return m


def select_train_sleeve(results: dict[str, object], index: pd.DatetimeIndex, train_start: pd.Timestamp, train_end: pd.Timestamp) -> tuple[str | None, dict]:
    folds = p4.fold_bounds(index, train_start, train_end)
    rows: dict[str, dict] = {}
    eligible_names: list[str] = []
    for name, result in results.items():
        train = sleeve_row(result, train_start, train_end)
        fold_rows = []
        valid = good = 0
        for i, (lo, hi) in enumerate(folds, 1):
            fm = sleeve_row(result, lo, hi)
            fold_rows.append({"fold": i, "start": lo.isoformat(), "end": hi.isoformat(), **fm})
            if int(fm["active_hours"]) >= MIN_FOLD_ACTIVE_HOURS:
                valid += 1
                good += int(
                    float(fm["roi"]) > 0.0
                    and float(fm["profit_factor"]) > 1.0
                    and float(fm["robust_mean_without_top1pct"]) > 0.0
                )
        eligible = bool(
            int(train["active_hours"]) >= MIN_TRAIN_ACTIVE_HOURS
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
        rows[name] = {
            "eligible": eligible,
            "quality_score": float(quality),
            "train": train,
            "valid_folds": int(valid),
            "good_folds": int(good),
            "folds": fold_rows,
        }
        if eligible:
            eligible_names.append(name)

    selected = max(eligible_names, key=lambda n: rows[n]["quality_score"]) if eligible_names else None
    return selected, {
        "candidates": rows,
        "selected_sleeve": selected,
        "train_pass": bool(selected),
        "selection_uses_train_only": True,
    }


def combine(f7_targets: pd.DataFrame, alpha: pd.DataFrame | None, enabled: bool) -> tuple[pd.DataFrame, dict]:
    if not enabled or alpha is None:
        return f7_targets.copy(), {"enabled": False, "raw_clip_fraction": 0.0, "alpha_gross": ALPHA_GROSS}
    raw = f7_targets.add(alpha, fill_value=0.0)
    raw_gross = raw.abs().sum(axis=1)
    out = p1.cap(raw, p1.GROSS_CAP)
    return out, {
        "enabled": True,
        "alpha_gross": ALPHA_GROSS,
        "raw_clip_fraction": float(raw_gross.gt(p1.GROSS_CAP + EPS).mean()),
        "mean_alpha_requested_gross": float(alpha.abs().sum(axis=1).mean()),
    }


def analyze(result, data, direction, vol_state, start, end):
    return audit.analyze_result(result, data, direction, vol_state, start, end)


def holdout_alpha_pass(result, hold_start: pd.Timestamp, hold_end: pd.Timestamp) -> tuple[bool, dict]:
    row = sleeve_row(result, hold_start, hold_end)
    passed = bool(
        int(row["active_hours"]) >= MIN_HOLDOUT_ACTIVE_HOURS
        and float(row["roi"]) > 0.0
        and float(row["profit_factor"]) > 1.05
        and float(row["robust_mean_without_top1pct"]) > 0.0
    )
    return passed, row


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

    enable_short_veto, phase7_diag = p12.choose_short_veto(
        data, raw, ex, guard, gross, direction, vol_state, base_cost
    )
    f7_targets, f7_base, _, r98_diag, _ = p12.build_f7_core(
        data, raw, ex, guard, gross, base_cost, enable_short_veto
    )

    sleeves = fixed_shv_sleeves(data, direction, vol_state)
    sleeve_results = {
        name: p1.run_targets(data, target, ex, guard, base_cost, p1.GROSS_CAP)
        for name, target in sleeves.items()
    }
    selected, selection = select_train_sleeve(sleeve_results, data.close.index, common_start, train_end)
    selected_result = sleeve_results[selected] if selected else None
    holdout_pass, holdout_diag = (
        holdout_alpha_pass(selected_result, hold_start, common_end)
        if selected_result is not None else (False, {})
    )

    candidate_targets, combine_diag = combine(
        f7_targets,
        sleeves[selected] if selected else None,
        enabled=bool(selection["train_pass"]),
    )
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

    fold_rows = []
    pareto_folds = 0
    nonharm_folds = 0
    for i, (lo, hi) in enumerate(p4.fold_bounds(data.close.index, common_start, train_end), 1):
        b = analyze(f7_base, data, direction, vol_state, lo, hi)
        c = analyze(candidate_base, data, direction, vol_state, lo, hi)
        d = p15.core_delta(c, b)
        strict = p15.core_pareto(d)
        nonharm = bool(
            d["wealth_ratio"] >= 0.995
            and d["dd_delta"] <= 0.01
            and d["pf_delta"] >= -0.03
        )
        pareto_folds += int(strict)
        nonharm_folds += int(nonharm)
        fold_rows.append({
            "fold": i,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "delta": d,
            "strict_pareto": strict,
            "nonharm": nonharm,
        })

    stress = {}
    stress_pass = True
    for name, cost in (("severe", severe_cost), ("supersevere", super_cost)):
        f7_t, f7_r, _, _, _ = p12.build_f7_core(
            data, raw, ex, guard, gross, cost, enable_short_veto
        )
        cand_t, cdiag = combine(
            f7_t,
            sleeves[selected] if selected else None,
            enabled=bool(selection["train_pass"]),
        )
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
            "combine": cdiag,
            "f7": b_all,
            "candidate": c_all,
            "f7_holdout": b_hold,
            "candidate_holdout": c_hold,
            "delta": d_all,
            "holdout_delta": d_hold,
            "strict_pareto": pass_all,
            "holdout_strict_pareto": pass_hold,
        }

    shv_base = f7_all["regimes"]["matrix"]["SIDEWAYS__HIGH_VOLATILITY"]
    shv_candidate = cand_all["regimes"]["matrix"]["SIDEWAYS__HIGH_VOLATILITY"]
    shv_hold_base = f7_hold["regimes"]["matrix"]["SIDEWAYS__HIGH_VOLATILITY"]
    shv_hold_candidate = cand_hold["regimes"]["matrix"]["SIDEWAYS__HIGH_VOLATILITY"]

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
        and holdout_pass
        and p15.core_pareto(train_delta)
        and nonharm_folds >= 3
        and p15.core_pareto(hold_delta)
        and p15.core_pareto(global_delta)
        and stress_pass
    )

    out = {
        "study": "V99 R106 phase 16 — independent SIDEWAYS+HIGH_VOL relative-value alpha",
        "status": "PROMOTABLE_RESEARCH_CANDIDATE" if accepted else "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "add independent market-neutral alpha in the weakest F7 SIDEWAYS+HIGH_VOL cell rather than reducing the existing core",
            "candidate_sleeves": list(sleeves),
            "fixed_alpha_gross": ALPHA_GROSS,
            "top_n_each_side": TOP_N,
            "rebalance_hours": REBALANCE_HOURS,
            "selection_uses_train_only": True,
            "holdout_used_for_selection": False,
            "regime_features_shifted_t_minus_1": True,
            "no_numeric_threshold_grid": True,
            "tail_robustness": "selected alpha must keep positive mean after removing its top 1% hourly winners",
            "fold_gate": ">=3 valid train folds and >=3 positive/PF>1/tail-robust folds",
            "holdout_gate": "only the train-selected sleeve is validated; no second-choice rescue",
            "promotion_gate": "selected alpha survives holdout and combined F7 improves ROI/DD/worst-day/PF Pareto on train, holdout, full path and both severe tiers; >=3/4 train folds must be nonharmful",
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
        "selected_holdout": holdout_diag,
        "selected_holdout_pass": holdout_pass,
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
        "sideways_high_vol": {
            "f7": shv_base,
            "candidate": shv_candidate,
            "f7_holdout": shv_hold_base,
            "candidate_holdout": shv_hold_candidate,
        },
        "stress": stress,
        "vs_v13_v16_metric_envelope": envelope_cmp,
        "pass_count": {
            "passed": sum(int(v["passed"]) for v in envelope_cmp.values()),
            "total": len(envelope_cmp),
        },
        "research_gate": {
            "accepted": accepted,
            "reason": "no promotion unless an independent SHV alpha is train/fold/tail robust, validates untouched holdout, and improves the F7 core under normal and stressed exact replay",
        },
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research and chronological holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")

    print(json.dumps({
        "selected_sleeve": selected,
        "selection_train_pass": selection["train_pass"],
        "selected_holdout_pass": holdout_pass,
        "selected_holdout": holdout_diag,
        "research_gate": out["research_gate"],
        "pareto_train_folds": pareto_folds,
        "nonharm_train_folds": nonharm_folds,
        "f7": p12.compact(f7_all),
        "candidate": p12.compact(cand_all),
        "f7_holdout": p12.compact(f7_hold),
        "candidate_holdout": p12.compact(cand_hold),
        "global_delta": global_delta,
        "train_delta": train_delta,
        "holdout_delta": hold_delta,
        "sideways_high_vol": out["sideways_high_vol"],
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
