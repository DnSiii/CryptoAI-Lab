from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from cryptoai.gates import PromotionGates
from cryptoai.metrics import block_bootstrap_ruin_probability, decisions_per_month, performance
from cryptoai.relative import relative_momentum_signal
from cryptoai.replay import (
    CandidateSpec,
    ReplayData,
    _core_signal,
    _daily_hold,
    _trend_confirmation_multiplier,
    _volatility_shock_multiplier,
    load_universe,
)
from cryptoai.splits import ResearchSplit
from cryptoai.universe import select_discovery_universe


RISK_PROFILES = (
    {"target_volatility": 0.62, "max_gross_leverage": 2.30, "max_single_weight": 0.78},
    {"target_volatility": 0.66, "max_gross_leverage": 2.45, "max_single_weight": 0.82},
    {"target_volatility": 0.70, "max_gross_leverage": 2.55, "max_single_weight": 0.85},
)
RELATIVE_ALLOCATIONS = (0.10, 0.20, 0.30)
RELATIVE_HORIZONS = (
    (20, 40, 60),
    (30, 60, 90),
    (60, 90, 120),
)
CONFLICT_SCALES = (0.40, 0.50)


def _overlay_weights(
    data: ReplayData,
    spec: CandidateSpec,
    *,
    relative_allocation: float,
    relative_horizons: tuple[int, ...],
) -> pd.DataFrame:
    close = data.close
    asset_returns = close.pct_change(fill_method=None)

    core_raw = _core_signal(
        close,
        spec.horizons_days,
        spec.core_model,
        spec.core_scope,
        spec.cross_section_quantile,
    )
    core = _daily_hold(core_raw, spec.rebalance_hour, close)
    relative = relative_momentum_signal(close, relative_horizons, spec.rebalance_hour)
    combined = core.mul(1.0 - relative_allocation).add(relative.mul(relative_allocation), fill_value=0.0)

    raw_ret = (combined.shift(1).fillna(0.0) * asset_returns.fillna(0.0)).sum(axis=1)
    rolling_vol = raw_ret.rolling(spec.vol_lookback_days * 24, min_periods=14 * 24).std() * np.sqrt(365.25 * 24)
    scale = (spec.target_volatility / rolling_vol.replace(0.0, np.nan)).clip(upper=spec.max_gross_leverage).fillna(0.0)
    combined = combined.mul(scale, axis=0)

    gross = combined.abs().sum(axis=1)
    gross_scale = (spec.max_gross_leverage / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    combined = combined.mul(gross_scale, axis=0).clip(-spec.max_single_weight, spec.max_single_weight)
    gross = combined.abs().sum(axis=1)
    gross_scale = (spec.max_gross_leverage / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    combined = combined.mul(gross_scale, axis=0)

    confirmation = _trend_confirmation_multiplier(close, spec)
    shock = _volatility_shock_multiplier(close, spec)
    combined = combined.mul(confirmation).mul(shock)
    combined = _daily_hold(combined, spec.rebalance_hour, close)

    if spec.execution_delay_hours:
        combined = combined.shift(spec.execution_delay_hours).fillna(0.0)
    return combined


def run_overlay(
    data: ReplayData,
    spec: CandidateSpec,
    *,
    relative_allocation: float,
    relative_horizons: tuple[int, ...],
    cost_multiplier: float = 1.0,
    funding_adverse: bool = False,
) -> dict[str, object]:
    weights = _overlay_weights(
        data,
        spec,
        relative_allocation=relative_allocation,
        relative_horizons=relative_horizons,
    )
    close = data.close
    asset_returns = close.pct_change(fill_method=None)
    funding = data.funding.reindex_like(close).fillna(0.0)
    held = weights.shift(1).fillna(0.0)
    price_pnl = (held * asset_returns.fillna(0.0)).sum(axis=1)

    signed_funding_pnl = -held * funding
    if funding_adverse:
        funding_effect = signed_funding_pnl.where(
            signed_funding_pnl < 0,
            signed_funding_pnl * 0.5,
        ).where(
            signed_funding_pnl >= 0,
            signed_funding_pnl * 1.5,
        )
        funding_pnl = funding_effect.sum(axis=1)
    else:
        funding_pnl = signed_funding_pnl.sum(axis=1)

    turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(weights.abs().sum(axis=1))
    costs = turnover * (spec.one_way_cost_bps * cost_multiplier / 10000.0)
    returns = price_pnl + funding_pnl - costs

    return {
        "returns": returns,
        "weights": weights,
        "performance": performance(returns).to_dict(),
        "decisions_per_month": decisions_per_month(weights),
        "liquidated": bool((returns <= -1.0).any()),
        "average_gross_exposure": float(weights.abs().sum(axis=1).mean()),
    }


def phase_sweep_overlay(
    data: ReplayData,
    spec: CandidateSpec,
    *,
    relative_allocation: float,
    relative_horizons: tuple[int, ...],
) -> dict[str, float]:
    out: dict[str, float] = {}
    for hour in range(24):
        result = run_overlay(
            data,
            replace(spec, rebalance_hour=hour),
            relative_allocation=relative_allocation,
            relative_horizons=relative_horizons,
        )
        out[str(hour)] = float(result["performance"]["cagr"])
    return out


def period_metrics(split: ResearchSplit, returns: pd.Series) -> dict[str, dict[str, float | int]]:
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
    return (
        0.45 * min(cagrs)
        + 0.20 * (sum(cagrs) / 3.0)
        + 0.35 * float(pre["cagr"])
        - max(0.0, abs(float(pre["max_drawdown"])) - 0.35) * 6.0
        - sum(max(0.0, -x) for x in cagrs) * 6.0
        - max(0.0, 10.0 - decisions) * 0.02
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-symbols", type=int, default=12)
    p.add_argument("--cache-dir", default=".cache/cryptoai")
    p.add_argument("--bootstrap-samples", type=int, default=2000)
    p.add_argument("--report", default="reports/relative_overlay.json")
    args = p.parse_args()

    split = ResearchSplit()
    symbols, universe_meta = select_discovery_universe(args.max_symbols, existed_by="2021-01")
    data = load_universe(symbols, split.discovery_start, "2024-12-31", Path(args.cache_dir))

    rows: list[dict[str, object]] = []
    for risk in RISK_PROFILES:
        for conflict_scale in CONFLICT_SCALES:
            for relative_allocation in RELATIVE_ALLOCATIONS:
                for relative_horizons in RELATIVE_HORIZONS:
                    spec = CandidateSpec(
                        core_model="momentum",
                        core_scope="btc_eth",
                        horizons_days=(90, 120, 180),
                        trend_filter_mode="agreement",
                        trend_fast_horizons_days=(20, 40, 60),
                        trend_conflict_scale=conflict_scale,
                        volatility_shock_mode="ratio",
                        volatility_shock_short_days=14,
                        volatility_shock_long_days=60,
                        volatility_shock_threshold=1.25,
                        volatility_shock_scale=0.50,
                        carry_base_allocation=0.0,
                        carry_dominant_allocation=0.0,
                        target_volatility=risk["target_volatility"],
                        max_gross_leverage=risk["max_gross_leverage"],
                        max_single_weight=risk["max_single_weight"],
                    )
                    result = run_overlay(
                        data,
                        spec,
                        relative_allocation=relative_allocation,
                        relative_horizons=relative_horizons,
                    )
                    split.assert_selection_index_is_pre_holdout(result["returns"].index)
                    periods = period_metrics(split, result["returns"])
                    decisions = float(result["decisions_per_month"])
                    selection_cagrs = [
                        float(periods["discovery"]["cagr"]),
                        float(periods["validation_2023"]["cagr"]),
                        float(periods["validation_2024"]["cagr"]),
                    ]
                    rows.append({
                        "spec": asdict(spec),
                        "relative_allocation": relative_allocation,
                        "relative_horizons": list(relative_horizons),
                        "score": robust_score(periods, decisions),
                        "positive_all_selection_periods": all(x > 0.0 for x in selection_cagrs),
                        "decisions_per_month": decisions,
                        "periods": periods,
                        "average_gross_exposure": result["average_gross_exposure"],
                    })

    rows.sort(key=lambda x: float(x["score"]), reverse=True)

    stress_rows: list[dict[str, object]] = []
    for row in rows[:15]:
        spec = CandidateSpec(**row["spec"])
        rel_alloc = float(row["relative_allocation"])
        rel_h = tuple(int(x) for x in row["relative_horizons"])
        base = run_overlay(data, spec, relative_allocation=rel_alloc, relative_horizons=rel_h)
        severe = run_overlay(data, spec, relative_allocation=rel_alloc, relative_horizons=rel_h, cost_multiplier=3.0)
        delayed = run_overlay(data, replace(spec, execution_delay_hours=3), relative_allocation=rel_alloc, relative_horizons=rel_h)
        adverse = run_overlay(data, spec, relative_allocation=rel_alloc, relative_horizons=rel_h, funding_adverse=True)
        base_pre = performance(split.pre_holdout_slice(base["returns"])).to_dict()
        severe_pre = performance(split.pre_holdout_slice(severe["returns"])).to_dict()
        delayed_pre = performance(split.pre_holdout_slice(delayed["returns"])).to_dict()
        adverse_pre = performance(split.pre_holdout_slice(adverse["returns"])).to_dict()
        liquidated = bool(base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or adverse["liquidated"])
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
            and float(base_pre["cagr"]) >= 0.48
            and float(base_pre["max_drawdown"]) >= -0.37
            and float(severe_pre["cagr"]) >= 0.34
            and float(delayed_pre["cagr"]) >= 0.40
            and float(adverse_pre["cagr"]) >= 0.35
            and float(row["decisions_per_month"]) >= 9.5
            and not liquidated
        )
        stress_rows.append({
            **row,
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
        rel_alloc = float(row["relative_allocation"])
        rel_h = tuple(int(x) for x in row["relative_horizons"])
        base = run_overlay(data, spec, relative_allocation=rel_alloc, relative_horizons=rel_h)
        phases = phase_sweep_overlay(
            data,
            spec,
            relative_allocation=rel_alloc,
            relative_horizons=rel_h,
        )
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
            "promotion_note": "Pre-holdout only. Asset-removal/delisted and maintenance-margin stresses remain before opening holdout.",
        })

    report = {
        "status": "RELATIVE_OVERLAY_PRE_HOLDOUT_ONLY",
        "selection_boundary": "No data from 2025-01-01 onward was loaded or used.",
        "hypothesis": "Add a low-frequency market-neutral ETH/BTC relative-momentum sleeve to the shock-braked slow-trend frontier to improve independent alpha, activity, and cost robustness.",
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
