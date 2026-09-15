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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase7_train_validated_bhv_short_veto.json"


def bhv_mask(index, direction, vol):
    d = direction.shift(1).reindex(index)
    v = vol.shift(1).reindex(index)
    return (d.eq("BEAR") & v.eq("HIGH_VOLATILITY")).fillna(False)


def isolated_side_targets(targets: pd.DataFrame, mask: pd.Series, side: str):
    out = targets * 0.0
    if side == "long":
        out.loc[mask, :] = targets.loc[mask].clip(lower=0.0)
    else:
        out.loc[mask, :] = targets.loc[mask].clip(upper=0.0)
    return out


def short_veto_targets(targets: pd.DataFrame, mask: pd.Series):
    out = targets.copy()
    out.loc[mask, :] = targets.loc[mask].clip(lower=0.0)
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
    mask = bhv_mask(data.close.index, direction, vol)
    r98_targets, r98_result, r98_diag = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)

    long_targets = isolated_side_targets(r98_targets, mask, "long")
    short_targets = isolated_side_targets(r98_targets, mask, "short")
    long_res = p1.run_targets(data, long_targets, ex, guard, base_cost, p1.GROSS_CAP)
    short_res = p1.run_targets(data, short_targets, ex, guard, base_cost, p1.GROSS_CAP)

    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    long_train = audit.analyze_result(long_res, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    short_train = audit.analyze_result(short_res, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    enable = bool(
        float(long_train.get("roi", 0.0)) > 0.0
        and float(long_train.get("profit_factor", 0.0)) > 1.0
        and float(short_train.get("roi", 0.0)) < 0.0
        and float(short_train.get("profit_factor", 0.0)) < 1.0
    )

    candidate_targets = short_veto_targets(r98_targets, mask) if enable else r98_targets.copy()
    candidate_result = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)

    common_start, common_end = data.close.index[0], data.close.index[-1]
    hold_idx = data.close.index[data.close.index > p1.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    base = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "candidate": audit.analyze_result(candidate_result, data, direction, vol, common_start, common_end),
    }
    hold = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end),
        "candidate": audit.analyze_result(candidate_result, data, direction, vol, hold_start, common_end),
    }

    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    candidate_sev_targets = short_veto_targets(r98_sev_targets, mask) if enable else r98_sev_targets.copy()
    candidate_sev = p1.run_targets(data, candidate_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = {
        "r98": audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end),
        "candidate": audit.analyze_result(candidate_sev, data, direction, vol, common_start, common_end),
    }

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    bench_results = {n: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for n, item in benchmarks.items()}
    bench = {n: audit.analyze_result(res, item["data"], direction, vol, common_start, common_end) for (n, res), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench.items()})
    cmp = audit.candidate_vs_envelope(base["candidate"]["global"], env)

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

    bhv = {
        name: analysis["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
        for name, analysis in base.items()
    }
    out = {
        "study": "V99 R106 phase 7 — train-validated BEAR+HIGH_VOL short veto",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "train_rule": {
            "enable_short_veto": enable,
            "long_only_train_bhv": long_train,
            "short_only_train_bhv": short_train,
            "decision": "enable only if long ROI>0/PF>1 AND short ROI<0/PF<1",
            "holdout_not_used_for_decision": True,
        },
        "r98_diagnostics": r98_diag,
        "base": base,
        "holdout": hold,
        "severe": severe,
        "bear_high_vol": bhv,
        "delta_vs_r98": {
            "base": delta(base["candidate"], base["r98"]),
            "holdout": delta(hold["candidate"], hold["r98"]),
            "severe": delta(severe["candidate"], severe["r98"]),
        },
        "vs_v13_v16_metric_envelope": cmp,
        "pass_count": {"passed": sum(int(v["passed"]) for v in cmp.values()), "total": len(cmp)},
        "horizons": {
            "r98": p1.horizon_stats(r98_result.equity, common_end),
            "candidate": p1.horizon_stats(candidate_result.equity, common_end),
        },
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "disclosure": "Historical research/chronological holdout only. No real orders. Binary rule is train-selected before holdout evaluation.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "train_rule": out["train_rule"],
        "base": {n: compact(a) for n, a in base.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "bear_high_vol": bhv,
        "delta_vs_r98": out["delta_vs_r98"],
        "pass_count": out["pass_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
