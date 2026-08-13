from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

from cryptoai.gates import PromotionGates
from cryptoai.metrics import block_bootstrap_ruin_probability, performance
from cryptoai.replay import CandidateSpec, load_universe, phase_sweep, run_replay
from cryptoai.splits import ResearchSplit
from cryptoai.universe import select_discovery_universe


RISK_PROFILES = (
    {"target_volatility": 0.58, "max_gross_leverage": 2.20, "max_single_weight": 0.72},
    {"target_volatility": 0.60, "max_gross_leverage": 2.25, "max_single_weight": 0.75},
    {"target_volatility": 0.62, "max_gross_leverage": 2.30, "max_single_weight": 0.78},
)
CONFLICT_SCALES = (0.40, 0.50, 0.60)
SHOCK_CONFIGS = (
    None,
    (3, 30, 1.40, 0.50),
    (7, 30, 1.25, 0.50),
    (7, 30, 1.50, 0.50),
    (7, 60, 1.25, 0.50),
    (7, 60, 1.50, 0.50),
    (14, 60, 1.25, 0.50),
    (7, 30, 1.25, 0.25),
)


def period_metrics(split: ResearchSplit, returns) -> dict[str, dict[str, float | int]]:
    return {
        "discovery": performance(split.discovery_slice(returns)).to_dict(),
        "validation_2023": performance(split.validation_1_slice(returns)).to_dict(),
        "validation_2024": performance(split.validation_2_slice(returns)).to_dict(),
        "pre_holdout": performance(split.pre_holdout_slice(returns)).to_dict(),
    }


def robust_score(periods: dict[str, dict], decisions: float) -> float:
    cagrs = [
        float(periods["discovery"]["cagr"]),
        float(periods["validation_2023"]["cagr"]),
        float(periods["validation_2024"]["cagr"]),
    ]
    pre = periods["pre_holdout"]
    dd = abs(float(pre["max_drawdown"]))
    return (
        0.45 * min(cagrs)
        + 0.20 * (sum(cagrs) / 3.0)
        + 0.35 * float(pre["cagr"])
        - max(0.0, dd - 0.35) * 6.0
        - sum(max(0.0, -x) for x in cagrs) * 6.0
        - max(0.0, 10.0 - decisions) * 0.015
    )


