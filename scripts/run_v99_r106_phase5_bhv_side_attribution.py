from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

# Apply validated fast/metric fixes before importing the audit users.
import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase5_bhv_side_attribution.json"


def bhv_mask(index: pd.Index, direction: pd.Series, vol: pd.Series) -> pd.Series:
    d = direction.shift(1).reindex(index)
    v = vol.shift(1).reindex(index)
    return (d.eq("BEAR") & v.eq("HIGH_VOLATILITY")).fillna(False)


def counterfactual_targets(r98_targets: pd.DataFrame, mask: pd.Series) -> dict[str, pd.DataFrame]:
    base = r98_targets.copy()
    long_part = base.clip(lower=0.0)
    short_part = base.clip(upper=0.0)
    zero = base * 0.0

    remove_longs = base.copy()
    remove_longs.loc[mask, :] = short_part.loc[mask, :]

    remove_shorts = base.copy()
    remove_shorts.loc[mask, :] = long_part.loc[mask, :]

    flat_bhv = base.copy()
    flat_bhv.loc[mask, :] = 0.0

    long_only_bhv = zero.copy()
    long_only_bhv.loc[mask, :] = long_part.loc[mask, :]

    short_only_bhv = zero.copy()
    short_only_bhv.loc[mask, :] = short_part.loc[mask, :]

    return {
        "r98": base,
        "remove_longs_bhv": remove_longs,
        "remove_shorts_bhv": remove_shorts,
        "flat_bhv": flat_bhv,
        "long_only_bhv": long_only_bhv,
        "short_only_bhv": short_only_bhv,
    }


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "trade_win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100.0 * float(m["avg_winning_trade"]),
        "avg_loss_pct": 100.0 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    r98_targets, r98_result, r98_diag = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    mask = bhv_mask(r98_targets.index, direction, vol)
    variants = counterfactual_targets(r98_targets, mask)
    gross_cap = p1.GROSS_CAP

    results = {"r98": r98_result}
    for name, targets in variants.items():
        if name == "r98":
            continue
        results[name] = p1.run_targets(data, targets, ex, guard, base_cost, gross_cap)

    common_start = data.close.index[0]
    common_end = data.close.index[-1]
    analyses = {
        name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
        for name, result in results.items()
    }
    hold_idx = data.close.index[data.close.index > p1.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold = {
        name: audit.analyze_result(result, data, direction, vol, hold_start, common_end)
        for name, result in results.items()
    }

    # Severe cost is run only for the three full-strategy marginal counterfactuals.
    severe_targets, severe_r98, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    severe_variants = counterfactual_targets(severe_targets, mask)
    severe_results = {"r98": severe_r98}
    for name in ("remove_longs_bhv", "remove_shorts_bhv", "flat_bhv"):
        severe_results[name] = p1.run_targets(data, severe_variants[name], ex, guard, severe_cost, gross_cap)
    severe = {
        name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
        for name, result in severe_results.items()
    }

    bhv_key = "BEAR__HIGH_VOLATILITY"
    side_exposure = {
        "active_fraction": float(mask.mean()),
        "avg_long_gross_when_bhv": float(r98_targets.clip(lower=0.0).sum(axis=1).loc[mask].mean()),
        "avg_short_gross_when_bhv": float((-r98_targets.clip(upper=0.0)).sum(axis=1).loc[mask].mean()),
        "avg_net_when_bhv": float(r98_targets.sum(axis=1).loc[mask].mean()),
        "median_net_when_bhv": float(r98_targets.sum(axis=1).loc[mask].median()),
        "net_short_fraction_when_bhv": float(r98_targets.sum(axis=1).loc[mask].lt(0.0).mean()),
        "net_long_fraction_when_bhv": float(r98_targets.sum(axis=1).loc[mask].gt(0.0).mean()),
    }

    def wealth_ratio(a, b):
        return float((1.0 + a["global"]["roi"]) / max(1e-12, 1.0 + b["global"]["roi"]))

    out = {
        "study": "V99 R106 phase 5 diagnostic — R98 BEAR+HIGH_VOL side attribution",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "r98_diagnostics": r98_diag,
        "side_exposure": side_exposure,
        "base": analyses,
        "holdout": hold,
        "severe": severe,
        "bear_high_vol": {
            name: analysis["regimes"]["matrix"][bhv_key]
            for name, analysis in analyses.items()
        },
        "marginal_vs_r98": {
            name: {
                "full_wealth_ratio": wealth_ratio(analysis, analyses["r98"]),
                "full_dd_delta": float(analysis["global"]["max_drawdown_abs"] - analyses["r98"]["global"]["max_drawdown_abs"]),
                "bhv_roi_delta": float(analysis["regimes"]["matrix"][bhv_key]["roi"] - analyses["r98"]["regimes"]["matrix"][bhv_key]["roi"]),
                "bhv_pf_delta": float(analysis["regimes"]["matrix"][bhv_key]["profit_factor"] - analyses["r98"]["regimes"]["matrix"][bhv_key]["profit_factor"]),
            }
            for name, analysis in analyses.items() if name != "r98"
        },
        "interpretation_contract": {
            "if_remove_longs_improves": "wrong-side long exposure is a primary BEAR+HIGH_VOL drag; next controller may scale only fighting longs",
            "if_remove_shorts_worsens": "short side carries useful crash alpha and must be preserved rather than globally hedged",
            "if_both_sides_bad": "BEAR+HIGH_VOL is primarily an exposure/timing problem rather than one-sided suppression",
            "no_parameter_tuning_in_this_phase": True,
        },
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "disclosure": "Diagnostic historical/holdout counterfactuals only. No real orders. Removing a side is not a proposed production rule.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "side_exposure": side_exposure,
        "base": {n: compact(a) for n, a in analyses.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "bear_high_vol": out["bear_high_vol"],
        "marginal_vs_r98": out["marginal_vs_r98"],
    }, indent=2))


if __name__ == "__main__":
    main()
