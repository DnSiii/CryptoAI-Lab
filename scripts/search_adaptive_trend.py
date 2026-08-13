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


SLOW_HORIZONS = (
    (60, 90, 120),
    (90, 120, 180),
    (120, 180, 240),
)
FAST_HORIZONS = (
    (10, 20, 40),
    (20, 40, 60),
    (30, 60, 90),
)
RISK_PROFILES = (
    {"target_volatility": 0.50, "max_gross_leverage": 1.90, "max_single_weight": 0.65},
    {"target_volatility": 0.60, "max_gross_leverage": 2.25, "max_single_weight": 0.75},
    {"target_volatility": 0.70, "max_gross_leverage": 2.50, "max_single_weight": 0.85},
)
CONFLICT_SCALES = (0.0, 0.25, 0.50)


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
    min_cagr = min(cagrs)
    mean_cagr = sum(cagrs) / len(cagrs)
    pre_cagr = float(pre["cagr"])
    dd = abs(float(pre["max_drawdown"]))
    dd_penalty = max(0.0, dd - 0.35) * 5.0
    negative_penalty = sum(max(0.0, -x) for x in cagrs) * 6.0
    activity_penalty = max(0.0, 10.0 - decisions) * 0.0125
    return 0.45 * min_cagr + 0.20 * mean_cagr + 0.35 * pre_cagr - dd_penalty - negative_penalty - activity_penalty


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
    p.add_argument("--bootstrap-samples", type=int, default=1500)
    p.add_argument("--report", default="reports/adaptive_trend.json")
    args = p.parse_args()

    split = ResearchSplit()
    symbols, universe_meta = select_discovery_universe(args.max_symbols, existed_by="2021-01")
    data = load_universe(symbols, split.discovery_start, "2024-12-31", Path(args.cache_dir))

    rows: list[dict[str, object]] = []

    # Baselines around the promising slow-momentum region. No holdout is loaded.
    for slow in SLOW_HORIZONS:
        for risk in RISK_PROFILES:
            spec = CandidateSpec(
                core_model="momentum",
                core_scope="btc_eth",
                horizons_days=slow,
                trend_filter_mode="none",
                carry_base_allocation=0.0,
                carry_dominant_allocation=0.0,
                target_volatility=risk["target_volatility"],
                max_gross_leverage=risk["max_gross_leverage"],
                max_single_weight=risk["max_single_weight"],
            )
            rows.append(row_from_result(split, spec, run_replay(data, spec)))

    # Causal risk brake: fast breakout confirmation is only observed up to each rebalance.
    for slow in SLOW_HORIZONS:
        for fast in FAST_HORIZONS:
            for conflict_scale in CONFLICT_SCALES:
                for risk in RISK_PROFILES:
                    spec = CandidateSpec(
                        core_model="momentum",
                        core_scope="btc_eth",
                        horizons_days=slow,
                        trend_filter_mode="agreement",
                        trend_fast_horizons_days=fast,
                        trend_conflict_scale=conflict_scale,
                        carry_base_allocation=0.0,
                        carry_dominant_allocation=0.0,
                        target_volatility=risk["target_volatility"],
                        max_gross_leverage=risk["max_gross_leverage"],
                        max_single_weight=risk["max_single_weight"],
                    )
                    rows.append(row_from_result(split, spec, run_replay(data, spec)))

    rows.sort(key=lambda x: float(x["score"]), reverse=True)

    stress_rows: list[dict[str, object]] = []
    for row in rows[:12]:
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
        stage2 = (
            row["positive_all_selection_periods"]
            and float(base_pre["cagr"]) >= 0.45
            and float(base_pre["max_drawdown"]) >= -0.38
            and float(severe_pre["cagr"]) >= 0.30
            and float(delayed_pre["cagr"]) >= 0.36
            and float(adverse_pre["cagr"]) >= 0.30
            and float(row["decisions_per_month"]) >= 8.0
            and not bool(base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or adverse["liquidated"])
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
            "stress_score": worst_cagr - max(0.0, abs(worst_dd) - 0.35) * 2.5,
            "liquidated": bool(base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or adverse["liquidated"]),
        })

    stress_rows.sort(key=lambda x: float(x["stress_score"]), reverse=True)
    finalists = [x for x in stress_rows if x["stage2_screen_passed"]][:3]
    if not finalists and stress_rows:
        finalists = stress_rows[:2]

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
        "status": "ADAPTIVE_TREND_PRE_HOLDOUT_ONLY",
        "selection_boundary": "No data from 2025-01-01 onward was loaded or used.",
        "hypothesis": "Use high-conviction slow momentum for return, then causally cut post-volatility-target exposure when fast breakout disagrees.",
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
