from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase8_position_aware_bhv_short_controller.json"
ALIGNMENT_HOURS = 12


def bhv_mask(index, direction, vol):
    d = direction.shift(1).reindex(index)
    v = vol.shift(1).reindex(index)
    return (d.eq("BEAR") & v.eq("HIGH_VOLATILITY")).fillna(False)


def split_short_alignment(targets: pd.DataFrame, close: pd.DataFrame, mask: pd.Series):
    # Target at close t executes at open t+1; trailing return through close t is causal.
    r12 = close.pct_change(ALIGNMENT_HOURS, fill_method=None).reindex(targets.index)
    short = targets.clip(upper=0.0)
    aligned = short.where(r12.le(0.0), 0.0).where(mask, 0.0)
    misaligned = short.where(r12.gt(0.0), 0.0).where(mask, 0.0)
    return aligned, misaligned, r12


def isolated(targets: pd.DataFrame, bhv: pd.Series):
    return targets.where(bhv, 0.0)


def controller_targets(targets: pd.DataFrame, aligned_short: pd.DataFrame, bhv: pd.Series):
    out = targets.copy()
    long = targets.clip(lower=0.0)
    out.loc[bhv, :] = long.loc[bhv, :].add(aligned_short.loc[bhv, :], fill_value=0.0)
    return out


def compact(a):
    m = a["global"]
    return {
        "roi_pct": 100 * float(m["roi"]),
        "max_dd_pct": -100 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100 * float(m["worst_day_abs"]),
        "win_rate_pct": 100 * float(m["trade_win_rate"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100 * float(m["avg_winning_trade"]),
        "avg_loss_pct": 100 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    bhv = bhv_mask(data.close.index, direction, vol)
    r98_targets, r98_result, r98_diag = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    aligned, misaligned, r12 = split_short_alignment(r98_targets, data.close, bhv)

    aligned_result = p1.run_targets(data, isolated(aligned, bhv), ex, guard, base_cost, p1.GROSS_CAP)
    misaligned_result = p1.run_targets(data, isolated(misaligned, bhv), ex, guard, base_cost, p1.GROSS_CAP)
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    aligned_train = audit.analyze_result(aligned_result, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    misaligned_train = audit.analyze_result(misaligned_result, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    enable = bool(
        float(aligned_train.get("roi", 0.0)) > 0.0
        and float(aligned_train.get("profit_factor", 0.0)) > 1.0
        and float(misaligned_train.get("roi", 0.0)) < 0.0
        and float(misaligned_train.get("profit_factor", 0.0)) < 1.0
    )

    candidate_targets = controller_targets(r98_targets, aligned, bhv) if enable else r98_targets.copy()
    candidate = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)
    common_start, common_end = data.close.index[0], data.close.index[-1]
    hold_idx = data.close.index[data.close.index > p1.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    base = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "candidate": audit.analyze_result(candidate, data, direction, vol, common_start, common_end),
        "aligned_short_only": audit.analyze_result(aligned_result, data, direction, vol, common_start, common_end),
        "misaligned_short_only": audit.analyze_result(misaligned_result, data, direction, vol, common_start, common_end),
    }
    hold = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end),
        "candidate": audit.analyze_result(candidate, data, direction, vol, hold_start, common_end),
    }

    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    aligned_sev, _, _ = split_short_alignment(r98_sev_targets, data.close, bhv)
    cand_sev_targets = controller_targets(r98_sev_targets, aligned_sev, bhv) if enable else r98_sev_targets.copy()
    cand_sev = p1.run_targets(data, cand_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = {
        "r98": audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end),
        "candidate": audit.analyze_result(cand_sev, data, direction, vol, common_start, common_end),
    }

    def delta(a, b):
        am, bm = a["global"], b["global"]
        return {
            "wealth_ratio": float((1 + am["roi"]) / max(1e-12, 1 + bm["roi"])),
            "dd_delta": float(am["max_drawdown_abs"] - bm["max_drawdown_abs"]),
            "worst_day_delta": float(am["worst_day_abs"] - bm["worst_day_abs"]),
            "pf_delta": float(am["profit_factor"] - bm["profit_factor"]),
            "win_rate_delta": float(am["trade_win_rate"] - bm["trade_win_rate"]),
            "positive_days_delta": float(am["positive_day_ratio"] - bm["positive_day_ratio"]),
        }

    bhv_metrics = {n: a["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"] for n, a in base.items()}
    out = {
        "study": "V99 R106 phase 8 — train-validated position-aware BEAR+HIGH_VOL short controller",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "train_rule": {
            "alignment_hours": ALIGNMENT_HOURS,
            "aligned_short_definition": "target<0 and trailing_12h_return<=0",
            "misaligned_short_definition": "target<0 and trailing_12h_return>0",
            "enable_controller": enable,
            "aligned_short_train_bhv": aligned_train,
            "misaligned_short_train_bhv": misaligned_train,
            "decision": "enable only if aligned shorts ROI>0/PF>1 AND misaligned shorts ROI<0/PF<1",
            "holdout_not_used_for_decision": True,
        },
        "exposure": {
            "bhv_fraction": float(bhv.mean()),
            "aligned_short_target_gross_fraction_of_bhv": float(aligned.abs().sum(axis=1).loc[bhv].mean()),
            "misaligned_short_target_gross_fraction_of_bhv": float(misaligned.abs().sum(axis=1).loc[bhv].mean()),
            "aligned_short_active_fraction_bhv": float(aligned.abs().sum(axis=1).loc[bhv].gt(1e-9).mean()),
            "misaligned_short_active_fraction_bhv": float(misaligned.abs().sum(axis=1).loc[bhv].gt(1e-9).mean()),
        },
        "base": base,
        "holdout": hold,
        "severe": severe,
        "bear_high_vol": bhv_metrics,
        "delta_vs_r98": {
            "base": delta(base["candidate"], base["r98"]),
            "holdout": delta(hold["candidate"], hold["r98"]),
            "severe": delta(severe["candidate"], severe["r98"]),
        },
        "horizons": {
            "r98": p1.horizon_stats(r98_result.equity, common_end),
            "candidate": p1.horizon_stats(candidate.equity, common_end),
        },
        "r98_diagnostics": r98_diag,
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "disclosure": "Historical research/chronological holdout only. Position alignment is causal at close t for next-open execution. No real orders.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "train_rule": out["train_rule"],
        "exposure": out["exposure"],
        "base": {n: compact(a) for n, a in base.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "bear_high_vol": bhv_metrics,
        "delta_vs_r98": out["delta_vs_r98"],
    }, indent=2))


if __name__ == "__main__":
    main()
