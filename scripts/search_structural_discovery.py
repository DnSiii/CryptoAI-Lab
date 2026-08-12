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


HORIZON_SETS = (
    (20, 40, 60),
    (30, 60, 90),
    (60, 90, 120, 150),
    (90, 120, 180),
)

RISK_PROFILES = (
    {"target_volatility": 0.30, "max_gross_leverage": 1.25, "max_single_weight": 0.50},
    {"target_volatility": 0.45, "max_gross_leverage": 1.75, "max_single_weight": 0.60},
)

CARRY_VARIANTS = (
    {
        "carry_horizons_days": (7, 14, 30),
        "carry_base_allocation": 0.15,
        "carry_dominant_allocation": 0.15,
        "carry_names_each_side": 3,
        "carry_require_sign": False,
        "allocation_compare_days": 30,
    },
    {
        "carry_horizons_days": (14, 30, 60),
        "carry_base_allocation": 0.15,
        "carry_dominant_allocation": 0.40,
        "carry_names_each_side": 4,
        "carry_require_sign": False,
        "allocation_compare_days": 45,
    },
    {
        "carry_horizons_days": (30, 60, 90),
        "carry_base_allocation": 0.15,
        "carry_dominant_allocation": 0.35,
        "carry_names_each_side": 3,
        "carry_require_sign": True,
        "allocation_compare_days": 60,
    },
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
    min_cagr = min(cagrs)
    mean_cagr = sum(cagrs) / len(cagrs)
    dd = abs(float(pre["max_drawdown"]))
    dd_penalty = max(0.0, dd - 0.35) * 4.0
    negative_penalty = sum(max(0.0, -x) for x in cagrs) * 5.0
    activity_penalty = max(0.0, 10.0 - decisions) * 0.01
    return 0.55 * min_cagr + 0.25 * mean_cagr + 0.20 * float(pre["cagr"]) - dd_penalty - negative_penalty - activity_penalty


def row_from_result(split: ResearchSplit, spec: CandidateSpec, result: dict[str, object], family: str) -> dict[str, object]:
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
        "family": family,
        "spec": asdict(spec),
        "score": robust_score(periods, decisions),
        "positive_all_selection_periods": all(x > 0.0 for x in cagrs),
        "decisions_per_month": decisions,
        "periods": periods,
        "diagnostics": result["diagnostics"],
    }


def structure_key(row: dict[str, object]) -> tuple:
    s = row["spec"]
    return (
        row["family"],
        s["core_scope"],
        s["core_model"],
        tuple(s["horizons_days"]),
        s["cross_section_quantile"],
    )


