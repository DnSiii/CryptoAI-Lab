from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase9_sideaware_hedge_component as p9
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase9b_sideaware_base_fast.json"


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100.0 * float(m["avg_winning_trade"]),
        "avg_loss_pct": 100.0 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    crash = p4.bear_high_vol_substates(data.close, direction, vol)["CRASH_CONTINUATION"]

    _, original, _ = p1.build_r98_targets(data, raw, ex, guard, gross, cost)
    _, sideaware, diag = p9.build_sideaware_r98(data, raw, ex, guard, gross, cost)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= end)]
    hold_start = hold_idx[0] if len(hold_idx) else end

    o = audit.analyze_result(original, data, direction, vol, start, end)
    s = audit.analyze_result(sideaware, data, direction, vol, start, end)
    oh = audit.analyze_result(original, data, direction, vol, hold_start, end)
    sh = audit.analyze_result(sideaware, data, direction, vol, hold_start, end)
    oc = p4.segment_metrics(original.equity, crash, start, end)
    sc = p4.segment_metrics(sideaware.equity, crash, start, end)
    och = p4.segment_metrics(original.equity, crash, hold_start, end)
    sch = p4.segment_metrics(sideaware.equity, crash, hold_start, end)

    out = {
        "study": "R106 phase 9b fast base-only side-aware check",
        "status": "DIAGNOSTIC_FAST_SAME_STRATEGY_AS_PHASE9",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "original": o,
        "sideaware": s,
        "original_holdout": oh,
        "sideaware_holdout": sh,
        "crash_original": oc,
        "crash_sideaware": sc,
        "crash_holdout_original": och,
        "crash_holdout_sideaware": sch,
        "diagnostics": diag,
        "ratios": {
            "full_wealth": float((1+s["global"]["roi"]) / max(1e-12, 1+o["global"]["roi"])),
            "holdout_wealth": float((1+sh["global"]["roi"]) / max(1e-12, 1+oh["global"]["roi"])),
            "full_dd_ratio": float(s["global"]["max_drawdown_abs"] / max(1e-12, o["global"]["max_drawdown_abs"])),
            "holdout_dd_ratio": float(sh["global"]["max_drawdown_abs"] / max(1e-12, oh["global"]["max_drawdown_abs"])),
        },
        "disclosure": "Fast diagnostic only; exact phase-9 strategy, base-cost only. Full phase 9 controls promotion.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "original": compact(o),
        "sideaware": compact(s),
        "original_holdout": compact(oh),
        "sideaware_holdout": compact(sh),
        "crash_original": oc,
        "crash_sideaware": sc,
        "crash_holdout_original": och,
        "crash_holdout_sideaware": sch,
        "ratios": out["ratios"],
        "diagnostics": diag,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