def row_from_result(split: ResearchSplit, spec: CandidateSpec, result: dict[str, object]) -> dict[str, object]:
    returns = result["returns"]
    split.assert_selection_index_is_pre_holdout(returns.index)
    periods = period_metrics(split, returns)
    decisions = float(result["decisions_per_month"])
    cagrs = [
        float(periods["discovery"]["cagr"]),
        float(periods["validation_2023"]["cagr"]),
        float(periods["validation_2024"]["cagr"]),
    ]
    return {
        "spec": asdict(spec),
        "score": robust_score(periods, decisions),
        "positive_all_selection_periods": all(x > 0.0 for x in cagrs),
        "decisions_per_month": decisions,
        "periods": periods,
        "diagnostics": result["diagnostics"],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-symbols", type=int, default=12)
    p.add_argument("--cache-dir", default=".cache/cryptoai")
    p.add_argument("--bootstrap-samples", type=int, default=2000)
    p.add_argument("--report", default="reports/shock_braked_trend.json")
    args = p.parse_args()

    split = ResearchSplit()
    symbols, universe_meta = select_discovery_universe(args.max_symbols, existed_by="2021-01")
    data = load_universe(symbols, split.discovery_start, "2024-12-31", Path(args.cache_dir))

    rows: list[dict[str, object]] = []
    for risk in RISK_PROFILES:
        for conflict_scale in CONFLICT_SCALES:
            for shock in SHOCK_CONFIGS:
                kwargs = {
                    "volatility_shock_mode": "none",
                    "volatility_shock_scale": 1.0,
                }
                if shock is not None:
                    short_days, long_days, threshold, shock_scale = shock
                    kwargs = {
                        "volatility_shock_mode": "ratio",
                        "volatility_shock_short_days": short_days,
                        "volatility_shock_long_days": long_days,
                        "volatility_shock_threshold": threshold,
                        "volatility_shock_scale": shock_scale,
                    }
                spec = CandidateSpec(
                    core_model="momentum",
                    core_scope="btc_eth",
                    horizons_days=(90, 120, 180),
                    trend_filter_mode="agreement",
                    trend_fast_horizons_days=(20, 40, 60),
                    trend_conflict_scale=conflict_scale,
                    carry_base_allocation=0.0,
                    carry_dominant_allocation=0.0,
                    target_volatility=risk["target_volatility"],
                    max_gross_leverage=risk["max_gross_leverage"],
                    max_single_weight=risk["max_single_weight"],
                    **kwargs,
                )
                rows.append(row_from_result(split, spec, run_replay(data, spec)))

    rows.sort(key=lambda x: float(x["score"]), reverse=True)

    stress_rows: list[dict[str, object]] = []
    for row in rows[:15]:
        spec = CandidateSpec(**row["spec"])
        base = run_replay(data, spec)
        severe = run_replay(data, spec, cost_multiplier=3.0)
        delayed = run_replay(data, replace(spec, execution_delay_hours=3))
        adverse = run_replay(data, spec, funding_adverse=True)
        base_pre = performance(split.pre_holdout_slice(base["returns"])).to_dict()
        severe_pre = performance(split.pre_holdout_slice(severe["returns"])).to_dict()
        delayed_pre = performance(split.pre_holdout_slice(delayed["returns"])).to_dict()
        adverse_pre = performance(split.pre_holdout_slice(adverse["returns"])).to_dict()
        worst_cagr = min(
            float(base_pre["cagr"]),
            float(severe_pre["cagr"]),
            float(delayed_pre["cagr"]),
            float(adverse_pre["cagr"]),
        )
        worst_dd = min(
            float(base_pre["max_drawdown"]),
            float(severe_pre["max_drawdown"]),
            float(delayed_pre["max_drawdown"]),
            float(adverse_pre["max_drawdown"]),
        )
        liquidated = bool(base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or adverse["liquidated"])
        stage2 = (
            row["positive_all_selection_periods"]
            and float(base_pre["cagr"]) >= 0.48
            and float(base_pre["max_drawdown"]) >= -0.37
            and float(severe_pre["cagr"]) >= 0.33
            and float(delayed_pre["cagr"]) >= 0.40
            and float(adverse_pre["cagr"]) >= 0.35
            and float(row["decisions_per_month"]) >= 9.5
            and not liquidated
        )
        stress_rows.append({
            "spec": row["spec"],
            "selection_score": row["score"],
            "positive_all_selection_periods": row["positive_all_selection_periods"],
            "decisions_per_month": row["decisions_per_month"],
            "base_pre_holdout": base_pre,
            "severe_cost_pre_holdout": severe_pre,
            "delay_3h_pre_holdout": delayed_pre,
            "adverse_funding_pre_holdout": adverse_pre,
            "worst_stress_cagr": worst_cagr,
            "worst_stress_drawdown": worst_dd,
            "stage2_screen_passed": stage2,
            "stress_score": worst_cagr - max(0.0, abs(worst_dd) - 0.35) * 3.0,
            "liquidated": liquidated,
        })

    stress_rows.sort(key=lambda x: float(x["stress_score"]), reverse=True)
    finalists = [x for x in stress_rows if x["stage2_screen_passed"]][:3]
    if not finalists and stress_rows:
        finalists = stress_rows[:3]

    finalist_reports: list[dict[str, object]] = []
    for row in finalists:
        spec = CandidateSpec(**row["spec"])
        base = run_replay(data, spec)
        phases = phase_sweep(data, spec)
        phase_min = min(phases.values()) if phases else -1.0
        ruin = block_bootstrap_ruin_probability(
            split.pre_holdout_slice(base["returns"]),
            samples=args.bootstrap_samples,
        )
        gate_inputs = {
            "base_cagr": row["base_pre_holdout"]["cagr"],
            "max_drawdown": row["base_pre_holdout"]["max_drawdown"],
            "severe_cost_cagr": row["severe_cost_pre_holdout"]["cagr"],
            "delay_3h_cagr": row["delay_3h_pre_holdout"]["cagr"],
            "decisions_per_month": row["decisions_per_month"],
            "bootstrap_ruin_probability": ruin,
            "phase_min_cagr": phase_min,
            "liquidated": row["liquidated"],
        }
        finalist_reports.append({
            **row,
            "phase_cagrs": phases,
            "phase_min_cagr": phase_min,
            "bootstrap_ruin_probability": ruin,
            "frozen_gate_shape_pre_holdout_only": PromotionGates().report(gate_inputs),
            "promotion_allowed": False,
            "promotion_note": "Pre-holdout research only; 2025-2026 remains unopened for selection.",
        })

    report = {
        "status": "SHOCK_BRAKED_TREND_PRE_HOLDOUT_ONLY",
        "selection_boundary": "No data from 2025-01-01 onward was loaded or used.",
        "hypothesis": "Keep the high-return slow-momentum engine, retain fast trend agreement, and cut exposure during causal realized-volatility shocks.",
        "universe_selection": {
            "cutoff": "2021-01",
            "selection_fields_used": ["first_month", "symbol"],
            "future_status_metadata_used_for_selection": False,
            "requested_max_symbols": args.max_symbols,
            "loaded_symbols": list(data.close.columns),
            "metadata_for_audit_only": universe_meta,
        },
        "tested_candidates": len(rows),
        "top_selection_candidates": rows[:20],
        "stress_candidates": stress_rows,
        "finalists_pre_holdout": finalist_reports,
    }

    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    best = stress_rows[0] if stress_rows else None
    print(json.dumps({
        "status": report["status"],
        "tested_candidates": len(rows),
        "best_base_cagr": best["base_pre_holdout"]["cagr"] if best else None,
        "best_base_max_drawdown": best["base_pre_holdout"]["max_drawdown"] if best else None,
        "best_severe_cost_cagr": best["severe_cost_pre_holdout"]["cagr"] if best else None,
        "best_delay_3h_cagr": best["delay_3h_pre_holdout"]["cagr"] if best else None,
        "best_adverse_funding_cagr": best["adverse_funding_pre_holdout"]["cagr"] if best else None,
        "best_decisions_per_month": best["decisions_per_month"] if best else None,
        "stage2_passers": sum(1 for x in stress_rows if x["stage2_screen_passed"]),
        "report": str(path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