def pick_diverse(rows: list[dict[str, object]], n: int) -> list[dict[str, object]]:
    picked: list[dict[str, object]] = []
    seen: set[tuple] = set()
    for row in sorted(rows, key=lambda x: float(x["score"]), reverse=True):
        key = structure_key(row)
        if key in seen:
            continue
        picked.append(row)
        seen.add(key)
        if len(picked) >= n:
            break
    return picked


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-symbols", type=int, default=28)
    p.add_argument("--cache-dir", default=".cache/cryptoai")
    p.add_argument("--bootstrap-samples", type=int, default=1000)
    p.add_argument("--report", default="reports/structural_discovery.json")
    args = p.parse_args()

    split = ResearchSplit()
    symbols, universe_meta = select_discovery_universe(args.max_symbols, existed_by="2021-01")
    data = load_universe(symbols, split.discovery_start, "2024-12-31", Path(args.cache_dir))

    rows: list[dict[str, object]] = []

    for scope, models in (
        ("btc_eth", ("breakout", "momentum", "ensemble")),
        ("universe", ("breakout", "momentum", "ensemble", "rank_momentum")),
    ):
        for model in models:
            for horizons in HORIZON_SETS:
                quantiles = (0.20, 0.25) if model == "rank_momentum" else (0.25,)
                for quantile in quantiles:
                    for risk in RISK_PROFILES:
                        max_single = min(risk["max_single_weight"], 0.35) if scope == "universe" else risk["max_single_weight"]
                        spec = CandidateSpec(
                            core_scope=scope,
                            core_model=model,
                            cross_section_quantile=quantile,
                            horizons_days=horizons,
                            carry_base_allocation=0.0,
                            carry_dominant_allocation=0.0,
                            target_volatility=risk["target_volatility"],
                            max_gross_leverage=risk["max_gross_leverage"],
                            max_single_weight=max_single,
                        )
                        result = run_replay(data, spec)
                        rows.append(row_from_result(split, spec, result, "core_only"))

    core_diverse = pick_diverse(rows, 6)

    overlay_rows: list[dict[str, object]] = []
    for base in core_diverse:
        base_spec = CandidateSpec(**base["spec"])
        for carry in CARRY_VARIANTS:
            spec = replace(base_spec, **carry)
            result = run_replay(data, spec)
            overlay_rows.append(row_from_result(split, spec, result, "core_plus_carry"))

    carry_only_rows: list[dict[str, object]] = []
    for horizons in ((7, 14, 30), (14, 30, 60), (30, 60, 90)):
        for names in (3, 5):
            spec = CandidateSpec(
                core_model="breakout",
                core_scope="btc_eth",
                horizons_days=(20, 40, 60),
                carry_horizons_days=horizons,
                carry_base_allocation=1.0,
                carry_dominant_allocation=1.0,
                carry_names_each_side=names,
                carry_require_sign=False,
                target_volatility=0.30,
                max_gross_leverage=1.50,
                max_single_weight=0.30,
                min_history_days=90,
            )
            result = run_replay(data, spec)
            carry_only_rows.append(row_from_result(split, spec, result, "carry_only"))

    all_rows = rows + overlay_rows + carry_only_rows
    all_rows.sort(key=lambda x: float(x["score"]), reverse=True)

    stress_rows: list[dict[str, object]] = []
    for row in pick_diverse(all_rows, 6):
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
            and float(base_pre["cagr"]) >= 0.35
            and float(base_pre["max_drawdown"]) >= -0.40
            and float(severe_pre["cagr"]) >= 0.20
            and float(delayed_pre["cagr"]) >= 0.30
            and float(adverse_pre["cagr"]) >= 0.20
            and float(row["decisions_per_month"]) >= 10.0
        )
        stress_rows.append({
            "family": row["family"],
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
            "stress_score": worst_cagr - max(0.0, abs(worst_dd) - 0.35) * 2.0,
            "liquidated": bool(base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or adverse["liquidated"]),
        })

    stress_rows.sort(key=lambda x: float(x["stress_score"]), reverse=True)
    finalists = [x for x in stress_rows if x["stage2_screen_passed"]][:2]
    if not finalists and stress_rows:
        finalists = stress_rows[:1]

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
        "status": "STRUCTURAL_DISCOVERY_PRE_HOLDOUT_ONLY",
        "selection_boundary": "No data from 2025-01-01 onward was loaded or used.",
        "universe_selection": {
            "cutoff": "2021-01",
            "selection_fields_used": ["first_month", "symbol"],
            "future_status_metadata_used_for_selection": False,
            "requested_max_symbols": args.max_symbols,
            "loaded_symbols": list(data.close.columns),
            "metadata_for_audit_only": universe_meta,
        },
        "tested": {
            "core_only": len(rows),
            "core_plus_carry": len(overlay_rows),
            "carry_only": len(carry_only_rows),
            "total": len(all_rows),
        },
        "top_selection_candidates": all_rows[:15],
        "stress_candidates": stress_rows,
        "finalists_pre_holdout": finalist_reports,
    }

    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    best = stress_rows[0] if stress_rows else None
    print(json.dumps({
        "status": report["status"],
        "loaded_symbols": len(data.close.columns),
        "tested_total": len(all_rows),
        "best_family": best["family"] if best else None,
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
